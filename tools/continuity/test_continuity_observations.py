"""Cross-process reproduction of QA3's known-observation loss."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from continue_work import ROOT, read_json, render, write_json
from adoption_engine.profile import file_hash, stable_hash
from synthetic_example import accept_synthetic_exception, bind_review, create
from observations import observation_hash


class ObservationContinuityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = create(Path(self.temp.name) / "synthetic")
        self.config = read_json(self.workspace / "work.json")
        self.target = Path(self.config["source"]["root"])

    def process(self, *args):
        write_json(self.workspace / "work.json", self.config)
        process = subprocess.run([sys.executable, str(ROOT / "tools/continuity/continue_work.py"),
            str(self.workspace), "--format", "json", *args], capture_output=True, text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(process.stderr, "")
        return process.returncode, json.loads(process.stdout)

    def observe_later_rule(self):
        code, first = self.process()
        self.assertEqual(code, 0)
        pointer = (self.workspace / "anchor.json").read_bytes()
        text = "SYNTHETIC_NEW_RULE: integration requires separate owner approval."
        source = self.target / "docs/work.md"
        source.write_text(source.read_text() + "\n" + text + "\n")
        for ref in self.config["governing_decisions"][0]["citations"]:
            ref["source_hash"] = file_hash(source)
        self.new_rule = {"id": "separate-integration-approval", "text": text,
                         "checked_by": "synthetic reviewer", "check_scope": "support/pilot",
                         "citations": [{"path": "docs/work.md", "quote": text, "source_hash": file_hash(source)}]}
        self.config["governing_decisions"].append(copy.deepcopy(self.new_rule))
        self.config["source"]["withheld_sources"] = ["docs/unrelated-withheld.md"]
        bind_review(self.config)
        code, observed = self.process("--reanchor", "--reason", "Observe the new visible rule during partial orientation")
        self.assertEqual(code, 2)
        self.assertEqual((self.workspace / "anchor.json").read_bytes(), pointer)
        self.assertIn(text, render(observed))
        self.config["governing_decisions"] = [self.config["governing_decisions"][0]]
        del self.config["source"]["withheld_sources"]
        bind_review(self.config)
        return first, observed

    def test_later_visible_constraint_survives_cross_process_return(self):
        self.observe_later_rule()
        code, returned = self.process("--reanchor", "--reason", "Return without any decision removing the new rule")
        self.assertEqual(code, 2)
        self.assertEqual(returned["status"], "needs_clarification")
        self.assertEqual(returned["proposal_fit"], "unverified_constraints")
        self.assertIn(self.new_rule["text"], render(returned))
        self.assertFalse(returned["proposal_review"]["execution_authorized"])

    def assert_pending(self, code, report):
        self.assertEqual(code, 2)
        self.assertNotEqual(report["status"], "brief_prepared_for_review")
        self.assertIn(report["proposal_fit"], ("unverified_constraints", "reanchor_required"))
        self.assertFalse(report["proposal_review"]["execution_authorized"])
        self.assertIn("restric", render(report).lower())

    def test_repeated_returns_keep_one_observation_and_original_anchor(self):
        self.observe_later_rule()
        anchor = (self.workspace / "anchor.json").read_bytes()
        for _ in range(3):
            code, report = self.process("--reanchor", "--reason", "Review still lacks a disposition")
            self.assert_pending(code, report)
            self.assertEqual(sum(d.get("id") == self.new_rule["id"] for d in report["observations"]), 1)
            self.assertIn(self.new_rule["text"], render(report))
            self.assertEqual((self.workspace / "anchor.json").read_bytes(), anchor)

    def resolve(self, disposition):
        self.config["review"]["observation_refs"] = copy.deepcopy(self.new_rule["citations"])
        accept_synthetic_exception(self.config)
        ref = self.config["review"]["decision_refs"][0]
        decision = json.loads(ref["quote"])
        decision["observation_dispositions"] = [{"observation_hash": observation_hash(self.new_rule),
            "disposition": disposition, "rationale": "Synthetic human owner reviewed the exact observation for this pilot.",
            "superseded_by": "primary-card-feed"}]
        ref["quote"] = json.dumps(decision, sort_keys=True)
        (self.target / ref["path"]).write_text(ref["quote"] + "\n")
        bind_review(self.config)

    def test_documented_not_applicable_resolution_allows_return_and_keeps_history(self):
        self.observe_later_rule()
        self.resolve("not_applicable")
        for _ in range(2):
            code, report = self.process("--reanchor", "--reason", "Exact synthetic human disposition")
            self.assertEqual(code, 0)
            self.assertEqual(report["status"], "brief_prepared_for_review")
            self.assertIn("documented_human_exception", report["proposal_fit"])
            self.assertFalse(report["proposal_review"]["execution_authorized"])
            self.assertNotIn(self.new_rule["id"], [d.get("id") for d in report["governing_decisions"]])
            self.assertIn("not_applicable", render(report))
            self.assertEqual(next(d for d in report["observations"] if d.get("id") == self.new_rule["id"])["disposition"], "not_applicable")

    def test_confirmation_restores_restriction_under_exact_current_review(self):
        self.observe_later_rule()
        self.config["governing_decisions"].append(self.new_rule)
        # A previous review does not bind this recovered material restriction.
        code, report = self.process("--reanchor", "--reason", "Observation restored without review")
        self.assert_pending(code, report)
        bind_review(self.config)
        code, report = self.process("--reanchor", "--reason", "Synthetic reviewer checks the restored rule")
        self.assertEqual(code, 0)
        self.assertIn(self.new_rule["text"], render(report))
        self.assertFalse(report["proposal_review"]["execution_authorized"])

    def test_supersession_requires_existing_replacement_and_exact_authority(self):
        self.observe_later_rule()
        self.resolve("superseded")
        code, report = self.process("--reanchor", "--reason", "Synthetic owner supersedes this observation")
        self.assertEqual(code, 0)
        self.assertIn("superseded", render(report))
        # Removing decision evidence cannot retain its former disposition.
        self.config["review"]["decision_refs"] = []
        bind_review(self.config)
        self.assert_pending(*self.process("--reanchor", "--reason", "Decision is now absent"))

    def test_missing_latest_artifact_recovery_remains_unknown(self):
        self.observe_later_rule()
        last = read_json(self.workspace / "last.json")
        (self.workspace / last["path"]).unlink()
        code, report = self.process("--recover", "--reason", "Latest observation evidence lost")
        self.assert_pending(code, report)
        self.assertTrue(report["observation_history_gap"])
        self.assertIn("observation_history_missing_or_altered", json.dumps(report))
        self.assert_pending(*self.process("--reanchor", "--reason", "Missing evidence still not restored"))

    def test_missing_observed_source_remains_unknown(self):
        self.observe_later_rule()
        (self.target / "docs/work.md").unlink()
        self.assert_pending(*self.process("--reanchor", "--reason", "Source unavailable"))

    def test_later_observation_protected_is_generic_without_hash_identity_or_count(self):
        self.observe_later_rule()
        self.config["source"]["visible_sources"].remove("docs/work.md")
        self.config["claims"] = {}
        self.config["governing_decisions"] = []
        self.config["review"] = {}
        code, report = self.process()
        self.assert_pending(code, report)
        serialized = json.dumps(report) + render(report)
        for private in (self.new_rule["id"], self.new_rule["text"], self.new_rule["citations"][0]["source_hash"], "docs/work.md"):
            self.assertNotIn(private, serialized)
        self.assertEqual(len(report["observations"]), 1)
        self.assertEqual(len(report["governing_decisions"]), 1)

    def test_scope_and_front_cannot_reuse_observations(self):
        self.observe_later_rule()
        original = copy.deepcopy(self.config)
        for scope in (True, False):
            self.config = copy.deepcopy(original)
            if scope:
                self.config["proposal"]["scope"] = "other/pilot"
            else:
                self.config["intent"] = "Unrelated work front"
            code, report = self.process("--reanchor", "--reason", "Unrelated scope")
            self.assertEqual(code, 2)
            self.assertNotIn(self.new_rule["text"], json.dumps(report))

    def test_same_id_substitution_retains_prior_revision_until_disposition(self):
        self.observe_later_rule()
        replacement = copy.deepcopy(self.config["governing_decisions"][0])
        replacement.update(id=self.new_rule["id"], text="A softer replacement cannot erase the observed rule.")
        self.config["governing_decisions"].append(replacement)
        bind_review(self.config)
        for _ in range(2):
            code, report = self.process("--reanchor", "--reason", "Same id is not a disposition")
            self.assert_pending(code, report)
            self.assertIn(self.new_rule["text"], render(report))
            self.assertEqual(len([d for d in report["observations"] if d.get("id") == self.new_rule["id"]]), 2)
        self.resolve("superseded")
        code, report = self.process("--reanchor", "--reason", "Synthetic exact disposition of original revision")
        self.assertEqual(code, 0)
        self.assertIn("superseded", render(report))

    def test_legacy_scope_mismatch_fails_without_mixing(self):
        self.process()
        pointer = read_json(self.workspace / "anchor.json")
        path = self.workspace / pointer["path"]
        legacy = read_json(path)
        for key in ("work_binding", "observations", "observation_history_gap", "protected_observations_covered_by_anchor", "anchor_eligible", "usable_anchor_expected"):
            legacy.pop(key, None)
        write_json(path, legacy)
        pointer["hash"] = stable_hash(legacy)
        for name in ("last.json", "anchor.json"):
            write_json(self.workspace / name, pointer)
        self.config["proposal"]["scope"] = "unrelated/new-scope"
        bind_review(self.config)
        code, report = self.process("--reanchor", "--reason", "Legacy scope cannot be inferred")
        self.assertEqual(code, 2)
        self.assertIn("Legacy observation scope", json.dumps(report))
        self.assertNotIn("primary-card-feed", json.dumps(report))

    def test_deliberately_unanchored_visible_partial_can_return_without_recovery(self):
        self.config["governing_decisions"][0]["citations"][0]["quote"] = "Synthetic absent quotation"
        for _ in range(2):
            code, report = self.process()
            self.assert_pending(code, report)
            self.assertFalse((self.workspace / "anchor.json").exists())
            self.assertIn("quote_not_found", json.dumps(report))
        self.assertIn("no accepted anchor", report["history"])

    def test_lost_usable_anchor_requires_explicit_unknown_recovery(self):
        self.process()
        (self.workspace / "anchor.json").unlink()
        code, report = self.process()
        self.assertEqual(code, 2)
        self.assertIn("evidence missing or altered", json.dumps(report))
        self.assert_pending(*self.process("--recover", "--reason", "Restore missing anchor with unknown history"))

    def test_expired_disposition_cannot_resolve_the_observation(self):
        self.observe_later_rule()
        self.resolve("not_applicable")
        ref = self.config["review"]["decision_refs"][0]
        decision = json.loads(ref["quote"])
        decision["valid_until"] = "2000-01-01T00:00:00Z"
        ref["quote"] = json.dumps(decision, sort_keys=True)
        (self.target / ref["path"]).write_text(ref["quote"] + "\n")
        bind_review(self.config)
        self.assert_pending(*self.process("--reanchor", "--reason", "Expired disposition is not current authority"))

    def evolve_source(self):
        source = self.target / "docs/work.md"
        source.write_text(source.read_text().replace(self.new_rule["text"], "The revised pilot preserves in-card continuity."))
        for item in self.config["governing_decisions"]:
            for ref in item["citations"]:
                ref["source_hash"] = file_hash(source)

    def test_terminal_disposition_of_history_survives_current_source_evolution(self):
        self.observe_later_rule()
        self.evolve_source()
        for disposition in ("not_applicable", "superseded", "rejected"):
            self.resolve(disposition)
            for _ in range(2):
                code, report = self.process("--reanchor", "--reason", "Synthetic owner settles the exact historical observation")
                self.assertEqual(code, 0)
                self.assertEqual(report["status"], "brief_prepared_for_review")
                self.assertFalse(report["proposal_review"]["execution_authorized"])
                settled = next(d for d in report["observations"] if d.get("id") == self.new_rule["id"])
                self.assertEqual(settled["disposition"], disposition)
                self.assertEqual(settled["status"], "unverifiable")  # old citation is not current truth
                self.assertIn(disposition, render(report))

    def test_history_disposition_still_requires_current_authority_and_visible_refs(self):
        self.observe_later_rule()
        self.evolve_source()
        self.resolve("not_applicable")
        self.assertEqual(self.process("--reanchor", "--reason", "Exact historical settlement")[0], 0)
        self.config["review"]["authority_refs"] = []
        bind_review(self.config)
        self.assert_pending(*self.process("--reanchor", "--reason", "Authority no longer evidenced"))
        self.config["source"]["visible_sources"].remove("docs/work.md")
        code, report = self.process()
        self.assert_pending(code, report)
        self.assertNotIn(self.new_rule["id"], json.dumps(report) + render(report))
        self.assertNotIn(self.new_rule["citations"][0]["source_hash"], json.dumps(report) + render(report))


if __name__ == "__main__":
    unittest.main()
