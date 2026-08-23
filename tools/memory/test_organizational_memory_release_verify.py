#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import os
import subprocess
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

from memory_engine import MemoryRetrievalEngine, OrganizationalMemoryEngine  # noqa: E402
from memory_engine.report_builder import render_human as render_continuity_human  # noqa: E402
from memory_engine.retrieval_report_builder import render_human as render_retrieval_human  # noqa: E402
from test_memory_context_version_integration import (  # noqa: E402
    GOAL,
    exact_candidate,
    exact_version,
    policy_inputs as version_policy_inputs,
)
from test_memory_retrieval import FIXED_TIME, make_repo, snapshot  # noqa: E402
from test_memory_retrieval_policy import metadata_for, policy, relevant_candidates  # noqa: E402


class OrganizationalMemoryReleaseVerificationTestCase(unittest.TestCase):
    def make_fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, dict]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        make_repo(root)
        version = exact_version(root)
        return temp, root, version

    def test_complete_memory_journey_preserves_forms_and_authority_boundary(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        candidate = exact_candidate(root, version)
        before = snapshot(root)
        continuity = OrganizationalMemoryEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            generated_at=FIXED_TIME,
        )
        retrieval = MemoryRetrievalEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            evaluation_time=FIXED_TIME,
            generated_at=FIXED_TIME,
            **version_policy_inputs(candidate, version),
        )
        after = snapshot(root)

        for form in ("mission", "decision", "evidence", "outcome", "learning"):
            self.assertGreater(continuity["summary"]["memory_form_counts"][form], 0)
        self.assertGreater(continuity["summary"]["supersession_count"], 0)
        self.assertEqual(continuity["summary"]["context_version_bindings"]["exact"], 1)
        self.assertEqual(retrieval["summary"]["selected_count"], 1)
        self.assertFalse(retrieval["authority"]["retrieved_memory_may_override_canonical"])
        self.assertFalse(retrieval["authority"]["retrieved_memory_added_to_governing_context"])
        self.assertFalse(retrieval["authority"]["usefulness_inferred"])
        self.assertEqual(before, after)

    def test_exact_partial_unknown_and_ambiguous_bindings_never_fabricate_history(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        partial_path = root / "SSOT/E.4_Mission_TEST-ACTIVATION-001_Context_Activation.md"
        partial_path.write_text(
            partial_path.read_text(encoding="utf-8")
            + "\nObserved historical evidence: activation.package.0123456789abcdef.\n",
            encoding="utf-8",
        )
        report = OrganizationalMemoryEngine(root).run(
            context_versions=[version],
            generated_at=FIXED_TIME,
        )
        ambiguous = OrganizationalMemoryEngine(root).run(
            context_versions=[version, copy.deepcopy(version)],
            generated_at=FIXED_TIME,
        )

        self.assertEqual(report["summary"]["context_version_bindings"], {"exact": 1, "partial": 1, "unknown": 0})
        partial = next(
            item for item in report["memory_forms"]["mission"] if item["mission_id"] == "TEST-ACTIVATION-001"
        )
        self.assertEqual(partial["context_evidence"]["binding_state"], "partial")
        self.assertIsNone(partial["context_evidence"]["context_version"])
        self.assertEqual(ambiguous["context_versions"]["accepted_exact_count"], 0)
        self.assertTrue(any("ambiguous" in gap["id"] for gap in ambiguous["continuity_gaps"]))

    def test_policy_matrix_is_evaluated_before_candidate_metadata_exposure(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            candidates = relevant_candidates(root)
            normal, elevated, excluded, prohibited, missing, conflict = candidates[:6]
            policies = [
                policy("policy.normal", normal["candidate_id"]),
                policy(
                    "policy.elevated",
                    elevated["candidate_id"],
                    required_authority={"retrieval": ["memory_owner"]},
                ),
                policy("policy.excluded", excluded["candidate_id"], "excluded", explanation_visibility="none"),
                policy("policy.prohibited", prohibited["candidate_id"], "prohibited", explanation_visibility="none"),
                policy(
                    "policy.conflict",
                    conflict["candidate_id"],
                    obligations=[{"id": "obligation.interpret", "kind": "preserve", "requires_interpretation": True}],
                    explanation_visibility="none",
                ),
            ]
            report = MemoryRetrievalEngine(root).run(
                goal=GOAL,
                retention_policies=policies,
                memory_metadata_by_id=metadata_for(candidates),
                evaluation_time=FIXED_TIME,
                generated_at=FIXED_TIME,
            )

        outcomes = report["summary"]["policy_outcomes"]
        self.assertEqual(outcomes["normal"], 1)
        self.assertEqual(outcomes["elevated_authority"], 1)
        self.assertEqual(outcomes["excluded"], 1)
        self.assertEqual(outcomes["prohibited"], 1)
        self.assertGreaterEqual(outcomes["unknown"], 2)
        protected = json.dumps({"evaluations": report["policy_evaluations"], "exclusions": report["exclusions"]})
        for candidate in (elevated, excluded, prohibited, missing, conflict):
            self.assertNotIn(candidate["candidate_id"], protected)
            self.assertNotIn(candidate["title"], protected)
            self.assertNotIn(candidate["source"]["path"], protected)

    def test_context_version_metadata_and_referenced_content_have_independent_policy(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        candidate = exact_candidate(root, version)
        inputs = version_policy_inputs(candidate, version, version_outcome="prohibited")
        report = MemoryRetrievalEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            evaluation_time=FIXED_TIME,
            generated_at=FIXED_TIME,
            **inputs,
        )

        item = next(row for row in report["items"] if row["mission_id"] == "TEST-MEMORY-001")
        self.assertEqual(item["context_evidence"]["status"], "withheld_by_policy")
        self.assertFalse(item["context_evidence"]["metadata_exposed"])
        self.assertNotIn(version["id"], json.dumps(item["context_evidence"], sort_keys=True))
        self.assertTrue(version["retention"]["version_metadata_and_referenced_content_independent"])
        self.assertFalse(version["retention"]["transition_executed"])

    def test_explicit_version_artifact_survives_process_restart_without_registry(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        artifact_temp = tempfile.TemporaryDirectory()
        self.addCleanup(artifact_temp.cleanup)
        artifact = Path(artifact_temp.name) / f"{version['id']}.json"
        artifact.write_text(json.dumps(version, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        script = """
import json, sys
from memory_engine import ContextVersionEngine, OrganizationalMemoryEngine
root, artifact = sys.argv[1:]
version = json.load(open(artifact, encoding='utf-8'))
check = ContextVersionEngine(root).check_version(version)
continuity = OrganizationalMemoryEngine(root).run(context_versions=[version])
print(json.dumps({'check': check['result'], 'bindings': continuity['summary']['context_version_bindings']}))
"""
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join((str(MEMORY_ROOT), str(ACTIVATION_ROOT)))
        completed = subprocess.run(
            [sys.executable, "-c", script, str(root), str(artifact)],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        result = json.loads(completed.stdout)

        self.assertEqual(result["check"]["immutable_identity"], "valid")
        self.assertEqual(result["check"]["historical_verification"], "verified")
        self.assertEqual(result["bindings"]["exact"], 1)

    def test_saved_retrieval_invalidates_on_policy_version_and_context_version_drift(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        candidate = exact_candidate(root, version)
        inputs = version_policy_inputs(candidate, version)
        engine = MemoryRetrievalEngine(root)
        report = engine.run(
            goal=GOAL,
            context_versions=[version],
            evaluation_time=FIXED_TIME,
            generated_at=FIXED_TIME,
            **inputs,
        )
        valid = engine.check_retrieval(report, context_versions=[version], generated_at=FIXED_TIME, **inputs)
        changed_policies = copy.deepcopy(inputs["retention_policies"])
        changed_policies[0]["version"] = "2"
        policy_drift = engine.check_retrieval(
            report,
            retention_policies=changed_policies,
            memory_metadata_by_id=inputs["memory_metadata_by_id"],
            context_versions=[version],
            generated_at=FIXED_TIME,
        )
        source = root / "docs/3.x_operation/3.6_COS_Human_Agent_Authority_Model.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nChanged authority evidence.\n", encoding="utf-8")
        version_drift = engine.check_retrieval(report, context_versions=[version], generated_at=FIXED_TIME, **inputs)

        self.assertTrue(valid["result"]["valid"])
        self.assertFalse(policy_drift["result"]["valid"])
        self.assertIn("memory_retrieval_check.policy_context_changed", policy_drift["result"]["failed_checks"])
        self.assertFalse(version_drift["result"]["valid"])
        self.assertIn("memory_retrieval_check.continuity_state_changed", version_drift["result"]["failed_checks"])

    def test_human_and_machine_reports_explain_history_without_implying_truth_or_usefulness(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        candidate = exact_candidate(root, version)
        continuity = OrganizationalMemoryEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            generated_at=FIXED_TIME,
        )
        retrieval = MemoryRetrievalEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            evaluation_time=FIXED_TIME,
            generated_at=FIXED_TIME,
            **version_policy_inputs(candidate, version),
        )
        continuity_text = render_continuity_human(continuity)
        retrieval_text = render_retrieval_human(retrieval)
        machine = json.loads(json.dumps(retrieval, sort_keys=True))

        self.assertIn("Exact Context Version bindings", continuity_text)
        self.assertIn("Historical Context Version", retrieval_text)
        self.assertIn("none_from_historical_context", retrieval_text)
        self.assertIn("not_evaluated", retrieval_text)
        self.assertFalse(machine["authority"]["usefulness_inferred"])
        self.assertFalse(machine["authority"]["retrieved_memory_added_to_governing_context"])

    def test_human_report_distinguishes_relevance_from_policy_eligibility(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            report = MemoryRetrievalEngine(root).run(goal=GOAL, generated_at=FIXED_TIME)
            human = render_retrieval_human(report)

        self.assertGreater(report["summary"]["relevant_candidate_count"], 0)
        self.assertEqual(report["summary"]["selected_count"], 0)
        self.assertIn("Relevant candidates were found, but none passed", human)
        self.assertNotIn("No candidate crossed the deterministic relevance threshold", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
