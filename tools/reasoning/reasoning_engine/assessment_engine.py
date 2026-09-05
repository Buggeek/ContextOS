from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from .report_builder import build_check_report, build_report


TOOLS_ROOT = Path(__file__).resolve().parents[2]
for runtime in ("activation", "health", "memory", "adoption"):
    path = TOOLS_ROOT / runtime
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from health_engine.health_engine import ContextHealthEngine  # noqa: E402
from memory_engine import ContextVersionEngine, MemoryRetrievalEngine  # noqa: E402
from adoption_engine import load_adoption_profile  # noqa: E402
from .work_ownership import WorkOwnershipResolver


ASSERTION_TYPES = {
    "observation",
    "prior_art",
    "context_change",
    "contradiction",
    "interpretation",
    "hypothesis",
    "recommendation",
    "unknown",
    "required_decision",
    "additional_evidence",
}
EPISTEMIC_SUPPORT = {"observed", "declared", "derived", "inferred", "unknown"}


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def assertion(
    kind: str,
    statement: str,
    evidence_refs: list[str] | tuple[str, ...],
    *,
    epistemic_support: str,
    support_state: str,
    governance_lifecycle: str = "suggested",
    strategic_belief: str | None = None,
    authority_required: str | None = None,
) -> dict:
    if kind not in ASSERTION_TYPES:
        raise ValueError(f"Unsupported reasoning assertion type: {kind}")
    if epistemic_support not in EPISTEMIC_SUPPORT:
        raise ValueError(f"Unsupported epistemic support: {epistemic_support}")
    refs = sorted(dict.fromkeys(evidence_refs))
    identity = stable_hash({"kind": kind, "statement": statement, "evidence_refs": refs})
    return {
        "id": f"reasoning.{kind}.{identity[:12]}",
        "type": kind,
        "statement": statement,
        "epistemic_support": epistemic_support,
        "support_state": support_state,
        "governance_lifecycle": governance_lifecycle,
        "strategic_belief": strategic_belief,
        "evidence_refs": refs,
        "authority_required": authority_required,
        "canonical": False,
        "decision": False,
    }


class ContextualAssessmentEngine:
    """Compose governed Runtime evidence into a bounded advisory assessment."""

    def __init__(self, root: str | Path = ".", adoption_profile=None) -> None:
        self.root = Path(root).resolve()
        self.adoption_profile = load_adoption_profile(adoption_profile)

    def run(
        self,
        *,
        goal: str,
        mission_id: str | None = None,
        consumer: str = "human",
        question: str | None = None,
        purpose: str | None = None,
        organizational_mode: str = "local",
        actor_roles: list[str] | tuple[str, ...] = (),
        authority_scope: str | None = None,
        retention_policies: list[dict] | None = None,
        memory_metadata_by_id: dict | None = None,
        context_versions: list[dict] | tuple[dict, ...] = (),
        mission_use_evidence: dict | None = None,
        reasoning_evidence: dict | None = None,
        work_ownership_resolution: dict | None = None,
        focus_entities: list[str] | tuple[str, ...] = (),
        memory_limit: int = 12,
        evaluation_time: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if not goal or not goal.strip():
            raise ValueError("Contextual Assessment requires a goal.")
        if not consumer or not consumer.strip():
            raise ValueError("Contextual Assessment requires a consumer.")

        from .structured_evidence import derive_reasoning, normalize_evidence_set

        versions = list(context_versions)
        evidence_set = normalize_evidence_set(reasoning_evidence)
        focus = sorted(set(str(item) for item in focus_entities))
        structured_reasoning = derive_reasoning(evidence_set, focus)
        version_checks = self._check_versions(versions, generated_at)
        ownership_check = self._check_work_ownership(work_ownership_resolution, generated_at)
        health = ContextHealthEngine(self.root, self.adoption_profile).run(
            mission_use_evidence=mission_use_evidence,
            generated_at=generated_at,
        )
        memory = MemoryRetrievalEngine(self.root, self.adoption_profile).run(
            goal=goal,
            mission_id=mission_id,
            question=question,
            consumer=consumer,
            purpose=purpose or "Supply governed prior art to Contextual Assessment.",
            organizational_mode=organizational_mode,
            actor_roles=actor_roles,
            authority_scope=authority_scope,
            retention_policies=retention_policies,
            memory_metadata_by_id=memory_metadata_by_id,
            context_versions=versions,
            limit=memory_limit,
            evaluation_time=evaluation_time,
            generated_at=generated_at,
        )
        reasoning = self._reason(
            health,
            memory,
            version_checks,
            structured_reasoning,
            work_ownership_resolution,
            ownership_check,
            has_structured_claims=bool(evidence_set["claims"]),
        )
        all_assertions = [item for values in reasoning.values() for item in values]
        counts = Counter(item["type"] for item in all_assertions)
        status = self._status(health, reasoning)
        consequential_gate = self._consequential_gate(work_ownership_resolution, ownership_check)
        query = {
            "goal": goal.strip(),
            "mission_id": mission_id,
            "consumer": consumer.strip(),
            "question": (question or "").strip() or None,
            "purpose": (purpose or "").strip() or None,
            "organizational_mode": organizational_mode,
            "actor_roles": sorted(set(actor_roles)),
            "authority_scope": authority_scope,
            "focus_entities": focus,
            "memory_limit": memory_limit,
            "evaluation_time": evaluation_time,
        }
        bindings = {
            "adoption_profile": self.adoption_profile.binding() if self.adoption_profile else None,
            "activation_package": self._ref(memory["activation_package"]),
            "health_report": self._ref(health),
            "memory_retrieval": self._ref(memory),
            "context_versions": {
                "supplied_count": len(versions),
                "index_hash": memory["bindings"]["context_version_index_hash"],
                "checks": [
                    {
                        "id": check["version"]["id"],
                        "identity_hash": check["version"]["identity_hash"],
                        "immutable_identity": check["result"]["immutable_identity"],
                        "historical_verification": check["result"]["historical_verification"],
                        "current_applicability": check["result"]["current_applicability"],
                    }
                    for check in version_checks
                ],
            },
            "reasoning_evidence": {
                "schema": evidence_set["schema"],
                "id": evidence_set["id"],
                "identity_hash": evidence_set["identity_hash"],
                "claim_count": len(evidence_set["claims"]),
                "relationship_count": len(evidence_set["relationships"]),
            },
        }
        if work_ownership_resolution and ownership_check:
            bindings["work_ownership"] = {
                "resolution": self._ref(work_ownership_resolution) if work_ownership_resolution else None,
                "check": {
                    "materially_current": ownership_check["result"]["materially_current"],
                    "reanchor_required": ownership_check["result"]["reanchor_required"],
                    "failed_checks": ownership_check["result"]["failed_checks"],
                }
                if ownership_check
                else None,
            }
        identity_payload = self._identity_payload(
            query,
            bindings,
            reasoning,
            consequential_gate if work_ownership_resolution else None,
        )
        identity_hash = stable_hash(identity_payload)
        report = {
            "id": f"reasoning.assessment.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            "read_only": True,
            "derived_view": True,
            "query": query,
            "summary": {
                "status": status,
                "assertion_count": len(all_assertions),
                "assertion_type_counts": dict(sorted(counts.items())),
                "unknown_count": counts["unknown"],
                "recommendation_count": counts["recommendation"],
                "required_decision_count": counts["required_decision"],
                "artificial_confidence_score_used": False,
            },
            "bindings": bindings,
            "reasoning": reasoning,
            "evidence": {
                "health": health,
                "memory_retrieval": memory,
                "context_versions": versions,
                "context_version_checks": version_checks,
                "reasoning_evidence": evidence_set,
                "mission_use_evidence": mission_use_evidence,
            },
            "authority": self._authority(),
            "truth_boundary": {
                "evidence_is_interpretation": False,
                "interpretation_is_decision": False,
                "hypothesis_is_verified": False,
                "recommendation_is_decision": False,
                "historical_context_is_current_authority": False,
                "assessment_is_canonical_truth": False,
            },
            "invalidation": {
                "source_fingerprint": stable_hash(bindings),
                "conditions": [
                    "The Goal, Mission, consumer, purpose, roles, or authority scope changes.",
                    "The Activation Package, Health Report, Memory Retrieval, Context Version, or structured reasoning evidence changes.",
                    "A source, policy, retention state, temporal basis, or permission bound to an input changes.",
                    "A material Goal, Mission, ownership, lifecycle, return-condition, or coverage source changes.",
                    "A saved assessment identity no longer matches its exact bound evidence.",
                ],
            },
            "limitations": [
                "Assertions are deterministic interpretations of structured Runtime evidence, not free-form semantic truth.",
                "Contradiction and impact results require explicit comparable claims or declared relationships.",
                "Missing or policy-withheld memory remains unknown and is not reconstructed.",
                "No causal usefulness, semantic historical applicability, or decision authority is inferred.",
                "GraphRAG, embeddings, vector search, broad RAG, and autonomous execution are not used.",
                "Work Ownership Resolution uses explicit relevance and lifecycle evidence; semantic equivalence is not inferred from prose.",
            ],
        }
        if work_ownership_resolution and ownership_check:
            report["summary"]["work_ownership_disposition"] = work_ownership_resolution["result"]["disposition"]
            report["consequential_recommendation_gate"] = consequential_gate
            report["evidence"]["work_ownership_resolution"] = work_ownership_resolution
            report["evidence"]["work_ownership_check"] = ownership_check
        if self.adoption_profile:
            report["adoption_profile"] = self.adoption_profile.binding()
            report["evidence_isolation"] = {
                "target_only": True,
                "host_context_used_as_target_evidence": False,
                "profile_identity_hash": self.adoption_profile.identity_hash,
            }
        return build_report(self.root, report, generated_at)

    def check_assessment(
        self,
        saved: dict,
        *,
        retention_policies: list[dict] | None = None,
        memory_metadata_by_id: dict | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if not isinstance(saved, dict) or saved.get("schema") != "contextos.reasoning.assessment/1":
            raise ValueError("Saved Assessment must use contextos.reasoning.assessment/1.")

        expected_hash = stable_hash(
            self._identity_payload(
                saved["query"],
                saved["bindings"],
                saved["reasoning"],
                saved.get("consequential_recommendation_gate"),
            )
        )
        identity_valid = saved.get("identity_hash") == expected_hash and saved.get("id") == f"reasoning.assessment.{expected_hash[:16]}"
        failed = [] if identity_valid else ["reasoning.assessment_check.immutable_identity"]
        current = None
        error = None
        try:
            query = saved["query"]
            versions = saved["evidence"].get("context_versions", [])
            current = self.run(
                goal=query["goal"],
                mission_id=query["mission_id"],
                consumer=query["consumer"],
                question=query["question"],
                purpose=query["purpose"],
                organizational_mode=query["organizational_mode"],
                actor_roles=query["actor_roles"],
                authority_scope=query["authority_scope"],
                retention_policies=retention_policies,
                memory_metadata_by_id=memory_metadata_by_id,
                context_versions=versions,
                mission_use_evidence=saved["evidence"].get("mission_use_evidence"),
                reasoning_evidence=saved["evidence"]["reasoning_evidence"],
                work_ownership_resolution=saved["evidence"].get("work_ownership_resolution"),
                focus_entities=query.get("focus_entities", []),
                memory_limit=query.get("memory_limit", 12),
                evaluation_time=query.get("evaluation_time"),
                generated_at=saved.get("generated_at"),
            )
            current_matches = current["identity_hash"] == saved.get("identity_hash")
        except (KeyError, TypeError, ValueError) as exc:
            current_matches = False
            error = str(exc)
        if not current_matches:
            failed.append("reasoning.assessment_check.current_state_changed")

        result_payload = {
            "assessment_id": saved.get("id"),
            "assessment_hash": saved.get("identity_hash"),
            "current_hash": current.get("identity_hash") if current else None,
            "failed_checks": sorted(set(failed)),
        }
        result_hash = stable_hash(result_payload)
        report = {
            "id": f"reasoning.assessment_check.{result_hash[:16]}",
            "identity_hash": result_hash,
            "read_only": True,
            "assessment": {
                "id": saved.get("id"),
                "identity_hash": saved.get("identity_hash"),
            },
            "current_assessment": self._ref(current) if current else None,
            "checks": {
                "immutable_identity": "valid" if identity_valid else "tampered",
                "current_state": "exact_match" if current_matches else "drifted_or_unverifiable",
            },
            "result": {
                "valid": not failed,
                "invalidated": bool(failed),
                "failed_checks": sorted(set(failed)),
                "error": error,
            },
            "authority": self._authority(),
            "limitations": [
                "The check validates exact reproducibility; it does not approve Assessment conclusions.",
                "Policies and metadata used by the saved Assessment must be supplied again exactly.",
            ],
        }
        return build_check_report(self.root, report, generated_at)

    def _check_versions(self, versions: list[dict], generated_at: str | None) -> list[dict]:
        engine = ContextVersionEngine(self.root, self.adoption_profile)
        checks = []
        for version in versions:
            check = engine.check_version(version, generated_at=generated_at)
            if check["result"]["immutable_identity"] != "valid":
                raise ValueError("Contextual Assessment rejects a tampered Context Version.")
            checks.append(check)
        return checks

    def _check_work_ownership(self, resolution: dict | None, generated_at: str | None) -> dict | None:
        if resolution is None:
            return None
        check = WorkOwnershipResolver(self.root, self.adoption_profile).check_resolution(
            resolution, generated_at=generated_at
        )
        if check["checks"]["immutable_identity"] != "valid":
            raise ValueError("Contextual Assessment rejects a tampered Work Ownership Resolution.")
        return check

    def _reason(
        self,
        health: dict,
        memory: dict,
        version_checks: list[dict],
        structured_reasoning: dict,
        work_ownership_resolution: dict | None,
        ownership_check: dict | None,
        *,
        has_structured_claims: bool,
    ) -> dict:
        health_ref = self._ref(health)["id"]
        observations = list(structured_reasoning["observations"])
        interpretations = list(structured_reasoning["interpretations"])
        prior_art = []
        context_changes = []
        contradictions = list(structured_reasoning["contradictions"])
        hypotheses = []
        recommendations = []
        unknowns = list(structured_reasoning["unknowns"])
        required_decisions = []
        additional_evidence = []

        observations.append(
            assertion(
                "observation",
                f"Current Context Health is {health['summary']['status']} across {health['summary']['signal_count']} structured signals.",
                [health_ref],
                epistemic_support="observed",
                support_state="direct",
            )
        )
        for dimension_id, value in sorted(health["dimensions"].items()):
            observations.append(
                assertion(
                    "observation",
                    f"{value['title']} is {value['status']}.",
                    [signal["id"] for signal in value["signals"]],
                    epistemic_support="observed",
                    support_state="direct",
                )
            )

        selected = memory["items"]
        if selected:
            for item in selected:
                prior_art.append(
                    assertion(
                        "prior_art",
                        f"{item['title']} is authorized prior art for consideration; current applicability remains {item['applicability']['status']}.",
                        [item["memory_id"], item["provenance"]["path"]],
                        epistemic_support="derived",
                        support_state="bounded",
                    )
                )
            interpretations.append(
                assertion(
                    "interpretation",
                    f"{len(selected)} policy-authorized Memory item(s) can inform the Mission, but Retrieval grants no current authority.",
                    [memory["id"]],
                    epistemic_support="derived",
                    support_state="bounded",
                )
            )
        elif memory["summary"]["relevant_candidate_count"]:
            unknowns.append(
                assertion(
                    "unknown",
                    "Relevant prior art exists, but no candidate is currently visible under the supplied policy and authority context.",
                    [memory["id"], "memory.summary.policy_outcomes"],
                    epistemic_support="unknown",
                    support_state="policy_limited",
                )
            )
            required_decisions.append(
                assertion(
                    "required_decision",
                    "An accountable human policy owner must define or authorize the Memory access context before restricted prior art can participate.",
                    [memory["id"]],
                    epistemic_support="derived",
                    support_state="required",
                    authority_required="memory_policy_owner",
                )
            )

        for check in version_checks:
            result = check["result"]
            ref = [check["version"]["id"]]
            if result["current_applicability"] == "superseded_or_drifted":
                context_changes.append(
                    assertion(
                        "context_change",
                        "A historically valid Context Version differs from current governed source state.",
                        ref,
                        epistemic_support="observed",
                        support_state=result["historical_verification"],
                    )
                )
            elif result["current_applicability"] == "unknown":
                unknowns.append(
                    assertion(
                        "unknown",
                        "Current applicability of a supplied historical Context Version is unknown.",
                        ref,
                        epistemic_support="unknown",
                        support_state=result["historical_verification"],
                    )
                )

        if work_ownership_resolution and ownership_check:
            ownership_ref = [work_ownership_resolution["id"]]
            disposition = work_ownership_resolution["result"]["disposition"]
            if ownership_check["result"]["reanchor_required"]:
                context_changes.append(
                    assertion(
                        "context_change",
                        "Material work-ownership context changed after resolution; consequential recommendation requires re-anchor.",
                        ownership_ref + ownership_check["result"]["failed_checks"],
                        epistemic_support="observed",
                        support_state="reanchor_required",
                    )
                )
                additional_evidence.append(
                    assertion(
                        "additional_evidence",
                        "Refresh only the materially bound Goal, Mission, ownership, lifecycle, and coverage evidence before qualification.",
                        ownership_ref,
                        epistemic_support="derived",
                        support_state="material_currentness_failed",
                    )
                )
            elif disposition == "QUALIFY_NEW_WORK":
                recommendations.append(
                    assertion(
                        "recommendation",
                        "Complete materially current ownership coverage found no current owner; normal Goal qualification is eligible.",
                        ownership_ref,
                        epistemic_support="derived",
                        support_state="eligible_not_authorized",
                        authority_required="human_goal_qualification",
                    )
                )
            elif disposition == "OWNERSHIP_CONFLICT":
                required_decisions.append(
                    assertion(
                        "required_decision",
                        "Current work ownership is conflicting; an accountable human must resolve ownership before parallel work is proposed.",
                        ownership_ref,
                        epistemic_support="derived",
                        support_state="ownership_conflict",
                        authority_required="work_owner_or_mission_owner",
                    )
                )
            elif disposition == "OWNERSHIP_UNKNOWN":
                additional_evidence.append(
                    assertion(
                        "additional_evidence",
                        "Current ownership remains unknown; complete the governed ownership coverage before proposing new work.",
                        ownership_ref,
                        epistemic_support="unknown",
                        support_state="ownership_unknown",
                    )
                )
            elif disposition == "AWAIT_HUMAN_DECISION":
                required_decisions.append(
                    assertion(
                        "required_decision",
                        "Existing work owns this need and is awaiting a human decision; do not create parallel work.",
                        ownership_ref,
                        epistemic_support="derived",
                        support_state="existing_work_awaits_human",
                        authority_required="existing_work_decision_owner",
                    )
                )
            elif disposition == "AWAIT_EVIDENCE":
                additional_evidence.append(
                    assertion(
                        "additional_evidence",
                        "Existing work owns this need and is awaiting evidence; reassess after its return condition is met.",
                        ownership_ref,
                        epistemic_support="derived",
                        support_state="existing_work_awaits_evidence",
                    )
                )
            else:
                interpretations.append(
                    assertion(
                        "interpretation",
                        f"Existing governed work owns this need with disposition {disposition}; no parallel Goal or Mission should be proposed.",
                        ownership_ref,
                        epistemic_support="derived",
                        support_state="existing_work_owns_need",
                    )
                )

        for dimension in health["dimensions"].values():
            for signal in dimension["signals"]:
                if signal["status"] in {"attention", "blocked"}:
                    interpretations.append(
                        assertion(
                            "interpretation",
                            signal["message"],
                            [signal["id"], *signal["evidence_refs"]],
                            epistemic_support="derived",
                            support_state=signal["status"],
                        )
                    )
                elif signal["status"] == "unknown":
                    unknowns.append(
                        assertion(
                            "unknown",
                            signal["message"],
                            [signal["id"], *signal["evidence_refs"]],
                            epistemic_support="unknown",
                            support_state="unmeasured",
                        )
                    )

        for candidate in health["context_update_candidates"]:
            candidate_refs = candidate.get("source_signal_refs", candidate.get("evidence_refs", []))
            recommendations.append(
                assertion(
                    "recommendation",
                    candidate["title"],
                    [candidate["id"], *candidate_refs],
                    epistemic_support="derived",
                    support_state="suggested",
                    authority_required="human_review",
                )
            )

        if not contradictions and not has_structured_claims:
            additional_evidence.append(
                assertion(
                    "additional_evidence",
                    "No structured contradiction was proven; semantic conflict analysis requires exact claim-level evidence.",
                    [health_ref, memory["id"]],
                    epistemic_support="unknown",
                    support_state="not_tested",
                )
            )
        if not version_checks:
            additional_evidence.append(
                assertion(
                    "additional_evidence",
                    "No exact Context Version was supplied, so historical-versus-current context change cannot be assessed.",
                    [memory["id"]],
                    epistemic_support="unknown",
                    support_state="missing",
                )
            )
        if memory["summary"]["selected_count"] == 0:
            hypotheses.append(
                assertion(
                    "hypothesis",
                    "Authorized Organizational Memory may change the assessment if policy-visible prior art becomes available.",
                    [memory["id"]],
                    epistemic_support="inferred",
                    support_state="untested",
                    strategic_belief="hypothesis",
                )
            )

        return {
            "observations": observations,
            "prior_art": prior_art,
            "context_changes": context_changes,
            "contradictions": contradictions,
            "interpretations": interpretations,
            "hypotheses": hypotheses,
            "recommendations": recommendations,
            "unknowns": unknowns,
            "required_decisions": required_decisions,
            "additional_evidence": additional_evidence,
        }

    @staticmethod
    def _status(health: dict, reasoning: dict) -> str:
        if health["summary"]["blocking_count"]:
            return "blocked"
        if reasoning["required_decisions"] or reasoning["unknowns"] or health["summary"]["attention_count"]:
            return "attention"
        return "ready"

    @staticmethod
    def _consequential_gate(resolution: dict | None, check: dict | None) -> dict:
        if resolution is None or check is None:
            return {
                "status": "not_evaluated",
                "eligible_for_goal_qualification": False,
                "parallel_goal_or_mission_authorized": False,
                "reanchor_required": False,
                "reason": "No Work Ownership Resolution was supplied; no ownership claim or new-work qualification is made.",
            }
        disposition = resolution["result"]["disposition"]
        if check["result"]["reanchor_required"]:
            status = "reanchor_required"
        elif disposition == "QUALIFY_NEW_WORK":
            status = "eligible_for_goal_qualification"
        elif disposition == "OWNERSHIP_CONFLICT":
            status = "withheld_ownership_conflict"
        elif disposition == "OWNERSHIP_UNKNOWN":
            status = "withheld_ownership_unknown"
        else:
            status = "withheld_existing_ownership"
        return {
            "status": status,
            "resolution_id": resolution["id"],
            "resolution_hash": resolution["identity_hash"],
            "disposition": disposition,
            "materially_current": check["result"]["materially_current"],
            "eligible_for_goal_qualification": status == "eligible_for_goal_qualification",
            "parallel_goal_or_mission_authorized": False,
            "reanchor_required": check["result"]["reanchor_required"],
            "failed_checks": check["result"]["failed_checks"],
        }

    @staticmethod
    def _ref(report: dict) -> dict:
        identity_payload = {key: value for key, value in report.items() if key not in {"generated_at", "root"}}
        identity_hash = report.get("identity_hash") or stable_hash(identity_payload)
        report_id = report.get("id") or f"{report['schema'].split('/', 1)[0].replace('contextos.', '')}.{identity_hash[:16]}"
        return {"schema": report["schema"], "id": report_id, "identity_hash": identity_hash}

    @staticmethod
    def _authority() -> dict:
        return {
            "level": "L1_suggest",
            "may_observe": True,
            "may_interpret": True,
            "may_form_hypotheses": True,
            "may_recommend": True,
            "may_decide": False,
            "may_approve": False,
            "may_execute": False,
            "may_mutate_canonical_context": False,
            "human_decision_required_for_consequential_transition": True,
        }

    @classmethod
    def _identity_payload(
        cls,
        query: dict,
        bindings: dict,
        reasoning: dict,
        consequential_recommendation_gate: dict | None = None,
    ) -> dict:
        payload = {
            "query": query,
            "bindings": bindings,
            "reasoning": reasoning,
            "authority": cls._authority(),
        }
        if consequential_recommendation_gate is not None:
            payload["consequential_recommendation_gate"] = consequential_recommendation_gate
        return payload
