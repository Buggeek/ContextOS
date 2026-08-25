#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REASONING_ROOT = Path(__file__).resolve().parent
for runtime_root in (REASONING_ROOT, REASONING_ROOT.parent / "memory", REASONING_ROOT.parent / "activation"):
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))

from reasoning_engine import ContextualAssessmentEngine  # noqa: E402
from reasoning_engine.structured_evidence import SCHEMA, normalize_evidence_set  # noqa: E402
from test_memory_context_version_integration import exact_version  # noqa: E402
from test_memory_retrieval import FIXED_TIME, make_repo, snapshot  # noqa: E402


def evidence_set() -> dict:
    return {
        "schema": SCHEMA,
        "claims": [
            {
                "id": "claim.goal.status.approved",
                "subject": "goal.release-v09",
                "predicate": "status",
                "value": "approved",
                "scope": "release-v09",
                "epistemic_support": "declared",
                "governance_lifecycle": "approved",
                "authority_status": "human_decision",
                "source_refs": ["decision.release-v09"],
            },
            {
                "id": "claim.goal.status.blocked",
                "subject": "goal.release-v09",
                "predicate": "status",
                "value": "blocked",
                "scope": "release-v09",
                "epistemic_support": "observed",
                "governance_lifecycle": "suggested",
                "authority_status": "evidence_only",
                "source_refs": ["validator.gate.blocked"],
            },
        ],
        "relationships": [
            {
                "id": "rel.mission.depends-decision",
                "source": "mission.reasoning",
                "relationship": "depends_on",
                "target": "decision.memory-policy",
                "epistemic_support": "declared",
                "governance_lifecycle": "approved",
                "authority_status": "current",
                "source_refs": ["mission.packet.reasoning"],
            },
            {
                "id": "rel.decision.affects-outcome",
                "source": "decision.memory-policy",
                "relationship": "affects",
                "target": "outcome.prior-art-visible",
                "epistemic_support": "derived",
                "governance_lifecycle": "suggested",
                "authority_status": "evidence_only",
                "source_refs": ["memory.policy.result"],
            },
        ],
        "limitations": ["Relationships are explicit fixture evidence; causality is not inferred."],
    }


class StructuredReasoningEvidenceTestCase(unittest.TestCase):
    def make_fixture(self) -> tuple[tempfile.TemporaryDirectory, Path, dict]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        make_repo(root)
        return temp, root, exact_version(root)

    def test_explicit_claim_conflict_and_paths_are_derived_read_only(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        before = snapshot(root)
        report = ContextualAssessmentEngine(root).run(
            goal="Assess exact claims and relationship impact",
            context_versions=[version],
            reasoning_evidence=evidence_set(),
            focus_entities=["mission.reasoning"],
            generated_at=FIXED_TIME,
        )
        after = snapshot(root)

        self.assertEqual(before, after)
        self.assertTrue(report["reasoning"]["contradictions"])
        self.assertTrue(any("impact on" in item["statement"] for item in report["reasoning"]["interpretations"]))
        self.assertTrue(any("indirect relationship path" in item["statement"] for item in report["reasoning"]["interpretations"]))
        indirect = next(item for item in report["reasoning"]["interpretations"] if "indirect" in item["statement"])
        self.assertIn("rel.mission.depends-decision", indirect["evidence_refs"])
        self.assertIn("rel.decision.affects-outcome", indirect["evidence_refs"])
        self.assertFalse(indirect["decision"])
        self.assertFalse(indirect["canonical"])

    def test_different_scopes_do_not_become_a_contradiction(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        evidence = evidence_set()
        evidence["claims"][1]["scope"] = "release-v10"
        report = ContextualAssessmentEngine(root).run(
            goal="Compare scoped claims",
            context_versions=[version],
            reasoning_evidence=evidence,
            generated_at=FIXED_TIME,
        )

        self.assertFalse(report["reasoning"]["contradictions"])
        self.assertTrue(any("No contradiction is proven" in item["statement"] for item in report["reasoning"]["unknowns"]))

    def test_unsupported_relationship_is_not_traversed(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        evidence = evidence_set()
        evidence["relationships"][0]["relationship"] = "mentioned_near"
        evidence["relationships"] = evidence["relationships"][:1]
        report = ContextualAssessmentEngine(root).run(
            goal="Do not infer impact from proximity",
            context_versions=[version],
            reasoning_evidence=evidence,
            focus_entities=["mission.reasoning"],
            generated_at=FIXED_TIME,
        )

        self.assertFalse(any("impact on" in item["statement"] for item in report["reasoning"]["interpretations"]))
        self.assertTrue(any("No bounded impact path" in item["statement"] for item in report["reasoning"]["unknowns"]))

    def test_identity_binds_exact_evidence_and_focus(self) -> None:
        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        engine = ContextualAssessmentEngine(root)
        first = engine.run(
            goal="Bind exact evidence",
            context_versions=[version],
            reasoning_evidence=evidence_set(),
            focus_entities=["mission.reasoning"],
            generated_at=FIXED_TIME,
        )
        changed = evidence_set()
        changed["claims"][0]["value"] = "reviewed"
        second = engine.run(
            goal="Bind exact evidence",
            context_versions=[version],
            reasoning_evidence=changed,
            focus_entities=["mission.reasoning"],
            generated_at=FIXED_TIME,
        )

        self.assertNotEqual(first["identity_hash"], second["identity_hash"])
        self.assertNotEqual(
            first["bindings"]["reasoning_evidence"]["identity_hash"],
            second["bindings"]["reasoning_evidence"]["identity_hash"],
        )
        json.loads(json.dumps(first, sort_keys=True))

    def test_invalid_or_unproven_evidence_is_rejected_or_preserved(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing"):
            normalize_evidence_set({"schema": SCHEMA, "claims": [{"id": "incomplete"}]})
        normalized = normalize_evidence_set(
            {
                "schema": SCHEMA,
                "claims": [
                    {
                        "id": "claim.unknown",
                        "subject": "question.answer",
                        "predicate": "status",
                        "value": "unresolved",
                        "source_refs": ["question.open"],
                    }
                ],
            }
        )
        self.assertEqual(normalized["claims"][0]["epistemic_support"], "unknown")
        self.assertEqual(normalized["claims"][0]["authority_status"], "unknown")

    def test_duplicate_ids_and_different_time_bases_do_not_corrupt_comparison(self) -> None:
        duplicated = evidence_set()
        duplicated["claims"][1]["id"] = duplicated["claims"][0]["id"]
        with self.assertRaisesRegex(ValueError, "ids must be unique"):
            normalize_evidence_set(duplicated)

        temp, root, version = self.make_fixture()
        self.addCleanup(temp.cleanup)
        temporal = evidence_set()
        temporal["claims"][0]["temporal_basis"] = {"effective_at": "2026-01-01"}
        temporal["claims"][1]["temporal_basis"] = {"effective_at": "2026-08-24"}
        report = ContextualAssessmentEngine(root).run(
            goal="Keep historical claims distinct",
            context_versions=[version],
            reasoning_evidence=temporal,
            generated_at=FIXED_TIME,
        )
        self.assertFalse(report["reasoning"]["contradictions"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
