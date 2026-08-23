from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from .context_version_report_builder import (
    PLAN_CHECK_SCHEMA,
    PLAN_SCHEMA,
    VERSION_CHECK_SCHEMA,
    VERSION_SCHEMA,
    build_report,
    generated_timestamp,
)
from .continuity_engine import stable_hash


TOOLS_ROOT = Path(__file__).resolve().parents[2]
ACTIVATION_ROOT = TOOLS_ROOT / "activation"
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
for module_root in (ACTIVATION_ROOT, VALIDATORS_ROOT):
    if str(module_root) not in sys.path:
        sys.path.insert(0, str(module_root))

from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402
from engine.validator_engine import ValidatorEngine  # noqa: E402


CAPTURE_EVENTS = {
    "mission_start",
    "consequential_decision",
    "accepted_approval",
    "canonical_promotion",
    "release_cut",
    "material_policy_change",
    "material_governance_change",
    "explicit_human_checkpoint",
}
TIERS = {"working", "project", "organizational"}
TRUTH_STATES = {
    "epistemic_support": ("observed", "declared", "inferred", "derived", "unknown"),
    "governance_lifecycle": ("suggested", "draft", "reviewed", "approved", "canonical"),
    "strategic_belief": ("hypothesis", "verified", "deprecated"),
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *args: str, text: bool = True) -> str | bytes | None:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=text,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip() if text else result.stdout


def _title_and_version(path: Path) -> tuple[str | None, str | None]:
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None, None
    title = None
    version = None
    for line in content.splitlines()[:100]:
        if title is None and line.startswith("# "):
            title = line[2:].strip() or None
        match = re.match(r"^##\s+Version:\s*(.+?)\s*$", line)
        if match:
            version = match.group(1).strip()
        if title and version:
            break
    return title, version


def _authority_tier(locator: str) -> str:
    if locator.startswith("SSOT/"):
        return "ssot"
    if locator.startswith("docs/0.x_foundations/"):
        return "foundation"
    if locator.startswith("docs/1.x_architecture/1.5_runtime_contracts/"):
        return "runtime_contract"
    if locator.startswith("docs/1.x_architecture/"):
        return "architecture"
    if locator.startswith("docs/5.x_strategy/"):
        return "strategy"
    if locator.startswith("docs/3.x_operation/") or locator.startswith("ops/"):
        return "governance"
    if locator == "README.md":
        return "repository_entrypoint"
    return "declared_source"


def _lifecycle_state(locator: str) -> str:
    return "canonical_verified" if locator.startswith("SSOT/") else "canonical_reference"


def _source_id(scope: dict, locator: str) -> str:
    identity = {
        "organization": scope["organization"],
        "domain": scope["domain"],
        "adapter": "filesystem",
        "locator": locator,
    }
    return f"context.source.{stable_hash(identity)[:16]}"


def _ref(value: dict | None) -> dict | None:
    if not value:
        return None
    return {"id": value.get("id"), "identity_hash": value.get("identity_hash"), "schema": value.get("schema")}


class ContextVersionEngine:
    """Plan, capture, and verify immutable content-free Context Versions."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def plan(
        self,
        *,
        scope: dict,
        event_type: str,
        reason: str,
        capture_at: str,
        mission_id: str | None = None,
        goal: str | None = None,
        triggering_event: dict | None = None,
        activation_package: dict | None = None,
        activation_handoff: dict | None = None,
        additional_source_paths: list[str] | tuple[str, ...] = (),
        authority_paths: list[str] | tuple[str, ...] = (),
        policy_paths: list[str] | tuple[str, ...] = (),
        parent_version: dict | None = None,
        effective_from: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        self._validate_inputs(scope, event_type, reason, capture_at, mission_id, activation_package, activation_handoff)
        if parent_version:
            if parent_version.get("schema") != VERSION_SCHEMA:
                raise ValueError(f"Parent Context Version must use {VERSION_SCHEMA}.")
            if parent_version.get("identity_hash") != stable_hash(self._version_identity_payload(parent_version)):
                raise ValueError("Parent Context Version identity is invalid.")
        source_paths = sorted(set(additional_source_paths) | set(authority_paths) | set(policy_paths))
        package_check = None
        handoff_check = None
        continuity_gaps = []
        package_sources = []
        if activation_package:
            package_check = ContextActivationPackageEngine(self.root).check_package(activation_package, generated_at=generated_at)
            package_sources = activation_package.get("canonical_sources", [])
            if not package_check["result"]["valid"]:
                continuity_gaps.append(
                    {"id": "context.version.gap.activation_package_invalid", "message": "The bound Activation Package is not currently valid."}
                )
        if activation_handoff:
            handoff_check = ContextActivationPackageEngine(self.root).check_handoff(activation_handoff, generated_at=generated_at)
            if not handoff_check["result"]["valid"]:
                continuity_gaps.append(
                    {"id": "context.version.gap.activation_handoff_invalid", "message": "The bound Activation Handoff is not currently valid."}
                )

        manifest, source_gaps = self._source_manifest(scope, package_sources, source_paths)
        continuity_gaps.extend(source_gaps)
        if not manifest:
            continuity_gaps.append(
                {"id": "context.version.gap.no_sources", "message": "No governed source was available for Context Version capture."}
            )
        validator = ValidatorEngine(self.root).run(mode="gate")
        validator_ok = validator["summary"]["error"] == 0 and validator["summary"]["fatal"] == 0
        if not validator_ok:
            continuity_gaps.append(
                {"id": "context.version.gap.validator_blocked", "message": "Validator gate blocks Context Version capture."}
            )
        if event_type == "mission_start" and not activation_package:
            continuity_gaps.append(
                {"id": "context.version.gap.mission_activation_missing", "message": "Mission-start capture requires exact Activation Package evidence."}
            )

        source_fingerprint = stable_hash(
            {
                "sources": [
                    {
                        "source_id": item["source_id"],
                        "fingerprint": item["fingerprint"],
                        "lifecycle_state": item["lifecycle_state"],
                        "authority_tier": item["authority_tier"],
                    }
                    for item in manifest
                ]
            }
        )
        repository_evidence = self._repository_evidence()
        bindings = {
            "activation_package": _ref(activation_package),
            "activation_handoff": _ref(activation_handoff),
            "authority_refs": self._source_refs(manifest, authority_paths),
            "policy_refs": self._source_refs(manifest, policy_paths),
            "parent_version": _ref(parent_version),
        }
        inputs = {
            "scope": scope,
            "event_type": event_type,
            "reason": reason.strip(),
            "capture_at": capture_at,
            "mission_id": mission_id,
            "goal": (goal or "").strip() or None,
            "triggering_event": triggering_event,
            "additional_source_paths": source_paths,
            "authority_paths": sorted(set(authority_paths)),
            "policy_paths": sorted(set(policy_paths)),
            "effective_from": effective_from or capture_at,
        }
        gates = {
            "sources_resolved": not source_gaps and bool(manifest),
            "activation_package_valid": package_check is None or package_check["result"]["valid"],
            "activation_handoff_valid": handoff_check is None or handoff_check["result"]["valid"],
            "validator_gate_ok": validator_ok,
            "mission_activation_bound": event_type != "mission_start" or activation_package is not None,
        }
        payload = {
            "inputs": inputs,
            "source_manifest": manifest,
            "source_fingerprint": source_fingerprint,
            "bindings": bindings,
            "implementation_evidence": repository_evidence,
            "validator": {"schema": validator["schema"], "summary": validator["summary"]},
            "gates": gates,
            "continuity_gaps": continuity_gaps,
        }
        identity_hash = stable_hash(payload)
        plan = {
            "id": f"context.version_capture_plan.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            "status": "ready" if all(gates.values()) else "blocked",
            "read_only": True,
            "scope": scope,
            "capture": {
                "event_type": event_type,
                "reason": reason.strip(),
                "mission_id": mission_id,
                "goal": (goal or "").strip() or None,
                "triggering_event": triggering_event,
            },
            "temporal": {
                "capture_at": capture_at,
                "effective_from": effective_from or capture_at,
                "effective_until": None,
            },
            "source_manifest": manifest,
            "source_fingerprint": source_fingerprint,
            "bindings": bindings,
            "implementation_evidence": repository_evidence,
            "validator": {"schema": validator["schema"], "summary": validator["summary"]},
            "gates": gates,
            "continuity_gaps": continuity_gaps,
            "inputs": inputs,
            "summary": {
                "source_count": len(manifest),
                "gap_count": len(continuity_gaps),
                "content_embedded": False,
                "writes_performed": False,
            },
            "boundaries": self._boundaries(),
        }
        return build_report(self.root, plan, PLAN_SCHEMA, generated_at)

    def check_plan(
        self,
        plan: dict,
        *,
        activation_package: dict | None = None,
        activation_handoff: dict | None = None,
        parent_version: dict | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if plan.get("schema") != PLAN_SCHEMA:
            raise ValueError(f"Context Version plan check requires {PLAN_SCHEMA} input.")
        expected = stable_hash(self._plan_identity_payload(plan))
        identity_valid = plan.get("identity_hash") == expected
        inputs = plan.get("inputs", {})
        current = self.plan(
            scope=inputs.get("scope", {}),
            event_type=inputs.get("event_type", ""),
            reason=inputs.get("reason", ""),
            capture_at=inputs.get("capture_at", ""),
            mission_id=inputs.get("mission_id"),
            goal=inputs.get("goal"),
            triggering_event=inputs.get("triggering_event"),
            activation_package=activation_package,
            activation_handoff=activation_handoff,
            additional_source_paths=inputs.get("additional_source_paths", []),
            authority_paths=inputs.get("authority_paths", []),
            policy_paths=inputs.get("policy_paths", []),
            parent_version=parent_version,
            effective_from=inputs.get("effective_from"),
            generated_at=generated_at,
        )
        failed = []
        if not identity_valid:
            failed.append("context_version_plan_check.identity_hash_mismatch")
        if plan.get("identity_hash") != current["identity_hash"]:
            failed.append("context_version_plan_check.current_state_changed")
        if current["status"] != "ready":
            failed.append("context_version_plan_check.current_plan_blocked")
        valid = not failed
        return build_report(
            self.root,
            {
                "read_only": True,
                "plan": {"id": plan.get("id"), "identity_hash": plan.get("identity_hash")},
                "checks": {
                    "identity_valid": identity_valid,
                    "current_state_unchanged": plan.get("identity_hash") == current["identity_hash"],
                    "current_plan_ready": current["status"] == "ready",
                },
                "current": {"id": current["id"], "identity_hash": current["identity_hash"], "status": current["status"]},
                "result": {"valid": valid, "invalidated": not valid, "failed_checks": failed},
                "boundaries": self._boundaries(),
            },
            PLAN_CHECK_SCHEMA,
            generated_at,
        )

    def capture(
        self,
        plan: dict,
        *,
        activation_package: dict | None = None,
        activation_handoff: dict | None = None,
        parent_version: dict | None = None,
        generated_at: str | None = None,
    ) -> dict:
        check = self.check_plan(
            plan,
            activation_package=activation_package,
            activation_handoff=activation_handoff,
            parent_version=parent_version,
            generated_at=generated_at,
        )
        if not check["result"]["valid"]:
            raise ValueError("Context Version capture requires an exact currently valid capture plan.")
        truth_summary = self._truth_summary(plan["source_manifest"])
        payload = {
            "immutable": True,
            "content_embedded": False,
            "scope": plan["scope"],
            "temporal": {
                "captured_at": plan["temporal"]["capture_at"],
                "effective_from": plan["temporal"]["effective_from"],
                "effective_until": None,
            },
            "capture": plan["capture"],
            "source_manifest": plan["source_manifest"],
            "source_fingerprint": plan["source_fingerprint"],
            "bindings": {
                "activation_package": plan["bindings"]["activation_package"],
                "activation_handoff": plan["bindings"]["activation_handoff"],
                "authority_refs": plan["bindings"]["authority_refs"],
                "policy_refs": plan["bindings"]["policy_refs"],
            },
            "lineage": {
                "parent_version": _ref(parent_version),
                "supersedes": parent_version.get("id") if parent_version else None,
                "superseding_version": None,
            },
            "implementation_evidence": plan["implementation_evidence"],
            "truth_summary": truth_summary,
            "retention": {
                "memory_form": "context_state",
                "retention_state": "unknown",
                "sensitivity": "unknown",
                "policy_refs": plan["bindings"]["policy_refs"],
                "version_metadata_and_referenced_content_independent": True,
                "transition_executed": False,
            },
            "provenance": {
                "captured_by": "ContextVersionEngine",
                "capture_plan": {"id": plan["id"], "identity_hash": plan["identity_hash"]},
                "source_authority": "referenced_sources_remain_authoritative",
            },
            "continuity_gaps": plan["continuity_gaps"],
            "authority": {
                "granted_by_version": False,
                "historical_context_may_override_current": False,
                "canonical_context_mutated": False,
            },
            "boundaries": self._boundaries(),
        }
        identity_hash = stable_hash(payload)
        version = {
            "id": f"context.version.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            **payload,
            "summary": {
                "source_count": len(plan["source_manifest"]),
                "gap_count": len(plan["continuity_gaps"]),
                "historical_identity_valid_at_capture": True,
                "current_applicability_at_capture": "exact_current_match",
                "writes_performed": False,
            },
        }
        return build_report(self.root, version, VERSION_SCHEMA, generated_at)

    def check_version(self, version: dict, *, generated_at: str | None = None) -> dict:
        if version.get("schema") != VERSION_SCHEMA:
            raise ValueError(f"Context Version check requires {VERSION_SCHEMA} input.")
        identity_valid = version.get("identity_hash") == stable_hash(self._version_identity_payload(version))
        source_checks = [self._check_source(source, version.get("implementation_evidence", {})) for source in version.get("source_manifest", [])]
        resolved = sum(1 for item in source_checks if item["resolution"] in {"current_source", "historical_implementation_evidence"})
        total = len(source_checks)
        if not identity_valid:
            historical_verification = "tampered"
        elif total and resolved == total:
            historical_verification = "verified"
        elif resolved:
            historical_verification = "partial"
        else:
            historical_verification = "unverifiable"
        current_known = [item for item in source_checks if item["current_exists"]]
        if total and len(current_known) == total and all(item["current_match"] for item in source_checks):
            current_applicability = "exact_current_match"
        elif source_checks:
            current_applicability = "superseded_or_drifted"
        else:
            current_applicability = "unknown"
        gaps = [
            {
                "id": f"context.version.gap.source_unavailable.{stable_hash(item['source_id'])[:12]}",
                "message": "A captured source identity remains known, but its exact content cannot currently be resolved.",
                "source_id": item["source_id"],
                "locator": item["locator"],
            }
            for item in source_checks
            if item["resolution"] == "unavailable"
        ]
        return build_report(
            self.root,
            {
                "read_only": True,
                "version": {"id": version.get("id"), "identity_hash": version.get("identity_hash")},
                "checks": {"identity_valid": identity_valid, "source_count": total, "resolved_source_count": resolved},
                "source_checks": source_checks,
                "continuity_gaps": gaps,
                "result": {
                    "immutable_identity": "valid" if identity_valid else "tampered",
                    "historical_verification": historical_verification,
                    "current_applicability": current_applicability,
                    "historically_valid_identity": identity_valid,
                    "all_historical_sources_resolvable": bool(total) and resolved == total,
                },
                "authority": {
                    "current_authority_from_version": False,
                    "current_canonical_context_governs": True,
                },
                "boundaries": self._boundaries(),
            },
            VERSION_CHECK_SCHEMA,
            generated_at,
        )

    def _source_manifest(self, scope: dict, package_sources: list[dict], extra_paths: list[str]) -> tuple[list[dict], list[dict]]:
        declarations = {item.get("path"): item for item in package_sources if item.get("path")}
        for locator in extra_paths:
            declarations.setdefault(locator, {})
        manifest = []
        gaps = []
        for locator, declared in sorted(declarations.items()):
            raw_path = Path(locator)
            path = (self.root / raw_path).resolve()
            try:
                path.relative_to(self.root)
            except ValueError:
                gaps.append(
                    {"id": f"context.version.gap.source_outside_root.{stable_hash(locator)[:12]}", "message": "A governed source locator escapes the Context root and was not read."}
                )
                continue
            if raw_path.is_absolute():
                gaps.append(
                    {"id": f"context.version.gap.source_absolute.{stable_hash(locator)[:12]}", "message": "An absolute source locator is not portable and was not read."}
                )
                continue
            if not path.is_file():
                gaps.append(
                    {"id": f"context.version.gap.source_missing.{stable_hash(locator)[:12]}", "message": f"Governed source is unavailable: {locator}"}
                )
                continue
            fingerprint = sha256_file(path)
            declared_hash = declared.get("hash")
            if declared_hash and declared_hash != fingerprint:
                gaps.append(
                    {"id": f"context.version.gap.source_drift.{stable_hash(locator)[:12]}", "message": f"Governed source drifted from its supplied binding: {locator}"}
                )
            title, source_version = _title_and_version(path)
            manifest.append(
                {
                    "source_id": _source_id(scope, locator),
                    "title": title,
                    "source_version": source_version,
                    "source_of_record": {"adapter": "filesystem", "locator": locator},
                    "fingerprint": {"algorithm": "sha256", "value": fingerprint},
                    "authority_tier": declared.get("authority_tier") or _authority_tier(locator),
                    "lifecycle_state": declared.get("lifecycle_state") or _lifecycle_state(locator),
                    "truth": {
                        "epistemic_support": None,
                        "governance_lifecycle": None,
                        "strategic_belief": None,
                    },
                    "content_embedded": False,
                }
            )
        return manifest, gaps

    def _repository_evidence(self) -> dict:
        head = _git(self.root, "rev-parse", "HEAD")
        if not head:
            return {"adapter": None, "available": False, "implementation_only": True, "snapshot_covers_sources": False}
        status = _git(self.root, "status", "--porcelain")
        tree = _git(self.root, "rev-parse", "HEAD^{tree}")
        clean = status == ""
        return {
            "adapter": "git",
            "available": True,
            "implementation_ref": head,
            "tree_ref": tree,
            "working_state_clean": clean,
            "snapshot_covers_sources": clean,
            "implementation_only": True,
            "universal_context_identity": False,
        }

    def _check_source(self, source: dict, implementation_evidence: dict) -> dict:
        locator = source.get("source_of_record", {}).get("locator")
        expected = source.get("fingerprint", {}).get("value")
        adapter = source.get("source_of_record", {}).get("adapter")
        current_path = self.root / locator if adapter == "filesystem" and locator else None
        current_exists = bool(current_path and current_path.is_file())
        current_hash = sha256_file(current_path) if current_exists else None
        current_match = current_hash == expected if current_hash else False
        historical_hash = None
        if not current_match and adapter == "filesystem" and implementation_evidence.get("adapter") == "git" and implementation_evidence.get("snapshot_covers_sources"):
            commit = implementation_evidence.get("implementation_ref")
            blob = _git(self.root, "show", f"{commit}:{locator}", text=False) if commit and locator else None
            historical_hash = sha256_bytes(blob) if isinstance(blob, bytes) else None
        historical_match = historical_hash == expected if historical_hash else False
        resolution = "current_source" if current_match else "historical_implementation_evidence" if historical_match else "unavailable"
        return {
            "source_id": source.get("source_id"),
            "locator": locator,
            "expected_hash": expected,
            "current_exists": current_exists,
            "current_hash": current_hash,
            "current_match": current_match,
            "historical_hash": historical_hash,
            "historical_match": historical_match,
            "resolution": resolution,
        }

    @staticmethod
    def _source_refs(manifest: list[dict], paths: list[str] | tuple[str, ...]) -> list[dict]:
        wanted = set(paths)
        return [
            {"source_id": item["source_id"], "locator": item["source_of_record"]["locator"], "fingerprint": item["fingerprint"]}
            for item in manifest
            if item["source_of_record"]["locator"] in wanted
        ]

    @staticmethod
    def _truth_summary(manifest: list[dict]) -> dict:
        summary = {}
        for axis, states in TRUTH_STATES.items():
            counts = Counter(item.get("truth", {}).get(axis) for item in manifest)
            summary[axis] = {state: counts[state] for state in states}
            summary[axis]["unclassified"] = sum(1 for item in manifest if item.get("truth", {}).get(axis) not in states)
        return summary

    @staticmethod
    def _validate_inputs(
        scope: dict,
        event_type: str,
        reason: str,
        capture_at: str,
        mission_id: str | None,
        activation_package: dict | None,
        activation_handoff: dict | None,
    ) -> None:
        required_scope = ("organization", "domain", "tier", "context_root")
        if not isinstance(scope, dict) or any(not scope.get(field) for field in required_scope):
            raise ValueError("Context Version scope requires organization, domain, tier, and context_root.")
        if scope["tier"] not in TIERS:
            raise ValueError(f"Context Version tier must be one of: {', '.join(sorted(TIERS))}.")
        if event_type not in CAPTURE_EVENTS:
            raise ValueError(f"Unsupported Context Version capture event: {event_type}")
        if not reason or not reason.strip():
            raise ValueError("Context Version capture requires an explicit reason.")
        if not capture_at:
            raise ValueError("Context Version capture requires an explicit temporal basis.")
        try:
            datetime.fromisoformat(capture_at.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Context Version capture_at must be ISO-8601.") from exc
        if event_type == "mission_start" and not mission_id:
            raise ValueError("Mission-start Context Version capture requires mission_id.")
        if activation_handoff and not activation_package:
            raise ValueError("Activation Handoff binding requires its Activation Package.")

    @staticmethod
    def _boundaries() -> dict:
        return {
            "read_only": True,
            "context_content_copied": False,
            "canonical_context_mutated": False,
            "authority_granted": False,
            "activation_package_replaced": False,
            "git_is_universal_identity": False,
            "historical_truth_regenerated": False,
            "retention_transition_executed": False,
            "graph_or_reasoning_used": False,
        }

    @staticmethod
    def _plan_identity_payload(plan: dict) -> dict:
        return {
            "inputs": plan.get("inputs"),
            "source_manifest": plan.get("source_manifest"),
            "source_fingerprint": plan.get("source_fingerprint"),
            "bindings": plan.get("bindings"),
            "implementation_evidence": plan.get("implementation_evidence"),
            "validator": plan.get("validator"),
            "gates": plan.get("gates"),
            "continuity_gaps": plan.get("continuity_gaps"),
        }

    @staticmethod
    def _version_identity_payload(version: dict) -> dict:
        return {
            key: version.get(key)
            for key in (
                "immutable",
                "content_embedded",
                "scope",
                "temporal",
                "capture",
                "source_manifest",
                "source_fingerprint",
                "bindings",
                "lineage",
                "implementation_evidence",
                "truth_summary",
                "retention",
                "provenance",
                "continuity_gaps",
                "authority",
                "boundaries",
            )
        }
