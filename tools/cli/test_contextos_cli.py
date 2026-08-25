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
from activation_engine.package_engine import ContextActivationPackageEngine
from health_engine.mission_use_evidence import MissionContextUseEvidenceEngine
from test_memory_context_version_integration import exact_version


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


def mission_doc() -> str:
    return """# E.4 Mission TEST-MEMORY-001 - Retrieval
## Version: 0.1.0
Last Updated: 2026-08-21
Owner: Test Owner
Status: closed:done

## Decision

Preserve memory retrieval provenance and human authority.

## Learning

Historical memory does not override current canonical context.
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
        self.assertIn("health", stdout)
        self.assertIn("memory", stdout)
        self.assertIn("reason", stdout)
        self.assertEqual(stderr, "")

    def test_reason_human_surface_is_read_only_and_authority_safe(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = tree_snapshot(root)
            code, stdout, stderr = self.invoke([
                "reason", "--root", temp, "--goal", "Determine what context requires attention"
            ])
            after = tree_snapshot(root)

        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn("# Context OS Contextual Assessment", stdout)
        self.assertIn("## Observed Facts", stdout)
        self.assertIn("## Interpretations", stdout)
        self.assertIn("## Recommendations", stdout)
        self.assertIn("## Required Human Decisions", stdout)
        self.assertIn("cannot decide, approve, execute", stdout)
        self.assertEqual(stderr, "")

    def test_reason_json_is_pure_and_accepts_structured_evidence(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            evidence_path = Path(output_temp) / "evidence.json"
            evidence_path.write_text(
                json.dumps(
                    {
                        "schema": "contextos.reasoning.evidence_set/1",
                        "claims": [
                            {
                                "id": "claim.test.status",
                                "subject": "mission.test",
                                "predicate": "status",
                                "value": "active",
                                "source_refs": ["test.evidence"],
                                "epistemic_support": "observed",
                            }
                        ],
                        "relationships": [],
                    }
                ),
                encoding="utf-8",
            )
            code, stdout, stderr = self.invoke([
                "reason",
                "--root",
                temp,
                "--goal",
                "Assess exact Mission evidence",
                "--reasoning-evidence",
                str(evidence_path),
                "--format",
                "json",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.reasoning.assessment/1")
        self.assertEqual(report["bindings"]["reasoning_evidence"]["claim_count"], 1)
        self.assertTrue(report["read_only"])
        self.assertFalse(report["authority"]["may_decide"])
        self.assertEqual(stderr, "")

    def test_reason_json_out_and_saved_check_are_valid(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            assessment_path = Path(output_temp) / "assessment.json"
            code, stdout, stderr = self.invoke([
                "reason",
                "--root",
                temp,
                "--goal",
                "Create a reusable governed assessment",
                "--json-out",
                str(assessment_path),
                "--format",
                "json",
            ])
            saved = json.loads(assessment_path.read_text(encoding="utf-8"))
            check_code, check_stdout, check_stderr = self.invoke([
                "reason",
                "--root",
                temp,
                "--check-assessment",
                str(assessment_path),
                "--format",
                "json",
            ])

        check = json.loads(check_stdout)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout)["identity_hash"], saved["identity_hash"])
        self.assertEqual(check_code, 0)
        self.assertEqual(check["schema"], "contextos.reasoning.assessment_check/1")
        self.assertTrue(check["result"]["valid"])
        self.assertEqual(stderr, "")
        self.assertEqual(check_stderr, "")

    def test_reason_saved_check_detects_source_drift(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            assessment_path = Path(output_temp) / "assessment.json"
            create_code, _, _ = self.invoke([
                "reason", "--root", temp, "--goal", "Detect stale reasoning", "--json-out", str(assessment_path)
            ])
            product_map = Path(temp) / "SSOT/P.1_Product_Map.md"
            product_map.write_text(product_map.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")
            code, stdout, stderr = self.invoke([
                "reason", "--root", temp, "--check-assessment", str(assessment_path), "--format", "json"
            ])

        report = json.loads(stdout)
        self.assertEqual(create_code, 0)
        self.assertEqual(code, 7)
        self.assertTrue(report["result"]["invalidated"])
        self.assertIn("reasoning.assessment_check.current_state_changed", report["result"]["failed_checks"])
        self.assertEqual(stderr, "")

    def test_reason_requires_goal_or_check(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke(["reason", "--root", temp, "--format", "json"])

        payload = json.loads(stdout)
        self.assertEqual(code, 9)
        self.assertEqual(payload["error"]["category"], "misconfiguration")
        self.assertIn("requires --goal", payload["error"]["evidence"]["error"])
        self.assertEqual(stderr, "")

    def test_version_exits_zero(self) -> None:
        code, stdout, stderr = self.invoke(["--version"])

        self.assertEqual(code, 0)
        self.assertEqual(stdout, "contextos 1.0.0\n")
        self.assertEqual(stderr, "")

    def test_health_default_is_read_only_and_explains_attention(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = tree_snapshot(root)
            code, stdout, stderr = self.invoke(["health", "--root", temp])
            after = tree_snapshot(root)

        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn("# Context OS Health Report", stdout)
        self.assertIn("## Health Dimensions", stdout)
        self.assertIn("## What Needs Attention", stdout)
        self.assertIn("## Context Integrity", stdout)
        self.assertIn("## Context Usefulness", stdout)
        self.assertIn("## Organizational Learning", stdout)
        self.assertIn("## Context Update Candidates", stdout)
        self.assertIn("What to consider next:", stdout)
        self.assertIn("This report made no automatic changes.", stdout)
        self.assertIn("Mission-use evidence: not supplied", stdout)
        self.assertEqual(stderr, "")

    def test_health_json_is_pure_machine_report(self) -> None:
        with self.make_repo() as temp:
            code, stdout, stderr = self.invoke(["health", "--root", temp, "--format", "json"])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.health.report/1")
        self.assertEqual(set(report["dimensions"]), {"integrity", "usefulness", "learning"})
        self.assertTrue(report["read_only"])
        self.assertFalse(report["authority"]["may_write_drafts"])
        self.assertEqual(stderr, "")

    def test_health_consumes_exact_mission_use_evidence(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            activation = ContextActivationPackageEngine(temp)
            package = activation.run(
                goal="Assess context use",
                consumer="human",
                mission_id="V07-HEALTH-CLI-TEST",
            )
            handoff = activation.build_handoff(package)
            evidence = MissionContextUseEvidenceEngine(temp).run(
                package=package,
                handoff=handoff,
                selected_accesses=[
                    {
                        "source_ref": handoff["selected_context"][0]["path"],
                        "evidence_semantics": "observed",
                        "evidence_refs": ["test.read"],
                    }
                ],
            )
            evidence_path = Path(output_temp) / "mission-use.json"
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            code, stdout, stderr = self.invoke([
                "health",
                "--root",
                temp,
                "--mission-use-evidence",
                str(evidence_path),
                "--format",
                "json",
            ])

        report = json.loads(stdout)
        signals = {item["kind"]: item for item in report["dimensions"]["usefulness"]["signals"]}
        self.assertEqual(code, 0)
        self.assertEqual(report["evidence_sources"]["mission_use"]["id"], evidence["id"])
        self.assertEqual(signals["per_source_usage_traceability"]["status"], "healthy")
        self.assertEqual(signals["usefulness_effect"]["status"], "unknown")
        self.assertEqual(stderr, "")

    def test_health_json_out_writes_full_machine_report(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            report_path = Path(output_temp) / "health.json"
            code, stdout, stderr = self.invoke([
                "health",
                "--root",
                temp,
                "--json-out",
                str(report_path),
            ])
            saved = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(code, 0)
        self.assertEqual(saved["schema"], "contextos.health.report/1")
        self.assertIn("# Context OS Health Report", stdout)
        self.assertEqual(stderr, "")

    def test_health_rejects_wrong_schema_as_misconfiguration(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            evidence_path = Path(output_temp) / "wrong.json"
            evidence_path.write_text(json.dumps({"schema": "wrong", "root": temp}), encoding="utf-8")
            code, stdout, stderr = self.invoke([
                "health",
                "--root",
                temp,
                "--mission-use-evidence",
                str(evidence_path),
                "--format",
                "json",
            ])

        error = json.loads(stdout)
        self.assertEqual(code, 9)
        self.assertEqual(error["error"]["category"], "misconfiguration")
        self.assertEqual(stderr, "")

    def test_health_preserves_blocking_validator_exit_code(self) -> None:
        with self.make_repo() as temp:
            write(Path(temp) / "README.md", "# Test Repo\n\n[Missing](missing.md)\n")
            code, stdout, stderr = self.invoke(["health", "--root", temp, "--format", "json"])

        report = json.loads(stdout)
        self.assertEqual(code, 7)
        self.assertEqual(report["dimensions"]["integrity"]["status"], "blocked")
        self.assertGreater(report["summary"]["blocking_count"], 0)
        self.assertEqual(stderr, "")

    def test_memory_human_surface_is_read_only_and_explainable(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(
                root / "SSOT" / "E.4_Mission_TEST-MEMORY-001_Retrieval.md",
                mission_doc(),
            )
            before = tree_snapshot(root)
            code, stdout, stderr = self.invoke([
                "memory", "--root", temp, "--goal", "memory retrieval provenance", "--consumer", "human"
            ])
            after = tree_snapshot(root)

        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn("# Context OS Memory Retrieval", stdout)
        self.assertIn("## Authority Boundary", stdout)
        self.assertIn("No retention policy was supplied", stdout)
        self.assertIn("Selected candidates: 0", stdout)
        self.assertEqual(stderr, "")

    def test_memory_json_is_pure_machine_report(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / "SSOT" / "E.4_Mission_TEST-MEMORY-001_Retrieval.md", mission_doc())
            code, stdout, stderr = self.invoke([
                "memory", "--root", temp, "--goal", "memory provenance", "--format", "json"
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.memory.retrieval_result/1")
        self.assertTrue(report["read_only"])
        self.assertFalse(report["authority"]["retrieved_memory_may_override_canonical"])
        self.assertEqual(stderr, "")

    def test_memory_cli_applies_retention_policy_before_exposure(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as inputs_temp:
            root = Path(temp)
            write(root / "SSOT" / "E.4_Mission_TEST-MEMORY-001_Retrieval.md", mission_doc())
            policy_path = Path(inputs_temp) / "policy.json"
            metadata_path = Path(inputs_temp) / "metadata.json"
            policy_path.write_text(
                json.dumps(
                    {
                        "schema": "contextos.memory.retention_policy/1",
                        "id": "policy.cli.memory",
                        "version": "1",
                        "status": "active",
                        "scope": {
                            "memory_forms": [
                                "mission", "decision", "evidence", "outcome", "learning",
                                "context_state", "evolution_inbox",
                            ]
                        },
                        "effects": {"access": "normal", "retrieval": "normal", "activation": "excluded"},
                        "obligations": [],
                        "holds": [],
                        "required_authority": {},
                        "inherits_from": [],
                        "explanation_visibility": "id_only",
                    }
                ),
                encoding="utf-8",
            )
            metadata_path.write_text(
                json.dumps(
                    {
                        "defaults": {
                            "organization": "test",
                            "operation": "product",
                            "tier": "organizational",
                            "owner": "Test Owner",
                            "sensitivity": "internal",
                            "retention_state": "historical",
                            "metadata_visibility": "full",
                        }
                    }
                ),
                encoding="utf-8",
            )
            code, stdout, stderr = self.invoke([
                "memory", "--root", temp,
                "--goal", "memory retrieval provenance",
                "--purpose", "Review historical prior art",
                "--consumer", "human",
                "--organizational-mode", "project",
                "--actor-role", "project_owner",
                "--authority-scope", "project:test",
                "--retention-policy", str(policy_path),
                "--memory-metadata", str(metadata_path),
                "--format", "json",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertGreater(report["summary"]["selected_count"], 0)
        self.assertEqual(report["query"]["purpose"], "Review historical prior art")
        self.assertEqual(report["query"]["organizational_mode"], "project")
        self.assertEqual(report["query"]["actor_roles"], ["project_owner"])
        self.assertEqual(report["query"]["authority_scope"], "project:test")
        self.assertTrue(report["authority"]["policy_evaluated_before_exposure"])
        self.assertTrue(all(item["retrieval_eligibility"]["retrieval_outcome"] == "normal" for item in report["items"]))
        self.assertTrue(all(item["retrieval_eligibility"]["activation_outcome"] == "excluded" for item in report["items"]))
        self.assertEqual(stderr, "")

    def test_memory_json_out_and_check_round_trip(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            write(root / "SSOT" / "E.4_Mission_TEST-MEMORY-001_Retrieval.md", mission_doc())
            report_path = Path(output_temp) / "retrieval.json"
            code, _stdout, stderr = self.invoke([
                "memory", "--root", temp, "--goal", "memory provenance", "--json-out", str(report_path)
            ])
            check_code, check_stdout, check_stderr = self.invoke([
                "memory", "--root", temp, "--check-retrieval", str(report_path), "--format", "json"
            ])
            saved = json.loads(report_path.read_text(encoding="utf-8"))

        check = json.loads(check_stdout)
        self.assertEqual(code, 0)
        self.assertEqual(saved["schema"], "contextos.memory.retrieval_result/1")
        self.assertEqual(check_code, 0)
        self.assertEqual(check["schema"], "contextos.memory.retrieval_check/1")
        self.assertTrue(check["result"]["valid"])
        self.assertEqual(stderr, "")
        self.assertEqual(check_stderr, "")

    def test_memory_cli_consumes_exact_context_version_without_granting_authority(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as inputs_temp:
            root = Path(temp)
            write(root / "SSOT/E.4_Mission_TEST-MEMORY-001_Retrieval.md", mission_doc())
            version = exact_version(root)
            version_path = Path(inputs_temp) / "version.json"
            policy_path = Path(inputs_temp) / "policy.json"
            metadata_path = Path(inputs_temp) / "metadata.json"
            version_path.write_text(json.dumps(version), encoding="utf-8")
            policy_path.write_text(
                json.dumps(
                    {
                        "schema": "contextos.memory.retention_policy/1",
                        "id": "policy.cli.context-version",
                        "version": "1",
                        "status": "active",
                        "scope": {"memory_forms": ["mission", "decision", "context_state"]},
                        "effects": {"access": "normal", "retrieval": "normal", "activation": "excluded"},
                        "obligations": [],
                        "holds": [],
                        "required_authority": {},
                        "inherits_from": [],
                        "explanation_visibility": "id_only",
                    }
                ),
                encoding="utf-8",
            )
            metadata_path.write_text(
                json.dumps(
                    {
                        "defaults": {
                            "organization": "test",
                            "operation": "product",
                            "tier": "organizational",
                            "owner": "Test Owner",
                            "sensitivity": "internal",
                            "retention_state": "historical",
                            "metadata_visibility": "full",
                        }
                    }
                ),
                encoding="utf-8",
            )
            code, stdout, stderr = self.invoke(
                [
                    "memory", "--root", temp,
                    "--goal", "memory decision provenance authority historical context version",
                    "--retention-policy", str(policy_path),
                    "--memory-metadata", str(metadata_path),
                    "--context-version", str(version_path),
                    "--format", "json",
                ]
            )

        report = json.loads(stdout)
        exact_items = [item for item in report["items"] if (item.get("context_evidence") or {}).get("metadata_exposed")]
        self.assertEqual(code, 0)
        self.assertEqual(report["summary"]["context_version_bindings"]["exact"], 1)
        self.assertGreater(len(exact_items), 0)
        self.assertEqual(exact_items[0]["context_evidence"]["context_version"]["id"], version["id"])
        self.assertEqual(exact_items[0]["authority"]["current_authority"], "none_from_retrieval")
        self.assertEqual(stderr, "")

    def test_memory_check_detects_source_drift(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            source = root / "SSOT" / "E.4_Mission_TEST-MEMORY-001_Retrieval.md"
            write(source, mission_doc())
            report_path = Path(output_temp) / "retrieval.json"
            code, _stdout, _stderr = self.invoke([
                "memory", "--root", temp, "--goal", "memory provenance", "--json-out", str(report_path)
            ])
            source.write_text(source.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")
            check_code, check_stdout, check_stderr = self.invoke([
                "memory", "--root", temp, "--check-retrieval", str(report_path), "--format", "json"
            ])

        check = json.loads(check_stdout)
        self.assertEqual(code, 0)
        self.assertEqual(check_code, 7)
        self.assertFalse(check["result"]["valid"])
        self.assertEqual(check_stderr, "")

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

    def test_activate_handoff_from_package_renders_human_without_target_writes(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp)
            before = tree_snapshot(root)
            package_path = Path(output_temp) / "activation-package.json"
            self.invoke([
                "activate",
                "--root",
                temp,
                "--goal",
                "Prepare a package-backed handoff",
                "--consumer",
                "codex",
                "--mission-id",
                "V06-ACTIVATION-HANDOFF-FORMAT-001",
                "--json-out",
                str(package_path),
            ])
            code, stdout, stderr = self.invoke([
                "activate",
                "--root",
                temp,
                "--check-package",
                str(package_path),
                "--handoff",
            ])
            after = tree_snapshot(root)

        self.assertEqual(code, 0)
        self.assertEqual(before, after)
        self.assertIn("# Context OS Activation Handoff", stdout)
        self.assertIn("Package valid now: yes", stdout)
        self.assertIn("This handoff is derived from an Activation Package and is not SSOT.", stdout)
        self.assertEqual(stderr, "")

    def test_activate_handoff_json_is_pure_machine_report(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            package_path = Path(output_temp) / "activation-package.json"
            self.invoke([
                "activate",
                "--root",
                temp,
                "--goal",
                "Prepare a package-backed handoff",
                "--consumer",
                "claude_code",
                "--json-out",
                str(package_path),
            ])
            code, stdout, stderr = self.invoke([
                "activate",
                "--root",
                temp,
                "--check-package",
                str(package_path),
                "--handoff",
                "--format",
                "json",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.activation.handoff/1")
        self.assertTrue(report["result"]["handoff_ready"])
        self.assertEqual(report["consumer"]["type"], "claude_code")
        self.assertFalse(report["constraints"]["duplicates_full_canonical_content"])
        self.assertEqual(stderr, "")

    def test_activate_handoff_exit_code_reports_drift(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            package_path = Path(output_temp) / "activation-package.json"
            self.invoke([
                "activate",
                "--root",
                temp,
                "--goal",
                "Prepare a package-backed handoff",
                "--consumer",
                "codex",
                "--json-out",
                str(package_path),
            ])
            write(Path(temp) / "README.md", "# Test Repo\n\nChanged after package.\n")
            code, stdout, stderr = self.invoke([
                "activate",
                "--root",
                temp,
                "--check-package",
                str(package_path),
                "--handoff",
                "--format",
                "json",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 7)
        self.assertEqual(report["schema"], "contextos.activation.handoff/1")
        self.assertFalse(report["result"]["handoff_ready"])
        self.assertTrue(report["result"]["invalidated"])
        self.assertEqual(stderr, "")

    def test_activate_check_handoff_json_is_pure_machine_report(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            package_path = Path(output_temp) / "activation-package.json"
            handoff_path = Path(output_temp) / "activation-handoff.json"
            self.invoke([
                "activate",
                "--root",
                temp,
                "--goal",
                "Use a package-backed handoff",
                "--consumer",
                "codex",
                "--json-out",
                str(package_path),
            ])
            self.invoke([
                "activate",
                "--root",
                temp,
                "--check-package",
                str(package_path),
                "--handoff",
                "--json-out",
                str(handoff_path),
            ])
            code, stdout, stderr = self.invoke([
                "activate",
                "--root",
                temp,
                "--check-handoff",
                str(handoff_path),
                "--format",
                "json",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 0)
        self.assertEqual(report["schema"], "contextos.activation.handoff_check/1")
        self.assertTrue(report["result"]["valid"])
        self.assertTrue(report["checks"]["handoff_identity_valid"])
        self.assertTrue(report["checks"]["package_ref_valid"])
        self.assertEqual(stderr, "")

    def test_activate_check_handoff_detects_drift(self) -> None:
        with self.make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            package_path = Path(output_temp) / "activation-package.json"
            handoff_path = Path(output_temp) / "activation-handoff.json"
            self.invoke([
                "activate",
                "--root",
                temp,
                "--goal",
                "Use a package-backed handoff",
                "--consumer",
                "codex",
                "--json-out",
                str(package_path),
            ])
            self.invoke([
                "activate",
                "--root",
                temp,
                "--check-package",
                str(package_path),
                "--handoff",
                "--json-out",
                str(handoff_path),
            ])
            write(Path(temp) / "README.md", "# Test Repo\n\nChanged after handoff.\n")
            code, stdout, stderr = self.invoke([
                "activate",
                "--root",
                temp,
                "--check-handoff",
                str(handoff_path),
                "--format",
                "json",
            ])

        report = json.loads(stdout)
        self.assertEqual(code, 7)
        self.assertEqual(report["schema"], "contextos.activation.handoff_check/1")
        self.assertFalse(report["result"]["valid"])
        self.assertTrue(report["result"]["invalidated"])
        self.assertEqual(stderr, "")

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
