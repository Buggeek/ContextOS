#!/usr/bin/env python3
"""Tests for Context OS Bootstrap Apply Preflight."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bootstrap_engine.acceptance_engine import BootstrapApprovalAcceptanceEngine
from bootstrap_engine.approval_engine import BootstrapApprovalRecordEngine
from bootstrap_engine.plan_engine import BootstrapPlanEngine
from bootstrap_engine.preflight_engine import BootstrapApplyPreflightEngine, SCHEMA
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


class BootstrapApplyPreflightTestCase(unittest.TestCase):
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

    def accepted_for(self, root: Path, output_root: Path) -> tuple[dict, Path]:
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
        return accepted, accepted_path

    def test_preflight_shape_eligibility_and_read_only_constraints(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            before = file_snapshot(root)
            accepted, accepted_path = self.accepted_for(root, Path(output_temp))
            report = BootstrapApplyPreflightEngine(root).run(
                accepted,
                accepted_decision_ref=str(accepted_path),
                generated_at="2026-08-11T00:00:04Z",
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertTrue(report["read_only"])
        self.assertTrue(report["eligibility"]["eligible_for_apply"])
        self.assertFalse(report["eligibility"]["apply_authorized"])
        self.assertFalse(report["constraints"]["writes_performed"])
        self.assertGreater(report["frozen_mutation_set"]["count"], 0)

    def test_preflight_freezes_exact_mutation_set(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            accepted, accepted_path = self.accepted_for(Path(temp), Path(output_temp))
            report = BootstrapApplyPreflightEngine(temp).run(accepted, accepted_decision_ref=str(accepted_path))

        actions = report["frozen_mutation_set"]["actions"]
        self.assertEqual(report["frozen_mutation_set"]["count"], len(actions))
        self.assertTrue(all(action["class"] in {"automatic", "approval_required"} for action in actions))
        self.assertTrue(all(action["no_overwrite"]["satisfied"] for action in actions))
        self.assertTrue(all(action["rollback_strategy"] == "delete_created" for action in actions))
        self.assertIn("hash", report["frozen_mutation_set"])

    def test_drift_makes_preflight_ineligible(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            accepted, accepted_path = self.accepted_for(root, Path(output_temp))
            write(root / ".contextos" / "manifest.yaml", "schema: contextos.runtime.manifest/1\n")
            report = BootstrapApplyPreflightEngine(root).run(accepted, accepted_decision_ref=str(accepted_path))

        self.assertFalse(report["eligibility"]["eligible_for_apply"])
        self.assertIn("preflight.check.no_drift", report["eligibility"]["failed_checks"])

    def test_tampered_accepted_decision_makes_preflight_ineligible(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            accepted, accepted_path = self.accepted_for(Path(temp), Path(output_temp))
            accepted["authority"]["accepted_role"] = "Observer"
            report = BootstrapApplyPreflightEngine(temp).run(accepted, accepted_decision_ref=str(accepted_path))

        self.assertFalse(report["eligibility"]["eligible_for_apply"])
        self.assertIn("preflight.check.accepted_decision_identity_valid", report["eligibility"]["failed_checks"])

    def test_json_report_is_serializable(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            accepted, accepted_path = self.accepted_for(Path(temp), Path(output_temp))
            report = BootstrapApplyPreflightEngine(temp).run(accepted, accepted_decision_ref=str(accepted_path))
            loaded = json.loads(json.dumps(report, sort_keys=True))

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertIn("frozen_mutation_set", loaded)
        self.assertIn("eligibility", loaded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
