#!/usr/bin/env python3
"""Tests for Context OS Local Discovery Bundle."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


DISCOVERY_ROOT = Path(__file__).resolve().parent
if str(DISCOVERY_ROOT) not in sys.path:
    sys.path.insert(0, str(DISCOVERY_ROOT))

from discovery_engine.local_discovery import LocalDiscoveryBundleEngine  # noqa: E402
from discovery_engine.report_builder import SCHEMA, render_human  # noqa: E402


def write(path: Path, text: str = "# Test\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_snapshot(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


class LocalDiscoveryBundleTestCase(unittest.TestCase):
    def make_repo(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        write(root / "README.md", "# Example\nOwner: Jane Example\n\nSee [Vision](SSOT/S.1_Vision.md).\n")
        write(root / "SSOT" / "S.1_Vision.md", "# Vision\nOwner: Founder\n")
        write(root / "tools" / "script.py", "print('hello')\n")
        return temp

    def test_bundle_shape_and_read_only_constraints(self) -> None:
        with self.make_repo() as temp:
            root = Path(temp)
            before = file_snapshot(root)
            bundle = LocalDiscoveryBundleEngine(root).run(generated_at="2026-08-11T00:00:00Z")
            after = file_snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(bundle["schema"], SCHEMA)
        self.assertEqual(bundle["generated_at"], "2026-08-11T00:00:00Z")
        self.assertTrue(bundle["read_only"])
        self.assertFalse(bundle["constraints"]["writes_performed"])
        self.assertFalse(bundle["constraints"]["organizational_truth_created"])

    def test_observed_metadata_and_inferred_classification_are_separate(self) -> None:
        with self.make_repo() as temp:
            bundle = LocalDiscoveryBundleEngine(temp).run(generated_at="2026-08-11T00:00:00Z")
        artifacts = {artifact["path"]: artifact for artifact in bundle["artifacts"]}

        self.assertEqual(artifacts["README.md"]["observed"]["belief_state"], "observed")
        self.assertEqual(artifacts["README.md"]["classification"]["belief_state"], "inferred")
        self.assertEqual(artifacts["SSOT/S.1_Vision.md"]["classification"]["taxonomy_class"], "ssot-strategy")
        self.assertIn("not organizational truth", artifacts["SSOT/S.1_Vision.md"]["classification"]["truth_boundary"])

    def test_ownership_and_reference_relationships_are_observed(self) -> None:
        with self.make_repo() as temp:
            bundle = LocalDiscoveryBundleEngine(temp).run(generated_at="2026-08-11T00:00:00Z")
        ownership_paths = {item["path"] for item in bundle["ownership_evidence"]}
        relationships = {(item["type"], item["from"], item["to"]) for item in bundle["relationships"]}

        self.assertIn("README.md", ownership_paths)
        self.assertIn("SSOT/S.1_Vision.md", ownership_paths)
        self.assertIn(("references_path", "README.md", "SSOT/S.1_Vision.md"), relationships)

    def test_bundle_is_deterministic_with_fixed_time(self) -> None:
        with self.make_repo() as temp:
            first = LocalDiscoveryBundleEngine(temp).run(generated_at="2026-08-11T00:00:00Z")
            second = LocalDiscoveryBundleEngine(temp).run(generated_at="2026-08-11T00:00:00Z")

        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertEqual(first["source"]["fingerprint"], second["source"]["fingerprint"])

    def test_contextos_repo_dogfood_bundle_has_expected_signals(self) -> None:
        bundle = LocalDiscoveryBundleEngine(".").run(generated_at="2026-08-11T00:00:00Z")

        self.assertEqual(bundle["schema"], SCHEMA)
        self.assertGreater(bundle["summary"]["artifact_count"], 100)
        self.assertGreater(bundle["summary"]["relationship_count"], bundle["summary"]["artifact_count"])
        self.assertGreater(bundle["summary"]["ownership_evidence_count"], 0)

    def test_human_report_names_boundaries(self) -> None:
        with self.make_repo() as temp:
            bundle = LocalDiscoveryBundleEngine(temp).run(generated_at="2026-08-11T00:00:00Z")
        human = render_human(bundle)

        self.assertIn("# Context OS Local Discovery Bundle", human)
        self.assertIn("## Ownership Evidence", human)
        self.assertIn("## Boundaries", human)
        self.assertIn("semantic meaning", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
