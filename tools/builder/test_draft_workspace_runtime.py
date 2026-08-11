#!/usr/bin/env python3
"""Tests for Context OS Draft Workspace runtime preflight."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


BUILDER_ROOT = Path(__file__).resolve().parent
if str(BUILDER_ROOT) not in sys.path:
    sys.path.insert(0, str(BUILDER_ROOT))

from builder_engine.draft_plan import BuilderDraftPlanEngine  # noqa: E402
from builder_engine.draft_workspace import (  # noqa: E402
    DEFAULT_MISSION_ID,
    DEFAULT_WORKSPACE,
    SCHEMA,
    DraftWorkspaceRuntime,
)


def write(path: Path, text: str = "# Test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_snapshot(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def ssot_doc(title: str) -> str:
    return f"""# {title}
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Test Owner

---

## Purpose

{title} fixture.

## Change Log

- 2026-08-11 - v0.1.0 - Initial creation
"""


class DraftWorkspaceRuntimeTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md", "# Draft Workspace Fixture\nOwner: Test Owner\n")
        write(root / "docs" / "1.x_architecture" / "1.5_runtime_contracts" / "1.5.1_Validator_Contract.md", "# Validator Contract\n")
        write(root / "docs" / "3.x_operation" / "3.6_COS_Human_Agent_Authority_Model.md", "# Authority\nL0 L1 L2 L3 L4 L5\n")
        write(root / "SSOT" / "README.md", "# SSOT\n\nCompliance profile: `strict`\n")
        write(root / "SSOT" / "S.1_Vision.md", ssot_doc("Vision"))
        return temp

    def draftable_plan(self, root: Path) -> dict:
        plan = BuilderDraftPlanEngine(root).run(generated_at="2026-08-11T00:00:00Z")
        plan = copy.deepcopy(plan)
        item = next(item for item in plan["draft_items"] if item["target_context_artifact"] == "SSOT/P.1_Product_Map.md")
        item["status"] = "draftable"
        item["support"] = {
            "level": "moderate",
            "confidence": "test_fixture_support",
            "evidence_count": 2,
        }
        item["contradictions"] = []
        item["provenance_chain"]["evidence_refs"] = ["README.md", item["source_candidate_id"]]
        plan["summary"]["draftable_count"] += 1
        plan["summary"]["blocked_count"] = max(0, plan["summary"]["blocked_count"] - 1)
        return plan

    def test_workspace_preflight_shape_and_read_only_guarantees(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = file_snapshot(root)
            plan = self.draftable_plan(root)
            report = DraftWorkspaceRuntime(root).run(plan, generated_at="2026-08-11T00:00:01Z")
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(report["schema"], SCHEMA)
        self.assertTrue(report["read_only"])
        self.assertFalse(report["draft_workspace"]["exists"])
        self.assertFalse(report["constraints"]["directories_created"])
        self.assertFalse(report["constraints"]["drafts_created"])
        self.assertFalse(report["constraints"]["canonical_context_modified"])

    def test_draftable_item_resolves_inside_contextos_drafts(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            report = DraftWorkspaceRuntime(root).run(self.draftable_plan(root), generated_at="2026-08-11T00:00:01Z")

        targets = {target["target_context_artifact"]: target for target in report["targets"]}
        product = targets["SSOT/P.1_Product_Map.md"]

        self.assertEqual(product["status"], "eligible")
        self.assertEqual(product["draft_workspace_target_path"], f"{DEFAULT_WORKSPACE}/{DEFAULT_MISSION_ID}/artifacts/SSOT/P.1_Product_Map.md")
        self.assertTrue(product["path_resolution"]["inside_workspace"])
        self.assertTrue(product["state"]["no_overwrite_satisfied"])
        self.assertEqual(product["authority_required"]["capability"], "builder.draft.create")
        self.assertFalse(product["authority_required"]["promotion_authorized"])

    def test_existing_draft_target_blocks_no_overwrite(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            write(root / DEFAULT_WORKSPACE / DEFAULT_MISSION_ID / "artifacts" / "SSOT" / "P.1_Product_Map.md", "# Existing draft\n")
            report = DraftWorkspaceRuntime(root).run(self.draftable_plan(root), generated_at="2026-08-11T00:00:01Z")

        product = {target["target_context_artifact"]: target for target in report["targets"]}["SSOT/P.1_Product_Map.md"]

        self.assertEqual(product["status"], "ineligible")
        self.assertIn("target.check.target_missing", product["failed_checks"])
        self.assertIn("target.check.no_overwrite", product["failed_checks"])

    def test_path_traversal_or_workspace_escape_is_blocked(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            plan = self.draftable_plan(root)
            item = next(item for item in plan["draft_items"] if item["target_context_artifact"] == "SSOT/P.1_Product_Map.md")
            item["target_context_artifact"] = "../../../../../SSOT/P.1_Product_Map.md"
            report = DraftWorkspaceRuntime(root).run(plan, generated_at="2026-08-11T00:00:01Z")

        escaped = next(target for target in report["targets"] if target["draft_item_id"] == item["id"])

        self.assertEqual(escaped["status"], "ineligible")
        self.assertIn("target.check.workspace_boundary", escaped["failed_checks"])
        self.assertIn("target.check.no_path_traversal", escaped["failed_checks"])

    def test_drift_invalidates_source_plan_identity(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            plan = BuilderDraftPlanEngine(root).run(generated_at="2026-08-11T00:00:00Z")
            write(root / "SSOT" / "P.1_Product_Map.md", ssot_doc("Product Map"))
            report = DraftWorkspaceRuntime(root).run(plan, generated_at="2026-08-11T00:00:01Z")

        self.assertFalse(report["source_plan"]["identity_bound"])
        self.assertIn("drift.check.draft_plan_identity_bound", report["eligibility"]["failed_checks"])
        self.assertIn("drift.check.discovery_fingerprint_bound", report["eligibility"]["failed_checks"])

    def test_json_report_is_serializable_and_deterministic_with_fixed_time(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            plan = self.draftable_plan(root)
            first = DraftWorkspaceRuntime(root).run(plan, generated_at="2026-08-11T00:00:01Z")
            second = DraftWorkspaceRuntime(root).run(plan, generated_at="2026-08-11T00:00:02Z")
            loaded = json.loads(json.dumps(first, sort_keys=True))

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["identity_hash"], second["identity_hash"])

    def test_contextos_repo_dogfood_preserves_validator_gate(self) -> None:
        report = DraftWorkspaceRuntime(".").run(generated_at="2026-08-11T00:00:00Z")

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["validation"]["validator"]["summary"]["error"], 0)
        self.assertEqual(report["validation"]["validator"]["summary"]["fatal"], 0)
        self.assertFalse(report["constraints"]["writes_performed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
