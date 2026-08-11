#!/usr/bin/env python3
"""Tests for Context OS Context Construction planning."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


CONSTRUCTION_ROOT = Path(__file__).resolve().parent
if str(CONSTRUCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(CONSTRUCTION_ROOT))

from construction_engine.planning_engine import ContextConstructionPlanEngine  # noqa: E402
from construction_engine.report_builder import SCHEMA, render_human  # noqa: E402


def write(path: Path, text: str = "# Test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_snapshot(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


class ContextConstructionPlanTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md")
        write(root / "SSOT" / "S.1_Vision.md")
        return temp

    def test_plan_shape_and_read_only_constraints(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = file_snapshot(root)
            report = ContextConstructionPlanEngine(root).run(generated_at="2026-08-11T00:00:00Z")
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["generated_at"], "2026-08-11T00:00:00Z")
        self.assertTrue(report["read_only"])
        self.assertFalse(report["constraints"]["writes_performed"])
        self.assertFalse(report["constraints"]["automatic_truth_creation"])
        self.assertFalse(report["constraints"]["automatic_promotion"])

    def test_contextos_repo_has_observed_and_suggested_candidates(self) -> None:
        report = ContextConstructionPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        candidates = {candidate["target_path"]: candidate for candidate in report["context_artifact_candidates"]}

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["discovery"]["schema"], "contextos.discovery.bundle/1")
        self.assertGreater(report["discovery"]["artifact_count"], 100)
        self.assertEqual(candidates["SSOT/S.1_Vision.md"]["lifecycle_state"], "observed")
        self.assertEqual(candidates["SSOT/A.1_System_Map.md"]["belief_state"], "observed")
        self.assertEqual(candidates["SSOT/A.1_System_Map.md"]["source_signals"]["discovery"], "observed")
        self.assertTrue(any(ref.startswith("discovery.artifact.") for ref in candidates["SSOT/A.1_System_Map.md"]["evidence_refs"]))
        self.assertIn("automatic_promotion", candidates["SSOT/S.1_Vision.md"]["prohibited_transitions"])

    def test_minimal_repo_marks_missing_artifacts_as_suggested_not_canonical(self) -> None:
        with self.make_repo() as temp:
            report = ContextConstructionPlanEngine(temp).run(generated_at="2026-08-11T00:00:00Z")
        candidates = {candidate["target_path"]: candidate for candidate in report["context_artifact_candidates"]}

        self.assertEqual(candidates["SSOT/S.1_Vision.md"]["lifecycle_state"], "observed")
        self.assertEqual(candidates["SSOT/P.1_Product_Map.md"]["lifecycle_state"], "suggested")
        self.assertIn("not invent canonical content", candidates["SSOT/P.1_Product_Map.md"]["truth_boundary"])
        self.assertEqual(candidates["SSOT/P.1_Product_Map.md"]["allowed_next_states"], ["draft"])

    def test_validator_or_readiness_blockers_are_explicit_actions(self) -> None:
        report = ContextConstructionPlanEngine("examples/sample_solo_founder").run(generated_at="2026-08-11T00:00:00Z")
        action_ids = {action["id"] for action in report["actions"]}

        self.assertIn("construction.action.resolve_validator_blockers", action_ids)
        self.assertIn("construction.action.reach_construction_readiness", action_ids)
        self.assertFalse(report["summary"]["ready_for_construction"])

    def test_human_report_contains_lifecycle_and_truth_boundary(self) -> None:
        report = ContextConstructionPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        human = render_human(report)

        self.assertIn("# Context OS Construction Plan", human)
        self.assertIn("observed -> inferred -> suggested -> draft -> reviewed -> approved -> canonical/verified", human)
        self.assertIn("## Constructable Candidates", human)
        self.assertIn("## Truth Boundary", human)
        self.assertIn("This construction plan did not modify the target repository.", human)

    def test_json_report_is_serializable_and_deterministic_with_fixed_time(self) -> None:
        first = ContextConstructionPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        second = ContextConstructionPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        loaded = json.loads(json.dumps(first, sort_keys=True))

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))


if __name__ == "__main__":
    unittest.main(verbosity=2)
