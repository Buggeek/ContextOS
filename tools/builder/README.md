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
