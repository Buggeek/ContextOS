#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


HEALTH_ROOT = Path(__file__).resolve().parent
ACTIVATION_ROOT = HEALTH_ROOT.parent / "activation"
for runtime_path in (HEALTH_ROOT, ACTIVATION_ROOT):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402
from health_engine.health_engine import ContextHealthEngine  # noqa: E402
from health_engine.mission_use_evidence import (  # noqa: E402
    SCHEMA,
    MissionContextUseEvidenceEngine,
    render_human,
)


FIXED_TIME = "2026-08-16T00:00:00Z"


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
