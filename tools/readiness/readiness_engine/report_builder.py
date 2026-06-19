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
    recommendations: list[dict] | None = None,
    generated_at: str | None = None,
) -> dict:
    level, level_name = level_for_score(score)
    blocking_issue_count = validator["summary"]["error"] + validator["summary"]["fatal"]
    level_index = int(level[1])
    recommendation_items = recommendations or []
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
            "recommendation_count": len(recommendation_items),
            "cap_reasons": cap_reasons,
        },
        "dimensions": dimensions,
        "inventory": inventory,
        "validator": validator,
        "recommendations": recommendation_items,
        "constraints": {
            "read_only": True,
            "external_connectors_used": False,
            "knowledge_engine_used": False,
            "graph_runtime_used": False,
            "documents_mutated": False,
        },
    }


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def first_gap(dimension: dict) -> str:
    if dimension["gaps"]:
        return dimension["gaps"][0]
    return "No gaps detected."


def render_human(report: dict) -> str:
    summary = report["summary"]
    validator_summary = report["validator"]["summary"]
    lines = [
        "# Context OS Readiness Report",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Root: `{report['root']}`",
        f"- Score: {summary['score']}/100 ({summary['level']} {summary['level_name']})",
        f"- Uncapped score: {summary['uncapped_score']}/100",
        f"- Can bootstrap: {yes_no(summary['can_bootstrap'])}",
        f"- Can construct: {yes_no(summary['can_construct'])}",
        f"- Recommendations: {summary['recommendation_count']}",
    ]

    lines.extend(["", "## Score Caps"])
    if summary["cap_reasons"]:
        for reason in summary["cap_reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- No score caps applied.")

    lines.extend(
        [
            "",
            "## Dimension Scores",
            "",
            "| Dimension | Score | Status | Key gap |",
            "|---|---:|---|---|",
        ]
    )
    for dimension_id, dimension in report["dimensions"].items():
        lines.append(
            f"| `{dimension_id}` | {dimension['score']} | {dimension['status']} | {first_gap(dimension)} |"
        )

    lines.extend(["", "## Key Gaps"])
    gaps = []
    for dimension_id, dimension in report["dimensions"].items():
        for gap in dimension["gaps"][:2]:
            gaps.append(f"- `{dimension_id}`: {gap}")
    if gaps:
        lines.extend(gaps[:12])
    else:
        lines.append("- No dimension gaps detected.")

    lines.extend(["", "## Next Recommended Actions"])
    recommendations = report["recommendations"]
    if recommendations:
        for item in recommendations[:10]:
            lines.append(f"- [{item['priority']}] `{item['id']}`: {item['title']}")
            lines.append(f"  Action: {item['suggested_action']}")
    else:
        lines.append("- No recommendations generated.")

    lines.extend(
        [
            "",
            "## Inventory Summary",
            f"- Artifacts: {report['inventory']['summary']['artifact_count']}",
            f"- Taxonomy classes: {report['inventory']['summary']['taxonomy_class_count']}",
            f"- Runtime artifacts: {report['inventory']['summary']['runtime_artifact_count']}",
            f"- Governance artifacts: {report['inventory']['summary']['governance_artifact_count']}",
            f"- Roadmap artifacts: {report['inventory']['summary']['roadmap_artifact_count']}",
            "",
            "## Validator Summary",
            f"- Mode: `{report['validator']['mode']}`",
            f"- Rules run: {validator_summary['rules_run']}",
            f"- Findings: info={validator_summary['info']}, warn={validator_summary['warn']}, "
            f"error={validator_summary['error']}, fatal={validator_summary['fatal']}",
            f"- Exit code: {validator_summary['exit_code']}",
        ]
    )
    return "\n".join(lines) + "\n"
