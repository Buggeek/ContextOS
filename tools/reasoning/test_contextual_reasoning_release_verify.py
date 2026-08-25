#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
for runtime_root in (ROOT / "tools/reasoning", ROOT / "tools/memory", ROOT / "tools/activation"):
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))

from reasoning_engine import ContextualAssessmentEngine, ReasoningBenchmarkEngine  # noqa: E402
from reasoning_engine.report_builder import render_human  # noqa: E402
from test_contextual_assessment import GOAL  # noqa: E402
from test_memory_context_version_integration import exact_candidate, exact_version, policy_inputs  # noqa: E402
from test_memory_retrieval import FIXED_TIME, make_repo, snapshot  # noqa: E402
import test_reasoning_benchmark as benchmark_fixture  # noqa: E402
from test_structured_reasoning_evidence import evidence_set  # noqa: E402


class ContextualReasoningReleaseVerifyTestCase(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, dict]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        make_repo(root)
        return temp, root, exact_version(root)

    def test_context_os_dogfood_is_read_only_and_explainable(self) -> None:
        before = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
        report = ContextualAssessmentEngine(ROOT).run(
            goal="Verify Context OS v0.9 reasoning readiness",
            mission_id="V09-CONTEXTUAL-REASONING-RELEASE-VERIFY-001",
            generated_at=FIXED_TIME,
        )
        after = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
        human = render_human(report)

        self.assertEqual(before, after)
        self.assertEqual(report["schema"], "contextos.reasoning.assessment/1")
        self.assertIn(report["summary"]["status"], {"ready", "attention", "blocked"})
        self.assertIn("## Observed Facts", human)
        self.assertIn("## Unknowns And Gaps", human)
        self.assertIn("## Required Human Decisions", human)
        self.assertFalse(report["authority"]["may_decide"])

    def test_controlled_benchmark_passes_all_classes_and_defers_graphrag(self) -> None:
        case = benchmark_fixture.ReasoningBenchmarkTestCase()
        temp, _, baseline, authorized, drifted, structured = case.make_reports()
        self.addCleanup(temp.cleanup)
        report = ReasoningBenchmarkEngine().run(
            case.cases(baseline, authorized, drifted, structured), generated_at=FIXED_TIME
        )

        self.assertEqual(report["summary"]["case_count"], 10)
        self.assertEqual(report["summary"]["passed_count"], 10)
        self.assertEqual(report["summary"]["release_gap_count"], 0)
        self.assertEqual(report["graphrag"]["decision"], "defer")
        self.assertTrue(report["graphrag"]["structured_multi_hop_passed"])
        self.assertFalse(report["graphrag"]["material_graph_advantage_proven"])

    def test_truth_axes_and_relationship_reasoning_do_not_grant_authority(self) -> None:
        temp, root, version = self.fixture()
        self.addCleanup(temp.cleanup)
        report = ContextualAssessmentEngine(root).run(
            goal="Verify governed structured reasoning",
            context_versions=[version],
            reasoning_evidence=evidence_set(),
            focus_entities=["mission.reasoning"],
            generated_at=FIXED_TIME,
        )

        self.assertTrue(report["reasoning"]["contradictions"])
        self.assertTrue(any("indirect relationship path" in item["statement"] for item in report["reasoning"]["interpretations"]))
        for values in report["reasoning"].values():
            for item in values:
                self.assertFalse(item["canonical"])
                self.assertFalse(item["decision"])
                self.assertTrue(item["evidence_refs"])
        self.assertFalse(report["authority"]["may_execute"])

    def test_policy_unknown_and_authorized_prior_art_remain_distinct(self) -> None:
        temp, root, version = self.fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextualAssessmentEngine(root)
        withheld = engine.run(goal=GOAL, context_versions=[version], generated_at=FIXED_TIME)
        candidate = exact_candidate(root, version)
        authorized = engine.run(
            goal=GOAL,
            context_versions=[version],
            generated_at=FIXED_TIME,
            evaluation_time=FIXED_TIME,
            **policy_inputs(candidate, version),
        )

        self.assertEqual(withheld["evidence"]["memory_retrieval"]["summary"]["selected_count"], 0)
        self.assertTrue(withheld["reasoning"]["required_decisions"])
        self.assertGreater(authorized["evidence"]["memory_retrieval"]["summary"]["selected_count"], 0)
        self.assertTrue(authorized["reasoning"]["prior_art"])
        self.assertFalse(authorized["truth_boundary"]["historical_context_is_current_authority"])

    def test_saved_assessment_exact_tampered_and_drifted_states(self) -> None:
        temp, root, version = self.fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextualAssessmentEngine(root)
        report = engine.run(goal=GOAL, context_versions=[version], generated_at=FIXED_TIME)
        exact = engine.check_assessment(report, generated_at=FIXED_TIME)
        tampered_report = copy.deepcopy(report)
        tampered_report["query"]["goal"] = "Changed saved goal"
        tampered = engine.check_assessment(tampered_report, generated_at=FIXED_TIME)
        source = root / "SSOT/P.1_Product_Map.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")
        drifted = engine.check_assessment(report, generated_at=FIXED_TIME)

        self.assertTrue(exact["result"]["valid"])
        self.assertEqual(tampered["checks"]["immutable_identity"], "tampered")
        self.assertFalse(drifted["result"]["valid"])
        self.assertEqual(drifted["checks"]["current_state"], "drifted_or_unverifiable")

    def test_cli_human_and_machine_product_surfaces(self) -> None:
        human = subprocess.run(
            [str(ROOT / "contextos"), "reason", "--root", str(ROOT), "--goal", "Verify v0.9 product experience"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        machine = subprocess.run(
            [
                str(ROOT / "contextos"),
                "reason",
                "--root",
                str(ROOT),
                "--goal",
                "Verify v0.9 product experience",
                "--evaluation-time",
                FIXED_TIME,
                "--format",
                "json",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(human.returncode, 0)
        self.assertIn("# Context OS Contextual Assessment", human.stdout)
        self.assertEqual(human.stderr, "")
        report = json.loads(machine.stdout)
        self.assertEqual(machine.returncode, 0)
        self.assertEqual(report["schema"], "contextos.reasoning.assessment/1")
        self.assertEqual(machine.stderr, "")

    def test_existing_examples_return_parseable_reports_without_crashing(self) -> None:
        for relative in ("examples/sample_solo_founder", "examples/sample_mid_size_org"):
            result = subprocess.run(
                [
                    str(ROOT / "contextos"),
                    "reason",
                    "--root",
                    str(ROOT / relative),
                    "--goal",
                    "Identify governed context gaps",
                    "--format",
                    "json",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            report = json.loads(result.stdout)
            self.assertIn(result.returncode, {0, 7})
            self.assertEqual(report["schema"], "contextos.reasoning.assessment/1")
            self.assertTrue(report["read_only"])
            self.assertEqual(result.stderr, "")

    def test_machine_reports_are_parseable_and_fixture_remains_unchanged(self) -> None:
        temp, root, version = self.fixture()
        self.addCleanup(temp.cleanup)
        before = snapshot(root)
        report = ContextualAssessmentEngine(root).run(
            goal=GOAL,
            context_versions=[version],
            reasoning_evidence=evidence_set(),
            focus_entities=["mission.reasoning"],
            generated_at=FIXED_TIME,
        )
        check = ContextualAssessmentEngine(root).check_assessment(report, generated_at=FIXED_TIME)
        after = snapshot(root)

        json.loads(json.dumps(report, sort_keys=True))
        json.loads(json.dumps(check, sort_keys=True))
        self.assertEqual(before, after)
        self.assertTrue(check["result"]["valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
