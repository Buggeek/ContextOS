from __future__ import annotations

import copy
import datetime as _dt
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from bootstrap_engine.plan_engine import BootstrapPlanEngine, TOOLS_ROOT


SCHEMA = "contextos.bootstrap.proposal/1"
DEFAULT_RELEASE = "v0.4 - Guided Bootstrap"
DEFAULT_GOAL = "Create a governed minimum Context OS bootstrap change set."
DEFAULT_MISSION_ID = "V04-BOOTSTRAP-PROPOSAL-001"

APPROVING_ROLES_BY_MODE = {
    "local": ["Mission Owner"],
    "project": ["Mission Owner", "Product Owner or Runtime Owner"],
    "organization": ["Runtime Owner", "Governance Role", "Product Owner for SSOT/product artifacts"],
    "embedded": ["Host-confirmed human approver", "Mission Owner or Runtime Owner"],
}


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_state(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "kind": "missing", "hash": None}
    if path.is_symlink():
        return {"exists": True, "kind": "symlink", "hash": hashlib.sha256(str(path.readlink()).encode("utf-8")).hexdigest()}
    if path.is_file():
        return {"exists": True, "kind": "file", "hash": file_hash(path)}
    if path.is_dir():
        entries = sorted(child.name for child in path.iterdir())
        return {"exists": True, "kind": "directory", "hash": stable_hash(entries)}
    return {"exists": True, "kind": "other", "hash": None}


def git_output(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def git_dirty_state(root: Path) -> str:
    in_worktree = git_output(root, "rev-parse", "--is-inside-work-tree")
    if in_worktree != "true":
        return "unknown"
    unstaged = subprocess.run(["git", "-C", str(root), "diff", "--quiet"], capture_output=True)
    staged = subprocess.run(["git", "-C", str(root), "diff", "--cached", "--quiet"], capture_output=True)
    return "clean" if unstaged.returncode == 0 and staged.returncode == 0 else "dirty"


def git_vcs(root: Path) -> str:
    return "git" if git_output(root, "rev-parse", "--is-inside-work-tree") == "true" else "none"


def relevant_paths(plan: dict) -> list[str]:
    paths: set[str] = set()
    for action in plan.get("actions", []):
        target = action.get("target_path")
        if target:
            paths.add(target)
        template = action.get("source_template")
        if template:
            paths.add(template)
    return sorted(paths)


def repository_fingerprint(root: Path, plan: dict) -> dict:
    resolved_root = root.resolve()
    paths = []
    for rel_path in relevant_paths(plan):
        target = resolved_root / rel_path
        if rel_path.startswith("templates/"):
            target = TOOLS_ROOT.parent / rel_path
        paths.append({"path": rel_path, **path_state(target)})
    state = {
        "vcs": git_vcs(resolved_root),
        "base_ref": git_output(resolved_root, "rev-parse", "HEAD"),
        "dirty_state": git_dirty_state(resolved_root),
        "paths": paths,
    }
    state["base_tree_hash"] = stable_hash(paths)
    state["fingerprint_hash"] = stable_hash(state)
    return state


def action_class(action: dict) -> str:
    if action.get("status") == "blocked":
        return "prohibited"
    if action.get("status") == "manual" or action.get("type") in {"manual_remediation", "validate_after_apply"}:
        return "manual"
    if action.get("type") == "create_directory":
        return "automatic"
    if action.get("type") in {"create_manifest", "create_from_template"}:
        return "approval_required"
    return "prohibited"


def rollback_strategy(action: dict) -> str:
    classification = action_class(action)
    if classification == "manual":
        return "manual"
    if classification == "prohibited":
        return "none"
    if action.get("status") == "skipped_existing":
        return "none"
    if action.get("status") == "required":
        return "delete_created"
    return "none"


def expected_before(root: Path, action: dict) -> dict:
    target = action.get("target_path")
    if target is None:
        return {"exists": "unknown", "hash": None}
    state = path_state(root.resolve() / target)
    return {"exists": state["exists"], "hash": state["hash"]}


def expected_after(root: Path, action: dict) -> dict:
    status = action.get("status")
    target = action.get("target_path")
    if target is None:
        return {"exists": False, "hash": None}
    if status == "skipped_existing":
        state = path_state(root.resolve() / target)
        return {"exists": state["exists"], "hash": state["hash"]}
    if status == "required":
        template = action.get("source_template")
        if template:
            template_path = TOOLS_ROOT.parent / template
            return {"exists": True, "hash": file_hash(template_path) if template_path.is_file() else None}
        return {"exists": True, "hash": None}
    return {"exists": False, "hash": None}


def no_overwrite(action: dict, before: dict) -> dict:
    if action.get("status") == "required":
        return {"required": True, "satisfied": before["exists"] is False}
    if action.get("status") == "skipped_existing":
        return {"required": True, "satisfied": True}
    return {"required": action_class(action) in {"automatic", "approval_required"}, "satisfied": action_class(action) not in {"automatic", "approval_required"}}


def proposal_action(root: Path, action: dict) -> dict:
    before = expected_before(root, action)
    classification = action_class(action)
    return {
        "id": action["id"],
        "type": action["type"],
        "status": action["status"],
        "target_path": action.get("target_path"),
        "class": classification,
        "source_template": action.get("source_template"),
        "expected_before": before,
        "expected_after": expected_after(root, action),
        "reversible": rollback_strategy(action) in {"delete_created", "restore_previous"},
        "rollback_strategy": rollback_strategy(action),
        "recommendation_ids": list(action.get("recommendation_ids", [])),
        "evidence_refs": list(action.get("evidence_refs", [])),
        "no_overwrite": no_overwrite(action, before),
        "future_apply_phase": action.get("future_apply_phase"),
    }


def authority_block(
    mode: str,
    mission_id: str,
    requested_by: str,
    allowed_paths: list[str],
    prohibited_paths: list[str],
    expires_at: str | None,
) -> dict:
    return {
        "requested_by": requested_by,
        "approving_roles": APPROVING_ROLES_BY_MODE[mode],
        "approvers": [],
        "authority_level": "L3",
        "approval_state": "planned",
        "decision_ref": None,
        "ledger_ref": None,
        "mission_id": mission_id,
        "allowed_write_paths": allowed_paths,
        "prohibited_write_paths": prohibited_paths,
        "expires_at": expires_at,
    }


def default_allowed_paths(plan: dict) -> list[str]:
    paths = []
    for action in plan.get("actions", []):
        if action.get("status") == "required" and action.get("target_path"):
            paths.append(action["target_path"])
    return sorted(dict.fromkeys(paths))


def default_prohibited_paths(plan: dict) -> list[str]:
    paths = ["/", "..", "../*", "**/.git/*"]
    for action in plan.get("actions", []):
        if action_class(action) == "prohibited" and action.get("target_path"):
            paths.append(action["target_path"])
    return sorted(dict.fromkeys(paths))


def identity_payload(proposal: dict) -> dict:
    return {
        "schema": proposal["schema"],
        "mode": proposal["mode"],
        "mission_id": proposal["mission_id"],
        "release": proposal["release"],
        "goal": proposal["goal"],
        "source_plan_hash": proposal["source_plan"]["plan_hash"],
        "repository_state_hash": proposal["repository_state"]["fingerprint_hash"],
        "authority": {
            "approving_roles": proposal["authority"]["approving_roles"],
            "authority_level": proposal["authority"]["authority_level"],
            "allowed_write_paths": proposal["authority"]["allowed_write_paths"],
            "prohibited_write_paths": proposal["authority"]["prohibited_write_paths"],
        },
        "actions": [
            {
                "id": action["id"],
                "type": action["type"],
                "status": action["status"],
                "target_path": action["target_path"],
                "class": action["class"],
                "source_template": action["source_template"],
                "expected_before": action["expected_before"],
                "expected_after": action["expected_after"],
                "rollback_strategy": action["rollback_strategy"],
            }
            for action in proposal["actions"]
        ],
    }


class BootstrapProposalEngine:
    """Read-only engine that freezes a bootstrap plan into an approvable proposal."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        bootstrap_plan: dict | None = None,
        *,
        mission_id: str = DEFAULT_MISSION_ID,
        release: str = DEFAULT_RELEASE,
        goal: str = DEFAULT_GOAL,
        mode: str = "local",
        requested_by: str = "operator",
        generated_at: str | None = None,
        expires_at: str | None = None,
        plan_ref: str | None = None,
    ) -> dict:
        if mode not in APPROVING_ROLES_BY_MODE:
            raise ValueError(f"Unsupported bootstrap proposal mode: {mode}")

        root = self.root.resolve()
        plan = copy.deepcopy(bootstrap_plan) if bootstrap_plan is not None else BootstrapPlanEngine(root).run()
        plan_hash = stable_hash(plan)
        repo_state = repository_fingerprint(root, plan)
        actions = [proposal_action(root, action) for action in plan.get("actions", [])]
        allowed_paths = default_allowed_paths(plan)
        prohibited_paths = default_prohibited_paths(plan)

        proposal = {
            "schema": SCHEMA,
            "id": "",
            "generated_at": generated_at or generated_timestamp(),
            "expires_at": expires_at,
            "root": str(root),
            "mode": mode,
            "mission_id": mission_id,
            "release": release,
            "goal": goal,
            "source_plan": {
                "schema": plan["schema"],
                "plan_ref": plan_ref,
                "plan_hash": plan_hash,
                "generated_at": plan["generated_at"],
            },
            "repository_state": repo_state,
            "readiness_evidence": plan["readiness"],
            "validator_evidence": plan["validator"],
            "authority": authority_block(mode, mission_id, requested_by, allowed_paths, prohibited_paths, expires_at),
            "actions": sorted(actions, key=lambda item: item["id"]),
            "gates": {
                "pre_apply_validator_ref": "embedded:source_plan.validator",
                "post_apply_validator_ref": None,
            },
            "drift_invalidation_conditions": [
                "source_plan_hash_changed",
                "repository_state_hash_changed",
                "action_set_changed",
                "authority_scope_changed",
                "target_path_state_changed",
                "source_template_hash_changed",
            ],
            "status": "planned",
            "read_only": True,
            "constraints": {
                "writes_performed": False,
                "approval_implied": False,
                "apply_authorized": False,
                "external_connectors_used": False,
                "agents_used": False,
            },
        }
        proposal["id"] = f"bootstrap.proposal.{stable_hash(identity_payload(proposal))[:16]}"
        proposal["identity_hash"] = stable_hash(identity_payload(proposal))
        return proposal

    def check_drift(self, proposal: dict, bootstrap_plan: dict | None = None) -> dict:
        current_plan = bootstrap_plan
        if current_plan is None:
            current_plan = BootstrapPlanEngine(self.root).run(generated_at=proposal["source_plan"]["generated_at"])
        current = self.run(
            bootstrap_plan=current_plan,
            mission_id=proposal["mission_id"],
            release=proposal["release"],
            goal=proposal["goal"],
            mode=proposal["mode"],
            requested_by=proposal["authority"]["requested_by"],
            generated_at=proposal["generated_at"],
            expires_at=proposal.get("expires_at"),
            plan_ref=proposal["source_plan"].get("plan_ref"),
        )
        checks = {
            "source_plan_hash_changed": proposal["source_plan"]["plan_hash"] != current["source_plan"]["plan_hash"],
            "repository_state_hash_changed": proposal["repository_state"]["fingerprint_hash"] != current["repository_state"]["fingerprint_hash"],
            "action_set_changed": action_identity(proposal) != action_identity(current),
            "authority_scope_changed": authority_identity(proposal) != authority_identity(current),
            "proposal_identity_changed": proposal["identity_hash"] != current["identity_hash"],
        }
        return {
            "schema": "contextos.bootstrap.proposal.drift/1",
            "proposal_id": proposal["id"],
            "invalidated": any(checks.values()),
            "checks": checks,
            "current_identity_hash": current["identity_hash"],
            "approved_identity_hash": proposal["identity_hash"],
        }


def action_identity(proposal: dict) -> list[dict]:
    return identity_payload(proposal)["actions"]


def authority_identity(proposal: dict) -> dict:
    return identity_payload(proposal)["authority"]
