#!/usr/bin/env python3
"""Tests for governed create-only Builder draft writes."""

from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


BUILDER_ROOT = Path(__file__).resolve().parent
REPO_ROOT = BUILDER_ROOT.parents[1]
if str(BUILDER_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILDER_ROOT))

from builder_engine.draft_create import BuilderDraftCreateEngine, SCHEMA  # noqa: E402
from builder_engine.draft_workspace import DraftWorkspaceRuntime, preflight_id, preflight_payload, stable_hash  # noqa: E402


CREATE_MISSION_ID = "V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001"


def copy_contextos_repo(destination: Path) -> None:
    def ignore(_dir: str, names: list[str]) -> set[str]:
        ignored = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".DS_Store"}
        return {name for name in names if name in ignored}

    shutil.copytree(REPO_ROOT, destination, ignore=ignore)


def file_snapshot(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def eligible_preflight(root: Path, target_artifact: str = "SSOT/P.1_Product_Map.md") -> dict:
    preflight = DraftWorkspaceRuntime(root).run(mission_id=CREATE_MISSION_ID, generated_at="2026-08-11T00:00:00Z")
    preflight = copy.deepcopy(preflight)
    selected = None
    for target in preflight["targets"]:
        if target["target_context_artifact"] == target_artifact:
            selected = target
            target["status"] = "eligible"
            target["failed_checks"] = []
            for check in target["checks"]:
                check["passed"] = True
            target["authority_required"]["role"] = "Product Owner"
            target["authority_required"]["authority_level"] = "L2"
            target["truth_boundaries"]["unknowns_preserved"] = ["semantic completeness", "human-approved truth status"]
            target["truth_boundaries"]["missing_evidence_preserved"] = ["human-authored draft source"]
            target["truth_boundaries"]["contradictions_preserved"] = []
        else:
            target["status"] = "eligible"
            target["failed_checks"] = []
            for check in target["checks"]:
                check["passed"] = True
            target["authority_required"]["role"] = "Product Owner"
            target["authority_required"]["authority_level"] = "L2"
            target["truth_boundaries"]["contradictions_preserved"] = []
    if selected is None:
        raise AssertionError(f"Missing target artifact in preflight: {target_artifact}")
    preflight["eligibility"]["eligible_for_future_draft_creation"] = True
    preflight["eligibility"]["eligible_target_count"] = len(preflight["targets"])
    preflight["eligibility"]["ineligible_target_count"] = 0
    preflight["eligibility"]["ineligible_targets"] = []
    preflight["eligibility"]["failed_check_count"] = 0
    preflight["eligibility"]["failed_checks"] = []
    preflight["source_plan"]["identity_bound"] = True
    preflight["source_plan"]["fresh_hash"] = preflight["source_plan"]["hash"]
    for group in ("workspace_checks", "drift_checks", "validator_checks"):
        for check in preflight["validation"][group]:
            check["passed"] = True
    preflight["id"] = preflight_id(preflight)
    preflight["identity_hash"] = stable_hash(preflight_payload(preflight))
    return preflight


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class BuilderDraftCreateTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        copy_contextos_repo(Path(temp.name) / "repo")
        return temp

    def auth_kwargs(self, preflight: dict, target: dict) -> dict:
        return {
            "confirm_create": True,
            "authorized_by": "Jane Product Owner",
            "authorized_role": "Product Owner",
            "authorized_authority_level": "L2",
            "authorized_capability": "builder.draft.create",
            "authorized_mission_id": preflight["mission"]["id"],
            "authorized_preflight_id": preflight["id"],
            "authorized_preflight_hash": preflight["identity_hash"],
            "authorized_builder_draft_plan_hash": preflight["source_plan"]["hash"],
            "authorized_draft_item_ids": [target["draft_item_id"]],
            "authorized_target_paths": [target["draft_workspace_target_path"]],
        }

    def preflight_and_target(self, root: Path) -> tuple[dict, dict]:
        preflight = eligible_preflight(root)
        target = next(target for target in preflight["targets"] if target["target_context_artifact"] == "SSOT/P.1_Product_Map.md")
        return preflight, target

    def test_create_only_draft_write_preserves_non_canonical_metadata(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight, target = self.preflight_and_target(root)
            preflight_path = Path(output_temp) / "preflight.json"
            write_json(preflight_path, preflight)
            before = file_snapshot(root)
            result = BuilderDraftCreateEngine(root).run(
                preflight,
                preflight_ref=str(preflight_path),
                generated_at="2026-08-11T00:00:01Z",
                **self.auth_kwargs(preflight, target),
            )
            after = file_snapshot(root)
            draft_path = root / target["draft_workspace_target_path"]
            content = draft_path.read_text(encoding="utf-8")

        self.assertEqual(result["schema"], SCHEMA)
        self.assertTrue(result["result"]["success"])
        self.assertEqual(result["result"]["state"], "created_validated")
        self.assertIn(target["draft_workspace_target_path"], after - before)
        self.assertTrue(target["draft_workspace_target_path"].startswith(".contextos/drafts/"))
        self.assertIn("Non-canonical draft", content)
        self.assertIn('"lifecycle_state": "draft"', content)
        self.assertIn('"canonical": false', content)
        self.assertIn('"promotion_authorized": false', content)
        self.assertIn('"source_preflight_id"', content)
        self.assertFalse(result["constraints"]["ssot_writes_performed"])
        self.assertFalse(result["constraints"]["promotion_performed"])
        self.assertEqual(result["validation"]["post_write_validator"]["summary"]["error"], 0)

    def test_requires_explicit_l2_authorization(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight, target = self.preflight_and_target(root)
            preflight_path = Path(output_temp) / "preflight.json"
            write_json(preflight_path, preflight)
            kwargs = self.auth_kwargs(preflight, target)
            kwargs["authorized_authority_level"] = "L1"
            with self.assertRaisesRegex(ValueError, "L2 authority"):
                BuilderDraftCreateEngine(root).run(preflight, preflight_ref=str(preflight_path), **kwargs)

    def test_authorization_must_bind_exact_preflight_and_targets(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight, target = self.preflight_and_target(root)
            preflight_path = Path(output_temp) / "preflight.json"
            write_json(preflight_path, preflight)
            kwargs = self.auth_kwargs(preflight, target)
            kwargs["authorized_preflight_id"] = "wrong"
            result = BuilderDraftCreateEngine(root).run(preflight, preflight_ref=str(preflight_path), **kwargs)

        self.assertFalse(result["result"]["success"])
        self.assertEqual(result["result"]["state"], "blocked")
        self.assertIn("draft_write.check.authorization_bound_to_preflight", result["result"]["failed_pre_checks"])

    def test_no_overwrite_and_repeated_execution_blocks(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight, target = self.preflight_and_target(root)
            preflight_path = Path(output_temp) / "preflight.json"
            write_json(preflight_path, preflight)
            kwargs = self.auth_kwargs(preflight, target)
            first = BuilderDraftCreateEngine(root).run(preflight, preflight_ref=str(preflight_path), **kwargs)
            second = BuilderDraftCreateEngine(root).run(preflight, preflight_ref=str(preflight_path), **kwargs)

        self.assertTrue(first["result"]["success"])
        self.assertFalse(second["result"]["success"])
        self.assertIn("draft_write.check.no_overwrite_current_state", second["result"]["failed_pre_checks"])

    def test_preflight_ineligible_blocks_without_mutation(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight, target = self.preflight_and_target(root)
            preflight["eligibility"]["eligible_for_future_draft_creation"] = False
            preflight["eligibility"]["failed_checks"] = ["drift.check.draft_plan_identity_bound"]
            preflight["eligibility"]["failed_check_count"] = 1
            preflight["id"] = preflight_id(preflight)
            preflight["identity_hash"] = stable_hash(preflight_payload(preflight))
            preflight_path = Path(output_temp) / "preflight.json"
            write_json(preflight_path, preflight)
            before = file_snapshot(root)
            result = BuilderDraftCreateEngine(root).run(
                preflight,
                preflight_ref=str(preflight_path),
                **self.auth_kwargs(preflight, target),
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertFalse(result["result"]["success"])
        self.assertIn("draft_write.check.preflight_eligible", result["result"]["failed_pre_checks"])

    def test_rollback_removes_only_created_draft_when_hash_matches(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight, target = self.preflight_and_target(root)
            preflight_path = Path(output_temp) / "preflight.json"
            write_json(preflight_path, preflight)
            result = BuilderDraftCreateEngine(root).run(
                preflight,
                preflight_ref=str(preflight_path),
                **self.auth_kwargs(preflight, target),
            )
            rollback = BuilderDraftCreateEngine(root).rollback(result)

            self.assertTrue(result["result"]["success"])
            self.assertIn(target["draft_workspace_target_path"], {item["target_path"] for item in rollback["removed"]})
            self.assertFalse((root / target["draft_workspace_target_path"]).exists())
            self.assertTrue((root / "SSOT" / "P.1_Product_Map.md").exists())
            self.assertFalse(rollback["constraints"]["ssot_removed"])

    def test_rollback_does_not_remove_user_modified_draft(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight, target = self.preflight_and_target(root)
            preflight_path = Path(output_temp) / "preflight.json"
            write_json(preflight_path, preflight)
            result = BuilderDraftCreateEngine(root).run(
                preflight,
                preflight_ref=str(preflight_path),
                **self.auth_kwargs(preflight, target),
            )
            (root / target["draft_workspace_target_path"]).write_text("user changed\n", encoding="utf-8")
            rollback = BuilderDraftCreateEngine(root).rollback(result)

            self.assertTrue((root / target["draft_workspace_target_path"]).exists())
            self.assertIn("current_hash_changed", {item["reason"] for item in rollback["skipped"]})


if __name__ == "__main__":
    unittest.main(verbosity=2)
