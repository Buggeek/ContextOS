from __future__ import annotations

import datetime as _dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path


TOOLS_ROOT = Path(__file__).resolve().parents[2]
ADOPTION_ROOT = TOOLS_ROOT / "adoption"
if str(ADOPTION_ROOT) not in sys.path:
    sys.path.insert(0, str(ADOPTION_ROOT))

from adoption_engine import load_adoption_profile  # noqa: E402


SCHEMA = "contextos.reasoning.work_ownership_resolution/1"
CHECK_SCHEMA = "contextos.reasoning.work_ownership_resolution_check/1"
WORK_KINDS = {"goal", "mission", "workstream", "initiative", "operation", "other"}
SEMANTIC_STATES = {
    "active",
    "awaiting_evidence",
    "awaiting_human_decision",
    "blocked",
    "deferred",
    "completed",
    "closed",
    "superseded",
    "historical",
    "unknown",
}
CURRENTNESS_STATES = {"current", "historical", "unknown"}
NON_OWNING_STATES = {"completed", "closed", "superseded", "historical"}
DISPOSITIONS = {
    "active": "OBSERVE_EXISTING_WORK",
    "awaiting_evidence": "AWAIT_EVIDENCE",
    "awaiting_human_decision": "AWAIT_HUMAN_DECISION",
    "blocked": "BLOCKED_BY_CURRENT_OWNER",
    "deferred": "WAIT_FOR_EXISTING_WORK",
}
DISPOSITION_PRIORITY = {
    "awaiting_human_decision": 50,
    "awaiting_evidence": 40,
    "blocked": 30,
    "deferred": 20,
    "active": 10,
}


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_locator(value: str) -> str:
    locator = Path(value).as_posix().removeprefix("./")
    if not value.strip() or locator in {"", "."} or Path(locator).is_absolute() or ".." in Path(locator).parts:
        raise ValueError(f"Work Ownership source locator escapes the target boundary: {value!r}.")
    return locator


def source_path(root: Path, locator: str) -> Path:
    path = (root / locator).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Work Ownership source resolves outside the target boundary: {locator!r}.") from exc
    return path


def _git(root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def _git_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    return (
        subprocess.run(
            ["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, descendant],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


class WorkOwnershipResolver:
    """Resolve explicit work ownership without creating or changing organizational work."""

    def __init__(self, root: str | Path = ".", adoption_profile=None) -> None:
        self.root = Path(root).resolve()
        self.adoption_profile = load_adoption_profile(adoption_profile)

    def run(
        self,
        *,
        need: dict,
        work_items: list[dict] | tuple[dict, ...],
        source_declarations: list[dict] | tuple[dict, ...],
        coverage: dict,
        generated_at: str | None = None,
    ) -> dict:
        normalized_need = self._normalize_need(need)
        material_sources = self._capture_sources(source_declarations)
        source_ids = {item["id"] for item in material_sources}
        normalized_coverage = self._normalize_coverage(coverage, source_ids)
        normalized_work = sorted(
            (self._normalize_work_item(item, source_ids) for item in work_items),
            key=lambda item: item["id"],
        )
        if len({item["id"] for item in normalized_work}) != len(normalized_work):
            raise ValueError("Work Ownership work item ids must be unique.")

        currentness = self._currentness_at_resolution(material_sources, normalized_coverage)
        ownership, result = self._resolve(normalized_need, normalized_work, normalized_coverage, currentness)
        bindings = {
            "adoption_profile": self.adoption_profile.binding() if self.adoption_profile else None,
            "work_semantics": self.adoption_profile.work_ownership_binding() if self.adoption_profile else None,
            "material_source_fingerprint": stable_hash(material_sources),
        }
        authority = self._authority()
        boundaries = self._boundaries()
        body = {
            "read_only": True,
            "derived_view": True,
            "need": normalized_need,
            "bindings": bindings,
            "material_sources": material_sources,
            "coverage": normalized_coverage,
            "work_items": normalized_work,
            "ownership": ownership,
            "currentness": currentness,
            "result": result,
            "implementation_evidence": {
                "repository_tip_at_resolution": _git(self.root, "rev-parse", "HEAD"),
                "repository_tree_at_resolution": _git(self.root, "rev-parse", "HEAD^{tree}"),
                "repository_tip_is_context_identity": False,
            },
            "authority": authority,
            "boundaries": boundaries,
            "limitations": [
                "Work relevance must be explicitly evidenced through need_refs; text similarity is not inferred.",
                "Complete coverage is a governed assertion bound to exact material sources, not a claim that every organizational system was searched.",
                "The resolver cannot create, cancel, merge, supersede, schedule, or authorize work.",
                "Unknown or conflicting ownership prevents new-work qualification until governed evidence resolves it.",
            ],
        }
        identity_hash = stable_hash(self._identity_payload(body))
        return {
            "schema": SCHEMA,
            "id": f"work_ownership.resolution.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            "generated_at": generated_at or generated_timestamp(),
            "root": str(self.root),
            **body,
        }

    def check_resolution(self, saved: dict, *, generated_at: str | None = None) -> dict:
        if not isinstance(saved, dict) or saved.get("schema") != SCHEMA:
            raise ValueError(f"Saved Work Ownership Resolution must use {SCHEMA}.")
        expected_hash = stable_hash(self._identity_payload(saved))
        identity_valid = (
            saved.get("identity_hash") == expected_hash
            and saved.get("id") == f"work_ownership.resolution.{expected_hash[:16]}"
        )
        profile_binding = saved.get("bindings", {}).get("adoption_profile")
        profile_check = (
            self.adoption_profile.check_binding(profile_binding or {})
            if self.adoption_profile
            else {"valid": profile_binding is None, "checks": {"profile_absent": profile_binding is None}}
        )
        source_checks = [self._check_source(item) for item in saved.get("material_sources", [])]
        material_sources_current = bool(source_checks) and all(item["current_match"] for item in source_checks)
        failed = []
        if not identity_valid:
            failed.append("work_ownership_check.immutable_identity")
        if not profile_check["valid"]:
            failed.append("work_ownership_check.adoption_profile_changed")
        for item in source_checks:
            if not item["current_match"]:
                failed.append(f"work_ownership_check.material_source_changed:{item['source_id']}")

        captured_tip = saved.get("implementation_evidence", {}).get("repository_tip_at_resolution")
        current_tip = _git(self.root, "rev-parse", "HEAD")
        if not captured_tip or not current_tip:
            tip_state = "unknown"
        elif captured_tip == current_tip:
            tip_state = "exact_resolution_tip"
        elif _git_is_ancestor(self.root, captured_tip, current_tip):
            tip_state = "advanced"
        else:
            tip_state = "different_or_divergent"
        materially_current = identity_valid and profile_check["valid"] and material_sources_current
        tip_relevance = (
            "irrelevant_to_material_work_context"
            if tip_state == "advanced" and materially_current
            else "material_work_context_drift"
            if not material_sources_current
            else "same_implementation_tip"
            if tip_state == "exact_resolution_tip"
            else "unknown"
        )
        result_payload = {
            "resolution_id": saved.get("id"),
            "resolution_hash": saved.get("identity_hash"),
            "profile_valid": profile_check["valid"],
            "source_checks": source_checks,
            "tip_state": tip_state,
            "failed_checks": sorted(set(failed)),
        }
        check_hash = stable_hash(result_payload)
        return {
            "schema": CHECK_SCHEMA,
            "id": f"work_ownership.resolution_check.{check_hash[:16]}",
            "identity_hash": check_hash,
            "generated_at": generated_at or generated_timestamp(),
            "root": str(self.root),
            "read_only": True,
            "resolution": {"id": saved.get("id"), "identity_hash": saved.get("identity_hash")},
            "checks": {
                "immutable_identity": "valid" if identity_valid else "tampered",
                "adoption_profile_valid": profile_check["valid"],
                "adoption_profile_checks": profile_check["checks"],
                "material_sources_current": material_sources_current,
                "source_checks": source_checks,
            },
            "repository_state": {
                "tip_at_resolution": captured_tip,
                "current_tip": current_tip,
                "tip_state": tip_state,
                "tip_relevance": tip_relevance,
                "repository_tip_is_context_identity": False,
            },
            "result": {
                "valid": not failed,
                "invalidated": bool(failed),
                "materially_current": materially_current,
                "reanchor_required": bool(failed),
                "historical_resolution_identity_valid": identity_valid,
                "saved_disposition": saved.get("result", {}).get("disposition"),
                "consequential_disposition_remains_eligible": not failed,
                "failed_checks": sorted(set(failed)),
            },
            "authority": self._authority(),
            "boundaries": self._boundaries(),
        }

    def _capture_sources(self, declarations: list[dict] | tuple[dict, ...]) -> list[dict]:
        profile_sources = None
        if self.adoption_profile:
            work_binding = self.adoption_profile.work_ownership_binding()
            if work_binding is None:
                raise ValueError("External Work Ownership Resolution requires profile work_ownership semantics.")
            if self.adoption_profile.data["lifecycle"]["state"] not in {"approved", "canonical"}:
                raise ValueError("External Work Ownership Resolution requires an approved or canonical Adoption Profile.")
            profile_sources = set()
            for mapping in self.adoption_profile.mappings():
                if (
                    mapping["concept"] in work_binding["source_concepts"]
                    and mapping["support"] in {"observed", "declared", "derived"}
                ):
                    profile_sources.update(
                        (mapping["concept"], source["locator"])
                        for source in mapping.get("sources", [])
                    )
        captured = []
        for declaration in declarations:
            source_id = str(declaration.get("id", "")).strip()
            if not source_id:
                raise ValueError("Work Ownership material source requires an id.")
            locator = safe_locator(str(declaration.get("locator", "")))
            concept = str(declaration.get("concept", "active_work"))
            if profile_sources is not None and (concept, locator) not in profile_sources:
                raise ValueError(
                    f"External Work Ownership source is not mapped by the active Adoption Profile: {concept}:{locator}."
                )
            path = source_path(self.root, locator)
            exists = path.is_file()
            captured.append(
                {
                    "id": source_id,
                    "source_of_record": {"adapter": "filesystem", "locator": locator},
                    "concept": concept,
                    "fingerprint": {"algorithm": "sha256", "value": file_hash(path) if exists else None},
                    "exists_at_resolution": exists,
                    "material_to_ownership": True,
                    "evidence_refs": sorted(set(str(ref) for ref in declaration.get("evidence_refs", []))),
                    "content_embedded": False,
                }
            )
        captured.sort(key=lambda item: item["id"])
        if len({item["id"] for item in captured}) != len(captured):
            raise ValueError("Work Ownership material source ids must be unique.")
        return captured

    def _check_source(self, source: dict) -> dict:
        source_of_record = source.get("source_of_record", {})
        locator = safe_locator(str(source_of_record.get("locator", "")))
        path = source_path(self.root, locator)
        exists = path.is_file()
        current_hash = file_hash(path) if exists else None
        expected_hash = source.get("fingerprint", {}).get("value")
        return {
            "source_id": source.get("id"),
            "adapter": source_of_record.get("adapter"),
            "locator": locator,
            "expected_hash": expected_hash,
            "current_hash": current_hash,
            "current_exists": exists,
            "current_match": exists and expected_hash is not None and current_hash == expected_hash,
        }

    def _normalize_work_item(self, item: dict, source_ids: set[str]) -> dict:
        item_id = str(item.get("id", "")).strip()
        if not item_id:
            raise ValueError("Work Ownership item requires an id.")
        kind = str(item.get("kind", "other"))
        if kind not in WORK_KINDS:
            raise ValueError(f"Unsupported work kind: {kind!r}.")
        lifecycle_state = str(item.get("lifecycle_state", "unknown"))
        semantic_state = (
            self.adoption_profile.normalize_work_state(lifecycle_state)
            if self.adoption_profile
            else lifecycle_state
            if lifecycle_state in SEMANTIC_STATES
            else "unknown"
        )
        currentness = str(item.get("currentness", "unknown"))
        if currentness not in CURRENTNESS_STATES:
            raise ValueError(f"Unsupported work currentness: {currentness!r}.")
        item_sources = sorted(set(str(value) for value in item.get("source_ids", [])))
        if not item_sources:
            raise ValueError(f"Work item {item_id!r} requires material source evidence.")
        unknown_sources = sorted(set(item_sources) - source_ids)
        if unknown_sources:
            raise ValueError(f"Work item {item_id!r} cites unknown material sources: {', '.join(unknown_sources)}.")
        return {
            "id": item_id,
            "kind": kind,
            "title": str(item.get("title", item_id)),
            "owner": item.get("owner"),
            "lifecycle_state": lifecycle_state,
            "semantic_state": semantic_state,
            "currentness": currentness,
            "need_refs": sorted(set(str(value) for value in item.get("need_refs", []))),
            "parent_work_id": item.get("parent_work_id"),
            "source_ids": item_sources,
            "authority_status": str(item.get("authority_status", "unknown")),
            "blocking_condition": item.get("blocking_condition"),
            "return_condition": item.get("return_condition"),
            "evidence_refs": sorted(set(str(ref) for ref in item.get("evidence_refs", []))),
            "canonical": False,
        }

    @staticmethod
    def _normalize_need(need: dict) -> dict:
        need_id = str(need.get("id", "")).strip()
        statement = str(need.get("statement", "")).strip()
        if not need_id or not statement:
            raise ValueError("Work Ownership need requires id and statement.")
        return {
            "id": need_id,
            "statement": statement,
            "scope": str(need.get("scope", "unspecified")),
            "evidence_refs": sorted(set(str(ref) for ref in need.get("evidence_refs", []))),
            "canonical": False,
        }

    @staticmethod
    def _normalize_coverage(coverage: dict, source_ids: set[str]) -> dict:
        status = str(coverage.get("status", "unknown"))
        if status not in {"complete", "partial", "unknown"}:
            raise ValueError(f"Unsupported ownership coverage status: {status!r}.")
        coverage_sources = sorted(set(str(value) for value in coverage.get("source_ids", [])))
        if set(coverage_sources) - source_ids:
            raise ValueError("Ownership coverage cites sources outside the material source set.")
        if status == "complete" and (not coverage_sources or set(coverage_sources) != source_ids):
            raise ValueError("Complete ownership coverage must bind every material source.")
        authority_status = str(coverage.get("authority_status", "unknown"))
        evidence_refs = sorted(set(str(ref) for ref in coverage.get("evidence_refs", [])))
        if status == "complete" and (authority_status == "unknown" or not evidence_refs):
            raise ValueError("Complete ownership coverage requires explicit authority and evidence.")
        return {
            "status": status,
            "scope": str(coverage.get("scope", "unspecified")),
            "source_ids": coverage_sources,
            "authority_status": authority_status,
            "evidence_refs": evidence_refs,
        }

    @staticmethod
    def _currentness_at_resolution(sources: list[dict], coverage: dict) -> dict:
        all_present = bool(sources) and all(item["exists_at_resolution"] for item in sources)
        exact = all_present
        return {
            "material_source_state": "exact" if exact else "missing_or_incomplete",
            "materially_current": exact,
            "coverage_state": coverage["status"],
            "repository_tip_used_as_context_identity": False,
            "consequential_recommendation_requires_recheck": True,
        }

    def _resolve(self, need: dict, work_items: list[dict], coverage: dict, currentness: dict) -> tuple[dict, dict]:
        relevant = [item for item in work_items if need["id"] in item["need_refs"]]
        historical = [
            item
            for item in relevant
            if item["currentness"] == "historical" or item["semantic_state"] in NON_OWNING_STATES
        ]
        current = [item for item in relevant if item not in historical and item["currentness"] == "current"]
        unresolved = [
            item
            for item in relevant
            if item not in historical
            and (item["currentness"] == "unknown" or item["semantic_state"] == "unknown" or not item["owner"])
        ]
        resolved_owner = None
        conflict = False

        if not currentness["materially_current"]:
            disposition = "REANCHOR_REQUIRED"
        elif coverage["status"] != "complete" or unresolved:
            disposition = "OWNERSHIP_UNKNOWN"
        elif not current:
            disposition = "QUALIFY_NEW_WORK"
        else:
            current_ids = {item["id"] for item in current}
            parent_ids = {item["parent_work_id"] for item in current if item.get("parent_work_id") in current_ids}
            leaves = [item for item in current if item["id"] not in parent_ids]
            if len(leaves) != 1 or not self._one_chain(current, leaves[0]):
                disposition = "OWNERSHIP_CONFLICT"
                conflict = True
            else:
                selected = leaves[0]
                controlling_item = max(
                    current,
                    key=lambda item: DISPOSITION_PRIORITY.get(item["semantic_state"], 0),
                )
                controlling_state = controlling_item["semantic_state"]
                disposition = DISPOSITIONS.get(controlling_state, "OWNERSHIP_UNKNOWN")
                resolved_owner = {
                    "work_id": selected["id"],
                    "work_kind": selected["kind"],
                    "owner": selected["owner"],
                    "semantic_state": selected["semantic_state"],
                    "controlling_work_id": controlling_item["id"],
                    "controlling_state": controlling_state,
                    "return_condition": controlling_item["return_condition"],
                    "authority_status": selected["authority_status"],
                    "evidence_refs": sorted(
                        set(
                            selected["evidence_refs"]
                            + selected["source_ids"]
                            + controlling_item["evidence_refs"]
                            + controlling_item["source_ids"]
                        )
                    ),
                }

        current_exists = bool(current) and disposition not in {"OWNERSHIP_UNKNOWN", "REANCHOR_REQUIRED"}
        duplicate_prevented = disposition in set(DISPOSITIONS.values()) | {"OWNERSHIP_CONFLICT"}
        ownership = {
            "relevant_work": relevant,
            "current_owning_work": current,
            "historical_or_non_owning_work": historical,
            "unresolved_work": unresolved,
            "resolved_owner": resolved_owner,
        }
        result = {
            "disposition": disposition,
            "existing_relevant_work_found": bool(relevant),
            "current_ownership_exists": current_exists,
            "current_work_ids": [item["id"] for item in current],
            "ownership_conflict": conflict,
            "ownership_unknown": disposition == "OWNERSHIP_UNKNOWN",
            "duplicate_work_prevented": duplicate_prevented,
            "eligible_for_goal_qualification": disposition == "QUALIFY_NEW_WORK",
            "parallel_goal_or_mission_creation_authorized": False,
            "reanchor_required": disposition == "REANCHOR_REQUIRED",
            "decision_authority_granted": False,
        }
        return ownership, result

    @staticmethod
    def _one_chain(items: list[dict], leaf: dict) -> bool:
        by_id = {item["id"]: item for item in items}
        visited = set()
        current = leaf
        while current:
            if current["id"] in visited:
                return False
            visited.add(current["id"])
            current = by_id.get(current.get("parent_work_id"))
        return visited == set(by_id)

    @staticmethod
    def _identity_payload(report: dict) -> dict:
        return {
            key: report.get(key)
            for key in (
                "need",
                "bindings",
                "material_sources",
                "coverage",
                "work_items",
                "ownership",
                "currentness",
                "result",
                "authority",
                "boundaries",
                "limitations",
            )
        }

    @staticmethod
    def _authority() -> dict:
        return {
            "level": "L1_observe_and_suggest",
            "may_resolve_explicit_evidence": True,
            "may_prevent_parallel_recommendation": True,
            "may_create_goal_or_mission": False,
            "may_change_existing_work": False,
            "may_assign_owner": False,
            "may_grant_authority": False,
            "may_mutate_canonical_context": False,
        }

    @staticmethod
    def _boundaries() -> dict:
        return {
            "need_is_goal": False,
            "goal_is_mission": False,
            "mission_is_owner": False,
            "owner_is_authority": False,
            "active_is_current_canon": False,
            "incomplete_is_active": False,
            "historical_is_current": False,
            "capability_is_eligibility": False,
            "eligibility_is_authority": False,
            "resolution_is_ssot": False,
            "historical_resolution_retains_current_authority": False,
        }


def render_human(report: dict) -> str:
    result = report["result"]
    lines = [
        "# Context OS Work Ownership Resolution",
        "",
        f"- Resolution: `{report['id']}`",
        f"- Need: {report['need']['statement']}",
        f"- Disposition: `{result['disposition']}`",
        f"- Materially current: {'yes' if report['currentness']['materially_current'] else 'no'}",
        f"- Current ownership exists: {'yes' if result['current_ownership_exists'] else 'no'}",
        f"- Duplicate work prevented: {'yes' if result['duplicate_work_prevented'] else 'no'}",
        f"- Eligible for Goal qualification: {'yes' if result['eligible_for_goal_qualification'] else 'no'}",
        "",
        "## Current Ownership",
    ]
    owner = report["ownership"]["resolved_owner"]
    if owner:
        lines.extend(
            [
                f"- Work: `{owner['work_id']}` ({owner['work_kind']})",
                f"- Owner: `{owner['owner']}`",
                f"- State: `{owner['semantic_state']}`",
                f"- Controlling work/state: `{owner['controlling_work_id']}` / `{owner['controlling_state']}`",
                f"- Return condition: {owner['return_condition'] or 'Not supplied.'}",
            ]
        )
    elif result["ownership_conflict"]:
        lines.append("- Multiple current ownership branches exist; no owner was selected.")
    else:
        lines.append("- No exact current owner was resolved.")
    lines.extend(
        [
            "",
            "## Currentness Boundary",
            "- Only exact material ownership sources govern this disposition.",
            "- An unrelated repository-tip advance does not make the resolution stale.",
            "- Material source drift requires re-anchor before consequential reuse.",
            "",
            "## Authority Boundary",
            "- This is a derived read-only resolution, not SSOT or authority.",
            "- It cannot create, modify, merge, cancel, or supersede organizational work.",
        ]
    )
    return "\n".join(lines) + "\n"
