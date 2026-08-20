from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from health_engine.report_builder import build_report


TOOLS_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
READINESS_ROOT = TOOLS_ROOT / "readiness"
for runtime_path in (VALIDATORS_ROOT, READINESS_ROOT):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

from engine.validator_engine import ValidatorEngine  # noqa: E402
from readiness_engine.readiness_scoring import ReadinessScoringEngine  # noqa: E402


MISSION_PATTERN = "E.4_Mission_*.md"
STATUS_PATTERN = re.compile(r"^Status:\s*(.+?)\s*$", re.MULTILINE)
INBOX_ROW_PATTERN = re.compile(r"^\|\s*(INBOX-\d+)\s*\|(.+?)\|\s*$")
BELIEF_STATES = {"observed", "declared", "derived", "unknown"}


def stable_hash(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def signal_id(dimension: str, kind: str, evidence_refs: list[str]) -> str:
    identity = {"dimension": dimension, "kind": kind, "evidence_refs": sorted(evidence_refs)}
    return f"health.signal.{dimension}.{kind}.{stable_hash(identity)[:12]}"


def make_signal(
    dimension: str,
    kind: str,
    status: str,
    message: str,
    evidence_refs: list[str],
    *,
    belief_state: str = "observed",
) -> dict:
    if belief_state not in BELIEF_STATES:
        raise ValueError(f"Unsupported Health signal belief state: {belief_state!r}.")
    refs = sorted(dict.fromkeys(evidence_refs))
    return {
        "id": signal_id(dimension, kind, refs),
        "dimension": dimension,
        "kind": kind,
        "status": status,
        "belief_state": belief_state,
        "message": message,
        "evidence_refs": refs,
        "canonical": False,
    }


def aggregate_status(signals: list[dict]) -> str:
    statuses = {signal["status"] for signal in signals}
    if "blocked" in statuses:
        return "blocked"
    if "attention" in statuses:
        return "attention"
    if "unknown" in statuses:
        return "unknown"
    return "healthy"


def dimension(dimension_id: str, title: str, question: str, signals: list[dict]) -> dict:
    counts = Counter(signal["status"] for signal in signals)
    return {
        "id": dimension_id,
        "title": title,
        "question": question,
        "status": aggregate_status(signals),
        "counts": {
            "total": len(signals),
            "healthy": counts["healthy"],
            "attention": counts["attention"],
            "blocked": counts["blocked"],
            "unknown": counts["unknown"],
        },
        "signals": signals,
    }


def read_mission_evidence(root: Path) -> dict:
    mission_dir = root / "SSOT"
    missions: list[dict] = []
    if mission_dir.is_dir():
        for path in sorted(mission_dir.glob(MISSION_PATTERN)):
            text = path.read_text(encoding="utf-8")
            status_match = STATUS_PATTERN.search(text)
            status = status_match.group(1).strip() if status_match else "unknown"
            missions.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "status": status,
                    "has_learning": "## Learning" in text,
                    "mentions_invalidation": "invalidat" in text.lower() or "drift" in text.lower(),
                    "mentions_execution_context": "Execution Context" in text or "additional context" in text.lower(),
                    "mentions_authority": "authority" in text.lower(),
                    "is_activation": "V06-" in path.name,
                }
            )
    closed = [mission for mission in missions if mission["status"].startswith("closed:done")]
    return {
        "items": missions,
        "count": len(missions),
        "closed_count": len(closed),
        "learning_count": sum(1 for mission in closed if mission["has_learning"]),
        "invalidation_count": sum(1 for mission in closed if mission["mentions_invalidation"]),
        "execution_context_count": sum(1 for mission in closed if mission["mentions_execution_context"]),
        "authority_count": sum(1 for mission in closed if mission["mentions_authority"]),
        "activation_paths": [mission["path"] for mission in closed if mission["is_activation"]],
    }


def read_evolution_inbox(root: Path) -> dict:
    path = root / "SSOT" / "E.5_Evolution_Inbox.md"
    items: list[dict] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            match = INBOX_ROW_PATTERN.match(line)
            if not match:
                continue
            cells = [cell.strip() for cell in match.group(2).split("|")]
            if len(cells) < 5:
                continue
            items.append(
                {
                    "id": match.group(1),
                    "category": cells[0],
                    "status": cells[1],
                    "source": cells[2],
                    "observation": cells[3],
                    "disposition": cells[4],
                }
            )
    return {
        "path": path.relative_to(root).as_posix() if path.is_file() else None,
        "items": items,
        "item_count": len(items),
        "category_counts": dict(sorted(Counter(item["category"] for item in items).items())),
        "status_counts": dict(sorted(Counter(item["status"] for item in items).items())),
    }


def validator_signals(validator_report: dict) -> list[dict]:
    summary = validator_report["summary"]
    blocking = summary["error"] + summary["fatal"]
    signals = [
        make_signal(
            "integrity",
            "validator_gate",
            "blocked" if blocking else "healthy",
            f"Validator reports {blocking} blocking findings.",
            ["validator.summary"],
        )
    ]
    warnings = [finding for finding in validator_report["findings"] if finding["severity"] == "warn"]
    warning_rules = Counter(finding["rule"] for finding in warnings)
    signals.append(
        make_signal(
            "integrity",
            "validator_warnings",
            "attention" if warnings else "healthy",
            f"Validator reports {len(warnings)} warnings across {len(warning_rules)} rule groups.",
            [f"validator.rule.{rule}" for rule in sorted(warning_rules)],
        )
    )
    ownership = [finding for finding in warnings if finding["rule"].startswith("ownership.")]
    signals.append(
        make_signal(
            "integrity",
            "ownership",
            "attention" if ownership else "healthy",
            "Ownership warnings require attention." if ownership else "Validator reports no ownership warnings.",
            [finding.get("path") or finding["id"] for finding in ownership] or ["validator.summary"],
        )
    )
    return signals


def readiness_signals(readiness_report: dict) -> list[dict]:
    summary = readiness_report["summary"]
    caps = summary.get("cap_reasons", [])
    return [
        make_signal(
            "integrity",
            "readiness_caps",
            "attention" if caps else "healthy",
            f"Readiness is capped for {len(caps)} explainable reason(s)." if caps else "Readiness has no score caps.",
            ["readiness.summary"] + [f"readiness.cap.{index + 1}" for index in range(len(caps))],
        )
    ]


def usefulness_signals(missions: dict, mission_use_evidence: dict | None = None) -> list[dict]:
    activation_refs = missions["activation_paths"]
    signals = [
        make_signal(
            "usefulness",
            "activation_mission_evidence",
            "healthy" if activation_refs else "unknown",
            f"Observed {len(activation_refs)} closed activation Mission artifacts." if activation_refs else "No closed activation Mission evidence was found.",
            activation_refs,
        ),
        make_signal(
            "usefulness",
            "drift_invalidation_evidence",
            "healthy" if missions["invalidation_count"] else "unknown",
            f"Observed drift or invalidation evidence in {missions['invalidation_count']} closed Missions."
            if missions["invalidation_count"]
            else "No Mission evidence demonstrates stale-context invalidation.",
            [mission["path"] for mission in missions["items"] if mission["status"].startswith("closed:done") and mission["mentions_invalidation"]],
        ),
        make_signal(
            "usefulness",
            "bounded_execution_context",
            "healthy" if missions["execution_context_count"] else "unknown",
            f"Observed bounded Execution Context discussion in {missions['execution_context_count']} closed Missions."
            if missions["execution_context_count"]
            else "No bounded Execution Context evidence was found.",
            [mission["path"] for mission in missions["items"] if mission["status"].startswith("closed:done") and mission["mentions_execution_context"]],
        ),
    ]
    if mission_use_evidence is None:
        signals.append(
            make_signal(
                "usefulness",
                "per_source_usage_traceability",
                "unknown",
                "Mission evidence is narrative; per-source selected-versus-used evidence is not yet machine-measurable.",
                activation_refs,
                belief_state="unknown",
            )
        )
        return signals

    if mission_use_evidence.get("schema") != "contextos.mission.context_use_evidence/1":
        raise ValueError("Health requires contextos.mission.context_use_evidence/1 input.")
    summary = mission_use_evidence["summary"]
    validity = mission_use_evidence["validity"]
    evidence_ref = [mission_use_evidence["id"]]
    valid = (
        validity["package_valid_at_capture"]
        and validity["handoff_valid_at_capture"]
        and validity["package_handoff_binding_matches"]
    )
    signals.extend(
        [
            make_signal(
                "usefulness",
                "mission_use_evidence_integrity",
                "healthy" if valid else "blocked",
                "Mission-use evidence is bound to a valid package and handoff."
                if valid
                else f"Mission-use evidence has {len(validity['failed_checks'])} failed binding or freshness checks.",
                evidence_ref + validity["failed_checks"],
                belief_state="derived",
            ),
            make_signal(
                "usefulness",
                "per_source_usage_traceability",
                "healthy" if summary["selected_accessed_count"] or summary["execution_retrieval_count"] else "unknown",
                f"Structured evidence distinguishes {summary['selected_count']} selected sources, "
                f"{summary['selected_accessed_count']} accessed selected sources, and "
                f"{summary['execution_retrieval_count']} additional retrievals.",
                evidence_ref,
                belief_state="derived",
            ),
            make_signal(
                "usefulness",
                "context_gaps_during_execution",
                "attention" if summary["gap_count"] or summary["stale_context_count"] else "healthy",
                f"Mission-use evidence records {summary['gap_count']} context gaps and "
                f"{summary['stale_context_count']} stale or invalid context observations.",
                evidence_ref,
                belief_state="derived",
            ),
            make_signal(
                "usefulness",
                "context_contribution_traceability",
                "healthy" if summary["contribution_count"] or summary["used_assertion_count"] else "unknown",
                f"Mission-use evidence records {summary['contribution_count']} contributions and "
                f"{summary['used_assertion_count']} explicit use assertions.",
                evidence_ref,
                belief_state="derived",
            ),
            make_signal(
                "usefulness",
                "usefulness_effect",
                "healthy" if summary["supported_useful_assertion_count"] else "unknown",
                f"Mission-use evidence contains {summary['supported_useful_assertion_count']} supported usefulness assertions."
                if summary["supported_useful_assertion_count"]
                else "Context participation is traceable, but actual usefulness remains unknown without explicit supporting evidence.",
                evidence_ref,
                belief_state="derived" if summary["supported_useful_assertion_count"] else "unknown",
            ),
        ]
    )
    return signals


def learning_signals(missions: dict, inbox: dict) -> list[dict]:
    mission_refs = [mission["path"] for mission in missions["items"] if mission["has_learning"]]
    inbox_ref = [inbox["path"]] if inbox["path"] else []
    return [
        make_signal(
            "learning",
            "mission_learning_capture",
            "healthy" if missions["learning_count"] else "unknown",
            f"Observed explicit Learning sections in {missions['learning_count']} closed Missions."
            if missions["learning_count"]
            else "No explicit Mission learning evidence was found.",
            mission_refs,
        ),
        make_signal(
            "learning",
            "evolution_inbox_capture",
            "healthy" if inbox["item_count"] else "unknown",
            f"Evolution Inbox preserves {inbox['item_count']} observations across {len(inbox['category_counts'])} categories."
            if inbox["item_count"]
            else "No Evolution Inbox observations were found.",
            inbox_ref,
        ),
        make_signal(
            "learning",
            "construction_route",
            "healthy",
            "Context update candidates are routed to the existing governed Construction lifecycle.",
            [
                "docs/1.x_architecture/1.5_runtime_contracts/1.5.8_Builder_Draft_Authority_Contract.md",
                "SSOT/E.4_Mission_V05-CONTEXT-CONSTRUCTION-PLAN-001_Context_Construction_Planning.md",
            ],
            belief_state="observed",
        ),
    ]


def candidate(kind: str, priority: str, title: str, rationale: str, action: str, signal_refs: list[str]) -> dict:
    identity = {"kind": kind, "signal_refs": sorted(signal_refs)}
    return {
        "id": f"health.candidate.{kind}.{stable_hash(identity)[:12]}",
        "kind": kind,
        "priority": priority,
        "title": title,
        "rationale": rationale,
        "suggested_action": action,
        "source_signal_refs": sorted(signal_refs),
        "lifecycle_state": "suggested",
        "canonical": False,
        "required_authority": "human_review_before_construction",
        "route": "existing_context_construction_lifecycle",
        "promotion_prohibited": True,
    }


def build_candidates(dimensions: dict, readiness_report: dict) -> list[dict]:
    signals = [signal for value in dimensions.values() for signal in value["signals"]]
    by_kind = {signal["kind"]: signal for signal in signals}
    candidates: list[dict] = []
    warning_signal = by_kind["validator_warnings"]
    if warning_signal["status"] == "attention":
        candidates.append(
            candidate(
                "review_validator_warnings",
                "high",
                "Review recurring Validator warning groups",
                warning_signal["message"],
                "Triage warning groups and create governed remediation Missions only for confirmed context defects.",
                [warning_signal["id"]],
            )
        )
    cap_signal = by_kind["readiness_caps"]
    if cap_signal["status"] == "attention":
        candidates.append(
            candidate(
                "review_readiness_caps",
                "high",
                "Review readiness constraints",
                "; ".join(readiness_report["summary"].get("cap_reasons", [])),
                "Use Readiness recommendations as evidence for a governed Construction or Bootstrap decision.",
                [cap_signal["id"]],
            )
        )
    usage_signal = by_kind["per_source_usage_traceability"]
    if usage_signal["status"] == "unknown":
        candidates.append(
            candidate(
                "structure_activation_usage_evidence",
                "medium",
                "Structure selected-versus-used activation evidence",
                usage_signal["message"],
                "Capture a read-only Mission-use evidence object before trend or effectiveness analysis.",
                [usage_signal["id"]],
            )
        )
    return candidates


class ContextHealthEngine:
    """Read-only, evidence-first Context Health and Learning report engine."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        *,
        validator_report: dict | None = None,
        readiness_report: dict | None = None,
        mission_use_evidence: dict | None = None,
        generated_at: str | None = None,
    ) -> dict:
        root = self.root.resolve()
        if mission_use_evidence is not None:
            evidence_root = mission_use_evidence.get("root")
            if not evidence_root or Path(evidence_root).resolve() != root:
                raise ValueError("Mission-use evidence root does not match the Health target root.")
        validator = validator_report or ValidatorEngine(root).run(mode="full")
        readiness = readiness_report or ReadinessScoringEngine(root, validator_mode="full").run(
            validator_report=validator,
            generated_at=generated_at,
        )
        missions = read_mission_evidence(root)
        inbox = read_evolution_inbox(root)
        dimensions = {
            "integrity": dimension(
                "integrity",
                "Context Integrity",
                "Is context structurally and epistemically trustworthy?",
                validator_signals(validator) + readiness_signals(readiness),
            ),
            "usefulness": dimension(
                "usefulness",
                "Context Usefulness",
                "Did activated context help a Mission without unnecessary or stale context?",
                usefulness_signals(missions, mission_use_evidence),
            ),
            "learning": dimension(
                "learning",
                "Organizational Learning",
                "What did execution teach that may justify governed context evolution?",
                learning_signals(missions, inbox),
            ),
        }
        candidates = build_candidates(dimensions, readiness)
        all_signals = [signal for value in dimensions.values() for signal in value["signals"]]
        counts = Counter(signal["status"] for signal in all_signals)
        report = {
            "read_only": True,
            "summary": {
                "status": aggregate_status(all_signals),
                "signal_count": len(all_signals),
                "healthy_count": counts["healthy"],
                "attention_count": counts["attention"],
                "blocking_count": counts["blocked"],
                "unknown_count": counts["unknown"],
                "context_update_candidate_count": len(candidates),
                "opaque_health_score_used": False,
            },
            "dimensions": dimensions,
            "context_update_candidates": candidates,
            "evidence_sources": {
                "validator": {"schema": validator["schema"], "summary": validator["summary"]},
                "readiness": {"schema": readiness["schema"], "summary": readiness["summary"]},
                "missions": {key: value for key, value in missions.items() if key != "items"},
                "evolution_inbox": {key: value for key, value in inbox.items() if key != "items"},
                "mission_use": (
                    {
                        "schema": mission_use_evidence["schema"],
                        "id": mission_use_evidence["id"],
                        "summary": mission_use_evidence["summary"],
                        "validity": mission_use_evidence["validity"],
                    }
                    if mission_use_evidence
                    else None
                ),
            },
            "learning_boundary": {
                "signals_are_canonical_truth": False,
                "candidates_are_canonical_truth": False,
                "automatic_context_mutation": False,
                "required_route": "Discovery/Evidence -> Construction Candidate -> Draft -> Review -> Approval -> Promotion -> Canonical Validation",
            },
            "authority": {
                "engine_level": "L1_suggest",
                "may_observe": True,
                "may_recommend": True,
                "may_write_drafts": False,
                "may_approve": False,
                "may_promote": False,
                "human_review_required": True,
            },
            "constraints": {
                "documents_mutated": False,
                "external_connectors_used": False,
                "knowledge_engine_used": False,
                "graph_runtime_used": False,
                "agents_orchestrated": False,
                "second_construction_lifecycle_created": False,
            },
            "limitations": [
                "This first report is a current-state observation; trend comparison requires explicit prior report evidence.",
                "Access evidence does not prove consumption, use, usefulness, or causal contribution.",
                "Health signals are explainable observations and suggestions, not a numerical truth score.",
            ],
        }
        return build_report(root, report, generated_at=generated_at)
