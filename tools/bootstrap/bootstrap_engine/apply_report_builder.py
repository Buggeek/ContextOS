from __future__ import annotations

import json
from pathlib import Path


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(result: dict) -> str:
    state = result["result"]
    confirmation = result["confirmation"]
    post_validator = result["validation"]["post_apply_validator"]
    lines = [
        "# Context OS Bootstrap Apply Result",
        "",
        f"- Schema: `{result['schema']}`",
        f"- Apply result ID: `{result['id']}`",
        f"- State: {state['state']}",
        f"- Success: {yes_no(state['success'])}",
        f"- Confirmed by: {confirmation['confirmed_by']}",
        f"- Confirmed role: {confirmation['confirmed_role']}",
        f"- Preflight ID: `{result['preflight']['id']}`",
        f"- Mutation set hash: `{result['mutation_set']['hash']}`",
        "",
        "## Mutations",
        f"- Requested actions: {result['mutation_set']['count']}",
        f"- Created artifacts: {len(result['mutations'])}",
    ]
    if result["mutations"]:
        for mutation in result["mutations"]:
            lines.append(f"- `{mutation['target_path']}` created by `{mutation['action_id']}`")
    else:
        lines.append("- None.")
    lines.extend(["", "## Pre-Apply Checks"])
    for check in result["validation"]["pre_apply_checks"]:
        lines.append(f"- `{check['id']}`: {'passed' if check['passed'] else 'failed'}")
    lines.extend(
        [
            "",
            "## Post-Apply Validator",
        ]
    )
    if post_validator is None:
        lines.append("- Not run because apply was blocked or failed before validation.")
    else:
        summary = post_validator["summary"]
        lines.append(f"- Errors: {summary['error']}")
        lines.append(f"- Fatals: {summary['fatal']}")
        lines.append(f"- Exit code: {summary['exit_code']}")
    lines.extend(
        [
            "",
            "## Rollback",
            f"- Available: {yes_no(result['rollback']['available'])}",
            f"- Created artifact count: {result['rollback']['created_artifact_count']}",
            f"- Strategy: {result['rollback']['strategy']}",
            f"- Will not remove pre-existing content: {yes_no(result['rollback']['will_not_remove_pre_existing_content'])}",
            "",
            "## Guarantees",
            "- Apply consumed the supplied preflight mutation set.",
            "- Apply performed create-only actions.",
            "- Apply did not overwrite, replace, or delete pre-existing content.",
            "- Prohibited and manual actions were not executed.",
            "",
            "## Next Step",
        ]
    )
    if state["success"]:
        lines.append("- Re-run `contextos assess` on the target repository and preserve this apply result as evidence.")
    else:
        lines.append("- Review failed checks or errors before generating a new preflight or attempting rollback.")
    if state["failed_pre_checks"]:
        lines.extend(["", "## Failed Pre-Apply Checks"])
        for failed in state["failed_pre_checks"]:
            lines.append(f"- `{failed}`")
    if state["errors"]:
        lines.extend(["", "## Errors"])
        for error in state["errors"]:
            lines.append(f"- {error['stage']}: {error['message']}")
    return "\n".join(lines) + "\n"


def write_json_report(path: str, result: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
