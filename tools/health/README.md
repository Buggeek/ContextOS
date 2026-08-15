# Context OS Health Tools

This folder contains the first Release v0.7 Context Health & Learning
capability.

`ContextHealthEngine` produces a read-only, evidence-first report:

```text
contextos.health.report/1
```

Public API:

```python
from health_engine.health_engine import ContextHealthEngine
from health_engine.report_builder import render_human

report = ContextHealthEngine(".").run()
human = render_human(report)
```

The report combines existing Validator, Readiness, Mission, Activation, and
Evolution Inbox evidence into three explainable dimensions:

- Context Integrity: structural and epistemic trustworthiness.
- Context Usefulness: evidence that activated context supported real Missions.
- Organizational Learning: observations that may justify governed evolution.

The first report deliberately has no aggregate numerical health score. It uses
observable signals with `healthy`, `attention`, `blocked`, or `unknown` status.

Context update candidates are `suggested`, non-canonical objects. They cannot
write or promote context. Any accepted candidate must enter the existing
Context Construction lifecycle:

```text
Evidence -> Construction Candidate -> Draft -> Review -> Approval
-> Promotion -> Canonical Validation
```

This slice does not add a CLI, automatic mutation, a second Construction
lifecycle, Knowledge Engine reasoning, Context Graph runtime, agents, external
connectors, broad RAG, or trend scoring without prior report evidence.
