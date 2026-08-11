#!/usr/bin/env python3
"""Tests for explicit Context OS Bootstrap Approval Acceptance."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bootstrap_engine.acceptance_engine import BootstrapApprovalAcceptanceEngine, SCHEMA
from bootstrap_engine.approval_engine import BootstrapApprovalRecordEngine
from bootstrap_engine.plan_engine import BootstrapPlanEngine
from bootstrap_engine.proposal_engine import BootstrapProposalEngine


def write(path: Path, text: str = "# Test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_snapshot(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


class BootstrapApprovalAcceptanceTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md")
        write(root / "SSOT" / "S.1_Vision.md")
        return temp

    def proposal_and_record_for(self, root: Path, output_root: Path) -> tuple[dict, dict]:
        plan = BootstrapPlanEngine(root).run(generated_at="2026-08-11T00:00:00Z")
        proposal = BootstrapProposalEngine(root).run(plan, generated_at="2026-08-11T00:00:01Z")
        proposal_path = output_root / "proposal.json"
        proposal_path.write_text(json.dumps(proposal, indent=2, sort_keys=True), encoding="utf-8")
        record = BootstrapApprovalRecordEngine(root).run(
            proposal,
            proposal_ref=str(proposal_path),
            generated_at="2026-08-11T00:00:02Z",
            approver_candidates=["Mission Owner"],
        )
        return proposal, record

    def test_acceptance_shape_and_read_only_constraints(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            before = file_snapshot(root)
            _proposal, record = self.proposal_and_record_for(root, Path(output_temp))
            decision = BootstrapApprovalAcceptanceEngine(root).run(
                record,
                accepted_by="Jane Owner",
                accepted_role="Mission Owner",
                rationale="Approve the exact preserved bootstrap proposal.",
                accepted_at="2026-08-11T00:00:03Z",
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(decision["schema"], SCHEMA)
        self.assertTrue(decision["read_only"])
        self.assertEqual(decision["decision"]["status"], "accepted")
        self.assertTrue(decision["decision"]["approved"])
        self.assertFalse(decision["decision"]["apply_authorized"])
        self.assertFalse(decision["decision"]["repository_mutation_authorized"])
        self.assertFalse(decision["constraints"]["writes_performed"])
        self.assertFalse(decision["constraints"]["apply_authorized"])

    def test_acceptance_binds_proposal_approval_and_decision_record(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            proposal, record = self.proposal_and_record_for(Path(temp), Path(output_temp))
            decision = BootstrapApprovalAcceptanceEngine(temp).run(
                record,
                accepted_by="Jane Owner",
                accepted_role="Mission Owner",
                accepted_at="2026-08-11T00:00:03Z",
            )

        self.assertEqual(decision["proposal"]["id"], proposal["id"])
        self.assertEqual(decision["proposal"]["identity_hash"], proposal["identity_hash"])
        self.assertEqual(decision["approval_record"]["id"], record["id"])
        self.assertEqual(decision["approval_record"]["identity_hash"], record["identity_hash"])
        self.assertEqual(decision["decision"]["decision_record"]["schema"], "contextos.decision/1")
        self.assertEqual(decision["decision"]["decision_record"]["proposal_identity_hash"], proposal["identity_hash"])
        self.assertIn(record["identity_hash"], decision["decision"]["decision_record"]["links"])

    def test_acceptance_is_stable_for_same_human_decision_intent(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            _proposal, record = self.proposal_and_record_for(Path(temp), Path(output_temp))
            first = BootstrapApprovalAcceptanceEngine(temp).run(
                record,
                accepted_by="Jane Owner",
                accepted_role="Mission Owner",
                accepted_at="2026-08-11T00:00:03Z",
            )
            second = BootstrapApprovalAcceptanceEngine(temp).run(
                record,
                accepted_by="Jane Owner",
                accepted_role="Mission Owner",
                accepted_at="2026-08-11T00:00:04Z",
            )

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["identity_hash"], second["identity_hash"])

    def test_missing_human_identity_or_role_blocks_acceptance(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            _proposal, record = self.proposal_and_record_for(Path(temp), Path(output_temp))
            with self.assertRaises(ValueError):
                BootstrapApprovalAcceptanceEngine(temp).run(
                    record,
                    accepted_by="",
                    accepted_role="Mission Owner",
                )
            with self.assertRaises(ValueError):
                BootstrapApprovalAcceptanceEngine(temp).run(
                    record,
                    accepted_by="Jane Owner",
                    accepted_role="",
                )

    def test_role_mismatch_blocks_acceptance(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            _proposal, record = self.proposal_and_record_for(Path(temp), Path(output_temp))
            with self.assertRaisesRegex(ValueError, "approving_role_satisfies_required_authority"):
                BootstrapApprovalAcceptanceEngine(temp).run(
                    record,
                    accepted_by="Jane Owner",
                    accepted_role="Observer",
                )

    def test_tampered_approval_identity_blocks_acceptance(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            _proposal, record = self.proposal_and_record_for(Path(temp), Path(output_temp))
            record["authority"]["required_roles"] = ["Runtime Owner"]

            with self.assertRaisesRegex(ValueError, "approval_record_identity_valid"):
                BootstrapApprovalAcceptanceEngine(temp).run(
                    record,
                    accepted_by="Jane Owner",
                    accepted_role="Runtime Owner",
                )

    def test_drift_blocks_acceptance(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            _proposal, record = self.proposal_and_record_for(root, Path(output_temp))
            write(root / ".contextos" / "manifest.yaml", "schema: contextos.runtime.manifest/1\n")

            with self.assertRaisesRegex(ValueError, "no_drift"):
                BootstrapApprovalAcceptanceEngine(root).run(
                    record,
                    accepted_by="Jane Owner",
                    accepted_role="Mission Owner",
                )

    def test_json_report_is_serializable(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            _proposal, record = self.proposal_and_record_for(Path(temp), Path(output_temp))
            decision = BootstrapApprovalAcceptanceEngine(temp).run(
                record,
                accepted_by="Jane Owner",
                accepted_role="Mission Owner",
            )
            loaded = json.loads(json.dumps(decision, sort_keys=True))

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertIn("proposal", loaded)
        self.assertIn("decision", loaded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
