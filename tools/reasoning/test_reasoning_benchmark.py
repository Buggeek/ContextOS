#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REASONING_ROOT = Path(__file__).resolve().parent
for runtime_root in (REASONING_ROOT, REASONING_ROOT.parent / "memory", REASONING_ROOT.parent / "activation"):
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))

from reasoning_engine import ContextualAssessmentEngine, ReasoningBenchmarkEngine  # noqa: E402
from reasoning_engine.report_builder import BENCHMARK_SCHEMA, render_benchmark_human  # noqa: E402
from test_memory_context_version_integration import exact_candidate, exact_version, policy_inputs  # noqa: E402
from test_memory_retrieval import FIXED_TIME, make_repo, snapshot  # noqa: E402
from test_structured_reasoning_evidence import evidence_set  # noqa: E402


GOAL = "assess organizational context memory evidence policy impact prior decisions"


class ReasoningBenchmarkTestCase(unittest.TestCase):
    def make_reports(self) -> tuple[tempfile.TemporaryDirectory, Path, dict, dict, dict, dict]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        make_repo(root)
        version = exact_version(root)
        engine = ContextualAssessmentEngine(root)
        baseline = engine.run(goal=GOAL, mission_id="BENCHMARK-001", context_versions=[version], generated_at=FIXED_TIME)
        candidate = exact_candidate(root, version)
        authorized = engine.run(
            goal=GOAL,
            mission_id="BENCHMARK-001",
            context_versions=[version],
            generated_at=FIXED_TIME,
            evaluation_time=FIXED_TIME,
            **policy_inputs(candidate, version),
        )
        source = root / "SSOT/P.1_Product_Map.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nChanged governed context.\n", encoding="utf-8")
        drifted = engine.run(goal=GOAL, mission_id="BENCHMARK-001", context_versions=[version], generated_at=FIXED_TIME)
        structured = engine.run(
            goal=GOAL,
            mission_id="BENCHMARK-001",
            context_versions=[version],
            reasoning_evidence=evidence_set(),
            focus_entities=["mission.reasoning"],
            generated_at=FIXED_TIME,
        )
        return temp, root, baseline, authorized, drifted, structured

    @staticmethod
    def cases(baseline: dict, authorized: dict, drifted: dict, structured: dict) -> list[dict]:
        return [
            {
                "id": "benchmark.current_state",
                "reasoning_class": "current_state",
                "question": "Can current structured state be assessed?",
                "assessment": baseline,
                "expected": {"minimum_assertions": {"observations": 1}},
            },
            {
                "id": "benchmark.historical_applicability",
                "reasoning_class": "historical_applicability",
                "question": "Is historical drift distinguished from current applicability?",
                "assessment": drifted,
                "expected": {"minimum_assertions": {"context_changes": 1}},
            },
            {
                "id": "benchmark.contradiction_detection",
                "reasoning_class": "contradiction_detection",
                "question": "Can explicit contradictory claims be identified?",
                "assessment": structured,
                "expected": {"minimum_assertions": {"contradictions": 1}},
            },
            {
                "id": "benchmark.impact_analysis",
                "reasoning_class": "impact_analysis",
                "question": "Can a governed context change be traced to affected outcomes?",
                "assessment": structured,
                "expected": {"statement_fragments": {"interpretations": ["impact on"]}},
            },
            {
                "id": "benchmark.hypothesis",
                "reasoning_class": "hypothesis_formation",
                "question": "Can an unsupported possibility remain a labelled hypothesis?",
                "assessment": baseline,
                "expected": {"minimum_assertions": {"hypotheses": 1}},
            },
            {
                "id": "benchmark.recommendation",
                "reasoning_class": "recommendation_generation",
                "question": "Can recommendations remain distinct from Decisions?",
                "assessment": baseline,
                "expected": {"minimum_assertions": {"recommendations": 1}},
            },
            {
                "id": "benchmark.missing_evidence",
                "reasoning_class": "missing_evidence",
                "question": "Does missing evidence remain explicit?",
                "assessment": baseline,
                "expected": {"minimum_assertions": {"additional_evidence": 1}, "unknowns_preserved": True},
            },
            {
                "id": "benchmark.prior_art",
                "reasoning_class": "prior_art",
                "question": "Can authorized memory inform reasoning without authority?",
                "assessment": authorized,
                "expected": {"minimum_assertions": {"prior_art": 1}, "minimum_selected_memory": 1},
            },
            {
                "id": "benchmark.policy_authority",
                "reasoning_class": "policy_authority",
                "question": "Does missing policy prevent Memory exposure?",
                "assessment": baseline,
                "expected": {"minimum_assertions": {"required_decisions": 1}, "unknowns_preserved": True},
            },
            {
                "id": "benchmark.multi_hop",
                "reasoning_class": "multi_hop_relationship",
                "question": "Can indirect evidence relationships support a multi-hop conclusion?",
                "assessment": structured,
                "expected": {"statement_fragments": {"interpretations": ["indirect relationship path"]}},
            },
        ]

    def test_controlled_benchmark_measures_gaps_without_hiding_them(self) -> None:
        temp, root, baseline, authorized, drifted, structured = self.make_reports()
        self.addCleanup(temp.cleanup)
        before = snapshot(root)
        report = ReasoningBenchmarkEngine().run(self.cases(baseline, authorized, drifted, structured), generated_at=FIXED_TIME)
        after = snapshot(root)

        self.assertEqual(report["schema"], BENCHMARK_SCHEMA)
        self.assertEqual(report["summary"]["status"], "complete")
        self.assertEqual(report["summary"]["case_count"], 10)
        self.assertEqual(report["summary"]["passed_count"], 10)
        self.assertEqual(report["summary"]["failed_count"], 0)
        self.assertEqual(report["summary"]["unexpected_result_count"], 0)
        self.assertEqual(before, after)
        self.assertTrue(report["read_only"])

    def test_graphrag_is_deferred_without_comparative_evidence(self) -> None:
        temp, _, baseline, authorized, drifted, structured = self.make_reports()
        self.addCleanup(temp.cleanup)
        report = ReasoningBenchmarkEngine().run(self.cases(baseline, authorized, drifted, structured), generated_at=FIXED_TIME)

        self.assertEqual(report["graphrag"]["decision"], "defer")
        self.assertFalse(report["graphrag"]["graph_comparison_performed"])
        self.assertFalse(report["graphrag"]["material_graph_advantage_proven"])
        self.assertIn("not required", report["graphrag"]["rationale"])

    def test_report_is_deterministic_parseable_and_human_readable(self) -> None:
        temp, _, baseline, authorized, drifted, structured = self.make_reports()
        self.addCleanup(temp.cleanup)
        cases = self.cases(baseline, authorized, drifted, structured)
        first = ReasoningBenchmarkEngine().run(cases, generated_at=FIXED_TIME)
        second = ReasoningBenchmarkEngine().run(cases, generated_at=FIXED_TIME)

        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        json.loads(json.dumps(first, sort_keys=True))
        human = render_benchmark_human(first)
        self.assertIn("## Reasoning Classes", human)
        self.assertIn("[PASS] `contradiction_detection`", human)
        self.assertIn("Decision: `defer`", human)

    def test_missing_required_class_invalidates_benchmark(self) -> None:
        temp, _, baseline, authorized, drifted, structured = self.make_reports()
        self.addCleanup(temp.cleanup)
        cases = self.cases(baseline, authorized, drifted, structured)[:-1]
        report = ReasoningBenchmarkEngine().run(cases, generated_at=FIXED_TIME)

        self.assertEqual(report["summary"]["status"], "invalid")
        self.assertEqual(report["summary"]["missing_required_classes"], ["multi_hop_relationship"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
