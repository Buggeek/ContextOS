#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


REASONING_ROOT = Path(__file__).resolve().parent
for runtime_root in (REASONING_ROOT, REASONING_ROOT.parent / "memory", REASONING_ROOT.parent / "activation"):
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))

from reasoning_engine import ContextualAssessmentEngine  # noqa: E402
from reasoning_engine.report_builder import SCHEMA, render_human  # noqa: E402
from test_memory_context_version_integration import exact_candidate, exact_version, policy_inputs  # noqa: E402
from test_memory_retrieval import FIXED_TIME, make_repo, snapshot  # noqa: E402


GOAL = "assess organizational memory evidence authority context health next decision"


class ContextualAssessmentTestCase(unittest.TestCase):
    def make_fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, dict]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        make_repo(root)
        version = exact_version(root)
        return temp, root, version

    def test_assessment_is_deterministic_read_only_and_preserves_boundaries(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        before = snapshot(root)
        engine = ContextualAssessmentEngine(root)
        first = engine.run(goal=GOAL, mission_id="TEST-REASONING-001", context_versions=[version], generated_at=FIXED_TIME)
        second = engine.run(goal=GOAL, mission_id="TEST-REASONING-001", context_versions=[version], generated_at=FIXED_TIME)
        after = snapshot(root)

        self.assertEqual(first["schema"], SCHEMA)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(before, after)
        self.assertTrue(first["read_only"])
        self.assertFalse(first["authority"]["may_decide"])
        self.assertFalse(first["authority"]["may_execute"])
        self.assertFalse(first["truth_boundary"]["recommendation_is_decision"])
        self.assertFalse(first["truth_boundary"]["assessment_is_canonical_truth"])
        self.assertFalse(first["summary"]["artificial_confidence_score_used"])

    def test_missing_policy_preserves_relevant_memory_as_unknown(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        report = ContextualAssessmentEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            generated_at=FIXED_TIME,
        )

        memory = report["evidence"]["memory_retrieval"]
        self.assertGreater(memory["summary"]["relevant_candidate_count"], 0)
        self.assertEqual(memory["summary"]["selected_count"], 0)
        self.assertTrue(any("no candidate is currently visible" in item["statement"] for item in report["reasoning"]["unknowns"]))
        self.assertTrue(report["reasoning"]["required_decisions"])
        self.assertTrue(report["reasoning"]["hypotheses"])

    def test_authorized_memory_becomes_prior_art_without_becoming_authority(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        candidate = exact_candidate(root, version)
        report = ContextualAssessmentEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            generated_at=FIXED_TIME,
            evaluation_time=FIXED_TIME,
            **policy_inputs(candidate, version),
        )

        self.assertTrue(report["reasoning"]["prior_art"])
        self.assertTrue(all(item["canonical"] is False for item in report["reasoning"]["prior_art"]))
        self.assertTrue(any("Retrieval grants no current authority" in item["statement"] for item in report["reasoning"]["interpretations"]))
        self.assertFalse(report["evidence"]["memory_retrieval"]["authority"]["retrieved_memory_may_override_canonical"])

    def test_historical_drift_is_context_change_not_semantic_applicability(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        source = root / "SSOT/P.1_Product_Map.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nChanged current context.\n", encoding="utf-8")
        report = ContextualAssessmentEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            generated_at=FIXED_TIME,
        )

        self.assertTrue(report["reasoning"]["context_changes"])
        self.assertIn("differs from current governed source state", report["reasoning"]["context_changes"][0]["statement"])
        self.assertNotIn("applicable", report["reasoning"]["context_changes"][0]["statement"].lower())
        self.assertFalse(report["truth_boundary"]["historical_context_is_current_authority"])

    def test_tampered_context_version_is_rejected(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        tampered = copy.deepcopy(version)
        tampered["capture"]["reason"] = "Rewritten reasoning history."

        with self.assertRaisesRegex(ValueError, "tampered Context Version"):
            ContextualAssessmentEngine(root).run(goal=GOAL, context_versions=[tampered], generated_at=FIXED_TIME)

    def test_saved_assessment_check_is_valid_until_bound_state_drifts(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextualAssessmentEngine(root)
        report = engine.run(goal=GOAL, context_versions=[version], generated_at=FIXED_TIME)
        valid = engine.check_assessment(report, generated_at=FIXED_TIME)
        source = root / "SSOT/P.1_Product_Map.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")
        drifted = engine.check_assessment(report, generated_at=FIXED_TIME)

        self.assertEqual(valid["schema"], "contextos.reasoning.assessment_check/1")
        self.assertTrue(valid["result"]["valid"])
        self.assertFalse(valid["result"]["invalidated"])
        self.assertFalse(drifted["result"]["valid"])
        self.assertIn("reasoning.assessment_check.current_state_changed", drifted["result"]["failed_checks"])

    def test_saved_assessment_check_rejects_tampering(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextualAssessmentEngine(root)
        report = engine.run(goal=GOAL, context_versions=[version], generated_at=FIXED_TIME)
        tampered = copy.deepcopy(report)
        tampered["reasoning"]["recommendations"][0]["statement"] = "Approve automatically."
        check = engine.check_assessment(tampered, generated_at=FIXED_TIME)

        self.assertEqual(check["checks"]["immutable_identity"], "tampered")
        self.assertFalse(check["result"]["valid"])
        self.assertIn("reasoning.assessment_check.immutable_identity", check["result"]["failed_checks"])

    def test_human_report_makes_epistemic_and_authority_states_visible(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        report = ContextualAssessmentEngine(root).run(goal=GOAL, context_versions=[version], generated_at=FIXED_TIME)
        human = render_human(report)

        self.assertIn("## Assessment Boundary", human)
        self.assertIn("## Observed Facts", human)
        self.assertIn("## Interpretations", human)
        self.assertIn("## Hypotheses", human)
        self.assertIn("## Recommendations", human)
        self.assertIn("## Required Human Decisions", human)
        self.assertIn("cannot decide, approve, execute", human)
        json.loads(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
