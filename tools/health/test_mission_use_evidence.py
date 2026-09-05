#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


HEALTH_ROOT = Path(__file__).resolve().parent
ACTIVATION_ROOT = HEALTH_ROOT.parent / "activation"
ADOPTION_ROOT = HEALTH_ROOT.parent / "adoption"
REASONING_ROOT = HEALTH_ROOT.parent / "reasoning"
for runtime_path in (HEALTH_ROOT, ACTIVATION_ROOT, ADOPTION_ROOT, REASONING_ROOT):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402
from adoption_engine import AdoptionProfile  # noqa: E402
from health_engine.health_engine import ContextHealthEngine  # noqa: E402
from health_engine.mission_use_evidence import (  # noqa: E402
    SCHEMA,
    MissionContextUseEvidenceEngine,
    render_human,
)
from reasoning_engine import WorkOwnershipResolver  # noqa: E402


FIXED_TIME = "2026-08-16T00:00:00Z"
PROFILE_PATH = Path(__file__).resolve().parents[2] / "examples" / "adoption_profiles" / "lukspeed.json"


class MissionContextUseEvidenceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.activation = ContextActivationPackageEngine(".")
        cls.package = cls.activation.run(
            goal="Measure context use evidence for Context Health",
            consumer="codex",
            mission_id="V07-CONTEXT-USE-EVIDENCE-TEST",
            max_artifacts=5,
            generated_at=FIXED_TIME,
        )
        cls.handoff = cls.activation.build_handoff(cls.package, generated_at=FIXED_TIME)
        cls.selected_ref = cls.handoff["selected_context"][0]["path"]

    def build_evidence(self, **overrides: object) -> dict:
        inputs = {
            "package": self.package,
            "handoff": self.handoff,
            "selected_accesses": [
                {
                    "source_ref": self.selected_ref,
                    "evidence_semantics": "observed",
                    "evidence_refs": ["test.execution_log"],
                }
            ],
            "execution_retrievals": [
                {
                    "source_ref": "tools/health/health_engine/health_engine.py",
                    "source_type": "runtime_implementation",
                    "reason": "Implement the Health integration.",
                    "mission_need": "Safely modify the existing integration boundary.",
                    "authority": "mission_execution_read",
                    "evidence_semantics": "observed",
                    "evidence_refs": ["test.execution_log"],
                }
            ],
            "use_assertions": [],
            "mission_outcome": {
                "status": "completed",
                "statement": "Controlled test completed.",
                "evidence_semantics": "observed",
                "evidence_refs": ["test.result"],
            },
            "generated_at": FIXED_TIME,
        }
        inputs.update(overrides)
        return MissionContextUseEvidenceEngine(".").run(**inputs)

    def test_model_preserves_selected_accessed_used_and_useful_distinctions(self) -> None:
        report = self.build_evidence()

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["summary"]["selected_accessed_count"], 1)
        self.assertEqual(report["summary"]["execution_retrieval_count"], 1)
        self.assertEqual(report["summary"]["used_assertion_count"], 0)
        self.assertEqual(report["summary"]["useful_assertion_count"], 0)
        selected = report["context_participation"]["governing_context_selected"][0]
        self.assertEqual(selected["consumption_state"], "unknown")
        self.assertEqual(selected["use_state"], "unknown")
        self.assertEqual(selected["usefulness_state"], "unknown")
        self.assertNotIn("work_ownership", report["bindings"])
        self.assertNotIn("work_ownership_resolution", report["context_participation"])
        self.assertNotIn("work_ownership_resolution_performed", report["summary"])

    def test_declared_usefulness_is_not_promoted_to_observed(self) -> None:
        report = self.build_evidence(
            use_assertions=[
                {
                    "state": "useful",
                    "source_ref": self.selected_ref,
                    "statement": "Consumer reports that the source helped.",
                    "evidence_semantics": "declared",
                    "evidence_refs": ["consumer.declaration"],
                }
            ]
        )

        assertion = report["context_participation"]["use_assertions"][0]
        self.assertEqual(assertion["evidence_semantics"], "declared")
        self.assertEqual(report["summary"]["evidence_semantics_counts"]["observed"], 3)

    def test_identity_is_deterministic_with_fixed_inputs(self) -> None:
        first = self.build_evidence()
        second = self.build_evidence()

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["identity_hash"], second["identity_hash"])
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_unselected_access_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "not bound"):
            self.build_evidence(
                selected_accesses=[
                    {
                        "source_ref": "not/selected",
                        "evidence_semantics": "observed",
                        "evidence_refs": [],
                    }
                ]
            )

    def test_invalid_handoff_is_explicit_not_silently_accepted(self) -> None:
        handoff = copy.deepcopy(self.handoff)
        handoff["identity_hash"] = "changed"
        report = self.build_evidence(handoff=handoff)

        self.assertFalse(report["validity"]["handoff_valid_at_capture"])
        self.assertIn("activation_handoff_check.identity_hash_mismatch", report["validity"]["failed_checks"])

    def test_package_must_match_exact_handoff_binding(self) -> None:
        other_package = copy.deepcopy(self.package)
        other_package["id"] = "activation.package.other"
        report = self.build_evidence(package=other_package)

        self.assertFalse(report["validity"]["package_handoff_binding_matches"])
        self.assertIn("mission_use.package_handoff_binding_mismatch", report["validity"]["failed_checks"])

    def test_unknown_usefulness_assertion_cannot_make_health_healthy(self) -> None:
        evidence = self.build_evidence(
            use_assertions=[
                {
                    "state": "useful",
                    "source_ref": self.selected_ref,
                    "statement": "Usefulness could not be established.",
                    "evidence_semantics": "unknown",
                    "evidence_refs": [],
                }
            ]
        )
        health = ContextHealthEngine(".").run(mission_use_evidence=evidence, generated_at=FIXED_TIME)
        signals = {item["kind"]: item for item in health["dimensions"]["usefulness"]["signals"]}

        self.assertEqual(evidence["summary"]["supported_useful_assertion_count"], 0)
        self.assertEqual(signals["usefulness_effect"]["status"], "unknown")

    def test_engine_is_read_only(self) -> None:
        root = Path(".").resolve()
        before = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
        MissionContextUseEvidenceEngine(root).run(
            package=self.package,
            handoff=self.handoff,
            generated_at=FIXED_TIME,
        )
        after = {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_health_explains_participation_but_preserves_unknown_usefulness(self) -> None:
        evidence = self.build_evidence()
        health = ContextHealthEngine(".").run(mission_use_evidence=evidence, generated_at=FIXED_TIME)
        signals = {item["kind"]: item for item in health["dimensions"]["usefulness"]["signals"]}

        self.assertEqual(signals["per_source_usage_traceability"]["status"], "healthy")
        self.assertEqual(signals["usefulness_effect"]["status"], "unknown")
        self.assertEqual(health["dimensions"]["usefulness"]["status"], "unknown")
        self.assertEqual(health["evidence_sources"]["mission_use"]["id"], evidence["id"])

    def test_human_report_exposes_epistemic_boundary(self) -> None:
        human = render_human(self.build_evidence())

        self.assertIn("# Context OS Mission-Use Evidence", human)
        self.assertIn("Selected does not imply retrieved", human)
        self.assertIn("Used does not imply useful", human)
        self.assertIn("unknown, not unused", human)

    def test_work_ownership_evidence_records_duplicate_prevention_without_claiming_benefit(self) -> None:
        source = "docs/1.x_architecture/1.5_runtime_contracts/1.5.4_Mission_Contract.md"
        resolver = WorkOwnershipResolver(".")
        resolution = resolver.run(
            need={"id": "need.mission-contract", "statement": "Evolve governed Missions.", "scope": "runtime"},
            work_items=[
                {
                    "id": "mission.current",
                    "kind": "mission",
                    "title": "Current governed Mission",
                    "owner": "mission-owner",
                    "lifecycle_state": "active",
                    "currentness": "current",
                    "need_refs": ["need.mission-contract"],
                    "source_ids": ["source.mission-contract"],
                    "authority_status": "authorized",
                    "evidence_refs": ["source.mission-contract"],
                }
            ],
            source_declarations=[
                {"id": "source.mission-contract", "locator": source, "concept": "goals_missions"}
            ],
            coverage={
                "status": "complete",
                "scope": "runtime",
                "source_ids": ["source.mission-contract"],
                "authority_status": "governed_test_coverage",
                "evidence_refs": ["source.mission-contract"],
            },
            generated_at=FIXED_TIME,
        )
        check = resolver.check_resolution(resolution, generated_at=FIXED_TIME)
        report = self.build_evidence(
            work_ownership_resolution=resolution,
            work_ownership_check=check,
        )

        ownership = report["context_participation"]["work_ownership_resolution"]
        self.assertTrue(ownership["duplicate_proposal_prevented"])
        self.assertEqual(ownership["human_intervention_avoided"], "unknown")
        self.assertTrue(report["summary"]["material_currentness_check_performed"])
        self.assertFalse(report["epistemic_boundaries"]["duplicate_prevention_implies_burden_reduction"])

    def external_evidence(self, **overrides: object) -> tuple[tempfile.TemporaryDirectory, dict]:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        profile = AdoptionProfile(PROFILE_PATH)
        for record in profile.source_records(root):
            path = root / record["locator"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"# {record['concept']}\n\nExternal governed evidence.\n", encoding="utf-8")
        activation = ContextActivationPackageEngine(root, profile)
        package = activation.run(
            goal="Reconcile external active execution evidence",
            mission_id="EXTERNAL-MISSION-USE-001",
            consumer="codex",
            generated_at=FIXED_TIME,
        )
        handoff = activation.build_handoff(package, generated_at=FIXED_TIME)
        inputs = {
            "package": package,
            "handoff": handoff,
            "target_identity": {
                "organization": "Lukspeed",
                "repository": "LKSPDEV/lukspeed",
                "evidence_semantics": "declared",
                "evidence_refs": ["mission.repository_preflight"],
            },
            "context_sufficiency": {
                "status": "partial",
                "statement": "The package oriented execution; one additional evidence source was required.",
                "evidence_semantics": "declared",
                "evidence_refs": ["mission.closure"],
            },
            "prior_art_reuse": [
                {
                    "statement": "Prior closure evidence was reused.",
                    "evidence_semantics": "observed",
                    "evidence_refs": ["mission.evidence.prior_art"],
                }
            ],
            "rejected_recommendations": [
                {
                    "statement": "A non-canonical recommendation was rejected.",
                    "evidence_semantics": "observed",
                    "evidence_refs": ["mission.decision.rejected"],
                }
            ],
            "authority_escalations": [
                {
                    "statement": "Remote publication required separate authority.",
                    "evidence_semantics": "observed",
                    "evidence_refs": ["mission.authority.escalation"],
                }
            ],
            "human_interventions": [
                {
                    "intervention_type": "procedural",
                    "actor": "Mission Owner",
                    "reason": "Confirm the isolated execution procedure.",
                    "evidence_semantics": "declared",
                    "evidence_refs": ["mission.intervention.procedural"],
                },
                {
                    "intervention_type": "strategic",
                    "actor": "Product Owner",
                    "reason": "Resolve one active-priority ambiguity.",
                    "evidence_semantics": "declared",
                    "evidence_refs": ["mission.intervention.strategic"],
                },
            ],
            "automatic_consequences": [
                {
                    "trigger_action_ref": "mission.action.pull_request_created",
                    "consequence": "preview_deployment_started",
                    "platform": "repository_platform",
                    "execution_mode": "platform_automatic",
                    "manual_authority_granted": False,
                    "downstream_manual_operations_authorized": False,
                    "evidence_semantics": "observed",
                    "evidence_refs": ["mission.platform.check"],
                }
            ],
            "mission_outcome": {
                "status": "completed",
                "statement": "External docs-only Mission completed.",
                "evidence_semantics": "observed",
                "evidence_refs": ["mission.closure"],
            },
            "generated_at": FIXED_TIME,
        }
        inputs.update(overrides)
        return temp, MissionContextUseEvidenceEngine(root, profile).run(**inputs)

    def test_external_mission_use_binds_profile_target_and_learning_evidence(self) -> None:
        temp, report = self.external_evidence()

        self.assertEqual(report["bindings"]["adoption_profile"]["id"], "adoption.profile.lukspeed.v1")
        self.assertEqual(report["bindings"]["target"]["repository"], "LKSPDEV/lukspeed")
        self.assertTrue(report["validity"]["adoption_profile_valid_at_capture"])
        self.assertEqual(report["summary"]["context_sufficiency"], "partial")
        self.assertEqual(report["summary"]["prior_art_reuse_count"], 1)
        self.assertEqual(report["summary"]["rejected_recommendation_count"], 1)
        self.assertEqual(report["summary"]["authority_escalation_count"], 1)
        self.assertEqual(report["summary"]["human_procedural_intervention_count"], 1)
        self.assertEqual(report["summary"]["human_strategic_intervention_count"], 1)

    def test_automatic_consequence_records_no_manual_authority(self) -> None:
        temp, report = self.external_evidence()
        consequence = report["context_participation"]["automatic_consequences"][0]

        self.assertFalse(consequence["manual_authority_granted"])
        self.assertFalse(consequence["downstream_manual_operations_authorized"])
        self.assertFalse(report["epistemic_boundaries"]["automatic_consequence_implies_manual_authority"])
        self.assertIn("does not imply delegated manual authority", render_human(report))

    def test_automatic_consequence_cannot_smuggle_manual_authority(self) -> None:
        consequence = {
            "trigger_action_ref": "mission.action.pull_request_created",
            "consequence": "preview_deployment_started",
            "platform": "repository_platform",
            "execution_mode": "platform_automatic",
            "manual_authority_granted": True,
            "downstream_manual_operations_authorized": False,
            "evidence_semantics": "observed",
            "evidence_refs": [],
        }
        with self.assertRaisesRegex(ValueError, "grant no manual authority"):
            temp, _report = self.external_evidence(automatic_consequences=[consequence])
            temp.cleanup()


if __name__ == "__main__":
    unittest.main(verbosity=2)
