from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

from readiness_engine.recommendations import generate_recommendations
from readiness_engine.report_builder import build_dimension, build_report


READINESS_ROOT = Path(__file__).resolve().parents[1]
VALIDATORS_ROOT = Path(__file__).resolve().parents[2] / "validators"
for runtime_path in (READINESS_ROOT, VALIDATORS_ROOT):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

from engine.validator_engine import ValidatorEngine  # noqa: E402
from inventory_engine.repository_inventory import RepositoryInventoryEngine  # noqa: E402


DIMENSION_WEIGHTS = {
    "inventory": 20,
    "structure": 20,
    "governance": 20,
    "operational_map": 15,
    "runtime": 15,
    "source_evidence": 10,
}

INVENTORY_CLASSES = {
    "repository-readme": "Repository README is visible.",
    "architecture": "Architecture documentation is visible.",
    "operation": "Operational documentation is visible.",
    "strategy": "Strategy documentation is visible.",
    "ssot-strategy": "SSOT strategy artifact is visible.",
    "ssot-product": "SSOT product artifact is visible.",
    "ssot-architecture": "SSOT architecture artifact is visible.",
    "ssot-governance": "SSOT governance artifacts are visible.",
    "ssot-epic": "SSOT epic backlog is visible.",
}

GOVERNANCE_KINDS = {
    "agent-rules": "Agent rules are present.",
    "authority-model": "Human-agent authority model is present.",
    "governance-protocol": "Governance protocol is present.",
    "ssot-governance": "DoR/DoD governance artifacts are present.",
    "epic-governance": "Epic governance artifacts are present.",
}

OPERATIONAL_ARTIFACTS = {
    "SSOT/S.1_Vision.md": "Vision artifact is present.",
    "SSOT/P.1_Product_Map.md": "Product map is present.",
    "SSOT/P.2_Product_Roadmap.md": "Product roadmap is present.",
    "SSOT/A.1_System_Map.md": "System map is present.",
    "SSOT/A.4_Data_Entities.md": "Data entity map is present.",
    "SSOT/G.1_Definition_of_Ready.md": "Definition of Ready is present.",
    "SSOT/G.2_Definition_of_Done.md": "Definition of Done is present.",
    "docs/3.x_operation/3.0_COS_Minimum_Operational_Map.md": "Minimum Operational Map documentation is present.",
}

RUNTIME_COMPONENTS = {
    "runtime-cli": "Runtime CLI artifacts are present.",
    "validator-engine": "Validator Engine artifacts are present.",
    "runtime-contract": "Runtime contracts are present.",
    "context-readiness-engine": "Context Readiness Engine artifacts are present.",
}

SOURCE_EVIDENCE_BUCKETS = {
    "README.md": "Repository README provides a first source signal.",
    "docs/": "Documentation corpus provides local evidence.",
    "SSOT/": "SSOT corpus provides structured evidence.",
    "examples/": "Examples provide adoption evidence.",
    "tools/": "Local runtime/tooling source is available.",
}

STRUCTURE_RULE_PREFIXES = {"structure", "naming", "links", "taxonomy"}
GOVERNANCE_RULE_PREFIXES = {"ownership", "governance", "authority"}
OPERATIONAL_RULE_PREFIXES = {"mom", "hypothesis"}
RUNTIME_RULES = {"structure.runtime_manifest", "drift.discovery_bundle_available"}


def as_paths(inventory_report: dict) -> set[str]:
    return {artifact["path"] for artifact in inventory_report["detected"]["artifacts"]}


def taxonomy_paths(inventory_report: dict) -> dict[str, list[str]]:
    return {item["id"]: item["paths"] for item in inventory_report["detected"]["taxonomy_classes"]}


def score_presence(present_count: int, total_count: int) -> int:
    if total_count == 0:
        return 0
    return round((present_count / total_count) * 100)


def limited_refs(paths: list[str], limit: int = 20) -> list[str]:
    return sorted(dict.fromkeys(path for path in paths if path))[:limit]


def findings_for_prefixes(validator_report: dict, prefixes: set[str]) -> list[dict]:
    return [finding for finding in validator_report["findings"] if finding["rule"].split(".", 1)[0] in prefixes]


def findings_for_rules(validator_report: dict, rules: set[str]) -> list[dict]:
    return [finding for finding in validator_report["findings"] if finding["rule"] in rules]


def severity_counts(findings: list[dict]) -> Counter:
    return Counter(finding["severity"] for finding in findings)


def score_from_findings(findings: list[dict], warning_cap: int = 35) -> int:
    counts = severity_counts(findings)
    if counts["fatal"]:
        return 0
    if counts["error"]:
        return max(20, 60 - counts["error"] * 10)
    return max(0, 100 - min(warning_cap, round(counts["warn"] * 0.5)))


def finding_refs(findings: list[dict]) -> list[str]:
    return limited_refs([finding["path"] for finding in findings if finding.get("path")])


def finding_rule_summary(findings: list[dict]) -> list[str]:
    counts = Counter(finding["rule"] for finding in findings)
    return [f"{rule}: {count}" for rule, count in sorted(counts.items())]


def build_inventory_dimension(inventory_report: dict) -> dict:
    paths_by_class = taxonomy_paths(inventory_report)
    present = [class_id for class_id in INVENTORY_CLASSES if class_id in paths_by_class]
    missing = [class_id for class_id in INVENTORY_CLASSES if class_id not in paths_by_class]
    signals = [INVENTORY_CLASSES[class_id] for class_id in present]
    gaps = [f"Missing inventory class: {class_id}." for class_id in missing]
    artifact_count = inventory_report["summary"]["artifact_count"]
    if artifact_count:
        signals.insert(0, f"{artifact_count} Context OS-relevant artifacts detected.")
    else:
        gaps.insert(0, "No Context OS-relevant artifacts were detected.")
    evidence = []
    for class_id in present:
        evidence.extend(paths_by_class[class_id])
    score = score_presence(len(present), len(INVENTORY_CLASSES))
    return build_dimension("inventory", score, DIMENSION_WEIGHTS["inventory"], signals, gaps, limited_refs(evidence))


def build_structure_dimension(validator_report: dict) -> dict:
    findings = findings_for_prefixes(validator_report, STRUCTURE_RULE_PREFIXES)
    counts = severity_counts(findings)
    signals = []
    gaps = []
    if counts["fatal"] or counts["error"]:
        gaps.append(f"{counts['fatal'] + counts['error']} blocking structural findings detected.")
    else:
        signals.append("Validator reports zero blocking structural findings.")
    if counts["warn"]:
        gaps.extend(f"Structural warning group: {item}." for item in finding_rule_summary(findings))
    else:
        signals.append("No structural warnings detected.")
    score = score_from_findings(findings)
    return build_dimension("structure", score, DIMENSION_WEIGHTS["structure"], signals, gaps, finding_refs(findings))


def build_governance_dimension(inventory_report: dict, validator_report: dict) -> dict:
    governance_artifacts = inventory_report["detected"]["governance_artifacts"]
    present_kinds = {artifact["kind"] for artifact in governance_artifacts}
    present = [kind for kind in GOVERNANCE_KINDS if kind in present_kinds]
    missing = [kind for kind in GOVERNANCE_KINDS if kind not in present_kinds]
    findings = findings_for_prefixes(validator_report, GOVERNANCE_RULE_PREFIXES)
    counts = severity_counts(findings)
    signals = [GOVERNANCE_KINDS[kind] for kind in present]
    gaps = [f"Missing governance signal: {kind}." for kind in missing]
    if counts["fatal"] or counts["error"]:
        gaps.append(f"{counts['fatal'] + counts['error']} blocking governance findings detected.")
    if counts["warn"]:
        gaps.extend(f"Governance warning group: {item}." for item in finding_rule_summary(findings))
    else:
        signals.append("No governance warnings detected.")
    presence_score = score_presence(len(present), len(GOVERNANCE_KINDS))
    validator_score = score_from_findings(findings)
    score = round((presence_score + validator_score) / 2)
    evidence = [artifact["path"] for artifact in governance_artifacts] + finding_refs(findings)
    return build_dimension("governance", score, DIMENSION_WEIGHTS["governance"], signals, gaps, limited_refs(evidence))


def build_operational_map_dimension(inventory_report: dict, validator_report: dict) -> dict:
    paths = as_paths(inventory_report)
    present = [path for path in OPERATIONAL_ARTIFACTS if path in paths]
    missing = [path for path in OPERATIONAL_ARTIFACTS if path not in paths]
    findings = findings_for_prefixes(validator_report, OPERATIONAL_RULE_PREFIXES)
    counts = severity_counts(findings)
    signals = [OPERATIONAL_ARTIFACTS[path] for path in present]
    gaps = [f"Missing operational map artifact: {path}." for path in missing]
    if counts["fatal"] or counts["error"]:
        gaps.append(f"{counts['fatal'] + counts['error']} blocking operational-map findings detected.")
    if counts["warn"]:
        gaps.extend(f"Operational map warning group: {item}." for item in finding_rule_summary(findings))
    else:
        signals.append("No operational-map warnings detected.")
    presence_score = score_presence(len(present), len(OPERATIONAL_ARTIFACTS))
    validator_score = score_from_findings(findings, warning_cap=25)
    score = round((presence_score * 0.75) + (validator_score * 0.25))
    return build_dimension(
        "operational_map",
        score,
        DIMENSION_WEIGHTS["operational_map"],
        signals,
        gaps,
        limited_refs(present + finding_refs(findings)),
    )


def build_runtime_dimension(inventory_report: dict, validator_report: dict) -> dict:
    runtime_artifacts = inventory_report["detected"]["runtime_artifacts"]
    components = {artifact["component"] for artifact in runtime_artifacts}
    present = [component for component in RUNTIME_COMPONENTS if component in components]
    missing = [component for component in RUNTIME_COMPONENTS if component not in components]
    paths = as_paths(inventory_report)
    manifest_present = any(path.startswith(".contextos/manifest.") for path in paths)
    findings = findings_for_rules(validator_report, RUNTIME_RULES)
    signals = [RUNTIME_COMPONENTS[component] for component in present]
    gaps = [f"Missing runtime component: {component}." for component in missing]
    if manifest_present:
        signals.append("Runtime manifest is present.")
    else:
        gaps.append("Runtime manifest is absent.")
    if validator_report["summary"]["exit_code"] == 0:
        signals.append("ValidatorEngine completed without blocking failures.")
    else:
        gaps.append("ValidatorEngine reported blocking failures.")
    component_score = score_presence(len(present), len(RUNTIME_COMPONENTS))
    score = round((component_score * 0.85) + (15 if manifest_present else 0))
    evidence = [artifact["path"] for artifact in runtime_artifacts] + finding_refs(findings)
    return build_dimension("runtime", score, DIMENSION_WEIGHTS["runtime"], signals, gaps, limited_refs(evidence))


def source_bucket_present(paths: set[str], bucket: str) -> bool:
    if bucket.endswith("/"):
        return any(path.startswith(bucket) for path in paths)
    return bucket in paths


def build_source_evidence_dimension(inventory_report: dict) -> dict:
    paths = as_paths(inventory_report)
    present = [bucket for bucket in SOURCE_EVIDENCE_BUCKETS if source_bucket_present(paths, bucket)]
    missing = [bucket for bucket in SOURCE_EVIDENCE_BUCKETS if bucket not in present]
    signals = [SOURCE_EVIDENCE_BUCKETS[bucket] for bucket in present]
    gaps = [f"Missing source evidence bucket: {bucket}." for bucket in missing]
    evidence = []
    for bucket in present:
        if bucket.endswith("/"):
            evidence.extend(path for path in paths if path.startswith(bucket))
        else:
            evidence.append(bucket)
    score = score_presence(len(present), len(SOURCE_EVIDENCE_BUCKETS))
    return build_dimension(
        "source_evidence",
        score,
        DIMENSION_WEIGHTS["source_evidence"],
        signals,
        gaps,
        limited_refs(evidence),
    )


def artifact_counts(inventory_report: dict) -> dict:
    paths = as_paths(inventory_report)
    return {
        "docs": sum(1 for path in paths if path.startswith("docs/")),
        "ssot": sum(1 for path in paths if path.startswith("SSOT/")),
        "epics": sum(1 for path in paths if path.startswith("SSOT/epics/")),
        "ops": sum(1 for path in paths if path.startswith("ops/")),
        "templates": sum(1 for path in paths if path.startswith("templates/")),
        "examples": sum(1 for path in paths if path.startswith("examples/")),
    }


def inventory_summary(inventory_report: dict) -> dict:
    paths = sorted(as_paths(inventory_report))
    missing = [path for path in OPERATIONAL_ARTIFACTS if path not in paths]
    return {
        "schema": inventory_report["schema"],
        "summary": inventory_report["summary"],
        "artifact_counts": artifact_counts(inventory_report),
        "present_artifacts": paths,
        "missing_artifacts": missing,
    }


def validator_summary(validator_report: dict) -> dict:
    top_findings = [
        {
            "id": finding["id"],
            "rule": finding["rule"],
            "severity": finding["severity"],
            "path": finding["path"],
            "message": finding["message"],
        }
        for finding in validator_report["findings"][:10]
    ]
    return {
        "schema": validator_report["schema"],
        "mode": validator_report["mode"],
        "summary": validator_report["summary"],
        "top_findings": top_findings,
    }


def weighted_score(dimensions: dict) -> int:
    score = 0.0
    for dimension in dimensions.values():
        score += dimension["score"] * (dimension["weight"] / 100)
    return round(score)


def ownership_absent(validator_report: dict) -> bool:
    return any(finding["rule"] == "ownership.framework_owner_present" for finding in validator_report["findings"])


def manifest_absent(validator_report: dict, inventory_report: dict) -> bool:
    paths = as_paths(inventory_report)
    if any(path.startswith(".contextos/manifest.") for path in paths):
        return False
    return any(finding["rule"] == "structure.runtime_manifest" for finding in validator_report["findings"])


def apply_score_caps(score: int, inventory_report: dict, validator_report: dict) -> tuple[int, list[str]]:
    capped = score
    reasons: list[str] = []
    summary = validator_report["summary"]
    if summary["fatal"]:
        capped = min(capped, 19)
        reasons.append("Validator returned fatal findings; maximum readiness level is R0.")
    elif summary["error"]:
        capped = min(capped, 59)
        reasons.append("Validator returned error findings; maximum readiness level is R2.")
    if inventory_report["summary"]["taxonomy_class_count"] == 0:
        capped = min(capped, 39)
        reasons.append("No Context OS-relevant taxonomy classes were found; maximum readiness level is R1.")
    if ownership_absent(validator_report):
        capped = min(capped, 74)
        reasons.append("Framework ownership is not fully declared; maximum readiness level is R3.")
    if manifest_absent(validator_report, inventory_report):
        capped = min(capped, 89)
        reasons.append("Runtime manifest is absent; maximum readiness level is R4.")
    return capped, reasons


class ReadinessScoringEngine:
    """Read-only Context Readiness scoring engine."""

    def __init__(self, root: str | Path = ".", validator_mode: str = "full") -> None:
        self.root = Path(root)
        self.validator_mode = validator_mode

    def run(
        self,
        inventory_report: dict | None = None,
        validator_report: dict | None = None,
        generated_at: str | None = None,
    ) -> dict:
        resolved_root = self.root.resolve()
        inventory = inventory_report or RepositoryInventoryEngine(resolved_root).run(generated_at=generated_at)
        validator = validator_report or ValidatorEngine(resolved_root).run(mode=self.validator_mode)
        dimensions = {
            "inventory": build_inventory_dimension(inventory),
            "structure": build_structure_dimension(validator),
            "governance": build_governance_dimension(inventory, validator),
            "operational_map": build_operational_map_dimension(inventory, validator),
            "runtime": build_runtime_dimension(inventory, validator),
            "source_evidence": build_source_evidence_dimension(inventory),
        }
        uncapped_score = weighted_score(dimensions)
        score, cap_reasons = apply_score_caps(uncapped_score, inventory, validator)
        embedded_inventory = inventory_summary(inventory)
        embedded_validator = validator_summary(validator)
        recommendations = generate_recommendations(dimensions, embedded_inventory, validator, cap_reasons)
        return build_report(
            resolved_root,
            dimensions,
            embedded_inventory,
            embedded_validator,
            score,
            uncapped_score,
            cap_reasons,
            recommendations,
            generated_at=generated_at,
        )
