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
    reasoning_evidence=exact_claims_and_relationships,
    focus_entities=["mission.current"],
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
- Explicit claims may be compared only across matching scope and temporal
  basis. Declared impact relationships may be traversed up to three hops with
  every edge cited; this is not an authoritative graph.

## Tests

```bash
python3 tools/reasoning/test_contextual_assessment.py
python3 tools/reasoning/test_reasoning_benchmark.py
python3 tools/reasoning/test_structured_reasoning_evidence.py
```

The controlled benchmark uses `contextos.reasoning.benchmark/1` to measure all
required v0.9 reasoning classes. Expected gaps remain failed cases; the
benchmark never repairs an Assessment or grants authority to add infrastructure.
