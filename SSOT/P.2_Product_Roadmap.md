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

v0.6 — Context Activation

Status: Active

Primary Goal:

Make governed context available in the places where humans, agents, and tools
perform work, without duplicating, degrading, or bypassing canonical context.

Canonical Contract:

[`../docs/1.x_architecture/1.5_runtime_contracts/1.5.9_Context_Activation_Package_Contract.md`](../docs/1.x_architecture/1.5_runtime_contracts/1.5.9_Context_Activation_Package_Contract.md)

Guided Bootstrap Apply Contract:

[`../docs/1.x_architecture/1.5_runtime_contracts/1.5.7_Bootstrap_Apply_Approval_Contract.md`](../docs/1.x_architecture/1.5_runtime_contracts/1.5.7_Bootstrap_Apply_Approval_Contract.md)

Self-Hosting Execution:

- Current closed mission:
  [`E.4 Mission V06-CONTEXT-ACTIVATION-PLAN-001`](E.4_Mission_V06-CONTEXT-ACTIVATION-PLAN-001_Context_Activation_Package.md)
- Closed v0.5 release cut mission:
  [`E.4 Mission V05-RELEASE-CUT-001`](E.4_Mission_V05-RELEASE-CUT-001_Context_Construction_Release_Cut.md)
- Closed v0.5 release verification mission:
  [`E.4 Mission V05-CONTEXT-CONSTRUCTION-RELEASE-VERIFY-001`](E.4_Mission_V05-CONTEXT-CONSTRUCTION-RELEASE-VERIFY-001_Context_Construction_Release_Verification.md)
- Closed v0.5 draft promotion execution mission:
  [`E.4 Mission V05-BUILDER-DRAFT-PROMOTION-EXECUTE-001`](E.4_Mission_V05-BUILDER-DRAFT-PROMOTION-EXECUTE-001_Draft_Promotion_Execute.md)
- Closed v0.5 draft promotion preflight mission:
  [`E.4 Mission V05-BUILDER-DRAFT-PROMOTION-PREFLIGHT-001`](E.4_Mission_V05-BUILDER-DRAFT-PROMOTION-PREFLIGHT-001_Draft_Promotion_Preflight.md)
- Closed v0.5 draft approval decision mission:
  [`E.4 Mission V05-BUILDER-DRAFT-APPROVAL-DECISION-001`](E.4_Mission_V05-BUILDER-DRAFT-APPROVAL-DECISION-001_Draft_Approval_Decision.md)
- Closed v0.5 draft review decision mission:
  [`E.4 Mission V05-BUILDER-DRAFT-REVIEW-DECISION-001`](E.4_Mission_V05-BUILDER-DRAFT-REVIEW-DECISION-001_Draft_Review_Decision.md)
- Closed v0.5 draft review surface mission:
  [`E.4 Mission V05-BUILDER-DRAFT-REVIEW-SURFACE-001`](E.4_Mission_V05-BUILDER-DRAFT-REVIEW-SURFACE-001_Draft_Review_Surface.md)
- Closed v0.5 create-only Builder draft write mission:
  [`E.4 Mission V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001`](E.4_Mission_V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001_Create_Only_Builder_Draft_Write.md)
- Closed v0.5 Draft Workspace runtime mission:
  [`E.4 Mission V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001`](E.4_Mission_V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001_Draft_Workspace_Runtime.md)
- Closed v0.5 draft workspace decision mission:
  [`E.4 Mission V05-BUILDER-DRAFT-SURFACE-DECISION-001`](E.4_Mission_V05-BUILDER-DRAFT-SURFACE-DECISION-001_Draft_Workspace_Decision.md)
- Closed v0.5 builder draft authority mission:
  [`E.4 Mission V05-BUILDER-DRAFT-AUTHORITY-001`](E.4_Mission_V05-BUILDER-DRAFT-AUTHORITY-001_Builder_Draft_Authority.md)
- Closed v0.5 builder draft planning mission:
  [`E.4 Mission V05-BUILDER-DRAFT-PLAN-001`](E.4_Mission_V05-BUILDER-DRAFT-PLAN-001_Builder_Draft_Planning.md)
- Closed v0.5 local discovery mission:
  [`E.4 Mission V05-DISCOVERY-BUNDLE-LOCAL-001`](E.4_Mission_V05-DISCOVERY-BUNDLE-LOCAL-001_Local_Discovery_Bundle.md)
- Closed v0.5 construction planning mission:
  [`E.4 Mission V05-CONTEXT-CONSTRUCTION-PLAN-001`](E.4_Mission_V05-CONTEXT-CONSTRUCTION-PLAN-001_Context_Construction_Planning.md)
- Foundational closed mission:
  [`E.4 Mission SELFHOST-001`](E.4_Mission_SELFHOST-001_Governed_Execution_Loop.md)
- Closed v0.4 approval-model mission:
  [`E.4 Mission V04-BOOTSTRAP-APPLY-001`](E.4_Mission_V04-BOOTSTRAP-APPLY-001_Guided_Bootstrap_Apply_Approval_Model.md)
- Closed v0.4 proposal-engine mission:
  [`E.4 Mission V04-BOOTSTRAP-PROPOSAL-001`](E.4_Mission_V04-BOOTSTRAP-PROPOSAL-001_Read_Only_Bootstrap_Proposal_Engine.md)
- Closed v0.4 proposal-review mission:
  [`E.4 Mission V04-BOOTSTRAP-PROPOSAL-REVIEW-001`](E.4_Mission_V04-BOOTSTRAP-PROPOSAL-REVIEW-001_Read_Only_Bootstrap_Proposal_Review_Surface.md)
- Closed v0.4 approval-record mission:
  [`E.4 Mission V04-BOOTSTRAP-APPROVAL-001`](E.4_Mission_V04-BOOTSTRAP-APPROVAL-001_Read_Only_Bootstrap_Approval_Record.md)
- Closed v0.4 approval-acceptance mission:
  [`E.4 Mission V04-BOOTSTRAP-APPROVAL-ACCEPT-001`](E.4_Mission_V04-BOOTSTRAP-APPROVAL-ACCEPT-001_Explicit_Bootstrap_Approval_Acceptance.md)
- Closed v0.4 apply-preflight mission:
  [`E.4 Mission V04-BOOTSTRAP-APPLY-PREFLIGHT-001`](E.4_Mission_V04-BOOTSTRAP-APPLY-PREFLIGHT-001_Bootstrap_Apply_Preflight.md)
- Closed v0.4 create-only apply mission:
  [`E.4 Mission V04-BOOTSTRAP-APPLY-CREATE-ONLY-001`](E.4_Mission_V04-BOOTSTRAP-APPLY-CREATE-ONLY-001_Create_Only_Bootstrap_Apply.md)
- Closed v0.4 release verification mission:
  [`E.4 Mission V04-GUIDED-BOOTSTRAP-RELEASE-VERIFY-001`](E.4_Mission_V04-GUIDED-BOOTSTRAP-RELEASE-VERIFY-001_Release_Verification.md)
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
| v0.4 Guided Bootstrap | EPIC-008 `contextos init`, EPIC-006 governed bootstrap proposal/approval/preflight/apply path, EPIC-007 pre-bootstrap/gate validation |
| v0.5 Context Construction | Construction planning, local Discovery Bundle, Builder Draft Plan, Builder Draft Authority, Draft Workspace runtime, create-only draft writes, draft review surface, EPIC-007 gate integration |
| v0.6 Context Activation | Context Activation Package, EPIC-008 activation surface, adapter epics, validated context delivery |
| v0.7 Context Health & Learning | Health/drift slices, EPIC-007 full-mode expansion, EPIC-005 learning inputs |
| v0.8 Organizational Memory | EPIC-005 durable knowledge and interpretation, Context Graph memory traversal |
| v0.9 Contextual Reasoning | Context reasoning, capability registry, governed agent-team assembly |
| v1.0 Organizational Context Runtime | Full governed product journey operating end-to-end |

---

# Active Runtime Epics

## EPIC-004

Discovery Engine

Status: Active

Primary release slice: v0.3 local readiness inventory, expanding in v0.5
Context Construction. The active v0.5 slice is a read-only local Discovery
Bundle consumed by construction planning; external connectors and `scan` CLI
remain deferred.

---

## EPIC-005

Knowledge Engine

Status: Planned

Primary release slice: v0.7 Context Health & Learning, expanding in v0.8
Organizational Memory.

---

## EPIC-006

Context Builder

Status: Active

Primary release slice: v0.4 Guided Bootstrap and v0.5 Context Construction.
The active v0.5 slice now includes read-only Builder Draft Planning, the
Builder Draft Authority Contract, the Draft Workspace decision, and the
read-only Draft Workspace runtime preflight, plus controlled create-only draft
write behavior inside the Draft Workspace, a read-only draft review surface,
governed human Review Decision object, and a governed human Approval Decision
object, plus a read-only Promotion Preflight and controlled create-only
canonical promotion execution. CLI exposure, replacement promotion, and broad
canonical SSOT mutation remain deferred to explicit governed missions.

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

The first v0.6 activation slice is engine/API-first:
`contextos.activation.package/1`. A Runtime CLI activation surface remains the
next release mission rather than a prerequisite for the initial activation
primitive.

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
- 2026-08-11 - v1.0 - Added read-only Bootstrap Proposal Review Surface
  mission reference.
- 2026-08-11 - v1.0 - Added read-only Bootstrap Approval Record mission
  reference.
- 2026-08-11 - v1.0 - Re-anchored current release on v0.5 Context
  Construction and linked the first construction planning mission.
- 2026-08-11 - v1.0 - Linked the local Discovery Bundle mission and updated
  EPIC-004 status.
- 2026-08-11 - v1.0 - Linked the Builder Draft Planning mission.
- 2026-08-11 - v1.0 - Linked the Builder Draft Authority mission and contract.
- 2026-08-11 - v1.0 - Linked the Draft Workspace decision.
- 2026-08-11 - v1.0 - Linked the Draft Workspace runtime mission.
- 2026-08-11 - v1.0 - Linked the create-only Builder draft write mission.
- 2026-08-11 - v1.0 - Linked the Draft Review Surface mission.
- 2026-08-11 - v1.0 - Linked the Draft Review Decision mission.
- 2026-08-11 - v1.0 - Linked the Draft Approval Decision mission.
- 2026-08-11 - v1.0 - Linked the Draft Promotion Preflight mission.
- 2026-08-11 - v1.0 - Linked the Draft Promotion Execute mission.
- 2026-08-11 - v1.0 - Closed v0.5 Context Construction release and re-anchored
  current release on v0.6 Context Activation.
- 2026-08-11 - v1.0 - Linked the first Context Activation Package mission.
