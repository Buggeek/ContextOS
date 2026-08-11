from __future__ import annotations

import json
import sys
from pathlib import Path

from builder_engine.draft_workspace import (
    SCHEMA as PREFLIGHT_SCHEMA,
    canonical_json,
    path_state,
    preflight_id,
    preflight_payload,
    stable_hash,
)
from builder_engine.report_builder import generated_timestamp


TOOLS_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from engine.validator_engine import ValidatorEngine  # noqa: E402


SCHEMA = "contextos.builder.draft_write_result/1"
ROLLBACK_SCHEMA = "contextos.builder.draft_rollback_result/1"


def role_options(required_role: str) -> list[str]:
    return [part.strip() for part in required_role.split(" or ") if part.strip()]


def role_satisfies(authorized_role: str, required_roles: list[str]) -> bool:
    normalized = authorized_role.strip().lower()
    for required in required_roles:
        if normalized == required.strip().lower():
            return True
        for option in role_options(required):
            if normalized == option.lower():
                return True
    return False


def draft_write_payload(result: dict) -> dict:
    return {
        "schema": result["schema"],
        "preflight": result["preflight"],
        "authorization": result["authorization"],
        "draft_set": result["draft_set"],
        "result": result["result"],
    }


def draft_write_result_id(result: dict) -> str:
    return f"builder.draft_write_result.{stable_hash(draft_write_payload(result))[:16]}"


def file_hash(path: str | Path | None) -> str | None:
    if path is None:
        return None
    target = Path(path)
    if not target.is_file():
        return None
    import hashlib

    digest = hashlib.sha256()
    with target.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def preflight_identity_valid(preflight: dict) -> bool:
    return preflight.get("id") == preflight_id(preflight) and preflight.get("identity_hash") == stable_hash(preflight_payload(preflight))


def passed_all(checks: list[dict]) -> bool:
    return all(check["passed"] for check in checks)


def target_by_id(preflight: dict) -> dict[str, dict]:
    return {target["draft_item_id"]: target for target in preflight.get("targets", [])}


def selected_targets(preflight: dict, draft_item_ids: list[str]) -> list[dict]:
    targets = target_by_id(preflight)
    return [targets[item_id] for item_id in draft_item_ids if item_id in targets]


def required_roles_for(targets: list[dict]) -> list[str]:
    return sorted(dict.fromkeys(target["authority_required"]["role"] for target in targets))


def validation_checks_passed(preflight: dict) -> bool:
    validation = preflight.get("validation", {})
    return (
        passed_all(validation.get("workspace_checks", []))
        and passed_all(validation.get("drift_checks", []))
        and passed_all(validation.get("validator_checks", []))
    )


def target_still_missing(root: Path, target: dict) -> bool:
    return not path_state(root / target["draft_workspace_target_path"])["exists"]


def target_path_allowed(target: dict, authorized_paths: list[str]) -> bool:
    return target["draft_workspace_target_path"] in set(authorized_paths)


def target_item_allowed(target: dict, authorized_item_ids: list[str]) -> bool:
    return target["draft_item_id"] in set(authorized_item_ids)


def parent_dirs_to_create(root: Path, target: Path) -> list[Path]:
    missing: list[Path] = []
    current = target.parent
    while current != root and not current.exists():
        missing.append(current)
        current = current.parent
    return list(reversed(missing))


def draft_document(preflight: dict, target: dict, authorization: dict, generated_at: str) -> str:
    metadata = {
        "schema": "contextos.builder.draft_artifact/1",
        "lifecycle_state": "draft",
        "canonical": False,
        "truth_status": "non_canonical_unreviewed_draft",
        "generated_by": SCHEMA,
        "generated_at": generated_at,
        "mission_id": authorization["authorized_mission_id"],
        "authorized_by": authorization["authorized_by"],
        "authorized_role": authorization["authorized_role"],
        "source_preflight_id": preflight["id"],
        "source_preflight_hash": preflight["identity_hash"],
        "source_builder_draft_plan_hash": preflight["source_plan"]["hash"],
        "draft_item_id": target["draft_item_id"],
        "target_context_artifact": target["target_context_artifact"],
        "target_identity": target["target_identity"],
        "artifact_class": target["artifact_class"],
        "operation_domain": target["operation_domain"],
        "plan_binding": target["plan_binding"],
        "unknowns": target["truth_boundaries"]["unknowns_preserved"],
        "missing_evidence": target["truth_boundaries"]["missing_evidence_preserved"],
        "contradictions": target["truth_boundaries"]["contradictions_preserved"],
        "promotion_authorized": False,
        "reviewed": False,
        "approved": False,
        "canonical_verified": False,
    }
    return "\n".join(
        [
            "# Context OS Draft Artifact",
            "",
            "> Non-canonical draft. This file is not reviewed, approved, or verified organizational truth.",
            "",
            "```json",
            json.dumps(metadata, indent=2, sort_keys=True),
            "```",
            "",
            "## Draft Content",
            "",
            "No organizational truth has been generated in this slice.",
            "Future Builder behavior may add evidence-supported draft content under separate authority.",
            "",
        ]
    )


def write_target(root: Path, preflight: dict, target: dict, authorization: dict, generated_at: str) -> dict:
    target_path = root / target["draft_workspace_target_path"]
    before = path_state(target_path)
    if before["exists"]:
        raise ValueError(f"Builder draft write refused to overwrite existing path: {target['draft_workspace_target_path']}")
    dirs = parent_dirs_to_create(root, target_path)
    for directory in dirs:
        directory.mkdir()
    content = draft_document(preflight, target, authorization, generated_at)
    target_path.write_text(content, encoding="utf-8")
    after = path_state(target_path)
    return {
        "draft_item_id": target["draft_item_id"],
        "target_path": target["draft_workspace_target_path"],
        "target_context_artifact": target["target_context_artifact"],
        "status": "created",
        "before": before,
        "after": after,
        "created_directories": [directory.relative_to(root).as_posix() for directory in dirs],
        "rollback": {
            "available": True,
            "strategy": "delete_created_if_hash_matches",
            "remove_only_if_hash": after["hash"],
            "remove_empty_created_directories": True,
        },
        "provenance": {
            "preflight_id": preflight["id"],
            "preflight_hash": preflight["identity_hash"],
            "builder_draft_plan_hash": preflight["source_plan"]["hash"],
            "target_identity": target["target_identity"],
            "evidence_refs": target["plan_binding"]["evidence_refs"],
        },
    }


class BuilderDraftCreateEngine:
    """Create-only Builder draft writer gated by Draft Workspace preflight."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        preflight: dict,
        *,
        preflight_ref: str | None = None,
        confirm_create: bool,
        authorized_by: str,
        authorized_role: str,
        authorized_authority_level: str,
        authorized_capability: str,
        authorized_mission_id: str,
        authorized_preflight_id: str,
        authorized_preflight_hash: str,
        authorized_builder_draft_plan_hash: str,
        authorized_draft_item_ids: list[str],
        authorized_target_paths: list[str],
        generated_at: str | None = None,
    ) -> dict:
        if preflight.get("schema") != PREFLIGHT_SCHEMA:
            raise ValueError("Builder draft creation requires contextos.builder.draft_workspace_preflight/1 input.")
        if not confirm_create:
            raise ValueError("Builder draft creation requires explicit create confirmation.")
        if not authorized_by or not authorized_by.strip():
            raise ValueError("Builder draft creation requires explicit authorizing human identity.")
        if not authorized_role or not authorized_role.strip():
            raise ValueError("Builder draft creation requires explicit authorizing role.")
        if authorized_authority_level != "L2":
            raise ValueError("Builder draft creation requires explicit L2 authority.")
        if authorized_capability != "builder.draft.create":
            raise ValueError("Builder draft creation requires builder.draft.create capability.")
        if not authorized_draft_item_ids:
            raise ValueError("Builder draft creation requires at least one authorized draft item id.")
        if not authorized_target_paths:
            raise ValueError("Builder draft creation requires at least one authorized target path.")

        root = self.root.resolve()
        timestamp = generated_at or generated_timestamp()
        targets = selected_targets(preflight, authorized_draft_item_ids)
        authorization = {
            "confirmed": True,
            "authorized_by": authorized_by.strip(),
            "authorized_role": authorized_role.strip(),
            "authorized_authority_level": authorized_authority_level,
            "authorized_capability": authorized_capability,
            "authorized_mission_id": authorized_mission_id,
            "authorized_preflight_id": authorized_preflight_id,
            "authorized_preflight_hash": authorized_preflight_hash,
            "authorized_builder_draft_plan_hash": authorized_builder_draft_plan_hash,
            "authorized_draft_item_ids": authorized_draft_item_ids,
            "authorized_target_paths": authorized_target_paths,
            "required_roles": required_roles_for(targets),
        }
        pre_checks = self._pre_write_checks(preflight, targets, authorization, preflight_ref)
        failed_pre_checks = [check for check in pre_checks if not check["passed"]]
        mutations: list[dict] = []
        errors: list[dict] = []
        result_state = "blocked"
        if not failed_pre_checks:
            try:
                for target in targets:
                    mutations.append(write_target(root, preflight, target, authorization, timestamp))
                result_state = "created"
            except (OSError, ValueError) as exc:
                errors.append({"stage": "write", "message": str(exc)})
                result_state = "failed_write"

        post_validator = ValidatorEngine(root).run(mode="gate") if result_state == "created" else None
        if post_validator is not None:
            if post_validator["summary"]["error"] or post_validator["summary"]["fatal"]:
                result_state = "failed_validation"
            else:
                result_state = "created_validated"

        result = {
            "schema": SCHEMA,
            "id": "",
            "generated_at": timestamp,
            "root": str(root),
            "preflight": {
                "id": preflight["id"],
                "identity_hash": preflight["identity_hash"],
                "schema": preflight["schema"],
                "ref": preflight_ref,
                "file_hash": file_hash(preflight_ref) if preflight_ref else None,
                "builder_draft_plan_hash": preflight["source_plan"]["hash"],
            },
            "authorization": {
                **authorization,
                "role_satisfied": role_satisfies(authorized_role.strip(), authorization["required_roles"]),
                "draft_creation_authorized": True,
                "promotion_authorized": False,
            },
            "draft_set": {
                "schema": "contextos.builder.draft_set/1",
                "count": len(targets),
                "targets": [
                    {
                        "draft_item_id": target["draft_item_id"],
                        "target_path": target["draft_workspace_target_path"],
                        "target_context_artifact": target["target_context_artifact"],
                        "target_identity": target["target_identity"],
                    }
                    for target in targets
                ],
                "hash": stable_hash(
                    [
                        [
                            target["target_identity"],
                            target["draft_item_id"],
                            target["draft_workspace_target_path"],
                        ]
                        for target in targets
                    ]
                ),
            },
            "mutations": mutations,
            "validation": {
                "pre_write_checks": pre_checks,
                "post_write_validator": {
                    "schema": post_validator["schema"],
                    "summary": post_validator["summary"],
                }
                if post_validator is not None
                else None,
            },
            "rollback": {
                "available": bool(mutations),
                "created_artifact_count": len(mutations),
                "strategy": "delete_created_if_hash_matches",
                "will_not_remove_pre_existing_content": True,
            },
            "result": {
                "state": result_state,
                "success": result_state == "created_validated",
                "failed_pre_check_count": len(failed_pre_checks),
                "failed_pre_checks": [check["id"] for check in failed_pre_checks],
                "errors": errors,
            },
            "constraints": {
                "create_only": True,
                "overwrites_performed": False,
                "replacements_performed": False,
                "deletions_performed": False,
                "ssot_writes_performed": False,
                "canonical_context_writes_performed": False,
                "promotion_performed": False,
                "review_performed": False,
                "approval_performed": False,
                "knowledge_engine_used": False,
                "graph_runtime_used": False,
                "agents_used": False,
                "external_connectors_used": False,
            },
        }
        result["id"] = draft_write_result_id(result)
        result["identity_hash"] = stable_hash(draft_write_payload(result))
        return result

    def rollback(self, result: dict) -> dict:
        removed: list[dict] = []
        skipped: list[dict] = []
        root = self.root.resolve()
        for mutation in reversed(result.get("mutations", [])):
            target = root / mutation["target_path"]
            current = path_state(target)
            rollback = mutation.get("rollback", {})
            if not current["exists"]:
                skipped.append({"target_path": mutation["target_path"], "reason": "already_missing"})
                continue
            if current["hash"] != rollback.get("remove_only_if_hash"):
                skipped.append({"target_path": mutation["target_path"], "reason": "current_hash_changed"})
                continue
            target.unlink()
            removed.append({"target_path": mutation["target_path"], "status": "removed"})
            for directory in reversed(mutation.get("created_directories", [])):
                dir_path = root / directory
                try:
                    dir_path.rmdir()
                except OSError:
                    skipped.append({"target_path": directory, "reason": "directory_not_empty"})
        return {
            "schema": ROLLBACK_SCHEMA,
            "root": str(root),
            "source_draft_write_result_id": result["id"],
            "removed": removed,
            "skipped": skipped,
            "constraints": {
                "removed_only_created_artifacts": True,
                "canonical_context_removed": False,
                "ssot_removed": False,
            },
        }

    def _pre_write_checks(self, preflight: dict, targets: list[dict], authorization: dict, preflight_ref: str | None) -> list[dict]:
        validator_report = ValidatorEngine(self.root).run(mode="gate")
        authorized_item_ids = authorization["authorized_draft_item_ids"]
        authorized_paths = authorization["authorized_target_paths"]
        required_roles = authorization["required_roles"]
        current_preflight_file_hash = file_hash(preflight_ref) if preflight_ref else None
        return [
            check(
                "draft_write.check.preflight_identity_valid",
                preflight_identity_valid(preflight),
                {"preflight_id": preflight.get("id"), "identity_hash": preflight.get("identity_hash")},
            ),
            check(
                "draft_write.check.preflight_file_preserved",
                preflight_ref is not None and current_preflight_file_hash is not None,
                {"ref": preflight_ref, "current_file_hash": current_preflight_file_hash},
            ),
            check(
                "draft_write.check.preflight_eligible",
                preflight["eligibility"]["eligible_for_future_draft_creation"],
                preflight["eligibility"],
            ),
            check(
                "draft_write.check.source_plan_identity_bound",
                preflight["source_plan"]["identity_bound"],
                preflight["source_plan"],
            ),
            check(
                "draft_write.check.preflight_validation_checks_passed",
                validation_checks_passed(preflight),
                preflight["validation"],
            ),
            check(
                "draft_write.check.authorization_bound_to_mission",
                authorization["authorized_mission_id"] == preflight["mission"]["id"],
                {"authorized": authorization["authorized_mission_id"], "preflight": preflight["mission"]["id"]},
            ),
            check(
                "draft_write.check.authorization_bound_to_preflight",
                authorization["authorized_preflight_id"] == preflight["id"]
                and authorization["authorized_preflight_hash"] == preflight["identity_hash"],
                {"authorized_preflight_id": authorization["authorized_preflight_id"]},
            ),
            check(
                "draft_write.check.authorization_bound_to_draft_plan",
                authorization["authorized_builder_draft_plan_hash"] == preflight["source_plan"]["hash"],
                {"authorized": authorization["authorized_builder_draft_plan_hash"], "preflight": preflight["source_plan"]["hash"]},
            ),
            check(
                "draft_write.check.authorized_targets_exist",
                len(targets) == len(set(authorized_item_ids)),
                {"authorized_item_ids": authorized_item_ids, "resolved_count": len(targets)},
            ),
            check(
                "draft_write.check.authorized_targets_eligible",
                bool(targets) and all(target["status"] == "eligible" for target in targets),
                {"target_statuses": {target["draft_item_id"]: target["status"] for target in targets}},
            ),
            check(
                "draft_write.check.authorized_paths_exact",
                all(target_path_allowed(target, authorized_paths) for target in targets)
                and set(authorized_paths) == {target["draft_workspace_target_path"] for target in targets},
                {"authorized_paths": authorized_paths},
            ),
            check(
                "draft_write.check.authorized_items_exact",
                all(target_item_allowed(target, authorized_item_ids) for target in targets)
                and set(authorized_item_ids) == {target["draft_item_id"] for target in targets},
                {"authorized_item_ids": authorized_item_ids},
            ),
            check(
                "draft_write.check.l2_authority",
                authorization["authorized_authority_level"] == "L2"
                and authorization["authorized_capability"] == "builder.draft.create",
                {
                    "authority_level": authorization["authorized_authority_level"],
                    "capability": authorization["authorized_capability"],
                },
            ),
            check(
                "draft_write.check.authorizing_role_satisfies_required_roles",
                bool(required_roles) and role_satisfies(authorization["authorized_role"], required_roles),
                {"authorized_role": authorization["authorized_role"], "required_roles": required_roles},
            ),
            check(
                "draft_write.check.no_overwrite_current_state",
                all(target_still_missing(self.root.resolve(), target) for target in targets),
                {"target_paths": [target["draft_workspace_target_path"] for target in targets]},
            ),
            check(
                "draft_write.check.only_draft_workspace_targets",
                all(target["draft_workspace_target_path"].startswith(".contextos/drafts/") for target in targets),
                {"target_paths": [target["draft_workspace_target_path"] for target in targets]},
            ),
            check(
                "draft_write.check.validator_gate_satisfied_before_write",
                validator_report["summary"]["error"] == 0 and validator_report["summary"]["fatal"] == 0,
                validator_report["summary"],
            ),
            check(
                "draft_write.check.preflight_did_not_authorize_promotion",
                not preflight["eligibility"]["draft_creation_authorized"] and not preflight["eligibility"]["promotion_authorized"],
                preflight["eligibility"],
            ),
        ]


def check(identifier: str, passed: bool, evidence: dict) -> dict:
    return {"id": identifier, "passed": bool(passed), "evidence": evidence}
