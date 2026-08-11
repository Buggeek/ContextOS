#!/usr/bin/env python3
"""Tests for Context OS Bootstrap Approval Record Drafts."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bootstrap_engine.approval_engine import BootstrapApprovalRecordEngine, SCHEMA
from bootstrap_engine.plan_engine import BootstrapPlanEngine
from bootstrap_engine.proposal_engine import BootstrapProposalEngine


def write(path: Path, text: str = "# Test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_snapshot(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


class BootstrapApprovalRecordTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md")
        write(root / "SSOT" / "S.1_Vision.md")
        return temp

    def proposal_for(self, root: Path) -> dict:
        plan = BootstrapPlanEngine(root).run(generated_at="2026-08-11T00:00:00Z")
        return BootstrapProposalEngine(root).run(plan, generated_at="2026-08-11T00:00:01Z")

    def test_approval_record_shape_and_read_only_constraints(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            proposal = self.proposal_for(root)
            before = file_snapshot(root)
            record = BootstrapApprovalRecordEngine(root).run(
                proposal,
                generated_at="2026-08-11T00:00:02Z",
                approver_candidates=["Test Owner"],
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(record["schema"], SCHEMA)
        self.assertTrue(record["read_only"])
        self.assertEqual(record["decision"]["status"], "draft")
        self.assertEqual(record["decision"]["decision_kind"], "pending")
        self.assertFalse(record["decision"]["approved"])
        self.assertFalse(record["decision"]["apply_authorized"])
        self.assertFalse(record["constraints"]["approval_implied"])
        self.assertFalse(record["constraints"]["apply_authorized"])
        self.assertTrue(record["constraints"]["human_authority_required"])

    def test_record_binds_proposal_identity_and_decision_draft(self) -> None:
        proposal = self.proposal_for(Path("."))
        record = BootstrapApprovalRecordEngine(".").run(
            proposal,
            approver_candidates=["Context OS Maintainers"],
            rationale="Review exact proposal before apply.",
        )

        self.assertEqual(record["proposal"]["id"], proposal["id"])
        self.assertEqual(record["proposal"]["identity_hash"], proposal["identity_hash"])
        self.assertEqual(record["proposal"]["source_plan_hash"], proposal["source_plan"]["plan_hash"])
        self.assertEqual(record["decision"]["decision_record_draft"]["schema"], "contextos.decision/1")
        self.assertEqual(record["decision"]["decision_record_draft"]["proposal_id"], proposal["id"])
        self.assertIn(proposal["identity_hash"], record["decision"]["decision_record_draft"]["links"])

    def test_record_is_deterministic_for_same_proposal_and_authority_inputs(self) -> None:
        proposal = self.proposal_for(Path("."))
        first = BootstrapApprovalRecordEngine(".").run(
            proposal,
            generated_at="2026-08-11T00:00:02Z",
            approver_candidates=["Context OS Maintainers"],
        )
        second = BootstrapApprovalRecordEngine(".").run(
            proposal,
            generated_at="2026-08-11T00:00:03Z",
            approver_candidates=["Context OS Maintainers"],
        )

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["identity_hash"], second["identity_hash"])

    def test_drift_blocks_approval_record(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            proposal = self.proposal_for(root)
            write(root / ".contextos" / "manifest.yaml", "schema: contextos.runtime.manifest/1\n")

            record = BootstrapApprovalRecordEngine(root).run(proposal)

        self.assertTrue(record["drift"]["invalidated"])
        blocker_ids = {blocker["id"] for blocker in record["blockers"]}
        self.assertIn("approval.blocker.proposal_drift", blocker_ids)

    def test_prohibited_actions_block_approval_record(self) -> None:
        proposal = self.proposal_for(Path("."))
        changed = copy.deepcopy(proposal)
        changed["actions"][0]["class"] = "prohibited"

        record = BootstrapApprovalRecordEngine(".").run(changed)

        blockers = {blocker["id"]: blocker for blocker in record["blockers"]}
        self.assertIn("approval.blocker.prohibited_actions", blockers)
        self.assertEqual(blockers["approval.blocker.prohibited_actions"]["severity"], "warn")

    def test_json_report_is_serializable(self) -> None:
        proposal = self.proposal_for(Path("."))
        record = BootstrapApprovalRecordEngine(".").run(proposal)
        loaded = json.loads(json.dumps(record, sort_keys=True))

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertIn("proposal", loaded)
        self.assertIn("decision", loaded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
