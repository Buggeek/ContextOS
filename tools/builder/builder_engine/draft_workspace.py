from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from builder_engine.draft_plan import BuilderDraftPlanEngine


BUILDER_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from engine.validator_engine import ValidatorEngine  # noqa: E402


SCHEMA = "contextos.builder.draft_workspace_preflight/1"
DEFAULT_MISSION_ID = "V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001"
DEFAULT_RELEASE = "v0.5 - Context Construction"
DEFAULT_GOAL = "Validate the governed Draft Workspace before future Builder draft writes."
DEFAULT_WORKSPACE = ".contextos/drafts"
PROHIBITED_ROOTS = ("SSOT", "docs", "ops", "templates", "tools", ".git")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def generated_timestamp() -> str:
    from builder_engine.report_builder import generated_timestamp as _generated_timestamp

    return _generated_timestamp()


def draft_plan_identity_payload(draft_plan: dict) -> dict:
    return {
        "schema": draft_plan["schema"],
        "root": draft_plan["root"],
        "mode": draft_plan["mode"],
        "read_only": draft_plan["read_only"],
        "source_inputs": draft_plan["source_inputs"],
        "summary": draft_plan["summary"],
        "draft_items": draft_plan["draft_items"],
        "lifecycle": draft_plan["lifecycle"],
        "truth_boundaries": draft_plan["truth_boundaries"],
        "constraints": draft_plan["constraints"],
    }


def draft_plan_hash(draft_plan: dict) -> str:
    return stable_hash(draft_plan_identity_payload(draft_plan))


def preflight_payload(report: dict) -> dict:
    return {
        "schema": report["schema"],
        "mission": report["mission"],
        "draft_workspace": report["draft_workspace"],
        "source_plan": report["source_plan"],
        "targets": report["targets"],
        "validation": report["validation"],
        "eligibility": report["eligibility"],
    }


def preflight_id(report: dict) -> str:
    return f"builder.draft_workspace_preflight.{stable_hash(preflight_payload(report))[:16]}"


def slug(value: str) -> str:
    cleaned = []
    for char in value.lower():
        cleaned.append(char if char.isalnum() else "_")
    return "_".join(part for part in "".join(cleaned).split("_") if part) or "item"


def path_state(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "kind": "missing", "hash": None}
    if path.is_symlink():
        return {"exists": True, "kind": "symlink", "hash": hashlib.sha256(str(path.readlink()).encode("utf-8")).hexdigest()}
    if path.is_file():
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return {"exists": True, "kind": "file", "hash": digest.hexdigest()}
    if path.is_dir():
        return {"exists": True, "kind": "directory", "hash": stable_hash(sorted(child.name for child in path.iterdir()))}
    return {"exists": True, "kind": "other", "hash": None}


def relative_to_or_none(path: Path, base: Path) -> str | None:
    try:
        return path.relative_to(base).as_posix()
    except ValueError:
        return None


def resolve_inside(root: Path, rel_path: str) -> Path:
    return (root / rel_path).resolve()


def has_forbidden_parts(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    return any(part in {"", ".", ".."} for part in parts) or rel_path.startswith("/")


def canonical_target_path_for(workspace_rel: str, mission_id: str, target_context_artifact: str) -> str:
    return f"{workspace_rel.rstrip('/')}/{mission_id}/artifacts/{target_context_artifact}"


def target_report(root: Path, workspace_abs: Path, workspace_rel: str, mission_id: str, item: dict) -> dict:
    source_target = item["target_context_artifact"]
    local_target_rel = canonical_target_path_for(workspace_rel, mission_id, source_target)
    local_target_abs = resolve_inside(root, local_target_rel)
    workspace_escape = relative_to_or_none(local_target_abs, workspace_abs) is None
    root_escape = relative_to_or_none(local_target_abs, root) is None
    source_escape = has_forbidden_parts(source_target)
    local_escape = has_forbidden_parts(local_target_rel)
    existing = path_state(local_target_abs)
    canonical_target_abs = (root / source_target).resolve()
    canonical_target_inside_root = not source_escape and relative_to_or_none(canonical_target_abs, root) is not None
    canonical_target_state = (
        path_state(canonical_target_abs)
        if canonical_target_inside_root
        else {"exists": "unknown", "kind": "unresolved", "hash": None}
    )
    prohibited_surface = local_target_rel.split("/", 1)[0] in PROHIBITED_ROOTS
    contradictions = item.get("contradictions", [])
    support_level = item.get("support", {}).get("level")
    evidence_refs = item.get("provenance_chain", {}).get("evidence_refs", [])
    validator_scope = source_target
    checks = [
        check("target.check.item_is_draftable", item["status"] == "draftable", {"status": item["status"]}),
        check("target.check.workspace_boundary", not workspace_escape and not root_escape, {"target_path": local_target_rel}),
        check("target.check.no_path_traversal", not source_escape and not local_escape, {"source_target": source_target}),
        check("target.check.not_canonical_surface", not prohibited_surface, {"target_path": local_target_rel}),
        check("target.check.target_missing", not existing["exists"], existing),
        check("target.check.no_overwrite", not existing["exists"], {"target_path": local_target_rel}),
        check(
            "target.check.source_canonical_not_overwritten",
            canonical_target_inside_root and local_target_abs != canonical_target_abs,
            {"canonical_target": source_target, "state": canonical_target_state},
        ),
        check("target.check.support_sufficient", support_level in {"moderate", "strong"}, {"support_level": support_level}),
        check("target.check.evidence_refs_present", bool(evidence_refs), {"evidence_ref_count": len(evidence_refs)}),
        check("target.check.no_contradictions", len(contradictions) == 0, {"contradiction_count": len(contradictions)}),
    ]
    failures = [entry["id"] for entry in checks if not entry["passed"]]
    return {
        "draft_item_id": item["id"],
        "source_candidate_id": item["source_candidate_id"],
        "target_context_artifact": source_target,
        "draft_workspace_target_path": local_target_rel,
        "target_identity": f"builder.draft_target.{stable_hash([mission_id, item['id'], source_target, local_target_rel])[:16]}",
        "artifact_class": item["artifact_class"],
        "operation_domain": item["operation_domain"],
        "intended_lifecycle_state": "draft",
        "support": item.get("support", {}),
        "status": "eligible" if not failures else "ineligible",
        "failed_checks": failures,
        "checks": checks,
        "path_resolution": {
            "workspace_relative": workspace_rel,
            "target_relative": local_target_rel,
            "inside_workspace": not workspace_escape,
            "inside_root": not root_escape,
            "canonical_target_path": source_target,
        },
        "state": {
            "draft_target": existing,
            "canonical_target": canonical_target_state,
            "no_overwrite_satisfied": not existing["exists"],
        },
        "plan_binding": {
            "builder_draft_plan_item_id": item["id"],
            "source_discovery_fingerprint": item["provenance_chain"]["discovery_fingerprint"],
            "source_discovery_id": item["provenance_chain"]["discovery_source_id"],
            "source_construction_candidate_id": item["provenance_chain"]["construction_candidate_id"],
            "evidence_refs": evidence_refs,
            "validator_scope": validator_scope,
        },
        "authority_required": {
            "capability": "builder.draft.create",
            "authority_level": item["required_human_review"]["authority_level"],
            "role": item["required_human_review"]["role"],
            "human_review_required": True,
            "promotion_authorized": False,
        },
        "truth_boundaries": {
            "draft_is_not_truth": True,
            "promotion_allowed": False,
            "unknowns_preserved": item.get("unknowns", []),
            "missing_evidence_preserved": item.get("missing_evidence", []),
            "contradictions_preserved": contradictions,
        },
    }


def check(check_id: str, passed: bool, evidence: dict) -> dict:
    return {"id": check_id, "passed": bool(passed), "evidence": evidence}


class DraftWorkspaceRuntime:
    """Read-only runtime that validates the local Draft Workspace boundary."""

    def __init__(self, root: str | Path = ".", workspace: str = DEFAULT_WORKSPACE) -> None:
        self.root = Path(root)
        self.workspace = workspace

    def run(
        self,
        draft_plan: dict | None = None,
        *,
        mission_id: str = DEFAULT_MISSION_ID,
        release: str = DEFAULT_RELEASE,
        goal: str = DEFAULT_GOAL,
        generated_at: str | None = None,
    ) -> dict:
        root = self.root.resolve()
        plan = draft_plan or BuilderDraftPlanEngine(root).run(generated_at=generated_at)
        if plan.get("schema") != "contextos.builder.draft_plan/1":
            raise ValueError("Draft Workspace runtime requires contextos.builder.draft_plan/1 input.")

        workspace_abs = resolve_inside(root, self.workspace)
        workspace_rel = relative_to_or_none(workspace_abs, root)
        workspace_state = path_state(workspace_abs)
        workspace_valid = workspace_rel is not None and workspace_rel == DEFAULT_WORKSPACE and not has_forbidden_parts(workspace_rel)
        fresh_plan = BuilderDraftPlanEngine(root).run(generated_at=plan.get("generated_at"))
        source_hash = draft_plan_hash(plan)
        fresh_hash = draft_plan_hash(fresh_plan)
        validator_report = ValidatorEngine(root).run(mode="gate")
        targets = [
            target_report(root, workspace_abs, workspace_rel or self.workspace, mission_id, item)
            for item in plan.get("draft_items", [])
        ]
        workspace_checks = [
            check("workspace.check.local_mapping_declared", self.workspace == DEFAULT_WORKSPACE, {"workspace": self.workspace}),
            check("workspace.check.inside_repository", workspace_rel is not None, {"workspace": self.workspace}),
            check("workspace.check.non_canonical_surface", workspace_rel == DEFAULT_WORKSPACE, {"workspace_relative": workspace_rel}),
            check("workspace.check.read_only_no_creation", not workspace_state["exists"] or workspace_state["kind"] == "directory", workspace_state),
        ]
        drift_checks = [
            check("drift.check.draft_plan_identity_bound", source_hash == fresh_hash, {"source_hash": source_hash, "fresh_hash": fresh_hash}),
            check(
                "drift.check.discovery_fingerprint_bound",
                plan["source_inputs"]["discovery_bundle"]["source_fingerprint"]
                == fresh_plan["source_inputs"]["discovery_bundle"]["source_fingerprint"],
                {
                    "source": plan["source_inputs"]["discovery_bundle"]["source_fingerprint"],
                    "fresh": fresh_plan["source_inputs"]["discovery_bundle"]["source_fingerprint"],
                },
            ),
            check(
                "drift.check.construction_summary_bound",
                plan["source_inputs"]["construction_plan"] == fresh_plan["source_inputs"]["construction_plan"],
                {"source": plan["source_inputs"]["construction_plan"], "fresh": fresh_plan["source_inputs"]["construction_plan"]},
            ),
        ]
        validator_checks = [
            check(
                "validator.check.gate_passes",
                validator_report["summary"]["error"] == 0 and validator_report["summary"]["fatal"] == 0,
                validator_report["summary"],
            )
        ]
        all_checks = workspace_checks + drift_checks + validator_checks
        failed_checks = [entry["id"] for entry in all_checks if not entry["passed"]]
        ineligible_targets = [target["draft_item_id"] for target in targets if target["status"] != "eligible"]
        report = {
            "schema": SCHEMA,
            "id": "",
            "generated_at": generated_at or generated_timestamp(),
            "root": str(root),
            "read_only": True,
            "mission": {
                "id": mission_id,
                "release": release,
                "goal": goal,
            },
            "draft_workspace": {
                "type": "local_filesystem",
                "concept": "governed_non_canonical_draft_workspace",
                "physical_mapping": DEFAULT_WORKSPACE,
                "configured_mapping": self.workspace,
                "path": workspace_rel or self.workspace,
                "absolute_path": str(workspace_abs),
                "exists": workspace_state["exists"],
                "state": workspace_state,
                "valid": workspace_valid,
                "canonical_surface": False,
                "creates_workspace": False,
            },
            "source_plan": {
                "schema": plan["schema"],
                "hash": source_hash,
                "fresh_hash": fresh_hash,
                "identity_bound": source_hash == fresh_hash,
                "draft_item_count": plan["summary"]["draft_item_count"],
                "draftable_count": plan["summary"]["draftable_count"],
                "discovery_source_id": plan["source_inputs"]["discovery_bundle"]["source_id"],
                "discovery_fingerprint": plan["source_inputs"]["discovery_bundle"]["source_fingerprint"],
                "construction_plan": plan["source_inputs"]["construction_plan"],
            },
            "targets": sorted(targets, key=lambda item: item["draft_item_id"]),
            "validation": {
                "workspace_checks": workspace_checks,
                "drift_checks": drift_checks,
                "validator_checks": validator_checks,
                "validator": {
                    "schema": validator_report["schema"],
                    "summary": validator_report["summary"],
                },
            },
            "eligibility": {
                "eligible_for_future_draft_creation": not failed_checks and not ineligible_targets,
                "eligible_target_count": sum(1 for target in targets if target["status"] == "eligible"),
                "ineligible_target_count": len(ineligible_targets),
                "ineligible_targets": ineligible_targets,
                "failed_check_count": len(failed_checks),
                "failed_checks": failed_checks,
                "requires_l2_human_authority": True,
                "draft_creation_authorized": False,
                "promotion_authorized": False,
            },
            "constraints": {
                "writes_performed": False,
                "directories_created": False,
                "drafts_created": False,
                "ssot_modified": False,
                "canonical_context_modified": False,
                "promotion_performed": False,
                "authority_escalated": False,
                "external_connectors_used": False,
                "knowledge_engine_used": False,
                "graph_runtime_used": False,
                "agents_used": False,
            },
        }
        report["id"] = preflight_id(report)
        report["identity_hash"] = stable_hash(preflight_payload(report))
        return report
