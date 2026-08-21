#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


MEMORY_ROOT = Path(__file__).resolve().parent
if str(MEMORY_ROOT) not in sys.path:
    sys.path.insert(0, str(MEMORY_ROOT))

from memory_engine.continuity_engine import file_hash, stable_hash  # noqa: E402
from memory_engine.retention_resolution_engine import RetentionResolutionEngine  # noqa: E402
from memory_engine.retention_resolution_report_builder import (  # noqa: E402
    CHECK_SCHEMA,
    SCHEMA,
    render_human,
)


FIXED_TIME = "2026-08-21T12:00:00Z"


def memory_item(**updates: object) -> dict:
    item = {
        "id": "memory.mission.test",
        "form": "mission",
        "organization": "contextos",
        "operation": "product",
        "tier": "organizational",
        "owner": "Context OS Maintainers",
        "sensitivity": "internal",
        "retention_state": "historical",
        "metadata_visibility": "full",
        "temporal": {"observed_at": "2026-08-20T12:00:00Z", "valid_until": None},
        "truth": {
            "epistemic_support": "observed",
            "governance_lifecycle": "canonical",
            "strategic_belief": None,
        },
        "required_policy_refs": ["policy.contextos.mission"],
        "evidence_refs": ["evidence:test"],
    }
    item.update(updates)
    return item


def policy(**updates: object) -> dict:
    value = {
        "schema": "contextos.memory.retention_policy/1",
        "id": "policy.contextos.mission",
        "version": "1",
        "status": "active",
        "scope": {"organizations": ["contextos"], "memory_forms": ["mission"]},
        "effects": {
            "access": "normal",
            "retrieval": "normal",
            "activation": "normal",
            "retention_transition": "elevated_authority",
            "destructive_action": "prohibited",
        },
        "obligations": [{"id": "preserve.audit", "kind": "preserve"}],
        "holds": [],
        "required_authority": {"retention_transition": ["governance_role"]},
        "inherits_from": [],
        "explanation_visibility": "id_only",
    }
    value.update(updates)
    return value


def snapshot(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


class RetentionResolutionTestCase(unittest.TestCase):
    def test_resolves_operations_independently_without_granting_authority(self) -> None:
        report = RetentionResolutionEngine(".").run(
            memory_item(), [policy()], consumer="memory_retrieval", generated_at=FIXED_TIME
        )

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["operation_results"]["access"]["outcome"], "normal")
        self.assertEqual(report["operation_results"]["retrieval"]["outcome"], "normal")
        self.assertEqual(report["operation_results"]["activation"]["outcome"], "excluded")
        self.assertEqual(report["operation_results"]["retention_transition"]["outcome"], "elevated_authority")
        self.assertEqual(report["operation_results"]["destructive_action"]["outcome"], "prohibited")
        self.assertFalse(report["authority"]["authority_granted"])
        self.assertFalse(report["mutation"]["occurred"])
        rendered = render_human(report)
        self.assertIn("## Operation Results", rendered)
        self.assertIn("## Policies Evaluated", rendered)
        self.assertIn("## Authority Boundary", rendered)
        self.assertIn("Mutation occurred: no", rendered)

    def test_resolution_is_deterministic_and_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "source.md").write_text("Evidence\n", encoding="utf-8")
            item = memory_item(provenance={"path": "source.md", "source_hash": file_hash(root / "source.md")})
            before = snapshot(root)
            first = RetentionResolutionEngine(root).run(item, [policy()], consumer="human", generated_at=FIXED_TIME)
            second = RetentionResolutionEngine(root).run(item, [policy()], consumer="human", generated_at=FIXED_TIME)
            after = snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))

    def test_no_policy_never_becomes_implicit_permission(self) -> None:
        report = RetentionResolutionEngine(".").run(
            memory_item(required_policy_refs=[]), [], consumer="human", generated_at=FIXED_TIME
        )

        self.assertTrue(report["unresolved_requirements"])
        self.assertNotIn("normal", {result["outcome"] for result in report["operation_results"].values()})
        self.assertEqual(report["operation_results"]["retention_transition"]["outcome"], "prohibited")
        self.assertEqual(report["operation_results"]["destructive_action"]["outcome"], "prohibited")

    def test_preservation_removal_conflict_blocks_transition(self) -> None:
        preserve = policy()
        minimize = policy(
            id="policy.contextos.minimize",
            obligations=[{"id": "minimize.data", "kind": "minimize"}],
        )
        report = RetentionResolutionEngine(".").run(
            memory_item(required_policy_refs=[]), [preserve, minimize], consumer="human", generated_at=FIXED_TIME
        )

        self.assertEqual(report["summary"]["status"], "blocked")
        self.assertEqual(report["conflicts"][0]["kind"], "preservation_vs_deletion_or_minimization")
        self.assertEqual(report["operation_results"]["retention_transition"]["outcome"], "prohibited")

    def test_active_hold_blocks_transition(self) -> None:
        held = policy(
            holds=[
                {
                    "id": "hold.legal.001",
                    "active": True,
                    "required_roles": ["legal_compliance_role"],
                    "metadata_visibility": "none",
                }
            ]
        )
        report = RetentionResolutionEngine(".").run(
            memory_item(), [held], consumer="human", generated_at=FIXED_TIME
        )

        self.assertEqual(report["operation_results"]["retention_transition"]["outcome"], "prohibited")
        self.assertIn("legal_compliance_role", report["authority"]["by_operation"]["retention_transition"]["required_roles"])
        self.assertEqual(report["holds"][0]["display_id"], "<restricted>")

    def test_unknown_scope_metadata_preserves_unknown_applicability(self) -> None:
        scoped = policy(scope={"organizations": ["contextos"], "memory_tiers": ["regulated"]})
        report = RetentionResolutionEngine(".").run(
            memory_item(tier="unknown", required_policy_refs=[]), [scoped], consumer="human", generated_at=FIXED_TIME
        )

        self.assertEqual(report["policy_evaluation"]["not_applied"][0]["reason"], "policy_applicability_unknown")
        self.assertTrue(any(item["kind"] == "policy_applicability_unknown" for item in report["unresolved_requirements"]))

    def test_temporal_policy_scope_is_evaluated_without_inventing_applicability(self) -> None:
        future = policy(effective_from="2026-08-22T00:00:00Z")
        invalid = policy(id="policy.contextos.invalid-time", effective_from="not-a-time")
        report = RetentionResolutionEngine(".").run(
            memory_item(required_policy_refs=[]), [future, invalid], consumer="human", generated_at=FIXED_TIME
        )

        reasons = {item["reason"] for item in report["policy_evaluation"]["not_applied"]}
        self.assertIn("policy_not_yet_effective", reasons)
        self.assertIn("policy_temporal_applicability_unknown", reasons)
        self.assertTrue(
            any(item["kind"] == "policy_temporal_applicability_unknown" for item in report["unresolved_requirements"])
        )

    def test_context_and_affected_parties_are_bound_without_becoming_authority(self) -> None:
        report = RetentionResolutionEngine(".").run(
            memory_item(affected_parties=["customer"], jurisdiction="organization_defined"),
            [policy()],
            consumer="human",
            organizational_mode="organization",
            authority_scope="audit-only",
            generated_at=FIXED_TIME,
        )

        self.assertEqual(report["memory"]["affected_parties"], ["customer"])
        self.assertEqual(report["memory"]["jurisdiction"], "organization_defined")
        self.assertEqual(report["request"]["organizational_mode"], "organization")
        self.assertEqual(report["request"]["authority_scope"], "audit-only")
        self.assertFalse(report["authority"]["authority_granted"])

    def test_required_roles_change_operation_outcome_but_never_grant_authority(self) -> None:
        guarded = policy(required_authority={"retrieval": ["memory_owner"]})
        missing = RetentionResolutionEngine(".").run(
            memory_item(), [guarded], consumer="human", generated_at=FIXED_TIME
        )
        present = RetentionResolutionEngine(".").run(
            memory_item(), [guarded], consumer="human", actor_roles=["memory_owner"], generated_at=FIXED_TIME
        )

        self.assertEqual(missing["operation_results"]["retrieval"]["outcome"], "elevated_authority")
        self.assertEqual(present["operation_results"]["retrieval"]["outcome"], "normal")
        self.assertTrue(present["authority"]["by_operation"]["retrieval"]["roles_present"])
        self.assertFalse(present["authority"]["by_operation"]["retrieval"]["authority_granted"])

    def test_truth_retention_and_access_axes_remain_independent(self) -> None:
        report = RetentionResolutionEngine(".").run(
            memory_item(retention_state="archived"), [policy()], consumer="human", generated_at=FIXED_TIME
        )

        self.assertEqual(report["memory"]["truth"]["governance_lifecycle"], "canonical")
        self.assertEqual(report["memory"]["retention_state"], "archived")
        self.assertEqual(report["operation_results"]["retrieval"]["outcome"], "elevated_authority")
        self.assertEqual(report["operation_results"]["activation"]["outcome"], "excluded")

    def test_restricted_memory_and_policy_do_not_leak_metadata(self) -> None:
        secret = "policy.secret.personnel"
        hidden_policy = policy(id=secret, explanation_visibility="none")
        item = memory_item(
            id="memory.secret.personnel",
            sensitivity="restricted",
            metadata_visibility="none",
            required_policy_refs=[secret],
            evidence_refs=["secret:evidence:path"],
        )
        report = RetentionResolutionEngine(".").run(
            item, [hidden_policy], consumer="auditor", generated_at=FIXED_TIME
        )
        rendered = render_human(report)
        serialized = json.dumps(report, sort_keys=True)

        self.assertNotIn("memory.secret.personnel", serialized)
        self.assertNotIn(secret, serialized)
        self.assertNotIn(stable_hash("memory.secret.personnel"), serialized)
        self.assertNotIn(stable_hash(secret), serialized)
        self.assertNotIn("secret:evidence:path", serialized)
        self.assertNotIn("restricted_sensitivity", serialized)
        self.assertIn("<restricted>", rendered)
        check = RetentionResolutionEngine(".").check_resolution(
            report, item, [hidden_policy], consumer="auditor", generated_at=FIXED_TIME
        )
        self.assertTrue(check["result"]["valid"])

    def test_check_detects_policy_and_source_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.md"
            source.write_text("Evidence\n", encoding="utf-8")
            item = memory_item(provenance={"path": "source.md", "source_hash": file_hash(source)})
            engine = RetentionResolutionEngine(root)
            report = engine.run(item, [policy()], consumer="human", generated_at=FIXED_TIME)
            valid = engine.check_resolution(report, item, [policy()], consumer="human", generated_at=FIXED_TIME)
            changed_policy = copy.deepcopy(policy())
            changed_policy["version"] = "2"
            policy_drift = engine.check_resolution(
                report, item, [changed_policy], consumer="human", generated_at=FIXED_TIME
            )
            source.write_text("Changed evidence\n", encoding="utf-8")
            source_drift = engine.check_resolution(
                report, item, [policy()], consumer="human", generated_at=FIXED_TIME
            )

        self.assertEqual(valid["schema"], CHECK_SCHEMA)
        self.assertTrue(valid["result"]["valid"])
        self.assertIn("retention_resolution_check.input_changed", policy_drift["result"]["failed_checks"])
        self.assertIn("retention_resolution_check.source_state_changed", source_drift["result"]["failed_checks"])

    def test_tampering_invalidates_resolution_identity(self) -> None:
        engine = RetentionResolutionEngine(".")
        report = engine.run(memory_item(), [policy()], consumer="human", generated_at=FIXED_TIME)
        report["operation_results"]["retrieval"]["outcome"] = "prohibited"
        check = engine.check_resolution(
            report, memory_item(), [policy()], consumer="human", generated_at=FIXED_TIME
        )

        self.assertFalse(check["checks"]["identity_valid"])
        self.assertIn("retention_resolution_check.identity_hash_mismatch", check["result"]["failed_checks"])


if __name__ == "__main__":
    unittest.main()
