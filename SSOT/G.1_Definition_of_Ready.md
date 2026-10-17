# G.1 Definition of Ready (DoR)
## Version: 0.1.1
Last Updated: 2026-10-16  
Owner: COERNC Maintainers  

---

## Purpose

Define what must be true before a change is accepted for implementation in this repository.

---

## DoR Rules (Non-Negotiable)

A change is Ready only if:

1. Objective is clearly stated.
2. Scope is explicit (what is changing, and what is not).
3. Impacted areas are listed (docs/templates/examples/tools/SSOT).
4. Compliance impact is stated (minimal/strict implications).
5. Links/paths referenced are correct.
6. Evidence is provided for factual claims (or flagged as assumptions).
7. Owner is assigned.

---

## Required References

- Linked artifacts impacted by the change (at minimum by path)
- If taxonomy changes: the template mapping impact
- If templates change: the example impact

---

## Exceptions

Exceptions are allowed for:
- Pure typo fixes
- Non-structural formatting

All structural changes still require review.

---

## Enforcement

- Enforced via PR review checklist.
- Changes failing DoR should not be merged.

---

## Change Log

- 2026-10-16 — Editorial identity alignment to COERNC; technical contracts and recorded evidence retain their compatibility identifiers.

- 2026-02-19 — v0.1.0 — Initial creation
