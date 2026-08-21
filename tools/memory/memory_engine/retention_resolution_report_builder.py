from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.memory.retention_resolution/1"
CHECK_SCHEMA = "contextos.memory.retention_resolution_check/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(root: Path, report: dict, generated_at: str | None = None) -> dict:
    report["schema"] = SCHEMA
    report["generated_at"] = generated_at or generated_timestamp()
    report["root"] = str(root.resolve())
    return report


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(report: dict) -> str:
    if report.get("schema") == CHECK_SCHEMA:
        return render_check_human(report)

    memory = report["memory"]
    lines = [
        "# Context OS Memory Retention Resolution",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Resolution: `{report['id']}`",
        f"- Memory: `{memory['display_id']}`",
        f"- Memory form: `{memory.get('form') or '<restricted>'}`",
        f"- Memory owner: `{memory.get('owner') or '<restricted>'}`",
        f"- Sensitivity: `{memory.get('sensitivity') or '<restricted>'}`",
        f"- Retention state: `{memory.get('retention_state') or '<restricted>'}`",
        f"- Affected parties: {', '.join(memory.get('affected_parties', [])) or 'unknown/restricted'}",
        f"- Consumer: `{report['request']['consumer']}`",
        f"- Evaluation time: `{report['request']['evaluation_time']}`",
        f"- Status: `{report['summary']['status']}`",
        f"- Read-only: {_yes_no(report['read_only'])}",
        f"- Mutation occurred: {_yes_no(report['mutation']['occurred'])}",
        "",
        "## Operation Results",
        "",
        "| Operation | Outcome | Why |",
        "|---|---|---|",
    ]
    for operation, result in report["operation_results"].items():
        reasons = ", ".join(result["reason_codes"]) or "no material rule"
        lines.append(f"| `{operation}` | `{result['outcome']}` | {reasons} |")

    lines.extend(["", "## Policies Evaluated"])
    if report["policy_evaluation"]["applied"]:
        for policy in report["policy_evaluation"]["applied"]:
            lines.append(
                f"- `{policy['display_id']}` version `{policy['version']}`: "
                f"{', '.join(policy['reason_codes'])}"
            )
            if policy.get("scope"):
                lines.append(f"  Scope: `{json.dumps(policy['scope'], sort_keys=True)}`")
    else:
        lines.append("- No policy was proven applicable.")
    for policy in report["policy_evaluation"]["not_applied"]:
        lines.append(f"- Not applied `{policy['display_id']}`: {policy['reason']}")

    lines.extend(["", "## Preservation And Holds"])
    if report["preservation_requirements"]:
        for requirement in report["preservation_requirements"]:
            lines.append(f"- `{requirement['id']}` from `{requirement['policy_id']}`")
    else:
        lines.append("- No explicit preservation requirement was resolved.")
    if report["holds"]:
        for hold in report["holds"]:
            lines.append(f"- Active hold `{hold['display_id']}` requires human authority.")
    else:
        lines.append("- No active hold was supplied.")

    lines.extend(["", "## Conflicts And Unknowns"])
    if report["conflicts"]:
        for conflict in report["conflicts"]:
            lines.append(f"- `{conflict['id']}`: {conflict['message']}")
    else:
        lines.append("- No explicit policy conflict was observed.")
    if report["unresolved_requirements"]:
        for requirement in report["unresolved_requirements"]:
            lines.append(f"- `{requirement['id']}`: {requirement['message']}")
    else:
        lines.append("- No unresolved requirement was observed.")

    lines.extend(["", "## Authority Boundary"])
    lines.append("- The resolver identifies required authority but grants none.")
    lines.append("- Legal/compliance interpretation remains a human decision.")
    lines.append("- Retention Resolution cannot approve or execute a transition.")
    for operation, authority in report["authority"]["by_operation"].items():
        roles = ", ".join(authority["required_roles"]) or "none declared"
        lines.append(f"- `{operation}` requires: {roles}; satisfied now: {_yes_no(authority['roles_present'])}.")

    lines.extend(["", "## Evidence And Freshness"])
    lines.append(f"- Input fingerprint: `{report['bindings']['input_fingerprint']}`")
    lines.append(f"- Source fingerprint: `{report['bindings']['source_fingerprint']}`")
    lines.append(f"- Evidence references visible: {len(report['evidence']['refs'])}")
    lines.append(f"- Bound source checks: {len(report['bindings']['source_checks'])}")
    if report["evidence"]["metadata_redacted"]:
        lines.append("- Restricted metadata was withheld from this report.")
    for condition in report["invalidation"]["conditions"]:
        lines.append(f"- {condition}")

    lines.extend(["", "## Interpretation Limits"])
    for limitation in report["limitations"]:
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"


def render_check_human(report: dict) -> str:
    lines = [
        "# Context OS Memory Retention Resolution Check",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Resolution: `{report['resolution']['id']}`",
        f"- Read-only: {_yes_no(report['read_only'])}",
        f"- Valid: {_yes_no(report['result']['valid'])}",
        f"- Invalidated: {_yes_no(report['result']['invalidated'])}",
        "",
        "## Checks",
    ]
    for name, value in report["checks"].items():
        lines.append(f"- `{name}`: {_yes_no(value)}")
    lines.extend(["", "## Failed Checks"])
    if report["result"]["failed_checks"]:
        lines.extend(f"- `{failure}`" for failure in report["result"]["failed_checks"])
    else:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def write_json_report(path: str | Path, report: dict) -> None:
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
