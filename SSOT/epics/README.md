# Context OS Epic Backlog

This folder is the **epic backlog** for the Context OS project.

Epics are **execution artifacts** derived from
[`../P.2_Product_Roadmap.md`](../P.2_Product_Roadmap.md) and the narrative
roadmap in [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md).

User stories are not yet expanded here. This phase only establishes the
foundation of the backlog.

---

## Rules

1. **Every epic maps to one or more roadmap release slices** (v0.1 → v1.0).
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

### v0.2 — Framework Hardening (Pre-Codex handoff complete)

The pre-Codex handoff is complete. Individual legacy epic statuses below are
retained from their epic files until those epics are separately closed or
superseded by a governance update.

| ID | Name | Status |
|---|---|---|
| [EPIC-001](EPIC-001_Structural_Integrity.md) | Structural Integrity | Active |
| [EPIC-002](EPIC-002_Governance_Foundation.md) | Governance Foundation | Planned |
| [EPIC-003](EPIC-003_Framework_Dogfooding.md) | Framework Dogfooding | Planned |

### v0.3 — Context Readiness (Active)

| ID | Name | Status |
|---|---|---|
| [EPIC-004](EPIC-004_Discovery_Engine.md) | Discovery Engine | Planned |
| [EPIC-005](EPIC-005_Knowledge_Engine.md) | Knowledge Engine | Planned |
| [EPIC-006](EPIC-006_Context_Builder.md) | Context Builder | Planned |
| [EPIC-007](EPIC-007_Validator_Engine.md) | Validator Engine | Active |
| [EPIC-008](EPIC-008_Runtime_CLI.md) | Runtime CLI | Active |

v0.3 does not require all five epics to be completed. The release takes the
smallest slices required to produce a Context Readiness Assessment:

- Validator and CLI foundations already shipped.
- Discovery contributes a local repository inventory slice.
- Builder contributes recommendation mapping only.
- Knowledge Engine is deferred until structured context construction and
  learning loops need interpretation.

### v0.4+ — Future Epics

Future releases follow the product journey in
[`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md):

```text
Guided Bootstrap -> Context Construction -> Context Activation ->
Context Health & Learning -> Organizational Memory -> Contextual Reasoning
```

EPIC-009 onward will be expanded into individual files when their release
slice becomes active.
