from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from .continuity_engine import OrganizationalMemoryEngine, stable_hash
from .retrieval_report_builder import CHECK_SCHEMA, build_report, generated_timestamp
from .retention_resolution_engine import RetentionResolutionEngine


TOOLS_ROOT = Path(__file__).resolve().parents[2]
ACTIVATION_ROOT = TOOLS_ROOT / "activation"
if str(ACTIVATION_ROOT) not in sys.path:
    sys.path.insert(0, str(ACTIVATION_ROOT))

from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402


TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{2,}")
STOP_WORDS = {
    "about", "against", "allow", "and", "answer", "context", "contextos", "current", "does", "for", "from",
    "explicitly", "goal", "inform", "into", "mission", "must", "now", "organizational", "remain", "remains",
    "result", "should", "that", "the", "this", "was", "what", "when", "where", "which", "with", "without",
}
FORM_PRIORITY = {
    "decision": 6,
    "learning": 5,
    "context_state": 4,
    "outcome": 4,
    "evidence": 3,
    "inbox": 3,
    "mission": 2,
    "pattern_candidate": 1,
}
RETENTION_FORM = {"inbox": "evolution_inbox", "pattern_candidate": "learning"}


def normalize_token(token: str) -> str:
    aliases = {
        "retrieval": "retrieve",
        "retrieved": "retrieve",
        "retrieving": "retrieve",
        "memories": "memory",
        "decisions": "decision",
        "outcomes": "outcome",
        "learnings": "learning",
        "historical": "history",
        "history": "history",
        "superseded": "supersession",
    }
    if token in aliases:
        return aliases[token]
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith("s") and len(token) > 4 and not token.endswith("ss"):
        return token[:-1]
    return token


def tokens(value: str) -> set[str]:
    return {
        normalize_token(token)
        for token in TOKEN_PATTERN.findall(value.lower())
        if token not in STOP_WORDS and not token.isdigit()
    }


def candidate_records(continuity: dict) -> list[dict]:
    records = []
    source_hashes = {item["path"]: item["source_hash"] for item in continuity["sources"]}
    for form, entries in continuity["memory_forms"].items():
        for entry in entries:
            records.append(
                {
                    "candidate_id": entry["id"],
                    "memory_form": form,
                    "title": entry.get("title") or f"{form.replace('_', ' ').title()} from {entry.get('mission_id', 'unknown')}",
                    "summary": entry.get("summary") or entry.get("title") or "No source summary is available.",
                    "mission_id": entry.get("mission_id"),
                    "release": entry.get("release"),
                    "applicability": entry.get("applicability", "unknown"),
                    "temporal": entry.get("temporal", {}),
                    "truth": entry.get("truth", {}),
                    "source": entry["source"],
                    "retention_class": entry.get("retention_class"),
                    "supersession": None,
                }
            )
    for item in continuity["inbox_memory"]:
        records.append(
            {
                "candidate_id": f"memory.inbox.{item['id'].lower()}",
                "memory_form": "inbox",
                "title": f"{item['id']} - {item['category']}",
                "summary": f"{item['summary']} Disposition: {item['disposition']}",
                "mission_id": item.get("source_mission"),
                "release": None,
                "applicability": "superseded" if item["status"] == "superseded" else "unresolved",
                "temporal": {"valid_from": None, "valid_to": None, "observed_at": None, "ceased_current_at": None},
                "truth": item["truth"],
                "source": item["source"],
                "retention_class": "evolution_inbox_record",
                "supersession": item["disposition"] if item["status"] == "superseded" else None,
            }
        )
    for item in continuity["pattern_candidates"]:
        records.append(
            {
                "candidate_id": item["id"],
                "memory_form": "pattern_candidate",
                "title": item["title"],
                "summary": f"Recurring candidate supported by {item['support_count']} Mission Learning records.",
                "mission_id": None,
                "release": None,
                "applicability": "hypothesis",
                "temporal": {"valid_from": None, "valid_to": None, "observed_at": None, "ceased_current_at": None},
                "truth": item["truth"],
                "source": {
                    "path": item["evidence_refs"][0].split("#", 1)[0],
                    "source_hash": source_hashes.get(item["evidence_refs"][0].split("#", 1)[0]),
                    "section": "Learning",
                },
                "retention_class": "pattern_candidate",
                "supersession": None,
                "evidence_refs": item["evidence_refs"],
            }
        )
    return records


def temporal_status(candidate: dict) -> str:
    if candidate["supersession"]:
        return "superseded"
    if candidate["applicability"] in {"current", "historical", "unresolved"}:
        return candidate["applicability"]
    return "unknown"


def memory_metadata(candidate: dict, supplied: dict) -> dict:
    defaults = supplied.get("defaults", {}) if isinstance(supplied, dict) else {}
    items = supplied.get("items", {}) if isinstance(supplied, dict) else {}
    explicit = items.get(candidate["candidate_id"], {}) if isinstance(items, dict) else {}
    metadata = {**defaults, **explicit}
    return {
        **metadata,
        "id": candidate["candidate_id"],
        "form": RETENTION_FORM.get(candidate["memory_form"], candidate["memory_form"]),
        "sensitivity": metadata.get("sensitivity", "unknown"),
        "retention_state": metadata.get("retention_state", "unknown"),
        "metadata_visibility": metadata.get("metadata_visibility", "none"),
        "temporal": candidate.get("temporal", {}),
        "truth": candidate.get("truth", {}),
        "evidence_refs": candidate.get("evidence_refs", [candidate["source"]["path"]]),
        "provenance": candidate["source"],
    }


def safe_policy_evaluation(resolution: dict) -> dict:
    access = resolution["operation_results"]["access"]
    retrieval = resolution["operation_results"]["retrieval"]
    activation = resolution["operation_results"]["activation"]
    access_authority = resolution["authority"]["by_operation"]["access"]
    retrieval_authority = resolution["authority"]["by_operation"]["retrieval"]
    visibility = resolution["memory"]["metadata_visibility"]
    retrieval_outcome = retrieval["outcome"]
    reason_codes = list(retrieval["reason_codes"])
    if resolution["summary"]["policies_applied"] == 0 and retrieval_outcome != "prohibited":
        retrieval_outcome = "unknown"
        reason_codes.append("no_applicable_policy")
    protected = (
        visibility == "none"
        or access["outcome"] != "normal"
        or retrieval_outcome != "normal"
    )
    return {
        "memory": {
            "display_id": "<restricted>" if protected else resolution["memory"]["display_id"],
            "form": None if protected else resolution["memory"]["form"],
            "metadata_visibility": "none" if protected else visibility,
        },
        "access_outcome": access["outcome"],
        "retrieval_outcome": retrieval_outcome,
        "activation_outcome": activation["outcome"],
        "resolution_status": resolution["summary"]["status"],
        "reason_codes": sorted(set(reason_codes)),
        "required_roles": sorted(set(access["required_roles"] + retrieval["required_roles"])),
        "present_roles": sorted(set(access_authority["present_roles"] + retrieval_authority["present_roles"])),
        "missing_roles": sorted(set(access_authority["missing_roles"] + retrieval_authority["missing_roles"])),
        "authority_granted": False,
        "policies": [] if protected else resolution["policy_evaluation"]["applied"],
        "conflicts": (
            {"count": len(resolution["conflicts"]), "details_withheld": bool(resolution["conflicts"])}
            if protected
            else {"count": len(resolution["conflicts"]), "items": resolution["conflicts"]}
        ),
        "unresolved": (
            {"count": len(resolution["unresolved_requirements"]), "details_withheld": bool(resolution["unresolved_requirements"])}
            if protected
            else {"count": len(resolution["unresolved_requirements"]), "items": resolution["unresolved_requirements"]}
        ),
        "resolution_ref": (
            None
            if protected
            else {"id": resolution["id"], "identity_hash": resolution["identity_hash"]}
        ),
        "mutation_occurred": False,
    }


class MemoryRetrievalEngine:
    """Retrieve bounded historical prior art while preserving current Activation authority."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def run(
        self,
        *,
        goal: str,
        mission_id: str | None = None,
        question: str | None = None,
        consumer: str = "human",
        limit: int = 12,
        purpose: str | None = None,
        organizational_mode: str = "local",
        actor_roles: list[str] | tuple[str, ...] = (),
        authority_scope: str | None = None,
        retention_policies: list[dict] | None = None,
        memory_metadata_by_id: dict | None = None,
        evaluation_time: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if not goal or not goal.strip():
            raise ValueError("Memory retrieval requires a goal.")
        if not consumer or not consumer.strip():
            raise ValueError("Memory retrieval requires a consumer.")
        if limit < 1 or limit > 50:
            raise ValueError("Memory retrieval limit must be between 1 and 50.")

        goal = goal.strip()
        question = (question or "").strip()
        consumer = consumer.strip()
        purpose = (purpose or question or goal).strip()
        roles = sorted(set(actor_roles))
        policies = list(retention_policies or [])
        supplied_metadata = memory_metadata_by_id or {}
        evaluated_at = evaluation_time or generated_at or generated_timestamp()
        continuity = OrganizationalMemoryEngine(self.root).run(
            mission_id=mission_id,
            goal=f"{goal} {question}".strip(),
            generated_at=generated_at,
        )
        activation = ContextActivationPackageEngine(self.root).run(
            goal=goal,
            mission_id=mission_id,
            consumer=consumer,
            generated_at=generated_at,
        )
        query_terms = tokens(f"{goal} {question} {mission_id or ''}")
        candidates = candidate_records(continuity)
        relevant, relevance_exclusions = self._rank_relevant(candidates, query_terms, mission_id)
        selected, policy_evaluations, policy_exclusions, resolution_hashes = self._authorize_relevant(
            relevant,
            policies,
            supplied_metadata,
            consumer=consumer,
            actor_roles=roles,
            organizational_mode=organizational_mode,
            authority_scope=authority_scope,
            evaluation_time=evaluated_at,
            limit=limit,
            generated_at=generated_at,
        )
        policy_summary = {
            "policies_supplied": len(policies),
            "visible_policy_versions": [
                {"id": policy["id"], "version": policy["version"]}
                for policy in policies
                if policy.get("explanation_visibility", "id_only") != "none"
            ],
            "restricted_policy_count": sum(
                1 for policy in policies if policy.get("explanation_visibility", "id_only") == "none"
            ),
            "input_fingerprint": stable_hash({"policies": policies, "memory_metadata": supplied_metadata}),
            "resolution_fingerprint": stable_hash(resolution_hashes),
        }
        query = {
            "goal": goal,
            "mission_id": mission_id,
            "question": question,
            "consumer": consumer,
            "purpose": purpose,
            "requested_operation": "retrieval",
            "organizational_mode": organizational_mode,
            "actor_roles": roles,
            "authority_scope": authority_scope,
            "evaluation_time": evaluated_at,
            "limit": limit,
        }
        exclusions = {
            "items": policy_exclusions,
            "relevance": relevance_exclusions,
            "bounded": True,
            "protected_candidate_metadata_exposed": False,
        }
        identity_payload = {
            "query": query,
            "continuity_identity_hash": continuity["identity_hash"],
            "activation_identity_hash": activation["identity_hash"],
            "policy_context": policy_summary,
            "items": selected,
            "policy_evaluations": policy_evaluations,
            "exclusions": exclusions,
        }
        identity_hash = stable_hash(identity_payload)
        statuses = Counter(item["temporal_status"] for item in selected)
        report = {
            "id": f"memory.retrieval.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            "read_only": True,
            "derived_view": True,
            "query": query,
            "summary": {
                "selected_count": len(selected),
                "relevant_candidate_count": len(relevant),
                "excluded_count": len(candidates) - len(selected),
                "policy_outcomes": dict(Counter(item["retrieval_outcome"] for item in policy_evaluations)),
                "access_outcomes": dict(Counter(item["access_outcome"] for item in policy_evaluations)),
                "activation_outcomes": dict(Counter(item["activation_outcome"] for item in policy_evaluations)),
                "current_count": statuses["current"],
                "historical_count": statuses["historical"],
                "superseded_count": statuses["superseded"],
                "unresolved_count": statuses["unresolved"],
                "unknown_count": statuses["unknown"],
                "continuity_gap_count": len(continuity["continuity_gaps"]),
            },
            "bindings": {
                "memory_continuity": {
                    "schema": continuity["schema"],
                    "id": continuity["id"],
                    "identity_hash": continuity["identity_hash"],
                    "source_fingerprint": continuity["source_fingerprint"],
                },
                "activation_package": {
                    "schema": activation["schema"],
                    "id": activation["id"],
                    "identity_hash": activation["identity_hash"],
                    "source_fingerprint": activation["source_fingerprint"],
                },
                "retention_policy_context": policy_summary,
            },
            "activation_package": activation,
            "items": selected,
            "policy_evaluations": policy_evaluations,
            "exclusions": exclusions,
            "continuity_gaps": continuity["continuity_gaps"],
            "retention": continuity["retention"],
            "authority": {
                "current_governing_context": "embedded_activation_package",
                "retrieved_memory_role": "historical_and_continuity_prior_art_only",
                "retrieved_memory_may_override_canonical": False,
                "retrieved_memory_added_to_governing_context": False,
                "applicability_requires_consumer_judgment": True,
                "usefulness_inferred": False,
                "writes_allowed": False,
                "policy_evaluated_before_exposure": True,
            },
            "freshness": {
                "fresh_at_generation": activation["summary"]["activation_allowed"],
                "continuity_source_fingerprint": continuity["source_fingerprint"],
                "activation_source_fingerprint": activation["source_fingerprint"],
            },
            "invalidation": {
                "conditions": [
                    "The retrieval identity, Goal, Mission, question, consumer, or limit changes.",
                    "The bound Memory Continuity identity or source fingerprint changes.",
                    "The bound Activation Package becomes invalid or its selected canonical sources change.",
                    "Supersession, temporal, retention, permission, or evidence relationships change.",
                    "A supplied policy, memory metadata value, sensitivity, hold, actor role, purpose, authority scope, organizational mode, or evaluation time changes.",
                ]
            },
            "limitations": [
                "Selection uses deterministic structured term overlap and declared metadata, not semantic reasoning.",
                "A selected candidate is not proven applicable, authoritative, or useful.",
                "Semantic conflict with current canonical context remains unknown without governed interpretation.",
                "Missing history, temporal state, context versions, and retention policy remain explicit gaps.",
                "Relevant candidates are exposed only after explicit Retention Resolution; no-policy remains unknown.",
                "No GraphRAG, embeddings, vector database, Knowledge Engine, external service, agent, or mutation is used.",
            ],
        }
        return build_report(self.root, report, generated_at)

    def check_retrieval(
        self,
        report: dict,
        *,
        retention_policies: list[dict] | None = None,
        memory_metadata_by_id: dict | None = None,
        evaluation_time: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if report.get("schema") != "contextos.memory.retrieval_result/1":
            raise ValueError("Memory retrieval check requires contextos.memory.retrieval_result/1 input.")
        expected_hash = stable_hash(self._identity_payload(report))
        identity_valid = report.get("identity_hash") == expected_hash
        activation_check = ContextActivationPackageEngine(self.root).check_package(
            report.get("activation_package", {}), generated_at=generated_at
        )
        query = report.get("query", {})
        current = self.run(
            goal=query.get("goal", ""),
            mission_id=query.get("mission_id"),
            question=query.get("question"),
            consumer=query.get("consumer", ""),
            limit=query.get("limit", 12),
            purpose=query.get("purpose"),
            organizational_mode=query.get("organizational_mode", "local"),
            actor_roles=query.get("actor_roles", []),
            authority_scope=query.get("authority_scope"),
            retention_policies=retention_policies,
            memory_metadata_by_id=memory_metadata_by_id,
            evaluation_time=evaluation_time or query.get("evaluation_time"),
            generated_at=generated_at,
        )
        continuity_state_unchanged = (
            report.get("bindings", {}).get("memory_continuity", {}).get("identity_hash")
            == current["bindings"]["memory_continuity"]["identity_hash"]
        )
        selection_unchanged = report.get("identity_hash") == current["identity_hash"]
        policy_context_unchanged = (
            report.get("bindings", {}).get("retention_policy_context", {}).get("input_fingerprint")
            == current["bindings"]["retention_policy_context"]["input_fingerprint"]
        )
        temporal_basis_unchanged = query.get("evaluation_time") == current["query"]["evaluation_time"]
        failed = []
        if not identity_valid:
            failed.append("memory_retrieval_check.identity_hash_mismatch")
        if not activation_check["result"]["valid"]:
            failed.append("memory_retrieval_check.activation_package_invalid")
        if not continuity_state_unchanged:
            failed.append("memory_retrieval_check.continuity_state_changed")
        if not selection_unchanged:
            failed.append("memory_retrieval_check.selection_changed")
        if not policy_context_unchanged:
            failed.append("memory_retrieval_check.policy_context_changed")
        if not temporal_basis_unchanged:
            failed.append("memory_retrieval_check.temporal_basis_changed")
        valid = not failed
        return {
            "schema": CHECK_SCHEMA,
            "generated_at": generated_at or generated_timestamp(),
            "root": str(self.root),
            "read_only": True,
            "retrieval": {
                "id": report.get("id"),
                "identity_hash": report.get("identity_hash"),
                "query": report.get("query"),
            },
            "checks": {
                "identity_valid": identity_valid,
                "activation_package_valid": activation_check["result"]["valid"],
                "continuity_state_unchanged": continuity_state_unchanged,
                "selection_unchanged": selection_unchanged,
                "policy_context_unchanged": policy_context_unchanged,
                "temporal_basis_unchanged": temporal_basis_unchanged,
            },
            "activation_package_check": activation_check,
            "current": {
                "continuity_identity_hash": current["bindings"]["memory_continuity"]["identity_hash"],
                "retrieval_identity_hash": current["identity_hash"],
            },
            "result": {"valid": valid, "invalidated": not valid, "failed_checks": failed},
        }

    def _rank_relevant(
        self,
        candidates: list[dict],
        query_terms: set[str],
        mission_id: str | None,
    ) -> tuple[list[tuple[int, dict, list[str], list[str]]], dict]:
        scored = []
        excluded_reasons: Counter[str] = Counter()
        for candidate in candidates:
            if mission_id and candidate["mission_id"] == mission_id:
                excluded_reasons["active_mission_self_record_excluded"] += 1
                continue
            candidate_terms = tokens(
                f"{candidate['memory_form']} {candidate['title']} {candidate['summary']} "
                f"{candidate['mission_id'] or ''} {candidate['release'] or ''} {candidate['source']['path']} "
                f"{candidate['applicability']} {candidate['supersession'] or ''}"
            )
            matched = sorted(query_terms & candidate_terms)
            if not matched:
                excluded_reasons["no_explainable_term_overlap"] += 1
                continue
            relationship_signals = []
            score = len(matched) * 10 + FORM_PRIORITY[candidate["memory_form"]]
            if candidate["supersession"] and "supersession" in query_terms:
                relationship_signals.append("explicit_supersession_requested")
                score += 30
            if candidate["applicability"] == "unresolved" and "unresolved" in query_terms:
                relationship_signals.append("unresolved_state_requested")
                score += 15
            if mission_id and mission_id.lower() in f"{candidate['title']} {candidate['summary']}".lower():
                relationship_signals.append("explicit_mission_reference")
                score += 20
            scored.append((score, candidate, matched, relationship_signals))
        scored.sort(key=lambda value: (-value[0], value[1]["source"]["path"], value[1]["candidate_id"]))
        return scored, {
            "count": sum(excluded_reasons.values()),
            "reason_counts": dict(sorted(excluded_reasons.items())),
        }

    def _authorize_relevant(
        self,
        scored: list[tuple[int, dict, list[str], list[str]]],
        policies: list[dict],
        supplied_metadata: dict,
        *,
        consumer: str,
        actor_roles: list[str],
        organizational_mode: str,
        authority_scope: str | None,
        evaluation_time: str,
        limit: int,
        generated_at: str | None,
    ) -> tuple[list[dict], list[dict], list[dict], list[str]]:
        selected = []
        evaluations = []
        exclusions = []
        resolution_hashes = []
        per_source: Counter[str] = Counter()
        resolver = RetentionResolutionEngine(self.root)
        for score, candidate, matched, relationship_signals in scored:
            resolution = resolver.run(
                memory_metadata(candidate, supplied_metadata),
                policies,
                consumer=consumer,
                actor_roles=actor_roles,
                requested_operations=["access", "retrieval", "activation"],
                organizational_mode=organizational_mode,
                authority_scope=authority_scope,
                evaluation_time=evaluation_time,
                generated_at=generated_at,
            )
            resolution_hashes.append(resolution["identity_hash"])
            evaluation = safe_policy_evaluation(resolution)
            evaluations.append(evaluation)
            outcome = evaluation["retrieval_outcome"]
            access_outcome = evaluation["access_outcome"]
            visibility = evaluation["memory"]["metadata_visibility"]
            path = candidate["source"]["path"]
            reason = None
            if access_outcome != "normal":
                reason = f"access_{access_outcome}"
            elif outcome != "normal":
                reason = f"retention_{outcome}"
            elif visibility == "none":
                reason = "retrievable_but_not_visible"
            elif per_source[path] >= 2:
                reason = "source_diversity_limit"
            elif len(selected) >= limit:
                reason = "bounded_result_limit"
            if reason:
                exclusions.append(
                    {
                        "candidate": evaluation["memory"]["display_id"],
                        "memory_form": evaluation["memory"]["form"],
                        "reason": reason,
                        "access_outcome": access_outcome,
                        "retrieval_outcome": outcome,
                        "required_roles": evaluation["required_roles"],
                        "missing_roles": evaluation["missing_roles"],
                        "unresolved_count": evaluation["unresolved"]["count"],
                        "conflict_count": evaluation["conflicts"]["count"],
                    }
                )
                continue
            per_source[path] += 1
            visibility_full = visibility == "full"
            selected.append(
                {
                    "id": f"memory.retrieval.item.{stable_hash({'candidate': candidate['candidate_id'], 'matched': matched})[:16]}",
                    "memory_id": evaluation["memory"]["display_id"],
                    "memory_form": candidate["memory_form"],
                    "title": candidate["title"] if visibility_full else "<metadata-restricted>",
                    "summary": candidate["summary"] if visibility_full else None,
                    "mission_id": candidate["mission_id"] if visibility_full else None,
                    "release": candidate["release"] if visibility_full else None,
                    "temporal_status": temporal_status(candidate),
                    "temporal": candidate["temporal"] if visibility_full else {},
                    "applicability": {
                        "status": "candidate",
                        "source_state": candidate["applicability"] if visibility_full else "withheld",
                        "requires_human_interpretation": True,
                        "proven_useful": False,
                    },
                    "authority": {
                        "current_authority": "none_from_retrieval",
                        "canonical_context_governs": True,
                        "may_override_current_context": False,
                    },
                    "selection": {
                        "method": "bounded_structured_term_overlap",
                        "score": score,
                        "matched_terms": matched if visibility_full else [],
                        "form_priority": FORM_PRIORITY[candidate["memory_form"]],
                        "relationship_signals": relationship_signals if visibility_full else [],
                        "rationale": (
                            f"Matched {len(matched)} normalized Goal/Mission term(s) in the "
                            f"{candidate['memory_form'].replace('_', ' ')} record"
                            + (f" with structured relationship signal(s): {', '.join(relationship_signals)}." if relationship_signals else ".")
                            if visibility_full
                            else "Relevant candidate; selection details are restricted by policy."
                        ),
                    },
                    "retrieval_eligibility": evaluation,
                    "truth": candidate["truth"] if visibility_full else {},
                    "supersession": {
                        "status": ("explicit" if candidate["supersession"] else "not_observed") if visibility_full else "withheld",
                        "detail": candidate["supersession"] if visibility_full else None,
                        "absence_is_not_proof_of_current_validity": not bool(candidate["supersession"]),
                    },
                    "current_context_comparison": {
                        "status": ("historically_bounded" if candidate["supersession"] else "unknown") if visibility_full else "unknown",
                        "canonical_context_governs_on_conflict": True,
                        "semantic_conflict_inferred": False,
                    },
                    "provenance": candidate["source"] if visibility_full else None,
                    "evidence_refs": candidate.get("evidence_refs", [candidate["source"]["path"]]) if visibility_full else [],
                    "retention_class": candidate["retention_class"] if visibility_full else None,
                    "canonical": False,
                }
            )
        exclusions.sort(key=lambda item: (item["reason"], item["candidate"] or ""))
        return selected, evaluations, exclusions, resolution_hashes

    @staticmethod
    def _identity_payload(report: dict) -> dict:
        return {
            "query": report.get("query"),
            "continuity_identity_hash": report.get("bindings", {}).get("memory_continuity", {}).get("identity_hash"),
            "activation_identity_hash": report.get("bindings", {}).get("activation_package", {}).get("identity_hash"),
            "policy_context": report.get("bindings", {}).get("retention_policy_context"),
            "items": report.get("items", []),
            "policy_evaluations": report.get("policy_evaluations", []),
            "exclusions": report.get("exclusions", {}),
        }
