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


if __name__ == "__main__":
    unittest.main(verbosity=2)
