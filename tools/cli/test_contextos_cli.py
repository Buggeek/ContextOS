#!/usr/bin/env python3
"""Tests for the narrow Context OS Runtime CLI v0 surface."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import contextos_cli


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def tree_snapshot(root: Path) -> set[tuple[str, str]]:
    return {
        ("dir" if path.is_dir() else "file", path.relative_to(root).as_posix())
        for path in root.rglob("*")
    }


def ssot_doc(title: str) -> str:
    return f"""# {title}
## Version: 0.1.0
Last Updated: 2026-02-19
Owner: Test Owner

---

## Purpose

Test artifact.

## Change Log

- 2026-02-19 - v0.1.0 - Initial creation
"""


class ContextOSCliTestCase(unittest.TestCase):
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

    def invoke(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = contextos_cli.main(argv)
            except SystemExit as exc:
                code = int(exc.code or 0)
        return code, stdout.getvalue(), stderr.getvalue()

    def test_help_exits_zero(self) -> None:
        code, stdout, stderr = self.invoke(["--help"])

        self.assertEqual(code, 0)
        self.assertIn("validate", stdout)
        self.assertIn("assess", stdout)
        self.assertIn("init", stdout)
        self.assertIn("activate", stdout)
        self.assertEqual(stderr, "")

    def test_version_exits_zero(self) -> None:
        code, stdout, stderr = self.invoke(["--version"])

        self.assertEqual(code, 0)
        self.assertIn("contextos", stdout)
        self.assertEqual(stderr, "")

    def test_validate_json_wraps_validator_engine(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke([
                "validate",
                "--root",
                temp,
                "--mode",
                "gate",
                "--format",
                "json",
                "--rules",
                "structure.required_roots,mom.required_artifacts,governance.agent_rules_present,authority.model_present",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.validator.report/1")
        self.assertEqual(report["summary"]["exit_code"], 0)
        self.assertEqual(report["summary"]["rules_run"], 4)
        self.assertEqual(stderr, "")

    def test_validate_text_alias_renders_human_report(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke([
                "validate",
                "--root",
                temp,
                "--mode",
                "full",
                "--format",
                "text",
                "--rules",
                "structure.required_roots",
            ])

        self.assertEqual(code, 0)
        self.assertIn("# Context OS Validator Report", stdout)
        self.assertEqual(stderr, "")

    def test_validate_bad_rule_selector_returns_9(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke([
                "validate",
                "--root",
                temp,
                "--format",
                "json",
                "--rules",
                "missing.rule",
            ])

        payload = json.loads(stdout)
        self.assertEqual(code, 9)
        self.assertEqual(payload["error"]["code"], 9)
        self.assertEqual(payload["error"]["category"], "rules")
        self.assertEqual(stderr, "")

    def test_assess_default_renders_human_report(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke(["assess", "--root", temp])

        self.assertEqual(code, 0)
        self.assertIn("# Context OS Readiness Report", stdout)
        self.assertIn("Score:", stdout)
        self.assertIn("## Dimension Scores", stdout)
        self.assertIn("## Next Recommended Actions", stdout)
        self.assertEqual(stderr, "")

    def test_assess_json_is_pure_readiness_report(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke(["assess", "--root", temp, "--format", "json"])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.readiness.report/1")
        self.assertIn("dimensions", report)
        self.assertIn("recommendations", report)
        self.assertEqual(stderr, "")

    def test_assess_json_out_writes_machine_report(self) -> None:
        with self.make_repo() as temp:
            output_path = Path(temp) / "readiness-report.json"
            code, stdout, stderr = self.invoke([
                "assess",
                "--root",
                temp,
                "--json-out",
                str(output_path),
            ])

            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("# Context OS Readiness Report", stdout)
        self.assertEqual(report["schema"], "contextos.readiness.report/1")
        self.assertEqual(stderr, "")

    def test_activate_default_renders_human_package_without_target_writes(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = tree_snapshot(root)
            code, stdout, stderr = self.invoke([
                "activate",
                "--root",
                temp,
                "--goal",
                "Prepare a governed activation mission",
                "--consumer",
                "codex",
                "--mission-id",
                "V06-ACTIVATION-PACKAGE-CLI-001",
            ])
            after = tree_snapshot(root)

        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn("# Context OS Activation Package", stdout)
        self.assertIn("Consumer: `codex`", stdout)
        self.assertIn("This package is derived working context, not SSOT.", stdout)
        self.assertEqual(stderr, "")

    def test_activate_json_is_pure_activation_package(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke([
                "activate",
                "--root",
                temp,
                "--goal",
                "Prepare a governed activation mission",
                "--consumer",
                "claude_code",
                "--format",
                "json",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.activation.package/1")
        self.assertEqual(report["consumer"]["type"], "claude_code")
        self.assertFalse(report["summary"]["working_context_is_ssot"])
        self.assertEqual(stderr, "")

    def test_activate_requires_goal_without_check_package(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke(["activate", "--root", temp, "--format", "json"])

        payload = json.loads(stdout)
        self.assertEqual(code, 9)
        self.assertEqual(payload["error"]["category"], "misconfiguration")
        self.assertIn("--goal", payload["error"]["message"])
        self.assertEqual(stderr, "")

    def test_activate_json_out_and_check_package_detects_drift(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            output_path = Path(output_temp) / "activation-package.json"
            code, stdout, stderr = self.invoke([
                "activate",
                "--root",
                temp,
                "--goal",
                "Prepare a governed activation mission",
                "--consumer",
                "codex",
                "--json-out",
                str(output_path),
            ])
            package = json.loads(output_path.read_text(encoding="utf-8"))
            check_code, check_stdout, check_stderr = self.invoke([
                "activate",
                "--root",
                temp,
                "--check-package",
                str(output_path),
                "--format",
                "json",
            ])
            write(Path(temp) / "README.md", "# Test Repo\n\nChanged after package.\n")
            drift_code, drift_stdout, drift_stderr = self.invoke([
                "activate",
                "--root",
                temp,
                "--check-package",
                str(output_path),
                "--format",
                "json",
            ])

        check_report = json.loads(check_stdout)
        drift_report = json.loads(drift_stdout)
        self.assertEqual(code, 0)
        self.assertIn("# Context OS Activation Package", stdout)
        self.assertEqual(package["schema"], "contextos.activation.package/1")
        self.assertEqual(check_code, 0)
        self.assertEqual(check_report["schema"], "contextos.activation.package_check/1")
        self.assertTrue(check_report["result"]["valid"])
        self.assertEqual(drift_code, 7)
        self.assertTrue(drift_report["result"]["invalidated"])
        self.assertFalse(drift_report["checks"]["source_hashes_match"])
        self.assertEqual(stderr, "")
        self.assertEqual(check_stderr, "")
        self.assertEqual(drift_stderr, "")

    def test_init_default_renders_human_bootstrap_plan_without_target_writes(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = tree_snapshot(root)
            code, stdout, stderr = self.invoke(["init", "--root", temp])
            after = tree_snapshot(root)

        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn("# Context OS Bootstrap Plan", stdout)
        self.assertIn("Ready for bootstrap:", stdout)
        self.assertIn("## Required Actions", stdout)
        self.assertIn("## Skipped Existing Targets", stdout)
        self.assertIn("## Blocked Actions", stdout)
        self.assertIn("## Manual Actions", stdout)
        self.assertIn("## Validator Summary", stdout)
        self.assertIn("This plan did not modify the target repository.", stdout)
        self.assertIn("future apply approval", stdout)
        self.assertEqual(stderr, "")

    def test_init_json_is_pure_bootstrap_plan(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke(["init", "--root", temp, "--format", "json"])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.bootstrap.plan/1")
        self.assertIn("actions", report)
        self.assertFalse(report["constraints"]["writes_performed"])
        self.assertEqual(stderr, "")

    def test_init_json_out_writes_machine_plan(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            output_path = Path(output_temp) / "bootstrap-plan.json"
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--json-out",
                str(output_path),
            ])

            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("# Context OS Bootstrap Plan", stdout)
        self.assertEqual(report["schema"], "contextos.bootstrap.plan/1")
        self.assertIn("actions", report)
        self.assertEqual(stderr, "")

    def test_init_proposal_default_renders_human_without_target_writes(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = tree_snapshot(root)
            code, stdout, stderr = self.invoke(["init", "--root", temp, "--proposal"])
            after = tree_snapshot(root)

        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn("# Context OS Bootstrap Proposal", stdout)
        self.assertIn("Proposal ID:", stdout)
        self.assertIn("Approval implied: no", stdout)
        self.assertIn("Apply authorized: no", stdout)
        self.assertIn("This proposal did not modify the target repository.", stdout)
        self.assertEqual(stderr, "")

    def test_init_proposal_json_is_pure_machine_report(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--proposal",
                "--format",
                "json",
                "--mission-id",
                "TEST-MISSION-001",
                "--requested-by",
                "Test Owner",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.bootstrap.proposal/1")
        self.assertEqual(report["mission_id"], "TEST-MISSION-001")
        self.assertEqual(report["authority"]["requested_by"], "Test Owner")
        self.assertFalse(report["constraints"]["writes_performed"])
        self.assertFalse(report["constraints"]["approval_implied"])
        self.assertFalse(report["constraints"]["apply_authorized"])
        self.assertEqual(stderr, "")

    def test_init_proposal_json_out_writes_machine_proposal(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            output_path = Path(output_temp) / "bootstrap-proposal.json"
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--proposal",
                "--json-out",
                str(output_path),
            ])

            report = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("# Context OS Bootstrap Proposal", stdout)
        self.assertEqual(report["schema"], "contextos.bootstrap.proposal/1")
        self.assertIn("identity_hash", report)
        self.assertEqual(stderr, "")

    def test_init_approval_record_json_is_pure_machine_report(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            proposal_path = Path(output_temp) / "bootstrap-proposal.json"
            self.invoke([
                "init",
                "--root",
                temp,
                "--proposal",
                "--format",
                "json",
                "--json-out",
                str(proposal_path),
            ])
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--approval-record",
                str(proposal_path),
                "--format",
                "json",
                "--approver",
                "Test Owner",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.bootstrap.approval_record/1")
        self.assertEqual(report["proposal"]["ref"], str(proposal_path))
        self.assertFalse(report["constraints"]["approval_implied"])
        self.assertFalse(report["constraints"]["apply_authorized"])
        self.assertTrue(report["constraints"]["human_authority_required"])
        self.assertEqual(stderr, "")

    def test_init_approval_record_default_renders_human_without_target_writes(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            before = tree_snapshot(root)
            proposal_path = Path(output_temp) / "bootstrap-proposal.json"
            self.invoke(["init", "--root", temp, "--proposal", "--json-out", str(proposal_path)])
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--approval-record",
                str(proposal_path),
            ])
            after = tree_snapshot(root)

        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn("# Context OS Bootstrap Approval Record Draft", stdout)
        self.assertIn("Apply authorized: no", stdout)
        self.assertIn("Human authority required: yes", stdout)
        self.assertIn("This approval record draft does not approve the proposal.", stdout)
        self.assertEqual(stderr, "")

    def test_init_approval_record_json_out_writes_machine_report(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            proposal_path = Path(output_temp) / "bootstrap-proposal.json"
            approval_path = Path(output_temp) / "bootstrap-approval.json"
            self.invoke(["init", "--root", temp, "--proposal", "--json-out", str(proposal_path)])
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--approval-record",
                str(proposal_path),
                "--json-out",
                str(approval_path),
            ])
            report = json.loads(approval_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("# Context OS Bootstrap Approval Record Draft", stdout)
        self.assertEqual(report["schema"], "contextos.bootstrap.approval_record/1")
        self.assertIn("decision", report)
        self.assertEqual(stderr, "")

    def test_init_approval_record_bad_input_returns_misconfiguration(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--approval-record",
                str(Path(temp) / "missing-proposal.json"),
                "--format",
                "json",
            ])

        payload = json.loads(stdout)
        self.assertEqual(code, 9)
        self.assertEqual(payload["error"]["category"], "misconfiguration")
        self.assertEqual(stderr, "")

    def test_init_accept_approval_json_is_pure_machine_report(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            proposal_path = Path(output_temp) / "bootstrap-proposal.json"
            approval_path = Path(output_temp) / "bootstrap-approval.json"
            self.invoke(["init", "--root", temp, "--proposal", "--json-out", str(proposal_path)])
            self.invoke([
                "init",
                "--root",
                temp,
                "--approval-record",
                str(proposal_path),
                "--json-out",
                str(approval_path),
                "--approver",
                "Mission Owner",
            ])
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--accept-approval",
                str(approval_path),
                "--accepted-by",
                "Jane Owner",
                "--accepted-role",
                "Mission Owner",
                "--format",
                "json",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.bootstrap.accepted_decision/1")
        self.assertTrue(report["decision"]["approved"])
        self.assertFalse(report["decision"]["apply_authorized"])
        self.assertFalse(report["decision"]["repository_mutation_authorized"])
        self.assertEqual(stderr, "")

    def test_init_accept_approval_default_renders_human_without_target_writes(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            before = tree_snapshot(root)
            proposal_path = Path(output_temp) / "bootstrap-proposal.json"
            approval_path = Path(output_temp) / "bootstrap-approval.json"
            self.invoke(["init", "--root", temp, "--proposal", "--json-out", str(proposal_path)])
            self.invoke([
                "init",
                "--root",
                temp,
                "--approval-record",
                str(proposal_path),
                "--json-out",
                str(approval_path),
                "--approver",
                "Mission Owner",
            ])
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--accept-approval",
                str(approval_path),
                "--accepted-by",
                "Jane Owner",
                "--accepted-role",
                "Mission Owner",
            ])
            after = tree_snapshot(root)

        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn("# Context OS Bootstrap Accepted Decision", stdout)
        self.assertIn("Accepted by: Jane Owner", stdout)
        self.assertIn("Apply authorized: no", stdout)
        self.assertIn("Repository mutation authorized: no", stdout)
        self.assertIn("This accepted decision does not authorize apply by itself.", stdout)
        self.assertEqual(stderr, "")

    def test_init_accept_approval_json_out_writes_machine_report(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            proposal_path = Path(output_temp) / "bootstrap-proposal.json"
            approval_path = Path(output_temp) / "bootstrap-approval.json"
            accepted_path = Path(output_temp) / "bootstrap-accepted.json"
            self.invoke(["init", "--root", temp, "--proposal", "--json-out", str(proposal_path)])
            self.invoke([
                "init",
                "--root",
                temp,
                "--approval-record",
                str(proposal_path),
                "--json-out",
                str(approval_path),
                "--approver",
                "Mission Owner",
            ])
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--accept-approval",
                str(approval_path),
                "--accepted-by",
                "Jane Owner",
                "--accepted-role",
                "Mission Owner",
                "--json-out",
                str(accepted_path),
            ])
            report = json.loads(accepted_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("# Context OS Bootstrap Accepted Decision", stdout)
        self.assertEqual(report["schema"], "contextos.bootstrap.accepted_decision/1")
        self.assertIn("decision_record", report["decision"])
        self.assertEqual(stderr, "")

    def test_init_accept_approval_requires_explicit_human_authority(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            proposal_path = Path(output_temp) / "bootstrap-proposal.json"
            approval_path = Path(output_temp) / "bootstrap-approval.json"
            self.invoke(["init", "--root", temp, "--proposal", "--json-out", str(proposal_path)])
            self.invoke(["init", "--root", temp, "--approval-record", str(proposal_path), "--json-out", str(approval_path)])
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--accept-approval",
                str(approval_path),
                "--format",
                "json",
            ])

        payload = json.loads(stdout)
        self.assertEqual(code, 9)
        self.assertEqual(payload["error"]["category"], "misconfiguration")
        self.assertIn("explicit approving human identity", payload["error"]["evidence"]["error"])
        self.assertEqual(stderr, "")

    def test_init_preflight_json_is_pure_machine_report(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            proposal_path = Path(output_temp) / "bootstrap-proposal.json"
            approval_path = Path(output_temp) / "bootstrap-approval.json"
            accepted_path = Path(output_temp) / "bootstrap-accepted.json"
            self.invoke(["init", "--root", temp, "--proposal", "--json-out", str(proposal_path)])
            self.invoke([
                "init",
                "--root",
                temp,
                "--approval-record",
                str(proposal_path),
                "--json-out",
                str(approval_path),
                "--approver",
                "Mission Owner",
            ])
            self.invoke([
                "init",
                "--root",
                temp,
                "--accept-approval",
                str(approval_path),
                "--accepted-by",
                "Jane Owner",
                "--accepted-role",
                "Mission Owner",
                "--json-out",
                str(accepted_path),
            ])
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--preflight",
                str(accepted_path),
                "--format",
                "json",
            ])
        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.bootstrap.apply_preflight/1")
        self.assertTrue(report["eligibility"]["eligible_for_apply"])
        self.assertFalse(report["eligibility"]["apply_authorized"])
        self.assertGreater(report["frozen_mutation_set"]["count"], 0)
        self.assertEqual(stderr, "")

    def test_init_preflight_default_renders_human_without_target_writes(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            before = tree_snapshot(root)
            proposal_path = Path(output_temp) / "bootstrap-proposal.json"
            approval_path = Path(output_temp) / "bootstrap-approval.json"
            accepted_path = Path(output_temp) / "bootstrap-accepted.json"
            self.invoke(["init", "--root", temp, "--proposal", "--json-out", str(proposal_path)])
            self.invoke(["init", "--root", temp, "--approval-record", str(proposal_path), "--approver", "Mission Owner", "--json-out", str(approval_path)])
            self.invoke([
                "init",
                "--root",
                temp,
                "--accept-approval",
                str(approval_path),
                "--accepted-by",
                "Jane Owner",
                "--accepted-role",
                "Mission Owner",
                "--json-out",
                str(accepted_path),
            ])
            code, stdout, stderr = self.invoke(["init", "--root", temp, "--preflight", str(accepted_path)])
            after = tree_snapshot(root)

        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn("# Context OS Bootstrap Apply Preflight", stdout)
        self.assertIn("Eligible for apply: yes", stdout)
        self.assertIn("Apply authorized: no", stdout)
        self.assertIn("Frozen Mutation Set", stdout)
        self.assertIn("This preflight does not authorize or perform apply.", stdout)
        self.assertEqual(stderr, "")

    def test_init_preflight_json_out_writes_machine_report(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            proposal_path = Path(output_temp) / "bootstrap-proposal.json"
            approval_path = Path(output_temp) / "bootstrap-approval.json"
            accepted_path = Path(output_temp) / "bootstrap-accepted.json"
            preflight_path = Path(output_temp) / "bootstrap-preflight.json"
            self.invoke(["init", "--root", temp, "--proposal", "--json-out", str(proposal_path)])
            self.invoke(["init", "--root", temp, "--approval-record", str(proposal_path), "--approver", "Mission Owner", "--json-out", str(approval_path)])
            self.invoke([
                "init",
                "--root",
                temp,
                "--accept-approval",
                str(approval_path),
                "--accepted-by",
                "Jane Owner",
                "--accepted-role",
                "Mission Owner",
                "--json-out",
                str(accepted_path),
            ])
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--preflight",
                str(accepted_path),
                "--json-out",
                str(preflight_path),
            ])
            report = json.loads(preflight_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertIn("# Context OS Bootstrap Apply Preflight", stdout)
        self.assertEqual(report["schema"], "contextos.bootstrap.apply_preflight/1")
        self.assertIn("frozen_mutation_set", report)
        self.assertEqual(stderr, "")

    def test_init_preflight_bad_input_returns_misconfiguration(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--preflight",
                str(Path(temp) / "missing-accepted.json"),
                "--format",
                "json",
            ])

        payload = json.loads(stdout)
        self.assertEqual(code, 9)
        self.assertEqual(payload["error"]["category"], "misconfiguration")
        self.assertEqual(stderr, "")

    def write_preflight_artifact(self, temp: str, output_temp: str) -> tuple[Path, dict]:
        proposal_path = Path(output_temp) / "bootstrap-proposal.json"
        approval_path = Path(output_temp) / "bootstrap-approval.json"
        accepted_path = Path(output_temp) / "bootstrap-accepted.json"
        preflight_path = Path(output_temp) / "bootstrap-preflight.json"
        self.invoke(["init", "--root", temp, "--proposal", "--json-out", str(proposal_path)])
        self.invoke(["init", "--root", temp, "--approval-record", str(proposal_path), "--approver", "Mission Owner", "--json-out", str(approval_path)])
        self.invoke([
            "init",
            "--root",
            temp,
            "--accept-approval",
            str(approval_path),
            "--accepted-by",
            "Jane Owner",
            "--accepted-role",
            "Mission Owner",
            "--json-out",
            str(accepted_path),
        ])
        self.invoke(["init", "--root", temp, "--preflight", str(accepted_path), "--json-out", str(preflight_path)])
        return preflight_path, json.loads(preflight_path.read_text(encoding="utf-8"))

    def test_init_apply_json_is_pure_machine_report_and_create_only(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            preflight_path, preflight = self.write_preflight_artifact(temp, output_temp)
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--apply",
                str(preflight_path),
                "--confirm-apply",
                "--confirmed-by",
                "Jane Owner",
                "--confirmed-role",
                "Mission Owner",
                "--confirmed-preflight-id",
                preflight["id"],
                "--confirmed-preflight-hash",
                preflight["identity_hash"],
                "--format",
                "json",
            ])
            manifest_exists = (root / ".contextos" / "manifest.yaml").exists()

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.bootstrap.apply_result/1")
        self.assertEqual(report["result"]["state"], "applied_validated")
        self.assertTrue(report["result"]["success"])
        self.assertTrue(manifest_exists)
        self.assertFalse(report["constraints"]["overwrites_performed"])
        self.assertEqual(stderr, "")

    def test_init_apply_default_renders_human(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            preflight_path, preflight = self.write_preflight_artifact(temp, output_temp)
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--apply",
                str(preflight_path),
                "--confirm-apply",
                "--confirmed-by",
                "Jane Owner",
                "--confirmed-role",
                "Mission Owner",
                "--confirmed-preflight-id",
                preflight["id"],
                "--confirmed-preflight-hash",
                preflight["identity_hash"],
            ])

        self.assertEqual(code, 0)
        self.assertIn("# Context OS Bootstrap Apply Result", stdout)
        self.assertIn("State: applied_validated", stdout)
        self.assertIn("Apply performed create-only actions.", stdout)
        self.assertEqual(stderr, "")

    def test_init_apply_requires_confirmation_without_target_writes(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            before = tree_snapshot(root)
            preflight_path, _preflight = self.write_preflight_artifact(temp, output_temp)
            code, stdout, stderr = self.invoke([
                "init",
                "--root",
                temp,
                "--apply",
                str(preflight_path),
                "--format",
                "json",
            ])
            after = tree_snapshot(root)

        payload = json.loads(stdout)
        self.assertEqual(code, 9)
        self.assertEqual(before, after)
        self.assertEqual(payload["error"]["category"], "misconfiguration")
        self.assertIn("confirm-apply", payload["error"]["evidence"]["error"])
        self.assertEqual(stderr, "")

    def test_init_apply_reusing_same_preflight_returns_blocked_result(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            preflight_path, preflight = self.write_preflight_artifact(temp, output_temp)
            argv = [
                "init",
                "--root",
                temp,
                "--apply",
                str(preflight_path),
                "--confirm-apply",
                "--confirmed-by",
                "Jane Owner",
                "--confirmed-role",
                "Mission Owner",
                "--confirmed-preflight-id",
                preflight["id"],
                "--confirmed-preflight-hash",
                preflight["identity_hash"],
                "--format",
                "json",
            ]
            first_code, _first_stdout, _first_stderr = self.invoke(argv)
            second_code, second_stdout, stderr = self.invoke(argv)

        report = json.loads(second_stdout)
        self.assertEqual(first_code, 0)
        self.assertEqual(second_code, 7)
        self.assertFalse(report["result"]["success"])
        self.assertIn("apply.check.no_overwrite_current_state", report["result"]["failed_pre_checks"])
        self.assertEqual(stderr, "")

    def test_init_example_repo_returns_validator_error_code_with_plan(self) -> None:
        code, stdout, stderr = self.invoke([
            "init",
            "--root",
            "examples/sample_solo_founder",
            "--format",
            "json",
        ])

        report = json.loads(stdout)
        self.assertEqual(code, 7)
        self.assertEqual(report["schema"], "contextos.bootstrap.plan/1")
        self.assertGreater(report["validator"]["error"], 0)
        self.assertGreater(report["summary"]["blocked_action_count"], 0)
        self.assertEqual(stderr, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
