#!/usr/bin/env python3
"""Create an explicitly synthetic, independent acceptance oracle and local input.

This is test/demo setup, not an organization generator or target mapping approval.
"""
import argparse
from pathlib import Path
from continue_work import write_json
from adoption_engine.profile import REQUIRED_CONCEPTS

DOCUMENT = """# Synthetic community support work
Owner: Product steward

Mission M-7 is active; owner is the support team.
Help returning volunteers understand their next support decision.
The principal experience is a feed of cards. Preserve its primacy.
Add continuity within existing cards; do not demote the feed.
Next: product steward reviews the in-card continuation proposal.
Candidate indicator: correct understanding in an observed return session.
No baseline or measured benefit exists.
"""
DECISION = """# Synthetic accepted exception
Product steward explicitly accepts proposal B as a bounded trial of a dominant
summary surface, replacing feed primacy for the pilot. Review before broadening.
"""


def create(base):
    base = Path(base).resolve()
    base.mkdir(parents=True, exist_ok=False)
    corpus, workspace = base / "target", base / "work"
    (corpus / "docs").mkdir(parents=True)
    workspace.mkdir(mode=0o700)
    (corpus / "docs/work.md").write_text(DOCUMENT)
    (corpus / "docs/decision.md").write_text(DECISION)
    profile = {"schema": "contextos.adoption.profile/1", "id": "profile.synthetic-support",
               "version": "1.0", "target": {"id": "synthetic-support", "scope": "repository"},
               "lifecycle": {"state": "approved", "target_ssot": False},
               "authority": {"owner": "synthetic-product-steward"},
               "mappings": [{"concept": c, "support": "declared", "recognized_as_canonical": True,
                             "sources": [{"locator": "docs/work.md", "authority_owner": "synthetic-product-steward",
                                          "lifecycle_state": "canonical", "currentness": "current",
                                          "applicable_operations": ["activation", "context_version"]}]} for c in REQUIRED_CONCEPTS],
               "validation": {"rules": {"structure.synthetic": {"applicability": "unknown", "enforcement": "none",
                                                                  "rationale": "Controlled corpus, not a native install."}}},
               "work_ownership": {"source_concepts": ["active_work"], "lifecycle_semantics": {"active": "active"}},
               "evidence_isolation": {"target_only": True, "host_context_is_evidence": False}}
    write_json(base / "profile.json", profile)
    def claim(text):
        return {"text": text, "citations": [{"path": "docs/work.md", "quote": text}]}
    config = {"target_id": "synthetic-support", "intent": "Retomar continuidad de voluntarios (sintético)",
              "profile": str(base / "profile.json"),
              "source": {"kind": "local_corpus", "root": str(corpus), "visible_sources": ["docs/work.md", "docs/decision.md"]},
              "claims": {"objective": claim("Help returning volunteers understand their next support decision."),
                         "audience": claim("Help returning volunteers understand their next support decision."),
                         "state": claim("Mission M-7 is active; owner is the support team."),
                         "existing_work": claim("Mission M-7 is active; owner is the support team."),
                         "next": claim("Next: product steward reviews the in-card continuation proposal."),
                         "value": claim("Help returning volunteers understand their next support decision."),
                         "indicator": claim("Candidate indicator: correct understanding in an observed return session.")},
              "interpretations": ["In-card continuity appears compatible; this is an operator interpretation, not automatic semantic validation. Baseline and causal contribution unknown."],
              "governing_decisions": [{"text": "Preserve the card feed as the main surface; changing its hierarchy needs an explicit product decision.",
                                       "checked_by": "synthetic operator", "check_scope": "proposal A compared against the cited integration boundary",
                                       "citations": [{"path": "docs/work.md", "quote": "Add continuity within existing cards; do not demote the feed."}]}],
              "review": {"proposal": "A: add continuity to existing cards", "fit": "compatible", "reviewed_by": "synthetic-Codex-reviewer",
                         "constraint_refs": [{"path": "docs/work.md", "quote": "The principal experience is a feed of cards. Preserve its primacy."}]},
              "ownership": {"need": {"id": "need.return", "statement": "Returning volunteer continuity", "scope": "support", "evidence_refs": ["source.work"]},
                            "work_items": [{"id": "M-7", "kind": "mission", "title": "Returning volunteer continuity", "owner": "support team",
                                            "lifecycle_state": "active", "currentness": "current", "need_refs": ["need.return"],
                                            "parent_work_id": None, "source_ids": ["source.work"], "authority_status": "target_authority",
                                            "return_condition": "Product review", "evidence_refs": ["source.work"]}],
                            "source_declarations": [{"id": "source.work", "locator": "docs/work.md", "concept": "active_work"}],
                            "coverage": {"status": "complete", "scope": "support", "source_ids": ["source.work"],
                                         "authority_status": "governed_test_coverage", "evidence_refs": ["source.work"]}}}
    write_json(workspace / "work.json", config)
    # Defined before execution; assertions are not generated from the result.
    write_json(base / "oracle.json", {"synthetic": True, "expected_owner": "M-7", "existing_work": True,
                                     "proposal_A": "operator_declares_compatible; product_acceptance_not_inferred",
                                     "proposal_B": "requires_product_architecture_decision",
                                     "proposal_B_accepted_exception": "human_declared_approved_exception; bounded_to_cited_decision",
                                     "business_value_measured": False, "execution_authorized": False})
    return workspace


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    print(create(parser.parse_args().directory))
