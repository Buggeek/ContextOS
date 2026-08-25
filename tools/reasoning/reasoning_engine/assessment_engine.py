from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from .report_builder import build_report


TOOLS_ROOT = Path(__file__).resolve().parents[2]
for runtime in ("activation", "health", "memory"):
    path = TOOLS_ROOT / runtime
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from health_engine.health_engine import ContextHealthEngine  # noqa: E402
from memory_engine import ContextVersionEngine, MemoryRetrievalEngine  # noqa: E402


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

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

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
        memory_limit: int = 12,
        evaluation_time: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if not goal or not goal.strip():
            raise ValueError("Contextual Assessment requires a goal.")
        if not consumer or not consumer.strip():
            raise ValueError("Contextual Assessment requires a consumer.")

        versions = list(context_versions)
        version_checks = self._check_versions(versions, generated_at)
        health = ContextHealthEngine(self.root).run(
            mission_use_evidence=mission_use_evidence,
            generated_at=generated_at,
        )
        memory = MemoryRetrievalEngine(self.root).run(
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
        reasoning = self._reason(health, memory, version_checks)
        all_assertions = [item for values in reasoning.values() for item in values]
        counts = Counter(item["type"] for item in all_assertions)
        status = self._status(health, reasoning)
        query = {
            "goal": goal.strip(),
            "mission_id": mission_id,
            "consumer": consumer.strip(),
            "question": (question or "").strip() or None,
            "purpose": (purpose or "").strip() or None,
            "organizational_mode": organizational_mode,
            "actor_roles": sorted(set(actor_roles)),
            "authority_scope": authority_scope,
        }
        bindings = {
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
        }
        identity_payload = {
            "query": query,
            "bindings": bindings,
            "reasoning": reasoning,
            "authority": self._authority(),
        }
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
                "context_version_checks": version_checks,
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
                    "The Activation Package, Health Report, Memory Retrieval, or Context Version evidence changes.",
                    "A source, policy, retention state, temporal basis, or permission bound to an input changes.",
                    "A saved assessment identity no longer matches its exact bound evidence.",
                ],
            },
            "limitations": [
                "Assertions are deterministic interpretations of structured Runtime evidence, not free-form semantic truth.",
                "Missing or policy-withheld memory remains unknown and is not reconstructed.",
                "No causal usefulness, semantic historical applicability, or decision authority is inferred.",
                "GraphRAG, embeddings, vector search, broad RAG, and autonomous execution are not used.",
            ],
        }
        return build_report(self.root, report, generated_at)

    def _check_versions(self, versions: list[dict], generated_at: str | None) -> list[dict]:
        engine = ContextVersionEngine(self.root)
        checks = []
        for version in versions:
            check = engine.check_version(version, generated_at=generated_at)
            if check["result"]["immutable_identity"] != "valid":
                raise ValueError("Contextual Assessment rejects a tampered Context Version.")
            checks.append(check)
        return checks

    def _reason(self, health: dict, memory: dict, version_checks: list[dict]) -> dict:
        health_ref = self._ref(health)["id"]
        observations = []
        interpretations = []
        prior_art = []
        context_changes = []
        contradictions = []
        hypotheses = []
        recommendations = []
        unknowns = []
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

        if not contradictions:
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
