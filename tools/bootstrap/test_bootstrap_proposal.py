#!/usr/bin/env python3
"""Tests for Context OS Bootstrap Proposals."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from bootstrap_engine.plan_engine import BootstrapPlanEngine
from bootstrap_engine.proposal_engine import BootstrapProposalEngine, SCHEMA, stable_hash


def write(path: Path, text: str = "# Test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_snapshot(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): path.read_text(encoding="utf-8") for path in root.rglob("*") if path.is_file()}


class BootstrapProposalTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md")
        write(root / "SSOT" / "S.1_Vision.md")
        return temp

    def test_proposal_shape_and_read_only_constraints(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            plan = BootstrapPlanEngine(root).run(generated_at="2026-08-11T00:00:00Z")
            before = file_snapshot(root)
            proposal = BootstrapProposalEngine(root).run(plan, generated_at="2026-08-11T00:00:01Z")
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(proposal["schema"], SCHEMA)
        self.assertTrue(proposal["read_only"])
        self.assertEqual(proposal["status"], "planned")
        self.assertEqual(proposal["authority"]["approval_state"], "planned")
        self.assertFalse(proposal["constraints"]["writes_performed"])
        self.assertFalse(proposal["constraints"]["approval_implied"])
        self.assertFalse(proposal["constraints"]["apply_authorized"])

    def test_identity_is_deterministic_for_same_plan_and_repository_state(self) -> None:
        plan = BootstrapPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        first = BootstrapProposalEngine(".").run(plan, generated_at="2026-08-11T00:00:01Z")
        second = BootstrapProposalEngine(".").run(plan, generated_at="2026-08-11T00:00:02Z")

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["identity_hash"], second["identity_hash"])
        self.assertEqual(first["source_plan"]["plan_hash"], stable_hash(plan))

    def test_plan_drift_invalidates_proposal(self) -> None:
        plan = BootstrapPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        proposal = BootstrapProposalEngine(".").run(plan, generated_at="2026-08-11T00:00:01Z")
        changed_plan = copy.deepcopy(plan)
        changed_plan["actions"][0]["reason"] = "Changed reason."

        drift = BootstrapProposalEngine(".").check_drift(proposal, changed_plan)

        self.assertTrue(drift["invalidated"])
        self.assertTrue(drift["checks"]["source_plan_hash_changed"])
        self.assertTrue(drift["checks"]["proposal_identity_changed"])

    def test_repository_drift_invalidates_proposal(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            plan = BootstrapPlanEngine(root).run(generated_at="2026-08-11T00:00:00Z")
            proposal = BootstrapProposalEngine(root).run(plan, generated_at="2026-08-11T00:00:01Z")
            write(root / ".contextos" / "manifest.yaml", "schema: contextos.runtime.manifest/1\n")

            drift = BootstrapProposalEngine(root).check_drift(proposal, plan)

        self.assertTrue(drift["invalidated"])
        self.assertTrue(drift["checks"]["repository_state_hash_changed"])
        self.assertTrue(drift["checks"]["proposal_identity_changed"])

    def test_saved_proposal_drift_check_reuses_source_plan_timestamp(self) -> None:
        plan = BootstrapPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        proposal = BootstrapProposalEngine(".").run(plan, generated_at="2026-08-11T00:00:01Z")

        drift = BootstrapProposalEngine(".").check_drift(proposal)

        self.assertFalse(drift["checks"]["source_plan_hash_changed"])

    def test_dirty_state_drift_invalidates_proposal(self) -> None:
        plan = BootstrapPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z")
        proposal = BootstrapProposalEngine(".").run(plan, generated_at="2026-08-11T00:00:01Z")
        changed = copy.deepcopy(proposal)
        changed["repository_state"]["fingerprint_hash"] = "stale-fingerprint"

        drift = BootstrapProposalEngine(".").check_drift(changed, plan)

        self.assertTrue(drift["invalidated"])
        self.assertTrue(drift["checks"]["repository_state_hash_changed"])

    def test_actions_preserve_classification_authority_and_rollback(self) -> None:
        proposal = BootstrapProposalEngine(".").run(
            BootstrapPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z"),
            mode="project",
            requested_by="Context OS Maintainers",
            generated_at="2026-08-11T00:00:01Z",
        )
        actions = {action["id"]: action for action in proposal["actions"]}

        self.assertEqual(proposal["authority"]["authority_level"], "L3")
        self.assertIn("Product Owner or Runtime Owner", proposal["authority"]["approving_roles"])
        self.assertEqual(actions["bootstrap.action.create_directory.contextos"]["class"], "automatic")
        self.assertEqual(actions["bootstrap.action.create_directory.contextos"]["rollback_strategy"], "delete_created")
        self.assertEqual(actions["bootstrap.action.create_manifest.contextos_manifest_yaml"]["class"], "approval_required")
        self.assertEqual(actions["bootstrap.action.validate_after_apply.pre_bootstrap"]["class"], "manual")

    def test_blocked_actions_are_prohibited_not_approvable(self) -> None:
        proposal = BootstrapProposalEngine("examples/sample_solo_founder").run(
            BootstrapPlanEngine("examples/sample_solo_founder").run(generated_at="2026-08-11T00:00:00Z"),
            generated_at="2026-08-11T00:00:01Z",
        )
        blocked = [action for action in proposal["actions"] if action["status"] == "blocked"]

        self.assertGreater(len(blocked), 0)
        self.assertTrue(all(action["class"] == "prohibited" for action in blocked))
        self.assertTrue(all(action["rollback_strategy"] == "none" for action in blocked))

    def test_json_report_is_serializable(self) -> None:
        proposal = BootstrapProposalEngine(".").run(
            BootstrapPlanEngine(".").run(generated_at="2026-08-11T00:00:00Z"),
            generated_at="2026-08-11T00:00:01Z",
        )
        loaded = json.loads(json.dumps(proposal, sort_keys=True))

        self.assertEqual(loaded["schema"], SCHEMA)
        self.assertIn("actions", loaded)


if __name__ == "__main__":
    unittest.main(verbosity=2)
