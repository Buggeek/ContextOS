#!/usr/bin/env python3
"""Tests for read-only Builder draft promotion preflight."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


BUILDER_ROOT = Path(__file__).resolve().parent
if str(BUILDER_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILDER_ROOT))

from builder_engine.draft_approval_decision import BuilderDraftApprovalDecisionEngine  # noqa: E402
from builder_engine.draft_promotion_preflight import (  # noqa: E402
    BuilderDraftPromotionPreflightEngine,
    SCHEMA,
    render_human,
    write_json_report,
)
from test_builder_draft_approval_decision import BuilderDraftApprovalDecisionTestCase  # noqa: E402


def file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


class BuilderDraftPromotionPreflightTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        case = BuilderDraftApprovalDecisionTestCase(methodName="run")
        return case.make_repo()

    def create_approval_decision(self, root: Path, output_root: Path) -> tuple[dict, dict]:
        case = BuilderDraftApprovalDecisionTestCase(methodName="run")
        review_decision, _result, target = case.create_review_decision(root, output_root)
        approval = BuilderDraftApprovalDecisionEngine(root).run(
            review_decision,
            outcome="approved_for_promotion_proposal",
            approved_by="Jane Product Owner",
            approver_role="Product Owner",
            approver_authority_level="L3",
            approver_capability="builder.draft.approve",
            approval_scope="draft_for_future_promotion_proposal",
            approver_rationale="The reviewed draft may be used as input to a separate promotion proposal.",
            source_mission_id=review_decision["source"]["mission_id"],
            generated_at="2026-08-11T00:00:04Z",
        )
        self.assertTrue(approval["result"]["success"])
        return approval, target

    def test_promotion_preflight_is_eligible_but_not_authorized(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            approval, _target = self.create_approval_decision(root, Path(output_temp))
            before = file_snapshot(root)
            preflight = BuilderDraftPromotionPreflightEngine(root).run(
                approval,
                canonical_policy="governed_replacement_review",
                generated_at="2026-08-11T00:00:05Z",
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(preflight["schema"], SCHEMA)
        self.assertTrue(preflight["read_only"])
        self.assertTrue(preflight["result"]["success"])
        self.assertTrue(preflight["eligibility"]["eligible_for_promotion"])
        self.assertFalse(preflight["eligibility"]["promotion_authorized"])
        self.assertFalse(preflight["eligibility"]["canonical_mutation_authorized"])
        self.assertFalse(preflight["boundaries"]["ssot_writes_performed"])
        self.assertEqual(preflight["canonical_write_set"]["items"][0]["action_type"], "propose_governed_replacement_candidate")

    def test_create_only_policy_blocks_existing_canonical_target(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            approval, _target = self.create_approval_decision(root, Path(output_temp))
            preflight = BuilderDraftPromotionPreflightEngine(root).run(
                approval,
                canonical_policy="create_only",
                generated_at="2026-08-11T00:00:05Z",
            )

        self.assertFalse(preflight["result"]["success"])
        self.assertIn(
            "draft_promotion_preflight.check.no_overwrite_or_replacement_policy_satisfied",
            preflight["eligibility"]["failed_checks"],
        )

    def test_draft_drift_blocks_promotion_preflight(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            approval, target = self.create_approval_decision(root, Path(output_temp))
            draft_path = root / target["draft_workspace_target_path"]
            draft_path.write_text(draft_path.read_text(encoding="utf-8") + "\nChanged after approval.\n", encoding="utf-8")
            preflight = BuilderDraftPromotionPreflightEngine(root).run(
                approval,
                canonical_policy="governed_replacement_review",
                generated_at="2026-08-11T00:00:05Z",
            )

        self.assertFalse(preflight["result"]["success"])
        self.assertIn("draft_promotion_preflight.check.draft_hash_unchanged_since_approval", preflight["eligibility"]["failed_checks"])

    def test_canonical_target_drift_blocks_promotion_preflight(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            approval, _target = self.create_approval_decision(root, Path(output_temp))
            canonical_path = root / approval["draft"]["target_context_artifact"]
            canonical_path.write_text(canonical_path.read_text(encoding="utf-8") + "\nChanged after approval.\n", encoding="utf-8")
            preflight = BuilderDraftPromotionPreflightEngine(root).run(
                approval,
                canonical_policy="governed_replacement_review",
                generated_at="2026-08-11T00:00:05Z",
            )

        self.assertFalse(preflight["result"]["success"])
        self.assertIn(
            "draft_promotion_preflight.check.target_canonical_state_unchanged_since_approval",
            preflight["eligibility"]["failed_checks"],
        )

    def test_non_approved_decision_blocks_preflight(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            case = BuilderDraftApprovalDecisionTestCase(methodName="run")
            review_decision, _result, _target = case.create_review_decision(root, Path(output_temp))
            approval = BuilderDraftApprovalDecisionEngine(root).run(
                review_decision,
                outcome="approval_deferred",
                approved_by="Jane Product Owner",
                approver_role="Product Owner",
                approver_authority_level="L3",
                approver_capability="builder.draft.approve",
                approval_scope="draft_for_future_promotion_proposal",
                approver_rationale="Need more evidence.",
                source_mission_id=review_decision["source"]["mission_id"],
                generated_at="2026-08-11T00:00:04Z",
            )
            preflight = BuilderDraftPromotionPreflightEngine(root).run(
                approval,
                canonical_policy="governed_replacement_review",
                generated_at="2026-08-11T00:00:05Z",
            )

        self.assertTrue(approval["result"]["success"])
        self.assertFalse(preflight["result"]["success"])
        self.assertIn("draft_promotion_preflight.check.approval_successful", preflight["eligibility"]["failed_checks"])
        self.assertIn("draft_promotion_preflight.check.approved_for_promotion_proposal", preflight["eligibility"]["failed_checks"])

    def test_persisted_promotion_preflight_is_json_and_non_mutating(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            output_root = Path(output_temp)
            approval, _target = self.create_approval_decision(root, output_root)
            before = file_snapshot(root)
            preflight = BuilderDraftPromotionPreflightEngine(root).run(
                approval,
                canonical_policy="governed_replacement_review",
                generated_at="2026-08-11T00:00:05Z",
            )
            preflight_path = output_root / "promotion-preflight.json"
            write_json_report(preflight_path, preflight)
            loaded = json.loads(preflight_path.read_text(encoding="utf-8"))
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertFalse(loaded["eligibility"]["promotion_authorized"])
        self.assertFalse(loaded["eligibility"]["canonical_mutation_authorized"])

    def test_human_report_names_preflight_boundaries(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            approval, _target = self.create_approval_decision(root, Path(output_temp))
            preflight = BuilderDraftPromotionPreflightEngine(root).run(
                approval,
                canonical_policy="governed_replacement_review",
                generated_at="2026-08-11T00:00:05Z",
            )
            human = render_human(preflight)

        self.assertIn("# Context OS Draft Promotion Preflight", human)
        self.assertIn("Approved is not promoted.", human)
        self.assertIn("This preflight performs no promotion, SSOT write, or canonical mutation.", human)
        self.assertIn("Promotion authorized: no", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
