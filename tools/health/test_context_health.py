#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


HEALTH_ROOT = Path(__file__).resolve().parent
if str(HEALTH_ROOT) not in sys.path:
    sys.path.insert(0, str(HEALTH_ROOT))

from health_engine.health_engine import ContextHealthEngine  # noqa: E402
from health_engine.report_builder import SCHEMA, render_human  # noqa: E402


def snapshot(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


class ContextHealthTestCase(unittest.TestCase):
    def test_contextos_dogfood_report_has_three_dimensions_and_candidates(self) -> None:
        report = ContextHealthEngine(".").run(generated_at="2026-08-14T00:00:00Z")

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(set(report["dimensions"]), {"integrity", "usefulness", "learning"})
        self.assertGreater(report["summary"]["signal_count"], 0)
        self.assertGreater(report["summary"]["context_update_candidate_count"], 0)
        self.assertEqual(report["dimensions"]["usefulness"]["status"], "unknown")
        self.assertGreater(report["evidence_sources"]["missions"]["closed_count"], 0)
        self.assertGreater(report["evidence_sources"]["evolution_inbox"]["item_count"], 0)

    def test_health_engine_is_read_only(self) -> None:
        root = Path(".").resolve()
        before = snapshot(root)
        ContextHealthEngine(root).run(generated_at="2026-08-14T00:00:00Z")
        after = snapshot(root)

        self.assertEqual(before, after)

    def test_report_is_deterministic_with_fixed_time(self) -> None:
        first = ContextHealthEngine(".").run(generated_at="2026-08-14T00:00:00Z")
        second = ContextHealthEngine(".").run(generated_at="2026-08-14T00:00:00Z")

        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_blocking_validator_findings_block_integrity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("# Broken\n\n[missing](missing.md)\n", encoding="utf-8")
            report = ContextHealthEngine(root).run(generated_at="2026-08-14T00:00:00Z")

        self.assertEqual(report["dimensions"]["integrity"]["status"], "blocked")
        self.assertGreater(report["summary"]["blocking_count"], 0)

    def test_missing_mission_evidence_keeps_usefulness_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "README.md").write_text("# Empty Context\n", encoding="utf-8")
            report = ContextHealthEngine(root).run(generated_at="2026-08-14T00:00:00Z")

        self.assertEqual(report["dimensions"]["usefulness"]["status"], "unknown")

    def test_candidates_are_suggested_noncanonical_and_route_to_construction(self) -> None:
        report = ContextHealthEngine(".").run(generated_at="2026-08-14T00:00:00Z")

        for candidate in report["context_update_candidates"]:
            self.assertEqual(candidate["lifecycle_state"], "suggested")
            self.assertFalse(candidate["canonical"])
            self.assertEqual(candidate["route"], "existing_context_construction_lifecycle")
            self.assertTrue(candidate["promotion_prohibited"])

    def test_human_report_exposes_health_learning_and_truth_boundary(self) -> None:
        report = ContextHealthEngine(".").run(generated_at="2026-08-14T00:00:00Z")
        human = render_human(report)

        self.assertIn("# Context OS Health Report", human)
        self.assertIn("## Executive Assessment", human)
        self.assertIn("Overall Health is", human)
        self.assertIn("## Context Integrity", human)
        self.assertIn("## Context Usefulness", human)
        self.assertIn("## Organizational Learning", human)
        self.assertIn("## Context Update Candidates", human)
        self.assertIn("not organizational truth", human)
        self.assertIn("more in JSON", human)
        self.assertLess(max(len(line) for line in human.splitlines()), 500)

    def test_signal_belief_states_use_canonical_evidence_semantics(self) -> None:
        report = ContextHealthEngine(".").run(generated_at="2026-08-14T00:00:00Z")
        states = {
            signal["belief_state"]
            for dimension in report["dimensions"].values()
            for signal in dimension["signals"]
        }

        self.assertTrue(states <= {"observed", "declared", "derived", "unknown"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
