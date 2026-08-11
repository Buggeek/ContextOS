from __future__ import annotations

import json
from pathlib import Path


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(report: dict) -> str:
    eligibility = report["eligibility"]
    proposal = report["proposal"]
    authority = report["authority"]
    mutation = report["frozen_mutation_set"]
    validator = report["validation"]["validator"]["summary"]
    lines = [
        "# Context OS Bootstrap Apply Preflight",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Preflight ID: `{report['id']}`",
        f"- Eligible for apply: {yes_no(eligibility['eligible_for_apply'])}",
        f"- Apply authorized: {yes_no(eligibility['apply_authorized'])}",
        f"- Repository mutation authorized: {yes_no(eligibility['repository_mutation_authorized'])}",
        f"- Read-only: {yes_no(report['read_only'])}",
        f"- Proposal ID: `{proposal['id']}`",
        f"- Proposal identity hash: `{proposal['identity_hash']}`",
        f"- Source plan hash: `{proposal['source_plan_hash']}`",
        f"- Repository fingerprint hash: `{proposal['repository_fingerprint_hash']}`",
        "",
        "## Authority",
        f"- Accepted by: {authority['accepted_by']}",
        f"- Accepted role: {authority['accepted_role']}",
        f"- Authority level: {authority['authority_level']}",
        f"- Role satisfied: {yes_no(authority['role_satisfied'])}",
        f"- Human apply confirmation required: {yes_no(authority['human_apply_confirmation_required'])}",
        "",
        "## Frozen Mutation Set",
        f"- Mutation set hash: `{mutation['hash']}`",
        f"- Executable actions: {mutation['count']}",
    ]
    if mutation["actions"]:
        for action in mutation["actions"]:
            lines.append(f"- `{action['id']}` -> `{action['target_path']}` ({action['type']}, rollback: {action['rollback_strategy']})")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Preflight Checks",
        ]
    )
    for check in report["validation"]["checks"]:
        lines.append(f"- `{check['id']}`: {'passed' if check['passed'] else 'failed'}")
    lines.extend(
        [
            "",
            "## Validator Gate",
            f"- Errors: {validator['error']}",
            f"- Fatals: {validator['fatal']}",
            f"- Exit code: {validator['exit_code']}",
            "",
            "## Read-Only Guarantee",
            "- This preflight did not modify the target repository.",
            "- This preflight freezes the exact mutation set that a future apply may request.",
            "- This preflight does not authorize or perform apply.",
        ]
    )
    if eligibility["failed_checks"]:
        lines.extend(["", "## Failed Checks"])
        for failed in eligibility["failed_checks"]:
            lines.append(f"- `{failed}`")
    return "\n".join(lines) + "\n"


def write_json_report(path: str, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
