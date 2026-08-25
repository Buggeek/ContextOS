from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1]
for runtime in ("adoption", "validators", "readiness", "activation", "health", "memory", "reasoning"):
    path = TOOLS / runtime
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from adoption_engine import AdoptionProfile  # noqa: E402
from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402
from engine.validator_engine import ValidatorEngine  # noqa: E402
from health_engine.health_engine import ContextHealthEngine  # noqa: E402
from memory_engine import ContextVersionEngine, MemoryRetrievalEngine  # noqa: E402
from readiness_engine.readiness_scoring import ReadinessScoringEngine  # noqa: E402
from reasoning_engine import ContextualAssessmentEngine  # noqa: E402


FIXED_TIME = "2026-08-25T00:00:00Z"
PROFILE_PATH = Path(__file__).resolve().parents[2] / "examples" / "adoption_profiles" / "lukspeed.json"
GOAL = "Reconcile active work Mission evidence while preserving target authority"
MISSION = "EXTERNAL-ADOPTION-TEST-001"


def snapshot(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


class ExternalAdoptionProfileTestCase(unittest.TestCase):
    def make_target(self) -> tuple[tempfile.TemporaryDirectory[str], Path, AdoptionProfile]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        profile = AdoptionProfile(PROFILE_PATH)
        for record in profile.source_records(root):
            path = root / record["locator"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f"# {record['concept'].replace('_', ' ').title()}\n\n"
                f"Target-native governed evidence for active work, Missions, decisions, closure, memory, authority, and architecture.\n",
                encoding="utf-8",
            )
        return temp, root, profile

    def test_profile_identity_is_deterministic_and_is_not_target_ssot(self) -> None:
        first = AdoptionProfile(PROFILE_PATH)
        second = AdoptionProfile(PROFILE_PATH)
        self.assertEqual(first.identity_hash, second.identity_hash)
        self.assertEqual(first.binding(), second.binding())
        self.assertTrue(first.binding()["not_target_ssot"])
        changed = copy.deepcopy(first.data)
        changed["version"] = "1.0.1"
        self.assertNotEqual(first.identity_hash, AdoptionProfile(changed).identity_hash)

    def test_native_taxonomy_is_classified_not_silently_suppressed(self) -> None:
        temp, root, profile = self.make_target()
        self.addCleanup(temp.cleanup)
        report = ValidatorEngine(root, profile).run(mode="full")
        results = {item["rule"]: item for item in report["rule_results"]}
        self.assertEqual(report["summary"]["exit_code"], 0)
        self.assertEqual(results["taxonomy.ssot_filename_prefix"]["status"], "not_applicable")
        self.assertEqual(results["mom.required_artifacts"]["status"], "mapped_equivalent")
        self.assertEqual(results["structure.tracked_junk_absent"]["status"], "unknown")
        self.assertTrue(results["mom.required_artifacts"]["equivalent_control_refs"])

    def test_readiness_uses_functional_equivalence_and_activation_is_profile_bound(self) -> None:
        temp, root, profile = self.make_target()
        self.addCleanup(temp.cleanup)
        readiness = ReadinessScoringEngine(root, adoption_profile=profile).run(generated_at=FIXED_TIME)
        self.assertEqual(readiness["mode"], "external_adoption_profile")
        self.assertGreaterEqual(readiness["summary"]["score"], 75)
        self.assertNotIn("Runtime manifest is absent.", json.dumps(readiness))

        engine = ContextActivationPackageEngine(root, profile)
        package = engine.run(goal=GOAL, mission_id=MISSION, consumer="codex", generated_at=FIXED_TIME)
        self.assertTrue(package["summary"]["activation_allowed"])
        self.assertGreater(len(package["canonical_sources"]), 1)
        self.assertEqual(package["adoption_profile"]["identity_hash"], profile.identity_hash)
        handoff = engine.build_handoff(package, generated_at=FIXED_TIME)
        self.assertTrue(handoff["mission_context"]["governing_context"]["sufficient_for_orientation"])
        self.assertTrue(engine.check_handoff(handoff, generated_at=FIXED_TIME)["result"]["valid"])
        (root / package["canonical_sources"][0]["path"]).write_text("# Drifted\n", encoding="utf-8")
        self.assertFalse(engine.check_package(package, generated_at=FIXED_TIME)["result"]["valid"])

    def test_health_memory_and_reasoning_use_only_target_profile_evidence(self) -> None:
        temp, root, profile = self.make_target()
        self.addCleanup(temp.cleanup)
        before = snapshot(root)
        health_engine = ContextHealthEngine(root, profile)
        health = health_engine.run(generated_at=FIXED_TIME)
        self.assertFalse(health["evidence_isolation"]["host_context_used_as_target_evidence"])
        for ref in health["evidence_isolation"]["target_evidence_refs"]:
            self.assertTrue((root / ref).is_file(), ref)

        memory = MemoryRetrievalEngine(root, profile).run(
            goal=GOAL,
            mission_id=MISSION,
            generated_at=FIXED_TIME,
            evaluation_time=FIXED_TIME,
        )
        self.assertGreater(memory["summary"]["relevant_candidate_count"], 0)
        self.assertEqual(memory["summary"]["selected_count"], 0)
        self.assertEqual(memory["summary"]["policy_outcomes"].get("unknown"), memory["summary"]["relevant_candidate_count"])

        reasoning = ContextualAssessmentEngine(root, profile).run(
            goal=GOAL,
            mission_id=MISSION,
            generated_at=FIXED_TIME,
            evaluation_time=FIXED_TIME,
        )
        self.assertEqual(reasoning["bindings"]["adoption_profile"]["identity_hash"], profile.identity_hash)
        self.assertFalse(reasoning["evidence_isolation"]["host_context_used_as_target_evidence"])
        self.assertEqual(snapshot(root), before)

    def test_profile_change_invalidates_health_and_context_version_applicability(self) -> None:
        temp, root, profile = self.make_target()
        self.addCleanup(temp.cleanup)
        health = ContextHealthEngine(root, profile).run(generated_at=FIXED_TIME)
        changed_data = copy.deepcopy(profile.data)
        changed_data["version"] = "1.0.1"
        changed = AdoptionProfile(changed_data)
        health_check = ContextHealthEngine(root, changed).check_report(health, generated_at=FIXED_TIME)
        self.assertTrue(health_check["result"]["invalidated"])

        package = ContextActivationPackageEngine(root, profile).run(
            goal=GOAL, mission_id=MISSION, consumer="codex", generated_at=FIXED_TIME
        )
        self.assertTrue(
            ContextActivationPackageEngine(root, changed).check_package(package, generated_at=FIXED_TIME)["result"]["invalidated"]
        )

        memory = MemoryRetrievalEngine(root, profile).run(
            goal=GOAL, mission_id=MISSION, evaluation_time=FIXED_TIME, generated_at=FIXED_TIME
        )
        self.assertTrue(
            MemoryRetrievalEngine(root, changed).check_retrieval(
                memory, evaluation_time=FIXED_TIME, generated_at=FIXED_TIME
            )["result"]["invalidated"]
        )

        reasoning = ContextualAssessmentEngine(root, profile).run(
            goal=GOAL, mission_id=MISSION, evaluation_time=FIXED_TIME, generated_at=FIXED_TIME
        )
        self.assertTrue(
            ContextualAssessmentEngine(root, changed).check_assessment(reasoning, generated_at=FIXED_TIME)["result"]["invalidated"]
        )

        engine = ContextVersionEngine(root, profile)
        plan = engine.plan(
            scope={"organization": "fixture", "domain": "organization", "tier": "organizational", "context_root": "repository"},
            event_type="explicit_human_checkpoint",
            reason="External adoption profile test",
            capture_at=FIXED_TIME,
            generated_at=FIXED_TIME,
        )
        self.assertEqual(plan["status"], "ready")
        self.assertGreater(plan["summary"]["source_count"], 1)
        version = engine.capture(plan, generated_at=FIXED_TIME)
        changed_check = ContextVersionEngine(root, changed).check_version(version, generated_at=FIXED_TIME)
        self.assertEqual(changed_check["result"]["immutable_identity"], "valid")
        self.assertEqual(changed_check["result"]["current_applicability"], "superseded_or_drifted")

    def test_cli_profile_surfaces_emit_pure_target_bound_json(self) -> None:
        temp, root, _profile = self.make_target()
        self.addCleanup(temp.cleanup)
        cli = Path(__file__).resolve().parents[2] / "contextos"
        common = ["--root", str(root), "--format", "json", "--adoption-profile", str(PROFILE_PATH)]
        commands = {
            "validate": [str(cli), "validate", *common, "--mode", "gate"],
            "assess": [str(cli), "assess", *common],
            "activate": [str(cli), "activate", *common, "--goal", GOAL, "--mission-id", MISSION],
            "health": [str(cli), "health", *common],
            "memory": [str(cli), "memory", *common, "--goal", GOAL, "--mission-id", MISSION],
            "reason": [str(cli), "reason", *common, "--goal", GOAL, "--mission-id", MISSION],
        }
        before = snapshot(root)
        for command, argv in commands.items():
            completed = subprocess.run(argv, check=False, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(completed.returncode, 0, f"{command}: {completed.stderr}")
            report = json.loads(completed.stdout)
            binding = report.get("adoption_profile") or report.get("bindings", {}).get("adoption_profile")
            self.assertEqual(binding["id"], "adoption.profile.lukspeed.v1", command)
        self.assertEqual(snapshot(root), before)


if __name__ == "__main__":
    unittest.main()
