from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.construction.plan/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def count_status(actions: list[dict], status: str) -> int:
    return sum(1 for action in actions if action["status"] == status)


def build_report(
    root: Path,
    readiness_report: dict,
    bootstrap_plan: dict,
    discovery_bundle: dict,
    candidates: list[dict],
    actions: list[dict],
    generated_at: str | None = None,
) -> dict:
    readiness_summary = readiness_report["summary"]
    inventory_summary = readiness_report["inventory"]["summary"]
    validator_summary = readiness_report["validator"]["summary"]
    return {
        "schema": SCHEMA,
        "generated_at": generated_at or generated_timestamp(),
        "root": str(root.resolve()),
        "mode": "plan",
        "read_only": True,
        "construction_lifecycle": {
            "states": ["observed", "inferred", "suggested", "draft", "reviewed", "approved", "canonical_verified"],
            "current_capability": "observed_evidence_to_suggested_draft_plan",
            "promotion_requires_human_approval": True,
            "canonical_truth_requires_validator_gate": True,
        },
        "readiness": {
            "schema": readiness_report["schema"],
            "score": readiness_summary["score"],
            "level": readiness_summary["level"],
            "level_name": readiness_summary["level_name"],
            "can_bootstrap": readiness_summary["can_bootstrap"],
            "can_construct": readiness_summary["can_construct"],
        },
        "inventory": {
            "schema": readiness_report["inventory"]["schema"],
            "artifact_count": inventory_summary["artifact_count"],
            "taxonomy_class_count": inventory_summary["taxonomy_class_count"],
            "runtime_artifact_count": inventory_summary["runtime_artifact_count"],
            "governance_artifact_count": inventory_summary["governance_artifact_count"],
            "roadmap_artifact_count": inventory_summary["roadmap_artifact_count"],
        },
        "validator": {
            "info": validator_summary["info"],
            "warn": validator_summary["warn"],
            "error": validator_summary["error"],
            "fatal": validator_summary["fatal"],
            "exit_code": validator_summary["exit_code"],
        },
        "bootstrap": {
            "schema": bootstrap_plan["schema"],
            "ready_for_bootstrap": bootstrap_plan["summary"]["ready_for_bootstrap"],
            "required_action_count": bootstrap_plan["summary"]["required_action_count"],
            "skipped_action_count": bootstrap_plan["summary"]["skipped_action_count"],
            "blocked_action_count": bootstrap_plan["summary"]["blocked_action_count"],
            "manual_action_count": bootstrap_plan["summary"]["manual_action_count"],
        },
        "discovery": {
            "schema": discovery_bundle["schema"],
            "source_id": discovery_bundle["source"]["id"],
            "source_type": discovery_bundle["source"]["type"],
            "source_fingerprint": discovery_bundle["source"]["fingerprint"],
            "artifact_count": discovery_bundle["summary"]["artifact_count"],
            "relationship_count": discovery_bundle["summary"]["relationship_count"],
            "ownership_evidence_count": discovery_bundle["summary"]["ownership_evidence_count"],
            "inferred_classification_count": discovery_bundle["summary"]["inferred_classification_count"],
        },
        "summary": {
            "ready_for_construction": readiness_summary["can_construct"] and validator_summary["error"] == 0 and validator_summary["fatal"] == 0,
            "candidate_count": len(candidates),
            "observed_candidate_count": sum(1 for candidate in candidates if candidate["lifecycle_state"] == "observed"),
            "suggested_candidate_count": sum(1 for candidate in candidates if candidate["lifecycle_state"] == "suggested"),
            "blocked_action_count": count_status(actions, "blocked"),
            "manual_action_count": count_status(actions, "manual"),
            "review_action_count": count_status(actions, "review"),
        },
        "context_artifact_candidates": sorted(candidates, key=lambda item: item["id"]),
        "actions": sorted(actions, key=lambda item: (item["status"], item["id"])),
        "truth_boundaries": {
            "observed_means": "The artifact or signal exists in the target repository.",
            "inferred_means": "The runtime derived a relationship from observed evidence; not used for canonical promotion in this slice.",
            "suggested_means": "The runtime recommends a draft target or review action; it has not created or verified truth.",
            "draft_means": "A future Builder may create reviewable content on a draft surface only.",
            "reviewed_means": "A human has reviewed the draft but has not necessarily approved canonical promotion.",
            "approved_means": "A human authority has approved the context for promotion under governance.",
            "canonical_verified_means": "The artifact is in a canonical surface and has passed applicable validation gates.",
        },
        "constraints": {
            "writes_performed": False,
            "artifacts_created": False,
            "automatic_truth_creation": False,
            "automatic_promotion": False,
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
        "# Context OS Construction Plan",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Root: `{report['root']}`",
        f"- Read-only: {yes_no(report['read_only'])}",
        f"- Ready for construction: {yes_no(summary['ready_for_construction'])}",
        f"- Source readiness: {readiness['score']}/100 ({readiness['level']} {readiness['level_name']})",
        f"- Candidates: {summary['candidate_count']}",
        f"- Observed candidates: {summary['observed_candidate_count']}",
        f"- Suggested candidates: {summary['suggested_candidate_count']}",
        f"- Review actions: {summary['review_action_count']}",
        f"- Manual actions: {summary['manual_action_count']}",
        f"- Blocked actions: {summary['blocked_action_count']}",
        f"- Discovery artifacts: {report['discovery']['artifact_count']}",
        f"- Discovery fingerprint: `{report['discovery']['source_fingerprint']}`",
        "",
        "## Context Lifecycle",
        "- observed -> inferred -> suggested -> draft -> reviewed -> approved -> canonical/verified",
        "- This plan stops at observed evidence and suggested draft/review actions.",
        "- It does not create drafts, approve context, or promote truth.",
        "",
        "## Constructable Candidates",
    ]
    for candidate in report["context_artifact_candidates"][:20]:
        lines.append(f"- `{candidate['id']}` -> `{candidate['target_path']}`")
        lines.append(f"  State: {candidate['lifecycle_state']} / {candidate['belief_state']}")
        lines.append(f"  Boundary: {candidate['truth_boundary']}")
    if not report["context_artifact_candidates"]:
        lines.append("- None.")

    lines.extend(["", "## Required Review / Construction Actions"])
    append_actions(lines, report["actions"], "review")
    lines.append("")
    lines.append("## Manual Actions")
    append_actions(lines, report["actions"], "manual")
    lines.append("")
    lines.append("## Blocked Actions")
    append_actions(lines, report["actions"], "blocked")
    lines.extend(
        [
            "",
            "## Validator Summary",
            f"- Findings: info={validator['info']}, warn={validator['warn']}, "
            f"error={validator['error']}, fatal={validator['fatal']}",
            f"- Exit code: {validator['exit_code']}",
            "",
            "## Truth Boundary",
            "- Observed artifacts are evidence of existence, not proof that their contents are complete or current.",
            "- Suggested candidates are not organizational truth.",
            "- Human review and Validator gates are required before canonical promotion.",
            "",
            "## Read-Only Guarantee",
            "- This construction plan did not modify the target repository.",
            "- No MOM, SSOT, graph, memory, or runtime artifacts were created.",
        ]
    )
    return "\n".join(lines) + "\n"


def append_actions(lines: list[str], actions: list[dict], status: str) -> None:
    matched = [action for action in actions if action["status"] == status]
    if not matched:
        lines.append("- None.")
        return
    for action in matched[:20]:
        target = action.get("target_path") or "<manual>"
        lines.append(f"- `{action['id']}` -> `{target}`")
        lines.append(f"  Reason: {action['reason']}")
        lines.append(f"  Authority: {action['authority_required']['role']} ({action['authority_required']['level']})")


def write_json_report(path: str, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
