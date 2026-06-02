#!/usr/bin/env python3
"""Tests for Context OS Validator Engine v0."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import contextos_validator as validator


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ssot_doc(title: str, extra: str = "") -> str:
    return f"""# {title}
## Version: 0.1.0
Last Updated: 2026-02-19
Owner: Test Owner

---

## Purpose

Test artifact.

## Change Log

- 2026-02-19 - v0.1.0 - Initial creation
{extra}
"""


class ValidatorTestCase(unittest.TestCase):
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

    def run_validator(self, root: Path, mode: str = "full", rules: str = "all", output_format: str = "json") -> tuple[int, dict | str]:
        stdout = io.StringIO()
        args = ["--root", str(root), "--mode", mode, "--rules", rules, "--format", output_format]
        with contextlib.redirect_stdout(stdout):
            code = validator.main(args)
        output = stdout.getvalue()
        if output_format == "json":
            return code, json.loads(output)
        return code, output

    def test_json_report_shape_and_clean_selected_rules_exit_zero(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            code, report = self.run_validator(
                root,
                mode="full",
                rules="structure.required_roots,mom.required_artifacts,governance.agent_rules_present,authority.model_present",
            )

        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], validator.SCHEMA)
        self.assertEqual(report["summary"]["rules_run"], 4)
        self.assertEqual(report["summary"]["error"], 0)
        self.assertIn("generated_at", report)
        self.assertIsInstance(report["findings"], list)

    def test_broken_relative_link_blocks(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / "docs" / "1.x_architecture" / "1.0_Test.md", "# Test\n\n[Missing](missing.md)\n")
            code, report = self.run_validator(root, rules="links.relative_paths_resolve")

        self.assertEqual(code, 7)
        self.assertEqual(report["summary"]["error"], 1)
        self.assertEqual(report["findings"][0]["rule"], "links.relative_paths_resolve")

    def test_missing_anchor_blocks(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / "docs" / "1.x_architecture" / "1.0_Target.md", "# Target\n\n## Existing\n")
            write(root / "docs" / "1.x_architecture" / "1.1_Source.md", "# Source\n\n[Bad](1.0_Target.md#missing)\n")
            code, report = self.run_validator(root, rules="links.anchors_resolve")

        self.assertEqual(code, 7)
        self.assertEqual(report["findings"][0]["anchor"], "missing")

    def test_missing_mom_artifact_blocks(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            (root / "SSOT" / "P.1_Product_Map.md").unlink()
            code, report = self.run_validator(root, rules="mom.required_artifacts")

        self.assertEqual(code, 7)
        self.assertEqual(report["findings"][0]["rule"], "mom.required_artifacts")
        self.assertIn("P.1_Product_Map.md", report["findings"][0]["path"])

    def test_required_fields_block_for_strict_ssot(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / "SSOT" / "S.1_Vision.md", "# S.1 Vision\n\n## Purpose\n\nNo owner.\n")
            code, report = self.run_validator(root, rules="mom.required_fields")

        self.assertEqual(code, 7)
        missing_fields = {finding["evidence"]["field"] for finding in report["findings"] if finding["evidence"]}
        self.assertIn("Version", missing_fields)
        self.assertIn("Owner", missing_fields)

    def test_doctrine_term_blocks(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / "docs" / "3.x_operation" / "3.1_Bad.md", "# Bad\n\nAgent Operating Model\n")
            code, report = self.run_validator(root, rules="naming.doctrine_terms")

        self.assertEqual(code, 7)
        self.assertEqual(report["findings"][0]["rule"], "naming.doctrine_terms")

    def test_rule_selector_exclusion(self) -> None:
        selected, error = validator.parse_rule_selector("links.*,-links.anchors_resolve")

        self.assertIsNone(error)
        self.assertIn("links.relative_paths_resolve", selected)
        self.assertNotIn("links.anchors_resolve", selected)

    def test_bad_rule_selector_returns_misconfiguration(self) -> None:
        with self.make_repo() as temp:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = validator.main(["--root", temp, "--rules", "missing.rule", "--format", "json"])

        self.assertEqual(code, 9)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error"]["code"], 9)

    def test_gate_reports_warn_only_findings_without_blocking(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / "docs" / "1.x_architecture" / "1.1_Warn.md", "# Warn\n\nContextOS in prose.\n")
            code, report = self.run_validator(root, mode="gate", rules="naming.contextos_convention")

        self.assertEqual(code, 0)
        self.assertEqual(report["summary"]["warn"], 1)

    def test_legacy_allowlist_suppresses_historical_reference(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(
                root / "SSOT" / "E.1_User_Story_US-001_Structure_Canonical_Paths.md",
                "# E.1 User Story\nVersion: 0.1.0\nOwner: Test Owner\n\nKeep legacy alias `docs/3.x_mom` documented.\n",
            )
            code, report = self.run_validator(root, rules="structure.legacy_paths")

        self.assertEqual(code, 0)
        self.assertEqual(report["summary"]["warn"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
