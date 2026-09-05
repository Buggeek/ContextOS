#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
for runtime_root in (ROOT / "tools/reasoning", ROOT / "tools/adoption", ROOT / "tools/memory", ROOT / "tools/activation"):
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))

from adoption_engine import AdoptionProfile  # noqa: E402
from reasoning_engine import ContextualAssessmentEngine, WorkOwnershipResolver  # noqa: E402
from reasoning_engine.assessment_engine import stable_hash as assessment_hash  # noqa: E402
from test_memory_context_version_integration import exact_version  # noqa: E402
from test_memory_retrieval import FIXED_TIME, make_repo  # noqa: E402


NEED = {
    "id": "need.customer-orientation",
    "statement": "Improve customer orientation without duplicating current work.",
    "scope": "product-experience",
    "evidence_refs": ["signal.customer-review"],
}


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def init_git(root: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Context OS Tests"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "tests@contextos.local"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)


class WorkOwnershipResolutionTestCase(unittest.TestCase):
    def fixture(self) -> tuple[tempfile.TemporaryDirectory[str], Path, WorkOwnershipResolver, list[dict]]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "governed/work.md", "# Current Work\n\nNo matching work is active.\n")
        init_git(root)
        engine = WorkOwnershipResolver(root)
        sources = [{"id": "source.current-work", "locator": "governed/work.md", "concept": "active_work"}]
        return temp, root, engine, sources

    @staticmethod
    def work(state: str, **overrides: object) -> dict:
        item = {
            "id": f"mission.{state}",
            "kind": "mission",
            "title": f"Mission in {state}",
            "owner": "accountable-human",
            "lifecycle_state": state,
            "currentness": "current",
            "need_refs": [NEED["id"]],
            "parent_work_id": None,
            "source_ids": ["source.current-work"],
            "authority_status": "target_authority",
            "return_condition": "Re-evaluate after the recorded boundary clears.",
            "evidence_refs": ["source.current-work"],
        }
        item.update(overrides)
        return item

    @staticmethod
    def coverage() -> dict:
        return {
            "status": "complete",
            "scope": NEED["scope"],
            "source_ids": ["source.current-work"],
            "authority_status": "governed_test_coverage",
            "evidence_refs": ["source.current-work"],
        }

    def resolve(self, engine: WorkOwnershipResolver, sources: list[dict], items: list[dict]) -> dict:
        return engine.run(
            need=NEED,
            work_items=items,
            source_declarations=sources,
            coverage=self.coverage(),
            generated_at=FIXED_TIME,
        )

    def test_no_existing_ownership_is_eligible_for_normal_goal_qualification(self) -> None:
        temp, _root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        report = self.resolve(engine, sources, [])

        self.assertEqual(report["result"]["disposition"], "QUALIFY_NEW_WORK")
        self.assertTrue(report["result"]["eligible_for_goal_qualification"])
        self.assertFalse(report["result"]["duplicate_work_prevented"])

    def test_active_mission_prevents_parallel_work(self) -> None:
        temp, _root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        report = self.resolve(engine, sources, [self.work("active")])

        self.assertEqual(report["result"]["disposition"], "OBSERVE_EXISTING_WORK")
        self.assertTrue(report["result"]["duplicate_work_prevented"])
        self.assertFalse(report["result"]["eligible_for_goal_qualification"])

    def test_human_decision_and_evidence_waits_remain_distinct(self) -> None:
        temp, _root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        human = self.resolve(engine, sources, [self.work("awaiting_human_decision")])
        evidence = self.resolve(engine, sources, [self.work("awaiting_evidence")])

        self.assertEqual(human["result"]["disposition"], "AWAIT_HUMAN_DECISION")
        self.assertEqual(evidence["result"]["disposition"], "AWAIT_EVIDENCE")
        self.assertTrue(human["result"]["duplicate_work_prevented"])
        self.assertTrue(evidence["result"]["duplicate_work_prevented"])

    def test_closed_historical_or_superseded_work_does_not_block_qualification(self) -> None:
        temp, _root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        items = [
            self.work("closed", id="mission.closed", currentness="historical"),
            self.work("superseded", id="mission.superseded", currentness="historical"),
            self.work("completed", id="mission.completed", currentness="historical"),
        ]
        report = self.resolve(engine, sources, items)

        self.assertEqual(report["result"]["disposition"], "QUALIFY_NEW_WORK")
        self.assertEqual(len(report["ownership"]["historical_or_non_owning_work"]), 3)

    def test_ambiguous_current_ownership_remains_explicit(self) -> None:
        temp, _root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        report = self.resolve(
            engine,
            sources,
            [self.work("active", id="mission.one"), self.work("active", id="mission.two")],
        )

        self.assertEqual(report["result"]["disposition"], "OWNERSHIP_CONFLICT")
        self.assertTrue(report["result"]["ownership_conflict"])
        self.assertTrue(report["result"]["duplicate_work_prevented"])
        self.assertIsNone(report["ownership"]["resolved_owner"])

    def test_linked_goal_and_mission_form_one_ownership_chain(self) -> None:
        temp, _root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        goal = self.work("active", id="goal.current", kind="goal")
        mission = self.work("active", id="mission.current", parent_work_id="goal.current")
        report = self.resolve(engine, sources, [goal, mission])

        self.assertEqual(report["result"]["disposition"], "OBSERVE_EXISTING_WORK")
        self.assertEqual(report["ownership"]["resolved_owner"]["work_id"], "mission.current")

    def test_parent_wait_state_controls_leaf_without_relabeling_leaf(self) -> None:
        temp, _root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        goal = self.work(
            "awaiting_human_decision",
            id="goal.current",
            kind="goal",
            return_condition="Await accountable product decision.",
        )
        mission = self.work("active", id="mission.current", parent_work_id="goal.current")
        report = self.resolve(engine, sources, [goal, mission])
        owner = report["ownership"]["resolved_owner"]

        self.assertEqual(report["result"]["disposition"], "AWAIT_HUMAN_DECISION")
        self.assertEqual(owner["work_id"], "mission.current")
        self.assertEqual(owner["semantic_state"], "active")
        self.assertEqual(owner["controlling_work_id"], "goal.current")
        self.assertEqual(owner["controlling_state"], "awaiting_human_decision")
        self.assertEqual(owner["return_condition"], "Await accountable product decision.")

    def test_cyclic_work_chain_is_an_explicit_conflict(self) -> None:
        temp, _root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        first = self.work("active", id="mission.first", parent_work_id="mission.second")
        second = self.work("active", id="mission.second", parent_work_id="mission.first")
        leaf = self.work("active", id="mission.leaf", parent_work_id="mission.second")
        report = self.resolve(engine, sources, [first, second, leaf])

        self.assertEqual(report["result"]["disposition"], "OWNERSHIP_CONFLICT")
        self.assertIsNone(report["ownership"]["resolved_owner"])

    def test_incomplete_coverage_does_not_infer_unowned_work(self) -> None:
        temp, _root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        coverage = self.coverage()
        coverage["status"] = "partial"
        report = engine.run(
            need=NEED,
            work_items=[],
            source_declarations=sources,
            coverage=coverage,
            generated_at=FIXED_TIME,
        )

        self.assertEqual(report["result"]["disposition"], "OWNERSHIP_UNKNOWN")
        self.assertFalse(report["result"]["eligible_for_goal_qualification"])
        self.assertFalse(report["result"]["duplicate_work_prevented"])

    def test_irrelevant_repository_tip_advance_preserves_material_currentness(self) -> None:
        temp, root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        saved = self.resolve(engine, sources, [self.work("active")])
        write(root / "unrelated.txt", "Unrelated implementation evidence.\n")
        subprocess.run(["git", "add", "unrelated.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "unrelated"], cwd=root, check=True)
        check = engine.check_resolution(saved, generated_at=FIXED_TIME)

        self.assertTrue(check["result"]["valid"])
        self.assertEqual(check["repository_state"]["tip_state"], "advanced")
        self.assertEqual(check["repository_state"]["tip_relevance"], "irrelevant_to_material_work_context")
        self.assertFalse(check["result"]["reanchor_required"])

    def test_material_work_source_change_requires_reanchor(self) -> None:
        temp, root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        saved = self.resolve(engine, sources, [self.work("active")])
        write(root / "governed/work.md", "# Current Work\n\nOwnership changed.\n")
        check = engine.check_resolution(saved, generated_at=FIXED_TIME)

        self.assertFalse(check["result"]["valid"])
        self.assertTrue(check["result"]["reanchor_required"])
        self.assertIn("work_ownership_check.material_source_changed:source.current-work", check["result"]["failed_checks"])
        self.assertTrue(check["result"]["historical_resolution_identity_valid"])

    def test_historical_context_version_survives_material_current_advance(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        make_repo(root)
        version = exact_version(root)
        source = root / "SSOT/P.1_Product_Map.md"
        source.write_text(source.read_text(encoding="utf-8") + "\nMaterial current change.\n", encoding="utf-8")
        from memory_engine import ContextVersionEngine

        check = ContextVersionEngine(root).check_version(version, generated_at=FIXED_TIME)
        self.assertTrue(check["result"]["historically_valid_identity"])
        self.assertTrue(check["result"]["material_drift"])

    def test_external_profile_translates_target_native_work_state(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        write(root / "native/current-work.txt", "Current target-native execution.\n")
        profile = AdoptionProfile(
            {
                "schema": "contextos.adoption.profile/1",
                "id": "adoption.profile.fixture.v1",
                "version": "1.0.0",
                "target": {"id": "fixture", "scope": "repository"},
                "lifecycle": {"state": "approved", "target_ssot": False},
                "authority": {"owner": "fixture-owner"},
                "mappings": [
                    {
                        "concept": "active_work",
                        "support": "declared",
                        "sources": [
                            {
                                "locator": "native/current-work.txt",
                                "authority_owner": "fixture-owner",
                                "lifecycle_state": "canonical",
                            }
                        ],
                    }
                ],
                "validation": {
                    "rules": {
                        "structure.fixture": {
                            "applicability": "target_native",
                            "enforcement": "advisory",
                            "rationale": "Fixture mapping.",
                        }
                    }
                },
                "work_ownership": {
                    "source_concepts": ["active_work"],
                    "lifecycle_semantics": {"underway": "active", "needs_person": "awaiting_human_decision"},
                },
                "evidence_isolation": {"target_only": True, "host_context_is_evidence": False},
            }
        )
        engine = WorkOwnershipResolver(root, profile)
        report = engine.run(
            need=NEED,
            work_items=[self.work("underway")],
            source_declarations=[
                {"id": "source.current-work", "locator": "native/current-work.txt", "concept": "active_work"}
            ],
            coverage=self.coverage(),
            generated_at=FIXED_TIME,
        )

        self.assertEqual(report["work_items"][0]["semantic_state"], "active")
        self.assertEqual(report["result"]["disposition"], "OBSERVE_EXISTING_WORK")
        self.assertEqual(report["bindings"]["adoption_profile"]["id"], "adoption.profile.fixture.v1")

    def test_external_profile_rejects_unmapped_work_source(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        write(root / "native/current-work.txt", "Mapped evidence.\n")
        write(root / "native/unmapped.txt", "Unmapped evidence.\n")
        profile = AdoptionProfile(
            {
                "schema": "contextos.adoption.profile/1",
                "id": "adoption.profile.fixture.v1",
                "version": "1.0.0",
                "target": {"id": "fixture", "scope": "repository"},
                "lifecycle": {"state": "approved", "target_ssot": False},
                "authority": {"owner": "fixture-owner"},
                "mappings": [
                    {
                        "concept": "active_work",
                        "support": "declared",
                        "sources": [
                            {
                                "locator": "native/current-work.txt",
                                "authority_owner": "fixture-owner",
                                "lifecycle_state": "canonical",
                            }
                        ],
                    }
                ],
                "validation": {
                    "rules": {
                        "structure.fixture": {
                            "applicability": "target_native",
                            "enforcement": "advisory",
                            "rationale": "Fixture mapping.",
                        }
                    }
                },
                "work_ownership": {
                    "source_concepts": ["active_work"],
                    "lifecycle_semantics": {"underway": "active"},
                },
                "evidence_isolation": {"target_only": True, "host_context_is_evidence": False},
            }
        )
        with self.assertRaisesRegex(ValueError, "not mapped"):
            WorkOwnershipResolver(root, profile).run(
                need=NEED,
                work_items=[],
                source_declarations=[
                    {"id": "source.current-work", "locator": "native/unmapped.txt", "concept": "active_work"}
                ],
                coverage=self.coverage(),
                generated_at=FIXED_TIME,
            )

    def test_source_symlink_cannot_escape_target_boundary(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        parent = Path(temp.name)
        root = parent / "target"
        root.mkdir()
        outside = parent / "outside.md"
        outside.write_text("Protected external evidence.\n", encoding="utf-8")
        (root / "governed").mkdir()
        (root / "governed/work.md").symlink_to(outside)
        engine = WorkOwnershipResolver(root)

        with self.assertRaisesRegex(ValueError, "resolves outside"):
            engine.run(
                need=NEED,
                work_items=[self.work("active")],
                source_declarations=[
                    {"id": "source.current-work", "locator": "governed/work.md", "concept": "active_work"}
                ],
                coverage=self.coverage(),
                generated_at=FIXED_TIME,
            )

    def test_contextual_assessment_uses_resolution_as_consequential_gate(self) -> None:
        temp, _root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        active = self.resolve(engine, sources, [self.work("active")])
        report = ContextualAssessmentEngine(engine.root).run(
            goal=NEED["statement"],
            mission_id="MISSION-QUALIFICATION-001",
            work_ownership_resolution=active,
            generated_at=FIXED_TIME,
        )

        self.assertEqual(report["consequential_recommendation_gate"]["status"], "withheld_existing_ownership")
        self.assertTrue(any("no parallel Goal or Mission" in item["statement"] for item in report["reasoning"]["interpretations"]))
        self.assertFalse(any("normal Goal qualification is eligible" in item["statement"] for item in report["reasoning"]["recommendations"]))
        json.loads(json.dumps(report, sort_keys=True))

    def test_assessment_without_resolution_preserves_legacy_identity_surface(self) -> None:
        temp, root, _engine, _sources = self.fixture()
        self.addCleanup(temp.cleanup)
        report = ContextualAssessmentEngine(root).run(
            goal=NEED["statement"],
            generated_at=FIXED_TIME,
        )
        legacy_payload = {
            "query": report["query"],
            "bindings": report["bindings"],
            "reasoning": report["reasoning"],
            "authority": report["authority"],
        }

        self.assertEqual(report["identity_hash"], assessment_hash(legacy_payload))
        self.assertNotIn("work_ownership", report["bindings"])
        self.assertNotIn("consequential_recommendation_gate", report)
        self.assertTrue(ContextualAssessmentEngine(root).check_assessment(report)["result"]["valid"])

    def test_changed_resolution_source_invalidates_assessment_reuse(self) -> None:
        temp, root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        resolution = self.resolve(engine, sources, [self.work("active")])
        assessment_engine = ContextualAssessmentEngine(root)
        report = assessment_engine.run(
            goal=NEED["statement"],
            work_ownership_resolution=resolution,
            generated_at=FIXED_TIME,
        )
        write(root / "governed/work.md", "# Current Work\n\nMaterial ownership drift.\n")
        check = assessment_engine.check_assessment(report, generated_at=FIXED_TIME)

        self.assertFalse(check["result"]["valid"])
        self.assertIn("reasoning.assessment_check.current_state_changed", check["result"]["failed_checks"])

    def test_irrelevant_tip_advance_preserves_assessment_reuse(self) -> None:
        temp, root, engine, sources = self.fixture()
        self.addCleanup(temp.cleanup)
        resolution = self.resolve(engine, sources, [self.work("active")])
        assessment_engine = ContextualAssessmentEngine(root)
        report = assessment_engine.run(
            goal=NEED["statement"],
            work_ownership_resolution=resolution,
            generated_at=FIXED_TIME,
        )
        write(root / "unrelated.txt", "Unrelated implementation evidence.\n")
        subprocess.run(["git", "add", "unrelated.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "unrelated"], cwd=root, check=True)
        check = assessment_engine.check_assessment(report, generated_at=FIXED_TIME)

        self.assertTrue(check["result"]["valid"])
        current_ownership = engine.check_resolution(resolution, generated_at=FIXED_TIME)
        self.assertEqual(
            current_ownership["repository_state"]["tip_relevance"],
            "irrelevant_to_material_work_context",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
