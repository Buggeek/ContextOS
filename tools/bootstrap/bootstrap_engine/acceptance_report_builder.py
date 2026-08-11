from __future__ import annotations

import json
from pathlib import Path


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(decision: dict) -> str:
    proposal = decision["proposal"]
    authority = decision["authority"]
    accepted = decision["decision"]
    lines = [
        "# Context OS Bootstrap Accepted Decision",
        "",
        f"- Schema: `{decision['schema']}`",
        f"- Accepted decision ID: `{decision['id']}`",
        f"- Status: {accepted['status']}",
        f"- Decision: {accepted['decision_kind']}",
        f"- Proposal ID: `{proposal['id']}`",
        f"- Proposal identity hash: `{proposal['identity_hash']}`",
        f"- Source plan hash: `{proposal['source_plan_hash']}`",
        f"- Repository fingerprint hash: `{proposal['repository_fingerprint_hash']}`",
        f"- Accepted by: {accepted['accepted_by']}",
        f"- Accepted role: {accepted['accepted_role']}",
        f"- Read-only: {yes_no(decision['read_only'])}",
        f"- Approved: {yes_no(accepted['approved'])}",
        f"- Apply authorized: {yes_no(accepted['apply_authorized'])}",
        f"- Repository mutation authorized: {yes_no(accepted['repository_mutation_authorized'])}",
        "",
        "## Authority",
        f"- Mode: {authority['mode']}",
        f"- Authority level: {authority['authority_level']}",
        f"- Required roles: {', '.join(authority['required_roles'])}",
        f"- Role satisfied: {yes_no(authority['role_satisfied'])}",
        "",
        "## Preserved Action Set",
        f"- Total actions: {proposal['action_summary']['count']}",
        f"- Automatic: {proposal['action_summary']['by_class'].get('automatic', 0)}",
        f"- Approval required: {proposal['action_summary']['by_class'].get('approval_required', 0)}",
        f"- Manual: {proposal['action_summary']['by_class'].get('manual', 0)}",
        f"- Prohibited: {proposal['action_summary']['by_class'].get('prohibited', 0)}",
        "",
        "## Acceptance Checks",
    ]
    for check in decision["validation"]["checks"]:
        lines.append(f"- `{check['id']}`: {'passed' if check['passed'] else 'failed'}")
    lines.extend(
        [
            "",
            "## Decision Record",
            f"- Schema: `{accepted['decision_record']['schema']}`",
            f"- ID: `{accepted['decision_record']['id']}`",
            f"- Outcome: {accepted['decision_record']['outcome']}",
            f"- Rationale: {accepted['decision_record']['rationale']}",
            "",
            "## Read-Only Guarantee",
            "- This accepted decision did not modify the target repository.",
            "- This accepted decision preserves the exact proposal identity for future apply.",
            "- This accepted decision does not authorize apply by itself.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json_report(path: str, decision: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(decision, indent=2, sort_keys=True) + "\n", encoding="utf-8")
