#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


MEMORY_ROOT = Path(__file__).resolve().parent
if str(MEMORY_ROOT) not in sys.path:
    sys.path.insert(0, str(MEMORY_ROOT))

from memory_engine import MemoryRetrievalEngine  # noqa: E402
from memory_engine.retrieval_report_builder import CHECK_SCHEMA, SCHEMA, render_human  # noqa: E402


FIXED_TIME = "2026-08-21T12:00:00Z"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def ssot_doc(title: str, body: str = "Test artifact.") -> str:
    return f"""# {title}
## Version: 0.1.0
Last Updated: 2026-08-21
Owner: Test Owner

---

## Purpose

{body}

## Change Log

- 2026-08-21 - v0.1.0 - Initial creation.
"""


def mission(mission_id: str, title: str, learning: str) -> str:
    return f"""# E.4 Mission {mission_id} - {title}
## Version: 0.1.0
Last Updated: 2026-08-21
Owner: Test Owner
Status: closed:done

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: {mission_id}
  release: v0.8-organizational-memory
  created_at: 2026-08-20
  status: closed:done
```

## Decision

Preserve bounded memory retrieval provenance and human authority.

## Evidence Captured

Observed source hashes remained traceable during retrieval validation.

## Outcome

The read-only memory result remained non-canonical.

## Learning

{learning}
"""


def make_repo(root: Path) -> None:
    for directory in ("docs", "SSOT", "ops", "templates"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    write(root / "README.md", "# Test Context OS Repository\n")
    write(root / "ops" / "AGENT_RULES.md", "# Context OS Agent Rules\n")
    write(root / "docs" / "3.x_operation" / "3.6_COS_Human_Agent_Authority_Model.md", "# Authority\n\nL0 L1 L2 L3 L4 L5\n")
    write(root / "SSOT" / "README.md", "# SSOT\n\nCompliance profile: `strict`\n")
    write(root / "SSOT" / "S.1_Vision.md", ssot_doc("S.1 Vision", "Governed organizational continuity."))
    write(root / "SSOT" / "P.1_Product_Map.md", ssot_doc("P.1 Product Map", "Memory retrieval product surface."))
    write(
        root / "SSOT" / "P.2_Product_Roadmap.md",
        ssot_doc("P.2 Product Roadmap", "# Current Version\n\nv0.8 - Organizational Memory\n\n| Version | Name |\n|---|---|\n| v0.8 | Organizational Memory |"),
    )
    write(root / "SSOT" / "A.1_System_Map.md", ssot_doc("A.1 System Map", "Memory and Activation runtime."))
    write(root / "SSOT" / "A.4_Data_Entities.md", ssot_doc("A.4 Data Entities"))
    write(root / "SSOT" / "G.1_Definition_of_Ready.md", ssot_doc("G.1 Definition of Ready"))
    write(root / "SSOT" / "G.2_Definition_of_Done.md", ssot_doc("G.2 Definition of Done"))
    write(
        root / "SSOT" / "E.4_Mission_TEST-MEMORY-001_Memory_Continuity.md",
        mission("TEST-MEMORY-001", "Memory Continuity", "Historical memory remains prior art and never regains authority automatically."),
    )
    write(
        root / "SSOT" / "E.4_Mission_TEST-ACTIVATION-001_Context_Activation.md",
        mission("TEST-ACTIVATION-001", "Context Activation", "Activation provides current context while memory preserves historical evidence provenance."),
    )
    write(
        root / "SSOT" / "E.5_Evolution_Inbox.md",
        """# E.5 Evolution Inbox
## Version: 0.1.0
Last Updated: 2026-08-21
Owner: Test Owner

| ID | Category | Status | Source | Observation | Disposition |
|---|---|---|---|---|---|
| INBOX-001 | architecture | superseded | TEST-MEMORY-001 | Earlier memory archive approach. | Superseded by governed continuity. |
""",
    )


def snapshot(root: Path) -> dict[str, bytes]:
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def policy_inputs() -> dict:
    return {
        "retention_policies": [
            {
                "schema": "contextos.memory.retention_policy/1",
                "id": "policy.test.memory-retrieval",
                "version": "1",
                "status": "active",
                "scope": {
                    "memory_forms": [
                        "mission", "decision", "evidence", "outcome", "learning", "context_state", "evolution_inbox"
                    ]
                },
                "effects": {"access": "normal", "retrieval": "normal", "activation": "normal"},
                "obligations": [{"id": "preserve.test-lineage", "kind": "preserve"}],
                "holds": [],
                "required_authority": {},
                "inherits_from": [],
                "explanation_visibility": "id_only",
            }
        ],
        "memory_metadata_by_id": {
            "defaults": {
                "organization": "test",
                "operation": "product",
                "tier": "organizational",
                "owner": "Test Owner",
                "sensitivity": "internal",
                "retention_state": "historical",
                "metadata_visibility": "full",
            }
        },
    }


class MemoryRetrievalTestCase(unittest.TestCase):
    def test_retrieval_binds_continuity_and_current_activation(self) -> None:
        report = MemoryRetrievalEngine(".").run(
            goal="Retrieve governed memory prior art with provenance",
            mission_id="V08-MEMORY-RETRIEVAL-SURFACE-001",
            consumer="codex",
            generated_at=FIXED_TIME,
            **policy_inputs(),
        )

        self.assertEqual(report["schema"], SCHEMA)
        self.assertEqual(report["bindings"]["memory_continuity"]["schema"], "contextos.memory.continuity_report/1")
        self.assertEqual(report["bindings"]["activation_package"]["schema"], "contextos.activation.package/1")
        self.assertGreater(report["summary"]["selected_count"], 0)
        self.assertFalse(report["authority"]["retrieved_memory_may_override_canonical"])
        self.assertFalse(report["authority"]["retrieved_memory_added_to_governing_context"])

    def test_retrieval_is_read_only_deterministic_and_bounded(self) -> None:
        root = Path(".").resolve()
        before = snapshot(root)
        first = MemoryRetrievalEngine(root).run(goal="memory provenance authority", limit=5, generated_at=FIXED_TIME, **policy_inputs())
        second = MemoryRetrievalEngine(root).run(goal="memory provenance authority", limit=5, generated_at=FIXED_TIME, **policy_inputs())
        after = snapshot(root)

        self.assertEqual(before, after)
        self.assertEqual(json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True))
        self.assertLessEqual(len(first["items"]), 5)
        self.assertTrue(all(item["selection"]["matched_terms"] for item in first["items"]))

    def test_selected_memory_preserves_truth_applicability_and_authority_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            report = MemoryRetrievalEngine(root).run(
                goal="memory retrieval provenance authority",
                question="Which historical decision remains relevant?",
                generated_at=FIXED_TIME,
                **policy_inputs(),
            )

        self.assertGreater(len(report["items"]), 0)
        for item in report["items"]:
            self.assertEqual(item["applicability"]["status"], "candidate")
            self.assertFalse(item["applicability"]["proven_useful"])
            self.assertEqual(item["authority"]["current_authority"], "none_from_retrieval")
            self.assertFalse(item["authority"]["may_override_current_context"])
            self.assertFalse(item["canonical"])
            self.assertIn("epistemic_support", item["truth"])

    def test_unchanged_retrieval_check_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            engine = MemoryRetrievalEngine(root)
            report = engine.run(goal="memory provenance", generated_at=FIXED_TIME, **policy_inputs())
            check = engine.check_retrieval(report, generated_at=FIXED_TIME, **policy_inputs())

        self.assertEqual(check["schema"], CHECK_SCHEMA)
        self.assertTrue(check["result"]["valid"])
        self.assertFalse(check["result"]["invalidated"])

    def test_source_drift_invalidates_saved_retrieval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            engine = MemoryRetrievalEngine(root)
            report = engine.run(goal="memory provenance", generated_at=FIXED_TIME, **policy_inputs())
            source = root / "SSOT" / "E.4_Mission_TEST-MEMORY-001_Memory_Continuity.md"
            source.write_text(source.read_text(encoding="utf-8") + "\nChanged evidence.\n", encoding="utf-8")
            check = engine.check_retrieval(report, generated_at=FIXED_TIME, **policy_inputs())

        self.assertFalse(check["result"]["valid"])
        self.assertIn("memory_retrieval_check.continuity_state_changed", check["result"]["failed_checks"])
        self.assertIn("memory_retrieval_check.selection_changed", check["result"]["failed_checks"])

    def test_tampered_retrieval_identity_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            engine = MemoryRetrievalEngine(root)
            report = engine.run(goal="memory provenance", generated_at=FIXED_TIME, **policy_inputs())
            report["items"][0]["selection"]["score"] += 1
            check = engine.check_retrieval(report, generated_at=FIXED_TIME, **policy_inputs())

        self.assertFalse(check["checks"]["identity_valid"])
        self.assertIn("memory_retrieval_check.identity_hash_mismatch", check["result"]["failed_checks"])

    def test_explicit_supersession_is_selectable_as_a_structured_relationship(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_repo(root)
            report = MemoryRetrievalEngine(root).run(
                goal="Retrieve supersession memory",
                question="What was superseded?",
                generated_at=FIXED_TIME,
                **policy_inputs(),
            )

        superseded = [item for item in report["items"] if item["temporal_status"] == "superseded"]
        self.assertGreater(len(superseded), 0)
        self.assertIn("explicit_supersession_requested", superseded[0]["selection"]["relationship_signals"])
        self.assertEqual(superseded[0]["supersession"]["status"], "explicit")

    def test_human_report_explains_selection_and_limits(self) -> None:
        report = MemoryRetrievalEngine(".").run(goal="memory prior art provenance", generated_at=FIXED_TIME, **policy_inputs())
        human = render_human(report)

        self.assertIn("# Context OS Memory Retrieval", human)
        self.assertIn("## Authority Boundary", human)
        self.assertIn("## Retrieved Memory Candidates", human)
        self.assertIn("Why selected:", human)
        self.assertIn("Selection does not prove applicability", human)
        self.assertIn("## Freshness And Invalidation", human)


if __name__ == "__main__":
    unittest.main(verbosity=2)
