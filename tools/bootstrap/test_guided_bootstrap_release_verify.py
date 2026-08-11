#!/usr/bin/env python3
"""Release verification for v0.4 Guided Bootstrap."""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import sys

TOOLS_ROOT = Path(__file__).resolve().parents[1]
CLI_ROOT = TOOLS_ROOT / "cli"
if str(CLI_ROOT) not in sys.path:
    sys.path.insert(0, str(CLI_ROOT))

import contextos_cli  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parents[2]


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

Release verification artifact.

## Change Log

- 2026-08-11 - v0.1.0 - Initial creation
"""


def tree_snapshot(root: Path) -> set[tuple[str, str]]:
    return {
        ("dir" if path.is_dir() else "file", path.relative_to(root).as_posix())
        for path in root.rglob("*")
    }


class GuidedBootstrapReleaseVerifyTestCase(unittest.TestCase):
    def invoke(self, argv: list[str]) -> tuple[int, str, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = contextos_cli.main(argv)
            except SystemExit as exc:
                code = int(exc.code or 0)
        return code, stdout.getvalue(), stderr.getvalue()

    def make_minimal_structured_repo(self, root: Path) -> None:
        for directory in ("docs", "SSOT", "ops", "templates"):
            (root / directory).mkdir(parents=True, exist_ok=True)
        write(root / "README.md", "# Minimal Structured Repo\n")
        write(root / "ops" / "AGENT_RULES.md", "# Context OS Agent Rules\n")
        write(root / "docs" / "3.x_operation" / "3.6_COS_Human_Agent_Authority_Model.md", "# 3.6 Authority\n\nL0 L1 L2 L3 L4 L5\n")
        write(root / "SSOT" / "README.md", "# SSOT\n\nCompliance profile: `strict`\n")
        for rel, title in [
            ("S.1_Vision.md", "S.1 Vision"),
            ("P.1_Product_Map.md", "P.1 Product Map"),
            ("A.1_System_Map.md", "A.1 System Map"),
            ("A.4_Data_Entities.md", "A.4 Data Entities"),
            ("G.1_Definition_of_Ready.md", "G.1 Definition of Ready"),
            ("G.2_Definition_of_Done.md", "G.2 Definition of Done"),
        ]:
            write(root / "SSOT" / rel, ssot_doc(title))

    def make_incomplete_repo(self, root: Path) -> None:
        write(root / "README.md", "# Incomplete Repo\n")

    def make_existing_artifacts_repo(self, root: Path) -> None:
        self.make_minimal_structured_repo(root)
        write(root / ".contextos" / "manifest.yaml", "schema: contextos.runtime.manifest/1\nversion: 0.1.0\n")
        (root / "SSOT" / "epics").mkdir(parents=True, exist_ok=True)

    def copy_example_repo(self, name: str, root: Path) -> None:
        shutil.copytree(REPO_ROOT / "examples" / name, root, dirs_exist_ok=True)

    def full_journey(self, root: Path, output_root: Path) -> dict:
        assess_before_code, assess_before_stdout, _stderr = self.invoke(["assess", "--root", str(root), "--format", "json"])
        plan_code, plan_stdout, _stderr = self.invoke(["init", "--root", str(root), "--format", "json"])
        before_read_only = tree_snapshot(root)
        proposal_path = output_root / "proposal.json"
        approval_path = output_root / "approval.json"
        accepted_path = output_root / "accepted.json"
        preflight_path = output_root / "preflight.json"
        apply_path = output_root / "apply.json"
        self.invoke(["init", "--root", str(root), "--proposal", "--json-out", str(proposal_path)])
        after_proposal = tree_snapshot(root)
        self.invoke(["init", "--root", str(root), "--approval-record", str(proposal_path), "--approver", "Mission Owner", "--json-out", str(approval_path)])
        after_approval = tree_snapshot(root)
        self.invoke([
            "init",
            "--root",
            str(root),
            "--accept-approval",
            str(approval_path),
            "--accepted-by",
            "Release Verifier",
            "--accepted-role",
            "Mission Owner",
            "--json-out",
            str(accepted_path),
        ])
        after_acceptance = tree_snapshot(root)
        preflight_code, _preflight_stdout, _stderr = self.invoke(["init", "--root", str(root), "--preflight", str(accepted_path), "--json-out", str(preflight_path)])
        after_preflight = tree_snapshot(root)
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
        apply_code, _apply_stdout, _stderr = self.invoke([
            "init",
            "--root",
            str(root),
            "--apply",
            str(preflight_path),
            "--confirm-apply",
            "--confirmed-by",
            "Release Verifier",
            "--confirmed-role",
            "Mission Owner",
            "--confirmed-preflight-id",
            preflight["id"],
            "--confirmed-preflight-hash",
            preflight["identity_hash"],
            "--json-out",
            str(apply_path),
        ])
        assess_after_code, assess_after_stdout, _stderr = self.invoke(["assess", "--root", str(root), "--format", "json"])
        return {
            "assess_before_code": assess_before_code,
            "assess_before": json.loads(assess_before_stdout),
            "plan_code": plan_code,
            "plan": json.loads(plan_stdout),
            "preflight_code": preflight_code,
            "preflight": preflight,
            "apply_code": apply_code,
            "apply": json.loads(apply_path.read_text(encoding="utf-8")),
            "assess_after_code": assess_after_code,
            "assess_after": json.loads(assess_after_stdout),
            "read_only_unchanged": before_read_only == after_proposal == after_approval == after_acceptance == after_preflight,
        }

    def test_minimal_structured_repo_completes_full_journey_and_improves_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            self.make_minimal_structured_repo(root)
            result = self.full_journey(root, Path(output_temp))

        self.assertTrue(result["read_only_unchanged"])
        self.assertEqual(result["preflight_code"], 0)
        self.assertTrue(result["preflight"]["eligibility"]["eligible_for_apply"])
        self.assertEqual(result["apply_code"], 0)
        self.assertEqual(result["apply"]["result"]["state"], "applied_validated")
        self.assertGreater(result["assess_after"]["summary"]["score"], result["assess_before"]["summary"]["score"])
        self.assertEqual(result["apply"]["validation"]["post_apply_validator"]["summary"]["error"], 0)

    def test_incomplete_repo_produces_explicit_non_success_without_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            self.make_incomplete_repo(root)
            result = self.full_journey(root, Path(output_temp))

        self.assertTrue(result["read_only_unchanged"])
        self.assertNotEqual(result["apply"]["result"]["state"], "applied_validated")
        self.assertFalse(result["apply"]["result"]["success"])
        self.assertTrue(result["apply"]["result"]["failed_pre_checks"] or result["apply"]["result"]["errors"])

    def test_existing_artifacts_repo_preserves_user_content_and_has_no_required_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            self.make_existing_artifacts_repo(root)
            original_manifest = (root / ".contextos" / "manifest.yaml").read_text(encoding="utf-8")
            result = self.full_journey(root, Path(output_temp))
            current_manifest = (root / ".contextos" / "manifest.yaml").read_text(encoding="utf-8")

        self.assertEqual(original_manifest, current_manifest)
        self.assertTrue(result["read_only_unchanged"])
        self.assertFalse(result["apply"]["result"]["success"])
        self.assertIn("apply.check.apply_has_executable_mutations", result["apply"]["result"]["failed_pre_checks"])
        self.assertEqual(result["apply"]["mutations"], [])

    def test_existing_example_copy_runs_without_crashing_or_mutating_read_only_stages(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            self.copy_example_repo("sample_solo_founder", root)
            result = self.full_journey(root, Path(output_temp))

        self.assertTrue(result["read_only_unchanged"])
        self.assertEqual(result["plan"]["schema"], "contextos.bootstrap.plan/1")
        self.assertEqual(result["preflight"]["schema"], "contextos.bootstrap.apply_preflight/1")
        self.assertEqual(result["apply"]["schema"], "contextos.bootstrap.apply_result/1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
