# Context OS Organizational Memory

`tools/memory` provides the first read-only Organizational Memory runtime.

## Public API

```python
from memory_engine import OrganizationalMemoryEngine
from memory_engine.report_builder import render_human

report = OrganizationalMemoryEngine(".").run(
    mission_id="V08-ORGANIZATIONAL-MEMORY-PLAN-001",
    goal="Preserve continuity across Missions, decisions, evidence, outcomes, and learning.",
)
print(render_human(report))
```

The machine report schema is `contextos.memory.continuity_report/1`.

## Boundary

- The report is a derived, read-only continuity view. It is not SSOT.
- Mission, decision, evidence, outcome, learning, and context-state memory remain distinct forms.
- Current, historical, superseded, remembered, canonical, and useful are not synonyms.
- Prior-art relevance is deterministic and explainable, but remains a derived hypothesis.
- Pattern candidates remain suggested hypotheses until governed review and Context Construction.
- Missing time, supersession, usefulness, and retention evidence remains explicit.
- No storage service, embedding, vector database, GraphRAG, Context Graph Runtime, Knowledge Engine, agent, or deletion behavior is introduced.

## Tests

```bash
python3 tools/memory/test_memory_continuity.py
```
