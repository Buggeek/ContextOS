from __future__ import annotations

from collections import defaultdict, deque

from .assessment_engine import EPISTEMIC_SUPPORT, assertion, stable_hash


SCHEMA = "contextos.reasoning.evidence_set/1"
IMPACT_RELATIONSHIPS = {"affects", "blocks", "constrains", "depends_on", "enables", "supersedes"}


def normalize_evidence_set(value: dict | None) -> dict:
    if value is None:
        payload = {"schema": SCHEMA, "claims": [], "relationships": [], "limitations": []}
    elif not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError(f"Structured reasoning evidence must use {SCHEMA}.")
    else:
        claims = [_claim(item) for item in value.get("claims", [])]
        relationships = [_relationship(item) for item in value.get("relationships", [])]
        _require_unique_ids(claims, "claim")
        _require_unique_ids(relationships, "relationship")
        payload = {
            "schema": SCHEMA,
            "claims": sorted(claims, key=lambda item: item["id"]),
            "relationships": sorted(relationships, key=lambda item: item["id"]),
            "limitations": sorted(set(value.get("limitations", []))),
        }
    identity_payload = {key: payload[key] for key in ("schema", "claims", "relationships", "limitations")}
    identity_hash = stable_hash(identity_payload)
    payload["id"] = f"reasoning.evidence_set.{identity_hash[:16]}"
    payload["identity_hash"] = identity_hash
    payload["read_only"] = True
    payload["canonical"] = False
    return payload


def derive_reasoning(evidence_set: dict, focus_entities: list[str] | tuple[str, ...]) -> dict:
    observations = []
    contradictions = []
    impacts = []
    unknowns = []

    for claim in evidence_set["claims"]:
        observations.append(
            assertion(
                "observation",
                f"Explicit claim: {claim['subject']} {claim['predicate']} {display_value(claim['value'])}.",
                [claim["id"], *claim["source_refs"]],
                epistemic_support=claim["epistemic_support"],
                support_state="explicit_claim",
                governance_lifecycle=claim["governance_lifecycle"],
                strategic_belief=claim["strategic_belief"],
            )
        )

    grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for claim in evidence_set["claims"]:
        temporal_key = stable_hash(claim["temporal_basis"])
        grouped[(claim["subject"], claim["predicate"], claim["scope"], temporal_key)].append(claim)
    for key, claims in sorted(grouped.items()):
        values = {stable_hash(item["value"]) for item in claims}
        if len(claims) > 1 and len(values) > 1:
            subject, predicate, scope, _ = key
            refs = [ref for item in claims for ref in [item["id"], *item["source_refs"]]]
            contradictions.append(
                assertion(
                    "contradiction",
                    f"Explicit comparable claims disagree for {subject} / {predicate} in scope {scope}.",
                    refs,
                    epistemic_support="derived",
                    support_state="explicit_value_conflict",
                )
            )

    paths = relationship_paths(evidence_set["relationships"], focus_entities, max_depth=3)
    for path in paths:
        relation_text = " -> ".join(
            f"{edge['source']} --{edge['relationship']}--> {edge['target']}" for edge in path
        )
        refs = [ref for edge in path for ref in [edge["id"], *edge["source_refs"]]]
        if len(path) == 1:
            statement = f"Explicit relationship indicates impact on {path[-1]['target']}: {relation_text}."
            support_state = "direct_relationship"
        else:
            statement = f"Explicit indirect relationship path indicates impact on {path[-1]['target']}: {relation_text}."
            support_state = f"bounded_path_{len(path)}_hops"
        impacts.append(
            assertion(
                "interpretation",
                statement,
                refs,
                epistemic_support="derived",
                support_state=support_state,
            )
        )

    if evidence_set["claims"] and not contradictions:
        unknowns.append(
            assertion(
                "unknown",
                "No contradiction is proven among comparable explicit claims; unstructured or non-comparable claims were not semantically reconciled.",
                [evidence_set["id"]],
                epistemic_support="unknown",
                support_state="bounded_comparison_only",
            )
        )
    if focus_entities and not paths:
        unknowns.append(
            assertion(
                "unknown",
                "No bounded impact path is supported from the supplied focus entities.",
                [evidence_set["id"]],
                epistemic_support="unknown",
                support_state="no_explicit_path",
            )
        )
    return {
        "observations": observations,
        "contradictions": contradictions,
        "interpretations": impacts,
        "unknowns": unknowns,
    }


def relationship_paths(relationships: list[dict], starts: list[str] | tuple[str, ...], *, max_depth: int) -> list[list[dict]]:
    adjacency: dict[str, list[dict]] = defaultdict(list)
    for edge in relationships:
        if edge["relationship"] in IMPACT_RELATIONSHIPS:
            adjacency[edge["source"]].append(edge)
    for edges in adjacency.values():
        edges.sort(key=lambda edge: edge["id"])

    results = []
    for start in sorted(set(starts)):
        queue = deque([(start, [], {start})])
        while queue:
            node, path, visited = queue.popleft()
            if len(path) >= max_depth:
                continue
            for edge in adjacency.get(node, []):
                if edge["target"] in visited:
                    continue
                next_path = [*path, edge]
                results.append(next_path)
                queue.append((edge["target"], next_path, {*visited, edge["target"]}))
    return results


def _claim(value: dict) -> dict:
    required = ("id", "subject", "predicate", "value", "source_refs")
    missing = [key for key in required if key not in value or value[key] in (None, "", [])]
    if missing:
        raise ValueError(f"Structured claim is missing: {', '.join(missing)}")
    support = value.get("epistemic_support", "unknown")
    if support not in EPISTEMIC_SUPPORT:
        raise ValueError(f"Unsupported claim epistemic support: {support}")
    return {
        "id": str(value["id"]),
        "subject": str(value["subject"]),
        "predicate": str(value["predicate"]),
        "value": value["value"],
        "scope": str(value.get("scope", "unspecified")),
        "epistemic_support": support,
        "governance_lifecycle": str(value.get("governance_lifecycle", "suggested")),
        "strategic_belief": value.get("strategic_belief"),
        "temporal_basis": value.get("temporal_basis"),
        "authority_status": str(value.get("authority_status", "unknown")),
        "source_refs": sorted(set(str(ref) for ref in value["source_refs"])),
    }


def _relationship(value: dict) -> dict:
    required = ("id", "source", "relationship", "target", "source_refs")
    missing = [key for key in required if key not in value or value[key] in (None, "", [])]
    if missing:
        raise ValueError(f"Structured relationship is missing: {', '.join(missing)}")
    support = value.get("epistemic_support", "unknown")
    if support not in EPISTEMIC_SUPPORT:
        raise ValueError(f"Unsupported relationship epistemic support: {support}")
    return {
        "id": str(value["id"]),
        "source": str(value["source"]),
        "relationship": str(value["relationship"]),
        "target": str(value["target"]),
        "epistemic_support": support,
        "governance_lifecycle": str(value.get("governance_lifecycle", "suggested")),
        "temporal_basis": value.get("temporal_basis"),
        "authority_status": str(value.get("authority_status", "unknown")),
        "source_refs": sorted(set(str(ref) for ref in value["source_refs"])),
    }


def display_value(value: object) -> str:
    if isinstance(value, str):
        return value
    return str(value).lower() if isinstance(value, bool) else str(value)


def _require_unique_ids(items: list[dict], kind: str) -> None:
    ids = [item["id"] for item in items]
    duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    if duplicates:
        raise ValueError(f"Structured {kind} ids must be unique: {', '.join(duplicates)}")
