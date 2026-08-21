from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.memory.continuity_report/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(root: Path, report: dict, generated_at: str | None = None) -> dict:
    report["schema"] = SCHEMA
    report["generated_at"] = generated_at or generated_timestamp()
    report["root"] = str(root.resolve())
    return report


def _preview(refs: list[str], limit: int = 3) -> str:
    visible = ", ".join(f"`{ref}`" for ref in refs[:limit])
    omitted = len(refs) - min(len(refs), limit)
    return f"{visible} (+{omitted} more in JSON)" if omitted else visible


def render_human(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Context OS Memory Continuity Report",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Report: `{report['id']}`",
        f"- Root: `{report['root']}`",
        f"- Active release: `{report['scope']['active_release']}`",
        f"- Active Mission: `{report['scope']['mission_id'] or '<none>'}`",
        f"- Read-only: {'yes' if report['read_only'] else 'no'}",
        f"- Source fingerprint: `{report['source_fingerprint']}`",
        "",
        "## What Is Remembered",
        "",
        "| Memory form | Entries |",
        "|---|---:|",
    ]
    for form, count in summary["memory_form_counts"].items():
        lines.append(f"| `{form}` | {count} |")

    lines.extend(
        [
            "",
            "## Current And Historical Continuity",
            f"- Current records: {summary['current_record_count']}",
            f"- Historical records: {summary['historical_record_count']}",
            f"- Explicit supersession records: {summary['supersession_count']}",
            f"- Unresolved continuity gaps: {summary['gap_count']}",
            "",
            "## Prior Art For This Mission",
        ]
    )
    if report["prior_art"]:
        for item in report["prior_art"]:
            lines.append(f"- `{item['mission_id']}` ({item['relevance']['score']} matched terms): {item['title']}")
            lines.append(f"  Why: {', '.join(item['relevance']['matched_terms'])}")
            lines.append(f"  Source: `{item['source']['path']}`")
    else:
        lines.append("- No prior Mission crossed the deterministic relevance threshold.")

    lines.extend(["", "## Decisions And Learning"])
    for form in ("decision", "learning"):
        entries = report["memory_forms"][form]
        lines.append(f"### {form.title()} Memory")
        if not entries:
            lines.append("- None observed.")
        for item in entries[:8]:
            lines.append(f"- `{item['mission_id']}`: {item['summary']}")
            lines.append(f"  Provenance: `{item['source']['path']}#{item['source']['section']}`")
        if len(entries) > 8:
            lines.append(f"- {len(entries) - 8} more in JSON.")

    lines.extend(["", "## Supersession"])
    if report["supersession"]:
        for item in report["supersession"]:
            lines.append(f"- `{item['id']}`: {item['summary']}")
            lines.append(f"  Source: `{item['source']['path']}`")
    else:
        lines.append("- No explicit supersession records were observed.")

    lines.extend(["", "## Pattern Candidates"])
    if report["pattern_candidates"]:
        for item in report["pattern_candidates"]:
            lines.append(f"- `{item['id']}` [{item['truth']['strategic_belief']}]: {item['title']}")
            lines.append(f"  Support: {len(item['evidence_refs'])} Mission learning records; {_preview(item['evidence_refs'])}")
    else:
        lines.append("- None met the explicit support threshold.")

    lines.extend(["", "## Continuity Gaps"])
    if report["continuity_gaps"]:
        for gap in report["continuity_gaps"]:
            lines.append(f"- `{gap['id']}` [{gap['status']}]: {gap['message']}")
    else:
        lines.append("- None observed.")

    lines.extend(
        [
            "",
            "## Governance Boundary",
            "- This report is a derived memory view, not a second SSOT.",
            "- Remembered does not mean canonical, current, approved, or useful.",
            "- Supersession is reported only when source evidence is explicit.",
            "- Pattern candidates remain derived suggestions and hypotheses until governed review.",
            "- No source, canonical context, retention state, or Mission artifact was mutated.",
            "",
            "## Retention And Forgetting",
            f"- Policy state: `{report['retention']['policy_state']}`",
            "- No automated deletion, compaction, archival, expiration, or forgetting is implemented.",
            "- Destructive retention behavior remains prohibited pending governance authority.",
            "",
            "## Theory Claims",
        ]
    )
    for claim in report["theory_claims"]:
        lines.append(f"- `{claim['status']}`: {claim['claim']}")
    return "\n".join(lines) + "\n"


def write_json_report(path: str | Path, report: dict) -> None:
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
