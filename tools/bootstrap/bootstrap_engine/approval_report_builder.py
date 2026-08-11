from __future__ import annotations

import json
from pathlib import Path


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(record: dict) -> str:
    proposal = record["proposal"]
    decision = record["decision"]
    authority = record["authority"]
    lines = [
        "# Context OS Bootstrap Approval Record Draft",
        "",
        f"- Schema: `{record['schema']}`",
        f"- Approval record ID: `{record['id']}`",
        f"- Status: {decision['status']}",
        f"- Decision: {decision['decision_kind']}",
        f"- Proposal ID: `{proposal['id']}`",
        f"- Proposal identity hash: `{proposal['identity_hash']}`",
        f"- Source plan hash: `{proposal['source_plan_hash']}`",
        f"- Read-only: {yes_no(record['read_only'])}",
        f"- Approval implied: {yes_no(record['constraints']['approval_implied'])}",
        f"- Apply authorized: {yes_no(record['constraints']['apply_authorized'])}",
        f"- Human authority required: {yes_no(record['constraints']['human_authority_required'])}",
        "",
        "## Authority Required",
        f"- Mode: {authority['mode']}",
        f"- Authority level: {authority['authority_level']}",
        f"- Required roles: {', '.join(authority['required_roles'])}",
        f"- Approver candidates: {', '.join(authority['approver_candidates']) or '<none>'}",
        "",
        "## Drift Status",
        f"- Invalidated: {yes_no(record['drift']['invalidated'])}",
        f"- Approved identity hash: `{record['drift']['approved_identity_hash']}`",
        f"- Current identity hash: `{record['drift']['current_identity_hash']}`",
        "",
        "## Blockers",
    ]
    if record["blockers"]:
        for blocker in record["blockers"]:
            lines.append(f"- `{blocker['id']}` ({blocker['severity']}): {blocker['message']}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Decision Record Draft",
            f"- Schema: `{decision['decision_record_draft']['schema']}`",
            f"- Title: {decision['decision_record_draft']['title']}",
            f"- Decided by: {', '.join(decision['decision_record_draft']['decided_by']) or '<pending>'}",
            "",
            "## Read-Only Guarantee",
            "- This approval record draft did not modify the target repository.",
            "- This approval record draft does not approve the proposal.",
            "- Future apply still requires human authority and an accepted decision record.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json_report(path: str, record: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
