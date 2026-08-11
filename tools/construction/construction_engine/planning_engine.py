from __future__ import annotations

import re
import sys
from pathlib import Path

from construction_engine.report_builder import build_report


CONSTRUCTION_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = Path(__file__).resolve().parents[2]
READINESS_ROOT = TOOLS_ROOT / "readiness"
BOOTSTRAP_ROOT = TOOLS_ROOT / "bootstrap"
for runtime_path in (READINESS_ROOT, BOOTSTRAP_ROOT):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

from bootstrap_engine.plan_engine import BootstrapPlanEngine  # noqa: E402
from readiness_engine.readiness_scoring import ReadinessScoringEngine  # noqa: E402


STANDARD_CONTEXT_ARTIFACTS = {
    "SSOT/S.1_Vision.md": {
        "artifact_class": "organizational_intent",
        "operation_domain": "strategy",
        "context_role": "purpose_true_north_customer_promise",
        "required_owner_role": "Product Owner",
    },
    "SSOT/P.1_Product_Map.md": {
        "artifact_class": "product_context",
        "operation_domain": "product",
        "context_role": "customer_journey_value_model_product_boundaries",
        "required_owner_role": "Product Owner",
    },
    "SSOT/P.2_Product_Roadmap.md": {
        "artifact_class": "roadmap_context",
        "operation_domain": "strategy",
        "context_role": "release_sequence_and_goals",
        "required_owner_role": "Product Owner",
    },
    "SSOT/A.1_System_Map.md": {
        "artifact_class": "system_context",
        "operation_domain": "technology",
        "context_role": "systems_components_boundaries",
        "required_owner_role": "Maintainer",
    },
    "SSOT/A.4_Data_Entities.md": {
        "artifact_class": "data_context",
        "operation_domain": "data",
        "context_role": "entities_relationships_and_semantics",
        "required_owner_role": "Maintainer",
    },
    "SSOT/G.1_Definition_of_Ready.md": {
        "artifact_class": "governance_context",
        "operation_domain": "operations",
        "context_role": "readiness_policy",
        "required_owner_role": "Maintainer",
    },
    "SSOT/G.2_Definition_of_Done.md": {
        "artifact_class": "governance_context",
        "operation_domain": "operations",
        "context_role": "completion_policy",
        "required_owner_role": "Maintainer",
    },
}


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return cleaned or "item"


def inventory_artifact_by_path(readiness_report: dict) -> dict[str, dict]:
    return {
        path: {"path": path}
        for path in readiness_report["inventory"].get("present_artifacts", [])
    }


def evidence_refs_for(path: str, readiness_report: dict, bootstrap_plan: dict) -> list[str]:
    refs = [path]
    for action in bootstrap_plan.get("actions", []):
        if action.get("target_path") == path:
            refs.extend(action.get("evidence_refs", []))
            refs.extend(action.get("recommendation_ids", []))
    for dimension in readiness_report.get("dimensions", {}).values():
        if path in dimension.get("evidence_refs", []):
            refs.append(f"readiness.dimension.{dimension['id']}")
    return sorted(dict.fromkeys(ref for ref in refs if ref))


def authority_for(definition: dict, lifecycle_state: str) -> dict:
    if lifecycle_state == "observed":
        return {
            "role": definition["required_owner_role"],
            "level": "L2",
            "reason": "Observed context requires human review before any update or promotion.",
        }
    return {
        "role": definition["required_owner_role"],
        "level": "L2",
        "reason": "Suggested construction may create drafts only after explicit human authorization.",
    }


def candidate_for(
    target_path: str,
    definition: dict,
    readiness_report: dict,
    bootstrap_plan: dict,
    present_artifacts: dict[str, dict],
) -> dict:
    present = target_path in present_artifacts
    lifecycle_state = "observed" if present else "suggested"
    belief_state = "observed" if present else "suggested"
    return {
        "id": f"construction.candidate.{slug(target_path)}",
        "target_path": target_path,
        "artifact_class": definition["artifact_class"],
        "operation_domain": definition["operation_domain"],
        "context_role": definition["context_role"],
        "lifecycle_state": lifecycle_state,
        "belief_state": belief_state,
        "truth_boundary": (
            "Artifact exists in the repository; content still requires review before update or canonical confidence changes."
            if present
            else "Artifact is missing or incomplete; Context OS may only suggest a draft path, not invent canonical content."
        ),
        "source_signals": {
            "inventory": "present" if present else "missing",
            "readiness_can_construct": readiness_report["summary"]["can_construct"],
            "bootstrap_ready": bootstrap_plan["summary"]["ready_for_bootstrap"],
        },
        "evidence_refs": evidence_refs_for(target_path, readiness_report, bootstrap_plan),
        "authority_required": authority_for(definition, lifecycle_state),
        "allowed_next_states": ["reviewed"] if present else ["draft"],
        "prohibited_transitions": [
            "suggested_to_canonical_verified",
            "draft_to_canonical_verified_without_review",
            "automatic_promotion",
        ],
    }


def action_for(candidate: dict) -> dict:
    if candidate["lifecycle_state"] == "observed":
        return {
            "id": f"construction.action.review_existing.{slug(candidate['target_path'])}",
            "status": "review",
            "type": "human_review",
            "target_path": candidate["target_path"],
            "reason": "Observed context artifact should be reviewed before construction updates are proposed.",
            "source_candidate_id": candidate["id"],
            "evidence_refs": candidate["evidence_refs"],
            "authority_required": candidate["authority_required"],
            "would_write": False,
            "would_promote_truth": False,
        }
    return {
        "id": f"construction.action.plan_draft.{slug(candidate['target_path'])}",
        "status": "manual",
        "type": "draft_planning",
        "target_path": candidate["target_path"],
        "reason": "Missing context artifact can become a draft only from explicit evidence and human-approved construction scope.",
        "source_candidate_id": candidate["id"],
        "evidence_refs": candidate["evidence_refs"],
        "authority_required": candidate["authority_required"],
        "would_write": False,
        "would_promote_truth": False,
    }


def blocking_actions(readiness_report: dict) -> list[dict]:
    validator_summary = readiness_report["validator"]["summary"]
    actions: list[dict] = []
    if validator_summary["fatal"] or validator_summary["error"]:
        actions.append(
            {
                "id": "construction.action.resolve_validator_blockers",
                "status": "blocked",
                "type": "validator_gate",
                "target_path": None,
                "reason": "Construction cannot promote context while Validator gate has blocking findings.",
                "source_candidate_id": None,
                "evidence_refs": ["validator.summary"],
                "authority_required": {
                    "role": "Maintainer",
                    "level": "L3",
                    "reason": "Blocking structural or governance findings require repository remediation.",
                },
                "would_write": False,
                "would_promote_truth": False,
            }
        )
    if not readiness_report["summary"]["can_construct"]:
        actions.append(
            {
                "id": "construction.action.reach_construction_readiness",
                "status": "blocked",
                "type": "readiness_gate",
                "target_path": None,
                "reason": "Readiness report does not yet mark the repository as constructable.",
                "source_candidate_id": None,
                "evidence_refs": ["readiness.summary"],
                "authority_required": {
                    "role": "Mission Owner",
                    "level": "L2",
                    "reason": "A human must decide whether to remediate readiness gaps before construction.",
                },
                "would_write": False,
                "would_promote_truth": False,
            }
        )
    return actions


class ContextConstructionPlanEngine:
    """Read-only engine that plans governed construction from observed evidence."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        readiness_report: dict | None = None,
        bootstrap_plan: dict | None = None,
        generated_at: str | None = None,
    ) -> dict:
        resolved_root = self.root.resolve()
        readiness = readiness_report or ReadinessScoringEngine(resolved_root).run(generated_at=generated_at)
        bootstrap = bootstrap_plan or BootstrapPlanEngine(resolved_root).run(readiness_report=readiness, generated_at=generated_at)
        present_artifacts = inventory_artifact_by_path(readiness)
        candidates = [
            candidate_for(path, definition, readiness, bootstrap, present_artifacts)
            for path, definition in STANDARD_CONTEXT_ARTIFACTS.items()
        ]
        actions = [action_for(candidate) for candidate in candidates]
        actions.extend(blocking_actions(readiness))
        return build_report(resolved_root, readiness, bootstrap, candidates, actions, generated_at=generated_at)
