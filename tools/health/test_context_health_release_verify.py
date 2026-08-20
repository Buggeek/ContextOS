#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS_ROOT = Path(__file__).resolve().parents[1]
for runtime_path in (TOOLS_ROOT / "activation", TOOLS_ROOT / "cli", TOOLS_ROOT / "health"):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

import contextos_cli  # noqa: E402
from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402
from health_engine.health_engine import ContextHealthEngine  # noqa: E402
from health_engine.mission_use_evidence import MissionContextUseEvidenceEngine  # noqa: E402


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ssot_doc(title: str) -> str:
    return f"""# {title}
## Version: 0.1.0
Last Updated: 2026-08-20
Owner: Test Owner

---

## Purpose

Controlled release-verification artifact.

## Learning

Fixture learning remains explicit.

## Change Log

- 2026-08-20 - v0.1.0 - Created fixture.
"""


def make_repo() -> tempfile.TemporaryDirectory[str]:
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    for directory in ("docs", "SSOT", "ops", "templates"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    write(root / "README.md", "# Health Fixture\n")
    write(root / "ops" / "AGENT_RULES.md", "# Context OS Agent Rules\n")
    write(root / "docs" / "3.x_operation" / "3.6_COS_Human_Agent_Authority_Model.md", "# Authority\n\nL0 L1 L2 L3 L4 L5\n")
    write(root / "SSOT" / "README.md", "# SSOT\n\nCompliance profile: `strict`\n")
    for name, title in (
        ("S.1_Vision.md", "S.1 Vision"),
        ("P.1_Product_Map.md", "P.1 Product Map"),
        ("A.1_System_Map.md", "A.1 System Map"),
        ("A.4_Data_Entities.md", "A.4 Data Entities"),
        ("G.1_Definition_of_Ready.md", "G.1 Definition of Ready"),
        ("G.2_Definition_of_Done.md", "G.2 Definition of Done"),
    ):
        write(root / "SSOT" / name, ssot_doc(title))
    return temp


def invoke(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            code = contextos_cli.main(argv)
        except SystemExit as exc:
            code = int(exc.code or 0)
    return code, stdout.getvalue(), stderr.getvalue()


def snapshot(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


class ContextHealthReleaseVerificationTestCase(unittest.TestCase):
    def test_no_evidence_human_and_json_are_clear_parseable_and_read_only(self) -> None:
        with make_repo() as temp:
            root = Path(temp)
            before = snapshot(root)
            human_code, human, human_err = invoke(["health", "--root", temp])
            json_code, machine, json_err = invoke(["health", "--root", temp, "--format", "json"])
            after = snapshot(root)

        report = json.loads(machine)
        self.assertEqual((human_code, json_code), (0, 0))
        self.assertEqual(before, after)
        self.assertIn("## Executive Assessment", human)
        self.assertIn("Mission-use evidence: not supplied", human)
        self.assertEqual(report["schema"], "contextos.health.report/1")
        self.assertIsNone(report["evidence_sources"]["mission_use"])
        self.assertEqual((human_err, json_err), ("", ""))

    def test_valid_mission_use_improves_traceability_without_claiming_usefulness(self) -> None:
        with make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            activation = ContextActivationPackageEngine(temp)
            package = activation.run(goal="Verify Health use evidence", consumer="human", mission_id="V07-VERIFY")
            handoff = activation.build_handoff(package)
            evidence = MissionContextUseEvidenceEngine(temp).run(
                package=package,
                handoff=handoff,
                selected_accesses=[{
                    "source_ref": handoff["selected_context"][0]["path"],
                    "evidence_semantics": "observed",
                    "evidence_refs": ["verification.read"],
                }],
            )
            evidence_path = Path(output_temp) / "mission-use.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            code, stdout, stderr = invoke([
                "health", "--root", temp, "--mission-use-evidence", str(evidence_path), "--format", "json"
            ])

        report = json.loads(stdout)
        signals = {item["kind"]: item for item in report["dimensions"]["usefulness"]["signals"]}
        self.assertEqual(code, 0)
        self.assertEqual(signals["per_source_usage_traceability"]["status"], "healthy")
        self.assertEqual(signals["usefulness_effect"]["status"], "unknown")
        self.assertEqual(signals["usefulness_effect"]["belief_state"], "unknown")
        self.assertEqual(stderr, "")

    def test_unhealthy_fixture_is_blocked_and_actionable(self) -> None:
        with make_repo() as temp:
            write(Path(temp) / "README.md", "# Health Fixture\n\n[Missing](missing.md)\n")
            code, stdout, stderr = invoke(["health", "--root", temp, "--format", "json"])

        report = json.loads(stdout)
        self.assertEqual(code, 7)
        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertGreater(report["summary"]["blocking_count"], 0)
        self.assertIn(
            "resolve_validator_blockers",
            {candidate["kind"] for candidate in report["context_update_candidates"]},
        )
        self.assertEqual(stderr, "")

    def test_mismatched_evidence_is_rejected_without_contamination(self) -> None:
        with make_repo() as source, make_repo() as target, tempfile.TemporaryDirectory() as output_temp:
            activation = ContextActivationPackageEngine(source)
            package = activation.run(goal="Source evidence", consumer="human", mission_id="V07-SOURCE")
            handoff = activation.build_handoff(package)
            evidence = MissionContextUseEvidenceEngine(source).run(package=package, handoff=handoff)
            evidence_path = Path(output_temp) / "source-evidence.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            before = snapshot(Path(target))
            code, stdout, stderr = invoke([
                "health", "--root", target, "--mission-use-evidence", str(evidence_path), "--format", "json"
            ])
            after = snapshot(Path(target))

        error = json.loads(stdout)
        self.assertEqual(code, 9)
        self.assertEqual(before, after)
        self.assertEqual(error["error"]["category"], "misconfiguration")
        self.assertEqual(stderr, "")

    def test_candidates_remain_noncanonical_and_construction_routed(self) -> None:
        report = ContextHealthEngine(".").run(generated_at="2026-08-20T00:00:00Z")

        self.assertTrue(report["context_update_candidates"])
        for candidate in report["context_update_candidates"]:
            self.assertFalse(candidate["canonical"])
            self.assertEqual(candidate["lifecycle_state"], "suggested")
            self.assertEqual(candidate["route"], "existing_context_construction_lifecycle")
            self.assertTrue(candidate["promotion_prohibited"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
