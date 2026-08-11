# Context OS Builder Tools

This folder contains the first Release v0.5 Builder capability.

Slice 1 implements **Builder Draft Planning** only:

- no Runtime CLI integration
- no `build-mom`
- no `build-ssot`
- no MOM/SSOT writes
- no draft file generation
- no automatic promotion
- no Knowledge Engine
- no Context Graph runtime
- no agents
- no external connectors

Public API:

```python
from builder_engine.draft_plan import BuilderDraftPlanEngine
from builder_engine.report_builder import render_human

plan = BuilderDraftPlanEngine(".").run()
human = render_human(plan)
```

Machine report schema:

```text
contextos.builder.draft_plan/1
```

The draft plan consumes:

- `contextos.discovery.bundle/1`
- `contextos.construction.plan/1`

It produces draft-planning items that preserve:

- target context artifact
- intended lifecycle state
- source evidence references
- provenance chain
- confidence/support level
- unresolved questions
- missing evidence
- contradictions
- human review and authority requirements
- promotion restrictions

The Builder boundary is strict:

```text
evidence may support a draft proposal
evidence must never silently become organizational truth
```

Before any future Builder draft write behavior, implementation must satisfy the
[`Builder Draft Authority Contract`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.8_Builder_Draft_Authority_Contract.md).

The canonical draft surface is a governed **Draft Workspace**. For the current
local filesystem runtime, that workspace maps to `.contextos/drafts/`; this path
is non-canonical and must not be treated as SSOT.

Slice V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001 adds
`DraftWorkspaceRuntime`, a read-only preflight that emits:

```text
contextos.builder.draft_workspace_preflight/1
```

It resolves future draft targets under `.contextos/drafts/<mission_id>/artifacts/`,
checks path isolation, no-overwrite, plan drift, and Validator gate status, and
does not create directories, drafts, or canonical artifacts.

Slice V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001 adds
`BuilderDraftCreateEngine`, a create-only writer that consumes an exact eligible
Draft Workspace preflight plus explicit L2 `builder.draft.create` authorization.
It emits:

```text
contextos.builder.draft_write_result/1
```

The writer may create only non-canonical draft envelopes inside `.contextos/drafts/`.
It performs no review, approval, promotion, SSOT write, or canonical context
mutation. Rollback removes only matching artifacts created by the exact write
result.

Slice V05-BUILDER-DRAFT-REVIEW-SURFACE-001 adds
`BuilderDraftReviewEngine`, a read-only review surface that emits:

```text
contextos.builder.draft_review/1
```

It reviews draft artifacts created by a draft write result, exposes identity,
provenance, evidence, support, unknowns, missing evidence, contradictions,
validation, no-overwrite evidence, and authority still required, and renders a
human-readable truth boundary. Review does not mutate, accept, approve, or
promote the draft.

Slice V05-BUILDER-DRAFT-REVIEW-DECISION-001 adds
`BuilderDraftReviewDecisionEngine`, a governed human decision surface that
emits:

```text
contextos.builder.draft_review_decision/1
```

It records an explicit L2 `builder.draft.review` outcome for an exact
`contextos.builder.draft_review/1` object and draft content hash. The decision
may be persisted as a JSON governance/evidence artifact, but it does not mutate
the reviewed draft, approve it, promote it, or write canonical SSOT context.

Allowed review-decision outcomes:

- `reviewed_ready_for_next_governance_step`
- `changes_requested`
- `rejected`
- `insufficient_evidence`
- `superseded`

The review decision preserves the boundary:

```text
Review Decision != Approval != Canonical Truth
```

Slice V05-BUILDER-DRAFT-APPROVAL-DECISION-001 adds
`BuilderDraftApprovalDecisionEngine`, a governed human approval surface that
emits:

```text
contextos.builder.draft_approval_decision/1
```

It records explicit L3 `builder.draft.approve` approval for an exact eligible
Review Decision and draft content hash. Approval may make a draft eligible as
input to a future promotion proposal, but it does not perform promotion, write
SSOT, mutate draft content, or create canonical organizational truth.

Allowed approval-decision outcomes:

- `approved_for_promotion_proposal`
- `approval_rejected`
- `approval_deferred`

The approval decision preserves the boundary:

```text
Approval Decision != Promotion != Canonical Truth
```

Slice V05-BUILDER-DRAFT-PROMOTION-PREFLIGHT-001 adds
`BuilderDraftPromotionPreflightEngine`, a read-only gate that emits:

```text
contextos.builder.draft_promotion_preflight/1
```

It consumes an exact eligible Approval Decision and determines whether the
approved draft is still safe, valid, authorized, and explainable enough to be
considered for a future canonical promotion. A successful preflight may set
`eligible_for_promotion: true`, but it always keeps:

```text
promotion_authorized: false
canonical_mutation_authorized: false
```

The preflight freezes a canonical write-set candidate and records target
canonical path state, Validator gate evidence, no-overwrite or governed
replacement-policy evidence, unresolved uncertainty, and rollback/recovery
expectations. It performs no promotion, SSOT write, canonical context mutation,
or draft mutation.
