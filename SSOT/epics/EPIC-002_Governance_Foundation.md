# EPIC-002 — Governance Foundation

- **Epic ID:** EPIC-002
- **Version:** v0.2 — Framework Hardening
- **Status:** Planned
- **Owner:** Context OS Maintainers

---

## Objective

Establish the minimal governance mechanisms required to evolve Context OS
without entropy: explicit Definition of Ready / Definition of Done, agent
contribution rules, and a diff-reviewable change process.

---

## Problem

Without explicit governance, structural and conceptual changes accumulate
silently. Agents and contributors lack a shared rulebook for what
"acceptable change" means, which leads to drift, duplicated abstractions,
and erosion of contextual integrity.

---

## Scope

- A complete `G.1 Definition of Ready` covering content, structure, and
  reference integrity for any proposed change.
- A complete `G.2 Definition of Done` covering verification, link integrity,
  and naming compliance.
- `ops/AGENT_RULES.md` aligned to the canonical structure and to the
  Agentic Operating Model.
- A documented change-proposal workflow (PR → review → merge) referenced
  from `A.1 System Map`.
- Governance scope explicitly limited (no premature SaaS, no autonomous
  structural mutation).

---

## Out of Scope

- Validator implementation (EPIC-007).
- Automated governance enforcement (deferred to the Runtime).
- External contributor onboarding flows beyond `CONTRIBUTING.md`.

---

## Expected Outcomes

- A single, unambiguous DoR and DoD pair that any contributor or agent can
  apply.
- Agent rules that prevent unreviewed structural mutation.
- Governance surface area visible from `SSOT/README.md` and `ops/`.
- A repeatable change-proposal pattern observed across Phase 1, Phase 2,
  and Phase 3 commits.

---

## Dependencies

- EPIC-001 Structural Integrity (canonical structure must exist before
  governance can reference it).
- [`../G.1_Definition_of_Ready.md`](../G.1_Definition_of_Ready.md)
- [`../G.2_Definition_of_Done.md`](../G.2_Definition_of_Done.md)
- [`../../ops/AGENT_RULES.md`](../../ops/AGENT_RULES.md)
- [`../../docs/3.x_operation/3.1_COS_Agentic_Operating_Model.md`](../../docs/3.x_operation/3.1_COS_Agentic_Operating_Model.md)

---

## Success Criteria

- DoR and DoD reference the canonical taxonomy and naming conventions.
- `ops/AGENT_RULES.md` uses `Context OS` prose and reflects the Agentic
  Operating Model vocabulary.
- A new contributor can submit a structural change PR using only the SSOT
  and `ops/` as guidance.
- Phase 1, Phase 2, and Phase 3 commits each satisfy the documented DoD
  retroactively.

---

## Definition of Ready (DoR)

- Canonical structure exists (EPIC-001 reaches `Done` for current scope).
- Current DoR / DoD content has been reviewed for gaps.
- `ops/AGENT_RULES.md` content audited for stale references.

---

## Definition of Done (DoD)

- DoR and DoD reviewed, edited if needed, and committed.
- `ops/AGENT_RULES.md` aligned with current canonical structure and naming
  rules.
- Governance surface linked from `SSOT/README.md`.
- No conflicting governance rules across SSOT and `ops/`.

---

## Related Artifacts

- [`../G.1_Definition_of_Ready.md`](../G.1_Definition_of_Ready.md)
- [`../G.2_Definition_of_Done.md`](../G.2_Definition_of_Done.md)
- [`../../ops/AGENT_RULES.md`](../../ops/AGENT_RULES.md)
- [`../../docs/3.x_operation/3.1_COS_Agentic_Operating_Model.md`](../../docs/3.x_operation/3.1_COS_Agentic_Operating_Model.md)
