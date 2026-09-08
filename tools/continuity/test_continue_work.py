#!/usr/bin/env python3
"""Predetermined synthetic acceptance scenarios; never a simulated human trial."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from continue_work import ROOT, read_json, run, write_json
from synthetic_example import accept_synthetic_exception, bind_review, create


class ContinuityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name) / "example"
        self.workspace = create(self.base)
        self.config = read_json(self.workspace / "work.json")
        self.target = Path(self.config["source"]["root"])
        self.oracle = read_json(self.base / "oracle.json")

    def save(self):
        write_json(self.workspace / "work.json", self.config)

    def process(self, *args):
        result = subprocess.run([sys.executable, str(ROOT / "tools/continuity/continue_work.py"), str(self.workspace),
                                 "--format", "json", *args], capture_output=True, text=True)
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def test_sufficient_first_orientation_and_existing_mission(self):
        report = run(self.workspace)
        self.assertEqual(report["status"], "brief_prepared_for_review")
        self.assertEqual(report["history"], "no prior reference")
        self.assertEqual(report["ownership_disposition"], "OBSERVE_EXISTING_WORK")
        self.assertEqual(report["ownership"]["ownership"]["resolved_owner"]["work_id"], self.oracle["expected_owner"])
        self.assertIsNone(report["human_measurements"])

    def test_incomplete_context_requests_only_missing_evidence(self):
        del self.config["claims"]["objective"]
        self.save()
        report = run(self.workspace)
        self.assertEqual(report["status"], "needs_clarification")
        self.assertNotIn("objective", report["claims"])
        self.assertTrue(any(g.startswith("objective:") for g in report["gaps"]))

    def test_unknown_ownership_does_not_mean_no_work(self):
        del self.config["ownership"]
        self.save()
        report = run(self.workspace)
        self.assertEqual(report["ownership_disposition"], "OWNERSHIP_UNKNOWN")
        self.assertIn("existing_work", report["claims"])

    def test_conflicting_owners(self):
        item = copy.deepcopy(self.config["ownership"]["work_items"][0])
        item["id"] = "M-8"
        self.config["ownership"]["work_items"].append(item)
        self.save()
        self.assertEqual(run(self.workspace)["ownership_disposition"], "OWNERSHIP_CONFLICT")

    def test_native_authorized_corpus_still_supported(self):
        sys.path.insert(0, str(ROOT / "tools/activation"))
        from test_activation_package import ContextActivationPackageTestCase
        native = ContextActivationPackageTestCase().make_repo()
        self.addCleanup(native.cleanup)
        native_root = Path(native.name).resolve()
        for locator in self.config["source"]["visible_sources"]:
            (native_root / locator).write_bytes((self.target / locator).read_bytes())
        self.config["source"]["root"] = str(native_root)
        self.config["source"]["visible_sources"] = sorted(str(p.relative_to(native_root)) for p in native_root.rglob("*") if p.is_file())
        del self.config["profile"]
        bind_review(self.config)
        self.save()
        self.assertEqual(run(self.workspace)["status"], "brief_prepared_for_review")

    def test_external_profile_without_ownership_mapping_stays_unknown(self):
        profile = read_json(self.base / "profile.json")
        del profile["work_ownership"]
        write_json(self.base / "profile.json", profile)
        self.assertEqual(run(self.workspace)["ownership_disposition"], "OWNERSHIP_UNKNOWN")

    def test_other_process_same_sources(self):
        code, first = self.process()
        self.assertEqual(code, 0)
        code, second = self.process()
        self.assertEqual(code, 0)
        self.assertEqual(first["version"]["id"], second["prior_reference"])
        self.assertEqual(second["version"]["lineage"]["parent_version"]["id"], first["version"]["id"])
        self.assertFalse(second["changed_sources"])
        self.assertTrue(second["prior_checks"]["package"]["result"]["valid"])

    def test_irrelevant_git_tip(self):
        def git(*args):
            subprocess.run(["git", *args], cwd=self.target, check=True, capture_output=True)
        git("init", "-q")
        git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "--allow-empty", "-qm", "initial")
        first = run(self.workspace)
        git("-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "--allow-empty", "-qm", "unrelated")
        second = run(self.workspace)
        self.assertNotEqual(first["provenance"]["local_tip"], second["provenance"]["local_tip"])
        self.assertEqual(second["status"], "brief_prepared_for_review")

    def test_material_change_requires_explicit_review_then_reanchor(self):
        run(self.workspace)
        path = self.target / "docs/work.md"
        path.write_text(path.read_text() + "\nMaterial constraint: steward approval expires tomorrow.\n")
        report = run(self.workspace)
        self.assertEqual(report["status"], "reanchor_required")
        self.assertEqual(report["claims"], {})
        code, report = self.process("--reanchor", "--reason", "Synthetic operator reviewed added constraint")
        self.assertEqual(code, 2)  # a re-anchor is not a fresh review of changed constraints
        self.assertEqual(report["proposal_fit"], "unverified_constraints")
        self.assertEqual(report["changed_sources"], ["docs/work.md"])

    def test_withheld_evidence_never_read_or_exposed(self):
        self.config["source"]["withheld_sources"] = ["docs/private.md"]
        (self.target / "docs/private.md").write_text("SECRET_SYNTHETIC_CANARY")
        self.config["claims"]["indicator"] = {"text": "SECRET_SYNTHETIC_CANARY", "citations": [{"path": "docs/private.md", "quote": "SECRET_SYNTHETIC_CANARY"}]}
        self.save()
        report = run(self.workspace)
        self.assertNotIn("SECRET_SYNTHETIC_CANARY", json.dumps(report))
        self.assertNotIn("indicator", report["claims"])
        self.assertIn("not_retrieved", report["provenance"]["memory"])

    def test_invalid_profile(self):
        write_json(self.base / "profile.json", {"schema": "invalid"})
        self.assertEqual(self.process()[0], 2)

    def test_wrong_target_profile(self):
        self.config["target_id"] = "another-organization"
        self.save()
        self.assertEqual(self.process()[0], 2)

    def test_cannot_reanchor_saved_history_to_another_target(self):
        run(self.workspace)
        self.config["target_id"] = "another-organization"
        self.save()
        profile = read_json(self.base / "profile.json")
        profile["target"]["id"] = "another-organization"
        write_json(self.base / "profile.json", profile)
        self.assertEqual(self.process("--reanchor", "--reason", "Attempted target change")[0], 2)

    def test_missing_local_record_explicit_recovery(self):
        run(self.workspace)
        (self.workspace / read_json(self.workspace / "anchor.json")["path"]).unlink()
        self.assertEqual(self.process()[0], 2)
        code, report = self.process("--recover", "--reason", "Lost local evidence; start new reference")
        self.assertEqual(code, 0)
        self.assertIn("prior history unknown", report["history"])
        self.assertIsNone(report["prior_reference"])

    def test_intact_anchor_cannot_claim_lost_history_recovery(self):
        run(self.workspace)
        self.assertEqual(self.process("--recover", "--reason", "No actual evidence loss")[0], 2)

    def test_missing_or_tampered_historical_source_requires_recovery(self):
        run(self.workspace)
        record_path = self.workspace / read_json(self.workspace / "anchor.json")["path"]
        (record_path.parent / "corpus/docs/work.md").unlink()
        self.assertEqual(self.process()[0], 2)

    def test_read_source_does_not_mean_restriction_checked(self):
        del self.config["governing_decisions"][0]["checked_by"]
        self.save()
        from continue_work import render
        self.assertIn("leída; restricción no comprobada", render(run(self.workspace)))

    def test_profile_change_requires_reanchor(self):
        run(self.workspace)
        profile = read_json(self.base / "profile.json")
        profile["version"] = "1.1"
        write_json(self.base / "profile.json", profile)
        self.assertEqual(run(self.workspace)["status"], "reanchor_required")

    def test_no_target_mutation(self):
        before = {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        run(self.workspace)
        self.process()
        after = {str(p.relative_to(self.target)): p.read_bytes() for p in self.target.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_semantic_fit_is_operator_declared_and_different(self):
        self.assertEqual(run(self.workspace)["proposal_fit"], self.oracle["proposal_A"])
        self.config["proposal"].update(content="B: dominant summary demotes feed", version="B.1")
        self.config["review"].update(fit="conflict", rationale="Synthetic reviewer identifies the inversion of primary surface.")
        bind_review(self.config)
        self.save()
        self.assertEqual(run(self.workspace, reanchor=True, reason="Synthetic reviewed proposal B")["proposal_fit"], self.oracle["proposal_B"])

    def test_unreviewed_proposal_and_self_documentation_do_not_grant_approval(self):
        self.config["review"].update(fit="approved_exception", human_approver="claimed approver",
                                     decision_refs=[{"path": "docs/work.md", "quote": "Preserve its primacy."}])
        self.save()
        self.assertEqual(run(self.workspace)["proposal_fit"], "unverified_constraints")

    def test_explicit_architectural_exception_permits_governed_evolution(self):
        accept_synthetic_exception(self.config)
        self.save()
        self.assertEqual(run(self.workspace)["proposal_fit"], self.oracle["proposal_B_accepted_exception"])

    def test_source_symlink_is_blocked(self):
        (self.target / "docs/work.md").unlink()
        (self.target / "docs/work.md").symlink_to(self.base / "profile.json")
        self.assertEqual(self.process()[0], 2)

    def test_input_symlink_blocked_before_read(self):
        (self.workspace / "work.json").unlink()
        (self.workspace / "work.json").symlink_to(self.base / "profile.json")
        with patch("continue_work.read_json", side_effect=AssertionError("must not read redirected input")):
            with self.assertRaises(ValueError):
                run(self.workspace)

    def test_published_reader_stops_at_wrong_bound_identity(self):
        self.config["source"].update(kind="published_git_docs", repository="Example/support", identity="Example")
        self.save()
        with patch("continue_work.command", return_value=b"AUTHORITY_OK repository=Example/support identity=Different\n") as mocked:
            with self.assertRaises(ValueError):
                run(self.workspace)
            self.assertEqual(mocked.call_count, 1)

    def test_state_inside_target_blocked(self):
        inside = self.target / "state"
        inside.mkdir()
        write_json(inside / "work.json", self.config)
        with self.assertRaises(ValueError):
            run(inside)


if __name__ == "__main__":
    unittest.main()
