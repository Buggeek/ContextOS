#!/usr/bin/env python3
"""Tests for Context OS Builder Draft Planning."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


BUILDER_ROOT = Path(__file__).resolve().parent
if str(BUILDER_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILDER_ROOT))

from builder_engine.draft_plan import BuilderDraftPlanEngine  # noqa: E402
from builder_engine.report_builder import SCHEMA, render_human  # noqa: E402


def write(path: Path, text: str = "# Test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_snapshot(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


class BuilderDraftPlanTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md", "# Example\nOwner: Jane Example\n")
        write(root / "SSOT" / "S.1_Vision.md", "# Vision\nOwner: Founder\n")
        return temp

    def test_draft_plan_shape_and_read_only_constraints(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = file_snapshot(root)
            report = BuilderDraftPlanEngine(root).run(generated_at="2026-08-11T00:00:00Z")
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertTrue(report["read_only"])
        self.assertFalse(report["constraints"]["writes_performed"])
        self.assertFalse(report["constraints"]["drafts_created"])
        self.assertFalse(report["constraints"]["automatic_truth_creation"])

    def test_existing_context_is_review_existing_not_truth(self) -> None:
        report = BuilderDraftPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        items = {item["target_context_artifact"]: item for item in report["draft_items"]}

        self.assertEqual(items["SSOT/S.1_Vision.md"]["status"], "blocked")
        self.assertEqual(items["SSOT/S.1_Vision.md"]["source_states"]["discovery_artifact_state"], "observed")
        self.assertIn("no_automatic_promotion", items["SSOT/S.1_Vision.md"]["promotion_restrictions"])
        self.assertTrue(items["SSOT/S.1_Vision.md"]["required_human_review"]["required"])

    def test_missing_context_tracks_unknowns_and_missing_evidence(self) -> None:
        with self.make_repo() as temp:
            report = BuilderDraftPlanEngine(temp).run(generated_at="2026-08-11T00:00:00Z")
        items = {item["target_context_artifact"]: item for item in report["draft_items"]}
        product_map = items["SSOT/P.1_Product_Map.md"]

        self.assertIn(product_map["status"], {"blocked", "draftable", "insufficient_evidence"})
        self.assertIn("draft content", product_map["unknowns"])
        self.assertIn("human-authored draft source", product_map["missing_evidence"])
        self.assertEqual(product_map["draftability"]["would_create_or_modify_file"], False)

    def test_conflicting_ownership_blocks_item(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / "SSOT" / "A.1_System_Map.md", "# System\nOwner: Alice\nOwner: Bob\n")
            report = BuilderDraftPlanEngine(root).run(generated_at="2026-08-11T00:00:00Z")
        items = {item["target_context_artifact"]: item for item in report["draft_items"]}
        item = items["SSOT/A.1_System_Map.md"]

        self.assertEqual(item["status"], "blocked")
        self.assertTrue(item["contradictions"])
        self.assertEqual(item["contradictions"][0]["type"], "conflicting_ownership_evidence")

    def test_json_report_is_serializable_and_deterministic_with_fixed_time(self) -> None:
        first = BuilderDraftPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        second = BuilderDraftPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        loaded = json.loads(json.dumps(first, sort_keys=True))

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_human_report_names_truth_boundary(self) -> None:
        report = BuilderDraftPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        human = render_human(report)

        self.assertIn("# Context OS Builder Draft Plan", human)
        self.assertIn("## Truth Boundary", human)
        self.assertIn("Evidence does not become organizational truth.", human)
        self.assertIn("No draft files were written.", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
