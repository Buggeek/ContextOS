from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.activation.package/1"
CHECK_SCHEMA = "contextos.activation.package_check/1"
HANDOFF_SCHEMA = "contextos.activation.handoff/1"
HANDOFF_CHECK_SCHEMA = "contextos.activation.handoff_check/1"


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
    if report.get("schema") == HANDOFF_CHECK_SCHEMA:
        return render_handoff_check_human(report)
    if report.get("schema") == HANDOFF_SCHEMA:
        return render_handoff_human(report)
    if report.get("schema") == CHECK_SCHEMA:
        return render_check_human(report)
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


def render_check_human(report: dict) -> str:
    validator = report["validator"]["summary"]
    lines = [
        "# Context OS Activation Package Check",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Package: `{report['package']['id']}`",
        f"- Root: `{report['root']}`",
        f"- Read-only: {yes_no(report['read_only'])}",
        f"- Valid: {yes_no(report['result']['valid'])}",
        f"- Invalidated: {yes_no(report['result']['invalidated'])}",
        f"- Identity valid: {yes_no(report['checks']['identity_valid'])}",
        f"- Source hashes match: {yes_no(report['checks']['source_hashes_match'])}",
        f"- Validator gate ok: {yes_no(report['checks']['validator_gate_ok'])}",
        f"- Validator findings: info={validator['info']}, warn={validator['warn']}, error={validator['error']}, fatal={validator['fatal']}",
        "",
        "## Source Checks",
    ]
    for check in report["checks"]["source_checks"]:
        lines.append(f"- `{check['path']}` match={yes_no(check['matches'])}")
        lines.append(f"  Expected: `{check['expected_hash']}`")
        lines.append(f"  Current: `{check['current_hash']}`")
    if not report["checks"]["source_checks"]:
        lines.append("- None.")
    lines.extend(["", "## Failed Checks"])
    if report["result"]["failed_checks"]:
        for check in report["result"]["failed_checks"]:
            lines.append(f"- `{check}`")
    else:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def render_handoff_human(report: dict) -> str:
    package = report["source_package"]
    check = report["package_check"]
    mission = report["mission"]
    metrics = report["metrics"]
    lines = [
        "# Context OS Activation Handoff",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Handoff: `{report['id']}`",
        f"- Package: `{package['id']}`",
        f"- Package hash: `{package['identity_hash']}`",
        f"- Root: `{report['root']}`",
        f"- Consumer: `{report['consumer']['type']}`",
        f"- Goal: {mission['goal']}",
        f"- Mission: `{mission['mission_id'] or '<none>'}`",
        f"- Read-only: {yes_no(report['read_only'])}",
        f"- Handoff ready: {yes_no(report['result']['handoff_ready'])}",
        f"- Package valid now: {yes_no(check['result']['valid'])}",
        f"- Selected sources: {metrics['selected_source_count']}",
        f"- Excluded sources: {metrics['excluded_source_count']}",
        f"- Known gaps: {metrics['gap_count']}",
        "",
        "## Working Instruction",
        report["working_instruction"],
        "",
        "## Governing Context",
    ]
    for source in report["selected_context"]:
        lines.append(f"- `{source['path']}`")
        lines.append(f"  Role: {source['activation_role']}")
        lines.append(f"  Authority: {source['authority_tier']}")
        lines.append(f"  Lifecycle: {source['lifecycle_state']}")
        lines.append(f"  Hash: `{source['source_hash']}`")
        if source.get("title"):
            lines.append(f"  Title: {source['title']}")
    if not report["selected_context"]:
        lines.append("- None.")

    lines.extend(["", "## Gaps And Limits"])
    if report["known_gaps"]:
        for gap in report["known_gaps"]:
            lines.append(f"- `{gap['id']}` ({gap['severity']}): {gap['message']}")
    else:
        lines.append("- None.")
    if report["exclusions"]["items"]:
        lines.append("")
        lines.append("## Exclusions")
        for item in report["exclusions"]["items"]:
            lines.append(f"- `{item['path']}`: {item['reason']}")
        if report["exclusions"]["truncated"]:
            lines.append(f"- Additional exclusions omitted: {report['exclusions']['omitted_count']}")

    lines.extend(
        [
            "",
            "## Authority Boundaries",
        ]
    )
    for permission in report["authority"]["allowed_permissions"]:
        lines.append(f"- Allowed: `{permission}`")
    for permission in report["authority"]["prohibited_permissions"]:
        lines.append(f"- Prohibited: `{permission}`")

    lines.extend(["", "## Invalidation"])
    for condition in report["invalidation"]["conditions"]:
        lines.append(f"- {condition}")
    if report["result"]["failed_checks"]:
        lines.append("")
        lines.append("## Failed Checks")
        for failed in report["result"]["failed_checks"]:
            lines.append(f"- `{failed}`")

    lines.extend(
        [
            "",
            "## Boundary",
            "- This handoff is derived from an Activation Package and is not SSOT.",
            "- Exact canonical source files remain authoritative.",
            "- Revalidate the package before acting when any invalidation condition may have changed.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_handoff_check_human(report: dict) -> str:
    validator = report["validator"]["summary"]
    lines = [
        "# Context OS Activation Handoff Check",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Handoff: `{report['handoff']['id']}`",
        f"- Package: `{report['source_package']['id']}`",
        f"- Root: `{report['root']}`",
        f"- Read-only: {yes_no(report['read_only'])}",
        f"- Valid: {yes_no(report['result']['valid'])}",
        f"- Invalidated: {yes_no(report['result']['invalidated'])}",
        f"- Handoff identity valid: {yes_no(report['checks']['handoff_identity_valid'])}",
        f"- Source hashes match: {yes_no(report['checks']['source_hashes_match'])}",
        f"- Validator gate ok: {yes_no(report['checks']['validator_gate_ok'])}",
        f"- Package ref available: {yes_no(report['checks']['package_ref_available'])}",
        f"- Package ref valid: {yes_no(report['checks']['package_ref_valid'])}",
        f"- Validator findings: info={validator['info']}, warn={validator['warn']}, error={validator['error']}, fatal={validator['fatal']}",
        "",
        "## Source Checks",
    ]
    for check in report["checks"]["source_checks"]:
        lines.append(f"- `{check['path']}` match={yes_no(check['matches'])}")
        lines.append(f"  Expected: `{check['expected_hash']}`")
        lines.append(f"  Current: `{check['current_hash']}`")
    if not report["checks"]["source_checks"]:
        lines.append("- None.")

    lines.extend(["", "## Failed Checks"])
    if report["result"]["failed_checks"]:
        for check in report["result"]["failed_checks"]:
            lines.append(f"- `{check}`")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Boundary",
            "- This check validates a handoff as derived working context.",
            "- It does not regenerate context selection or create a second SSOT.",
            "- It performs no repository mutation.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json_report(path: str | Path, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
