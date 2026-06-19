#!/usr/bin/env python3
"""Tests for Context OS Readiness Scoring."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from readiness_engine.readiness_scoring import DIMENSION_WEIGHTS, ReadinessScoringEngine
from readiness_engine.report_builder import SCHEMA


def write(path: Path, text: str = "# Test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def fake_validator_report(summary: dict | None = None, findings: list[dict] | None = None) -> dict:
    return {
        "schema": "contextos.validator.report/1",
        "generated_at": "2026-06-19T00:00:00Z",
        "mode": "full",
        "root": "/tmp/contextos-test",
        "summary": summary
        or {
            "rules_run": 23,
            "info": 0,
            "warn": 0,
            "error": 0,
            "fatal": 0,
            "exit_code": 0,
        },
        "findings": findings or [],
    }


class ReadinessScoringTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md")
        write(root / "contextos", "#!/usr/bin/env python3\n")
        write(root / ".contextos" / "manifest.yaml", "version: 1\n")
        write(root / "docs" / "1.x_architecture" / "1.0_COS_Architecture.md")
        write(root / "docs" / "1.x_architecture" / "1.5_runtime_contracts" / "README.md")
        write(root / "docs" / "3.x_operation" / "3.0_COS_Minimum_Operational_Map.md")
        write(root / "docs" / "3.x_operation" / "3.6_COS_Human_Agent_Authority_Model.md")
        write(root / "docs" / "3.x_operation" / "3.7_COS_Governance_Protocol.md")
        write(root / "docs" / "5.x_strategy" / "5.4_COS_Product_Roadmap.md")
        write(root / "SSOT" / "S.1_Vision.md")
        write(root / "SSOT" / "P.1_Product_Map.md")
        write(root / "SSOT" / "P.2_Product_Roadmap.md")
        write(root / "SSOT" / "A.1_System_Map.md")
        write(root / "SSOT" / "A.4_Data_Entities.md")
        write(root / "SSOT" / "G.1_Definition_of_Ready.md")
        write(root / "SSOT" / "G.2_Definition_of_Done.md")
        write(root / "SSOT" / "epics" / "EPIC-004_Discovery_Engine.md")
        write(root / "ops" / "AGENT_RULES.md")
        write(root / "templates" / "governance" / "G.1_Definition_of_Ready.template.md")
        write(root / "examples" / "sample" / "README.md")
        write(root / "tools" / "validators" / "contextos_validator.py", "print('validator')\n")
        write(root / "tools" / "cli" / "contextos_cli.py", "print('cli')\n")
        write(root / "tools" / "readiness" / "README.md")
        return temp

    def test_report_shape_and_slice_boundaries(self) -> None:
        with self.make_repo() as temp:
            report = ReadinessScoringEngine(temp).run(
                validator_report=fake_validator_report(),
                generated_at="2026-06-19T00:00:00Z",
            )

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["generated_at"], "2026-06-19T00:00:00Z")
        self.assertEqual(set(report["dimensions"]), set(DIMENSION_WEIGHTS))
        self.assertEqual(report["recommendations"], [])
        self.assertEqual(report["summary"]["recommendation_count"], 0)
        self.assertTrue(report["constraints"]["read_only"])
        self.assertFalse(report["constraints"]["knowledge_engine_used"])
        self.assertFalse(report["constraints"]["graph_runtime_used"])

    def test_dimensions_include_signals_gaps_and_evidence(self) -> None:
        with self.make_repo() as temp:
            report = ReadinessScoringEngine(temp).run(validator_report=fake_validator_report())

        for dimension in report["dimensions"].values():
            self.assertIn("signals", dimension)
            self.assertIn("gaps", dimension)
            self.assertIn("evidence_refs", dimension)
            self.assertIsInstance(dimension["score"], int)
            self.assertGreaterEqual(dimension["score"], 0)
            self.assertLessEqual(dimension["score"], 100)

    def test_validator_errors_cap_report_at_r2(self) -> None:
        findings = [
            {
                "id": "finding-1",
                "rule": "links.relative_paths_resolve",
                "severity": "error",
                "message": "Broken link.",
                "path": "docs/example.md",
                "line": 1,
                "anchor": None,
                "evidence": None,
                "suggested_fix": None,
            }
        ]
        summary = {"rules_run": 23, "info": 0, "warn": 0, "error": 1, "fatal": 0, "exit_code": 7}
        with self.make_repo() as temp:
            report = ReadinessScoringEngine(temp).run(validator_report=fake_validator_report(summary, findings))

        self.assertLessEqual(report["summary"]["score"], 59)
        self.assertEqual(report["summary"]["level"], "R2")
        self.assertFalse(report["summary"]["can_bootstrap"])

    def test_public_engine_runs_on_contextos_repository(self) -> None:
        report = ReadinessScoringEngine(".").run()

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["inventory"]["schema"], "contextos.inventory.report/1")
        self.assertEqual(report["validator"]["schema"], "contextos.validator.report/1")
        self.assertEqual(report["summary"]["recommendation_count"], len(report["recommendations"]))
        self.assertIn(report["summary"]["level"], {"R0", "R1", "R2", "R3", "R4", "R5"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
