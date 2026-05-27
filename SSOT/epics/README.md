# Context OS Epic Backlog

This folder is the **epic backlog** for the Context OS project.

Epics are **execution artifacts** derived from
[`../P.2_Product_Roadmap.md`](../P.2_Product_Roadmap.md) and the narrative
roadmap in [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md).

User stories are not yet expanded here. This phase only establishes the
foundation of the backlog.

---

## Rules

1. **Every epic maps to a roadmap version** (v0.1 → v1.0).
2. **One file per epic.** Filename pattern: `EPIC-NNN_Short_Name.md`.
3. **Epic IDs are immutable.** Once assigned, an ID is not reused or renumbered.
4. **Status values:** `Planned`, `Active`, `Blocked`, `Done`, `Cancelled`.
5. Epics are **product-oriented** (capabilities, outcomes), not document-oriented.
6. Each epic must satisfy the **Definition of Ready** in
   [`../G.1_Definition_of_Ready.md`](../G.1_Definition_of_Ready.md) before
   moving to `Active`, and the **Definition of Done** in
   [`../G.2_Definition_of_Done.md`](../G.2_Definition_of_Done.md) before
   moving to `Done`.

---

## Required Sections per Epic

Each epic file must include:

- Epic ID
- Version
- Status
- Objective
- Problem
- Scope
- Out of Scope
- Expected Outcomes
- Dependencies
- Success Criteria
- DoR
- DoD
- Related Artifacts

---

## Current Backlog

### v0.2 — Framework Hardening (Active)

| ID | Name | Status |
|---|---|---|
| [EPIC-001](EPIC-001_Structural_Integrity.md) | Structural Integrity | Active |
| [EPIC-002](EPIC-002_Governance_Foundation.md) | Governance Foundation | Planned |
| [EPIC-003](EPIC-003_Framework_Dogfooding.md) | Framework Dogfooding | Planned |

### v0.3+ — Future Epics

EPIC-004 through EPIC-032 are listed in
[`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
and will be expanded into individual files when their version becomes active.
