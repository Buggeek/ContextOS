from __future__ import annotations

import json
from pathlib import Path


def count_class(actions: list[dict], classification: str) -> int:
    return sum(1 for action in actions if action["class"] == classification)


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(proposal: dict) -> str:
    authority = proposal["authority"]
    repo = proposal["repository_state"]
    lines = [
        "# Context OS Bootstrap Proposal",
        "",
        f"- Schema: `{proposal['schema']}`",
        f"- Proposal ID: `{proposal['id']}`",
        f"- Identity hash: `{proposal['identity_hash']}`",
        f"- Status: {proposal['status']}",
        f"- Root: `{proposal['root']}`",
        f"- Read-only: {yes_no(proposal['read_only'])}",
        f"- Approval implied: {yes_no(proposal['constraints']['approval_implied'])}",
        f"- Apply authorized: {yes_no(proposal['constraints']['apply_authorized'])}",
        f"- Mission: `{proposal['mission_id']}`",
        f"- Release: {proposal['release']}",
        f"- Source plan hash: `{proposal['source_plan']['plan_hash']}`",
        "",
        "## Repository Fingerprint",
        f"- VCS: {repo['vcs']}",
        f"- Base ref: `{repo['base_ref']}`",
        f"- Dirty state: {repo['dirty_state']}",
        f"- Fingerprint hash: `{repo['fingerprint_hash']}`",
        "",
        "## Authority Required",
        f"- Requested by: {authority['requested_by']}",
        f"- Authority level: {authority['authority_level']}",
        f"- Approval state: {authority['approval_state']}",
        f"- Approving roles: {', '.join(authority['approving_roles'])}",
        f"- Allowed write paths: {len(authority['allowed_write_paths'])}",
        f"- Prohibited write paths: {len(authority['prohibited_write_paths'])}",
        "",
        "## Action Summary",
        f"- Total actions: {len(proposal['actions'])}",
        f"- Automatic: {count_class(proposal['actions'], 'automatic')}",
        f"- Approval required: {count_class(proposal['actions'], 'approval_required')}",
        f"- Manual: {count_class(proposal['actions'], 'manual')}",
        f"- Prohibited: {count_class(proposal['actions'], 'prohibited')}",
        "",
        "## Approval Required Actions",
    ]
    append_actions(lines, proposal["actions"], "approval_required")
    lines.append("")
    lines.append("## Automatic Actions")
    append_actions(lines, proposal["actions"], "automatic")
    lines.append("")
    lines.append("## Manual Actions")
    append_actions(lines, proposal["actions"], "manual")
    lines.append("")
    lines.append("## Prohibited Actions")
    append_actions(lines, proposal["actions"], "prohibited")
    lines.extend(
        [
            "",
            "## Drift Invalidation",
        ]
    )
    for condition in proposal["drift_invalidation_conditions"]:
        lines.append(f"- {condition}")
    lines.extend(
        [
            "",
            "## Read-Only Guarantee",
            "- This proposal did not modify the target repository.",
            "- This proposal does not approve or authorize apply.",
            "- Future apply must use this exact proposal identity and source plan hash.",
        ]
    )
    return "\n".join(lines) + "\n"


def append_actions(lines: list[str], actions: list[dict], classification: str) -> None:
    matched = [action for action in actions if action["class"] == classification]
    if not matched:
        lines.append("- None.")
        return
    for action in matched[:20]:
        target = action["target_path"] or "<manual>"
        rollback = action["rollback_strategy"]
        lines.append(f"- `{action['id']}` -> `{target}`")
        lines.append(f"  Status: {action['status']}")
        lines.append(f"  Rollback: {rollback}")


def write_json_report(path: str, proposal: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
