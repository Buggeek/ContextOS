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
