# EPIC-003 — Framework Dogfooding

- **Epic ID:** EPIC-003
- **Version:** v0.2 — Framework Hardening
- **Status:** Planned
- **Owner:** Context OS Maintainers

---

## Objective

Use Context OS to govern the Context OS repository itself, so the framework
is continuously validated against its own rules and every structural,
strategic, and execution change is produced through its own artifacts.

---

## Problem

A framework that does not apply to its own source loses credibility and
accumulates contradictions. Without dogfooding, the gap between "what the
framework says" and "how the framework evolves" widens over time, eroding
trust for external adopters.

---

## Scope

- Maintain a complete MOM (`S.1`, `P.1`, `A.1`, `A.4`, `G.1`, `G.2`) for
  the Context OS project itself in `SSOT/`.
- Maintain an execution surface in `SSOT/` that goes beyond the MOM:
  Product Roadmap (`P.2`), epic backlog (`epics/`), and user stories
  (`E.1`).
- Drive every structural and strategic change through SSOT-anchored
  artifacts (epics, user stories) before code or doc changes are made.
- Use commits as evidence: each commit message references the epic(s) it
  advances when applicable.
- Keep `examples/` aligned with the canonical taxonomy so they remain
  reusable references.

---

## Out of Scope

- Runtime CLI to automate SSOT generation (EPIC-008).
- Validator automation (EPIC-007).
- Multi-repo dogfooding (Lukspeed, Cocora) — separate initiative.

---

## Expected Outcomes

- `SSOT/` is the authoritative execution surface for the Context OS
  project; narrative strategy stays in `docs/5.x_strategy/`.
- Every active epic has a corresponding file in `SSOT/epics/` with status,
  scope, outcomes, and success criteria.
- New contributors can understand the current state of the project by
  reading `SSOT/README.md` and the epic backlog alone.
- Phase 1, Phase 2, and Phase 3 commits are explicitly traceable to
  EPIC-001 / EPIC-002 / EPIC-003 respectively.

---

## Dependencies

- EPIC-001 Structural Integrity (canonical structure required).
- EPIC-002 Governance Foundation (DoR / DoD required to drive epics).
- [`../P.1_Product_Map.md`](../P.1_Product_Map.md)
- [`../P.2_Product_Roadmap.md`](../P.2_Product_Roadmap.md)
- [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
- [`README.md`](README.md) (epic backlog rules)

---

## Success Criteria

- `SSOT/README.md` lists MOM, Execution Artifacts, and the `epics/` folder.
- `SSOT/epics/` contains one file per active epic with all required
  sections populated.
- All future product changes originate from an epic and, when they reach
  story-level granularity, from an `E.x` user story.
- Examples in `examples/` remain aligned with the live taxonomy.

---

## Definition of Ready (DoR)

- EPIC-001 is `Active` or `Done` for the in-scope structural surface.
- DoR and DoD exist and are referenced from the epic template.
- `SSOT/README.md` reflects the current SSOT layout.

---

## Definition of Done (DoD)

- Epic backlog established under `SSOT/epics/` with v0.2 epics fully
  defined.
- Future epics are added as their version becomes active, not earlier.
- SSOT artifacts pass the DoD defined in `G.2`.
- Examples and templates updated to match the live taxonomy when SSOT
  artifacts evolve.

---

## Related Artifacts

- [`README.md`](README.md) — epic backlog rules.
- [`../P.2_Product_Roadmap.md`](../P.2_Product_Roadmap.md)
- [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
- [`../E.1_User_Story_US-001_Structure_Canonical_Paths.md`](../E.1_User_Story_US-001_Structure_Canonical_Paths.md)
