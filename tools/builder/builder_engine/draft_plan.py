from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

from builder_engine.report_builder import build_report


BUILDER_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = Path(__file__).resolve().parents[2]
DISCOVERY_ROOT = TOOLS_ROOT / "discovery"
CONSTRUCTION_ROOT = TOOLS_ROOT / "construction"
for runtime_path in (DISCOVERY_ROOT, CONSTRUCTION_ROOT):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

from construction_engine.planning_engine import ContextConstructionPlanEngine  # noqa: E402
from discovery_engine.local_discovery import LocalDiscoveryBundleEngine  # noqa: E402


def slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return cleaned or "item"


def discovery_artifacts_by_path(discovery_bundle: dict) -> dict[str, dict]:
    return {artifact["path"]: artifact for artifact in discovery_bundle.get("artifacts", [])}


def ownership_by_path(discovery_bundle: dict) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in discovery_bundle.get("ownership_evidence", []):
        grouped[item["path"]].append(item)
    return grouped


def relationship_refs_for(path: str, discovery_bundle: dict) -> list[str]:
    refs: list[str] = []
    for relationship in discovery_bundle.get("relationships", []):
        if relationship["from"] == path or relationship["to"] == path:
            refs.append(relationship["id"])
    return sorted(dict.fromkeys(refs))[:20]


def contradictions_for_ownership(ownership_items: list[dict]) -> list[dict]:
    values_by_field: dict[str, set[str]] = defaultdict(set)
    for item in ownership_items:
        values_by_field[item["field"].lower()].add(item["value"])
    contradictions: list[dict] = []
    for field, values in sorted(values_by_field.items()):
        if len(values) > 1:
            contradictions.append(
                {
                    "type": "conflicting_ownership_evidence",
                    "field": field,
                    "values": sorted(values),
                    "truth_boundary": "Multiple owner-like values were observed; Context OS does not choose between them.",
                }
            )
    return contradictions


def support_for(candidate: dict, discovery_artifact: dict | None, ownership_items: list[dict], relationship_refs: list[str]) -> dict:
    evidence_count = len(candidate.get("evidence_refs", []))
    if discovery_artifact:
        evidence_count += 1
    evidence_count += len(ownership_items) + len(relationship_refs)
    if discovery_artifact and candidate["lifecycle_state"] == "observed":
        return {
            "level": "strong",
            "confidence": "observed_artifact_with_local_provenance",
            "evidence_count": evidence_count,
        }
    if candidate["lifecycle_state"] == "suggested" and evidence_count >= 2:
        return {
            "level": "moderate",
            "confidence": "suggested_by_readiness_and_bootstrap_evidence",
            "evidence_count": evidence_count,
        }
    if evidence_count:
        return {
            "level": "weak",
            "confidence": "limited_supporting_evidence",
            "evidence_count": evidence_count,
        }
    return {
        "level": "insufficient",
        "confidence": "no_direct_supporting_evidence",
        "evidence_count": 0,
    }


def unknowns_for(candidate: dict, discovery_artifact: dict | None, ownership_items: list[dict]) -> list[str]:
    unknowns = [
        "semantic completeness",
        "current correctness",
        "human-approved truth status",
    ]
    if not ownership_items:
        unknowns.append("explicit owner authority")
    if discovery_artifact is None:
        unknowns.extend(["source artifact content", "artifact-specific provenance"])
    if candidate["lifecycle_state"] == "suggested":
        unknowns.append("draft content")
    return sorted(dict.fromkeys(unknowns))


def missing_evidence_for(candidate: dict, discovery_artifact: dict | None, ownership_items: list[dict]) -> list[str]:
    missing: list[str] = []
    if discovery_artifact is None:
        missing.append("direct local artifact observation")
    if not ownership_items:
        missing.append("direct owner-like field")
    if candidate["lifecycle_state"] == "suggested":
        missing.append("human-authored draft source")
    return missing


def draftability_for(candidate: dict, support: dict, contradictions: list[dict], construction_plan: dict) -> dict:
    if construction_plan["summary"]["blocked_action_count"]:
        return {
            "status": "blocked",
            "reason": "Construction plan has blocking actions that must be resolved before draft creation.",
        }
    if contradictions:
        return {
            "status": "blocked",
            "reason": "Conflicting evidence requires human resolution before draft planning can proceed.",
        }
    if candidate["lifecycle_state"] == "observed":
        return {
            "status": "review_existing",
            "reason": "Existing context should be reviewed before a future update draft is proposed.",
        }
    if support["level"] in {"moderate", "strong"}:
        return {
            "status": "draftable",
            "reason": "Suggested context has enough non-semantic support for a future draft proposal.",
        }
    return {
        "status": "insufficient_evidence",
        "reason": "Not enough evidence exists to responsibly plan a draft.",
    }


def draft_item_for(candidate: dict, discovery_bundle: dict, construction_plan: dict) -> dict:
    artifacts = discovery_artifacts_by_path(discovery_bundle)
    owners = ownership_by_path(discovery_bundle)
    target = candidate["target_path"]
    discovery_artifact = artifacts.get(target)
    ownership_items = owners.get(target, [])
    relationship_refs = relationship_refs_for(target, discovery_bundle)
    contradictions = contradictions_for_ownership(ownership_items)
    support = support_for(candidate, discovery_artifact, ownership_items, relationship_refs)
    draftability = draftability_for(candidate, support, contradictions, construction_plan)
    status = draftability["status"]
    intended_state = "draft" if status == "draftable" else candidate["lifecycle_state"]
    evidence_refs = list(candidate.get("evidence_refs", []))
    if discovery_artifact:
        evidence_refs.append(discovery_artifact["id"])
    evidence_refs.extend(item["id"] for item in ownership_items)
    evidence_refs.extend(relationship_refs)
    return {
        "id": f"builder.draft_plan.{slug(target)}",
        "target_context_artifact": target,
        "operation_domain": candidate["operation_domain"],
        "artifact_class": candidate["artifact_class"],
        "context_role": candidate["context_role"],
        "source_candidate_id": candidate["id"],
        "status": status,
        "intended_lifecycle_state": intended_state,
        "source_states": {
            "construction_lifecycle_state": candidate["lifecycle_state"],
            "construction_belief_state": candidate["belief_state"],
            "discovery_artifact_state": "observed" if discovery_artifact else "unknown",
        },
        "support": support,
        "draftability": {
            **draftability,
            "would_create_or_modify_file": False,
            "would_promote_truth": False,
        },
        "provenance_chain": {
            "discovery_source_id": discovery_bundle["source"]["id"],
            "discovery_fingerprint": discovery_bundle["source"]["fingerprint"],
            "construction_candidate_id": candidate["id"],
            "evidence_refs": sorted(dict.fromkeys(evidence_refs)),
        },
        "observed_evidence_refs": sorted(
            dict.fromkeys(
                ([discovery_artifact["id"]] if discovery_artifact else [])
                + [item["id"] for item in ownership_items]
                + relationship_refs
            )
        ),
        "inferred_interpretations": [
            {
                "type": "draft_support_level",
                "value": support["level"],
                "truth_boundary": "Support level is a planning aid, not organizational truth.",
            },
            {
                "type": "artifact_classification",
                "value": candidate["artifact_class"],
                "truth_boundary": "Artifact class comes from construction mapping and requires future review.",
            },
        ],
        "unknowns": unknowns_for(candidate, discovery_artifact, ownership_items),
        "missing_evidence": missing_evidence_for(candidate, discovery_artifact, ownership_items),
        "contradictions": contradictions,
        "required_human_review": {
            "required": True,
            "role": candidate["authority_required"]["role"],
            "authority_level": candidate["authority_required"]["level"],
            "reason": "Future draft creation or review needs explicit human authority.",
        },
        "promotion_restrictions": [
            "no_automatic_promotion",
            "draft_requires_human_review",
            "approval_requires_accountable_human",
            "canonical_verification_requires_validator_gate",
        ],
    }


class BuilderDraftPlanEngine:
    """Read-only Builder engine that plans draftable context from evidence."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        discovery_bundle: dict | None = None,
        construction_plan: dict | None = None,
        generated_at: str | None = None,
    ) -> dict:
        resolved_root = self.root.resolve()
        discovery = discovery_bundle or LocalDiscoveryBundleEngine(resolved_root).run(generated_at=generated_at)
        construction = construction_plan or ContextConstructionPlanEngine(resolved_root).run(
            discovery_bundle=discovery,
            generated_at=generated_at,
        )
        draft_items = [
            draft_item_for(candidate, discovery, construction)
            for candidate in construction.get("context_artifact_candidates", [])
        ]
        return build_report(resolved_root, discovery, construction, draft_items, generated_at=generated_at)
