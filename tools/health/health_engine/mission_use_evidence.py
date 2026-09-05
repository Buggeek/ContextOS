from __future__ import annotations

import datetime as _dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path


TOOLS_ROOT = Path(__file__).resolve().parents[2]
ACTIVATION_ROOT = TOOLS_ROOT / "activation"
ADOPTION_ROOT = TOOLS_ROOT / "adoption"
for module_root in (ACTIVATION_ROOT, ADOPTION_ROOT):
    if str(module_root) not in sys.path:
        sys.path.insert(0, str(module_root))

from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402
from adoption_engine import load_adoption_profile  # noqa: E402


SCHEMA = "contextos.mission.context_use_evidence/1"
EVIDENCE_SEMANTICS = {"observed", "declared", "derived", "unknown"}
USE_STATES = {"consumed", "used", "useful"}
SUFFICIENCY_STATES = {"sufficient", "partial", "insufficient", "unknown"}
INTERVENTION_TYPES = {"procedural", "strategic"}


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


def _normalize_sufficiency(item: dict | None) -> dict:
    assertion = _normalize_assertion(
        item
        or {
            "status": "unknown",
            "statement": "Context sufficiency was not supplied.",
            "evidence_semantics": "unknown",
            "evidence_refs": [],
        }
    )
    if assertion.get("status") not in SUFFICIENCY_STATES:
        raise ValueError(f"Unsupported context sufficiency state: {assertion.get('status')!r}.")
    return assertion


def _normalize_human_intervention(item: dict) -> dict:
    assertion = _normalize_assertion(item)
    if assertion.get("intervention_type") not in INTERVENTION_TYPES:
        raise ValueError("Human intervention must be procedural or strategic.")
    if not assertion.get("actor") or not assertion.get("reason"):
        raise ValueError("Human intervention requires actor and reason.")
    return assertion


def _normalize_automatic_consequence(item: dict) -> dict:
    assertion = _normalize_assertion(item)
    required = ("trigger_action_ref", "consequence", "platform")
    if any(not assertion.get(field) for field in required):
        raise ValueError("Automatic consequence requires trigger_action_ref, consequence, and platform.")
    if assertion.get("execution_mode") != "platform_automatic":
        raise ValueError("Automatic consequence must declare execution_mode=platform_automatic.")
    if assertion.get("manual_authority_granted") is not False:
        raise ValueError("Automatic consequence must explicitly grant no manual authority.")
    if assertion.get("downstream_manual_operations_authorized") is not False:
        raise ValueError("Automatic consequence must explicitly prohibit downstream manual authority.")
    return assertion


def _normalize_work_ownership(resolution: dict | None, check: dict | None) -> dict | None:
    if resolution is None and check is None:
        return None
    if resolution is None or check is None:
        raise ValueError("Mission-use ownership evidence requires both Resolution and currentness check.")
    if resolution.get("schema") != "contextos.reasoning.work_ownership_resolution/1":
        raise ValueError("Mission-use ownership evidence requires a Work Ownership Resolution.")
    if check.get("schema") != "contextos.reasoning.work_ownership_resolution_check/1":
        raise ValueError("Mission-use ownership evidence requires a Work Ownership Resolution check.")
    bound = check.get("resolution", {})
    binding_matches = (
        bound.get("id") == resolution.get("id")
        and bound.get("identity_hash") == resolution.get("identity_hash")
    )
    result = resolution.get("result", {})
    check_result = check.get("result", {})
    disposition = result.get("disposition")
    return {
        "resolution": {"id": resolution.get("id"), "identity_hash": resolution.get("identity_hash")},
        "currentness_check": {"id": check.get("id"), "identity_hash": check.get("identity_hash")},
        "binding_matches": binding_matches,
        "disposition": disposition,
        "existing_work_found": bool(result.get("current_ownership_exists")),
        "duplicate_proposal_prevented": bool(result.get("duplicate_work_prevented")),
        "material_currentness_check_performed": True,
        "materially_current": bool(check_result.get("materially_current")),
        "reanchor_required": bool(check_result.get("reanchor_required")),
        "recommendation_invalidated_by_current_work": bool(result.get("duplicate_work_prevented")),
        "ownership_conflict": bool(result.get("ownership_conflict")),
        "ownership_unknown": disposition == "OWNERSHIP_UNKNOWN",
        "human_intervention_avoided": "unknown",
        "evidence_semantics": "derived",
        "evidence_refs": sorted(
            ref for ref in (resolution.get("id"), check.get("id")) if ref
        ),
    }


class MissionContextUseEvidenceEngine:
    """Build explicit, read-only evidence about context participation in a Mission."""

    def __init__(self, root: str | Path = ".", adoption_profile=None) -> None:
        self.root = Path(root)
        self.adoption_profile = load_adoption_profile(adoption_profile)

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
        target_identity: dict | None = None,
        context_sufficiency: dict | None = None,
        prior_art_reuse: list[dict] | None = None,
        rejected_recommendations: list[dict] | None = None,
        authority_escalations: list[dict] | None = None,
        human_interventions: list[dict] | None = None,
        automatic_consequences: list[dict] | None = None,
        work_ownership_resolution: dict | None = None,
        work_ownership_check: dict | None = None,
        mission_outcome: dict | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if package.get("schema") != "contextos.activation.package/1":
            raise ValueError("Mission-use evidence requires contextos.activation.package/1 input.")
        if handoff.get("schema") != "contextos.activation.handoff/1":
            raise ValueError("Mission-use evidence requires contextos.activation.handoff/1 input.")

        root = self.root.resolve()
        if self.adoption_profile and not target_identity:
            raise ValueError("External Mission-use evidence requires explicit target_identity.")
        if target_identity and not self.adoption_profile:
            raise ValueError("Target identity requires an exact Adoption Profile binding.")
        target_binding = _normalize_assertion(target_identity) if target_identity else None
        if target_binding and (not target_binding.get("organization") or not target_binding.get("repository")):
            raise ValueError("Target identity requires organization and repository.")

        activation = ContextActivationPackageEngine(root, self.adoption_profile)
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
        sufficiency = _normalize_sufficiency(context_sufficiency)
        prior_art = [_normalize_assertion(item) for item in prior_art_reuse or []]
        rejected = [_normalize_assertion(item) for item in rejected_recommendations or []]
        escalations = [_normalize_assertion(item) for item in authority_escalations or []]
        interventions = [_normalize_human_intervention(item) for item in human_interventions or []]
        consequences = [_normalize_automatic_consequence(item) for item in automatic_consequences or []]
        ownership_evidence = _normalize_work_ownership(work_ownership_resolution, work_ownership_check)
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
                    "mapped_concept": source.get("mapped_concept"),
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
            for group in (
                accesses,
                retrievals,
                assertions,
                gaps,
                stale,
                contribution_items,
                [sufficiency],
                prior_art,
                rejected,
                escalations,
                interventions,
                consequences,
                [ownership_evidence] if ownership_evidence else [],
                [target_binding] if target_binding else [],
                [outcome],
            )
            for item in group
        )
        profile_binding = self.adoption_profile.binding() if self.adoption_profile else None
        package_profile = package.get("adoption_profile")
        handoff_profile = handoff.get("adoption_profile")
        profile_check = (
            self.adoption_profile.check_binding(package_profile or {})
            if self.adoption_profile
            else {"valid": package_profile is None, "checks": {"profile_absent": package_profile is None}}
        )
        handoff_profile_matches = handoff_profile == profile_binding
        target_matches_profile = True
        if self.adoption_profile and target_binding:
            profile_target = self.adoption_profile.data["target"]
            organization = str(target_binding["organization"]).casefold()
            target_matches_profile = organization in {
                str(profile_target.get("id", "")).casefold(),
                str(profile_target.get("name", "")).casefold(),
            }
        bindings = {
            "activation_package": {"id": package.get("id"), "identity_hash": package.get("identity_hash")},
            "activation_handoff": {"id": handoff.get("id"), "identity_hash": handoff.get("identity_hash")},
            "adoption_profile": profile_binding,
            "adoption_profile_binding_semantics": "derived" if profile_binding else "not_applicable",
            "target": target_binding,
            "mission": handoff.get("mission", {}),
            "consumer": handoff.get("consumer", {}),
        }
        if ownership_evidence:
            bindings["work_ownership"] = ownership_evidence
        failed_checks = (
            package_check["result"]["failed_checks"]
            + handoff_check["result"]["failed_checks"]
            + ([] if package_handoff_binding_matches else ["mission_use.package_handoff_binding_mismatch"])
            + ([] if profile_check["valid"] else ["mission_use.adoption_profile_binding_mismatch"])
            + ([] if handoff_profile_matches else ["mission_use.handoff_profile_binding_mismatch"])
            + ([] if target_matches_profile else ["mission_use.target_profile_mismatch"])
            + (
                []
                if ownership_evidence is None or ownership_evidence["binding_matches"]
                else ["mission_use.work_ownership_binding_mismatch"]
            )
            + (
                []
                if ownership_evidence is None or ownership_evidence["materially_current"]
                else ["mission_use.work_ownership_requires_reanchor"]
            )
        )
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
                "context_sufficiency": sufficiency,
                "prior_art_reuse": prior_art,
                "rejected_recommendations": rejected,
                "authority_escalations": escalations,
                "human_interventions": interventions,
                "automatic_consequences": consequences,
                "explicit_exclusions": package.get("exclusions", []),
            },
            "mission_outcome": outcome,
            "summary": {
                "selected_count": len(selected),
                "selected_accessed_count": len(accessed_refs),
                "execution_retrieval_count": len(retrievals),
                "additional_retrieval_burden_count": len(retrievals),
                "gap_count": len(gaps),
                "stale_context_count": len(stale),
                "contribution_count": len(contribution_items),
                "prior_art_reuse_count": len(prior_art),
                "rejected_recommendation_count": len(rejected),
                "authority_escalation_count": len(escalations),
                "human_procedural_intervention_count": sum(1 for item in interventions if item["intervention_type"] == "procedural"),
                "human_strategic_intervention_count": sum(1 for item in interventions if item["intervention_type"] == "strategic"),
                "automatic_consequence_count": len(consequences),
                "context_sufficiency": sufficiency["status"],
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
                "adoption_profile_valid_at_capture": profile_check["valid"],
                "adoption_profile_checks": profile_check["checks"],
                "handoff_profile_binding_matches": handoff_profile_matches,
                "target_identity_matches_profile": target_matches_profile,
                "failed_checks": sorted(set(failed_checks)),
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
                "automatic_consequence_implies_manual_authority": False,
                "procedural_intervention_implies_strategic_authority": False,
            },
            "observability_limits": [
                "Filesystem or runtime access alone does not prove cognitive consumption.",
                "Mission success alone does not prove that selected context caused the outcome.",
                "A source without an access record remains not-observed-accessed, not unused.",
                "A platform-defined automatic consequence does not grant manual authority over the downstream system.",
                "A human procedural intervention does not imply a human strategic decision.",
            ],
            "read_only": True,
            "constraints": {
                "telemetry_installed": False,
                "surveillance_monitoring_used": False,
                "canonical_context_mutated": False,
                "usefulness_inferred": False,
                "automatic_consequence_grants_manual_authority": False,
                "adoption_profile_is_target_ssot": False,
            },
        }
        if ownership_evidence:
            body["context_participation"]["work_ownership_resolution"] = ownership_evidence
            body["summary"].update(
                {
                    "work_ownership_resolution_performed": True,
                    "duplicate_work_prevented": ownership_evidence["duplicate_proposal_prevented"],
                    "material_currentness_check_performed": True,
                    "work_ownership_reanchor_required": ownership_evidence["reanchor_required"],
                }
            )
            body["epistemic_boundaries"]["duplicate_prevention_implies_burden_reduction"] = False
            body["observability_limits"].append(
                "Preventing one duplicate proposal does not prove reduced cognitive burden or organizational usefulness."
            )
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
        (
            f"- Adoption Profile: `{report['bindings']['adoption_profile']['id']}` "
            f"v{report['bindings']['adoption_profile']['version']}"
            if report["bindings"].get("adoption_profile")
            else "- Adoption Profile: `<native Context OS mode>`"
        ),
        (
            f"- Target: `{report['bindings']['target']['organization']}` / "
            f"`{report['bindings']['target']['repository']}`"
            if report["bindings"].get("target")
            else "- Target: `<current Context root>`"
        ),
        f"- Package valid at capture: {'yes' if report['validity']['package_valid_at_capture'] else 'no'}",
        f"- Handoff valid at capture: {'yes' if report['validity']['handoff_valid_at_capture'] else 'no'}",
        "",
        "## Participation",
        f"- Governing sources selected: {summary['selected_count']}",
        f"- Selected sources with access evidence: {summary['selected_accessed_count']}",
        f"- Additional Execution Context retrieved: {summary['execution_retrieval_count']}",
        f"- Context sufficiency: `{summary['context_sufficiency']}`",
        f"- Prior-art reuse records: {summary['prior_art_reuse_count']}",
        f"- Rejected recommendations: {summary['rejected_recommendation_count']}",
        f"- Authority escalations: {summary['authority_escalation_count']}",
        f"- Human procedural interventions: {summary['human_procedural_intervention_count']}",
        f"- Human strategic interventions: {summary['human_strategic_intervention_count']}",
        f"- Platform-automatic consequences: {summary['automatic_consequence_count']}",
        *(
            [
                "- Work Ownership Resolution performed: yes",
                f"- Duplicate work proposal prevented: {'yes' if summary['duplicate_work_prevented'] else 'no'}",
                f"- Material ownership re-anchor required: {'yes' if summary['work_ownership_reanchor_required'] else 'no'}",
            ]
            if summary.get("work_ownership_resolution_performed")
            else []
        ),
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
        "- Automatic consequence does not imply delegated manual authority.",
        "- Procedural intervention does not imply strategic authority.",
        *(
            ["- Duplicate prevention does not by itself prove reduced cognitive burden."]
            if summary.get("work_ownership_resolution_performed")
            else []
        ),
        "",
        "## Mission Outcome",
        f"- `{report['mission_outcome'].get('status', 'unknown')}` "
        f"[{report['mission_outcome']['evidence_semantics']}]: {report['mission_outcome'].get('statement', '')}",
    ]
    return "\n".join(lines) + "\n"
