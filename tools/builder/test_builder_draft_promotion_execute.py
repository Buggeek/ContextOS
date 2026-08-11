#!/usr/bin/env python3
"""Tests for governed create-only Builder draft promotion."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


BUILDER_ROOT = Path(__file__).resolve().parent
if str(BUILDER_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILDER_ROOT))

from builder_engine.draft_approval_decision import approval_decision_id, approval_decision_payload  # noqa: E402
from builder_engine.draft_promotion_execute import BuilderDraftPromotionEngine, SCHEMA, render_human  # noqa: E402
from builder_engine.draft_promotion_preflight import BuilderDraftPromotionPreflightEngine  # noqa: E402
from builder_engine.draft_workspace import stable_hash  # noqa: E402
from test_builder_draft_promotion_preflight import BuilderDraftPromotionPreflightTestCase  # noqa: E402


PROMOTION_MISSION_ID = "V05-BUILDER-DRAFT-PROMOTION-EXECUTE-001"


def file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def retarget_approval_to_missing_canonical(approval: dict, target_path: str) -> dict:
    updated = copy.deepcopy(approval)
    updated["draft"]["target_context_artifact"] = target_path
    updated["evidence"]["repository_state"]["canonical_target_path"] = target_path
    updated["evidence"]["repository_state"]["canonical_target_state"] = {"exists": False, "kind": "missing", "hash": None}
    updated["id"] = approval_decision_id(updated)
    updated["identity_hash"] = stable_hash(approval_decision_payload(updated))
    return updated


class BuilderDraftPromotionExecuteTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        case = BuilderDraftPromotionPreflightTestCase(methodName="run")
        return case.make_repo()

    def create_existing_target_preflight(self, root: Path, output_root: Path) -> dict:
        case = BuilderDraftPromotionPreflightTestCase(methodName="run")
        approval, _target = case.create_approval_decision(root, output_root)
        return BuilderDraftPromotionPreflightEngine(root).run(
            approval,
            canonical_policy="governed_replacement_review",
            generated_at="2026-08-11T00:00:05Z",
        )

    def create_create_only_preflight(self, root: Path, output_root: Path) -> dict:
        case = BuilderDraftPromotionPreflightTestCase(methodName="run")
        approval, _target = case.create_approval_decision(root, output_root)
        approval = retarget_approval_to_missing_canonical(approval, "SSOT/P.9_New_Context.md")
        preflight = BuilderDraftPromotionPreflightEngine(root).run(
            approval,
            canonical_policy="create_only",
            generated_at="2026-08-11T00:00:05Z",
        )
        self.assertTrue(preflight["result"]["success"])
        self.assertEqual(preflight["canonical_write_set"]["items"][0]["action_type"], "create_canonical_candidate")
        return preflight

    def promotion_kwargs(self, preflight: dict) -> dict:
        item = preflight["canonical_write_set"]["items"][0]
        return {
            "confirm_promotion": True,
            "promoted_by": "Jane Product Owner",
            "promoter_role": "Product Owner",
            "promoter_authority_level": "L3",
            "promoter_capability": "builder.draft.promote",
            "promotion_mission_id": PROMOTION_MISSION_ID,
            "authorized_preflight_id": preflight["id"],
            "authorized_preflight_hash": preflight["identity_hash"],
            "authorized_approval_decision_id": preflight["approval_decision"]["id"],
            "authorized_approval_decision_hash": preflight["approval_decision"]["identity_hash"],
            "authorized_draft_item_id": item["draft_item_id"],
            "authorized_draft_content_hash": item["source_draft_hash"],
            "authorized_canonical_target_path": item["target_canonical_path"],
            "authorized_promotion_action": item["action_type"],
            "authorized_canonical_target_state_hash": preflight["canonical_target"]["current_state"]["hash"],
            "canonical_mutation_scope": "create_canonical_from_approved_draft",
        }

    def test_create_only_promotion_creates_canonical_artifact_and_validates(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.create_create_only_preflight(root, Path(output_temp))
            before = file_snapshot(root)
            result = BuilderDraftPromotionEngine(root).run(
                preflight,
                generated_at="2026-08-11T00:00:06Z",
                **self.promotion_kwargs(preflight),
            )
            after = file_snapshot(root)
            target_path = root / preflight["canonical_target"]["path"]
            content = target_path.read_text(encoding="utf-8")

        self.assertEqual(result["schema"], SCHEMA)
        self.assertTrue(result["result"]["success"])
        self.assertEqual(result["result"]["state"], "promoted_validated")
        self.assertIn(preflight["canonical_target"]["path"], set(after) - set(before))
        self.assertIn("contextos.builder.promoted_canonical_artifact/1", content)
        self.assertIn('"canonical": true', content)
        self.assertIn('"source_promotion_preflight_id"', content)
        self.assertIn('"source_approval_decision_id"', content)
        self.assertTrue(result["validation"]["canonical_validation_succeeded"])
        self.assertFalse(result["constraints"]["overwrites_performed"])
        self.assertFalse(result["constraints"]["replacements_performed"])
        self.assertFalse(result["constraints"]["unrelated_files_modified"])

    def test_requires_explicit_confirmation(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.create_create_only_preflight(root, Path(output_temp))
            kwargs = self.promotion_kwargs(preflight)
            kwargs["confirm_promotion"] = False
            with self.assertRaisesRegex(ValueError, "explicit human promotion confirmation"):
                BuilderDraftPromotionEngine(root).run(preflight, **kwargs)

    def test_confirmation_must_bind_exact_preflight_and_target(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.create_create_only_preflight(root, Path(output_temp))
            kwargs = self.promotion_kwargs(preflight)
            kwargs["authorized_preflight_hash"] = "wrong"
            result = BuilderDraftPromotionEngine(root).run(preflight, **kwargs)

        self.assertFalse(result["result"]["success"])
        self.assertIn("draft_promotion.check.confirmation_bound_to_preflight", result["result"]["failed_pre_checks"])

    def test_existing_canonical_target_blocks_without_overwrite(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.create_existing_target_preflight(root, Path(output_temp))
            before = file_snapshot(root)
            result = BuilderDraftPromotionEngine(root).run(
                preflight,
                generated_at="2026-08-11T00:00:06Z",
                **self.promotion_kwargs(preflight),
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertFalse(result["result"]["success"])
        self.assertIn("draft_promotion.check.action_is_create_canonical_candidate", result["result"]["failed_pre_checks"])
        self.assertIn("draft_promotion.check.no_existing_canonical_target", result["result"]["failed_pre_checks"])

    def test_repeated_execution_is_blocked_no_overwrite(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.create_create_only_preflight(root, Path(output_temp))
            kwargs = self.promotion_kwargs(preflight)
            first = BuilderDraftPromotionEngine(root).run(preflight, generated_at="2026-08-11T00:00:06Z", **kwargs)
            second = BuilderDraftPromotionEngine(root).run(preflight, generated_at="2026-08-11T00:00:07Z", **kwargs)

        self.assertTrue(first["result"]["success"])
        self.assertFalse(second["result"]["success"])
        self.assertIn("draft_promotion.check.no_existing_canonical_target", second["result"]["failed_pre_checks"])

    def test_draft_drift_blocks_without_mutation(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.create_create_only_preflight(root, Path(output_temp))
            draft_path = root / preflight["canonical_write_set"]["items"][0]["source_draft_path"]
            draft_path.write_text(draft_path.read_text(encoding="utf-8") + "\nChanged before promotion.\n", encoding="utf-8")
            before = file_snapshot(root)
            result = BuilderDraftPromotionEngine(root).run(
                preflight,
                generated_at="2026-08-11T00:00:06Z",
                **self.promotion_kwargs(preflight),
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertFalse(result["result"]["success"])
        self.assertIn("draft_promotion.check.draft_hash_still_matches_preflight", result["result"]["failed_pre_checks"])

    def test_rollback_removes_only_created_canonical_artifact_when_hash_matches(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.create_create_only_preflight(root, Path(output_temp))
            engine = BuilderDraftPromotionEngine(root)
            result = engine.run(preflight, generated_at="2026-08-11T00:00:06Z", **self.promotion_kwargs(preflight))
            rollback = engine.rollback(result)
            target_path = root / preflight["canonical_target"]["path"]

        self.assertTrue(result["result"]["success"])
        self.assertFalse(target_path.exists())
        self.assertIn(preflight["canonical_target"]["path"], {item["target_path"] for item in rollback["removed"]})
        self.assertFalse(rollback["constraints"]["removed_pre_existing_content"])

    def test_rollback_does_not_remove_user_modified_canonical_artifact(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.create_create_only_preflight(root, Path(output_temp))
            engine = BuilderDraftPromotionEngine(root)
            result = engine.run(preflight, generated_at="2026-08-11T00:00:06Z", **self.promotion_kwargs(preflight))
            target_path = root / preflight["canonical_target"]["path"]
            target_path.write_text(target_path.read_text(encoding="utf-8") + "\nUser change.\n", encoding="utf-8")
            rollback = engine.rollback(result)
            target_still_exists = target_path.exists()

        self.assertTrue(target_still_exists)
        self.assertIn("current_hash_changed", {item["reason"] for item in rollback["skipped"]})

    def test_human_report_names_canonical_boundary_and_rollback(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.create_create_only_preflight(root, Path(output_temp))
            result = BuilderDraftPromotionEngine(root).run(
                preflight,
                generated_at="2026-08-11T00:00:06Z",
                **self.promotion_kwargs(preflight),
            )
            human = render_human(result)

        self.assertIn("# Context OS Draft Promotion Result", human)
        self.assertIn("Approved is not canonical until promotion executes and validation succeeds.", human)
        self.assertIn("Rollback", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
