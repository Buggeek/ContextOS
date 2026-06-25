#!/usr/bin/env python3
"""Tests for Context OS Bootstrap Planning."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bootstrap_engine.plan_engine import BootstrapPlanEngine
from bootstrap_engine.report_builder import SCHEMA, render_human


def write(path: Path, text: str = "# Test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_snapshot(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


class BootstrapPlanTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md")
        write(root / "SSOT" / "S.1_Vision.md")
        return temp

    def test_plan_shape_and_read_only_constraints(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = file_snapshot(root)
            report = BootstrapPlanEngine(root).run(generated_at="2026-06-25T00:00:00Z")
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["generated_at"], "2026-06-25T00:00:00Z")
        self.assertTrue(report["read_only"])
        self.assertFalse(report["constraints"]["writes_performed"])
        self.assertFalse(report["constraints"]["manifests_created"])
        self.assertFalse(report["constraints"]["artifacts_created"])

    def test_contextos_repo_plan_has_required_manifest_and_skips_existing_ssot(self) -> None:
        report = BootstrapPlanEngine(".").run()
        actions = {action["target_path"]: action for action in report["actions"] if action["target_path"]}

        self.assertEqual(report["schema"], SCHEMA)
        self.assertTrue(report["summary"]["ready_for_bootstrap"])
        self.assertEqual(actions[".contextos/manifest.yaml"]["status"], "required")
        self.assertEqual(actions["SSOT/S.1_Vision.md"]["status"], "skipped_existing")

    def test_example_repo_plan_handles_validator_errors_without_fatal(self) -> None:
        report = BootstrapPlanEngine("examples/sample_solo_founder").run()
        actions = {action["target_path"]: action for action in report["actions"] if action["target_path"]}
        ids = {action["id"] for action in report["actions"]}

        self.assertFalse(report["summary"]["ready_for_bootstrap"])
        self.assertTrue(report["summary"]["can_plan_bootstrap"])
        self.assertEqual(report["validator"]["fatal"], 0)
        self.assertEqual(actions["SSOT/P.2_Product_Roadmap.md"]["status"], "blocked")
        self.assertIn("bootstrap.action.manual_remediation.readiness_structure_resolve_blocking_validator_findings", ids)

    def test_human_report_contains_core_sections(self) -> None:
        report = BootstrapPlanEngine(".").run()
        human = render_human(report)

        self.assertIn("# Context OS Bootstrap Plan", human)
        self.assertIn("Ready for bootstrap:", human)
        self.assertIn("## Required Actions", human)
        self.assertIn("## Skipped Existing Targets", human)
        self.assertIn("## Blocked Actions", human)
        self.assertIn("## Validator Summary", human)
        self.assertIn("This plan did not write files.", human)

    def test_json_report_is_serializable(self) -> None:
        report = BootstrapPlanEngine(".").run()
        loaded = json.loads(json.dumps(report, sort_keys=True))

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertIn("actions", loaded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
