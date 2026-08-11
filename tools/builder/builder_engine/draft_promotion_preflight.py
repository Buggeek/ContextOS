from __future__ import annotations

import json
import sys
from pathlib import Path

from builder_engine.draft_approval_decision import SCHEMA as APPROVAL_SCHEMA
from builder_engine.draft_approval_decision import approval_decision_id, approval_decision_payload
from builder_engine.draft_workspace import path_state, stable_hash
from builder_engine.report_builder import generated_timestamp


TOOLS_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from engine.validator_engine import ValidatorEngine  # noqa: E402


SCHEMA = "contextos.builder.draft_promotion_preflight/1"
DEFAULT_PROMOTION_SCOPE = "draft_to_canonical_promotion_proposal"
ALLOWED_CANONICAL_POLICIES = {"create_only", "governed_replacement_review"}


def approval_decision_identity_valid(approval_decision: dict) -> bool:
    return approval_decision.get("id") == approval_decision_id(approval_decision) and approval_decision.get("identity_hash") == stable_hash(
        approval_decision_payload(approval_decision)
    )


def preflight_payload(preflight: dict) -> dict:
    return {
        "schema": preflight["schema"],
        "approval_decision": preflight["approval_decision"],
        "review_decision": preflight["review_decision"],
        "draft": preflight["draft"],
        "source": preflight["source"],
        "promotion_scope": preflight["promotion_scope"],
        "canonical_target": preflight["canonical_target"],
        "canonical_write_set": preflight["canonical_write_set"],
        "evidence": preflight["evidence"],
        "eligibility": preflight["eligibility"],
        "boundaries": preflight["boundaries"],
    }


def preflight_id(preflight: dict) -> str:
    return f"builder.draft_promotion_preflight.{stable_hash(preflight_payload(preflight))[:16]}"


def check(identifier: str, passed: bool, evidence: dict) -> dict:
    return {"id": identifier, "passed": bool(passed), "evidence": evidence}


def write_json_report(path: str | Path, report: dict) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_action_for(target_state: dict, canonical_policy: str) -> dict:
    if not target_state["exists"]:
        return {
            "action_type": "create_canonical_candidate",
            "policy": "create_only",
            "no_overwrite_satisfied": True,
            "governed_replacement_policy_satisfied": False,
        }
    return {
        "action_type": "propose_governed_replacement_candidate",
        "policy": canonical_policy,
        "no_overwrite_satisfied": False,
        "governed_replacement_policy_satisfied": canonical_policy == "governed_replacement_review",
    }


class BuilderDraftPromotionPreflightEngine:
    """Read-only gate before an approved draft can be considered for promotion."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        approval_decision: dict,
        *,
        promotion_scope: str = DEFAULT_PROMOTION_SCOPE,
        canonical_policy: str = "governed_replacement_review",
        generated_at: str | None = None,
    ) -> dict:
        if approval_decision.get("schema") != APPROVAL_SCHEMA:
            raise ValueError("Draft promotion preflight requires contextos.builder.draft_approval_decision/1 input.")
        if promotion_scope != DEFAULT_PROMOTION_SCOPE:
            raise ValueError(f"Unsupported promotion scope: {promotion_scope}")
        if canonical_policy not in ALLOWED_CANONICAL_POLICIES:
            raise ValueError(f"Unsupported canonical policy: {canonical_policy}")

        root = self.root.resolve()
        before = self._file_snapshot(root)
        timestamp = generated_at or generated_timestamp()
        draft_path = root / approval_decision["draft"]["draft_path"]
        target_path = root / approval_decision["draft"]["target_context_artifact"]
        draft_state = path_state(draft_path)
        target_state = path_state(target_path)
        approval_target_state = approval_decision.get("evidence", {}).get("repository_state", {}).get("canonical_target_state")
        validator_report = ValidatorEngine(root).run(mode="gate")
        canonical_action = canonical_action_for(target_state, canonical_policy)
        contradictions = approval_decision.get("evidence", {}).get("contradictions", [])
        checks = [
            check(
                "draft_promotion_preflight.check.approval_decision_identity_valid",
                approval_decision_identity_valid(approval_decision),
                {"approval_decision_id": approval_decision.get("id"), "identity_hash": approval_decision.get("identity_hash")},
            ),
            check(
                "draft_promotion_preflight.check.review_decision_identity_bound",
                bool(approval_decision.get("review_decision", {}).get("id"))
                and bool(approval_decision.get("review_decision", {}).get("identity_hash")),
                approval_decision.get("review_decision", {}),
            ),
            check(
                "draft_promotion_preflight.check.approval_successful",
                approval_decision.get("result", {}).get("success") is True
                and approval_decision.get("approval", {}).get("approval_granted") is True,
                approval_decision.get("result", {}),
            ),
            check(
                "draft_promotion_preflight.check.approved_for_promotion_proposal",
                approval_decision.get("approval", {}).get("value") == "approved_for_promotion_proposal"
                and approval_decision.get("promotion", {}).get("eligible_for_future_promotion_proposal") is True,
                {"approval": approval_decision.get("approval", {}), "promotion": approval_decision.get("promotion", {})},
            ),
            check(
                "draft_promotion_preflight.check.promotion_not_already_authorized",
                approval_decision.get("promotion", {}).get("promotion_authorized") is False
                and approval_decision.get("promotion", {}).get("canonical_write_authorized") is False,
                approval_decision.get("promotion", {}),
            ),
            check(
                "draft_promotion_preflight.check.draft_hash_unchanged_since_approval",
                draft_state.get("hash") == approval_decision.get("draft", {}).get("content_hash"),
                {"current": draft_state, "approved_hash": approval_decision.get("draft", {}).get("content_hash")},
            ),
            check(
                "draft_promotion_preflight.check.draft_workspace_path_exact",
                approval_decision.get("draft", {}).get("draft_path", "").startswith(".contextos/drafts/")
                and draft_state.get("exists") is True,
                {"draft_path": approval_decision.get("draft", {}).get("draft_path"), "current": draft_state},
            ),
            check(
                "draft_promotion_preflight.check.builder_draft_plan_identity_bound",
                bool(approval_decision.get("source", {}).get("builder_draft_plan_hash")),
                {"builder_draft_plan_hash": approval_decision.get("source", {}).get("builder_draft_plan_hash")},
            ),
            check(
                "draft_promotion_preflight.check.discovery_construction_provenance_bound",
                bool(approval_decision.get("source", {}).get("discovery_fingerprint"))
                and bool(approval_decision.get("source", {}).get("construction_candidate_id")),
                {
                    "discovery_fingerprint": approval_decision.get("source", {}).get("discovery_fingerprint"),
                    "construction_candidate_id": approval_decision.get("source", {}).get("construction_candidate_id"),
                },
            ),
            check(
                "draft_promotion_preflight.check.approval_authority_remains_valid",
                approval_decision.get("approver", {}).get("authority_level") == "L3"
                and approval_decision.get("approver", {}).get("capability") == "builder.draft.approve"
                and approval_decision.get("approver", {}).get("role_satisfied") is True,
                approval_decision.get("approver", {}),
            ),
            check(
                "draft_promotion_preflight.check.no_unresolved_contradictions",
                len(contradictions) == 0,
                {"contradiction_count": len(contradictions)},
            ),
            check(
                "draft_promotion_preflight.check.unknowns_missing_evidence_preserved",
                isinstance(approval_decision.get("evidence", {}).get("unknowns"), list)
                and isinstance(approval_decision.get("evidence", {}).get("missing_evidence"), list),
                {
                    "unknown_count": len(approval_decision.get("evidence", {}).get("unknowns", [])),
                    "missing_evidence_count": len(approval_decision.get("evidence", {}).get("missing_evidence", [])),
                },
            ),
            check(
                "draft_promotion_preflight.check.target_canonical_path_explicit",
                bool(approval_decision.get("draft", {}).get("target_context_artifact")),
                {"target_context_artifact": approval_decision.get("draft", {}).get("target_context_artifact")},
            ),
            check(
                "draft_promotion_preflight.check.target_canonical_state_unchanged_since_approval",
                approval_target_state is not None and target_state == approval_target_state,
                {"current": target_state, "approval_baseline": approval_target_state},
            ),
            check(
                "draft_promotion_preflight.check.no_overwrite_or_replacement_policy_satisfied",
                canonical_action["no_overwrite_satisfied"] or canonical_action["governed_replacement_policy_satisfied"],
                canonical_action,
            ),
            check(
                "draft_promotion_preflight.check.promotion_scope_explicit",
                promotion_scope == DEFAULT_PROMOTION_SCOPE,
                {"promotion_scope": promotion_scope},
            ),
            check(
                "draft_promotion_preflight.check.validator_gate_satisfied",
                validator_report["summary"]["error"] == 0 and validator_report["summary"]["fatal"] == 0,
                validator_report["summary"],
            ),
        ]
        after = self._file_snapshot(root)
        checks.append(check("draft_promotion_preflight.check.read_only_unchanged", before == after, {"file_state_unchanged": before == after}))
        failed_checks = [entry["id"] for entry in checks if not entry["passed"]]
        preflight = {
            "schema": SCHEMA,
            "id": "",
            "identity_hash": "",
            "generated_at": timestamp,
            "root": str(root),
            "read_only": True,
            "approval_decision": {
                "schema": approval_decision["schema"],
                "id": approval_decision["id"],
                "identity_hash": approval_decision["identity_hash"],
                "identity_valid": approval_decision_identity_valid(approval_decision),
            },
            "review_decision": approval_decision["review_decision"],
            "draft": {
                "draft_item_id": approval_decision["draft"]["draft_item_id"],
                "draft_path": approval_decision["draft"]["draft_path"],
                "draft_workspace_location": approval_decision["draft"]["draft_workspace_location"],
                "target_context_artifact": approval_decision["draft"]["target_context_artifact"],
                "target_identity": approval_decision["draft"]["target_identity"],
                "approved_content_hash": approval_decision["draft"]["content_hash"],
                "current_content_hash": draft_state.get("hash"),
                "state": draft_state,
                "approved": approval_decision["draft"]["approval_recorded"],
                "promoted": False,
                "canonical": False,
            },
            "source": approval_decision["source"],
            "promotion_scope": {
                "value": promotion_scope,
                "approved_scope": approval_decision["approval"]["scope"],
                "promotion_authorized": False,
                "canonical_mutation_authorized": False,
            },
            "canonical_target": {
                "path": approval_decision["draft"]["target_context_artifact"],
                "approval_baseline_state": approval_target_state,
                "current_state": target_state,
                "unchanged_since_approval": approval_target_state is not None and target_state == approval_target_state,
            },
            "canonical_write_set": {
                "frozen": True,
                "count": 1,
                "items": [
                    {
                        "draft_item_id": approval_decision["draft"]["draft_item_id"],
                        "source_draft_path": approval_decision["draft"]["draft_path"],
                        "source_draft_hash": approval_decision["draft"]["content_hash"],
                        "target_canonical_path": approval_decision["draft"]["target_context_artifact"],
                        "action_type": canonical_action["action_type"],
                        "canonical_policy": canonical_action["policy"],
                        "explainable": True,
                        "promotion_authorized": False,
                        "canonical_mutation_authorized": False,
                    }
                ],
            },
            "evidence": {
                "checks": checks,
                "validator": {"schema": validator_report["schema"], "summary": validator_report["summary"]},
                "evidence_refs": approval_decision["evidence"]["evidence_refs"],
                "support": approval_decision["evidence"]["support"],
                "unknowns": approval_decision["evidence"]["unknowns"],
                "missing_evidence": approval_decision["evidence"]["missing_evidence"],
                "contradictions": contradictions,
                "reviewer_rationale": approval_decision["evidence"]["reviewer_rationale"],
                "approver_rationale": approval_decision["evidence"]["approver_rationale"],
            },
            "eligibility": {
                "eligible_for_promotion": not failed_checks,
                "promotion_authorized": False,
                "canonical_mutation_authorized": False,
                "failed_check_count": len(failed_checks),
                "failed_checks": failed_checks,
            },
            "rollback_recovery": {
                "known": True,
                "strategy": "future_promotion_must_record_inverse_or_restore_plan_before_mutation",
                "preflight_performs_rollback": False,
                "must_not_remove_draft_workspace_evidence": True,
                "must_not_mutate_canonical_context_in_preflight": True,
            },
            "invalidation": {
                "invalidated_by": [
                    "approval_decision_identity_changed",
                    "review_decision_identity_changed",
                    "draft_content_hash_changed",
                    "draft_workspace_path_changed",
                    "builder_draft_plan_hash_changed",
                    "discovery_or_construction_provenance_changed",
                    "canonical_target_state_changed",
                    "validator_gate_changed",
                    "approval_authority_changed",
                    "promotion_scope_changed",
                ],
                "silent_regeneration_allowed": False,
                "silent_reinterpretation_allowed": False,
            },
            "boundaries": {
                "approved_is_not_promoted": True,
                "promoted_is_not_canonical_until_validated": True,
                "promotion_authorized": False,
                "canonical_mutation_authorized": False,
                "ssot_writes_performed": False,
                "canonical_context_writes_performed": False,
                "draft_content_mutated": False,
                "knowledge_engine_used": False,
                "graph_runtime_used": False,
                "agents_used": False,
                "external_connectors_used": False,
            },
            "result": {
                "state": "promotion_preflight_eligible" if not failed_checks else "blocked",
                "success": not failed_checks,
            },
        }
        preflight["id"] = preflight_id(preflight)
        preflight["identity_hash"] = stable_hash(preflight_payload(preflight))
        return preflight

    def _file_snapshot(self, root: Path) -> dict[str, dict]:
        return {path.relative_to(root).as_posix(): path_state(path) for path in root.rglob("*") if path.is_file()}


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(preflight: dict) -> str:
    eligibility = preflight["eligibility"]
    write_item = preflight["canonical_write_set"]["items"][0]
    lines = [
        "# Context OS Draft Promotion Preflight",
        "",
        f"- Schema: `{preflight['schema']}`",
        f"- Preflight: `{preflight['id']}`",
        f"- Eligible for promotion: {yes_no(eligibility['eligible_for_promotion'])}",
        f"- Promotion authorized: {yes_no(eligibility['promotion_authorized'])}",
        f"- Canonical mutation authorized: {yes_no(eligibility['canonical_mutation_authorized'])}",
        f"- Draft: `{preflight['draft']['draft_item_id']}`",
        f"- Draft path: `{preflight['draft']['draft_path']}`",
        f"- Target canonical path: `{preflight['canonical_target']['path']}`",
        f"- Frozen write action: `{write_item['action_type']}`",
        "",
        "## Boundary",
        "- Approved is not promoted.",
        "- Promoted is not canonical truth until separately validated.",
        "- This preflight performs no promotion, SSOT write, or canonical mutation.",
        "",
        "## Evidence",
        f"- Evidence refs: {len(preflight['evidence']['evidence_refs'])}",
        f"- Unknowns preserved: {len(preflight['evidence']['unknowns'])}",
        f"- Missing evidence preserved: {len(preflight['evidence']['missing_evidence'])}",
        f"- Contradictions: {len(preflight['evidence']['contradictions'])}",
        f"- Validator errors/fatals: {preflight['evidence']['validator']['summary']['error']}/"
        f"{preflight['evidence']['validator']['summary']['fatal']}",
        "",
        "## Result",
        f"- State: `{preflight['result']['state']}`",
        f"- Failed checks: {eligibility['failed_check_count']}",
    ]
    return "\n".join(lines) + "\n"
