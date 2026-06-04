from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

from engine.findings import Finding, SEVERITIES


SCHEMA = "contextos.validator.report/1"


def exit_code_for(mode: str, findings: list[Finding]) -> int:
    if any(f.severity == "fatal" for f in findings):
        return 8
    if any(f.severity == "error" for f in findings):
        return 7
    return 0


def summary_for(findings: list[Finding], rules_run: int, exit_code: int) -> dict:
    counts = {severity: 0 for severity in SEVERITIES}
    for finding in findings:
        counts[finding.severity] += 1
    return {
        "rules_run": rules_run,
        "info": counts["info"],
        "warn": counts["warn"],
        "error": counts["error"],
        "fatal": counts["fatal"],
        "exit_code": exit_code,
    }


def build_report(ctx, findings: list[Finding], rules_run: int, exit_code: int) -> dict:
    generated_at = _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema": SCHEMA,
        "generated_at": generated_at,
        "mode": ctx.mode,
        "root": str(ctx.root),
        "summary": summary_for(findings, rules_run, exit_code),
        "findings": [finding.as_dict() for finding in findings],
    }


def render_human(report: dict, machine_report_path: str | None = None) -> str:
    summary = report["summary"]
    lines = [
        "# Context OS Validator Report",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Mode: `{report['mode']}`",
        f"- Root: `{report['root']}`",
        f"- Rules run: {summary['rules_run']}",
        f"- Findings: info={summary['info']}, warn={summary['warn']}, error={summary['error']}, fatal={summary['fatal']}",
        f"- Exit code: {summary['exit_code']}",
    ]
    if machine_report_path:
        lines.append(f"- Machine report: `{machine_report_path}`")

    findings = report["findings"]
    lines.extend(["", "## Top Findings"])
    if not findings:
        lines.append("")
        lines.append("No findings.")
    else:
        severity_order = {"fatal": 0, "error": 1, "warn": 2, "info": 3}
        top = sorted(findings, key=lambda f: (severity_order[f["severity"]], f["rule"], f["path"] or "", f["line"] or 0))[:10]
        for finding in top:
            location = finding["path"] or "<repo>"
            if finding["line"]:
                location = f"{location}:{finding['line']}"
            lines.append("")
            lines.append(f"- [{finding['severity']}] `{finding['rule']}` at `{location}`")
            lines.append(f"  {finding['message']}")
            if finding.get("suggested_fix"):
                lines.append(f"  Suggested fix: {finding['suggested_fix']}")
    return "\n".join(lines) + "\n"


def write_json_report(path: str, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
