"""Local presentation checks, reusing citation and stable-hash evidence bindings.

No authority is issued here. Documentary actor/decision declarations must come
from the existing canon selected by the operator; their authenticity and the
semantic judgement remain human/Codex responsibilities, not Runtime findings.
There is deliberately no new persisted Runtime schema or authentication system.
"""
import json
from datetime import datetime, timezone

from adoption_engine.profile import file_hash, safe_locator, stable_hash


def citation_problem(refs, corpus, allowed):
    if not refs:
        return "citation_missing"
    # Visibility has precedence across the ENTIRE set, including when an earlier
    # visible quote is invalid. No diagnostic may expose later protected refs.
    if any(ref.get("path") not in allowed for ref in refs):
        return "evidence_not_visible"
    for ref in refs:
        path = corpus / safe_locator(ref["path"])
        if not path.is_file():
            return "source_missing"
        if ref.get("source_hash") and ref["source_hash"] != file_hash(path):
            return "source_changed"
        if not ref.get("quote", "").strip() or ref["quote"] not in path.read_text():
            return "quote_not_found"
    return None


def governing_constraints(items, corpus, allowed):
    results = []
    for item in items:
        problem = citation_problem(item.get("citations"), corpus, allowed)
        visible = problem != "evidence_not_visible"
        results.append({
            **({k: item[k] for k in ("id", "text", "citations", "checked_by", "check_scope") if k in item} if visible else {}),
            "status": "unverifiable" if problem else "verified_citation",
            "missing_evidence": problem,
            "semantic_check": "operator_declared; not_runtime_verified" if visible and item.get("checked_by") else "not_checked",
            "limitation": "dependent_proposal_not_sufficient" if problem else "citation_is_not_semantic_fit",
        })
    return results


def same_restriction(old, new):
    """Identity is separate from revision. Legacy migration preserves old text.

    Adding an id to an unchanged legacy restriction is allowed; that input edit
    still invalidates the exact review binding. Omission is never an update.
    """
    if old.get("id"):
        return old["id"] == new.get("id")
    return bool(old.get("text")) and old["text"] == new.get("text")


def review_binding(config, corpus, allowed, profile_hash=None):
    """Operator calls only AFTER reviewing; run() never refreshes a verdict."""
    review = {k: v for k, v in config.get("review", {}).items() if k != "binding"}
    context_refs = [r for item in config.get("governing_decisions", []) for r in item.get("citations", [])]
    context_refs += review.get("constraint_refs", []) + review.get("authority_refs", []) + review.get("observation_refs", [])
    def hashes(refs):
        return {r["path"]: file_hash(corpus / safe_locator(r["path"]))
                if r.get("path") in allowed and (corpus / safe_locator(r["path"])).is_file() else None
                for r in refs if r.get("path") in allowed}
    context = {"restrictions": config.get("governing_decisions", []), "refs": context_refs,
               "sources": hashes(context_refs), "profile_hash": profile_hash,
               "target_id": config.get("target_id")}
    return {"proposal_hash": stable_hash(config.get("proposal")),
            "governing_context_hash": stable_hash(context),
            "review_hash": stable_hash(review),
            "decision_source_hashes": hashes(review.get("decision_refs", []))}


def cited_records(refs, corpus, allowed):
    """Read exact JSON quotations of existing documentary decisions, no NLP."""
    if citation_problem(refs, corpus, allowed):
        return []
    try:
        records = [json.loads(ref["quote"]) for ref in refs]
        return records if all(isinstance(r, dict) for r in records) else []
    except (ValueError, TypeError):
        return []


def current(record, now):
    try:
        start = datetime.fromisoformat(record["valid_from"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(record["valid_until"].replace("Z", "+00:00"))
        return start <= now < end
    except (KeyError, ValueError, TypeError):
        return False


def evaluate_review(config, corpus, allowed, constraints, profile_hash=None, authority_sources=None):
    proposal, review = config.get("proposal"), config.get("review", {})
    result = {"fit": "no_proposal_submitted", "issues": [], "execution_authorized": False,
              "authority_verification": "documentary_only; authenticity_not_verified",
              "semantic_verification": "not_performed_by_runtime"}
    if not proposal and not review:
        return result
    result["fit"] = "unverified_constraints"
    refs = [r for key in ("constraint_refs", "authority_refs", "decision_refs", "observation_refs") for r in review.get(key, [])]
    if any(r.get("path") not in allowed for r in refs):
        result["issues"] = ["review_evidence_not_visible; proposal_and_actor_details_withheld"]
        return result
    result.update(proposal=proposal, judgement={k: v for k, v in review.items() if k != "binding"})
    expected = review_binding(config, corpus, allowed, profile_hash)
    result["binding"] = {"current": expected, "reviewed": review.get("binding"), "valid": review.get("binding") == expected}
    issues = result["issues"]
    if not isinstance(proposal, dict) or any(not proposal.get(k) for k in ("id", "version", "content", "author", "scope")):
        issues.append("exact_proposal_content_version_author_scope_required")
    if not result["binding"]["valid"]:
        issues.append("proposal_context_or_review_changed; new_attributed_review_required")
    if not constraints or any(c["status"] == "unverifiable" for c in constraints):
        issues.append("governing_constraints_missing_or_unverifiable")
    if citation_problem(review.get("constraint_refs"), corpus, allowed):
        issues.append("constraint_citations_unverifiable")
    if not review.get("reviewed_by") or not review.get("rationale"):
        issues.append("attributed_semantic_judgement_required")
    if issues:
        return result
    same_author = proposal["author"] == review["reviewed_by"]
    result["review_relationship"] = "self_review" if same_author else "distinct_declared_actors; independence_not_authenticated"
    if same_author and review.get("independent_of_candidate") is True:
        issues.append("self_review_cannot_be_independent")
        return result
    if review.get("fit") == "conflict":
        result["fit"] = "requires_product_architecture_decision"
        return result
    if review.get("fit") == "compatible":
        result["fit"] = "operator_declares_compatible; product_acceptance_not_inferred"
        return result
    if review.get("fit") != "approved_exception":
        issues.append("semantic_judgement_unknown")
        return result
    # Existing authority must be separately cited, not a role within a proposal,
    # boolean flag, or the rule being excepted. This is documentary corroboration,
    # not verification that the named person authored/approved the record.
    authority = cited_records(review.get("authority_refs"), corpus, allowed)
    decisions = cited_records(review.get("decision_refs"), corpus, allowed)
    now = datetime.now(timezone.utc)  # fresh on EVERY return; never a saved timestamp
    result["authority_checked_at"] = now.isoformat()
    governing_paths = {r["path"] for c in config.get("governing_decisions", []) for r in c.get("citations", [])}
    authority_paths = {r["path"] for r in review.get("authority_refs", [])}
    decision_paths = {r["path"] for r in review.get("decision_refs", [])}
    if authority_sources is not None and not authority_paths <= authority_sources:
        issues.append("authority_source_not_recognized_by_approved_profile")
        return result
    if not decisions or not authority or decision_paths & (governing_paths | authority_paths):
        issues.append("separate_explicit_decision_and_authority_evidence_required")
        return result
    for decision in decisions:
        grants = [a for a in authority if a.get("actor") == decision.get("human_owner")
                  and a.get("actor_kind") == "human" and a.get("capability") == "architecture_exception"
                  and a.get("scope") == proposal["scope"] and current(a, now)]
        accepted = (decision.get("outcome") == "accepted" and decision.get("scope") == proposal["scope"]
                    and decision.get("proposal_hash") == expected["proposal_hash"]
                    and decision.get("governing_context_hash") == expected["governing_context_hash"]
                    and current(decision, now))
        if accepted and grants and (decision["human_owner"] != proposal["author"] or grants[0].get("allow_self_approval") is True):
            result.update(fit="documented_human_exception; authenticity_not_verified", decision=decision,
                          authority_evidence=grants[0])
            return result
    issues.append("human_authority_decision_scope_binding_or_currentness_unverifiable")
    return result
