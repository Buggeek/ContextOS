from __future__ import annotations

import json
import sys
from pathlib import Path

from builder_engine.draft_create import role_satisfies
from builder_engine.draft_promotion_preflight import SCHEMA as PREFLIGHT_SCHEMA
from builder_engine.draft_promotion_preflight import preflight_id, preflight_payload
from builder_engine.draft_review import body_after_metadata
from builder_engine.draft_workspace import path_state, stable_hash
from builder_engine.report_builder import generated_timestamp


TOOLS_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from engine.validator_engine import ValidatorEngine  # noqa: E402


SCHEMA = "contextos.builder.draft_promotion_result/1"
ROLLBACK_SCHEMA = "contextos.builder.draft_promotion_rollback_result/1"
REQUIRED_AUTHORITY_LEVEL = "L3"
REQUIRED_CAPABILITY = "builder.draft.promote"
REQUIRED_SCOPE = "create_canonical_from_approved_draft"


def preflight_identity_valid(preflight: dict) -> bool:
    return preflight.get("id") == preflight_id(preflight) and preflight.get("identity_hash") == stable_hash(preflight_payload(preflight))


def promotion_result_payload(result: dict) -> dict:
    return {
        "schema": result["schema"],
        "preflight": result["preflight"],
        "confirmation": result["confirmation"],
        "canonical_write_set": result["canonical_write_set"],
        "mutations": result["mutations"],
        "validation": result["validation"],
        "result": result["result"],
    }


def promotion_result_id(result: dict) -> str:
    return f"builder.draft_promotion_result.{stable_hash(promotion_result_payload(result))[:16]}"


def check(identifier: str, passed: bool, evidence: dict) -> dict:
    return {"id": identifier, "passed": bool(passed), "evidence": evidence}


def canonical_document(preflight: dict, confirmation: dict, draft_content: str, generated_at: str, *, canonical_verified: bool) -> str:
    item = preflight["canonical_write_set"]["items"][0]
    target_name = Path(item["target_canonical_path"]).name
    artifact_id = target_name.removesuffix(".md").split("_", 1)[0]
    title_words = target_name.removesuffix(".md").replace("_", " ")
    metadata = {
        "schema": "contextos.builder.promoted_canonical_artifact/1",
        "canonical": canonical_verified,
        "canonical_verified": canonical_verified,
        "lifecycle_state": "canonical_verified" if canonical_verified else "promoted_pending_validation",
        "generated_by": SCHEMA,
        "generated_at": generated_at,
        "mission_id": confirmation["promotion_mission_id"],
        "promoted_by": confirmation["promoted_by"],
        "promoter_role": confirmation["promoter_role"],
        "source_promotion_preflight_id": preflight["id"],
        "source_promotion_preflight_hash": preflight["identity_hash"],
        "source_approval_decision_id": preflight["approval_decision"]["id"],
        "source_approval_decision_hash": preflight["approval_decision"]["identity_hash"],
        "source_review_decision_id": preflight["review_decision"]["id"],
        "source_review_decision_hash": preflight["review_decision"]["identity_hash"],
        "source_builder_draft_plan_hash": preflight["source"]["builder_draft_plan_hash"],
        "source_discovery_fingerprint": preflight["source"]["discovery_fingerprint"],
        "source_construction_candidate_id": preflight["source"]["construction_candidate_id"],
        "source_draft_path": item["source_draft_path"],
        "source_draft_hash": item["source_draft_hash"],
        "target_canonical_path": item["target_canonical_path"],
        "promotion_scope": confirmation["canonical_mutation_scope"],
        "promotion_action": item["action_type"],
        "evidence_refs": preflight["evidence"]["evidence_refs"],
        "unknowns": preflight["evidence"]["unknowns"],
        "missing_evidence": preflight["evidence"]["missing_evidence"],
        "contradictions": preflight["evidence"]["contradictions"],
        "approved_content_hash": stable_hash(draft_content),
        "epistemic_boundary": "canonical_verified_by_validator" if canonical_verified else "approved_draft_promoted_pending_canonical_validation",
    }
    return "\n".join(
        [
            f"# {artifact_id} {title_words}",
            "## Version: 0.1.0",
            f"Owner: {confirmation['promoter_role']}",
            "",
            "---",
            "",
            "> Canonical promotion candidate created from an approved Draft Workspace artifact.",
            "> Canonical verification is recorded only after post-promotion Validator evidence succeeds.",
            "",
            "```json",
            json.dumps(metadata, indent=2, sort_keys=True),
            "```",
            "",
            "## Approved Draft Content",
            "",
            draft_content.rstrip(),
            "",
        ]
    )


def parent_dirs_to_create(root: Path, target: Path) -> list[Path]:
    missing: list[Path] = []
    current = target.parent
    while current != root and not current.exists():
        missing.append(current)
        current = current.parent
    return list(reversed(missing))


class BuilderDraftPromotionEngine:
    """Create-only canonical promotion from a fresh eligible promotion preflight."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        preflight: dict,
        *,
        confirm_promotion: bool,
        promoted_by: str,
        promoter_role: str,
        promoter_authority_level: str,
        promoter_capability: str,
        promotion_mission_id: str,
        authorized_preflight_id: str,
        authorized_preflight_hash: str,
        authorized_approval_decision_id: str,
        authorized_approval_decision_hash: str,
        authorized_draft_item_id: str,
        authorized_draft_content_hash: str,
        authorized_canonical_target_path: str,
        authorized_promotion_action: str,
        authorized_canonical_target_state_hash: str | None,
        canonical_mutation_scope: str,
        generated_at: str | None = None,
    ) -> dict:
        if preflight.get("schema") != PREFLIGHT_SCHEMA:
            raise ValueError("Draft promotion requires contextos.builder.draft_promotion_preflight/1 input.")
        if not confirm_promotion:
            raise ValueError("Draft promotion requires explicit human promotion confirmation.")
        if not promoted_by or not promoted_by.strip():
            raise ValueError("Draft promotion requires explicit promoting human identity.")
        if not promoter_role or not promoter_role.strip():
            raise ValueError("Draft promotion requires explicit promoting role.")

        root = self.root.resolve()
        timestamp = generated_at or generated_timestamp()
        before = self._file_snapshot(root)
        item = preflight["canonical_write_set"]["items"][0]
        draft_path = root / item["source_draft_path"]
        target_path = root / item["target_canonical_path"]
        current_draft_state = path_state(draft_path)
        current_target_state = path_state(target_path)
        required_roles = sorted(
            dict.fromkeys(
                role
                for role in [
                    preflight.get("approval_decision", {}).get("id") and "Product Owner",
                    preflight.get("evidence", {}).get("support", {}).get("required_role"),
                ]
                if role
            )
        )
        if not required_roles:
            required_roles = ["Product Owner"]
        confirmation = {
            "confirmed": True,
            "promoted_by": promoted_by.strip(),
            "promoter_role": promoter_role.strip(),
            "promoter_authority_level": promoter_authority_level,
            "promoter_capability": promoter_capability,
            "promotion_mission_id": promotion_mission_id,
            "authorized_preflight_id": authorized_preflight_id,
            "authorized_preflight_hash": authorized_preflight_hash,
            "authorized_approval_decision_id": authorized_approval_decision_id,
            "authorized_approval_decision_hash": authorized_approval_decision_hash,
            "authorized_draft_item_id": authorized_draft_item_id,
            "authorized_draft_content_hash": authorized_draft_content_hash,
            "authorized_canonical_target_path": authorized_canonical_target_path,
            "authorized_promotion_action": authorized_promotion_action,
            "authorized_canonical_target_state_hash": authorized_canonical_target_state_hash,
            "canonical_mutation_scope": canonical_mutation_scope,
            "required_roles": required_roles,
            "role_satisfied": role_satisfies(promoter_role, required_roles),
        }
        pre_checks = self._pre_write_checks(preflight, confirmation, current_draft_state, current_target_state)
        failed_pre_checks = [entry["id"] for entry in pre_checks if not entry["passed"]]
        mutations: list[dict] = []
        errors: list[dict] = []
        result_state = "blocked"

        if not failed_pre_checks:
            try:
                draft_content = draft_path.read_text(encoding="utf-8")
                body = body_after_metadata(draft_content)
                dirs = parent_dirs_to_create(root, target_path)
                for directory in dirs:
                    directory.mkdir()
                content = canonical_document(preflight, confirmation, body, timestamp, canonical_verified=False)
                before_target = path_state(target_path)
                if before_target["exists"]:
                    raise ValueError(f"Promotion refused to overwrite existing canonical target: {item['target_canonical_path']}")
                target_path.write_text(content, encoding="utf-8")
                after_target = path_state(target_path)
                mutations.append(
                    {
                        "draft_item_id": item["draft_item_id"],
                        "action_type": item["action_type"],
                        "source_draft_path": item["source_draft_path"],
                        "source_draft_hash": item["source_draft_hash"],
                        "target_canonical_path": item["target_canonical_path"],
                        "status": "created",
                        "before": before_target,
                        "after": after_target,
                        "created_directories": [directory.relative_to(root).as_posix() for directory in dirs],
                        "rollback": {
                            "available": True,
                            "strategy": "delete_created_if_hash_matches",
                            "remove_only_if_hash": after_target["hash"],
                            "remove_empty_created_directories": True,
                        },
                        "provenance": {
                            "promotion_preflight_id": preflight["id"],
                            "promotion_preflight_hash": preflight["identity_hash"],
                            "approval_decision_id": preflight["approval_decision"]["id"],
                            "approval_decision_hash": preflight["approval_decision"]["identity_hash"],
                            "review_decision_id": preflight["review_decision"]["id"],
                            "review_decision_hash": preflight["review_decision"]["identity_hash"],
                            "builder_draft_plan_hash": preflight["source"]["builder_draft_plan_hash"],
                            "discovery_fingerprint": preflight["source"]["discovery_fingerprint"],
                            "construction_candidate_id": preflight["source"]["construction_candidate_id"],
                            "evidence_refs": preflight["evidence"]["evidence_refs"],
                        },
                    }
                )
                result_state = "promoted"
            except (OSError, ValueError) as exc:
                errors.append({"stage": "write", "message": str(exc)})
                result_state = "failed_write"

        post_validator = ValidatorEngine(root).run(mode="gate") if result_state == "promoted" else None
        final_validator = None
        if post_validator is not None:
            if post_validator["summary"]["error"] or post_validator["summary"]["fatal"]:
                result_state = "failed_validation"
            else:
                item = preflight["canonical_write_set"]["items"][0]
                target_path = root / item["target_canonical_path"]
                draft_path = root / item["source_draft_path"]
                body = body_after_metadata(draft_path.read_text(encoding="utf-8"))
                target_path.write_text(canonical_document(preflight, confirmation, body, timestamp, canonical_verified=True), encoding="utf-8")
                final_validator = ValidatorEngine(root).run(mode="gate")
                if final_validator["summary"]["error"] or final_validator["summary"]["fatal"]:
                    result_state = "failed_validation"
                else:
                    result_state = "promoted_validated"
                    final_state = path_state(target_path)
                    for mutation in mutations:
                        if mutation["target_canonical_path"] == item["target_canonical_path"]:
                            mutation["after"] = final_state
                            mutation["rollback"]["remove_only_if_hash"] = final_state["hash"]
        after = self._file_snapshot(root)
        result = {
            "schema": SCHEMA,
            "id": "",
            "identity_hash": "",
            "generated_at": timestamp,
            "root": str(root),
            "preflight": {
                "schema": preflight["schema"],
                "id": preflight["id"],
                "identity_hash": preflight["identity_hash"],
                "approval_decision_id": preflight["approval_decision"]["id"],
                "approval_decision_hash": preflight["approval_decision"]["identity_hash"],
            },
            "confirmation": confirmation,
            "canonical_write_set": preflight["canonical_write_set"],
            "mutations": mutations,
            "validation": {
                "pre_write_checks": pre_checks,
                "post_promotion_validator": {"schema": post_validator["schema"], "summary": post_validator["summary"]}
                if post_validator is not None
                else None,
                "final_canonical_validator": {"schema": final_validator["schema"], "summary": final_validator["summary"]}
                if final_validator is not None
                else None,
                "canonical_validation_succeeded": result_state == "promoted_validated",
            },
            "rollback": {
                "available": bool(mutations),
                "created_artifact_count": len(mutations),
                "strategy": "delete_created_if_hash_matches",
                "will_not_remove_pre_existing_content": True,
            },
            "evidence": {
                "repository_before_file_count": len(before),
                "repository_after_file_count": len(after),
                "unrelated_files_modified": sorted(
                    path
                    for path in set(before) & set(after)
                    if before[path] != after[path] and path not in {item["target_canonical_path"]}
                ),
                "unknowns": preflight["evidence"]["unknowns"],
                "missing_evidence": preflight["evidence"]["missing_evidence"],
                "contradictions": preflight["evidence"]["contradictions"],
            },
            "result": {
                "state": result_state,
                "success": result_state == "promoted_validated",
                "failed_pre_check_count": len(failed_pre_checks),
                "failed_pre_checks": failed_pre_checks,
                "errors": errors,
            },
            "boundaries": {
                "approved_is_not_canonical_without_promotion": True,
                "canonical_status_requires_successful_validation": True,
                "promotion_consumed_exact_preflight": True,
                "regenerated_intent": False,
                "reinterpreted_draft": False,
            },
            "constraints": {
                "create_only": True,
                "overwrites_performed": False,
                "replacements_performed": False,
                "deletions_performed": False,
                "unrelated_files_modified": False,
                "knowledge_engine_used": False,
                "graph_runtime_used": False,
                "agents_used": False,
                "external_connectors_used": False,
            },
        }
        result["id"] = promotion_result_id(result)
        result["identity_hash"] = stable_hash(promotion_result_payload(result))
        return result

    def rollback(self, result: dict) -> dict:
        root = self.root.resolve()
        removed: list[dict] = []
        skipped: list[dict] = []
        for mutation in reversed(result.get("mutations", [])):
            target = root / mutation["target_canonical_path"]
            current = path_state(target)
            rollback = mutation.get("rollback", {})
            if not current["exists"]:
                skipped.append({"target_path": mutation["target_canonical_path"], "reason": "already_missing"})
                continue
            if current["hash"] != rollback.get("remove_only_if_hash"):
                skipped.append({"target_path": mutation["target_canonical_path"], "reason": "current_hash_changed"})
                continue
            target.unlink()
            removed.append({"target_path": mutation["target_canonical_path"], "status": "removed"})
            for directory in reversed(mutation.get("created_directories", [])):
                dir_path = root / directory
                try:
                    dir_path.rmdir()
                except OSError:
                    skipped.append({"target_path": directory, "reason": "directory_not_empty"})
        return {
            "schema": ROLLBACK_SCHEMA,
            "root": str(root),
            "source_promotion_result_id": result["id"],
            "removed": removed,
            "skipped": skipped,
            "constraints": {
                "removed_only_created_artifacts": True,
                "removed_pre_existing_content": False,
                "removed_unrelated_content": False,
            },
        }

    def _pre_write_checks(self, preflight: dict, confirmation: dict, current_draft_state: dict, current_target_state: dict) -> list[dict]:
        item = preflight["canonical_write_set"]["items"][0]
        validator_report = ValidatorEngine(self.root).run(mode="gate")
        return [
            check(
                "draft_promotion.check.preflight_identity_valid",
                preflight_identity_valid(preflight),
                {"preflight_id": preflight.get("id"), "identity_hash": preflight.get("identity_hash")},
            ),
            check("draft_promotion.check.preflight_eligible", preflight["eligibility"]["eligible_for_promotion"], preflight["eligibility"]),
            check(
                "draft_promotion.check.confirmation_bound_to_preflight",
                confirmation["authorized_preflight_id"] == preflight["id"]
                and confirmation["authorized_preflight_hash"] == preflight["identity_hash"],
                {"authorized_preflight_id": confirmation["authorized_preflight_id"]},
            ),
            check(
                "draft_promotion.check.confirmation_bound_to_approval_decision",
                confirmation["authorized_approval_decision_id"] == preflight["approval_decision"]["id"]
                and confirmation["authorized_approval_decision_hash"] == preflight["approval_decision"]["identity_hash"],
                {"authorized_approval_decision_id": confirmation["authorized_approval_decision_id"]},
            ),
            check(
                "draft_promotion.check.confirmation_bound_to_draft",
                confirmation["authorized_draft_item_id"] == item["draft_item_id"]
                and confirmation["authorized_draft_content_hash"] == item["source_draft_hash"],
                {"authorized_draft_item_id": confirmation["authorized_draft_item_id"]},
            ),
            check(
                "draft_promotion.check.confirmation_bound_to_canonical_target",
                confirmation["authorized_canonical_target_path"] == item["target_canonical_path"]
                and confirmation["authorized_canonical_target_state_hash"] == preflight["canonical_target"]["current_state"]["hash"],
                {"authorized_canonical_target_path": confirmation["authorized_canonical_target_path"]},
            ),
            check(
                "draft_promotion.check.confirmation_bound_to_frozen_action",
                confirmation["authorized_promotion_action"] == item["action_type"],
                {"authorized_action": confirmation["authorized_promotion_action"], "preflight_action": item["action_type"]},
            ),
            check(
                "draft_promotion.check.explicit_l3_promotion_authority",
                confirmation["promoter_authority_level"] == REQUIRED_AUTHORITY_LEVEL
                and confirmation["promoter_capability"] == REQUIRED_CAPABILITY
                and confirmation["role_satisfied"],
                {
                    "authority_level": confirmation["promoter_authority_level"],
                    "capability": confirmation["promoter_capability"],
                    "role_satisfied": confirmation["role_satisfied"],
                },
            ),
            check(
                "draft_promotion.check.scope_is_create_only",
                confirmation["canonical_mutation_scope"] == REQUIRED_SCOPE,
                {"canonical_mutation_scope": confirmation["canonical_mutation_scope"]},
            ),
            check(
                "draft_promotion.check.action_is_create_canonical_candidate",
                item["action_type"] == "create_canonical_candidate",
                {"action_type": item["action_type"]},
            ),
            check("draft_promotion.check.no_existing_canonical_target", current_target_state["exists"] is False, current_target_state),
            check(
                "draft_promotion.check.draft_hash_still_matches_preflight",
                current_draft_state.get("hash") == item["source_draft_hash"],
                {"current": current_draft_state, "preflight_hash": item["source_draft_hash"]},
            ),
            check(
                "draft_promotion.check.no_unresolved_contradictions",
                len(preflight["evidence"]["contradictions"]) == 0,
                {"contradiction_count": len(preflight["evidence"]["contradictions"])},
            ),
            check(
                "draft_promotion.check.validator_gate_satisfied_before_write",
                validator_report["summary"]["error"] == 0 and validator_report["summary"]["fatal"] == 0,
                validator_report["summary"],
            ),
        ]

    def _file_snapshot(self, root: Path) -> dict[str, dict]:
        return {path.relative_to(root).as_posix(): path_state(path) for path in root.rglob("*") if path.is_file()}


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(result: dict) -> str:
    lines = [
        "# Context OS Draft Promotion Result",
        "",
        f"- Schema: `{result['schema']}`",
        f"- Result: `{result['id']}`",
        f"- State: `{result['result']['state']}`",
        f"- Success: {yes_no(result['result']['success'])}",
        f"- Mutations: {len(result['mutations'])}",
        f"- Canonical validation succeeded: {yes_no(result['validation']['canonical_validation_succeeded'])}",
        "",
        "## Boundary",
        "- Approved is not canonical until promotion executes and validation succeeds.",
        "- Promotion consumed the exact eligible preflight.",
        "- No replacement, overwrite, delete, Knowledge Engine, Graph, agents, or external connectors were used.",
        "",
        "## Rollback",
        f"- Available: {yes_no(result['rollback']['available'])}",
        f"- Strategy: `{result['rollback']['strategy']}`",
        "",
        "## Result",
        f"- Failed pre-checks: {result['result']['failed_pre_check_count']}",
    ]
    return "\n".join(lines) + "\n"
