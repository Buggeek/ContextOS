# Context OS Construction Tools

This folder contains the first Release v0.5 Context Construction capability.

Slice 1 implements **Construction Planning** only:

- no Runtime CLI integration
- no `build-mom`
- no `build-ssot`
- no writes to target repositories
- no automatic truth creation
- no automatic promotion
- no Knowledge Engine, Context Graph, agents, or external connectors

Public API:

```python
from construction_engine.planning_engine import ContextConstructionPlanEngine
from construction_engine.report_builder import render_human

plan = ContextConstructionPlanEngine(".").run()
human = render_human(plan)
```

Machine report schema:

```text
contextos.construction.plan/1
```

The plan turns existing Context Readiness, Repository Inventory, Validator, and
Bootstrap Plan evidence into reviewable construction candidates. It preserves
the canonical lifecycle:

```text
observed -> inferred -> suggested -> draft -> reviewed -> approved -> canonical/verified
```

This slice stops at observed evidence and suggested draft/review actions. It
does not create drafts, approve context, or promote organizational truth.
