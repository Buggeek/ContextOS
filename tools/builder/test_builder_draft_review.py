#!/usr/bin/env python3
"""Tests for Context OS Builder draft review surface."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


BUILDER_ROOT = Path(__file__).resolve().parent
if str(BUILDER_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILDER_ROOT))

from builder_engine.draft_create import BuilderDraftCreateEngine  # noqa: E402
from builder_engine.draft_review import BuilderDraftReviewEngine, SCHEMA, render_human  # noqa: E402
from test_builder_draft_create import copy_contextos_repo, eligible_preflight, write_json  # noqa: E402


def file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


class BuilderDraftReviewTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        copy_contextos_repo(Path(temp.name) / "repo")
        return temp

    def create_draft(self, root: Path, output_root: Path) -> tuple[dict, dict]:
        preflight = eligible_preflight(root)
        target = next(target for target in preflight["targets"] if target["target_context_artifact"] == "SSOT/P.1_Product_Map.md")
        preflight_path = output_root / "preflight.json"
        write_json(preflight_path, preflight)
        result = BuilderDraftCreateEngine(root).run(
            preflight,
            preflight_ref=str(preflight_path),
            confirm_create=True,
            authorized_by="Jane Product Owner",
            authorized_role="Product Owner",
            authorized_authority_level="L2",
            authorized_capability="builder.draft.create",
            authorized_mission_id=preflight["mission"]["id"],
            authorized_preflight_id=preflight["id"],
            authorized_preflight_hash=preflight["identity_hash"],
            authorized_builder_draft_plan_hash=preflight["source_plan"]["hash"],
            authorized_draft_item_ids=[target["draft_item_id"]],
            authorized_target_paths=[target["draft_workspace_target_path"]],
            generated_at="2026-08-11T00:00:01Z",
        )
        self.assertTrue(result["result"]["success"])
        return result, target

    def test_review_shape_and_read_only_guarantees(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            result, _target = self.create_draft(root, Path(output_temp))
            before = file_snapshot(root)
            review = BuilderDraftReviewEngine(root).run(result, generated_at="2026-08-11T00:00:02Z")
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(review["schema"], SCHEMA)
        self.assertTrue(review["read_only"])
        self.assertTrue(review["result"]["success"])
        self.assertEqual(review["result"]["state"], "review_ready")
        self.assertFalse(review["constraints"]["drafts_mutated"])
        self.assertFalse(review["constraints"]["approval_performed"])
        self.assertFalse(review["constraints"]["promotion_performed"])

    def test_review_exposes_lifecycle_truth_and_provenance_boundaries(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            result, target = self.create_draft(root, Path(output_temp))
            review = BuilderDraftReviewEngine(root).run(result, generated_at="2026-08-11T00:00:02Z")

        item = review["draft_reviews"][0]
        boundary = item["truth_boundary"]

        self.assertEqual(item["draft_path"], target["draft_workspace_target_path"])
        self.assertEqual(item["target_context_artifact"], "SSOT/P.1_Product_Map.md")
        self.assertEqual(item["lifecycle"]["state"], "draft")
        self.assertFalse(item["lifecycle"]["canonical"])
        self.assertFalse(item["lifecycle"]["approved"])
        self.assertIn("source_preflight_id", item["source"])
        self.assertIn("source_discovery_fingerprint", item["provenance"])
        self.assertIn("evidence_refs", item)
        self.assertEqual(boundary["observed"]["meaning"], "Source evidence and file existence were observed.")
        self.assertIn("planning interpretations", boundary["inferred"]["meaning"])
        self.assertIn("construction/draft plan", boundary["suggested"]["meaning"])
        self.assertIn("non-canonical draft", boundary["drafted"]["meaning"])
        self.assertIn("Unknowns", boundary["unknown"]["meaning"])
        self.assertFalse(boundary["approved_truth"]["canonical"])

    def test_review_exposes_uncertainty_authority_and_next_action(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            result, _target = self.create_draft(root, Path(output_temp))
            review = BuilderDraftReviewEngine(root).run(result, generated_at="2026-08-11T00:00:02Z")

        item = review["draft_reviews"][0]

        self.assertGreater(len(item["uncertainty"]["unknowns"]), 0)
        self.assertGreater(len(item["uncertainty"]["missing_evidence"]), 0)
        self.assertEqual(item["uncertainty"]["contradictions"], [])
        self.assertTrue(item["authority_still_required"]["review_required"])
        self.assertTrue(item["authority_still_required"]["approval_required"])
        self.assertTrue(item["authority_still_required"]["promotion_authority_required"])
        self.assertIn("no_automatic_promotion", item["promotion_restrictions"])
        self.assertEqual(item["recommended_next_action"]["state"], "ready_for_human_review")

    def test_human_review_names_truth_boundary(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            result, _target = self.create_draft(root, Path(output_temp))
            human = render_human(BuilderDraftReviewEngine(root).run(result, generated_at="2026-08-11T00:00:02Z"))

        self.assertIn("# Context OS Draft Review", human)
        self.assertIn("## Truth Boundary", human)
        self.assertIn("Observed evidence, inferred classification, suggested context, draft content", human)
        self.assertIn("This review does not approve, promote, or persist a review decision.", human)
        self.assertIn("Repository file state unchanged: yes", human)

    def test_missing_draft_blocks_review_without_mutation(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            result, target = self.create_draft(root, Path(output_temp))
            (root / target["draft_workspace_target_path"]).unlink()
            before = file_snapshot(root)
            review = BuilderDraftReviewEngine(root).run(result, generated_at="2026-08-11T00:00:02Z")
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertFalse(review["result"]["success"])
        self.assertEqual(review["result"]["state"], "blocked")
        self.assertEqual(review["draft_reviews"][0]["status"], "missing")

    def test_tampered_canonical_metadata_blocks_review(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            result, target = self.create_draft(root, Path(output_temp))
            draft_path = root / target["draft_workspace_target_path"]
            content = draft_path.read_text(encoding="utf-8")
            draft_path.write_text(content.replace('"canonical": false', '"canonical": true'), encoding="utf-8")
            review = BuilderDraftReviewEngine(root).run(result, generated_at="2026-08-11T00:00:02Z")

        self.assertFalse(review["result"]["success"])
        self.assertEqual(review["draft_reviews"][0]["status"], "blocked")
        self.assertIn("Draft metadata implies review, approval, promotion, or canonical truth.", review["result"]["errors"])

    def test_json_review_is_serializable(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            result, _target = self.create_draft(root, Path(output_temp))
            review = BuilderDraftReviewEngine(root).run(result, generated_at="2026-08-11T00:00:02Z")
            loaded = json.loads(json.dumps(review, sort_keys=True))

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertIn("draft_reviews", loaded)
        self.assertIn("boundaries", loaded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
