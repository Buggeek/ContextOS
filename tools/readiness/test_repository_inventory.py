#!/usr/bin/env python3
"""Tests for Context OS Repository Inventory."""

from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import contextos_inventory
from inventory_engine.report_builder import SCHEMA
from inventory_engine.repository_inventory import RepositoryInventoryEngine


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def markdown(title: str) -> str:
    return f"# {title}\n\nTest artifact.\n"


class RepositoryInventoryTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md", markdown("Sample Repo"))
        write(root / "contextos", "#!/usr/bin/env python3\n")

        write(root / "docs" / "1.x_architecture" / "1.0_COS_Architecture.md", markdown("1.0 Architecture"))
        write(root / "docs" / "1.x_architecture" / "1.5_runtime_contracts" / "README.md", markdown("Runtime Contracts"))
        write(root / "docs" / "3.x_operation" / "3.6_COS_Human_Agent_Authority_Model.md", markdown("3.6 Authority"))
        write(root / "docs" / "3.x_operation" / "3.7_COS_Governance_Protocol.md", markdown("3.7 Governance"))
        write(root / "docs" / "5.x_strategy" / "5.4_COS_Product_Roadmap.md", markdown("5.4 Product Roadmap"))
        write(root / "docs" / "5.x_strategy" / "5.5_COS_Runtime_Maturity_Model.md", markdown("5.5 Runtime Maturity"))

        write(root / "SSOT" / "P.1_Product_Map.md", markdown("P.1 Product Map"))
        write(root / "SSOT" / "P.2_Product_Roadmap.md", markdown("P.2 Product Roadmap"))
        write(root / "SSOT" / "G.1_Definition_of_Ready.md", markdown("G.1 Definition of Ready"))
        write(root / "SSOT" / "epics" / "EPIC-004_Discovery_Engine.md", markdown("EPIC-004 Discovery Engine"))

        write(root / "ops" / "AGENT_RULES.md", markdown("Agent Rules"))
        write(root / "templates" / "governance" / "G.1_Definition_of_Ready.template.md", markdown("G.1 Template"))
        write(root / "examples" / "sample" / "README.md", markdown("Example"))
        write(root / "tools" / "validators" / "contextos_validator.py", "print('validator')\n")
        write(root / "tools" / "cli" / "contextos_cli.py", "print('cli')\n")
        return temp

    def test_inventory_report_shape_and_slice_boundaries(self) -> None:
        with self.make_repo() as temp:
            report = RepositoryInventoryEngine(temp).run(generated_at="2026-06-19T00:00:00Z")

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["generated_at"], "2026-06-19T00:00:00Z")
        self.assertIn("detected", report)
        self.assertNotIn("score", report["summary"])
        self.assertNotIn("level", report["summary"])
        self.assertNotIn("recommendations", report)

    def test_inventory_detects_required_groups(self) -> None:
        with self.make_repo() as temp:
            report = RepositoryInventoryEngine(temp).run()

        detected = report["detected"]
        classes = {item["id"] for item in detected["taxonomy_classes"]}
        runtime_components = {item["component"] for item in detected["runtime_artifacts"]}
        governance_kinds = {item["kind"] for item in detected["governance_artifacts"]}
        roadmap_kinds = {item["kind"] for item in detected["roadmap_artifacts"]}

        self.assertIn("architecture", classes)
        self.assertIn("operation", classes)
        self.assertIn("strategy", classes)
        self.assertIn("ssot-product", classes)
        self.assertIn("ssot-governance", classes)
        self.assertIn("ssot-epic", classes)
        self.assertIn("template", classes)
        self.assertIn("example", classes)

        self.assertIn("runtime-cli", runtime_components)
        self.assertIn("validator-engine", runtime_components)
        self.assertIn("runtime-contract", runtime_components)

        self.assertIn("agent-rules", governance_kinds)
        self.assertIn("authority-model", governance_kinds)
        self.assertIn("governance-protocol", governance_kinds)
        self.assertIn("ssot-governance", governance_kinds)
        self.assertIn("epic-governance", governance_kinds)
        self.assertIn("governance-template", governance_kinds)

        self.assertIn("ssot-roadmap", roadmap_kinds)
        self.assertIn("product-roadmap", roadmap_kinds)
        self.assertIn("maturity-roadmap", roadmap_kinds)
        self.assertIn("epic-backlog", roadmap_kinds)
        self.assertIn("product-map", roadmap_kinds)

    def test_cli_json_output_is_pure(self) -> None:
        with self.make_repo() as temp:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = contextos_inventory.main(["--root", temp, "--format", "json"])

        self.assertEqual(code, 0)
        report = json.loads(stdout.getvalue())
        self.assertEqual(report["schema"], SCHEMA)
        self.assertIn("detected", report)

    def test_cli_missing_root_returns_misconfiguration(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = contextos_inventory.main(["--root", "/definitely/missing/contextos", "--format", "json"])

        self.assertEqual(code, 9)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error"]["category"], "misconfiguration")


if __name__ == "__main__":
    unittest.main(verbosity=2)
