from __future__ import annotations

import hashlib
import json
from pathlib import Path


SCHEMA = "contextos.adoption.profile/1"
MAPPING_STATES = {"observed", "declared", "derived", "suggested", "unknown"}
APPLICABILITY_STATES = {"universal", "target_native", "mapped_equivalent", "not_applicable", "unknown"}
ENFORCEMENT_STATES = {"blocking", "advisory", "none"}
WORK_OWNERSHIP_STATES = {
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
REQUIRED_CONCEPTS = (
    "organizational_intent",
    "product_value_model",
    "current_roadmap",
    "active_work",
    "architecture",
    "runtime_inventory",
    "governance",
    "authority_boundaries",
    "goals_missions",
    "evidence_closure",
    "organizational_memory",
    "environment_boundaries",
)


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
    locator = Path(value).as_posix()
    if not locator or Path(locator).is_absolute() or ".." in Path(locator).parts:
        raise ValueError(f"Adoption Profile source locator escapes the target boundary: {value!r}.")
    return locator.removeprefix("./")


class AdoptionProfile:
    """Governed semantic mapping between universal Context OS concepts and target canon."""

    def __init__(self, value: dict | str | Path) -> None:
        if isinstance(value, dict):
            raw = json.loads(json.dumps(value))
            self.source_path: Path | None = None
        else:
            self.source_path = Path(value).resolve()
            raw = json.loads(self.source_path.read_text(encoding="utf-8"))
        self.data = self._validate(raw)
        self.identity_hash = stable_hash(self._identity_payload(self.data))
        self.id = self.data.get("id") or f"adoption.profile.{self.identity_hash[:16]}"

    @staticmethod
    def _identity_payload(data: dict) -> dict:
        return {key: value for key, value in data.items() if key not in {"identity_hash"}}

    @classmethod
    def _validate(cls, data: dict) -> dict:
        if not isinstance(data, dict) or data.get("schema") != SCHEMA:
            raise ValueError(f"Adoption Profile must use schema {SCHEMA}.")
        if not str(data.get("version", "")).strip():
            raise ValueError("Adoption Profile requires a version.")
        target = data.get("target")
        if not isinstance(target, dict) or not target.get("id") or not target.get("scope"):
            raise ValueError("Adoption Profile requires target.id and target.scope.")
        if data.get("lifecycle", {}).get("state") not in {"draft", "reviewed", "approved", "canonical"}:
            raise ValueError("Adoption Profile requires an explicit governed lifecycle state.")
        if data.get("lifecycle", {}).get("target_ssot") is not False:
            raise ValueError("Adoption Profile must state that it is not the target SSOT.")
        if not data.get("authority", {}).get("owner"):
            raise ValueError("Adoption Profile requires an accountable authority owner.")
        mappings = data.get("mappings")
        if not isinstance(mappings, list) or not mappings:
            raise ValueError("Adoption Profile requires at least one concept mapping.")
        seen: set[str] = set()
        for mapping in mappings:
            concept = mapping.get("concept")
            if not concept or concept in seen:
                raise ValueError("Adoption Profile concept mappings must have unique identifiers.")
            seen.add(concept)
            if mapping.get("support") not in MAPPING_STATES:
                raise ValueError(f"Unsupported mapping support for {concept!r}.")
            sources = mapping.get("sources", [])
            if mapping["support"] in {"observed", "declared", "derived"} and not sources:
                raise ValueError(f"Supported mapping {concept!r} requires source evidence.")
            for source in sources:
                source["locator"] = safe_locator(source.get("locator", ""))
                if not source.get("authority_owner") or not source.get("lifecycle_state"):
                    raise ValueError(f"Mapped source {source['locator']!r} requires authority and lifecycle metadata.")
            if mapping["support"] == "suggested" and mapping.get("recognized_as_canonical"):
                raise ValueError("Suggested mappings cannot be recognized as target canon.")
        validation = data.get("validation", {}).get("rules")
        if not isinstance(validation, dict) or not validation:
            raise ValueError("Adoption Profile requires validation applicability decisions.")
        for rule_id, decision in validation.items():
            if decision.get("applicability") not in APPLICABILITY_STATES:
                raise ValueError(f"Unsupported applicability for rule {rule_id!r}.")
            if decision.get("enforcement") not in ENFORCEMENT_STATES:
                raise ValueError(f"Unsupported enforcement for rule {rule_id!r}.")
            if not decision.get("rationale"):
                raise ValueError(f"Validation decision {rule_id!r} requires a rationale.")
        isolation = data.get("evidence_isolation", {})
        if isolation.get("target_only") is not True or isolation.get("host_context_is_evidence") is not False:
            raise ValueError("Adoption Profile must enforce target-only evidence isolation.")
        work_ownership = data.get("work_ownership")
        if work_ownership is not None:
            if not isinstance(work_ownership, dict):
                raise ValueError("Adoption Profile work_ownership must be an object.")
            source_concepts = work_ownership.get("source_concepts")
            if not isinstance(source_concepts, list) or not source_concepts:
                raise ValueError("Adoption Profile work_ownership requires source_concepts.")
            unknown_concepts = sorted(set(source_concepts) - seen)
            if unknown_concepts:
                raise ValueError(f"Work ownership cites unmapped concepts: {', '.join(unknown_concepts)}.")
            semantics = work_ownership.get("lifecycle_semantics")
            if not isinstance(semantics, dict) or not semantics:
                raise ValueError("Adoption Profile work_ownership requires lifecycle_semantics.")
            unsupported = sorted({value for value in semantics.values() if value not in WORK_OWNERSHIP_STATES})
            if unsupported:
                raise ValueError(f"Unsupported work ownership semantic states: {', '.join(unsupported)}.")
        return data

    def binding(self) -> dict:
        return {
            "schema": SCHEMA,
            "id": self.id,
            "identity_hash": self.identity_hash,
            "version": self.data["version"],
            "target": self.data["target"],
            "lifecycle": self.data["lifecycle"],
            "not_target_ssot": True,
        }

    def mapping(self, concept: str) -> dict | None:
        return next((item for item in self.data["mappings"] if item["concept"] == concept), None)

    def mappings(self) -> list[dict]:
        return list(self.data["mappings"])

    def rule_decision(self, rule_id: str) -> dict:
        decision = self.data["validation"]["rules"].get(rule_id)
        if decision is None:
            return {
                "applicability": "unknown",
                "enforcement": "none",
                "rationale": "The active Adoption Profile does not classify this rule; applicability remains unknown.",
                "equivalent_control_refs": [],
                "gap": True,
            }
        return decision

    def source_records(self, root: str | Path, concepts: set[str] | None = None) -> list[dict]:
        target_root = Path(root).resolve()
        records: list[dict] = []
        for mapping in self.data["mappings"]:
            if concepts is not None and mapping["concept"] not in concepts:
                continue
            for source in mapping.get("sources", []):
                path = target_root / source["locator"]
                exists = path.is_file()
                records.append(
                    {
                        "concept": mapping["concept"],
                        "mapping_support": mapping["support"],
                        "mapping_confidence": mapping.get("confidence", "unknown"),
                        "unresolved_ambiguity": mapping.get("unresolved_ambiguity"),
                        **source,
                        "exists": exists,
                        "source_hash": file_hash(path) if exists else None,
                    }
                )
        return sorted(records, key=lambda item: (item["concept"], item["locator"]))

    def state(self, root: str | Path) -> dict:
        sources = self.source_records(root)
        source_material = [
            {
                "concept": item["concept"],
                "locator": item["locator"],
                "source_hash": item["source_hash"],
                "lifecycle_state": item["lifecycle_state"],
                "currentness": item.get("currentness", "unknown"),
                "supersession_status": item.get("supersession_status", "unknown"),
            }
            for item in sources
        ]
        return {
            "profile": self.binding(),
            "source_fingerprint": stable_hash(source_material),
            "source_count": len(sources),
            "available_source_count": sum(1 for item in sources if item["exists"]),
            "missing_sources": [item["locator"] for item in sources if not item["exists"]],
            "sources": sources,
        }

    def check_binding(self, binding: dict) -> dict:
        checks = {
            "id_matches": binding.get("id") == self.id,
            "identity_hash_matches": binding.get("identity_hash") == self.identity_hash,
            "version_matches": binding.get("version") == self.data["version"],
            "target_matches": binding.get("target") == self.data["target"],
        }
        return {"valid": all(checks.values()), "checks": checks}

    def normalize_work_state(self, target_state: str) -> str:
        work_ownership = self.data.get("work_ownership", {})
        return work_ownership.get("lifecycle_semantics", {}).get(target_state, "unknown")

    def work_ownership_binding(self) -> dict | None:
        work_ownership = self.data.get("work_ownership")
        if work_ownership is None:
            return None
        return {
            "source_concepts": sorted(set(work_ownership["source_concepts"])),
            "lifecycle_semantics": dict(sorted(work_ownership["lifecycle_semantics"].items())),
            "identity_hash": stable_hash(work_ownership),
            "target_authority_preserved": True,
        }


def load_adoption_profile(value: AdoptionProfile | dict | str | Path | None) -> AdoptionProfile | None:
    if value is None:
        return None
    return value if isinstance(value, AdoptionProfile) else AdoptionProfile(value)
