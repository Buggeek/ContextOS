#!/usr/bin/env python3
"""Tests for Context OS activation packages."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ACTIVATION_ROOT = Path(__file__).resolve().parent
if str(ACTIVATION_ROOT) not in sys.path:
    sys.path.insert(0, str(ACTIVATION_ROOT))

from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402
from activation_engine.report_builder import HANDOFF_SCHEMA, SCHEMA, render_human  # noqa: E402


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_snapshot(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): path.read_text(encoding="utf-8") for path in root.rglob("*") if path.is_file()}


def ssot_doc(artifact_id: str, title: str, body: str) -> str:
    return f"""# {artifact_id} {title}
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers

---

## Purpose

{body}

## Change Log

- 2026-08-11 - v0.1.0 - Initial test artifact.
"""


class ContextActivationPackageTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md", "# Example Runtime\nOwner: Maintainers\n")
        (root / "templates").mkdir(parents=True, exist_ok=True)
        write(root / "ops" / "AGENT_RULES.md", "# Context OS Agent Rules\n")
        write(root / "docs" / "3.x_operation" / "3.6_COS_Human_Agent_Authority_Model.md", "# 3.6 Authority\n\nL0 L1 L2 L3 L4 L5\n")
        write(root / "SSOT" / "README.md", "# SSOT\n\nCompliance profile: `strict`\n")
        write(root / "SSOT" / "S.1_Vision.md", ssot_doc("S.1", "Vision", "Activation context."))
        write(root / "SSOT" / "P.1_Product_Map.md", ssot_doc("P.1", "Product Map", "Activation product context."))
        write(root / "SSOT" / "P.2_Product_Roadmap.md", ssot_doc("P.2", "Roadmap", "v0.6 Context Activation."))
        write(root / "SSOT" / "A.1_System_Map.md", ssot_doc("A.1", "System Map", "Activation system context."))
        write(root / "SSOT" / "A.4_Data_Entities.md", ssot_doc("A.4", "Data Entities", "Activation entities."))
        write(root / "SSOT" / "G.1_Definition_of_Ready.md", ssot_doc("G.1", "Definition of Ready", "Ready."))
        write(root / "SSOT" / "G.2_Definition_of_Done.md", ssot_doc("G.2", "Definition of Done", "Done."))
        write(root / "docs" / "0.x_foundations" / "0.8_COS_GENESIS.md", "# GENESIS\nActivation must be governed.\n")
        write(root / "docs" / "1.x_architecture" / "1.0_COS_Architecture.md", "# Architecture\nActivation Layer.\n")
        return temp

    def test_package_shape_and_read_only_boundaries(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = file_snapshot(root)
            report = ContextActivationPackageEngine(root).run(
                goal="Activate context for a planning mission",
                consumer="codex",
                mission_id="V06-CONTEXT-ACTIVATION-PLAN-001",
                generated_at="2026-08-11T00:00:00Z",
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["generated_at"], "2026-08-11T00:00:00Z")
        self.assertTrue(report["read_only"])
        self.assertFalse(report["summary"]["working_context_is_ssot"])
        self.assertTrue(report["boundaries"]["canonical_source_authority_preserved"])
        self.assertTrue(report["boundaries"]["working_context_is_not_ssot"])
        self.assertFalse(report["constraints"]["writes_performed"])
        self.assertFalse(report["constraints"]["parallel_ssot_created"])

    def test_package_preserves_source_hashes_and_invalidation_conditions(self) -> None:
        with self.make_repo() as temp:
            report = ContextActivationPackageEngine(temp).run(
                goal="Activate governed context",
                consumer="claude_code",
                generated_at="2026-08-11T00:00:00Z",
            )

        self.assertTrue(report["source_fingerprint"])
        self.assertTrue(report["invalidation"]["source_hashes"])
        self.assertIn("Any included source hash changes.", report["invalidation"]["conditions"])
        for source in report["canonical_sources"]:
            self.assertEqual(report["invalidation"]["source_hashes"][source["path"]], source["hash"])

    def test_package_is_deterministic_with_fixed_time(self) -> None:
        with self.make_repo() as temp:
            first = ContextActivationPackageEngine(temp).run(
                goal="Activate governed context",
                consumer="human",
                mission_id="V06-CONTEXT-ACTIVATION-PLAN-001",
                generated_at="2026-08-11T00:00:00Z",
            )
            second = ContextActivationPackageEngine(temp).run(
                goal="Activate governed context",
                consumer="human",
                mission_id="V06-CONTEXT-ACTIVATION-PLAN-001",
                generated_at="2026-08-11T00:00:00Z",
            )

        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(first["identity_hash"], second["identity_hash"])

    def test_goal_and_consumer_are_required(self) -> None:
        with self.make_repo() as temp:
            engine = ContextActivationPackageEngine(temp)
            with self.assertRaisesRegex(ValueError, "goal"):
                engine.run(goal="", consumer="codex")
            with self.assertRaisesRegex(ValueError, "consumer"):
                engine.run(goal="Activate", consumer="")

    def test_validator_gate_blocks_activation_package(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / "README.md", "# Broken\n\nSee [Missing](missing.md).\n")
            report = ContextActivationPackageEngine(root).run(
                goal="Activate governed context",
                consumer="codex",
                generated_at="2026-08-11T00:00:00Z",
            )

        self.assertFalse(report["summary"]["activation_allowed"])
        self.assertGreater(report["validator"]["summary"]["error"], 0)
        self.assertIn("activation.gap.validator_gate_blocked", {gap["id"] for gap in report["context_gaps"]})

    def test_contextos_repo_dogfood_selects_activation_sources(self) -> None:
        report = ContextActivationPackageEngine(".").run(
            goal="Define the minimum Context Activation package for Codex and Claude Code",
            consumer="codex",
            mission_id="V06-CONTEXT-ACTIVATION-PLAN-001",
            generated_at="2026-08-11T00:00:00Z",
        )
        paths = {item["path"] for item in report["working_context"]["items"]}

        self.assertEqual(report["schema"], SCHEMA)
        self.assertTrue(report["summary"]["activation_allowed"])
        self.assertIn("SSOT/P.2_Product_Roadmap.md", paths)
        self.assertIn("docs/0.x_foundations/0.8_COS_GENESIS.md", paths)
        self.assertTrue(any("Activation" in (item["title"] or "") or "activation" in item["content_excerpt"].lower() for item in report["working_context"]["items"]))
        self.assertEqual(report["validator"]["summary"]["error"], 0)
        self.assertEqual(report["validator"]["summary"]["fatal"], 0)

    def test_human_report_names_package_boundary(self) -> None:
        with self.make_repo() as temp:
            report = ContextActivationPackageEngine(temp).run(
                goal="Activate governed context",
                consumer="ide_assistant",
                generated_at="2026-08-11T00:00:00Z",
            )
        human = render_human(report)

        self.assertIn("# Context OS Activation Package", human)
        self.assertIn("This package is derived working context, not SSOT.", human)
        self.assertIn("Canonical source artifacts remain authoritative.", human)
        self.assertIn("## Invalidation", human)

    def test_handoff_shape_preserves_package_binding_without_full_content_copy(self) -> None:
        with self.make_repo() as temp:
            engine = ContextActivationPackageEngine(temp)
            package = engine.run(
                goal="Activate governed context for handoff",
                consumer="codex",
                mission_id="V06-ACTIVATION-HANDOFF-FORMAT-001",
                generated_at="2026-08-11T00:00:00Z",
            )
            handoff = engine.build_handoff(
                package,
                package_ref="/tmp/package.json",
                generated_at="2026-08-11T00:00:00Z",
            )

        self.assertEqual(handoff["schema"], HANDOFF_SCHEMA)
        self.assertTrue(handoff["result"]["handoff_ready"])
        self.assertEqual(handoff["source_package"]["id"], package["id"])
        self.assertEqual(handoff["source_package"]["identity_hash"], package["identity_hash"])
        self.assertEqual(handoff["source_package"]["ref"], "/tmp/package.json")
        self.assertTrue(handoff["constraints"]["not_ssot"])
        self.assertFalse(handoff["constraints"]["duplicates_full_canonical_content"])
        self.assertNotIn("content_excerpt", handoff["selected_context"][0])
        self.assertIn("revalidate before acting", handoff["working_instruction"])

    def test_handoff_is_deterministic_with_fixed_time(self) -> None:
        with self.make_repo() as temp:
            engine = ContextActivationPackageEngine(temp)
            package = engine.run(
                goal="Activate governed context for handoff",
                consumer="human",
                mission_id="V06-ACTIVATION-HANDOFF-FORMAT-001",
                generated_at="2026-08-11T00:00:00Z",
            )
            first = engine.build_handoff(package, generated_at="2026-08-11T00:00:00Z")
            second = engine.build_handoff(package, generated_at="2026-08-11T00:00:00Z")

        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(first["identity_hash"], second["identity_hash"])

    def test_handoff_detects_package_drift(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            engine = ContextActivationPackageEngine(root)
            package = engine.run(
                goal="Activate governed context for handoff",
                consumer="codex",
                generated_at="2026-08-11T00:00:00Z",
            )
            write(root / "README.md", "# Example Runtime\nOwner: Maintainers\nChanged.\n")
            handoff = engine.build_handoff(package, generated_at="2026-08-11T00:00:00Z")

        self.assertFalse(handoff["result"]["handoff_ready"])
        self.assertTrue(handoff["result"]["invalidated"])
        self.assertIn("activation_package_check.source_hash_changed:README.md", handoff["result"]["failed_checks"])

    def test_handoff_human_report_names_boundaries(self) -> None:
        with self.make_repo() as temp:
            engine = ContextActivationPackageEngine(temp)
            package = engine.run(
                goal="Activate governed context for handoff",
                consumer="ide_assistant",
                generated_at="2026-08-11T00:00:00Z",
            )
            handoff = engine.build_handoff(package, generated_at="2026-08-11T00:00:00Z")
        human = render_human(handoff)

        self.assertIn("# Context OS Activation Handoff", human)
        self.assertIn("Handoff ready: yes", human)
        self.assertIn("## Governing Context", human)
        self.assertIn("This handoff is derived from an Activation Package and is not SSOT.", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
