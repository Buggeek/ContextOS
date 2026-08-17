from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


TOOLS_ROOT = Path(__file__).resolve().parents[2]
ACTIVATION_ROOT = TOOLS_ROOT / "activation"
if str(ACTIVATION_ROOT) not in sys.path:
    sys.path.insert(0, str(ACTIVATION_ROOT))

from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402


SCHEMA = "contextos.mission.context_use_evidence/1"
EVIDENCE_SEMANTICS = {"observed", "declared", "derived", "unknown"}
USE_STATES = {"consumed", "used", "useful"}


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: dict) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_assertion(item: dict, *, allowed_states: set[str] | None = None) -> dict:
    assertion = dict(item)
    semantics = assertion.get("evidence_semantics")
    if semantics not in EVIDENCE_SEMANTICS:
        raise ValueError(f"Unsupported evidence semantics: {semantics!r}.")
    if allowed_states is not None and assertion.get("state") not in allowed_states:
        raise ValueError(f"Unsupported context-use state: {assertion.get('state')!r}.")
    assertion["evidence_refs"] = sorted(dict.fromkeys(assertion.get("evidence_refs", [])))
    return assertion


class MissionContextUseEvidenceEngine:
    """Build explicit, read-only evidence about context participation in a Mission."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        *,
        package: dict,
        handoff: dict,
        selected_accesses: list[dict] | None = None,
        execution_retrievals: list[dict] | None = None,
        use_assertions: list[dict] | None = None,
        context_gaps: list[dict] | None = None,
        stale_context: list[dict] | None = None,
        contributions: list[dict] | None = None,
        mission_outcome: dict | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if package.get("schema") != "contextos.activation.package/1":
            raise ValueError("Mission-use evidence requires contextos.activation.package/1 input.")
        if handoff.get("schema") != "contextos.activation.handoff/1":
            raise ValueError("Mission-use evidence requires contextos.activation.handoff/1 input.")

        root = self.root.resolve()
        activation = ContextActivationPackageEngine(root)
        package_check = activation.check_package(package, generated_at=generated_at)
        handoff_check = activation.check_handoff(handoff, generated_at=generated_at)
        handoff_package = handoff.get("source_package", {})
        package_handoff_binding_matches = (
            handoff_package.get("id") == package.get("id")
            and handoff_package.get("identity_hash") == package.get("identity_hash")
        )
        selected_by_ref = {item["path"]: item for item in handoff.get("selected_context", [])}

        accesses = []
        for item in selected_accesses or []:
            normalized = _normalize_assertion(item)
            source_ref = normalized.get("source_ref")
            if source_ref not in selected_by_ref:
                raise ValueError(f"Selected access is not bound to handoff context: {source_ref!r}.")
            normalized["selected_source_hash"] = selected_by_ref[source_ref].get("source_hash")
            accesses.append(normalized)

        retrievals = []
        for item in execution_retrievals or []:
            normalized = _normalize_assertion(item)
            if not normalized.get("reason") or not normalized.get("mission_need"):
                raise ValueError("Execution retrieval requires reason and mission_need.")
            if not normalized.get("authority"):
                raise ValueError("Execution retrieval requires explicit access authority.")
            source_ref = normalized.get("source_ref")
            if not source_ref:
                raise ValueError("Execution retrieval requires source_ref.")
            local_path = root / source_ref
            if local_path.is_file():
                normalized["freshness"] = {
                    "observed_hash": sha256_file(local_path),
                    "exists_at_capture": True,
                    "stale_when": "source_hash_changes",
                }
            else:
                normalized["freshness"] = {
                    "observed_hash": None,
                    "exists_at_capture": False,
                    "stale_when": "source_identity_or_operational_state_changes",
                }
            retrievals.append(normalized)

        assertions = [_normalize_assertion(item, allowed_states=USE_STATES) for item in use_assertions or []]
        gaps = [_normalize_assertion(item) for item in context_gaps or []]
        stale = [_normalize_assertion(item) for item in stale_context or []]
        contribution_items = [_normalize_assertion(item) for item in contributions or []]
        outcome = _normalize_assertion(mission_outcome or {
            "status": "unknown",
            "evidence_semantics": "unknown",
            "statement": "Mission outcome was not supplied.",
            "evidence_refs": [],
        })

        accessed_refs = {item["source_ref"] for item in accesses}
        selected = []
        for source_ref, source in selected_by_ref.items():
            selected.append(
                {
                    "source_ref": source_ref,
                    "source_hash": source.get("source_hash"),
                    "authority_tier": source.get("authority_tier"),
                    "selection_state": "selected",
                    "access_state": "accessed" if source_ref in accessed_refs else "not_observed_accessed",
                    "access_state_semantics": "derived",
                    "consumption_state": "unknown",
                    "use_state": "unknown",
                    "usefulness_state": "unknown",
                }
            )

        assertion_counts = Counter(item["state"] for item in assertions)
        supported_useful_count = sum(
            1
            for item in assertions
            if item["state"] == "useful" and item["evidence_semantics"] in {"observed", "declared"}
        )
        semantics_counts = Counter(
            item["evidence_semantics"]
            for group in (accesses, retrievals, assertions, gaps, stale, contribution_items, [outcome])
            for item in group
        )
        bindings = {
            "activation_package": {"id": package.get("id"), "identity_hash": package.get("identity_hash")},
            "activation_handoff": {"id": handoff.get("id"), "identity_hash": handoff.get("identity_hash")},
            "mission": handoff.get("mission", {}),
            "consumer": handoff.get("consumer", {}),
        }
        body = {
            "bindings": bindings,
            "context_participation": {
                "governing_context_selected": selected,
                "selected_context_accesses": sorted(accesses, key=lambda item: item["source_ref"]),
                "execution_context_retrieved": sorted(retrievals, key=lambda item: item["source_ref"]),
                "use_assertions": sorted(assertions, key=lambda item: (item["state"], item.get("source_ref", ""))),
                "context_gaps": gaps,
                "stale_or_invalid_context": stale,
                "contributions": contribution_items,
                "explicit_exclusions": package.get("exclusions", []),
            },
            "mission_outcome": outcome,
            "summary": {
                "selected_count": len(selected),
                "selected_accessed_count": len(accessed_refs),
                "execution_retrieval_count": len(retrievals),
                "gap_count": len(gaps),
                "stale_context_count": len(stale),
                "contribution_count": len(contribution_items),
                "consumed_assertion_count": assertion_counts["consumed"],
                "used_assertion_count": assertion_counts["used"],
                "useful_assertion_count": assertion_counts["useful"],
                "supported_useful_assertion_count": supported_useful_count,
                "evidence_semantics_counts": {key: semantics_counts[key] for key in sorted(EVIDENCE_SEMANTICS)},
            },
            "validity": {
                "package_valid_at_capture": package_check["result"]["valid"],
                "handoff_valid_at_capture": handoff_check["result"]["valid"],
                "package_handoff_binding_matches": package_handoff_binding_matches,
                "failed_checks": sorted(
                    set(
                        package_check["result"]["failed_checks"]
                        + handoff_check["result"]["failed_checks"]
                        + ([] if package_handoff_binding_matches else ["mission_use.package_handoff_binding_mismatch"])
                    )
                ),
            },
            "evidence_semantics": {
                "observed": "Directly supported by runtime or Mission evidence.",
                "declared": "Explicitly reported by the consumer but not independently observed.",
                "derived": "Deterministically computed from observed evidence.",
                "unknown": "Available evidence cannot support a claim.",
            },
            "epistemic_boundaries": {
                "selected_implies_retrieved": False,
                "retrieved_implies_consumed": False,
                "consumed_implies_used": False,
                "used_implies_useful": False,
                "missing_access_record_implies_unused": False,
                "usefulness_inferred_from_mission_success": False,
            },
            "observability_limits": [
                "Filesystem or runtime access alone does not prove cognitive consumption.",
                "Mission success alone does not prove that selected context caused the outcome.",
                "A source without an access record remains not-observed-accessed, not unused.",
            ],
            "read_only": True,
            "constraints": {
                "telemetry_installed": False,
                "surveillance_monitoring_used": False,
                "canonical_context_mutated": False,
                "usefulness_inferred": False,
            },
        }
        identity_hash = stable_hash(body)
        return {
            "schema": SCHEMA,
            "id": f"mission.context_use_evidence.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            "generated_at": generated_at or generated_timestamp(),
            "root": str(root),
            **body,
        }


def render_human(report: dict) -> str:
    summary = report["summary"]
    mission = report["bindings"]["mission"]
    lines = [
        "# Context OS Mission-Use Evidence",
        "",
        f"- Mission: `{mission.get('mission_id')}`",
        f"- Consumer: `{report['bindings']['consumer'].get('type')}`",
        f"- Package: `{report['bindings']['activation_package']['id']}`",
        f"- Handoff: `{report['bindings']['activation_handoff']['id']}`",
        f"- Package valid at capture: {'yes' if report['validity']['package_valid_at_capture'] else 'no'}",
        f"- Handoff valid at capture: {'yes' if report['validity']['handoff_valid_at_capture'] else 'no'}",
        "",
        "## Participation",
        f"- Governing sources selected: {summary['selected_count']}",
        f"- Selected sources with access evidence: {summary['selected_accessed_count']}",
        f"- Additional Execution Context retrieved: {summary['execution_retrieval_count']}",
        f"- Context gaps: {summary['gap_count']}",
        f"- Stale or invalid context observations: {summary['stale_context_count']}",
        f"- Recorded contributions: {summary['contribution_count']}",
        "",
        "## Evidence Boundary",
        "- Selected does not imply retrieved.",
        "- Retrieved does not imply consumed.",
        "- Consumed does not imply used.",
        "- Used does not imply useful.",
        "- Missing access evidence means unknown, not unused.",
        "",
        "## Mission Outcome",
        f"- `{report['mission_outcome'].get('status', 'unknown')}` "
        f"[{report['mission_outcome']['evidence_semantics']}]: {report['mission_outcome'].get('statement', '')}",
    ]
    return "\n".join(lines) + "\n"
