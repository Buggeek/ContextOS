from __future__ import annotations


PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}

DIMENSION_RECOMMENDATIONS = {
    "inventory": ("coverage", "improve_inventory", "Improve context inventory coverage."),
    "structure": ("structure", "improve_structure", "Improve structural consistency."),
    "governance": ("governance", "improve_governance", "Improve governance signals."),
    "operational_map": ("construction", "improve_operational_map", "Improve operational map completeness."),
    "runtime": ("runtime", "improve_runtime", "Improve local runtime readiness."),
    "source_evidence": ("source_evidence", "improve_source_evidence", "Improve local source evidence."),
}


def limited_refs(paths: list[str], limit: int = 10) -> list[str]:
    return sorted(dict.fromkeys(path for path in paths if path))[:limit]


def make_recommendation(
    category: str,
    action: str,
    priority: str,
    title: str,
    rationale: str,
    suggested_action: str,
    related_dimension: str,
    evidence_refs: list[str] | None = None,
) -> dict:
    return {
        "id": f"readiness.{category}.{action}",
        "priority": priority,
        "category": category,
        "title": title,
        "rationale": rationale,
        "suggested_action": suggested_action,
        "suggested_next_action": suggested_action,
        "related_dimension": related_dimension,
        "evidence_refs": limited_refs(evidence_refs or []),
    }


def add_unique(recommendations: list[dict], recommendation: dict) -> None:
    if recommendation["id"] not in {item["id"] for item in recommendations}:
        recommendations.append(recommendation)


def findings_by_rule(validator_report: dict, rule: str) -> list[dict]:
    return [finding for finding in validator_report["findings"] if finding["rule"] == rule]


def blocking_findings(validator_report: dict) -> list[dict]:
    return [finding for finding in validator_report["findings"] if finding["severity"] in {"error", "fatal"}]


def findings_with_prefix(validator_report: dict, prefix: str) -> list[dict]:
    return [finding for finding in validator_report["findings"] if finding["rule"].startswith(prefix)]


def finding_paths(findings: list[dict]) -> list[str]:
    return [finding["path"] for finding in findings if finding.get("path")]


def manifest_missing(dimensions: dict, validator_report: dict) -> bool:
    if findings_by_rule(validator_report, "structure.runtime_manifest"):
        return True
    return any("manifest is absent" in gap.lower() for gap in dimensions["runtime"]["gaps"])


def generate_recommendations(
    dimensions: dict,
    inventory: dict,
    validator_report: dict,
    cap_reasons: list[str],
) -> list[dict]:
    recommendations: list[dict] = []

    blockers = blocking_findings(validator_report)
    if blockers:
        add_unique(
            recommendations,
            make_recommendation(
                "structure",
                "resolve_blocking_validator_findings",
                "P0",
                "Resolve blocking validator findings.",
                "The validator reported error or fatal findings, so the readiness assessment is capped before bootstrap.",
                "Run the validator, fix error/fatal findings, and re-run readiness scoring.",
                "structure",
                finding_paths(blockers),
            ),
        )

    if manifest_missing(dimensions, validator_report):
        manifest_findings = findings_by_rule(validator_report, "structure.runtime_manifest")
        add_unique(
            recommendations,
            make_recommendation(
                "runtime",
                "create_manifest",
                "P1",
                "Create the Runtime manifest.",
                "The repository is missing `.contextos/manifest.yaml`, which caps readiness before construction.",
                "Add the Runtime manifest during the guided bootstrap slice, then re-run readiness.",
                "runtime",
                finding_paths(manifest_findings) or [".contextos/manifest.yaml"],
            ),
        )

    ownership_findings = findings_by_rule(validator_report, "ownership.framework_owner_present")
    if ownership_findings or any("ownership" in reason.lower() for reason in cap_reasons):
        add_unique(
            recommendations,
            make_recommendation(
                "ownership",
                "assign_framework_owners",
                "P1",
                "Assign owners to framework artifacts.",
                "Framework artifacts without explicit ownership cap readiness before construction.",
                "Declare accountable owners for framework artifacts that are moving under strict governance.",
                "governance",
                finding_paths(ownership_findings),
            ),
        )

    missing_mom = inventory.get("missing_artifacts", [])
    if missing_mom:
        add_unique(
            recommendations,
            make_recommendation(
                "coverage",
                "add_operational_map_artifacts",
                "P1",
                "Add missing operational map artifacts.",
                "The assessment could not find all minimum operational map artifacts needed for guided bootstrap.",
                "Create or restore the missing MOM/SSOT artifacts before relying on readiness results for construction.",
                "operational_map",
                missing_mom,
            ),
        )

    mom_findings = findings_with_prefix(validator_report, "mom.")
    if mom_findings:
        add_unique(
            recommendations,
            make_recommendation(
                "construction",
                "complete_mom_fields",
                "P2",
                "Complete MOM and SSOT metadata fields.",
                "Validator findings show incomplete MOM/SSOT fields or sections.",
                "Fill the missing MOM/SSOT fields and sections called out by the validator.",
                "operational_map",
                finding_paths(mom_findings),
            ),
        )

    for dimension_id, dimension in dimensions.items():
        if dimension["score"] >= 75:
            continue
        category, action, title = DIMENSION_RECOMMENDATIONS[dimension_id]
        add_unique(
            recommendations,
            make_recommendation(
                category,
                action,
                "P2",
                title,
                f"The `{dimension_id}` dimension scored {dimension['score']}/100 with status `{dimension['status']}`.",
                "Address the listed dimension gaps, then re-run readiness scoring.",
                dimension_id,
                dimension.get("evidence_refs", []),
            ),
        )

    return sorted(recommendations, key=lambda item: (PRIORITY_ORDER[item["priority"]], item["id"]))
