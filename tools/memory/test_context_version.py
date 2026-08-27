#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MEMORY_ROOT = Path(__file__).resolve().parent
if str(MEMORY_ROOT) not in sys.path:
    sys.path.insert(0, str(MEMORY_ROOT))

from memory_engine import ContextVersionEngine  # noqa: E402
from memory_engine.context_version_report_builder import (  # noqa: E402
    PLAN_CHECK_SCHEMA,
    PLAN_SCHEMA,
    VERSION_CHECK_SCHEMA,
    VERSION_SCHEMA,
    render_human,
)
from test_memory_retrieval import make_repo, snapshot  # noqa: E402


FIXED_TIME = "2026-08-23T12:00:00Z"
SCOPE = {
    "organization": "context-os-test",
    "domain": "product",
    "tier": "organizational",
    "context_root": "organizational-context",
}
EXTRA_SOURCES = [
    "docs/0.x_foundations/0.7_COS_Context_Versioning_and_Memory.md",
    "docs/3.x_operation/3.6_COS_Human_Agent_Authority_Model.md",
]


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def add_context_version_sources(root: Path) -> None:
    write(root / EXTRA_SOURCES[0], "# Context Versioning\n## Version: 0.1.0\n\nImmutable references.\n")
    write(root / EXTRA_SOURCES[1], "# Authority\n## Version: 0.1.0\n\nAuthority remains explicit: L0 L1 L2 L3 L4 L5.\n")


def git_commit(root: Path, message: str = "fixture") -> str:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.name=Context OS Tests", "-c", "user.email=tests@contextos.local", "commit", "-qm", message],
        cwd=root,
        check=True,
    )
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def package_and_handoff(root: Path) -> tuple[dict, dict]:
    from activation_engine.package_engine import ContextActivationPackageEngine

    engine = ContextActivationPackageEngine(root)
    package = engine.run(
        goal="Capture governed context for an exact Mission",
        mission_id="TEST-CONTEXT-VERSION-001",
        consumer="codex",
        generated_at=FIXED_TIME,
    )
    return package, engine.build_handoff(package, generated_at=FIXED_TIME)


def plan_for(root: Path, package: dict, handoff: dict, **overrides: object) -> dict:
    values = {
        "scope": SCOPE,
        "event_type": "mission_start",
        "reason": "Freeze exact governed context before Mission execution.",
        "capture_at": FIXED_TIME,
        "mission_id": "TEST-CONTEXT-VERSION-001",
        "goal": "Prove immutable Context Version evidence.",
        "triggering_event": {"type": "mission", "id": "TEST-CONTEXT-VERSION-001"},
        "activation_package": package,
        "activation_handoff": handoff,
        "additional_source_paths": EXTRA_SOURCES,
        "authority_paths": [EXTRA_SOURCES[1]],
        "policy_paths": [],
        "generated_at": FIXED_TIME,
    }
    values.update(overrides)
    return ContextVersionEngine(root).plan(**values)


class ContextVersionTestCase(unittest.TestCase):
    def make_fixture(self, *, git: bool = False) -> tuple[tempfile.TemporaryDirectory, Path, dict, dict]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        make_repo(root)
        add_context_version_sources(root)
        if git:
            git_commit(root)
        package, handoff = package_and_handoff(root)
        return temp, root, package, handoff

    def test_plan_binds_exact_activation_sources_without_copying_content(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        plan = plan_for(root, package, handoff)

        self.assertEqual(plan["schema"], PLAN_SCHEMA)
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["bindings"]["activation_package"]["identity_hash"], package["identity_hash"])
        self.assertEqual(plan["bindings"]["activation_handoff"]["identity_hash"], handoff["identity_hash"])
        self.assertTrue(all(not source["content_embedded"] for source in plan["source_manifest"]))
        serialized = json.dumps(plan, sort_keys=True)
        self.assertNotIn("working_context", serialized)
        self.assertNotIn("content_excerpt", serialized)

    def test_capture_is_deterministic_idempotent_and_read_only(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        before = snapshot(root)
        engine = ContextVersionEngine(root)
        plan = plan_for(root, package, handoff)
        first = engine.capture(plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)
        second = engine.capture(plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)
        after = snapshot(root)

        self.assertEqual(first["schema"], VERSION_SCHEMA)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["identity_hash"], second["identity_hash"])
        self.assertEqual(before, after)
        self.assertTrue(first["immutable"])
        self.assertFalse(first["content_embedded"])
        self.assertFalse(first["authority"]["granted_by_version"])

    def test_source_drift_invalidates_plan_and_blocks_capture(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextVersionEngine(root)
        plan = plan_for(root, package, handoff)
        source = root / "SSOT" / "P.1_Product_Map.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")
        check = engine.check_plan(plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)

        self.assertEqual(check["schema"], PLAN_CHECK_SCHEMA)
        self.assertFalse(check["result"]["valid"])
        self.assertIn("context_version_plan_check.current_state_changed", check["result"]["failed_checks"])
        with self.assertRaises(ValueError):
            engine.capture(plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)

    def test_captured_version_remains_historically_verifiable_after_current_drift(self) -> None:
        temp, root, package, handoff = self.make_fixture(git=True)
        self.addCleanup(temp.cleanup)
        engine = ContextVersionEngine(root)
        plan = plan_for(root, package, handoff)
        version = engine.capture(plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)
        source = root / "SSOT" / "P.1_Product_Map.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nNew current context.\n", encoding="utf-8")
        check = engine.check_version(version, generated_at=FIXED_TIME)

        self.assertEqual(check["schema"], VERSION_CHECK_SCHEMA)
        self.assertEqual(check["result"]["immutable_identity"], "valid")
        self.assertEqual(check["result"]["historical_verification"], "verified")
        self.assertEqual(check["result"]["current_applicability"], "superseded_or_drifted")
        self.assertTrue(check["result"]["material_drift"])
        self.assertEqual(check["result"]["selected_source_content_currentness"], "material_drift")
        drifted = next(item for item in check["source_checks"] if item["locator"] == "SSOT/P.1_Product_Map.md")
        self.assertEqual(drifted["resolution"], "historical_implementation_evidence")

    def test_unrelated_repository_advancement_does_not_make_selected_context_stale(self) -> None:
        temp, root, package, handoff = self.make_fixture(git=True)
        self.addCleanup(temp.cleanup)
        engine = ContextVersionEngine(root)
        plan = plan_for(root, package, handoff)
        version = engine.capture(plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)
        captured_ref = version["implementation_evidence"]["implementation_ref"]
        write(root / "unrelated.txt", "Unrelated implementation evidence.\n")
        subprocess.run(["git", "add", "unrelated.txt"], cwd=root, check=True)
        subprocess.run(
            ["git", "-c", "user.name=Context OS Tests", "-c", "user.email=tests@contextos.local", "commit", "-qm", "unrelated"],
            cwd=root,
            check=True,
        )
        current_ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        check = engine.check_version(version, generated_at=FIXED_TIME)

        self.assertNotEqual(captured_ref, current_ref)
        self.assertEqual(check["result"]["repository_tip_state"], "advanced")
        self.assertEqual(check["result"]["repository_tip_relevance"], "irrelevant_to_selected_context")
        self.assertTrue(check["result"]["irrelevant_repository_advancement"])
        self.assertFalse(check["result"]["material_drift"])
        self.assertEqual(check["result"]["selected_source_content_currentness"], "current")
        self.assertEqual(check["result"]["target_canonical_currentness"], "current")
        self.assertEqual(check["result"]["current_applicability"], "exact_current_match")

    def test_unavailable_historical_source_is_a_gap_not_reconstructed_truth(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextVersionEngine(root)
        plan = plan_for(root, package, handoff)
        version = engine.capture(plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)
        (root / EXTRA_SOURCES[0]).unlink()
        check = engine.check_version(version, generated_at=FIXED_TIME)

        self.assertEqual(check["result"]["immutable_identity"], "valid")
        self.assertEqual(check["result"]["historical_verification"], "partial")
        self.assertEqual(check["result"]["current_applicability"], "superseded_or_drifted")
        self.assertGreater(len(check["continuity_gaps"]), 0)
        self.assertTrue(any(item["resolution"] == "unavailable" for item in check["source_checks"]))

    def test_later_version_records_supersession_without_mutating_parent(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextVersionEngine(root)
        parent_plan = plan_for(root, package, handoff)
        parent = engine.capture(parent_plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)
        preserved_parent = copy.deepcopy(parent)
        source = root / "SSOT" / "P.1_Product_Map.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nGoverned new state.\n", encoding="utf-8")
        next_package, next_handoff = package_and_handoff(root)
        next_plan = plan_for(
            root,
            next_package,
            next_handoff,
            event_type="explicit_human_checkpoint",
            capture_at="2026-08-24T12:00:00Z",
            parent_version=parent,
        )
        child = engine.capture(
            next_plan,
            activation_package=next_package,
            activation_handoff=next_handoff,
            parent_version=parent,
            generated_at=FIXED_TIME,
        )

        self.assertEqual(parent, preserved_parent)
        self.assertEqual(child["lineage"]["parent_version"]["id"], parent["id"])
        self.assertEqual(child["lineage"]["supersedes"], parent["id"])
        self.assertIsNone(parent["lineage"]["superseding_version"])
        self.assertNotEqual(child["id"], parent["id"])

    def test_tampered_version_identity_is_detected(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextVersionEngine(root)
        plan = plan_for(root, package, handoff)
        version = engine.capture(plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)
        version["capture"]["reason"] = "Rewritten historical rationale."
        check = engine.check_version(version, generated_at=FIXED_TIME)

        self.assertEqual(check["result"]["immutable_identity"], "tampered")
        self.assertFalse(check["result"]["historically_valid_identity"])

    def test_truth_axes_remain_unclassified_instead_of_inferred(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        plan = plan_for(root, package, handoff)
        version = ContextVersionEngine(root).capture(
            plan,
            activation_package=package,
            activation_handoff=handoff,
            generated_at=FIXED_TIME,
        )

        count = len(version["source_manifest"])
        self.assertEqual(version["truth_summary"]["epistemic_support"]["unclassified"], count)
        self.assertEqual(version["truth_summary"]["governance_lifecycle"]["unclassified"], count)
        self.assertEqual(version["truth_summary"]["strategic_belief"]["unclassified"], count)

    def test_routine_file_change_is_not_a_capture_event(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        with self.assertRaises(ValueError):
            plan_for(root, package, handoff, event_type="routine_file_change")

    def test_invalid_time_and_source_escape_do_not_enter_capture(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        with self.assertRaises(ValueError):
            plan_for(root, package, handoff, capture_at="not-a-time")
        escaped = plan_for(root, package, handoff, additional_source_paths=[*EXTRA_SOURCES, "../outside.md"])

        self.assertEqual(escaped["status"], "blocked")
        self.assertTrue(any("source_outside_root" in gap["id"] for gap in escaped["continuity_gaps"]))
        self.assertNotIn("../outside.md", [item["source_of_record"]["locator"] for item in escaped["source_manifest"]])

    def test_tampered_parent_version_is_rejected(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextVersionEngine(root)
        plan = plan_for(root, package, handoff)
        parent = engine.capture(plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)
        parent["capture"]["reason"] = "Tampered parent."

        with self.assertRaises(ValueError):
            plan_for(root, package, handoff, event_type="explicit_human_checkpoint", parent_version=parent)

    def test_human_reports_explain_version_without_presenting_context_copy(self) -> None:
        temp, root, package, handoff = self.make_fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextVersionEngine(root)
        plan = plan_for(root, package, handoff)
        version = engine.capture(plan, activation_package=package, activation_handoff=handoff, generated_at=FIXED_TIME)
        check = engine.check_version(version, generated_at=FIXED_TIME)

        plan_human = render_human(plan)
        version_human = render_human(version)
        check_human = render_human(check)
        self.assertIn("Context Version Capture Plan", plan_human)
        self.assertIn("Content embedded: no", plan_human)
        self.assertIn("Historical identity grants no authority", version_human)
        self.assertIn("Historical verification", check_human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
