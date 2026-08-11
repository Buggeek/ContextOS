#!/usr/bin/env python3
"""Tests for governed Builder draft review decisions."""

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
from builder_engine.draft_review import BuilderDraftReviewEngine  # noqa: E402
from builder_engine.draft_review_decision import (  # noqa: E402
    ALLOWED_OUTCOMES,
    BuilderDraftReviewDecisionEngine,
    SCHEMA,
    render_human,
    write_json_report,
)
from test_builder_draft_create import copy_contextos_repo, eligible_preflight, write_json  # noqa: E402


def file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


class BuilderDraftReviewDecisionTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        copy_contextos_repo(Path(temp.name) / "repo")
        return temp

    def create_review(self, root: Path, output_root: Path) -> tuple[dict, dict, dict]:
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
        review = BuilderDraftReviewEngine(root).run(result, generated_at="2026-08-11T00:00:02Z")
        self.assertTrue(result["result"]["success"])
        self.assertTrue(review["result"]["success"])
        return review, result, target

    def decision_kwargs(self, review: dict) -> dict:
        return {
            "outcome": "reviewed_ready_for_next_governance_step",
            "reviewed_by": "Jane Product Owner",
            "reviewer_role": "Product Owner",
            "reviewer_authority_level": "L2",
            "reviewer_capability": "builder.draft.review",
            "reviewer_rationale": "The draft envelope preserves evidence and is ready for a separate governance step.",
            "source_mission_id": review["source_write_result"]["authorization"]["authorized_mission_id"],
        }

    def test_review_decision_records_non_canonical_human_outcome(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review, _result, _target = self.create_review(root, Path(output_temp))
            before = file_snapshot(root)
            decision = BuilderDraftReviewDecisionEngine(root).run(
                review,
                generated_at="2026-08-11T00:00:03Z",
                **self.decision_kwargs(review),
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(decision["schema"], SCHEMA)
        self.assertTrue(decision["result"]["success"])
        self.assertEqual(decision["result"]["state"], "review_decision_recorded")
        self.assertEqual(decision["reviewer"]["capability"], "builder.draft.review")
        self.assertTrue(decision["reviewer"]["role_satisfied"])
        self.assertEqual(decision["outcome"]["next_permitted_transition"], "approval_proposal_allowed")
        self.assertFalse(decision["outcome"]["approval_granted"])
        self.assertFalse(decision["outcome"]["promotion_granted"])
        self.assertFalse(decision["outcome"]["canonical_truth_created"])
        self.assertTrue(decision["outcome"]["draft_remains_non_canonical"])
        self.assertFalse(decision["constraints"]["drafts_mutated"])
        self.assertFalse(decision["constraints"]["ssot_writes_performed"])

    def test_allowed_outcomes_have_explicit_next_transition(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review, _result, _target = self.create_review(root, Path(output_temp))

            for outcome in ALLOWED_OUTCOMES:
                with self.subTest(outcome=outcome):
                    kwargs = self.decision_kwargs(review)
                    kwargs["outcome"] = outcome
                    decision = BuilderDraftReviewDecisionEngine(root).run(
                        review,
                        generated_at="2026-08-11T00:00:03Z",
                        **kwargs,
                    )
                    self.assertTrue(decision["result"]["success"])
                    self.assertIn("next_permitted_transition", decision["outcome"])
                    self.assertTrue(decision["outcome"]["review_is_not_approval"])

    def test_requires_explicit_l2_human_review_authority(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review, _result, _target = self.create_review(root, Path(output_temp))
            kwargs = self.decision_kwargs(review)
            kwargs["reviewer_authority_level"] = "L1"
            decision = BuilderDraftReviewDecisionEngine(root).run(
                review,
                generated_at="2026-08-11T00:00:03Z",
                **kwargs,
            )

        self.assertFalse(decision["result"]["success"])
        self.assertIn("draft_review_decision.check.explicit_l2_review_authority", decision["result"]["failed_checks"])

    def test_role_mismatch_blocks_decision(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review, _result, _target = self.create_review(root, Path(output_temp))
            kwargs = self.decision_kwargs(review)
            kwargs["reviewer_role"] = "Observer"
            decision = BuilderDraftReviewDecisionEngine(root).run(
                review,
                generated_at="2026-08-11T00:00:03Z",
                **kwargs,
            )

        self.assertFalse(decision["result"]["success"])
        self.assertIn(
            "draft_review_decision.check.reviewer_role_satisfies_required_roles",
            decision["result"]["failed_checks"],
        )

    def test_persisted_review_decision_is_json_and_not_draft_mutation(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            output_root = Path(output_temp)
            review, _result, target = self.create_review(root, output_root)
            draft_before = (root / target["draft_workspace_target_path"]).read_text(encoding="utf-8")
            decision = BuilderDraftReviewDecisionEngine(root).run(
                review,
                generated_at="2026-08-11T00:00:03Z",
                **self.decision_kwargs(review),
            )
            decision_path = output_root / "review-decision.json"
            write_json_report(decision_path, decision)
            loaded = json.loads(decision_path.read_text(encoding="utf-8"))
            draft_after = (root / target["draft_workspace_target_path"]).read_text(encoding="utf-8")

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertEqual(draft_before, draft_after)
        self.assertEqual(loaded["draft"]["content_hash"], decision["draft"]["content_hash"])

    def test_changed_draft_invalidates_previous_review_decision(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review, result, target = self.create_review(root, Path(output_temp))
            engine = BuilderDraftReviewDecisionEngine(root)
            decision = engine.run(review, generated_at="2026-08-11T00:00:03Z", **self.decision_kwargs(review))
            draft_path = root / target["draft_workspace_target_path"]
            draft_path.write_text(draft_path.read_text(encoding="utf-8") + "\nHuman edit after review.\n", encoding="utf-8")
            current_review = BuilderDraftReviewEngine(root).run(result, generated_at="2026-08-11T00:00:04Z")
            invalidation = engine.check_invalidation(decision, current_review)

        self.assertTrue(invalidation["invalidated"])
        self.assertIn(
            "draft_review_decision.invalidation.draft_content_hash_unchanged",
            invalidation["failed_checks"],
        )

    def test_human_report_names_review_not_approval_boundary(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review, _result, _target = self.create_review(root, Path(output_temp))
            decision = BuilderDraftReviewDecisionEngine(root).run(
                review,
                generated_at="2026-08-11T00:00:03Z",
                **self.decision_kwargs(review),
            )
            human = render_human(decision)

        self.assertIn("# Context OS Draft Review Decision", human)
        self.assertIn("Review decision is not approval.", human)
        self.assertIn("Draft remains non-canonical organizational context.", human)
        self.assertIn("Unknowns preserved:", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
