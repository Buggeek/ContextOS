"""Fold permitted observations from existing anchor/last records; no new store."""
from adoption_engine.profile import stable_hash
from review_evidence import citation_problem, governing_constraints, same_restriction


def work_binding(config, profile_hash):
    # Routing identity only: no observed restriction, protected locator or count.
    return stable_hash({"target": config["target_id"], "root": config["source"]["root"],
                        "repository": config["source"].get("repository"), "profile": profile_hash,
                        "front": config["intent"], "scope": config.get("proposal", {}).get("scope")})


def observation_payload(item):
    return {k: item[k] for k in ("id", "text", "citations", "checked_by", "check_scope") if k in item}


def observation_hash(item):
    return stable_hash(observation_payload(item))


def preserves(old, new):
    """Literal coverage, not semantic equivalence or authority to replace a rule.

    A refreshed fingerprint or additive clarification can preserve an observed
    restriction. A reused id with different text/quotes cannot silently replace it.
    """
    refs = lambda item: {(r.get("path"), r.get("quote")) for r in item.get("citations", [])}
    return (same_restriction(old, new) and bool(old.get("text"))
            and old["text"] in new.get("text", "") and refs(old) <= refs(new))


def reconcile(current, previous, review, corpus, visible, history_gap=False, anchor_items=()):
    """One state per identity; recheck documentary dispositions every return."""
    known = []
    for item in [*previous, *current]:
        if item.get("missing_evidence") == "observation_history_missing_or_altered":
            continue  # sticky history_gap is carried separately, not a hidden identity
        item = observation_payload(item)
        position = next((i for i, old in enumerate(known) if preserves(old, item)), None)
        if position is None:
            if item or not any(not old for old in known):
                known.append(item)
        else:
            known[position] = item
    observations, active, restricted, covered = [], [], False, True
    for item in known:
        checked = governing_constraints([item], corpus, visible)[0]
        if not item or checked["missing_evidence"] == "evidence_not_visible":
            restricted = True
            covered = covered and bool(item) and any(observation_payload(old) == item for old in anchor_items)
            continue
        supplied = any(preserves(item, candidate) for candidate in current)
        disposition, evidence = ("current_input" if supplied else "pending"), None
        if not supplied and review.get("fit") == "documented_human_exception; authenticity_not_verified":
            decision = review["decision"]
            for resolution in decision.get("observation_dispositions", []):
                refs = review.get("judgement", {}).get("observation_refs", [])
                covers = all(ref in refs for ref in item.get("citations", []))
                state = resolution.get("disposition")
                # A terminal decision settles this exact recorded observation;
                # it does not assert its old quotation is still current truth.
                # The decision/authority themselves were checked against current
                # sources, scope and time. Confirmation still needs current support.
                supported = state in {"rejected", "not_applicable", "superseded"} or not citation_problem(item.get("citations"), corpus, visible)
                if (resolution.get("observation_hash") == observation_hash(item) and covers
                        and supported
                        and resolution.get("rationale") and state in {"confirmed", "rejected", "not_applicable", "superseded"}
                        and (state != "superseded" or any(c.get("id") == resolution.get("superseded_by") for c in current))):
                    disposition = state
                    evidence = {"human_owner": decision["human_owner"], "scope": decision["scope"],
                                "valid_until": decision["valid_until"], "rationale": resolution["rationale"],
                                "authority": "documentary_only; authenticity_not_verified"}
                    break
        if disposition == "pending":
            checked.update(status="unverifiable", missing_evidence="later_observation_unresolved",
                           limitation="dependent_proposal_not_sufficient")
        if item.get("id") and sum(c.get("id") == item["id"] for c in current) > 1:
            checked.update(status="unverifiable", missing_evidence="duplicate_restriction_identity",
                           limitation="dependent_proposal_not_sufficient")
        observations.append({**checked, "disposition": disposition, "resolution_evidence": evidence})
        if disposition not in {"rejected", "not_applicable", "superseded"}:
            active.append(checked)
    if restricted:
        # Exactly one generic notice, never protected identities or cardinality.
        opaque = {"status": "unverifiable", "missing_evidence": "evidence_not_visible",
                  "limitation": "dependent_proposal_not_sufficient"}
        observations.append(opaque)
        active.append(opaque)
    if history_gap:
        gap = {"status": "unverifiable", "missing_evidence": "observation_history_missing_or_altered",
               "limitation": "dependent_proposal_not_sufficient"}
        observations.append(gap)
        active.append(gap)
    return observations, active, restricted, bool(restricted and covered)
