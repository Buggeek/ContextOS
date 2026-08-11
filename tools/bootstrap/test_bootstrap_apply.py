#!/usr/bin/env python3
"""Tests for governed create-only Context OS Bootstrap Apply."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bootstrap_engine.acceptance_engine import BootstrapApprovalAcceptanceEngine
from bootstrap_engine.apply_engine import BootstrapApplyEngine, SCHEMA
from bootstrap_engine.approval_engine import BootstrapApprovalRecordEngine
from bootstrap_engine.plan_engine import BootstrapPlanEngine
from bootstrap_engine.preflight_engine import BootstrapApplyPreflightEngine
from bootstrap_engine.proposal_engine import BootstrapProposalEngine


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ssot_doc(title: str) -> str:
    return f"""# {title}
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Test Owner

---

## Purpose

Test artifact.

## Change Log

- 2026-08-11 - v0.1.0 - Initial creation
"""


def file_snapshot(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


class BootstrapApplyTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for directory in ("docs", "SSOT", "ops", "templates"):
            (root / directory).mkdir(parents=True, exist_ok=True)
        write(root / "README.md", "# Test Repo\n")
        write(root / "ops" / "AGENT_RULES.md", "# Context OS Agent Rules\n")
        write(root / "docs" / "3.x_operation" / "3.6_COS_Human_Agent_Authority_Model.md", "# 3.6 Authority\n\nL0 L1 L2 L3 L4 L5\n")
        write(root / "SSOT" / "README.md", "# SSOT\n\nCompliance profile: `strict`\n")
        write(root / "SSOT" / "S.1_Vision.md", ssot_doc("S.1 Vision"))
        write(root / "SSOT" / "P.1_Product_Map.md", ssot_doc("P.1 Product Map"))
        write(root / "SSOT" / "A.1_System_Map.md", ssot_doc("A.1 System Map"))
        write(root / "SSOT" / "A.4_Data_Entities.md", ssot_doc("A.4 Data Entities"))
        write(root / "SSOT" / "G.1_Definition_of_Ready.md", ssot_doc("G.1 Definition of Ready"))
        write(root / "SSOT" / "G.2_Definition_of_Done.md", ssot_doc("G.2 Definition of Done"))
        return temp

    def preflight_for(self, root: Path, output_root: Path) -> tuple[dict, Path]:
        plan = BootstrapPlanEngine(root).run(generated_at="2026-08-11T00:00:00Z")
        proposal = BootstrapProposalEngine(root).run(plan, generated_at="2026-08-11T00:00:01Z")
        proposal_path = output_root / "proposal.json"
        proposal_path.write_text(json.dumps(proposal, indent=2, sort_keys=True), encoding="utf-8")
        approval = BootstrapApprovalRecordEngine(root).run(
            proposal,
            proposal_ref=str(proposal_path),
            generated_at="2026-08-11T00:00:02Z",
            approver_candidates=["Mission Owner"],
        )
        approval_path = output_root / "approval.json"
        approval_path.write_text(json.dumps(approval, indent=2, sort_keys=True), encoding="utf-8")
        accepted = BootstrapApprovalAcceptanceEngine(root).run(
            approval,
            approval_record_ref=str(approval_path),
            accepted_by="Jane Owner",
            accepted_role="Mission Owner",
            accepted_at="2026-08-11T00:00:03Z",
        )
        accepted_path = output_root / "accepted.json"
        accepted_path.write_text(json.dumps(accepted, indent=2, sort_keys=True), encoding="utf-8")
        preflight = BootstrapApplyPreflightEngine(root).run(
            accepted,
            accepted_decision_ref=str(accepted_path),
            generated_at="2026-08-11T00:00:04Z",
        )
        preflight_path = output_root / "preflight.json"
        preflight_path.write_text(json.dumps(preflight, indent=2, sort_keys=True), encoding="utf-8")
        return preflight, preflight_path

    def test_apply_creates_only_approved_artifacts_and_validates(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            before = file_snapshot(root)
            preflight, preflight_path = self.preflight_for(root, Path(output_temp))
            result = BootstrapApplyEngine(root).run(
                preflight,
                preflight_ref=str(preflight_path),
                confirm_apply=True,
                confirmed_by="Jane Owner",
                confirmed_role="Mission Owner",
                confirmed_preflight_id=preflight["id"],
                confirmed_preflight_hash=preflight["identity_hash"],
                generated_at="2026-08-11T00:00:05Z",
            )
            after = file_snapshot(root)

        self.assertEqual(result["schema"], SCHEMA)
        self.assertTrue(result["result"]["success"])
        self.assertEqual(result["result"]["state"], "applied_validated")
        self.assertEqual(result["mutation_set"]["count"], len(result["mutations"]))
        self.assertIn(".contextos/manifest.yaml", after - before)
        self.assertFalse(result["constraints"]["overwrites_performed"])
        self.assertFalse(result["constraints"]["deletions_performed"])
        self.assertEqual(result["validation"]["post_apply_validator"]["summary"]["error"], 0)

    def test_apply_requires_explicit_confirmation(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            preflight, preflight_path = self.preflight_for(Path(temp), Path(output_temp))
            with self.assertRaisesRegex(ValueError, "confirm-apply"):
                BootstrapApplyEngine(temp).run(
                    preflight,
                    preflight_ref=str(preflight_path),
                    confirm_apply=False,
                    confirmed_by="Jane Owner",
                    confirmed_role="Mission Owner",
                )

    def test_apply_requires_confirmation_bound_to_exact_preflight(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            preflight, preflight_path = self.preflight_for(Path(temp), Path(output_temp))
            with self.assertRaisesRegex(ValueError, "preflight id does not match"):
                BootstrapApplyEngine(temp).run(
                    preflight,
                    preflight_ref=str(preflight_path),
                    confirm_apply=True,
                    confirmed_by="Jane Owner",
                    confirmed_role="Mission Owner",
                    confirmed_preflight_id="wrong",
                    confirmed_preflight_hash=preflight["identity_hash"],
                )

    def test_repository_drift_before_apply_blocks_without_mutation(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            preflight, preflight_path = self.preflight_for(root, Path(output_temp))
            write(root / ".contextos" / "manifest.yaml", "user: content\n")
            before = file_snapshot(root)
            result = BootstrapApplyEngine(root).run(
                preflight,
                preflight_ref=str(preflight_path),
                confirm_apply=True,
                confirmed_by="Jane Owner",
                confirmed_role="Mission Owner",
                confirmed_preflight_id=preflight["id"],
                confirmed_preflight_hash=preflight["identity_hash"],
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertFalse(result["result"]["success"])
        self.assertEqual(result["result"]["state"], "blocked")
        self.assertIn("apply.check.no_overwrite_current_state", result["result"]["failed_pre_checks"])

    def test_repeated_execution_with_same_preflight_blocks(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            preflight, preflight_path = self.preflight_for(root, Path(output_temp))
            first = BootstrapApplyEngine(root).run(
                preflight,
                preflight_ref=str(preflight_path),
                confirm_apply=True,
                confirmed_by="Jane Owner",
                confirmed_role="Mission Owner",
                confirmed_preflight_id=preflight["id"],
                confirmed_preflight_hash=preflight["identity_hash"],
            )
            second = BootstrapApplyEngine(root).run(
                preflight,
                preflight_ref=str(preflight_path),
                confirm_apply=True,
                confirmed_by="Jane Owner",
                confirmed_role="Mission Owner",
                confirmed_preflight_id=preflight["id"],
                confirmed_preflight_hash=preflight["identity_hash"],
            )

        self.assertTrue(first["result"]["success"])
        self.assertFalse(second["result"]["success"])
        self.assertIn("apply.check.no_overwrite_current_state", second["result"]["failed_pre_checks"])

    def test_rollback_removes_only_created_artifacts_when_hash_matches(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            preflight, preflight_path = self.preflight_for(root, Path(output_temp))
            result = BootstrapApplyEngine(root).run(
                preflight,
                preflight_ref=str(preflight_path),
                confirm_apply=True,
                confirmed_by="Jane Owner",
                confirmed_role="Mission Owner",
                confirmed_preflight_id=preflight["id"],
                confirmed_preflight_hash=preflight["identity_hash"],
            )
            rollback = BootstrapApplyEngine(root).rollback(result)

            self.assertGreater(len(rollback["removed"]), 0)
            self.assertFalse((root / ".contextos" / "manifest.yaml").exists())
            self.assertTrue((root / "README.md").exists())

    def test_rollback_does_not_remove_user_modified_created_artifact(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            preflight, preflight_path = self.preflight_for(root, Path(output_temp))
            result = BootstrapApplyEngine(root).run(
                preflight,
                preflight_ref=str(preflight_path),
                confirm_apply=True,
                confirmed_by="Jane Owner",
                confirmed_role="Mission Owner",
                confirmed_preflight_id=preflight["id"],
                confirmed_preflight_hash=preflight["identity_hash"],
            )
            write(root / ".contextos" / "manifest.yaml", "user modified\n")
            rollback = BootstrapApplyEngine(root).rollback(result)

            self.assertTrue((root / ".contextos" / "manifest.yaml").exists())
            self.assertIn("current_hash_changed", {item["reason"] for item in rollback["skipped"]})


if __name__ == "__main__":
    unittest.main(verbosity=2)
