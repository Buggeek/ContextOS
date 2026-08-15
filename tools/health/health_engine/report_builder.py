from __future__ import annotations

import datetime as _dt
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

    for dimension in report["dimensions"].values():
        lines.extend(["", f"## {dimension['title']}"])
        for signal in dimension["signals"]:
            lines.append(f"- `{signal['id']}` [{signal['status']}]: {signal['message']}")
            if signal["evidence_refs"]:
                lines.append(f"  Evidence: {', '.join(f'`{ref}`' for ref in signal['evidence_refs'][:8])}")

    lines.extend(["", "## Context Update Candidates"])
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
            "",
            "## Evidence Sources",
            f"- Validator: `{report['evidence_sources']['validator']['schema']}`",
            f"- Readiness: `{report['evidence_sources']['readiness']['schema']}`",
            f"- Closed Mission artifacts observed: {report['evidence_sources']['missions']['closed_count']}",
            f"- Evolution Inbox items observed: {report['evidence_sources']['evolution_inbox']['item_count']}",
        ]
    )
    return "\n".join(lines) + "\n"
