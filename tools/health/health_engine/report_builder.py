from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.health.report/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(root: Path, report: dict, generated_at: str | None = None) -> dict:
    report["schema"] = SCHEMA
    report["generated_at"] = generated_at or generated_timestamp()
    report["root"] = str(root.resolve())
    return report


def render_human(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Context OS Health Report",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Root: `{report['root']}`",
        f"- Overall status: `{summary['status']}`",
        f"- Read-only: {'yes' if report['read_only'] else 'no'}",
        f"- Signals: {summary['signal_count']}",
        f"- Attention signals: {summary['attention_count']}",
        f"- Blocking signals: {summary['blocking_count']}",
        f"- Unknown signals: {summary['unknown_count']}",
        f"- Context update candidates: {summary['context_update_candidate_count']}",
        "",
        "## Health Dimensions",
        "",
        "| Dimension | Status | Signals | Attention | Blocked | Unknown |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for dimension in report["dimensions"].values():
        counts = dimension["counts"]
        lines.append(
            f"| `{dimension['id']}` | {dimension['status']} | {counts['total']} | "
            f"{counts['attention']} | {counts['blocked']} | {counts['unknown']} |"
        )

    priority = {"blocked": 0, "attention": 1, "unknown": 2}
    actionable = [
        signal
        for value in report["dimensions"].values()
        for signal in value["signals"]
        if signal["status"] in priority
    ]
    actionable.sort(key=lambda signal: (priority[signal["status"]], signal["dimension"], signal["kind"]))
    lines.extend(["", "## What Needs Attention"])
    if actionable:
        for signal in actionable:
            lines.append(
                f"- `{signal['status']}` / `{signal['dimension']}` / `{signal['belief_state']}`: {signal['message']}"
            )
            if signal["evidence_refs"]:
                lines.append(f"  Evidence: {', '.join(f'`{ref}`' for ref in signal['evidence_refs'][:8])}")
    else:
        lines.append("- No blocking, attention, or unknown signals were observed.")

    for dimension in report["dimensions"].values():
        lines.extend(["", f"## {dimension['title']}"])
        for signal in dimension["signals"]:
            lines.append(
                f"- `{signal['id']}` [{signal['status']}; {signal['belief_state']}]: {signal['message']}"
            )
            if signal["evidence_refs"]:
                lines.append(f"  Evidence: {', '.join(f'`{ref}`' for ref in signal['evidence_refs'][:8])}")

    lines.extend(["", "## Context Update Candidates", "", "What to consider next:"])
    if report["context_update_candidates"]:
        for candidate in report["context_update_candidates"]:
            lines.append(f"- `{candidate['id']}` [{candidate['priority']}]: {candidate['title']}")
            lines.append(f"  Why: {candidate['rationale']}")
            lines.append(f"  Next: {candidate['suggested_action']}")
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Learning Boundary",
            "- Health signals and learning candidates are observations and suggestions, not organizational truth.",
            "- No candidate may modify canonical context directly.",
            "- Any accepted context update must enter the existing Discovery/Construction draft, review, approval, and promotion lifecycle.",
            "- This report made no automatic changes.",
            "",
            "## Observability Limits",
            *[f"- {limitation}" for limitation in report["limitations"]],
            "",
            "## Evidence Sources",
            f"- Validator: `{report['evidence_sources']['validator']['schema']}`",
            f"- Readiness: `{report['evidence_sources']['readiness']['schema']}`",
            f"- Closed Mission artifacts observed: {report['evidence_sources']['missions']['closed_count']}",
            f"- Evolution Inbox items observed: {report['evidence_sources']['evolution_inbox']['item_count']}",
        ]
    )
    mission_use = report["evidence_sources"].get("mission_use")
    lines.append(
        f"- Mission-use evidence: `{mission_use['id']}`"
        if mission_use
        else "- Mission-use evidence: not supplied; per-source usefulness remains limited."
    )
    return "\n".join(lines) + "\n"


def write_json_report(path: str | Path, report: dict) -> None:
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
