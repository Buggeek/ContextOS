#!/usr/bin/env python3
"""Tests for governed Builder draft approval decisions."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


BUILDER_ROOT = Path(__file__).resolve().parent
if str(BUILDER_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILDER_ROOT))

from builder_engine.draft_approval_decision import (  # noqa: E402
    ALLOWED_OUTCOMES,
    BuilderDraftApprovalDecisionEngine,
    SCHEMA,
    render_human,
    write_json_report,
)
from builder_engine.draft_create import BuilderDraftCreateEngine  # noqa: E402
from builder_engine.draft_review import BuilderDraftReviewEngine  # noqa: E402
from builder_engine.draft_review_decision import BuilderDraftReviewDecisionEngine  # noqa: E402
from test_builder_draft_create import copy_contextos_repo, eligible_preflight, write_json  # noqa: E402


def file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


class BuilderDraftApprovalDecisionTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        copy_contextos_repo(Path(temp.name) / "repo")
        return temp

    def create_review_decision(self, root: Path, output_root: Path, *, review_outcome: str = "reviewed_ready_for_next_governance_step") -> tuple[dict, dict, dict]:
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
        decision = BuilderDraftReviewDecisionEngine(root).run(
            review,
            outcome=review_outcome,
            reviewed_by="Jane Product Owner",
            reviewer_role="Product Owner",
            reviewer_authority_level="L2",
            reviewer_capability="builder.draft.review",
            reviewer_rationale="The draft envelope preserves evidence for approval review.",
            source_mission_id=review["source_write_result"]["authorization"]["authorized_mission_id"],
            generated_at="2026-08-11T00:00:03Z",
        )
        self.assertTrue(result["result"]["success"])
        self.assertTrue(review["result"]["success"])
        self.assertTrue(decision["result"]["success"])
        return decision, result, target

    def approval_kwargs(self, review_decision: dict) -> dict:
        return {
            "outcome": "approved_for_promotion_proposal",
            "approved_by": "Jane Product Owner",
            "approver_role": "Product Owner",
            "approver_authority_level": "L3",
            "approver_capability": "builder.draft.approve",
            "approval_scope": "draft_for_future_promotion_proposal",
            "approver_rationale": "The reviewed draft may be used as input to a separate promotion proposal.",
            "source_mission_id": review_decision["source"]["mission_id"],
        }

    def test_approval_decision_records_approval_without_promotion_or_canonical_truth(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review_decision, _result, _target = self.create_review_decision(root, Path(output_temp))
            before = file_snapshot(root)
            approval = BuilderDraftApprovalDecisionEngine(root).run(
                review_decision,
                generated_at="2026-08-11T00:00:04Z",
                **self.approval_kwargs(review_decision),
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(approval["schema"], SCHEMA)
        self.assertTrue(approval["result"]["success"])
        self.assertEqual(approval["result"]["state"], "approval_decision_recorded")
        self.assertTrue(approval["approval"]["approval_granted"])
        self.assertTrue(approval["promotion"]["eligible_for_future_promotion_proposal"])
        self.assertFalse(approval["promotion"]["promotion_authorized"])
        self.assertFalse(approval["approval"]["canonical"])
        self.assertFalse(approval["draft"]["canonical"])
        self.assertFalse(approval["constraints"]["ssot_writes_performed"])
        self.assertFalse(approval["constraints"]["canonical_context_writes_performed"])
        self.assertFalse(approval["constraints"]["drafts_mutated"])

    def test_allowed_approval_outcomes_preserve_promotion_boundary(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review_decision, _result, _target = self.create_review_decision(root, Path(output_temp))

            for outcome in ALLOWED_OUTCOMES:
                with self.subTest(outcome=outcome):
                    kwargs = self.approval_kwargs(review_decision)
                    kwargs["outcome"] = outcome
                    approval = BuilderDraftApprovalDecisionEngine(root).run(
                        review_decision,
                        generated_at="2026-08-11T00:00:04Z",
                        **kwargs,
                    )
                    self.assertTrue(approval["result"]["success"])
                    self.assertIn("next_permitted_transition", approval["approval"])
                    self.assertFalse(approval["promotion"]["promotion_authorized"])
                    self.assertFalse(approval["approval"]["canonical"])

    def test_only_eligible_review_decision_outcome_can_be_approved(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review_decision, _result, _target = self.create_review_decision(root, Path(output_temp), review_outcome="changes_requested")
            approval = BuilderDraftApprovalDecisionEngine(root).run(
                review_decision,
                generated_at="2026-08-11T00:00:04Z",
                **self.approval_kwargs(review_decision),
            )

        self.assertFalse(approval["result"]["success"])
        self.assertFalse(approval["approval"]["approval_granted"])
        self.assertIn("draft_approval_decision.check.review_outcome_eligible", approval["result"]["failed_checks"])

    def test_requires_explicit_l3_approval_authority(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review_decision, _result, _target = self.create_review_decision(root, Path(output_temp))
            kwargs = self.approval_kwargs(review_decision)
            kwargs["approver_authority_level"] = "L2"
            approval = BuilderDraftApprovalDecisionEngine(root).run(
                review_decision,
                generated_at="2026-08-11T00:00:04Z",
                **kwargs,
            )

        self.assertFalse(approval["result"]["success"])
        self.assertIn("draft_approval_decision.check.explicit_l3_approval_authority", approval["result"]["failed_checks"])

    def test_role_mismatch_blocks_approval(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review_decision, _result, _target = self.create_review_decision(root, Path(output_temp))
            kwargs = self.approval_kwargs(review_decision)
            kwargs["approver_role"] = "Observer"
            approval = BuilderDraftApprovalDecisionEngine(root).run(
                review_decision,
                generated_at="2026-08-11T00:00:04Z",
                **kwargs,
            )

        self.assertFalse(approval["result"]["success"])
        self.assertIn("draft_approval_decision.check.approver_role_satisfies_required_roles", approval["result"]["failed_checks"])

    def test_changed_draft_blocks_and_invalidates_approval(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review_decision, _result, target = self.create_review_decision(root, Path(output_temp))
            engine = BuilderDraftApprovalDecisionEngine(root)
            approval = engine.run(review_decision, generated_at="2026-08-11T00:00:04Z", **self.approval_kwargs(review_decision))
            draft_path = root / target["draft_workspace_target_path"]
            draft_path.write_text(draft_path.read_text(encoding="utf-8") + "\nHuman edit after approval.\n", encoding="utf-8")
            blocked = engine.run(review_decision, generated_at="2026-08-11T00:00:05Z", **self.approval_kwargs(review_decision))
            invalidation = engine.check_invalidation(approval, review_decision)

        self.assertTrue(approval["result"]["success"])
        self.assertFalse(blocked["result"]["success"])
        self.assertIn("draft_approval_decision.check.draft_hash_unchanged", blocked["result"]["failed_checks"])
        self.assertTrue(invalidation["invalidated"])
        self.assertIn("draft_approval_decision.invalidation.draft_content_hash_unchanged", invalidation["failed_checks"])

    def test_persisted_approval_decision_is_json_and_not_draft_mutation(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            output_root = Path(output_temp)
            review_decision, _result, target = self.create_review_decision(root, output_root)
            draft_before = (root / target["draft_workspace_target_path"]).read_text(encoding="utf-8")
            approval = BuilderDraftApprovalDecisionEngine(root).run(
                review_decision,
                generated_at="2026-08-11T00:00:04Z",
                **self.approval_kwargs(review_decision),
            )
            approval_path = output_root / "approval-decision.json"
            write_json_report(approval_path, approval)
            loaded = json.loads(approval_path.read_text(encoding="utf-8"))
            draft_after = (root / target["draft_workspace_target_path"]).read_text(encoding="utf-8")

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertEqual(draft_before, draft_after)
        self.assertFalse(loaded["approval"]["canonical"])
        self.assertFalse(loaded["promotion"]["promotion_authorized"])

    def test_human_report_names_approval_not_promotion_boundary(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            review_decision, _result, _target = self.create_review_decision(root, Path(output_temp))
            approval = BuilderDraftApprovalDecisionEngine(root).run(
                review_decision,
                generated_at="2026-08-11T00:00:04Z",
                **self.approval_kwargs(review_decision),
            )
            human = render_human(approval)

        self.assertIn("# Context OS Draft Approval Decision", human)
        self.assertIn("Approval Decision is not promotion.", human)
        self.assertIn("Draft remains non-canonical organizational context.", human)
        self.assertIn("Promotion authorized: no", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
