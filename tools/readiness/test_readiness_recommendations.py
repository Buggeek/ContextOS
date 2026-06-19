#!/usr/bin/env python3
"""Tests for Context OS Readiness recommendations and human report rendering."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from readiness_engine.readiness_scoring import ReadinessScoringEngine
from readiness_engine.report_builder import render_human


def write(path: Path, text: str = "# Test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def finding(rule: str, severity: str, path: str | None, message: str) -> dict:
    return {
        "id": f"{rule}-{severity}-{path or 'repo'}",
        "rule": rule,
        "severity": severity,
        "message": message,
        "path": path,
        "line": 1 if path else None,
        "anchor": None,
        "evidence": None,
        "suggested_fix": None,
    }


def fake_validator_report(findings: list[dict]) -> dict:
    counts = {severity: 0 for severity in ("info", "warn", "error", "fatal")}
    for item in findings:
        counts[item["severity"]] += 1
    exit_code = 8 if counts["fatal"] else 7 if counts["error"] else 0
    return {
        "schema": "contextos.validator.report/1",
        "generated_at": "2026-06-19T00:00:00Z",
        "mode": "full",
        "root": "/tmp/contextos-test",
        "summary": {
            "rules_run": 23,
            "info": counts["info"],
            "warn": counts["warn"],
            "error": counts["error"],
            "fatal": counts["fatal"],
            "exit_code": exit_code,
        },
        "findings": findings,
    }


class ReadinessRecommendationTestCase(unittest.TestCase):
    def make_repo(self, with_manifest: bool = False) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md")
        write(root / "contextos", "#!/usr/bin/env python3\n")
        if with_manifest:
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
        write(root / "examples" / "sample" / "README.md")
        write(root / "tools" / "validators" / "contextos_validator.py", "print('validator')\n")
        write(root / "tools" / "cli" / "contextos_cli.py", "print('cli')\n")
        write(root / "tools" / "readiness" / "README.md")
        return temp

    def test_current_repo_generates_recommendations_for_known_caps(self) -> None:
        report = ReadinessScoringEngine(".").run()
        ids = {item["id"] for item in report["recommendations"]}

        self.assertGreater(report["summary"]["recommendation_count"], 0)
        self.assertIn("readiness.runtime.create_manifest", ids)
        self.assertIn("readiness.ownership.assign_framework_owners", ids)
        self.assertIn("readiness.construction.complete_mom_fields", ids)

    def test_missing_manifest_produces_recommendation(self) -> None:
        findings = [
            finding(
                "structure.runtime_manifest",
                "warn",
                ".contextos/manifest.yaml",
                "Runtime manifest is not present.",
            )
        ]
        with self.make_repo(with_manifest=False) as temp:
            report = ReadinessScoringEngine(temp).run(validator_report=fake_validator_report(findings))

        recommendation = next(item for item in report["recommendations"] if item["id"] == "readiness.runtime.create_manifest")
        for field in ("id", "priority", "category", "title", "rationale", "suggested_action", "related_dimension"):
            self.assertIn(field, recommendation)
        self.assertEqual(recommendation["related_dimension"], "runtime")
        self.assertIn(".contextos/manifest.yaml", recommendation["evidence_refs"])

    def test_framework_ownership_gap_produces_recommendation(self) -> None:
        findings = [
            finding(
                "ownership.framework_owner_present",
                "warn",
                "docs/1.x_architecture/1.0_COS_Architecture.md",
                "Framework artifact does not declare an explicit owner.",
            )
        ]
        with self.make_repo(with_manifest=True) as temp:
            report = ReadinessScoringEngine(temp).run(validator_report=fake_validator_report(findings))

        ids = {item["id"] for item in report["recommendations"]}
        self.assertIn("readiness.ownership.assign_framework_owners", ids)

    def test_blocking_validator_findings_produce_recommendation(self) -> None:
        findings = [
            finding(
                "links.relative_paths_resolve",
                "error",
                "docs/broken.md",
                "Relative link does not resolve.",
            )
        ]
        with self.make_repo(with_manifest=True) as temp:
            report = ReadinessScoringEngine(temp).run(validator_report=fake_validator_report(findings))

        ids = {item["id"] for item in report["recommendations"]}
        self.assertIn("readiness.structure.resolve_blocking_validator_findings", ids)
        self.assertEqual(report["summary"]["blocking_issue_count"], 1)

    def test_human_report_contains_score_dimensions_and_next_actions(self) -> None:
        report = ReadinessScoringEngine(".").run()
        human = render_human(report)

        self.assertIn("Score:", human)
        self.assertIn(report["summary"]["level"], human)
        self.assertIn("## Dimension Scores", human)
        self.assertIn("## Next Recommended Actions", human)
        self.assertIn("## Validator Summary", human)
        self.assertIn("`runtime`", human)

    def test_json_report_remains_valid(self) -> None:
        report = ReadinessScoringEngine(".").run()
        loaded = json.loads(json.dumps(report, sort_keys=True))

        self.assertEqual(loaded["schema"], "contextos.readiness.report/1")
        self.assertEqual(loaded["summary"]["recommendation_count"], len(loaded["recommendations"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
