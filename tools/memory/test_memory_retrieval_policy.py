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

from memory_engine import MemoryRetrievalEngine, OrganizationalMemoryEngine  # noqa: E402
from memory_engine.retrieval_engine import candidate_records, tokens  # noqa: E402
from test_memory_retrieval import FIXED_TIME, make_repo, snapshot  # noqa: E402


GOAL = "memory retrieval provenance authority learning decision evidence supersession"


def policy(policy_id: str, memory_id: str, retrieval: str = "normal", **extra: object) -> dict:
    result = {
        "schema": "contextos.memory.retention_policy/1",
        "id": policy_id,
        "version": "1",
        "status": "active",
        "scope": {"memory_ids": [memory_id]},
        "effects": {"access": "normal", "retrieval": retrieval, "activation": "normal"},
        "obligations": [],
        "holds": [],
        "required_authority": {},
        "inherits_from": [],
        "explanation_visibility": "id_only",
    }
    result.update(extra)
    return result


def relevant_candidates(root: Path, count: int = 6) -> list[dict]:
    engine = MemoryRetrievalEngine(root)
    continuity = OrganizationalMemoryEngine(root).run(goal=GOAL, generated_at=FIXED_TIME)
    ranked, _ = engine._rank_relevant(candidate_records(continuity), tokens(GOAL), None)
    return [row[1] for row in ranked[:count]]


def metadata_for(candidates: list[dict]) -> dict:
    return {
        "defaults": {
            "organization": "test",
            "operation": "product",
            "tier": "organizational",
            "owner": "Test Owner",
            "sensitivity": "internal",
            "retention_state": "historical",
            "metadata_visibility": "full",
        },
        "items": {
            candidate["candidate_id"]: {"metadata_visibility": "none"}
            for candidate in candidates[1:]
        },
    }


class PolicyAwareMemoryRetrievalTestCase(unittest.TestCase):
    def test_policy_outcomes_are_independent_and_protected_metadata_does_not_leak(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            candidates = relevant_candidates(root)
            self.assertGreaterEqual(len(candidates), 6)
            normal, elevated, excluded, prohibited, missing, conflict = candidates[:6]
            policies = [
                policy("policy.normal", normal["candidate_id"]),
                policy(
                    "policy.elevated",
                    elevated["candidate_id"],
                    required_authority={"retrieval": ["memory_owner"]},
                ),
                policy("policy.excluded", excluded["candidate_id"], "excluded", explanation_visibility="none"),
                policy("policy.prohibited", prohibited["candidate_id"], "prohibited", explanation_visibility="none"),
                policy(
                    "policy.conflict",
                    conflict["candidate_id"],
                    obligations=[{"id": "obligation.interpret", "kind": "preserve", "requires_interpretation": True}],
                    explanation_visibility="none",
                ),
            ]
            report = MemoryRetrievalEngine(root).run(
                goal=GOAL,
                consumer="codex",
                purpose="Controlled policy integration test",
                retention_policies=policies,
                memory_metadata_by_id=metadata_for(candidates),
                evaluation_time=FIXED_TIME,
                generated_at=FIXED_TIME,
            )

        outcomes = report["summary"]["policy_outcomes"]
        self.assertEqual(outcomes["normal"], 1)
        self.assertEqual(outcomes["elevated_authority"], 1)
        self.assertEqual(outcomes["excluded"], 1)
        self.assertEqual(outcomes["prohibited"], 1)
        self.assertGreaterEqual(outcomes["unknown"], 2)
        self.assertEqual(len(report["items"]), 1)
        self.assertEqual(report["items"][0]["memory_id"], normal["candidate_id"])
        protected_surface = json.dumps(
            {"policy_evaluations": report["policy_evaluations"], "exclusions": report["exclusions"]},
            sort_keys=True,
        )
        for candidate in (elevated, excluded, prohibited, missing, conflict):
            self.assertNotIn(candidate["candidate_id"], protected_surface)
            self.assertNotIn(candidate["title"], protected_surface)
            self.assertNotIn(candidate["source"]["path"], protected_surface)
            self.assertNotIn(candidate["source"]["source_hash"], protected_surface)
        self.assertTrue(report["exclusions"]["protected_candidate_metadata_exposed"] is False)
        self.assertTrue(all(item["candidate"] == "<restricted>" for item in report["exclusions"]["items"][:5]))

    def test_missing_policy_is_unknown_and_exposes_no_relevant_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            candidates = relevant_candidates(root)
            report = MemoryRetrievalEngine(root).run(goal=GOAL, generated_at=FIXED_TIME)

        self.assertGreater(report["summary"]["relevant_candidate_count"], 0)
        self.assertEqual(report["summary"]["selected_count"], 0)
        self.assertEqual(report["summary"]["policy_outcomes"]["unknown"], len(report["policy_evaluations"]))
        serialized = json.dumps(report, sort_keys=True)
        for candidate in candidates:
            self.assertNotIn(candidate["candidate_id"], serialized)
            self.assertNotIn(candidate["title"], serialized)

    def test_consumer_role_changes_elevated_retrieval_without_granting_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            candidate = relevant_candidates(root, 1)[0]
            policies = [
                policy(
                    "policy.role-bound",
                    candidate["candidate_id"],
                    required_authority={"retrieval": ["memory_owner"]},
                )
            ]
            metadata = metadata_for([candidate])
            without_role = MemoryRetrievalEngine(root).run(
                goal=GOAL,
                actor_roles=[],
                retention_policies=policies,
                memory_metadata_by_id=metadata,
                evaluation_time=FIXED_TIME,
                generated_at=FIXED_TIME,
            )
            with_role = MemoryRetrievalEngine(root).run(
                goal=GOAL,
                actor_roles=["memory_owner"],
                retention_policies=policies,
                memory_metadata_by_id=metadata,
                evaluation_time=FIXED_TIME,
                generated_at=FIXED_TIME,
            )

        self.assertEqual(without_role["summary"]["policy_outcomes"]["elevated_authority"], 1)
        self.assertEqual(without_role["summary"]["selected_count"], 0)
        self.assertEqual(with_role["summary"]["policy_outcomes"]["normal"], 1)
        self.assertEqual(with_role["summary"]["selected_count"], 1)
        self.assertFalse(with_role["policy_evaluations"][0]["authority_granted"])

    def test_normal_retrieval_cannot_bypass_prohibited_access(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            candidate = relevant_candidates(root, 1)[0]
            policies = [policy("policy.access-prohibited", candidate["candidate_id"])]
            policies[0]["effects"]["access"] = "prohibited"
            report = MemoryRetrievalEngine(root).run(
                goal=GOAL,
                retention_policies=policies,
                memory_metadata_by_id=metadata_for([candidate]),
                evaluation_time=FIXED_TIME,
                generated_at=FIXED_TIME,
            )

        self.assertEqual(report["policy_evaluations"][0]["access_outcome"], "prohibited")
        self.assertEqual(report["policy_evaluations"][0]["retrieval_outcome"], "normal")
        self.assertEqual(report["summary"]["selected_count"], 0)
        self.assertEqual(report["exclusions"]["items"][0]["candidate"], "<restricted>")

    def test_policy_and_metadata_drift_invalidate_saved_retrieval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            candidate = relevant_candidates(root, 1)[0]
            policies = [policy("policy.saved", candidate["candidate_id"])]
            metadata = metadata_for([candidate])
            engine = MemoryRetrievalEngine(root)
            report = engine.run(
                goal=GOAL,
                retention_policies=policies,
                memory_metadata_by_id=metadata,
                evaluation_time=FIXED_TIME,
                generated_at=FIXED_TIME,
            )
            valid = engine.check_retrieval(
                report,
                retention_policies=policies,
                memory_metadata_by_id=metadata,
                generated_at=FIXED_TIME,
            )
            changed_policies = copy.deepcopy(policies)
            changed_policies[0]["version"] = "2"
            policy_drift = engine.check_retrieval(
                report,
                retention_policies=changed_policies,
                memory_metadata_by_id=metadata,
                generated_at=FIXED_TIME,
            )
            changed_metadata = copy.deepcopy(metadata)
            changed_metadata["defaults"]["sensitivity"] = "restricted"
            metadata_drift = engine.check_retrieval(
                report,
                retention_policies=policies,
                memory_metadata_by_id=changed_metadata,
                generated_at=FIXED_TIME,
            )
            temporal_drift = engine.check_retrieval(
                report,
                retention_policies=policies,
                memory_metadata_by_id=metadata,
                evaluation_time="2026-08-22T12:00:00Z",
                generated_at=FIXED_TIME,
            )

        self.assertTrue(valid["result"]["valid"])
        for check in (policy_drift, metadata_drift):
            self.assertFalse(check["result"]["valid"])
            self.assertIn("memory_retrieval_check.policy_context_changed", check["result"]["failed_checks"])
        self.assertFalse(temporal_drift["result"]["valid"])
        self.assertIn("memory_retrieval_check.selection_changed", temporal_drift["result"]["failed_checks"])
        self.assertIn("memory_retrieval_check.temporal_basis_changed", temporal_drift["result"]["failed_checks"])

    def test_policy_aware_retrieval_is_read_only_and_retrieval_does_not_activate_memory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            candidate = relevant_candidates(root, 1)[0]
            policies = [policy("policy.activation-separated", candidate["candidate_id"], activation="excluded")]
            # Override the helper's default activation effect explicitly.
            policies[0]["effects"]["activation"] = "excluded"
            metadata = metadata_for([candidate])
            before = snapshot(root)
            report = MemoryRetrievalEngine(root).run(
                goal=GOAL,
                retention_policies=policies,
                memory_metadata_by_id=metadata,
                evaluation_time=FIXED_TIME,
                generated_at=FIXED_TIME,
            )
            after = snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(report["summary"]["selected_count"], 1)
        self.assertEqual(report["items"][0]["retrieval_eligibility"]["activation_outcome"], "excluded")
        self.assertFalse(report["authority"]["retrieved_memory_added_to_governing_context"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
