#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


MEMORY_ROOT = Path(__file__).resolve().parent
if str(MEMORY_ROOT) not in sys.path:
    sys.path.insert(0, str(MEMORY_ROOT))

from memory_engine import OrganizationalMemoryEngine  # noqa: E402
from memory_engine.report_builder import SCHEMA, render_human  # noqa: E402


FIXED_TIME = "2026-08-21T00:00:00Z"


def snapshot(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def write_fixture(root: Path) -> None:
    ssot = root / "SSOT"
    ssot.mkdir()
    (ssot / "P.2_Product_Roadmap.md").write_text("# Current Version\n\nv0.8 - Organizational Memory\n", encoding="utf-8")
    mission = """# E.4 Mission TEST-001 - Governed Memory\n## Version: 0.1.0\nLast Updated: 2026-08-21\nOwner: Test Owner\nStatus: closed:done\n\n## Mission Packet\n```yaml\nmission_packet:\n  schema: contextos.mission.packet/1\n  id: TEST-001\n  release: v0.8-organizational-memory\n  created_at: 2026-08-20\n  status: closed:done\n```\n\n## Decision\nDecision: preserve evidence provenance and authority.\n\n## Evidence Captured\nValidator evidence remained traceable.\n\n## Outcome\nA read-only continuity result was produced.\n\n## Learning\nRead-only evidence and authority prevent canonical truth drift.\n"""
    (ssot / "E.4_Mission_TEST-001_Governed_Memory.md").write_text(mission, encoding="utf-8")
    mission2 = mission.replace("TEST-001", "TEST-002").replace("Governed Memory", "Drift Validation").replace("2026-08-20", "2026-08-21")
    (ssot / "E.4_Mission_TEST-002_Drift_Validation.md").write_text(mission2, encoding="utf-8")
    mission3 = mission.replace("TEST-001", "TEST-003").replace("Governed Memory", "Authority Evidence")
    (ssot / "E.4_Mission_TEST-003_Authority_Evidence.md").write_text(mission3, encoding="utf-8")
    inbox = """# Evolution Inbox\n\n| ID | Category | Status | Source | Observation | Disposition | Owner |\n|---|---|---|---|---|---|---|\n| INBOX-001 | product | superseded | TEST-001 | Old decision remains historical. | Superseded by TEST-002. | Maintainers |\n"""
    (ssot / "E.5_Evolution_Inbox.md").write_text(inbox, encoding="utf-8")


class OrganizationalMemoryTestCase(unittest.TestCase):
    def test_contextos_dogfood_preserves_memory_forms_and_provenance(self) -> None:
        report = OrganizationalMemoryEngine(".").run(
            mission_id="V08-ORGANIZATIONAL-MEMORY-PLAN-001",
            goal="Preserve Mission decision evidence outcome learning continuity and prior art.",
            generated_at=FIXED_TIME,
        )

        self.assertEqual(report["schema"], SCHEMA)
        for form in ("mission", "decision", "evidence", "outcome", "learning", "context_state"):
            self.assertIn(form, report["memory_forms"])
        self.assertGreater(report["summary"]["memory_form_counts"]["mission"], 0)
        self.assertGreater(report["summary"]["memory_form_counts"]["learning"], 0)
        self.assertGreater(report["summary"]["prior_art_count"], 0)
        self.assertTrue(all(item["source"]["source_hash"] for item in report["memory_forms"]["decision"]))
        self.assertTrue(all(item["truth"]["index_status"] == "recorded" for item in report["memory_forms"]["decision"]))
        self.assertTrue(all(item["truth"]["governance_lifecycle"] is None for item in report["memory_forms"]["decision"]))
        self.assertTrue(any(gap["id"] == "memory.gap.release_transition_records" for gap in report["continuity_gaps"]))

    def test_engine_is_read_only_and_deterministic_with_fixed_time(self) -> None:
        root = Path(".").resolve()
        before = snapshot(root)
        first = OrganizationalMemoryEngine(root).run(mission_id="TEST", goal="memory continuity", generated_at=FIXED_TIME)
        second = OrganizationalMemoryEngine(root).run(mission_id="TEST", goal="memory continuity", generated_at=FIXED_TIME)
        after = snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_explicit_supersession_is_preserved_without_deletion(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_fixture(root)
            report = OrganizationalMemoryEngine(root).run(goal="governed memory", generated_at=FIXED_TIME)

        self.assertEqual(report["summary"]["supersession_count"], 1)
        self.assertEqual(report["supersession"][0]["id"], "INBOX-001")
        self.assertIn("TEST-002", report["supersession"][0]["superseded_by"])
        self.assertFalse(report["retention"]["automated_deletion"])

    def test_temporal_unknowns_remain_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_fixture(root)
            path = root / "SSOT" / "E.4_Mission_TEST-001_Governed_Memory.md"
            path.write_text(path.read_text(encoding="utf-8").replace("  created_at: 2026-08-20\n", ""), encoding="utf-8")
            report = OrganizationalMemoryEngine(root).run(generated_at=FIXED_TIME)

        item = next(item for item in report["memory_forms"]["mission"] if item["mission_id"] == "TEST-001")
        self.assertIsNone(item["temporal"]["valid_from"])
        self.assertIn("valid_from", item["temporal"]["temporal_unknowns"])

    def test_pattern_candidates_remain_noncanonical_hypotheses(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_fixture(root)
            report = OrganizationalMemoryEngine(root).run(goal="evidence authority", generated_at=FIXED_TIME)

        self.assertGreater(len(report["pattern_candidates"]), 0)
        for candidate in report["pattern_candidates"]:
            self.assertEqual(candidate["truth"]["epistemic_support"], "derived")
            self.assertEqual(candidate["truth"]["governance_lifecycle"], "suggested")
            self.assertEqual(candidate["truth"]["strategic_belief"], "hypothesis")
            self.assertFalse(candidate["canonical"])
            self.assertTrue(candidate["automatic_consolidation_prohibited"])

    def test_prior_art_is_explainable_and_not_claimed_useful(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            write_fixture(root)
            report = OrganizationalMemoryEngine(root).run(mission_id="NEW", goal="evidence authority", generated_at=FIXED_TIME)

        self.assertGreater(len(report["prior_art"]), 0)
        item = report["prior_art"][0]
        self.assertEqual(item["relevance"]["method"], "deterministic_term_overlap")
        self.assertTrue(item["relevance"]["matched_terms"])
        self.assertEqual(item["truth"]["epistemic_support"], "derived")
        self.assertEqual(item["truth"]["strategic_belief"], "hypothesis")

    def test_human_report_exposes_continuity_and_governance_boundaries(self) -> None:
        report = OrganizationalMemoryEngine(".").run(goal="memory continuity", generated_at=FIXED_TIME)
        human = render_human(report)

        self.assertIn("# Context OS Memory Continuity Report", human)
        self.assertIn("## Prior Art For This Mission", human)
        self.assertIn("## Supersession", human)
        self.assertIn("## Pattern Candidates", human)
        self.assertIn("not a second SSOT", human)
        self.assertIn("Remembered does not mean canonical", human)
        self.assertIn("No automated deletion", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
