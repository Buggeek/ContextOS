from __future__ import annotations

import json
from pathlib import Path

from builder_engine.draft_create import role_satisfies
from builder_engine.draft_review import SCHEMA as REVIEW_SCHEMA
from builder_engine.draft_review import draft_review_id, draft_review_payload
from builder_engine.draft_workspace import path_state, stable_hash
from builder_engine.report_builder import generated_timestamp


SCHEMA = "contextos.builder.draft_review_decision/1"
REQUIRED_AUTHORITY_LEVEL = "L2"
REQUIRED_CAPABILITY = "builder.draft.review"

ALLOWED_OUTCOMES = {
    "reviewed_ready_for_next_governance_step": {
        "label": "Reviewed: ready for next governance step",
        "next_permitted_transition": "approval_proposal_allowed",
    },
    "changes_requested": {
        "label": "Changes requested",
        "next_permitted_transition": "draft_revision_required",
    },
    "rejected": {
        "label": "Rejected",
        "next_permitted_transition": "terminal_rejected_unless_new_evidence",
    },
    "insufficient_evidence": {
        "label": "Insufficient evidence",
        "next_permitted_transition": "evidence_collection_required",
    },
    "superseded": {
        "label": "Superseded",
        "next_permitted_transition": "newer_draft_required",
    },
}


def review_identity_valid(review: dict) -> bool:
    return review.get("id") == draft_review_id(review) and review.get("identity_hash") == stable_hash(draft_review_payload(review))


def decision_payload(decision: dict) -> dict:
    return {
        "schema": decision["schema"],
        "review": decision["review"],
        "draft": decision["draft"],
        "source": decision["source"],
        "reviewer": decision["reviewer"],
        "outcome": decision["outcome"],
        "evidence": decision["evidence"],
        "boundaries": decision["boundaries"],
        "result": decision["result"],
    }


def review_decision_id(decision: dict) -> str:
    return f"builder.draft_review_decision.{stable_hash(decision_payload(decision))[:16]}"


def selected_review_item(review: dict, draft_item_id: str | None) -> dict:
    items = review.get("draft_reviews", [])
    if draft_item_id is None:
        if len(items) != 1:
            raise ValueError("Draft review decision requires draft_item_id when review contains multiple drafts.")
        return items[0]
    for item in items:
        if item.get("draft_item_id") == draft_item_id:
            return item
    raise ValueError(f"Draft review decision could not find draft_item_id: {draft_item_id}")


def required_roles_for(review: dict, item: dict) -> list[str]:
    roles = []
    draft_role = item.get("authority_still_required", {}).get("draft_authority", {}).get("role")
    authorized_role = review.get("source_write_result", {}).get("authorization", {}).get("authorized_role")
    if draft_role:
        roles.append(draft_role)
    if authorized_role:
        roles.append(authorized_role)
    return sorted(dict.fromkeys(roles))


def check(identifier: str, passed: bool, evidence: dict) -> dict:
    return {"id": identifier, "passed": bool(passed), "evidence": evidence}


def write_json_report(path: str | Path, report: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class BuilderDraftReviewDecisionEngine:
    """Persist a governed human review decision without approving or promoting."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        review: dict,
        *,
        outcome: str,
        reviewed_by: str,
        reviewer_role: str,
        reviewer_authority_level: str,
        reviewer_capability: str,
        reviewer_rationale: str,
        source_mission_id: str,
        draft_item_id: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if review.get("schema") != REVIEW_SCHEMA:
            raise ValueError("Draft review decision requires contextos.builder.draft_review/1 input.")
        if outcome not in ALLOWED_OUTCOMES:
            raise ValueError(f"Unsupported draft review decision outcome: {outcome}")
        if not reviewed_by or not reviewed_by.strip():
            raise ValueError("Draft review decision requires explicit reviewer identity.")
        if not reviewer_role or not reviewer_role.strip():
            raise ValueError("Draft review decision requires explicit reviewer role.")
        if not reviewer_rationale or not reviewer_rationale.strip():
            raise ValueError("Draft review decision requires reviewer rationale.")

        item = selected_review_item(review, draft_item_id)
        root = self.root.resolve()
        target_path = root / item["draft_path"]
        current_state = path_state(target_path)
        roles = required_roles_for(review, item)
        outcome_model = ALLOWED_OUTCOMES[outcome]
        checks = [
            check(
                "draft_review_decision.check.review_identity_valid",
                review_identity_valid(review),
                {"review_id": review.get("id"), "review_identity_hash": review.get("identity_hash")},
            ),
            check(
                "draft_review_decision.check.review_result_success",
                review.get("result", {}).get("success") is True,
                review.get("result", {}),
            ),
            check(
                "draft_review_decision.check.draft_reviewable",
                item.get("reviewable") is True and item.get("status") == "reviewable",
                {"status": item.get("status"), "errors": item.get("errors", [])},
            ),
            check(
                "draft_review_decision.check.draft_hash_unchanged",
                current_state.get("hash") == item.get("identity", {}).get("file_hash"),
                {"current": current_state, "reviewed_hash": item.get("identity", {}).get("file_hash")},
            ),
            check(
                "draft_review_decision.check.lifecycle_still_draft",
                item.get("lifecycle", {}).get("state") == "draft"
                and not item.get("lifecycle", {}).get("canonical")
                and not item.get("lifecycle", {}).get("approved")
                and not item.get("lifecycle", {}).get("canonical_verified"),
                item.get("lifecycle", {}),
            ),
            check(
                "draft_review_decision.check.explicit_l2_review_authority",
                reviewer_authority_level == REQUIRED_AUTHORITY_LEVEL and reviewer_capability == REQUIRED_CAPABILITY,
                {"authority_level": reviewer_authority_level, "capability": reviewer_capability},
            ),
            check(
                "draft_review_decision.check.reviewer_role_satisfies_required_roles",
                bool(roles) and role_satisfies(reviewer_role, roles),
                {"reviewer_role": reviewer_role, "required_roles": roles},
            ),
            check(
                "draft_review_decision.check.source_mission_bound",
                source_mission_id == item.get("source", {}).get("mission_id")
                or source_mission_id == review.get("source_write_result", {}).get("authorization", {}).get("authorized_mission_id"),
                {
                    "source_mission_id": source_mission_id,
                    "draft_mission_id": item.get("source", {}).get("mission_id"),
                    "write_mission_id": review.get("source_write_result", {})
                    .get("authorization", {})
                    .get("authorized_mission_id"),
                },
            ),
            check(
                "draft_review_decision.check.no_approval_or_promotion",
                True,
                {"approval_granted": False, "promotion_granted": False, "canonical_truth_created": False},
            ),
        ]
        failed_checks = [entry["id"] for entry in checks if not entry["passed"]]
        result_state = "review_decision_recorded" if not failed_checks else "blocked"
        decision = {
            "schema": SCHEMA,
            "id": "",
            "identity_hash": "",
            "generated_at": generated_at or generated_timestamp(),
            "root": str(root),
            "review": {
                "schema": review["schema"],
                "id": review["id"],
                "identity_hash": review["identity_hash"],
                "identity_valid": review_identity_valid(review),
            },
            "draft": {
                "draft_item_id": item["draft_item_id"],
                "draft_path": item["draft_path"],
                "draft_workspace_location": ".contextos/drafts/",
                "target_context_artifact": item.get("target_context_artifact"),
                "target_identity": item.get("identity", {}).get("target_identity"),
                "content_hash": item.get("identity", {}).get("file_hash"),
                "current_content_hash": current_state.get("hash"),
                "lifecycle_state": item.get("lifecycle", {}).get("state"),
                "canonical": item.get("lifecycle", {}).get("canonical") is True,
                "approved": item.get("lifecycle", {}).get("approved") is True,
                "canonical_verified": item.get("lifecycle", {}).get("canonical_verified") is True,
            },
            "source": {
                "mission_id": source_mission_id,
                "write_result_id": review.get("source_write_result", {}).get("id"),
                "write_result_hash": review.get("source_write_result", {}).get("identity_hash"),
                "source_preflight_id": item.get("source", {}).get("source_preflight_id"),
                "source_preflight_hash": item.get("source", {}).get("source_preflight_hash"),
                "builder_draft_plan_hash": item.get("source", {}).get("source_builder_draft_plan_hash"),
                "discovery_id": item.get("provenance", {}).get("source_discovery_id"),
                "discovery_fingerprint": item.get("provenance", {}).get("source_discovery_fingerprint"),
                "construction_candidate_id": item.get("provenance", {}).get("source_construction_candidate_id"),
            },
            "reviewer": {
                "reviewed_by": reviewed_by.strip(),
                "reviewer_role": reviewer_role.strip(),
                "authority_level": reviewer_authority_level,
                "capability": reviewer_capability,
                "required_roles": roles,
                "role_satisfied": role_satisfies(reviewer_role, roles) if roles else False,
            },
            "outcome": {
                "value": outcome,
                "label": outcome_model["label"],
                "rationale": reviewer_rationale.strip(),
                "next_permitted_transition": outcome_model["next_permitted_transition"],
                "draft_remains_non_canonical": True,
                "review_is_not_approval": True,
                "approval_granted": False,
                "promotion_granted": False,
                "canonical_truth_created": False,
            },
            "evidence": {
                "checks": checks,
                "evidence_refs": item.get("evidence_refs", []),
                "support": item.get("support", {}),
                "unknowns": item.get("uncertainty", {}).get("unknowns", []),
                "missing_evidence": item.get("uncertainty", {}).get("missing_evidence", []),
                "contradictions": item.get("uncertainty", {}).get("contradictions", []),
                "validator": review.get("validation", {}).get("validator", {}),
                "repository_state": {
                    "draft_path_state": current_state,
                    "review_read_only_unchanged": review.get("validation", {}).get("read_only_unchanged"),
                },
            },
            "invalidation": {
                "invalidated_by": [
                    "review_identity_changed",
                    "draft_content_hash_changed",
                    "draft_path_changed",
                    "draft_lifecycle_not_draft",
                    "canonical_or_approved_flag_appeared",
                    "source_preflight_changed",
                    "builder_draft_plan_hash_changed",
                    "reviewer_authority_changed",
                    "validator_gate_changed",
                ],
                "changed_draft_invalidates_decision": True,
                "supersession_required_for_new_draft": True,
                "silent_inheritance_allowed": False,
            },
            "boundaries": {
                "review_is_not_approval": True,
                "decision_is_not_promotion": True,
                "draft_remains_non_canonical": True,
                "ssot_writes_performed": False,
                "canonical_context_writes_performed": False,
                "draft_content_mutated": False,
                "uncertainty_preserved": True,
            },
            "result": {
                "state": result_state,
                "success": not failed_checks,
                "failed_check_count": len(failed_checks),
                "failed_checks": failed_checks,
            },
            "constraints": {
                "review_decision_persistable": True,
                "drafts_mutated": False,
                "approval_performed": False,
                "promotion_performed": False,
                "ssot_writes_performed": False,
                "canonical_context_writes_performed": False,
                "knowledge_engine_used": False,
                "graph_runtime_used": False,
                "agents_used": False,
                "external_connectors_used": False,
            },
        }
        decision["id"] = review_decision_id(decision)
        decision["identity_hash"] = stable_hash(decision_payload(decision))
        return decision

    def check_invalidation(self, decision: dict, current_review: dict) -> dict:
        item = selected_review_item(current_review, decision["draft"]["draft_item_id"])
        checks = [
            check(
                "draft_review_decision.invalidation.review_identity_unchanged",
                current_review.get("id") == decision.get("review", {}).get("id")
                and current_review.get("identity_hash") == decision.get("review", {}).get("identity_hash"),
                {
                    "decision_review_id": decision.get("review", {}).get("id"),
                    "current_review_id": current_review.get("id"),
                },
            ),
            check(
                "draft_review_decision.invalidation.draft_content_hash_unchanged",
                item.get("identity", {}).get("file_hash") == decision.get("draft", {}).get("content_hash"),
                {
                    "decision_hash": decision.get("draft", {}).get("content_hash"),
                    "current_hash": item.get("identity", {}).get("file_hash"),
                },
            ),
            check(
                "draft_review_decision.invalidation.draft_path_unchanged",
                item.get("draft_path") == decision.get("draft", {}).get("draft_path"),
                {"decision_path": decision.get("draft", {}).get("draft_path"), "current_path": item.get("draft_path")},
            ),
            check(
                "draft_review_decision.invalidation.draft_still_non_canonical",
                item.get("lifecycle", {}).get("state") == "draft"
                and not item.get("lifecycle", {}).get("canonical")
                and not item.get("lifecycle", {}).get("approved")
                and not item.get("lifecycle", {}).get("canonical_verified"),
                item.get("lifecycle", {}),
            ),
        ]
        failed = [entry["id"] for entry in checks if not entry["passed"]]
        return {
            "schema": "contextos.builder.draft_review_decision_invalidation/1",
            "source_decision_id": decision["id"],
            "draft_item_id": decision["draft"]["draft_item_id"],
            "invalidated": bool(failed),
            "failed_checks": failed,
            "checks": checks,
        }


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(decision: dict) -> str:
    outcome = decision["outcome"]
    evidence = decision["evidence"]
    lines = [
        "# Context OS Draft Review Decision",
        "",
        f"- Schema: `{decision['schema']}`",
        f"- Decision: `{decision['id']}`",
        f"- Outcome: {outcome['label']}",
        f"- Success: {yes_no(decision['result']['success'])}",
        f"- Draft: `{decision['draft']['draft_item_id']}`",
        f"- Draft path: `{decision['draft']['draft_path']}`",
        f"- Reviewer: {decision['reviewer']['reviewed_by']} ({decision['reviewer']['reviewer_role']})",
        f"- Authority: {decision['reviewer']['authority_level']} `{decision['reviewer']['capability']}`",
        f"- Next permitted transition: `{outcome['next_permitted_transition']}`",
        "",
        "## Boundary",
        "- Review decision is not approval.",
        "- Review decision is not promotion.",
        "- Draft remains non-canonical organizational context.",
        "- Canonical SSOT remains unchanged.",
        "",
        "## Rationale",
        outcome["rationale"],
        "",
        "## Evidence",
        f"- Evidence refs: {len(evidence['evidence_refs'])}",
        f"- Unknowns preserved: {len(evidence['unknowns'])}",
        f"- Missing evidence preserved: {len(evidence['missing_evidence'])}",
        f"- Contradictions preserved: {len(evidence['contradictions'])}",
        f"- Validator errors/fatals: {evidence['validator']['summary']['error']}/"
        f"{evidence['validator']['summary']['fatal']}",
        "",
        "## Result",
        f"- State: `{decision['result']['state']}`",
        f"- Failed checks: {decision['result']['failed_check_count']}",
    ]
    return "\n".join(lines) + "\n"
