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

`MissionContextUseEvidenceEngine` produces the read-only input:

```text
contextos.mission.context_use_evidence/1
```

```python
from health_engine.mission_use_evidence import MissionContextUseEvidenceEngine

evidence = MissionContextUseEvidenceEngine(".").run(
    package=package,
    handoff=handoff,
    selected_accesses=selected_accesses,
    execution_retrievals=execution_retrievals,
)
report = ContextHealthEngine(".").run(mission_use_evidence=evidence)
```

Runtime CLI:

```bash
./contextos health --root .
./contextos health --root . --format json
./contextos health --root . --mission-use-evidence <mission-use.json>
./contextos health --root . --json-out <health-report.json>
```

The default human report starts with dimension status and prioritized
attention, blocking, and unknown signals. It preserves evidence references and
belief state, then shows governed Context Update Candidates, observability
limits, and why no automatic mutation occurred. JSON stdout is the pure
`contextos.health.report/1` object.

The object binds an exact package, handoff, Mission, and consumer to explicit
observed, declared, derived, or unknown evidence. It never treats selection as
retrieval, retrieval as consumption, consumption as use, or use as usefulness.
Missing access evidence remains unknown rather than becoming an `unused` claim.

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

This slice does not add telemetry, surveillance monitoring, automatic mutation,
a second Construction lifecycle, remediation execution, Knowledge Engine
reasoning, Context Graph runtime, agents, external connectors, broad RAG, or
trend scoring without prior report evidence.
