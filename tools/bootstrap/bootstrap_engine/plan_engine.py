from __future__ import annotations

import re
import sys
from pathlib import Path

from bootstrap_engine.report_builder import build_report


BOOTSTRAP_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = Path(__file__).resolve().parents[2]
READINESS_ROOT = TOOLS_ROOT / "readiness"
if str(READINESS_ROOT) not in sys.path:
    sys.path.insert(0, str(READINESS_ROOT))

from readiness_engine.readiness_scoring import ReadinessScoringEngine  # noqa: E402


FUTURE_APPLY_PHASE = "v0.4_apply"

STANDARD_DIRECTORIES = (
    ".contextos",
    "SSOT",
    "SSOT/epics",
    "docs",
    "ops",
    "templates",
)

STANDARD_FILES = {
    ".contextos/manifest.yaml": {
        "type": "create_manifest",
        "reason": "Runtime manifest is required for guided bootstrap.",
        "recommendation_ids": ["readiness.runtime.create_manifest"],
        "related_dimension": "runtime",
        "source_template": None,
        "blocked_without_template": False,
    },
    "SSOT/S.1_Vision.md": {
        "type": "create_from_template",
        "reason": "Vision artifact is part of the minimum operational map.",
        "recommendation_ids": ["readiness.coverage.add_operational_map_artifacts"],
        "related_dimension": "operational_map",
        "source_template": "templates/strategy/S.1_Vision.template.md",
        "blocked_without_template": False,
    },
    "SSOT/P.1_Product_Map.md": {
        "type": "create_from_template",
        "reason": "Product map is part of the minimum operational map.",
        "recommendation_ids": ["readiness.coverage.add_operational_map_artifacts"],
        "related_dimension": "operational_map",
        "source_template": "templates/product/P.1_Product_Map.template.md",
        "blocked_without_template": False,
    },
    "SSOT/P.2_Product_Roadmap.md": {
        "type": "create_from_template",
        "reason": "Product roadmap scaffold is required before construction readiness.",
        "recommendation_ids": ["readiness.coverage.add_operational_map_artifacts"],
        "related_dimension": "operational_map",
        "source_template": None,
        "blocked_without_template": True,
    },
    "SSOT/A.1_System_Map.md": {
        "type": "create_from_template",
        "reason": "System map is part of the minimum operational map.",
        "recommendation_ids": ["readiness.coverage.add_operational_map_artifacts"],
        "related_dimension": "operational_map",
        "source_template": "templates/architecture/A.1_System_Map.template.md",
        "blocked_without_template": False,
    },
    "SSOT/A.4_Data_Entities.md": {
        "type": "create_from_template",
        "reason": "Data entities map is part of the minimum operational map.",
        "recommendation_ids": ["readiness.coverage.add_operational_map_artifacts"],
        "related_dimension": "operational_map",
        "source_template": "templates/architecture/A.4_Data_Entities.template.md",
        "blocked_without_template": False,
    },
    "SSOT/G.1_Definition_of_Ready.md": {
        "type": "create_from_template",
        "reason": "Definition of Ready is part of the minimum governance set.",
        "recommendation_ids": ["readiness.coverage.add_operational_map_artifacts"],
        "related_dimension": "governance",
        "source_template": "templates/governance/G.1_Definition_of_Ready.template.md",
        "blocked_without_template": False,
    },
    "SSOT/G.2_Definition_of_Done.md": {
        "type": "create_from_template",
        "reason": "Definition of Done is part of the minimum governance set.",
        "recommendation_ids": ["readiness.coverage.add_operational_map_artifacts"],
        "related_dimension": "governance",
        "source_template": "templates/governance/G.2_Definition_of_Done.template.md",
        "blocked_without_template": False,
    },
    "SSOT/epics/README.md": {
        "type": "create_from_template",
        "reason": "Epic backlog index is needed for governed execution planning.",
        "recommendation_ids": ["readiness.coverage.add_operational_map_artifacts"],
        "related_dimension": "operational_map",
        "source_template": None,
        "blocked_without_template": True,
    },
    "ops/AGENT_RULES.md": {
        "type": "create_from_template",
        "reason": "Agent rules are required for governance visibility.",
        "recommendation_ids": ["readiness.governance.improve_governance"],
        "related_dimension": "governance",
        "source_template": None,
        "blocked_without_template": True,
    },
    "docs/3.x_operation/3.0_COS_Minimum_Operational_Map.md": {
        "type": "create_from_template",
        "reason": "Operational map documentation is part of the readiness model.",
        "recommendation_ids": ["readiness.coverage.add_operational_map_artifacts"],
        "related_dimension": "operational_map",
        "source_template": None,
        "blocked_without_template": True,
    },
}

MANUAL_RECOMMENDATIONS = {
    "readiness.structure.resolve_blocking_validator_findings": {
        "type": "manual_remediation",
        "status": "blocked",
        "reason": "Validator blocking findings must be resolved before bootstrap can be considered ready.",
        "related_dimension": "structure",
    },
    "readiness.ownership.assign_framework_owners": {
        "type": "manual_remediation",
        "status": "manual",
        "reason": "Framework ownership gaps require human ownership decisions.",
        "related_dimension": "governance",
    },
    "readiness.construction.complete_mom_fields": {
        "type": "manual_remediation",
        "status": "manual",
        "reason": "Incomplete MOM/SSOT fields require human review before construction.",
        "related_dimension": "operational_map",
    },
    "readiness.structure.improve_structure": {
        "type": "manual_remediation",
        "status": "manual",
        "reason": "Structural warnings should be reviewed before applying bootstrap changes.",
        "related_dimension": "structure",
    },
    "readiness.coverage.improve_inventory": {
        "type": "manual_remediation",
        "status": "manual",
        "reason": "Inventory coverage is low and may require additional local context.",
        "related_dimension": "inventory",
    },
    "readiness.governance.improve_governance": {
        "type": "manual_remediation",
        "status": "manual",
        "reason": "Governance gaps require human authority and ownership decisions.",
        "related_dimension": "governance",
    },
    "readiness.runtime.improve_runtime": {
        "type": "manual_remediation",
        "status": "manual",
        "reason": "Runtime readiness gaps require guided bootstrap setup.",
        "related_dimension": "runtime",
    },
    "readiness.source_evidence.improve_source_evidence": {
        "type": "manual_remediation",
        "status": "manual",
        "reason": "Source evidence gaps require adding or declaring more local context.",
        "related_dimension": "source_evidence",
    },
}


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return cleaned or "action"


def action_id(prefix: str, value: str) -> str:
    return f"bootstrap.action.{prefix}.{slug(value)}"


def existing_paths(root: Path) -> set[str]:
    paths: set[str] = set()
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        paths.add(path.relative_to(root).as_posix())
    return paths


def template_exists(template: str | None) -> bool:
    if template is None:
        return False
    return (TOOLS_ROOT.parent / template).exists()


def make_action(
    action_id_value: str,
    action_type: str,
    status: str,
    target_path: str | None,
    reason: str,
    recommendation_ids: list[str],
    related_dimension: str,
    evidence_refs: list[str] | None = None,
    source_template: str | None = None,
) -> dict:
    return {
        "id": action_id_value,
        "type": action_type,
        "status": status,
        "target_path": target_path,
        "would_create": status == "required",
        "would_skip": status == "skipped_existing",
        "blocked": status == "blocked",
        "reason": reason,
        "recommendation_ids": recommendation_ids,
        "related_dimension": related_dimension,
        "evidence_refs": sorted(dict.fromkeys(evidence_refs or [])),
        "source_template": source_template,
        "future_apply_phase": FUTURE_APPLY_PHASE,
        "reversible": action_type in {"create_directory", "create_manifest", "create_from_template"},
    }


def recommendation_by_id(readiness_report: dict) -> dict[str, dict]:
    return {item["id"]: item for item in readiness_report.get("recommendations", [])}


def recommendation_present(readiness_report: dict, recommendation_id: str) -> bool:
    return recommendation_id in recommendation_by_id(readiness_report)


def recommendation_evidence(readiness_report: dict, recommendation_id: str) -> list[str]:
    recommendation = recommendation_by_id(readiness_report).get(recommendation_id)
    if not recommendation:
        return []
    return recommendation.get("evidence_refs", [])


class BootstrapPlanEngine:
    """Read-only engine that converts readiness output into a bootstrap plan."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(self, readiness_report: dict | None = None, generated_at: str | None = None) -> dict:
        resolved_root = self.root.resolve()
        readiness = readiness_report or ReadinessScoringEngine(resolved_root).run(generated_at=generated_at)
        actions = build_actions(resolved_root, readiness)
        return build_report(resolved_root, readiness, actions, generated_at=generated_at)


def build_actions(root: Path, readiness_report: dict) -> list[dict]:
    present = existing_paths(root)
    actions: list[dict] = []
    actions.extend(directory_actions(present))
    actions.extend(file_actions(present, readiness_report))
    actions.extend(manual_actions(readiness_report))
    actions.append(validate_after_apply_action())
    return dedupe_actions(actions)


def directory_actions(present: set[str]) -> list[dict]:
    actions: list[dict] = []
    for directory in STANDARD_DIRECTORIES:
        status = "skipped_existing" if directory in present else "required"
        actions.append(
            make_action(
                action_id("create_directory", directory),
                "create_directory",
                status,
                directory,
                "Bootstrap requires the canonical directory to exist.",
                [],
                "inventory",
            )
        )
    return actions


def file_actions(present: set[str], readiness_report: dict) -> list[dict]:
    actions: list[dict] = []
    for target_path, spec in STANDARD_FILES.items():
        if target_path in present:
            status = "skipped_existing"
        elif spec["blocked_without_template"] and not template_exists(spec["source_template"]):
            status = "blocked"
        else:
            status = "required"
        rec_ids = [rec_id for rec_id in spec["recommendation_ids"] if recommendation_present(readiness_report, rec_id)]
        evidence = []
        for rec_id in rec_ids:
            evidence.extend(recommendation_evidence(readiness_report, rec_id))
        actions.append(
            make_action(
                action_id(spec["type"], target_path),
                spec["type"],
                status,
                target_path,
                spec["reason"],
                rec_ids,
                spec["related_dimension"],
                evidence_refs=evidence or [target_path],
                source_template=spec["source_template"],
            )
        )
    return actions


def manual_actions(readiness_report: dict) -> list[dict]:
    actions: list[dict] = []
    for recommendation in readiness_report.get("recommendations", []):
        spec = MANUAL_RECOMMENDATIONS.get(recommendation["id"])
        if spec is None:
            continue
        actions.append(
            make_action(
                action_id(spec["type"], recommendation["id"]),
                spec["type"],
                spec["status"],
                None,
                spec["reason"],
                [recommendation["id"]],
                spec["related_dimension"],
                evidence_refs=recommendation.get("evidence_refs", []),
            )
        )
    return actions


def validate_after_apply_action() -> dict:
    return make_action(
        "bootstrap.action.validate_after_apply.pre_bootstrap",
        "validate_after_apply",
        "manual",
        None,
        "After a future apply phase, run `contextos validate --mode pre-bootstrap`.",
        [],
        "structure",
    )


def dedupe_actions(actions: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}
    for action in actions:
        deduped[action["id"]] = action
    return list(deduped.values())
