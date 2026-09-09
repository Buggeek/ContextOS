"""A controlled internal second crossing must not change historical evidence."""
import sys
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

for name in ("reasoning", "memory", "activation"):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / name))
from reasoning_engine import ContextualAssessmentEngine
from memory_engine import MemoryRetrievalEngine
from test_memory_retrieval import make_repo
from test_memory_retrieval_policy import GOAL, relevant_candidates, metadata_for, policy
from reasoning_engine.assessment_engine import stable_hash

T = "2026-09-08T12:00:00Z"
T1 = "2026-09-08T12:00:01Z"


class AssessmentTimeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        make_repo(self.root)
        self.engine = ContextualAssessmentEngine(self.root)
        candidate = relevant_candidates(self.root, 1)[0]
        self.policies = [policy("policy.temporal", candidate["candidate_id"], effective_until=T1)]
        self.metadata = metadata_for([candidate])

    def assessment(self):
        return self.engine.run(goal=GOAL, retention_policies=self.policies,
            memory_metadata_by_id=self.metadata, generated_at=T)

    def check(self, saved, now, policies=None):
        with patch("reasoning_engine.report_builder.generated_timestamp", return_value=now):
            return self.engine.check_assessment(saved, retention_policies=self.policies if policies is None else policies,
                memory_metadata_by_id=self.metadata)

    def test_default_internal_second_crossing_is_reproducible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            original = MemoryRetrievalEngine.run
            clock = {"now": T}
            def memory(engine, *args, **kwargs):
                result = original(engine, *args, **kwargs)
                clock["now"] = T1
                return result
            with patch("memory_engine.retrieval_engine.generated_timestamp", side_effect=lambda: clock["now"]), \
                 patch("reasoning_engine.report_builder.generated_timestamp", side_effect=lambda: clock["now"]), \
                 patch.object(MemoryRetrievalEngine, "run", memory):
                engine = ContextualAssessmentEngine(root)
                saved = engine.run(goal="Resume governed work without timestamp input")
                checked = engine.check_assessment(saved)
            self.assertEqual(saved["evidence"]["memory_retrieval"]["query"]["evaluation_time"], T)
            self.assertTrue(checked["result"]["valid"], checked["result"])

    def test_expiry_preserves_history_but_invalidates_actual_default_check(self):
        saved = self.assessment()
        self.assertGreater(len(saved["evidence"]["memory_retrieval"]["items"]), 0)
        original = copy.deepcopy(saved)
        self.assertTrue(self.check(saved, T)["result"]["valid"])
        later = self.check(saved, T1)
        self.assertEqual(later["checks"]["immutable_identity"], "valid")
        self.assertEqual(later["checks"]["historical_reproducibility"], "exact_match")
        self.assertEqual(later["checks"]["current_eligibility"], "changed_or_unverifiable")
        self.assertEqual(later["checks"]["eligibility_checked_at"], T1)
        self.assertFalse(later["result"]["valid"])
        self.assertEqual(saved, original)

    def test_later_time_with_live_policy_is_valid_without_clock_hash_equality(self):
        self.policies[0]["effective_until"] = "2026-09-09T12:00:00Z"
        saved = self.assessment()
        checked = self.check(saved, T1)
        self.assertTrue(checked["result"]["valid"], checked["result"])

    def test_revocation_policy_and_metadata_drift_remain_invalid(self):
        saved = self.assessment()
        revoked = copy.deepcopy(self.policies)
        revoked[0]["effects"]["access"] = "prohibited"
        for policies in (revoked, [{**self.policies[0], "version": "2"}]):
            with self.subTest(policies=policies):
                checked = self.check(saved, T, policies)
                self.assertFalse(checked["result"]["valid"])
                self.assertEqual(checked["checks"]["historical_reproducibility"], "drifted_or_unverifiable")
        self.metadata["defaults"]["sensitivity"] = "restricted"
        self.assertFalse(self.check(saved, T)["result"]["valid"])

    def test_source_drift_still_invalidates_historical_reproduction(self):
        saved = self.assessment()
        for path in self.root.rglob("*.md"):
            path.write_text(path.read_text() + "\nMaterial governed source change.\n")
        self.assertFalse(self.check(saved, T)["result"]["valid"])

    def test_legacy_null_time_uses_bound_memory_time_and_rejects_tampering(self):
        saved = self.assessment()
        saved["query"]["evaluation_time"] = None
        saved["generated_at"] = T1
        saved["identity_hash"] = stable_hash(self.engine._identity_payload(saved["query"], saved["bindings"],
            saved["reasoning"], saved.get("consequential_recommendation_gate")))
        saved["id"] = "reasoning.assessment." + saved["identity_hash"][:16]
        self.assertTrue(self.check(saved, T)["result"]["valid"])
        self.assertFalse(self.check(saved, T1)["result"]["valid"])
        saved["evidence"]["memory_retrieval"]["query"]["evaluation_time"] = T1
        self.assertFalse(self.check(saved, T)["result"]["valid"])


if __name__ == "__main__":
    unittest.main()
