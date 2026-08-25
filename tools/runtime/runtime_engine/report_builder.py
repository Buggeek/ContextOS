from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.runtime.integration_benchmark/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(root: Path, report: dict, generated_at: str | None = None) -> dict:
    report["schema"] = SCHEMA
    report["generated_at"] = generated_at or generated_timestamp()
    report["root"] = str(root.resolve())
    return report


def write_json_report(path: str | Path, report: dict) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_human(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Context OS Organizational Context Runtime Benchmark",
        "",
        f"- Benchmark: `{report['id']}`",
        f"- Mission: `{report['mission']['id']}`",
        f"- Goal: {report['mission']['goal']}",
        f"- Status: `{summary['status']}`",
        f"- Checks: {summary['passed_check_count']}/{summary['check_count']} passed",
        f"- Release blockers: {summary['release_blocker_count']}",
        f"- Target mutation: {'none' if report['read_only'] else 'detected'}",
        "",
        "## Integrated Journey",
    ]
    for stage in report["journey"]:
        lines.append(
            f"- `{stage['stage']}` -> `{stage['schema']}` "
            f"({stage['status']})"
        )
    lines.extend(["", "## Integration Checks"])
    for check in report["checks"]:
        marker = "PASS" if check["passed"] else "GAP"
        lines.append(f"- [{marker}] `{check['id']}`: {check['message']}")
    lines.extend(["", "## Governed Change Evidence"])
    for item in report["governed_change_evidence"]:
        lines.append(
            f"- `{item['release']}` `{item['path']}` "
            f"[{item['verification_state']}]"
        )
    lines.extend(
        [
            "",
            "## Runtime Boundaries",
            "- Canonical context remains distinct from activated working context.",
            "- Selected context remains distinct from used or useful context.",
            "- Remembered context remains distinct from current authority.",
            "- Reasoning remains advisory and cannot decide or execute.",
            "- Benchmark success grants no mutation or release authority.",
            "",
            "## Intentional Deferrals",
        ]
    )
    lines.extend(f"- {item}" for item in report["intentional_deferrals"])
    return "\n".join(lines) + "\n"
