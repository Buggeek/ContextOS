# G.2 Definition of Done (DoD)
## Version: 0.1.0
Last Updated: 2026-02-19  
Owner: Context OS Maintainers  

---

## Purpose

Define what must be true before a change is considered complete and safe to merge.

---

## DoD Rules (Non-Negotiable)

A change is Done only if:

1. Internal links remain valid (no broken relative references).
2. If taxonomy changed, templates and examples are updated (or explicitly deferred with rationale).
3. Strict examples remain strict (required headers + change log present).
4. Minimal examples remain minimal (profile declared, and omissions are intentional).
5. Rationale is captured in the diff/PR description.

---

## Exceptions

Exceptions require maintainer approval and must include an explicit follow-up item.

---

## Enforcement

- Enforced during PR review.
- Missing alignment is treated as a blocker for merge.

---

## Change Log

- 2026-02-19 — v0.1.0 — Initial creation
