"""Correction counterexamples. All corpora/decisions are explicitly synthetic."""
import copy
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from continue_work import read_json, render, run, write_json
from adoption_engine.profile import file_hash
from synthetic_example import accept_synthetic_exception, bind_review, create


class ReviewEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = create(Path(self.temp.name) / "fixture")
        self.config = read_json(self.workspace / "work.json")
        self.target = Path(self.config["source"]["root"])

    def report(self, **kwargs):
        write_json(self.workspace / "work.json", self.config)
        return run(self.workspace, **kwargs)

    def assert_limited(self, report):
        self.assertEqual(report["status"], "needs_clarification")
        self.assertEqual(report["proposal_fit"], "unverified_constraints")
        self.assertFalse(report["proposal_review"]["execution_authorized"])
        self.assertTrue(report["gaps"])
        self.assertIn("Encaje no comprobado", render(report))

    def test_invalid_quote_retained_in_brief_and_machine(self):
        self.config["governing_decisions"][0]["citations"][0]["quote"] = "This quote does not exist"
        report = self.report()
        self.assert_limited(report)
        item = report["governing_decisions"][0]
        self.assertEqual(item["status"], "unverifiable")
        self.assertEqual(item["missing_evidence"], "quote_not_found")
        self.assertEqual(item["citations"][0]["path"], "docs/work.md")
        self.assertIn("NO VERIFICABLE", render(report))
        self.assertIn("Preserve the card feed", render(report))
        self.assertIn("objective", report["claims"])  # safe partial orientation survives

    def test_missing_source_keeps_known_restriction(self):
        (self.target / "docs/work.md").unlink()
        report = self.report()
        self.assert_limited(report)
        self.assertEqual(report["governing_decisions"][0]["missing_evidence"], "source_missing")
        self.assertIn("docs/work.md", report["provenance"]["missing_sources"])
        self.assertNotIn("objective", report["claims"])

    def test_changed_source_with_original_quote_is_not_original_evidence(self):
        path = self.target / "docs/work.md"
        path.write_text(path.read_text() + "\nA new condition applies.\n")
        report = self.report()
        self.assert_limited(report)
        self.assertEqual(report["governing_decisions"][0]["missing_evidence"], "source_changed")

    def test_deleting_known_constraint_cannot_make_unrestricted_brief(self):
        self.report()
        self.config["governing_decisions"] = []
        bind_review(self.config)
        report = self.report(reanchor=True, reason="Deletion is not acceptance")
        self.assert_limited(report)
        self.assertTrue(report["governing_decisions"])
        self.assertIn("NO VERIFICABLE", render(report))

    def test_changed_proposal_keeps_label_but_loses_verdict(self):
        first = self.report()
        self.config["proposal"]["content"] = "B: replace the feed with a dominant summary"
        report = self.report(reanchor=True, reason="Re-anchor must not refresh semantic review")
        self.assert_limited(report)
        self.assertFalse(report["proposal_review"]["binding"]["valid"])
        self.assertEqual(report["proposal_review"]["judgement"]["fit"], "compatible")
        self.assertNotEqual(report["proposal_review"]["binding"]["current"], first["proposal_review"]["binding"]["current"])

    def test_changed_version_scope_or_rationale_invalidates_review(self):
        for section, key in (("proposal", "version"), ("proposal", "scope"), ("review", "rationale")):
            with self.subTest(key=key):
                original = copy.deepcopy(self.config)
                self.config[section][key] += " changed"
                if key == "scope" and (self.workspace / "anchor.json").exists():
                    with self.assertRaisesRegex(ValueError, "different target, profile, front or scope"):
                        self.report(reanchor=True, reason="Synthetic change")
                else:
                    self.assert_limited(self.report(reanchor=True, reason="Synthetic change"))
                self.config = original

    def test_same_author_cannot_claim_independent_review(self):
        self.config["review"].update(reviewed_by=self.config["proposal"]["author"], independent_of_candidate=True)
        bind_review(self.config)
        report = self.report()
        self.assert_limited(report)
        self.assertEqual(report["proposal_review"]["review_relationship"], "self_review")
        self.assertIn("no es una revisión independiente", render(report))

    def test_honest_self_review_is_attributed_not_independent(self):
        self.config["review"].update(reviewed_by=self.config["proposal"]["author"])
        bind_review(self.config)
        report = self.report()
        self.assertEqual(report["status"], "brief_prepared_for_review")
        self.assertEqual(report["proposal_review"]["review_relationship"], "self_review")

    def change_decision(self, **changes):
        ref = self.config["review"]["decision_refs"][0]
        decision = json.loads(ref["quote"])
        decision.update(changes)
        ref["quote"] = json.dumps(decision, sort_keys=True)
        (self.target / ref["path"]).write_text("# Synthetic decision\n" + ref["quote"])
        bind_review(self.config)

    def test_agent_author_cannot_self_approve_as_human(self):
        self.config["proposal"]["actor_kind"] = "human"  # candidate role is ignored
        accept_synthetic_exception(self.config)
        self.config["review"].update(human_approver=self.config["proposal"]["author"], authority_verified_by="author", independent_of_candidate=True)
        self.change_decision(human_owner=self.config["proposal"]["author"])
        self.assert_limited(self.report())

    def test_unrecognized_authority_source_cannot_bootstrap_approval(self):
        profile = read_json(self.config["profile"])
        for mapping in profile["mappings"]:
            if mapping["concept"] in {"governance", "authority_boundaries"}:
                mapping["sources"][0]["locator"] = "docs/work.md"
        write_json(self.config["profile"], profile)
        accept_synthetic_exception(self.config)
        report = self.report()
        self.assert_limited(report)
        self.assertIn("authority_source_not_recognized_by_approved_profile", report["proposal_review"]["issues"])

    def test_rule_being_excepted_is_not_an_exception_decision(self):
        accept_synthetic_exception(self.config)
        self.config["review"]["decision_refs"] = [{"path": "docs/work.md", "quote": "Preserve its primacy."}]
        bind_review(self.config)
        self.assert_limited(self.report())

    def test_exception_missing_or_invalid_decision(self):
        for refs in ([], [{"path": "docs/decision.md", "quote": "Invented acceptance"}]):
            accept_synthetic_exception(self.config)
            self.config["review"]["decision_refs"] = refs
            bind_review(self.config)
            self.assert_limited(self.report(reanchor=True, reason="Synthetic negative"))

    def test_exception_outside_scope_rejected_even_after_rebinding(self):
        accept_synthetic_exception(self.config)
        self.change_decision(scope="another organization/all surfaces")
        self.assert_limited(self.report())

    def test_explicit_human_founder_may_author_and_approve_bounded_trial(self):
        accept_synthetic_exception(self.config, founder_authors=True)
        report = self.report()
        self.assertEqual(report["proposal_fit"], "documented_human_exception; authenticity_not_verified")
        evidence = report["proposal_review"]
        self.assertEqual(evidence["decision"]["human_owner"], evidence["proposal"]["author"])
        self.assertEqual(evidence["decision"]["scope"], "support/pilot")
        self.assertTrue(evidence["binding"]["valid"])
        self.assertFalse(evidence["execution_authorized"])
        self.assertIn("autenticidad no verificada", render(report))

    def test_changed_governing_context_invalidates_exception(self):
        accept_synthetic_exception(self.config)
        self.report()
        self.config["governing_decisions"][0]["text"] += " Requires language parity."
        bind_review(self.config)  # new review cannot update the OLD decision's context
        self.assert_limited(self.report(reanchor=True, reason="Changed governing context"))

    def test_changed_decision_source_invalidates_review_even_if_quote_remains(self):
        accept_synthetic_exception(self.config)
        path = self.target / "docs/decision.md"
        path.write_text(path.read_text() + "\nDecision revoked pending further review.\n")
        report = self.report()
        self.assert_limited(report)
        self.assertFalse(report["proposal_review"]["binding"]["valid"])

    def test_expiration_rechecked_with_current_clock_without_source_change(self):
        accept_synthetic_exception(self.config)
        first = self.report()
        future = datetime.now(timezone.utc) + timedelta(days=3)
        class Later(datetime):
            @classmethod
            def now(cls, tz=None):
                return future
        with patch("review_evidence.datetime", Later):
            report = self.report()
        self.assert_limited(report)
        self.assertEqual(first["proposal_review"]["binding"], report["proposal_review"]["binding"])
        self.assertFalse(report["changed_sources"])

    def test_withheld_restriction_and_review_never_leak_content_or_metadata(self):
        secret_path, secret = "docs/PRIVATE_CANARY_PATH.md", "PRIVATE_CANARY_CONTENT"
        self.config["source"]["withheld_sources"] = [secret_path]
        item = self.config["governing_decisions"][0]
        item.update(text=secret, checked_by="PRIVATE_CANARY_ACTOR", citations=[{"path": secret_path, "quote": secret}])
        self.config["review"]["constraint_refs"] = item["citations"]
        self.config["proposal"]["content"] = secret
        report = self.report()
        self.assert_limited(report)
        combined = json.dumps(report) + render(report)
        self.assertNotIn("PRIVATE_CANARY", combined)
        self.assertTrue(report["governing_decisions"])

    def test_revoked_visibility_does_not_read_or_expose_old_source(self):
        self.report()
        self.config["source"]["visible_sources"].remove("docs/work.md")
        self.config["source"]["withheld_sources"] = ["docs/work.md"]
        report = self.report(reanchor=True, reason="Visibility withdrawn")
        self.assert_limited(report)
        combined = json.dumps(report) + render(report)
        self.assertNotIn("docs/work.md", combined)
        self.assertNotIn("Preserve the card feed", combined)
        self.assertNotIn("Add continuity within", combined)

    def test_unchanged_return_preserves_valid_review_and_context_reference(self):
        first, second = self.report(), self.report()
        self.assertEqual(first["proposal_review"]["binding"], second["proposal_review"]["binding"])
        self.assertEqual(first["version"]["id"], second["prior_reference"])
        self.assertTrue(second["proposal_review"]["binding"]["valid"])
        self.assertEqual(second["status"], "brief_prepared_for_review")

    def test_mixed_invalid_visible_and_protected_references_never_leak(self):
        for problem in ("quote", "source_missing", "source_changed"):
            with self.subTest(problem=problem):
                config = copy.deepcopy(self.config)
                item = self.config["governing_decisions"][0]
                ref = item["citations"][0]
                if problem == "quote":
                    ref["quote"] = "invalid quote"
                elif problem == "source_missing":
                    ref["path"] = "docs/missing.md"
                    self.config["source"]["visible_sources"].append(ref["path"])
                else:
                    ref["source_hash"] = "invalid source fingerprint"
                item.update(text="PRIVATE_CANARY_TEXT", id="PRIVATE_CANARY_ID", checked_by="PRIVATE_CANARY_ACTOR")
                item["citations"].append({"path": "docs/PRIVATE_CANARY_PATH.md", "quote": "PRIVATE_CANARY_QUOTE"})
                report = self.report(reanchor=True, reason="Synthetic mixed visibility negative")
                self.assert_limited(report)
                self.assertNotIn("PRIVATE_CANARY", json.dumps(report) + render(report))
                self.assertEqual(report["governing_decisions"][0]["missing_evidence"], "evidence_not_visible")
                self.config = config

    def test_legitimate_restriction_update_can_be_reviewed_and_accepted(self):
        self.report()
        path = self.target / "docs/work.md"
        addition = "The pilot additionally requires language parity."
        path.write_text(path.read_text() + "\n" + addition)
        item = self.config["governing_decisions"][0]
        item["text"] += " " + addition
        item["citations"].append({"path": "docs/work.md", "quote": addition})
        for ref in item["citations"]:
            ref["source_hash"] = file_hash(path)
        self.assert_limited(self.report(reanchor=True, reason="Same identity alone is not a review"))
        bind_review(self.config)
        report = self.report(reanchor=True, reason="Synthetic reviewer compares the updated requirement")
        self.assertEqual(report["status"], "brief_prepared_for_review")
        self.assertEqual(len(report["governing_decisions"]), 1)
        accept_synthetic_exception(self.config)
        report = self.report(reanchor=True, reason="Synthetic exact new decision")
        self.assertEqual(report["status"], "brief_prepared_for_review")
        self.assertIn("documented_human_exception", report["proposal_fit"])
        self.assertEqual(self.report()["status"], "brief_prepared_for_review")

    def test_legacy_restriction_can_gain_identity_without_omission(self):
        del self.config["governing_decisions"][0]["id"]
        bind_review(self.config)
        self.report()
        self.config["governing_decisions"][0]["id"] = "primary-card-feed"
        self.assert_limited(self.report(reanchor=True, reason="Identity migration is not semantic review"))
        bind_review(self.config)
        self.assertEqual(self.report(reanchor=True, reason="Reviewed unchanged legacy restriction")["status"], "brief_prepared_for_review")

    def test_restoring_omitted_visible_restriction_resolves_gap(self):
        self.report()
        original = copy.deepcopy(self.config["governing_decisions"])
        self.config["governing_decisions"] = []
        bind_review(self.config)
        report = self.report(reanchor=True, reason="Known restriction missing")
        self.assert_limited(report)
        self.assertEqual(report["governing_decisions"][0]["id"], original[0]["id"])
        self.config["governing_decisions"] = original
        bind_review(self.config)
        self.assertEqual(self.report(reanchor=True, reason="Restored and reviewed known constraint")["status"], "brief_prepared_for_review")

    def test_duplicate_restriction_ids_require_clarification(self):
        self.config["governing_decisions"].append(copy.deepcopy(self.config["governing_decisions"][0]))
        bind_review(self.config)
        self.assert_limited(self.report())

    def test_visibility_restoration_reuses_preserved_usable_anchor(self):
        first = self.report()
        pointer = (self.workspace / "anchor.json").read_bytes()
        original = copy.deepcopy(self.config)
        self.config["source"]["visible_sources"].remove("docs/work.md")
        self.config["source"]["withheld_sources"] = ["docs/work.md"]
        counts = []
        for kwargs in ({"reanchor": True, "reason": "Access withdrawn"}, {}, {}):
            partial = self.report(**kwargs)
            self.assert_limited(partial)
            self.assertEqual((self.workspace / "anchor.json").read_bytes(), pointer)
            self.assertNotIn("docs/work.md", json.dumps(partial) + render(partial))
            counts.append(len(partial["governing_decisions"]))
        self.assertEqual(len(set(counts)), 1)
        self.config = original
        bind_review(self.config)
        restored = self.report(reanchor=True, reason="Visibility restored; exact evidence reviewed")
        self.assertEqual(restored["status"], "brief_prepared_for_review")
        self.assertEqual(restored["prior_reference"], first["version"]["id"])
        self.assertEqual(len(restored["governing_decisions"]), 1)

    def test_folder_born_partial_never_invents_verified_history(self):
        self.config["source"]["visible_sources"].remove("docs/work.md")
        self.config["source"]["withheld_sources"] = ["docs/work.md"]
        first = self.report()
        self.assert_limited(first)
        self.assertFalse((self.workspace / "anchor.json").exists())
        again = self.report()
        self.assert_limited(again)
        self.assertIn("prior protected context unknown", again["history"])
        self.assertEqual(len(first["governing_decisions"]), len(again["governing_decisions"]))
        recovered = self.report(recover=True, reason="Partial evidence cannot recover protected history")
        self.assert_limited(recovered)
        self.assertIn("prior history unknown", recovered["history"])
        self.assertIsNone(recovered["prior_reference"])

    def test_recover_cannot_erase_known_restrictions_of_partial_reference(self):
        self.config["source"]["withheld_sources"] = ["docs/private.md"]
        self.report()
        self.config["governing_decisions"] = []
        bind_review(self.config)
        report = self.report(recover=True, reason="A recovery flag is not approval to erase a known restriction")
        self.assert_limited(report)
        self.assertTrue(report["governing_decisions"])


if __name__ == "__main__":
    unittest.main()
