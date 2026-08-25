#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


RUNTIME_ROOT = Path(__file__).resolve().parent
REPO_ROOT = RUNTIME_ROOT.parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from runtime_engine import OrganizationalContextRuntimeBenchmarkEngine  # noqa: E402
from runtime_engine.report_builder import SCHEMA, render_human  # noqa: E402
from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402


FIXED_TIME = "2026-08-24T12:00:00Z"
GOAL = "Prove the complete governed Organizational Context Runtime"
MISSION_ID = "V10-RUNTIME-INTEGRATION-BENCHMARK-001"


def copy_repo(destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".DS_Store"}
        return {name for name in names if name in ignored}

    shutil.copytree(REPO_ROOT, destination, ignore=ignore)


class RuntimeIntegrationBenchmarkTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        copy_repo(Path(temp.name) / "repo")
        return temp

    def test_integrated_benchmark_passes_and_preserves_runtime_boundaries(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp) / "repo"
            report = OrganizationalContextRuntimeBenchmarkEngine(root).run(
                goal=GOAL,
                mission_id=MISSION_ID,
                generated_at=FIXED_TIME,
            )

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["summary"]["status"], "pass")
        self.assertEqual(report["summary"]["release_blocker_count"], 0)
        self.assertTrue(report["read_only"])
        self.assertFalse(report["boundaries"]["activated_context_is_canonical"])
        self.assertFalse(report["boundaries"]["memory_is_current_authority"])
        self.assertFalse(report["boundaries"]["reasoning_may_decide"])
        self.assertFalse(report["boundaries"]["write_stages_replayed"])
        self.assertEqual(report["graphrag"]["decision"], "defer")
        self.assertEqual(len(report["journey"]), 14)

    def test_fixed_state_is_deterministic_and_machine_parseable(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp) / "repo"
            engine = OrganizationalContextRuntimeBenchmarkEngine(root)
            first = engine.run(goal=GOAL, mission_id=MISSION_ID, generated_at=FIXED_TIME)
            second = engine.run(goal=GOAL, mission_id=MISSION_ID, generated_at=FIXED_TIME)

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["identity_hash"], second["identity_hash"])
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(json.loads(json.dumps(first))["schema"], SCHEMA)

    def test_source_drift_invalidates_package_and_fresh_generation_recovers(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp) / "repo"
            engine = ContextActivationPackageEngine(root)
            package = engine.run(goal=GOAL, mission_id=MISSION_ID, generated_at=FIXED_TIME)
            selected = root / package["canonical_sources"][0]["path"]
            selected.write_text(selected.read_text(encoding="utf-8") + "\nControlled drift.\n", encoding="utf-8")
            stale_check = engine.check_package(package, generated_at=FIXED_TIME)
            fresh = engine.run(goal=GOAL, mission_id=MISSION_ID, generated_at=FIXED_TIME)
            fresh_check = engine.check_package(fresh, generated_at=FIXED_TIME)

        self.assertFalse(stale_check["result"]["valid"])
        self.assertTrue(stale_check["result"]["invalidated"])
        self.assertTrue(fresh_check["result"]["valid"])
        self.assertNotEqual(package["identity_hash"], fresh["identity_hash"])

    def test_tampered_boundary_is_visible_as_a_failed_check(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp) / "repo"
            report = OrganizationalContextRuntimeBenchmarkEngine(root).run(
                goal=GOAL,
                mission_id=MISSION_ID,
                generated_at=FIXED_TIME,
            )
        tampered = copy.deepcopy(report)
        tampered["boundaries"]["reasoning_may_decide"] = True

        self.assertTrue(OrganizationalContextRuntimeBenchmarkEngine.identity_valid(report))
        self.assertFalse(OrganizationalContextRuntimeBenchmarkEngine.identity_valid(tampered))

    def test_human_report_explains_journey_checks_and_boundaries(self) -> None:
        report = OrganizationalContextRuntimeBenchmarkEngine(REPO_ROOT).run(
            goal=GOAL,
            mission_id=MISSION_ID,
            generated_at=FIXED_TIME,
        )
        human = render_human(report)

        self.assertIn("# Context OS Organizational Context Runtime Benchmark", human)
        self.assertIn("## Integrated Journey", human)
        self.assertIn("## Runtime Boundaries", human)
        self.assertIn("Reasoning remains advisory", human)
        self.assertIn("Target mutation: none", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
