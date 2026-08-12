#!/usr/bin/env python3
"""Release verification for v0.5 Context Construction."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


BUILDER_ROOT = Path(__file__).resolve().parent
REPO_ROOT = BUILDER_ROOT.parents[1]
for runtime_path in (
    BUILDER_ROOT,
    REPO_ROOT / "tools" / "discovery",
    REPO_ROOT / "tools" / "construction",
):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

from builder_engine.draft_promotion_execute import BuilderDraftPromotionEngine, render_human as render_promotion_human  # noqa: E402
from builder_engine.draft_review import render_human as render_review_human  # noqa: E402
from construction_engine.planning_engine import ContextConstructionPlanEngine  # noqa: E402
from discovery_engine.local_discovery import LocalDiscoveryBundleEngine  # noqa: E402
import test_builder_draft_promotion_execute as promotion_helpers  # noqa: E402
import test_builder_draft_review_decision as review_helpers  # noqa: E402


def file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def assess_json(root: Path) -> tuple[int, dict]:
    completed = subprocess.run(
        [str(REPO_ROOT / "contextos"), "assess", "--root", str(root), "--format", "json"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.stdout:
        report = json.loads(completed.stdout)
    else:
        report = {}
    return completed.returncode, report


class ContextConstructionReleaseVerifyTestCase(unittest.TestCase):
    def promotion_case(self) -> promotion_helpers.BuilderDraftPromotionExecuteTestCase:
        return promotion_helpers.BuilderDraftPromotionExecuteTestCase(methodName="run")

    def promotion_kwargs(self, preflight: dict) -> dict:
        return self.promotion_case().promotion_kwargs(preflight)

    def test_complete_create_only_lifecycle_preserves_truth_boundaries(self) -> None:
        with review_helpers.BuilderDraftReviewDecisionTestCase(methodName="run").make_repo() as review_temp, tempfile.TemporaryDirectory() as review_output:
            review_root = Path(review_temp) / "repo"
            review, _write_result, _target = review_helpers.BuilderDraftReviewDecisionTestCase(methodName="run").create_review(
                review_root, Path(review_output)
            )
            review_human = render_review_human(review)

        with self.promotion_case().make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.promotion_case().create_create_only_preflight(root, Path(output_temp))
            result = BuilderDraftPromotionEngine(root).run(
                preflight,
                generated_at="2026-08-11T00:00:06Z",
                **self.promotion_kwargs(preflight),
            )
            promotion_human = render_promotion_human(result)
            reassess_code, reassessment = assess_json(root)

        self.assertTrue(result["result"]["success"])
        self.assertEqual(result["result"]["state"], "promoted_validated")
        self.assertEqual(reassessment["schema"], "contextos.readiness.report/1")
        self.assertIn(reassess_code, {0, 7})
        self.assertTrue(result["boundaries"]["approved_is_not_canonical_without_promotion"])
        self.assertTrue(result["boundaries"]["canonical_status_requires_successful_validation"])
        self.assertFalse(result["boundaries"]["regenerated_intent"])
        self.assertFalse(result["boundaries"]["reinterpreted_draft"])
        self.assertFalse(result["constraints"]["overwrites_performed"])
        self.assertFalse(result["constraints"]["replacements_performed"])
        self.assertFalse(result["constraints"]["deletions_performed"])
        self.assertFalse(result["constraints"]["knowledge_engine_used"])
        self.assertFalse(result["constraints"]["graph_runtime_used"])
        self.assertFalse(result["constraints"]["agents_used"])
        self.assertFalse(result["constraints"]["external_connectors_used"])
        self.assertIn("Observed evidence", review_human)
        self.assertIn("inferred classification", review_human)
        self.assertIn("suggested context", review_human)
        self.assertIn("draft content", review_human)
        self.assertIn("unknowns", review_human)
        self.assertIn("approved truth", review_human)
        self.assertIn("Canonical validation succeeded: yes", promotion_human)
        self.assertIn("Rollback", promotion_human)
        json.dumps(result, sort_keys=True)

    def test_existing_canonical_target_blocks_replacement_without_mutation(self) -> None:
        with self.promotion_case().make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.promotion_case().create_existing_target_preflight(root, Path(output_temp))
            before = file_snapshot(root)
            result = BuilderDraftPromotionEngine(root).run(
                preflight,
                generated_at="2026-08-11T00:00:06Z",
                **self.promotion_kwargs(preflight),
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertFalse(result["result"]["success"])
        self.assertIn("draft_promotion.check.action_is_create_canonical_candidate", result["result"]["failed_pre_checks"])
        self.assertIn("draft_promotion.check.no_existing_canonical_target", result["result"]["failed_pre_checks"])
        self.assertFalse(result["constraints"]["overwrites_performed"])
        self.assertFalse(result["constraints"]["replacements_performed"])

    def test_drift_blocks_downstream_promotion_without_mutation(self) -> None:
        with self.promotion_case().make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.promotion_case().create_create_only_preflight(root, Path(output_temp))
            draft_path = root / preflight["canonical_write_set"]["items"][0]["source_draft_path"]
            draft_path.write_text(draft_path.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")
            before = file_snapshot(root)
            result = BuilderDraftPromotionEngine(root).run(
                preflight,
                generated_at="2026-08-11T00:00:06Z",
                **self.promotion_kwargs(preflight),
            )
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertFalse(result["result"]["success"])
        self.assertIn("draft_promotion.check.draft_hash_still_matches_preflight", result["result"]["failed_pre_checks"])

    def test_incomplete_repo_assessment_and_construction_do_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "incomplete"
            root.mkdir()
            (root / "README.md").write_text("# Incomplete Repo\n", encoding="utf-8")
            discovery = LocalDiscoveryBundleEngine(root).run()
            plan = ContextConstructionPlanEngine(root).run()
            code, report = assess_json(root)

        self.assertEqual(discovery["schema"], "contextos.discovery.bundle/1")
        self.assertEqual(plan["schema"], "contextos.construction.plan/1")
        self.assertEqual(report["schema"], "contextos.readiness.report/1")
        self.assertIn(code, {0, 7})
        self.assertGreaterEqual(plan["summary"]["blocked_action_count"], 1)

    def test_existing_example_assessment_and_discovery_are_parseable(self) -> None:
        root = REPO_ROOT / "examples" / "sample_solo_founder"
        discovery = LocalDiscoveryBundleEngine(root).run()
        plan = ContextConstructionPlanEngine(root).run()
        code, report = assess_json(root)

        self.assertEqual(discovery["schema"], "contextos.discovery.bundle/1")
        self.assertEqual(plan["schema"], "contextos.construction.plan/1")
        self.assertEqual(report["schema"], "contextos.readiness.report/1")
        self.assertIn(code, {0, 7})
        json.dumps(discovery, sort_keys=True)
        json.dumps(plan, sort_keys=True)

    def test_rollback_removes_only_exact_created_promotion_artifact(self) -> None:
        with self.promotion_case().make_repo() as temp, tempfile.TemporaryDirectory() as output_temp:
            root = Path(temp) / "repo"
            preflight = self.promotion_case().create_create_only_preflight(root, Path(output_temp))
            engine = BuilderDraftPromotionEngine(root)
            result = engine.run(preflight, generated_at="2026-08-11T00:00:06Z", **self.promotion_kwargs(preflight))
            rollback = engine.rollback(result)
            target_path = root / preflight["canonical_target"]["path"]

        self.assertTrue(result["result"]["success"])
        self.assertFalse(target_path.exists())
        self.assertFalse(rollback["constraints"]["removed_pre_existing_content"])
        self.assertFalse(rollback["constraints"]["removed_unrelated_content"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
