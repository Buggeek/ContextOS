from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.bootstrap.plan/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def count_status(actions: list[dict], status: str) -> int:
    return sum(1 for action in actions if action["status"] == status)


def build_report(
    root: Path,
    readiness_report: dict,
    actions: list[dict],
    generated_at: str | None = None,
) -> dict:
    readiness_summary = readiness_report["summary"]
    validator_summary = readiness_report["validator"]["summary"]
    return {
        "schema": SCHEMA,
        "generated_at": generated_at or generated_timestamp(),
        "root": str(root.resolve()),
        "mode": "plan",
        "read_only": True,
        "readiness": {
            "schema": readiness_report["schema"],
            "score": readiness_summary["score"],
            "level": readiness_summary["level"],
            "level_name": readiness_summary["level_name"],
            "can_bootstrap": readiness_summary["can_bootstrap"],
            "can_construct": readiness_summary["can_construct"],
            "recommendation_count": readiness_summary["recommendation_count"],
        },
        "validator": {
            "info": validator_summary["info"],
            "warn": validator_summary["warn"],
            "error": validator_summary["error"],
            "fatal": validator_summary["fatal"],
            "exit_code": validator_summary["exit_code"],
        },
        "summary": {
            "ready_for_bootstrap": readiness_summary["can_bootstrap"],
            "can_plan_bootstrap": validator_summary["fatal"] == 0,
            "required_action_count": count_status(actions, "required"),
            "skipped_action_count": count_status(actions, "skipped_existing"),
            "blocked_action_count": count_status(actions, "blocked"),
            "manual_action_count": count_status(actions, "manual"),
        },
        "actions": sorted(actions, key=lambda item: (item["status"], item["id"])),
        "constraints": {
            "writes_performed": False,
            "manifests_created": False,
            "artifacts_created": False,
            "external_connectors_used": False,
            "knowledge_engine_used": False,
            "graph_runtime_used": False,
            "agents_used": False,
        },
    }


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(report: dict) -> str:
    summary = report["summary"]
    readiness = report["readiness"]
    validator = report["validator"]
    lines = [
        "# Context OS Bootstrap Plan",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Root: `{report['root']}`",
        f"- Read-only: {yes_no(report['read_only'])}",
        f"- Ready for bootstrap: {yes_no(summary['ready_for_bootstrap'])}",
        f"- Can plan bootstrap: {yes_no(summary['can_plan_bootstrap'])}",
        f"- Source readiness: {readiness['score']}/100 ({readiness['level']} {readiness['level_name']})",
        f"- Required actions: {summary['required_action_count']}",
        f"- Skipped existing: {summary['skipped_action_count']}",
        f"- Blocked actions: {summary['blocked_action_count']}",
        f"- Manual actions: {summary['manual_action_count']}",
        "",
        "## Required Actions",
    ]
    append_actions(lines, report["actions"], "required")
    lines.append("")
    lines.append("## Skipped Existing Targets")
    append_actions(lines, report["actions"], "skipped_existing")
    lines.append("")
    lines.append("## Blocked Actions")
    append_actions(lines, report["actions"], "blocked")
    lines.append("")
    lines.append("## Manual Actions")
    append_actions(lines, report["actions"], "manual")
    lines.extend(
        [
            "",
            "## Validator Summary",
            f"- Findings: info={validator['info']}, warn={validator['warn']}, "
            f"error={validator['error']}, fatal={validator['fatal']}",
            f"- Exit code: {validator['exit_code']}",
            "",
            "## Read-Only Guarantee",
            "- This plan did not modify the target repository.",
            "- No manifests, directories, or scaffold artifacts were created.",
            "",
            "## Next Step",
            "- Review required, blocked, and manual actions before any future apply approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def append_actions(lines: list[str], actions: list[dict], status: str) -> None:
    matched = [action for action in actions if action["status"] == status]
    if not matched:
        lines.append("- None.")
        return
    for action in matched[:20]:
        target = action["target_path"] or "<manual>"
        recs = ", ".join(action["recommendation_ids"]) or "<none>"
        lines.append(f"- `{action['id']}` -> `{target}`")
        lines.append(f"  Reason: {action['reason']}")
        lines.append(f"  Recommendation: {recs}")


def write_json_report(path: str, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
