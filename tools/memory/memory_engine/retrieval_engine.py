from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

from .continuity_engine import OrganizationalMemoryEngine, stable_hash
from .retrieval_report_builder import CHECK_SCHEMA, build_report, generated_timestamp


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
        selected, exclusions = self._select(candidate_records(continuity), query_terms, mission_id, limit)
        identity_payload = {
            "query": {
                "goal": goal,
                "mission_id": mission_id,
                "question": question,
                "consumer": consumer,
                "limit": limit,
            },
            "continuity_identity_hash": continuity["identity_hash"],
            "activation_identity_hash": activation["identity_hash"],
            "selected": [
                {
                    "memory_id": item["memory_id"],
                    "matched_terms": item["selection"]["matched_terms"],
                    "relationship_signals": item["selection"]["relationship_signals"],
                    "score": item["selection"]["score"],
                }
                for item in selected
            ],
        }
        identity_hash = stable_hash(identity_payload)
        statuses = Counter(item["temporal_status"] for item in selected)
        report = {
            "id": f"memory.retrieval.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            "read_only": True,
            "derived_view": True,
            "query": identity_payload["query"],
            "summary": {
                "selected_count": len(selected),
                "excluded_count": len(exclusions),
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
            },
            "activation_package": activation,
            "items": selected,
            "exclusions": {"items": exclusions, "bounded": True},
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
                ]
            },
            "limitations": [
                "Selection uses deterministic structured term overlap and declared metadata, not semantic reasoning.",
                "A selected candidate is not proven applicable, authoritative, or useful.",
                "Semantic conflict with current canonical context remains unknown without governed interpretation.",
                "Missing history, temporal state, context versions, and retention policy remain explicit gaps.",
                "No GraphRAG, embeddings, vector database, Knowledge Engine, external service, agent, or mutation is used.",
            ],
        }
        return build_report(self.root, report, generated_at)

    def check_retrieval(self, report: dict, *, generated_at: str | None = None) -> dict:
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
            generated_at=generated_at,
        )
        continuity_state_unchanged = (
            report.get("bindings", {}).get("memory_continuity", {}).get("identity_hash")
            == current["bindings"]["memory_continuity"]["identity_hash"]
        )
        selection_unchanged = report.get("identity_hash") == current["identity_hash"]
        failed = []
        if not identity_valid:
            failed.append("memory_retrieval_check.identity_hash_mismatch")
        if not activation_check["result"]["valid"]:
            failed.append("memory_retrieval_check.activation_package_invalid")
        if not continuity_state_unchanged:
            failed.append("memory_retrieval_check.continuity_state_changed")
        if not selection_unchanged:
            failed.append("memory_retrieval_check.selection_changed")
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
            },
            "activation_package_check": activation_check,
            "current": {
                "continuity_identity_hash": current["bindings"]["memory_continuity"]["identity_hash"],
                "retrieval_identity_hash": current["identity_hash"],
            },
            "result": {"valid": valid, "invalidated": not valid, "failed_checks": failed},
        }

    def _select(
        self,
        candidates: list[dict],
        query_terms: set[str],
        mission_id: str | None,
        limit: int,
    ) -> tuple[list[dict], list[dict]]:
        scored = []
        exclusions = []
        for candidate in candidates:
            if mission_id and candidate["mission_id"] == mission_id:
                exclusions.append({"candidate_id": candidate["candidate_id"], "reason": "active_mission_self_record_excluded"})
                continue
            candidate_terms = tokens(
                f"{candidate['memory_form']} {candidate['title']} {candidate['summary']} "
                f"{candidate['mission_id'] or ''} {candidate['release'] or ''} {candidate['source']['path']} "
                f"{candidate['applicability']} {candidate['supersession'] or ''}"
            )
            matched = sorted(query_terms & candidate_terms)
            if not matched:
                exclusions.append({"candidate_id": candidate["candidate_id"], "reason": "no_explainable_term_overlap"})
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
        selected = []
        per_source: Counter[str] = Counter()
        for score, candidate, matched, relationship_signals in scored:
            path = candidate["source"]["path"]
            if per_source[path] >= 2:
                exclusions.append({"candidate_id": candidate["candidate_id"], "reason": "source_diversity_limit"})
                continue
            if len(selected) >= limit:
                exclusions.append({"candidate_id": candidate["candidate_id"], "reason": "bounded_result_limit"})
                continue
            per_source[path] += 1
            status = temporal_status(candidate)
            selected.append(
                {
                    "id": f"memory.retrieval.item.{stable_hash({'candidate': candidate['candidate_id'], 'matched': matched})[:16]}",
                    "memory_id": candidate["candidate_id"],
                    "memory_form": candidate["memory_form"],
                    "title": candidate["title"],
                    "summary": candidate["summary"],
                    "mission_id": candidate["mission_id"],
                    "release": candidate["release"],
                    "temporal_status": status,
                    "temporal": candidate["temporal"],
                    "applicability": {
                        "status": "candidate",
                        "source_state": candidate["applicability"],
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
                        "matched_terms": matched,
                        "form_priority": FORM_PRIORITY[candidate["memory_form"]],
                        "relationship_signals": relationship_signals,
                        "rationale": (
                            f"Matched {len(matched)} normalized Goal/Mission term(s) in the "
                            f"{candidate['memory_form'].replace('_', ' ')} record"
                            + (f" with structured relationship signal(s): {', '.join(relationship_signals)}." if relationship_signals else ".")
                        ),
                    },
                    "truth": candidate["truth"],
                    "supersession": {
                        "status": "explicit" if candidate["supersession"] else "not_observed",
                        "detail": candidate["supersession"],
                        "absence_is_not_proof_of_current_validity": not bool(candidate["supersession"]),
                    },
                    "current_context_comparison": {
                        "status": "historically_bounded" if candidate["supersession"] else "unknown",
                        "canonical_context_governs_on_conflict": True,
                        "semantic_conflict_inferred": False,
                    },
                    "provenance": candidate["source"],
                    "evidence_refs": candidate.get("evidence_refs", [candidate["source"]["path"]]),
                    "retention_class": candidate["retention_class"],
                    "canonical": False,
                }
            )
        exclusions.sort(key=lambda item: (item["reason"], item["candidate_id"]))
        return selected, exclusions

    @staticmethod
    def _identity_payload(report: dict) -> dict:
        return {
            "query": report.get("query"),
            "continuity_identity_hash": report.get("bindings", {}).get("memory_continuity", {}).get("identity_hash"),
            "activation_identity_hash": report.get("bindings", {}).get("activation_package", {}).get("identity_hash"),
            "selected": [
                {
                    "memory_id": item.get("memory_id"),
                    "matched_terms": item.get("selection", {}).get("matched_terms"),
                    "relationship_signals": item.get("selection", {}).get("relationship_signals"),
                    "score": item.get("selection", {}).get("score"),
                }
                for item in report.get("items", [])
            ],
        }
