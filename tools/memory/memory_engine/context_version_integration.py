from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from .context_version_engine import ContextVersionEngine
from .context_version_report_builder import VERSION_SCHEMA


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


PACKAGE_PATTERN = re.compile(r"activation\.package\.[0-9a-f]+")
HANDOFF_PATTERN = re.compile(r"activation\.handoff\.[0-9a-f]+")
VERSION_PATTERN = re.compile(r"context\.version\.[0-9a-f]+")
COMMIT_PATTERN = re.compile(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])")


def _refs(values: list[str]) -> list[str]:
    return sorted(set(values))


def _source_availability(check: dict) -> str:
    source_count = check["checks"]["source_count"]
    resolved = check["checks"]["resolved_source_count"]
    if source_count and resolved == source_count:
        return "resolvable"
    if resolved:
        return "partial"
    return "unavailable"


def exact_context_evidence(version: dict, check: dict) -> dict:
    return {
        "binding_state": "exact",
        "context_version": {
            "id": version["id"],
            "identity_hash": version["identity_hash"],
            "capture_event": version["capture"]["event_type"],
            "captured_at": version["temporal"]["captured_at"],
            "historical_verification": check["result"]["historical_verification"],
            "applicability_at_capture": version["summary"]["current_applicability_at_capture"],
            "current_applicability": check["result"]["current_applicability"],
            "source_availability": _source_availability(check),
            "historically_valid_identity": check["result"]["historically_valid_identity"],
        },
        "lineage": version["lineage"],
        "activation_evidence": {
            "package": version["bindings"].get("activation_package"),
            "handoff": version["bindings"].get("activation_handoff"),
        },
        "continuity_gaps": check.get("continuity_gaps", []) + version.get("continuity_gaps", []),
        "authority": {
            "current_authority": "none_from_historical_context",
            "canonical_context_governs": True,
        },
        "semantic_applicability": "not_evaluated",
        "content_duplicated": False,
    }


def partial_context_evidence(mission: dict) -> dict:
    text = mission["raw_text"]
    packages = _refs(PACKAGE_PATTERN.findall(text))
    handoffs = _refs(HANDOFF_PATTERN.findall(text))
    versions = _refs(VERSION_PATTERN.findall(text))
    commits = _refs(COMMIT_PATTERN.findall(text))
    if not any((packages, handoffs, versions, commits)):
        return {
            "binding_state": "unknown",
            "context_version": None,
            "activation_evidence": {"package_ids": [], "handoff_ids": []},
            "implementation_evidence": {"git_commits": []},
            "continuity_gaps": [
                {
                    "id": "memory.gap.context_version_unavailable",
                    "status": "unknown",
                    "message": "No exact Context Version or partial implementation/Activation evidence was observed for this Mission.",
                }
            ],
            "authority": {"current_authority": "none_from_historical_context", "canonical_context_governs": True},
            "semantic_applicability": "not_evaluated",
            "content_duplicated": False,
        }
    return {
        "binding_state": "partial",
        "context_version": None,
        "referenced_context_version_ids": versions,
        "activation_evidence": {"package_ids": packages, "handoff_ids": handoffs},
        "implementation_evidence": {"git_commits": commits, "universal_context_version": False},
        "continuity_gaps": [
            {
                "id": "memory.gap.context_version_partial",
                "status": "partial",
                "message": "Activation or implementation evidence exists, but no exact verified Context Version object is bound.",
            }
        ],
        "authority": {"current_authority": "none_from_historical_context", "canonical_context_governs": True},
        "semantic_applicability": "not_evaluated",
        "content_duplicated": False,
    }


def integrate_context_versions(
    root: Path,
    missions: list[dict],
    context_versions: list[dict] | tuple[dict, ...],
) -> tuple[list[dict], dict, list[dict]]:
    engine = ContextVersionEngine(root)
    exact_by_mission: dict[str, dict] = {}
    ambiguous_missions: set[str] = set()
    index = []
    gaps = []
    for version in context_versions:
        if version.get("schema") != VERSION_SCHEMA:
            gaps.append(
                {
                    "id": "memory.gap.context_version_schema",
                    "status": "unknown",
                    "message": "A supplied Context Version used an unsupported schema and was not bound.",
                }
            )
            continue
        check = engine.check_version(version)
        mission_id = version.get("capture", {}).get("mission_id")
        if check["result"]["immutable_identity"] != "valid" or not mission_id:
            gaps.append(
                {
                    "id": "memory.gap.context_version_invalid",
                    "status": "unknown",
                    "message": "A supplied Context Version lacked valid immutable identity or explicit Mission binding.",
                }
            )
            continue
        if mission_id in exact_by_mission or mission_id in ambiguous_missions:
            gaps.append(
                {
                    "id": f"memory.gap.context_version_ambiguous.{stable_hash(mission_id)[:12]}",
                    "status": "unknown",
                    "message": "Multiple exact Context Versions claimed the same Mission; none may silently replace another.",
                }
            )
            exact_by_mission.pop(mission_id, None)
            index = [item for item in index if item["mission_id"] != mission_id]
            ambiguous_missions.add(mission_id)
            continue
        evidence = exact_context_evidence(version, check)
        exact_by_mission[mission_id] = evidence
        index.append(
            {
                "mission_id": mission_id,
                "id": version["id"],
                "identity_hash": version["identity_hash"],
                "historical_verification": check["result"]["historical_verification"],
                "current_applicability": check["result"]["current_applicability"],
                "source_availability": evidence["context_version"]["source_availability"],
                "content_duplicated": False,
            }
        )

    counts = {"exact": 0, "partial": 0, "unknown": 0}
    for mission in missions:
        evidence = exact_by_mission.get(mission["mission_id"]) or partial_context_evidence(mission)
        mission["context_evidence"] = evidence
        counts[evidence["binding_state"]] += 1

    known_missions = {mission["mission_id"] for mission in missions}
    for item in index:
        if item["mission_id"] not in known_missions:
            gaps.append(
                {
                    "id": f"memory.gap.context_version_mission_unavailable.{stable_hash(item['mission_id'])[:12]}",
                    "status": "partial",
                    "message": "An exact Context Version is valid, but its bound Mission record is unavailable in this continuity corpus.",
                }
            )

    index.sort(key=lambda item: (item["mission_id"], item["id"]))
    summary = {
        "supplied_count": len(context_versions),
        "accepted_exact_count": len(index),
        "mission_binding_counts": counts,
        "identity_hash": stable_hash(index),
        "versions": index,
        "historical_authority_granted": False,
        "semantic_comparison_performed": False,
        "content_duplicated": False,
    }
    return missions, summary, gaps
