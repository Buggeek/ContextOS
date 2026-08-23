#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


MEMORY_ROOT = Path(__file__).resolve().parent
if str(MEMORY_ROOT) not in sys.path:
    sys.path.insert(0, str(MEMORY_ROOT))
ACTIVATION_ROOT = MEMORY_ROOT.parent / "activation"
if str(ACTIVATION_ROOT) not in sys.path:
    sys.path.insert(0, str(ACTIVATION_ROOT))

from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402
from memory_engine import ContextVersionEngine, MemoryRetrievalEngine, OrganizationalMemoryEngine  # noqa: E402
from memory_engine.report_builder import render_human as render_continuity_human  # noqa: E402
from memory_engine.retrieval_engine import candidate_records, tokens  # noqa: E402
from memory_engine.retrieval_report_builder import render_human as render_retrieval_human  # noqa: E402
from test_memory_retrieval import FIXED_TIME, make_repo, snapshot  # noqa: E402
from test_memory_retrieval_policy import policy  # noqa: E402


GOAL = "memory decision provenance authority historical context version"


def exact_version(root: Path, mission_id: str = "TEST-MEMORY-001") -> dict:
    mission_path = next((root / "SSOT").glob(f"E.4_Mission_{mission_id}_*.md"))
    activation = ContextActivationPackageEngine(root)
    package = activation.run(
        goal="Bind exact governed context to historical memory",
        mission_id=mission_id,
        consumer="codex",
        generated_at=FIXED_TIME,
    )
    handoff = activation.build_handoff(package, generated_at=FIXED_TIME)
    engine = ContextVersionEngine(root)
    plan = engine.plan(
        scope={
            "organization": "test",
            "domain": "product",
            "tier": "organizational",
            "context_root": "test-canonical-context",
        },
        event_type="mission_start",
        reason="Freeze exact governed context for the Mission.",
        capture_at=FIXED_TIME,
        mission_id=mission_id,
        goal="Bind exact governed context to historical memory.",
        activation_package=package,
        activation_handoff=handoff,
        additional_source_paths=[
            mission_path.relative_to(root).as_posix(),
            "docs/3.x_operation/3.6_COS_Human_Agent_Authority_Model.md",
        ],
        authority_paths=["docs/3.x_operation/3.6_COS_Human_Agent_Authority_Model.md"],
        generated_at=FIXED_TIME,
    )
    return engine.capture(
        plan,
        activation_package=package,
        activation_handoff=handoff,
        generated_at=FIXED_TIME,
    )


def exact_candidate(root: Path, version: dict) -> dict:
    continuity = OrganizationalMemoryEngine(root).run(
        goal=GOAL,
        context_versions=[version],
        generated_at=FIXED_TIME,
    )
    engine = MemoryRetrievalEngine(root)
    ranked, _ = engine._rank_relevant(candidate_records(continuity), tokens(GOAL), None)
    return next(row[1] for row in ranked if row[1]["mission_id"] == "TEST-MEMORY-001")


def policy_inputs(candidate: dict, version: dict, *, version_outcome: str = "normal") -> dict:
    policies = [
        policy("policy.memory-item", candidate["candidate_id"]),
        policy(
            "policy.context-version",
            version["id"],
            version_outcome,
            explanation_visibility="none" if version_outcome != "normal" else "id_only",
        ),
    ]
    return {
        "retention_policies": policies,
        "memory_metadata_by_id": {
            "defaults": {
                "organization": "test",
                "operation": "product",
                "tier": "organizational",
                "owner": "Test Owner",
                "sensitivity": "internal",
                "retention_state": "historical",
                "metadata_visibility": "full",
            },
            "items": {
                candidate["candidate_id"]: {"metadata_visibility": "full"},
                version["id"]: {
                    "metadata_visibility": "none" if version_outcome != "normal" else "full"
                },
            },
        },
    }


class MemoryContextVersionIntegrationTestCase(unittest.TestCase):
    def make_fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, dict]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        make_repo(root)
        version = exact_version(root)
        return temp, root, version

    def test_continuity_binds_exact_partial_and_unknown_without_reconstruction(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        activation_mission = root / "SSOT/E.4_Mission_TEST-ACTIVATION-001_Context_Activation.md"
        activation_mission.write_text(
            activation_mission.read_text(encoding="utf-8")
            + "\nPartial evidence: activation.package.0123456789abcdef and `0123456789abcdef0123456789abcdef01234567`.\n",
            encoding="utf-8",
        )
        report = OrganizationalMemoryEngine(root).run(context_versions=[version], generated_at=FIXED_TIME)

        counts = report["summary"]["context_version_bindings"]
        self.assertEqual(counts["exact"], 1)
        self.assertEqual(counts["partial"], 1)
        exact = next(item for item in report["memory_forms"]["decision"] if item["mission_id"] == "TEST-MEMORY-001")
        partial = next(item for item in report["memory_forms"]["decision"] if item["mission_id"] == "TEST-ACTIVATION-001")
        self.assertEqual(exact["context_evidence"]["context_version"]["id"], version["id"])
        self.assertEqual(partial["context_evidence"]["binding_state"], "partial")
        self.assertIsNone(partial["context_evidence"]["context_version"])
        self.assertFalse(report["context_versions"]["historical_authority_granted"])
        self.assertFalse(report["context_versions"]["semantic_comparison_performed"])

    def test_policy_permitted_retrieval_exposes_exact_version_without_authority(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        candidate = exact_candidate(root, version)
        report = MemoryRetrievalEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            evaluation_time=FIXED_TIME,
            generated_at=FIXED_TIME,
            **policy_inputs(candidate, version),
        )

        item = next(item for item in report["items"] if item["mission_id"] == "TEST-MEMORY-001")
        context = item["context_evidence"]
        self.assertTrue(context["metadata_exposed"])
        self.assertEqual(context["context_version"]["id"], version["id"])
        self.assertEqual(context["context_version"]["historical_verification"], "verified")
        self.assertEqual(context["authority"]["current_authority"], "none_from_historical_context")
        self.assertEqual(context["semantic_applicability"], "not_evaluated")
        self.assertFalse(item["authority"]["may_override_current_context"])

    def test_restricted_version_lineage_does_not_leak_through_retrieval(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        candidate = exact_candidate(root, version)
        report = MemoryRetrievalEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            evaluation_time=FIXED_TIME,
            generated_at=FIXED_TIME,
            **policy_inputs(candidate, version, version_outcome="prohibited"),
        )

        item = next(item for item in report["items"] if item["mission_id"] == "TEST-MEMORY-001")
        context = item["context_evidence"]
        serialized = json.dumps(context, sort_keys=True)
        self.assertEqual(context["status"], "withheld_by_policy")
        self.assertFalse(context["metadata_exposed"])
        self.assertNotIn(version["id"], serialized)
        self.assertNotIn(version["identity_hash"], serialized)
        self.assertNotIn("source_manifest", serialized)
        self.assertNotIn("lineage", serialized)

    def test_version_state_drift_invalidates_saved_retrieval(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        candidate = exact_candidate(root, version)
        inputs = policy_inputs(candidate, version)
        engine = MemoryRetrievalEngine(root)
        report = engine.run(
            goal=GOAL,
            context_versions=[version],
            evaluation_time=FIXED_TIME,
            generated_at=FIXED_TIME,
            **inputs,
        )
        valid = engine.check_retrieval(
            report,
            context_versions=[version],
            generated_at=FIXED_TIME,
            **inputs,
        )
        authority = root / "docs/3.x_operation/3.6_COS_Human_Agent_Authority_Model.md"
        authority.write_text(authority.read_text(encoding="utf-8") + "\nChanged authority evidence.\n", encoding="utf-8")
        check = engine.check_retrieval(
            report,
            context_versions=[version],
            generated_at=FIXED_TIME,
            **inputs,
        )

        self.assertTrue(valid["result"]["valid"])
        self.assertFalse(check["result"]["valid"])
        self.assertIn("memory_retrieval_check.continuity_state_changed", check["result"]["failed_checks"])
        self.assertIn("memory_retrieval_check.selection_changed", check["result"]["failed_checks"])

    def test_tampered_version_is_not_bound_and_engine_remains_read_only(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        tampered = copy.deepcopy(version)
        tampered["capture"]["reason"] = "Rewritten history."
        before = snapshot(root)
        report = OrganizationalMemoryEngine(root).run(context_versions=[tampered], generated_at=FIXED_TIME)
        after = snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(report["context_versions"]["accepted_exact_count"], 0)
        self.assertTrue(any(gap["id"] == "memory.gap.context_version_invalid" for gap in report["continuity_gaps"]))

    def test_multiple_versions_for_one_mission_are_ambiguous_not_silently_selected(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        report = OrganizationalMemoryEngine(root).run(
            context_versions=[version, copy.deepcopy(version)],
            generated_at=FIXED_TIME,
        )

        self.assertEqual(report["context_versions"]["accepted_exact_count"], 0)
        self.assertEqual(report["summary"]["context_version_bindings"]["exact"], 0)
        self.assertTrue(any("context_version_ambiguous" in gap["id"] for gap in report["continuity_gaps"]))

    def test_human_reports_make_epistemic_and_authority_boundaries_visible(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        continuity = OrganizationalMemoryEngine(root).run(context_versions=[version], generated_at=FIXED_TIME)
        candidate = exact_candidate(root, version)
        retrieval = MemoryRetrievalEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            evaluation_time=FIXED_TIME,
            generated_at=FIXED_TIME,
            **policy_inputs(candidate, version),
        )

        continuity_text = render_continuity_human(continuity)
        retrieval_text = render_retrieval_human(retrieval)
        self.assertIn("Exact Context Version bindings", continuity_text)
        self.assertIn("Historical Context Version", retrieval_text)
        self.assertIn("none_from_historical_context", retrieval_text)
        self.assertIn("not_evaluated", retrieval_text)


if __name__ == "__main__":
    unittest.main(verbosity=2)
