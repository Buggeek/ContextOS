# P.2 — Context OS Product Roadmap

Version: 1.0

Last Updated: 2026-08-11

Owner: Context OS Core Team

Status: Active

---

# Product Goal

Build Context OS as the canonical Organizational Context Runtime for
human-agent systems.

Context OS enables humans, agents, and systems to operate using a shared
contextual model that continuously evolves, validates itself, and supports
intelligent execution.

Canonical architecture:
[`../docs/1.x_architecture/1.0_COS_Architecture.md`](../docs/1.x_architecture/1.0_COS_Architecture.md).

---

# Canonical Product Journey

```text
Assess -> Bootstrap -> Construct -> Activate -> Learn -> Reason
```

This journey is the organizing principle for releases from v0.3 onward.
Runtime subsystems remain part of the architecture, but releases are planned
around user-visible progress through the journey.

---

# Strategic Themes

## Theme 1

Context Readiness

Help users understand what context exists, what is missing, and what to do
next.

---

## Theme 2

Guided Context Formation

Move from readiness to governed bootstrap and construction without silently
inventing truth.

---

## Theme 3

Context Activation

Enable humans, agents, and tools to use governed context where work happens.

---

## Theme 4

Context Learning and Memory

Keep context current, traceable, and reusable across decisions and teams.

---

## Theme 5

Contextual Reasoning

Transform governed context into better recommendations, planning, and
execution.

---

# Current Version

v0.4 — Guided Bootstrap

Status: Active

Primary Goal:

Transform Context Readiness findings into a governed bootstrap plan and,
through later v0.4 slices, an approved minimum Context OS home.

Canonical Contract:

[`../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md`](../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md)

Guided Bootstrap Apply Contract:

[`../docs/1.x_architecture/1.5_runtime_contracts/1.5.7_Bootstrap_Apply_Approval_Contract.md`](../docs/1.x_architecture/1.5_runtime_contracts/1.5.7_Bootstrap_Apply_Approval_Contract.md)

Self-Hosting Execution:

- Current closed mission:
  [`E.4 Mission SELFHOST-001`](E.4_Mission_SELFHOST-001_Governed_Execution_Loop.md)
- Closed v0.4 approval-model mission:
  [`E.4 Mission V04-BOOTSTRAP-APPLY-001`](E.4_Mission_V04-BOOTSTRAP-APPLY-001_Guided_Bootstrap_Apply_Approval_Model.md)
- Closed v0.4 proposal-engine mission:
  [`E.4 Mission V04-BOOTSTRAP-PROPOSAL-001`](E.4_Mission_V04-BOOTSTRAP-PROPOSAL-001_Read_Only_Bootstrap_Proposal_Engine.md)
- Evolution Inbox:
  [`E.5 Evolution Inbox`](E.5_Evolution_Inbox.md)

The release is now executed through Mission Packets. Roadmap scope still governs
release intent; Mission Packets govern bounded execution.

---

# Planned Releases

| Version | Name |
|----------|--------|
| v0.3 | Context Readiness |
| v0.4 | Guided Bootstrap |
| v0.5 | Context Construction |
| v0.6 | Context Activation |
| v0.7 | Context Health & Learning |
| v0.8 | Organizational Memory |
| v0.9 | Contextual Reasoning |
| v1.0 | Organizational Context Runtime |

---

# Release Slice Alignment

| Release | Primary epic slices |
|---|---|
| v0.3 Context Readiness | Context Readiness Assessment contract, EPIC-007 Validator Engine, EPIC-008 Runtime CLI, EPIC-004 local inventory, EPIC-006 recommendation mapping |
| v0.4 Guided Bootstrap | EPIC-008 read-only `contextos init` planning, EPIC-006 scaffolding/drafts in later slices, EPIC-007 pre-bootstrap/gate validation |
| v0.5 Context Construction | EPIC-004 Discovery Bundle, EPIC-006 Builder promotion path, EPIC-007 gate integration |
| v0.6 Context Activation | EPIC-008 activation surface, adapter epics, validated context delivery |
| v0.7 Context Health & Learning | Health/drift slices, EPIC-007 full-mode expansion, EPIC-005 learning inputs |
| v0.8 Organizational Memory | EPIC-005 durable knowledge and interpretation, Context Graph memory traversal |
| v0.9 Contextual Reasoning | Context reasoning, capability registry, governed agent-team assembly |
| v1.0 Organizational Context Runtime | Full governed product journey operating end-to-end |

---

# Active Runtime Epics

## EPIC-004

Discovery Engine

Status: Planned

Primary release slice: v0.3 local readiness inventory, expanding in v0.5
Context Construction.

---

## EPIC-005

Knowledge Engine

Status: Planned

Primary release slice: v0.7 Context Health & Learning, expanding in v0.8
Organizational Memory.

---

## EPIC-006

Context Builder

Status: Planned

Primary release slice: v0.4 Guided Bootstrap and v0.5 Context Construction.
The active v0.4 slice is bootstrap planning only; write-capable scaffolding is
deferred to an explicit proposal-approved apply slice.

---

## EPIC-007

Validator Engine

Status: Active

Primary release slice: v0.3 Context Readiness. Validator Engine v0 and the
runtime component extraction have shipped; later slices harden health and
runtime-event integration.

---

## EPIC-008

Runtime CLI

Status: Active

Primary release slice: v0.3 Context Readiness and v0.4 Guided Bootstrap. The
validate and assess surfaces have shipped; v0.4 now exposes read-only
`contextos init` bootstrap planning. Later slices add bootstrap apply,
construction, activation, and mission-oriented commands as their releases
require them.

---

# Success Criteria

Context OS successfully becomes:

- assessable
- bootstrapable
- constructable
- activatable
- learnable
- reason-capable
- governable
- extensible
- operational

while preserving contextual integrity.

---

# North Star

Context is infrastructure.

The objective of Context OS is to make organizational context operational,
governable, and reusable across humans, agents, and systems.

---

# Change Log

- 2026-08-11 - v1.0 - Added self-hosting execution references for v0.4
  Guided Bootstrap.
- 2026-08-11 - v1.0 - Added read-only Bootstrap Proposal Engine mission
  reference.
