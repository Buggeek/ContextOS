from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.activation.package/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def build_report(
    root: Path,
    package: dict,
    generated_at: str | None = None,
) -> dict:
    package["schema"] = SCHEMA
    package["generated_at"] = generated_at or generated_timestamp()
    package["root"] = str(root.resolve())
    return package


def render_human(report: dict) -> str:
    summary = report["summary"]
    validator = report["validator"]
    lines = [
        "# Context OS Activation Package",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Package: `{report['id']}`",
        f"- Root: `{report['root']}`",
        f"- Consumer: `{report['consumer']['type']}`",
        f"- Goal: {report['goal']['statement']}",
        f"- Mission: `{report['goal']['mission_id'] or '<none>'}`",
        f"- Read-only: {yes_no(report['read_only'])}",
        f"- Activation allowed: {yes_no(summary['activation_allowed'])}",
        f"- Included artifacts: {summary['included_artifact_count']}",
        f"- Excluded artifacts: {summary['excluded_artifact_count']}",
        f"- Context gaps: {summary['context_gap_count']}",
        f"- Source fingerprint: `{report['source_fingerprint']}`",
        "",
        "## Included Context",
    ]
    for item in report["working_context"]["items"]:
        lines.append(f"- `{item['path']}`")
        lines.append(f"  Role: {item['activation_role']}")
        lines.append(f"  Lifecycle: {item['lifecycle_state']}")
        lines.append(f"  Hash: `{item['source_hash']}`")
        if item.get("title"):
            lines.append(f"  Title: {item['title']}")
    if not report["working_context"]["items"]:
        lines.append("- None.")

    lines.extend(["", "## Gaps"])
    if report["context_gaps"]:
        for gap in report["context_gaps"]:
            lines.append(f"- `{gap['id']}`: {gap['message']}")
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Validator Gate",
            f"- Findings: info={validator['summary']['info']}, warn={validator['summary']['warn']}, "
            f"error={validator['summary']['error']}, fatal={validator['summary']['fatal']}",
            f"- Exit code: {validator['summary']['exit_code']}",
            "",
            "## Boundary",
            "- This package is derived working context, not SSOT.",
            "- Canonical source artifacts remain authoritative.",
            "- Included excerpts are invalidated when source hashes or validator gates change.",
            "- The package performs no mutation, activation side effect, Knowledge Engine reasoning, graph runtime, or agent orchestration.",
            "",
            "## Invalidation",
        ]
    )
    for condition in report["invalidation"]["conditions"]:
        lines.append(f"- {condition}")
    return "\n".join(lines) + "\n"


def write_json_report(path: str | Path, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
