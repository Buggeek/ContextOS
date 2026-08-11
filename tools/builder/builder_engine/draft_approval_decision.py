from __future__ import annotations

import json
import sys
from pathlib import Path

from builder_engine.draft_create import role_satisfies
from builder_engine.draft_review_decision import SCHEMA as REVIEW_DECISION_SCHEMA
from builder_engine.draft_review_decision import decision_payload as review_decision_payload
from builder_engine.draft_review_decision import review_decision_id
from builder_engine.draft_workspace import path_state, stable_hash
from builder_engine.report_builder import generated_timestamp


TOOLS_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from engine.validator_engine import ValidatorEngine  # noqa: E402


SCHEMA = "contextos.builder.draft_approval_decision/1"
REQUIRED_AUTHORITY_LEVEL = "L3"
REQUIRED_CAPABILITY = "builder.draft.approve"
ELIGIBLE_REVIEW_OUTCOME = "reviewed_ready_for_next_governance_step"

ALLOWED_OUTCOMES = {
    "approved_for_promotion_proposal": {
        "label": "Approved for separate promotion proposal",
        "approval_granted": True,
        "next_permitted_transition": "promotion_proposal_allowed",
    },
    "approval_rejected": {
        "label": "Approval rejected",
        "approval_granted": False,
        "next_permitted_transition": "draft_revision_or_review_required",
    },
    "approval_deferred": {
        "label": "Approval deferred",
        "approval_granted": False,
        "next_permitted_transition": "evidence_or_authority_required",
    },
}


def review_decision_identity_valid(review_decision: dict) -> bool:
    return review_decision.get("id") == review_decision_id(review_decision) and review_decision.get("identity_hash") == stable_hash(
        review_decision_payload(review_decision)
    )


def approval_decision_payload(decision: dict) -> dict:
    return {
        "schema": decision["schema"],
        "review_decision": decision["review_decision"],
        "draft": decision["draft"],
        "source": decision["source"],
        "reviewer": decision["reviewer"],
        "approver": decision["approver"],
        "approval": decision["approval"],
        "evidence": decision["evidence"],
        "boundaries": decision["boundaries"],
        "result": decision["result"],
    }


def approval_decision_id(decision: dict) -> str:
    return f"builder.draft_approval_decision.{stable_hash(approval_decision_payload(decision))[:16]}"


def check(identifier: str, passed: bool, evidence: dict) -> dict:
    return {"id": identifier, "passed": bool(passed), "evidence": evidence}


def write_json_report(path: str | Path, report: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class BuilderDraftApprovalDecisionEngine:
    """Record organizational approval of an exact reviewed draft without promotion."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        review_decision: dict,
        *,
        outcome: str,
        approved_by: str,
        approver_role: str,
        approver_authority_level: str,
        approver_capability: str,
        approval_scope: str,
        approver_rationale: str,
        source_mission_id: str,
        generated_at: str | None = None,
    ) -> dict:
        if review_decision.get("schema") != REVIEW_DECISION_SCHEMA:
            raise ValueError("Draft approval decision requires contextos.builder.draft_review_decision/1 input.")
        if outcome not in ALLOWED_OUTCOMES:
            raise ValueError(f"Unsupported draft approval decision outcome: {outcome}")
        if not approved_by or not approved_by.strip():
            raise ValueError("Draft approval decision requires explicit approver identity.")
        if not approver_role or not approver_role.strip():
            raise ValueError("Draft approval decision requires explicit approver role.")
        if not approver_rationale or not approver_rationale.strip():
            raise ValueError("Draft approval decision requires approver rationale.")
        if not approval_scope or not approval_scope.strip():
            raise ValueError("Draft approval decision requires explicit approval scope.")

        root = self.root.resolve()
        timestamp = generated_at or generated_timestamp()
        draft_path = root / review_decision["draft"]["draft_path"]
        current_state = path_state(draft_path)
        validator_report = ValidatorEngine(root).run(mode="gate")
        approval_model = ALLOWED_OUTCOMES[outcome]
        required_roles = review_decision.get("reviewer", {}).get("required_roles", [])
        contradictions = review_decision.get("evidence", {}).get("contradictions", [])
        checks = [
            check(
                "draft_approval_decision.check.review_decision_identity_valid",
                review_decision_identity_valid(review_decision),
                {
                    "review_decision_id": review_decision.get("id"),
                    "review_decision_identity_hash": review_decision.get("identity_hash"),
                },
            ),
            check(
                "draft_approval_decision.check.review_decision_success",
                review_decision.get("result", {}).get("success") is True,
                review_decision.get("result", {}),
            ),
            check(
                "draft_approval_decision.check.review_outcome_eligible",
                review_decision.get("outcome", {}).get("value") == ELIGIBLE_REVIEW_OUTCOME,
                {"review_outcome": review_decision.get("outcome", {}).get("value"), "required": ELIGIBLE_REVIEW_OUTCOME},
            ),
            check(
                "draft_approval_decision.check.draft_hash_unchanged",
                current_state.get("hash") == review_decision.get("draft", {}).get("content_hash"),
                {"current": current_state, "review_decision_hash": review_decision.get("draft", {}).get("content_hash")},
            ),
            check(
                "draft_approval_decision.check.draft_remains_non_canonical",
                not review_decision.get("draft", {}).get("canonical")
                and not review_decision.get("draft", {}).get("approved")
                and not review_decision.get("draft", {}).get("canonical_verified"),
                review_decision.get("draft", {}),
            ),
            check(
                "draft_approval_decision.check.builder_draft_plan_bound",
                bool(review_decision.get("source", {}).get("builder_draft_plan_hash")),
                {"builder_draft_plan_hash": review_decision.get("source", {}).get("builder_draft_plan_hash")},
            ),
            check(
                "draft_approval_decision.check.discovery_construction_provenance_bound",
                bool(review_decision.get("source", {}).get("discovery_fingerprint"))
                and bool(review_decision.get("source", {}).get("construction_candidate_id")),
                {
                    "discovery_fingerprint": review_decision.get("source", {}).get("discovery_fingerprint"),
                    "construction_candidate_id": review_decision.get("source", {}).get("construction_candidate_id"),
                },
            ),
            check(
                "draft_approval_decision.check.no_contradictions_for_approval",
                outcome != "approved_for_promotion_proposal" or len(contradictions) == 0,
                {"contradiction_count": len(contradictions)},
            ),
            check(
                "draft_approval_decision.check.explicit_l3_approval_authority",
                approver_authority_level == REQUIRED_AUTHORITY_LEVEL and approver_capability == REQUIRED_CAPABILITY,
                {"authority_level": approver_authority_level, "capability": approver_capability},
            ),
            check(
                "draft_approval_decision.check.approver_role_satisfies_required_roles",
                bool(required_roles) and role_satisfies(approver_role, required_roles),
                {"approver_role": approver_role, "required_roles": required_roles},
            ),
            check(
                "draft_approval_decision.check.source_mission_bound",
                source_mission_id == review_decision.get("source", {}).get("mission_id"),
                {"source_mission_id": source_mission_id, "review_decision_mission_id": review_decision.get("source", {}).get("mission_id")},
            ),
            check(
                "draft_approval_decision.check.scope_is_promotion_proposal_only",
                approval_scope == "draft_for_future_promotion_proposal",
                {"approval_scope": approval_scope},
            ),
            check(
                "draft_approval_decision.check.validator_gate_satisfied",
                validator_report["summary"]["error"] == 0 and validator_report["summary"]["fatal"] == 0,
                validator_report["summary"],
            ),
            check(
                "draft_approval_decision.check.promotion_not_authorized",
                True,
                {"promotion_authorized": False, "canonical_context_write_authorized": False},
            ),
        ]
        failed_checks = [entry["id"] for entry in checks if not entry["passed"]]
        decision = {
            "schema": SCHEMA,
            "id": "",
            "identity_hash": "",
            "generated_at": timestamp,
            "root": str(root),
            "review_decision": {
                "schema": review_decision["schema"],
                "id": review_decision["id"],
                "identity_hash": review_decision["identity_hash"],
                "identity_valid": review_decision_identity_valid(review_decision),
                "outcome": review_decision["outcome"]["value"],
                "rationale": review_decision["outcome"]["rationale"],
            },
            "draft": {
                "draft_item_id": review_decision["draft"]["draft_item_id"],
                "draft_path": review_decision["draft"]["draft_path"],
                "draft_workspace_location": review_decision["draft"]["draft_workspace_location"],
                "target_context_artifact": review_decision["draft"]["target_context_artifact"],
                "target_identity": review_decision["draft"]["target_identity"],
                "content_hash": review_decision["draft"]["content_hash"],
                "current_content_hash": current_state.get("hash"),
                "lifecycle_state": "approved" if outcome == "approved_for_promotion_proposal" and not failed_checks else "draft",
                "approval_recorded": outcome == "approved_for_promotion_proposal" and not failed_checks,
                "canonical": False,
                "canonical_verified": False,
                "promotion_authorized": False,
            },
            "source": {
                "mission_id": source_mission_id,
                "write_result_id": review_decision["source"]["write_result_id"],
                "write_result_hash": review_decision["source"]["write_result_hash"],
                "source_preflight_id": review_decision["source"]["source_preflight_id"],
                "source_preflight_hash": review_decision["source"]["source_preflight_hash"],
                "builder_draft_plan_hash": review_decision["source"]["builder_draft_plan_hash"],
                "discovery_id": review_decision["source"]["discovery_id"],
                "discovery_fingerprint": review_decision["source"]["discovery_fingerprint"],
                "construction_candidate_id": review_decision["source"]["construction_candidate_id"],
            },
            "reviewer": review_decision["reviewer"],
            "approver": {
                "approved_by": approved_by.strip(),
                "approver_role": approver_role.strip(),
                "authority_level": approver_authority_level,
                "capability": approver_capability,
                "required_roles": required_roles,
                "role_satisfied": role_satisfies(approver_role, required_roles) if required_roles else False,
            },
            "approval": {
                "value": outcome,
                "label": approval_model["label"],
                "approval_granted": approval_model["approval_granted"] and not failed_checks,
                "scope": approval_scope,
                "rationale": approver_rationale.strip(),
                "next_permitted_transition": approval_model["next_permitted_transition"],
                "promotion_eligible": outcome == "approved_for_promotion_proposal" and not failed_checks,
                "promotion_authorized": False,
                "canonical_truth_created": False,
                "canonical": False,
            },
            "evidence": {
                "checks": checks,
                "evidence_refs": review_decision["evidence"]["evidence_refs"],
                "support": review_decision["evidence"]["support"],
                "unknowns": review_decision["evidence"]["unknowns"],
                "missing_evidence": review_decision["evidence"]["missing_evidence"],
                "contradictions": contradictions,
                "reviewer_rationale": review_decision["outcome"]["rationale"],
                "approver_rationale": approver_rationale.strip(),
                "validator": {"schema": validator_report["schema"], "summary": validator_report["summary"]},
                "repository_state": {
                    "draft_path_state": current_state,
                    "review_decision_repository_state": review_decision["evidence"]["repository_state"],
                },
            },
            "invalidation": {
                "invalidated_by": [
                    "review_decision_identity_changed",
                    "draft_content_hash_changed",
                    "draft_path_changed",
                    "builder_draft_plan_hash_changed",
                    "discovery_or_construction_provenance_changed",
                    "reviewer_or_approver_authority_changed",
                    "validator_gate_changed",
                    "promotion_scope_changed",
                ],
                "changed_draft_invalidates_approval": True,
                "changed_review_decision_invalidates_approval": True,
                "silent_inheritance_allowed": False,
            },
            "promotion": {
                "eligible_for_future_promotion_proposal": outcome == "approved_for_promotion_proposal" and not failed_checks,
                "promotion_authorized": False,
                "canonical_write_authorized": False,
                "requires_separate_governed_mission": True,
                "restrictions": [
                    "no_automatic_promotion",
                    "promotion_requires_fresh_validation",
                    "promotion_requires_explicit_human_authority",
                    "promotion_requires_canonical_write_boundary",
                ],
            },
            "boundaries": {
                "review_decision_is_not_approval_decision": True,
                "approval_decision_is_not_promotion": True,
                "promotion_is_not_canonical_until_validated": True,
                "draft_remains_non_canonical": True,
                "ssot_writes_performed": False,
                "canonical_context_writes_performed": False,
                "draft_content_mutated": False,
                "uncertainty_preserved": True,
            },
            "result": {
                "state": "approval_decision_recorded" if not failed_checks else "blocked",
                "success": not failed_checks,
                "failed_check_count": len(failed_checks),
                "failed_checks": failed_checks,
            },
            "constraints": {
                "approval_decision_persistable": True,
                "drafts_mutated": False,
                "promotion_performed": False,
                "ssot_writes_performed": False,
                "canonical_context_writes_performed": False,
                "knowledge_engine_used": False,
                "graph_runtime_used": False,
                "agents_used": False,
                "external_connectors_used": False,
            },
        }
        decision["id"] = approval_decision_id(decision)
        decision["identity_hash"] = stable_hash(approval_decision_payload(decision))
        return decision

    def check_invalidation(self, approval_decision: dict, current_review_decision: dict) -> dict:
        draft_path = self.root.resolve() / approval_decision["draft"]["draft_path"]
        current_state = path_state(draft_path)
        validator_report = ValidatorEngine(self.root).run(mode="gate")
        checks = [
            check(
                "draft_approval_decision.invalidation.review_decision_identity_unchanged",
                current_review_decision.get("id") == approval_decision.get("review_decision", {}).get("id")
                and current_review_decision.get("identity_hash") == approval_decision.get("review_decision", {}).get("identity_hash"),
                {
                    "approval_review_decision_id": approval_decision.get("review_decision", {}).get("id"),
                    "current_review_decision_id": current_review_decision.get("id"),
                },
            ),
            check(
                "draft_approval_decision.invalidation.review_decision_authentic",
                review_decision_identity_valid(current_review_decision),
                {"current_review_decision_id": current_review_decision.get("id")},
            ),
            check(
                "draft_approval_decision.invalidation.draft_content_hash_unchanged",
                current_state.get("hash") == approval_decision.get("draft", {}).get("content_hash"),
                {"approval_hash": approval_decision.get("draft", {}).get("content_hash"), "current": current_state},
            ),
            check(
                "draft_approval_decision.invalidation.builder_draft_plan_hash_unchanged",
                current_review_decision.get("source", {}).get("builder_draft_plan_hash")
                == approval_decision.get("source", {}).get("builder_draft_plan_hash"),
                {
                    "approval_hash": approval_decision.get("source", {}).get("builder_draft_plan_hash"),
                    "current_hash": current_review_decision.get("source", {}).get("builder_draft_plan_hash"),
                },
            ),
            check(
                "draft_approval_decision.invalidation.validator_gate_still_satisfied",
                validator_report["summary"]["error"] == 0 and validator_report["summary"]["fatal"] == 0,
                validator_report["summary"],
            ),
        ]
        failed = [entry["id"] for entry in checks if not entry["passed"]]
        return {
            "schema": "contextos.builder.draft_approval_decision_invalidation/1",
            "source_approval_decision_id": approval_decision["id"],
            "draft_item_id": approval_decision["draft"]["draft_item_id"],
            "invalidated": bool(failed),
            "failed_checks": failed,
            "checks": checks,
        }


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(decision: dict) -> str:
    lines = [
        "# Context OS Draft Approval Decision",
        "",
        f"- Schema: `{decision['schema']}`",
        f"- Decision: `{decision['id']}`",
        f"- Outcome: {decision['approval']['label']}",
        f"- Success: {yes_no(decision['result']['success'])}",
        f"- Draft: `{decision['draft']['draft_item_id']}`",
        f"- Draft path: `{decision['draft']['draft_path']}`",
        f"- Approver: {decision['approver']['approved_by']} ({decision['approver']['approver_role']})",
        f"- Authority: {decision['approver']['authority_level']} `{decision['approver']['capability']}`",
        f"- Promotion eligible: {yes_no(decision['promotion']['eligible_for_future_promotion_proposal'])}",
        f"- Promotion authorized: {yes_no(decision['promotion']['promotion_authorized'])}",
        f"- Canonical: {yes_no(decision['approval']['canonical'])}",
        "",
        "## Boundary",
        "- Review Decision is not Approval Decision.",
        "- Approval Decision is not promotion.",
        "- Promotion is not canonical truth until separately governed and validated.",
        "- Draft remains non-canonical organizational context.",
        "- Canonical SSOT remains unchanged.",
        "",
        "## Rationale",
        decision["approval"]["rationale"],
        "",
        "## Preserved Uncertainty",
        f"- Unknowns: {len(decision['evidence']['unknowns'])}",
        f"- Missing evidence: {len(decision['evidence']['missing_evidence'])}",
        f"- Contradictions: {len(decision['evidence']['contradictions'])}",
        "",
        "## Result",
        f"- State: `{decision['result']['state']}`",
        f"- Failed checks: {decision['result']['failed_check_count']}",
    ]
    return "\n".join(lines) + "\n"
