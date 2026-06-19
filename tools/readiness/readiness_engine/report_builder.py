from __future__ import annotations

import datetime as _dt
from pathlib import Path


SCHEMA = "contextos.readiness.report/1"

LEVELS = (
    ("R0", "Unassessable", 0, 19),
    ("R1", "Unstructured", 20, 39),
    ("R2", "Inventory Ready", 40, 59),
    ("R3", "Bootstrap Ready", 60, 74),
    ("R4", "Construction Ready", 75, 89),
    ("R5", "Operational Context Ready", 90, 100),
)


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def level_for_score(score: int) -> tuple[str, str]:
    for level, name, minimum, maximum in LEVELS:
        if minimum <= score <= maximum:
            return level, name
    if score < 0:
        return "R0", "Unassessable"
    return "R5", "Operational Context Ready"


def status_for_score(score: int) -> str:
    if score >= 90:
        return "excellent"
    if score >= 75:
        return "good"
    if score >= 50:
        return "partial"
    if score >= 20:
        return "weak"
    return "blocked"


def build_dimension(
    dimension_id: str,
    score: int,
    weight: int,
    signals: list[str],
    gaps: list[str],
    evidence_refs: list[str],
) -> dict:
    bounded_score = max(0, min(100, round(score)))
    return {
        "id": dimension_id,
        "score": bounded_score,
        "weight": weight,
        "status": status_for_score(bounded_score),
        "signals": signals,
        "gaps": gaps,
        "evidence_refs": sorted(dict.fromkeys(evidence_refs)),
    }


def build_report(
    root: Path,
    dimensions: dict,
    inventory: dict,
    validator: dict,
    score: int,
    uncapped_score: int,
    cap_reasons: list[str],
    generated_at: str | None = None,
) -> dict:
    level, level_name = level_for_score(score)
    blocking_issue_count = validator["summary"]["error"] + validator["summary"]["fatal"]
    level_index = int(level[1])
    return {
        "schema": SCHEMA,
        "generated_at": generated_at or generated_timestamp(),
        "root": str(root.resolve()),
        "mode": "repository",
        "summary": {
            "score": score,
            "uncapped_score": uncapped_score,
            "level": level,
            "level_name": level_name,
            "can_bootstrap": level_index >= 3 and blocking_issue_count == 0,
            "can_construct": level_index >= 4 and blocking_issue_count == 0,
            "blocking_issue_count": blocking_issue_count,
            "recommendation_count": 0,
            "cap_reasons": cap_reasons,
        },
        "dimensions": dimensions,
        "inventory": inventory,
        "validator": validator,
        "recommendations": [],
        "constraints": {
            "read_only": True,
            "external_connectors_used": False,
            "knowledge_engine_used": False,
            "graph_runtime_used": False,
            "documents_mutated": False,
        },
    }
