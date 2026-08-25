# P.2 — Context OS Product Roadmap

Version: 1.0

Last Updated: 2026-08-24

Owner: Context OS Core Team

Status: Active

---

# Product Goal

Build Context OS as the canonical Organizational Context Runtime for
human-agent systems.

Context OS enables humans, agents, and systems to operate using a shared
contextual model that continuously evolves, validates itself, and supports
intelligent execution.

The broader organizational outcome is to enable AI-native organizations to
govern their own evolution, as defined by the canonical
[`Theory of the AI-Native Organization`](../docs/0.x_foundations/0.9_COS_Theory_of_the_AI_Native_Organization.md).

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

v0.9 — Contextual Reasoning

Status: Active

Primary Goal:

Interpret current organizational context, governed memory, historical context,
evidence, outcomes, Health, and prior decisions to produce explainable,
evidence-backed assessments, hypotheses, recommendations, and required human
decisions without creating autonomous truth or authority.

Governing Context:

[`../docs/0.x_foundations/0.9_COS_Theory_of_the_AI_Native_Organization.md`](../docs/0.x_foundations/0.9_COS_Theory_of_the_AI_Native_Organization.md)

[`../docs/0.x_foundations/0.8_COS_GENESIS.md`](../docs/0.x_foundations/0.8_COS_GENESIS.md)

[`../docs/0.x_foundations/0.7_COS_Context_Versioning_and_Memory.md`](../docs/0.x_foundations/0.7_COS_Context_Versioning_and_Memory.md)

[`../SSOT/epics/EPIC-005_Knowledge_Engine.md`](epics/EPIC-005_Knowledge_Engine.md)

Self-Hosting Execution:

- Latest closed release mission:
  [`E.4 Mission V08-RELEASE-CUT-001`](E.4_Mission_V08-RELEASE-CUT-001_Organizational_Memory_Release_Cut.md)
- Closed v0.8 release verification mission:
  [`E.4 Mission V08-ORGANIZATIONAL-MEMORY-RELEASE-VERIFY-001`](E.4_Mission_V08-ORGANIZATIONAL-MEMORY-RELEASE-VERIFY-001_Organizational_Memory_Release_Verification.md)
- Previous closed v0.8 mission:
  [`E.4 Mission V08-MEMORY-CONTEXT-VERSION-INTEGRATION-001`](E.4_Mission_V08-MEMORY-CONTEXT-VERSION-INTEGRATION-001_Context_Version_Memory_Integration.md)
- Previous closed v0.8 mission:
  [`E.4 Mission V08-CONTEXT-VERSION-CAPTURE-001`](E.4_Mission_V08-CONTEXT-VERSION-CAPTURE-001_Context_Version_Capture.md)
- Earlier closed v0.8 mission:
  [`E.4 Mission V08-MEMORY-RETRIEVAL-POLICY-INTEGRATION-001`](E.4_Mission_V08-MEMORY-RETRIEVAL-POLICY-INTEGRATION-001_Policy_Aware_Memory_Retrieval.md)
- Earlier closed v0.8 mission:
  [`E.4 Mission V08-MEMORY-RETENTION-RESOLUTION-001`](E.4_Mission_V08-MEMORY-RETENTION-RESOLUTION-001_Read_Only_Retention_Resolution.md)
- Earlier closed v0.8 mission:
  [`E.4 Mission V08-MEMORY-RETENTION-GOVERNANCE-001`](E.4_Mission_V08-MEMORY-RETENTION-GOVERNANCE-001_Memory_Retention_Governance.md)
- Earlier closed v0.8 mission:
  [`E.4 Mission V08-MEMORY-RETRIEVAL-SURFACE-001`](E.4_Mission_V08-MEMORY-RETRIEVAL-SURFACE-001_Bounded_Memory_Retrieval.md)
- Earlier closed v0.8 mission:
  [`E.4 Mission V08-ORGANIZATIONAL-MEMORY-PLAN-001`](E.4_Mission_V08-ORGANIZATIONAL-MEMORY-PLAN-001_Organizational_Memory_Continuity.md)
- Latest closed foundational mission:
  [`E.4 Mission THEORY-AI-NATIVE-ORGANIZATION-V01`](E.4_Mission_THEORY-AI-NATIVE-ORGANIZATION-V01.md)
- Latest closed release mission:
  [`E.4 Mission V07-RELEASE-CUT-001`](E.4_Mission_V07-RELEASE-CUT-001_Context_Health_and_Learning_Release_Cut.md)
- Closed v0.7 release verification mission:
  [`E.4 Mission V07-CONTEXT-HEALTH-RELEASE-VERIFY-001`](E.4_Mission_V07-CONTEXT-HEALTH-RELEASE-VERIFY-001_Context_Health_Release_Verification.md)
- Previous closed mission:
  [`E.4 Mission V07-CONTEXT-HEALTH-CLI-001`](E.4_Mission_V07-CONTEXT-HEALTH-CLI-001_Context_Health_CLI.md)
- Earlier closed mission:
  [`E.4 Mission V07-CONTEXT-USE-EVIDENCE-001`](E.4_Mission_V07-CONTEXT-USE-EVIDENCE-001_Mission_Use_Evidence.md)
- Earlier closed mission:
  [`E.4 Mission V07-CONTEXT-HEALTH-PLAN-001`](E.4_Mission_V07-CONTEXT-HEALTH-PLAN-001_Context_Health_and_Learning.md)
- Latest closed release mission:
  [`E.4 Mission V06-RELEASE-CUT-001`](E.4_Mission_V06-RELEASE-CUT-001_Context_Activation_Release_Cut.md)
- Closed v0.6 release verification mission:
  [`E.4 Mission V06-CONTEXT-ACTIVATION-RELEASE-VERIFY-001`](E.4_Mission_V06-CONTEXT-ACTIVATION-RELEASE-VERIFY-001_Context_Activation_Release_Verification.md)
- Previous closed mission:
  [`E.4 Mission V06-ACTIVATION-CONTEXT-LAYERS-001`](E.4_Mission_V06-ACTIVATION-CONTEXT-LAYERS-001_Mission_Context_Layers.md)
- Earlier closed mission:
  [`E.4 Mission V06-ACTIVATION-HANDOFF-USE-001`](E.4_Mission_V06-ACTIVATION-HANDOFF-USE-001_Handoff_First_Mission_Execution.md)
- Closed v0.6 handoff format mission:
  [`E.4 Mission V06-ACTIVATION-HANDOFF-FORMAT-001`](E.4_Mission_V06-ACTIVATION-HANDOFF-FORMAT-001_Package_Backed_Handoff_Format.md)
- Closed v0.6 package-first execution mission:
  [`E.4 Mission V06-ACTIVATION-PACKAGE-USE-001`](E.4_Mission_V06-ACTIVATION-PACKAGE-USE-001_Package_First_Mission_Execution.md)
- Closed v0.6 Activation Package CLI mission:
  [`E.4 Mission V06-ACTIVATION-PACKAGE-CLI-001`](E.4_Mission_V06-ACTIVATION-PACKAGE-CLI-001_Activation_Package_CLI.md)
- Closed v0.6 activation package mission:
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
| v0.8 Organizational Memory | Governed Mission, decision, evidence, outcome, learning, temporal, supersession, retention, prior-art, and pattern continuity; EPIC-005 interpretation only where required |
| v0.9 Contextual Reasoning | Evidence-backed interpretation, impact analysis, hypotheses, improvement and capability recommendations; GraphRAG only where justified |
| v1.0 Organizational Context Runtime | Full product journey and governed organizational evolution loop operating end-to-end |

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

Status: Active

Primary release slice: v0.9 Contextual Reasoning, building on released v0.8
Organizational Memory. Reasoning must preserve evidence, interpretation,
hypothesis, recommendation, Decision, authority, temporal applicability, and
truth boundaries. GraphRAG remains optional until a controlled comparison
demonstrates material value over bounded structured Retrieval.

The first active v0.9 slice is a read-only governed Contextual Assessment over
Activation, Health, policy-aware Memory, and exact Context Versions. The next
release dependency is a controlled multi-class benchmark and evidence-backed
GraphRAG decision.

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

The first v0.6 activation slices provide `contextos.activation.package/1`,
`contextos.activation.package_check/1`, and the read-only
`contextos activate` CLI surface. Package-first Mission execution is now
proven for a self-hosted Context OS Mission.

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
- 2026-08-11 - v1.0 - Linked the Activation Package CLI mission.
- 2026-08-11 - v1.0 - Linked the package-backed activation handoff mission.
- 2026-08-11 - v1.0 - Linked the handoff-first Mission execution and handoff check mission.
- 2026-08-11 - v1.0 - Linked the Mission Context layers mission.
- 2026-08-11 - v1.0 - Linked the package-first Mission execution proof.
- 2026-08-13 - v1.0 - Closed Context Activation release verification and
  recorded v0.6 release readiness.
- 2026-08-13 - v1.0 - Closed v0.6 Context Activation and re-anchored the
  current release on v0.7 Context Health & Learning.
- 2026-08-15 - v1.0 - Linked the first Context Health & Learning Mission and
  Health Report contract.
- 2026-08-16 - v1.0 - Linked structured Mission-use evidence and its Health
  integration.
- 2026-08-20 - v1.0 - Linked the read-only Context Health CLI Mission.
- 2026-08-20 - v1.0 - Recorded v0.7 Context Health & Learning release
  readiness.
- 2026-08-20 - v1.0 - Closed v0.7 Context Health & Learning and re-anchored
  the current release on v0.8 Organizational Memory.
- 2026-08-20 - v1.0 - Linked the canonical Theory of the AI-Native
  Organization and aligned v0.8-v1.0 around governed memory, reasoning, and
  organizational evolution.
- 2026-08-21 - v1.0 - Opened the policy-only Organizational Memory retention
  governance Mission after publishing bounded retrieval.
- 2026-08-23 - v1.0 - Integrated deterministic Retention Resolution into
  Memory Retrieval before candidate exposure and preserved independent
  Retrieval, visibility, and Activation outcomes.
- 2026-08-23 - v1.0 - Added immutable, content-free Context Version capture
  and historical verification as the next Organizational Memory continuity
  primitive.
- 2026-08-23 - v1.0 - Integrated exact Context Version evidence into Memory
  Continuity and policy-aware Retrieval while preserving partial/unknown
  history and current canonical authority.
- 2026-08-23 - v1.0 - Verified v0.8 Organizational Memory release readiness,
  retained explicit artifact persistence, and deferred automatic registry and
  destructive retention capabilities.
- 2026-08-24 - v1.0 - Closed v0.8 Organizational Memory and re-anchored the
  current release on v0.9 Contextual Reasoning.
- 2026-08-24 - v1.0 - Linked the first governed Contextual Assessment Mission
  and the controlled reasoning benchmark dependency.
