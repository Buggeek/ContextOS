from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.builder.draft_plan/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def count_status(items: list[dict], status: str) -> int:
    return sum(1 for item in items if item["status"] == status)


def build_report(
    root: Path,
    discovery_bundle: dict,
    construction_plan: dict,
    draft_items: list[dict],
    generated_at: str | None = None,
) -> dict:
    return {
        "schema": SCHEMA,
        "generated_at": generated_at or generated_timestamp(),
        "root": str(root.resolve()),
        "mode": "plan",
        "read_only": True,
        "source_inputs": {
            "discovery_bundle": {
                "schema": discovery_bundle["schema"],
                "source_id": discovery_bundle["source"]["id"],
                "source_fingerprint": discovery_bundle["source"]["fingerprint"],
                "artifact_count": discovery_bundle["summary"]["artifact_count"],
                "relationship_count": discovery_bundle["summary"]["relationship_count"],
                "ownership_evidence_count": discovery_bundle["summary"]["ownership_evidence_count"],
            },
            "construction_plan": {
                "schema": construction_plan["schema"],
                "ready_for_construction": construction_plan["summary"]["ready_for_construction"],
                "candidate_count": construction_plan["summary"]["candidate_count"],
                "blocked_action_count": construction_plan["summary"]["blocked_action_count"],
            },
        },
        "summary": {
            "draft_item_count": len(draft_items),
            "draftable_count": count_status(draft_items, "draftable"),
            "review_existing_count": count_status(draft_items, "review_existing"),
            "blocked_count": count_status(draft_items, "blocked"),
            "insufficient_evidence_count": count_status(draft_items, "insufficient_evidence"),
            "conflict_count": sum(len(item["contradictions"]) for item in draft_items),
            "unknown_count": sum(len(item["unknowns"]) for item in draft_items),
        },
        "draft_items": sorted(draft_items, key=lambda item: item["id"]),
        "lifecycle": {
            "input_states_allowed": ["observed", "suggested"],
            "output_states_allowed": ["draftable", "review_existing", "blocked", "insufficient_evidence"],
            "future_draft_state": "draft",
            "promotion_states_not_allowed": ["reviewed", "approved", "canonical_verified"],
        },
        "truth_boundaries": {
            "evidence_supports_draft_proposal": "Evidence may justify a future draft plan item.",
            "draft_is_not_truth": "A future draft artifact would remain non-canonical until human review, approval, and validation.",
            "observed_is_not_verified_complete": "Observed artifacts prove existence and literal metadata only.",
            "inferred_is_not_canonical": "Inferred classifications and support levels must not become organizational truth.",
        },
        "constraints": {
            "writes_performed": False,
            "drafts_created": False,
            "mom_created_or_modified": False,
            "ssot_created_or_modified": False,
            "automatic_truth_creation": False,
            "automatic_promotion": False,
            "knowledge_engine_used": False,
            "graph_runtime_used": False,
            "agents_used": False,
            "external_connectors_used": False,
        },
    }


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(report: dict) -> str:
    summary = report["summary"]
    lines = [
        "# Context OS Builder Draft Plan",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Root: `{report['root']}`",
        f"- Read-only: {yes_no(report['read_only'])}",
        f"- Draft items: {summary['draft_item_count']}",
        f"- Draftable: {summary['draftable_count']}",
        f"- Review existing: {summary['review_existing_count']}",
        f"- Blocked: {summary['blocked_count']}",
        f"- Insufficient evidence: {summary['insufficient_evidence_count']}",
        f"- Contradictions: {summary['conflict_count']}",
        f"- Unknowns: {summary['unknown_count']}",
        "",
        "## Draft Plan Items",
    ]
    if not report["draft_items"]:
        lines.append("- None.")
    for item in report["draft_items"][:20]:
        lines.append(f"- `{item['id']}` -> `{item['target_context_artifact']}`")
        lines.append(f"  Status: {item['status']} / intended state: {item['intended_lifecycle_state']}")
        lines.append(f"  Support: {item['support']['level']} ({item['support']['confidence']})")
        lines.append(f"  Reason: {item['draftability']['reason']}")

    lines.extend(
        [
            "",
            "## Truth Boundary",
            "- Evidence may support a draft proposal.",
            "- Evidence does not become organizational truth.",
            "- Draft creation, review, approval, and canonical verification remain separate future states.",
            "",
            "## Read-Only Guarantee",
            "- This plan did not create or modify MOM/SSOT artifacts.",
            "- No draft files were written.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_json_report(path: str, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
