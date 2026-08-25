# Context OS Contextual Reasoning

`tools/reasoning` provides the first governed, read-only Contextual Reasoning
runtime primitive.

## Public API

```python
from reasoning_engine import ContextualAssessmentEngine

report = ContextualAssessmentEngine(".").run(
    goal="Determine what organizational context requires attention and what should be considered next.",
    mission_id="MISSION-ID",
    consumer="human",
    context_versions=[current_context_version],
    retention_policies=authorized_policies,
    memory_metadata_by_id=authorized_metadata,
)
```

Machine schema:

```text
contextos.reasoning.assessment/1
```

## Boundary

- The Assessment composes structured Activation, Health, Memory, and Context
  Version evidence. It does not freely reinterpret canonical source content.
- Evidence, observation, interpretation, hypothesis, recommendation, Decision,
  authority, and canonical truth remain distinct.
- Historical context and retrieved Memory never regain current authority.
- Missing or policy-withheld evidence remains unknown.
- No artificial percentage confidence is assigned.
- The engine is deterministic for fixed inputs, read-only, and stdlib-only.
- It does not use GraphRAG, embeddings, vectors, broad RAG, agents, external
  connectors, or autonomous execution.

## Tests

```bash
python3 tools/reasoning/test_contextual_assessment.py
```
