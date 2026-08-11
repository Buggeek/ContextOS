from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

from bootstrap_engine.acceptance_engine import role_satisfies
from bootstrap_engine.approval_engine import load_json
from bootstrap_engine.preflight_engine import preflight_payload
from bootstrap_engine.proposal_engine import canonical_json, generated_timestamp, path_state, stable_hash


TOOLS_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from engine.validator_engine import ValidatorEngine  # noqa: E402


SCHEMA = "contextos.bootstrap.apply_result/1"


def file_hash(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def apply_result_payload(result: dict) -> dict:
    return {
        "schema": result["schema"],
        "preflight": result["preflight"],
        "confirmation": result["confirmation"],
        "mutation_set": result["mutation_set"],
        "result": result["result"],
    }


def apply_result_id(result: dict) -> str:
    return f"bootstrap.apply_result.{stable_hash(apply_result_payload(result))[:16]}"


def preflight_identity_valid(preflight: dict) -> bool:
    return preflight.get("id") == f"bootstrap.apply_preflight.{stable_hash(preflight_payload(preflight))[:16]}" and preflight.get(
        "identity_hash"
    ) == stable_hash(preflight_payload(preflight))


def target_state_matches(root: Path, action: dict) -> bool:
    target = root.resolve() / action["target_path"]
    current = path_state(target)
    expected = action["expected_before"]
    return current["exists"] == expected["exists"] and current["hash"] == expected["hash"]


def target_scope_ok(action: dict, preflight: dict) -> bool:
    target = action.get("target_path")
    if not target:
        return False
    return target in preflight["authority"]["allowed_write_paths"] and target not in preflight["authority"]["prohibited_write_paths"]


def deterministic_manifest_content(preflight: dict, action: dict) -> str:
    return "\n".join(
        [
            "schema: contextos.runtime.manifest/1",
            "version: 0.1.0",
            f"generated_by: {SCHEMA}",
            f"source_preflight_id: {preflight['id']}",
            f"source_proposal_id: {preflight['proposal']['id']}",
            f"action_id: {action['id']}",
            "",
        ]
    )


def write_action(root: Path, preflight: dict, action: dict) -> dict:
    target = root.resolve() / action["target_path"]
    before = path_state(target)
    if before["exists"]:
        raise ValueError(f"Apply refused to overwrite existing path: {action['target_path']}")

    if action["type"] == "create_directory":
        target.mkdir(parents=True, exist_ok=False)
    elif action["type"] == "create_manifest":
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(deterministic_manifest_content(preflight, action), encoding="utf-8")
    elif action["type"] == "create_from_template":
        template = action.get("source_template")
        if not template:
            raise ValueError(f"Apply action missing source template: {action['id']}")
        template_path = TOOLS_ROOT.parent / template
        if not template_path.is_file():
            raise ValueError(f"Apply source template is missing: {template}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(template_path, target)
    else:
        raise ValueError(f"Unsupported apply action type: {action['type']}")

    after = path_state(target)
    return {
        "action_id": action["id"],
        "target_path": action["target_path"],
        "type": action["type"],
        "status": "created",
        "before": before,
        "after": after,
        "rollback": {
            "available": action["rollback_strategy"] == "delete_created",
            "strategy": action["rollback_strategy"],
            "remove_only_if_hash": after["hash"],
        },
        "source_template": action.get("source_template"),
        "proposal_id": preflight["proposal"]["id"],
        "preflight_id": preflight["id"],
    }


def rollback_created_artifacts(root: Path, result: dict) -> dict:
    removed: list[dict] = []
    skipped: list[dict] = []
    for mutation in reversed(result.get("mutations", [])):
        rollback = mutation.get("rollback", {})
        target = root.resolve() / mutation["target_path"]
        current = path_state(target)
        if not rollback.get("available"):
            skipped.append({"target_path": mutation["target_path"], "reason": "rollback_unavailable"})
            continue
        if not current["exists"]:
            skipped.append({"target_path": mutation["target_path"], "reason": "already_missing"})
            continue
        if current["hash"] != rollback.get("remove_only_if_hash"):
            skipped.append({"target_path": mutation["target_path"], "reason": "current_hash_changed"})
            continue
        if target.is_dir():
            try:
                target.rmdir()
            except OSError:
                skipped.append({"target_path": mutation["target_path"], "reason": "directory_not_empty"})
                continue
        else:
            target.unlink()
        removed.append({"target_path": mutation["target_path"], "status": "removed"})
    return {
        "schema": "contextos.bootstrap.rollback_result/1",
        "root": str(root.resolve()),
        "source_apply_result_id": result["id"],
        "removed": removed,
        "skipped": skipped,
    }


class BootstrapApplyEngine:
    """Create-only Guided Bootstrap apply engine gated by preflight."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        preflight: dict,
        *,
        preflight_ref: str | None = None,
        confirm_apply: bool,
        confirmed_by: str,
        confirmed_role: str,
        confirmed_preflight_id: str | None = None,
        confirmed_preflight_hash: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if preflight.get("schema") != "contextos.bootstrap.apply_preflight/1":
            raise ValueError("Bootstrap apply requires contextos.bootstrap.apply_preflight/1 input.")
        if not confirm_apply:
            raise ValueError("Bootstrap apply requires explicit --confirm-apply.")
        if not confirmed_by or not confirmed_by.strip():
            raise ValueError("Bootstrap apply requires explicit confirming human identity.")
        if not confirmed_role or not confirmed_role.strip():
            raise ValueError("Bootstrap apply requires explicit confirming authority role.")
        if not confirmed_preflight_id:
            raise ValueError("Bootstrap apply confirmation must include the exact preflight id.")
        if not confirmed_preflight_hash:
            raise ValueError("Bootstrap apply confirmation must include the exact preflight identity hash.")
        if confirmed_preflight_id and confirmed_preflight_id != preflight["id"]:
            raise ValueError("Bootstrap apply confirmation preflight id does not match.")
        if confirmed_preflight_hash and confirmed_preflight_hash != preflight["identity_hash"]:
            raise ValueError("Bootstrap apply confirmation preflight hash does not match.")

        pre_checks = self._pre_apply_checks(preflight, confirmed_role.strip(), preflight_ref)
        failed_pre_checks = [check for check in pre_checks if not check["passed"]]
        mutations: list[dict] = []
        errors: list[dict] = []
        result_state = "blocked"
        if not failed_pre_checks:
            try:
                for action in preflight["frozen_mutation_set"]["actions"]:
                    mutations.append(write_action(self.root, preflight, action))
                result_state = "applied"
            except (OSError, ValueError) as exc:
                errors.append({"stage": "apply", "message": str(exc)})
                result_state = "failed_apply"

        post_validator = ValidatorEngine(self.root).run(mode="gate") if result_state == "applied" else None
        if post_validator is not None:
            if post_validator["summary"]["error"] or post_validator["summary"]["fatal"]:
                result_state = "failed_validation"
            else:
                result_state = "applied_validated"

        result = {
            "schema": SCHEMA,
            "id": "",
            "generated_at": generated_at or generated_timestamp(),
            "root": str(self.root.resolve()),
            "preflight": {
                "id": preflight["id"],
                "identity_hash": preflight["identity_hash"],
                "schema": preflight["schema"],
                "ref": preflight_ref,
                "file_hash": file_hash(preflight_ref) if preflight_ref else None,
            },
            "confirmation": {
                "confirmed": True,
                "confirmed_by": confirmed_by.strip(),
                "confirmed_role": confirmed_role.strip(),
                "confirmed_preflight_id": confirmed_preflight_id or preflight["id"],
                "confirmed_preflight_hash": confirmed_preflight_hash or preflight["identity_hash"],
                "role_satisfied": role_satisfies(confirmed_role.strip(), preflight["authority"]["required_roles"]),
            },
            "mutation_set": preflight["frozen_mutation_set"],
            "mutations": mutations,
            "validation": {
                "pre_apply_checks": pre_checks,
                "post_apply_validator": {
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
                "success": result_state == "applied_validated",
                "failed_pre_check_count": len(failed_pre_checks),
                "failed_pre_checks": [check["id"] for check in failed_pre_checks],
                "errors": errors,
            },
            "constraints": {
                "create_only": True,
                "overwrites_performed": False,
                "replacements_performed": False,
                "deletions_performed": False,
                "prohibited_actions_performed": False,
                "manual_actions_performed": False,
                "external_connectors_used": False,
                "agents_used": False,
            },
        }
        result["id"] = apply_result_id(result)
        result["identity_hash"] = stable_hash(apply_result_payload(result))
        return result

    def rollback(self, result: dict) -> dict:
        return rollback_created_artifacts(self.root, result)

    def _pre_apply_checks(self, preflight: dict, confirmed_role: str, preflight_ref: str | None) -> list[dict]:
        validator_report = ValidatorEngine(self.root).run(mode="gate")
        actions = preflight["frozen_mutation_set"]["actions"]
        current_preflight_file_hash = file_hash(preflight_ref) if preflight_ref else None
        return [
            check(
                "apply.check.preflight_identity_valid",
                preflight_identity_valid(preflight),
                {"preflight_id": preflight.get("id"), "identity_hash": preflight.get("identity_hash")},
            ),
            check(
                "apply.check.preflight_eligible",
                preflight["eligibility"]["eligible_for_apply"],
                preflight["eligibility"],
            ),
            check(
                "apply.check.preflight_file_preserved",
                preflight_ref is not None and current_preflight_file_hash is not None,
                {"ref": preflight_ref, "current_file_hash": current_preflight_file_hash},
            ),
            check(
                "apply.check.confirming_role_satisfies_required_authority",
                role_satisfies(confirmed_role, preflight["authority"]["required_roles"]),
                {"confirmed_role": confirmed_role, "required_roles": preflight["authority"]["required_roles"]},
            ),
            check(
                "apply.check.mutation_set_hash_valid",
                stable_hash({"actions": actions}) == preflight["frozen_mutation_set"]["hash"],
                {"mutation_set_hash": preflight["frozen_mutation_set"]["hash"]},
            ),
            check(
                "apply.check.apply_has_executable_mutations",
                bool(actions),
                {"mutation_action_count": len(actions)},
            ),
            check(
                "apply.check.only_create_actions",
                all(action["type"] in {"create_directory", "create_manifest", "create_from_template"} for action in actions),
                {"action_ids": [action["id"] for action in actions]},
            ),
            check(
                "apply.check.no_prohibited_or_manual_actions",
                all(action["class"] in {"automatic", "approval_required"} for action in actions),
                {"action_ids": [action["id"] for action in actions]},
            ),
            check(
                "apply.check.actions_within_approved_scope",
                all(target_scope_ok(action, preflight) for action in actions),
                {
                    "allowed_paths": preflight["authority"]["allowed_write_paths"],
                    "prohibited_paths": preflight["authority"]["prohibited_write_paths"],
                    "action_ids": [action["id"] for action in actions],
                },
            ),
            check(
                "apply.check.no_overwrite_current_state",
                all(target_state_matches(self.root, action) and action["no_overwrite"]["satisfied"] for action in actions),
                {"action_ids": [action["id"] for action in actions]},
            ),
            check(
                "apply.check.rollback_available_for_all_actions",
                all(action["rollback_strategy"] == "delete_created" and action["reversible"] for action in actions),
                {"action_ids": [action["id"] for action in actions]},
            ),
            check(
                "apply.check.validator_gate_satisfied_before_apply",
                validator_report["summary"]["error"] == 0 and validator_report["summary"]["fatal"] == 0,
                validator_report["summary"],
            ),
            check(
                "apply.check.preflight_did_not_authorize_apply",
                not preflight["eligibility"]["apply_authorized"] and not preflight["eligibility"]["repository_mutation_authorized"],
                preflight["eligibility"],
            ),
        ]


def check(identifier: str, passed: bool, evidence: dict) -> dict:
    return {"id": identifier, "passed": bool(passed), "evidence": evidence}


def apply_result_hash(result: dict) -> str:
    return hashlib.sha256(canonical_json(result).encode("utf-8")).hexdigest()
