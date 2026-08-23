# Context OS Organizational Memory

`tools/memory` provides the first read-only Organizational Memory runtime.

## Public API

```python
from memory_engine import MemoryRetrievalEngine, OrganizationalMemoryEngine, RetentionResolutionEngine
from memory_engine.report_builder import render_human

report = OrganizationalMemoryEngine(".").run(
    mission_id="V08-ORGANIZATIONAL-MEMORY-PLAN-001",
    goal="Preserve continuity across Missions, decisions, evidence, outcomes, and learning.",
)
print(render_human(report))

retrieval = MemoryRetrievalEngine(".").run(
    goal="Use prior Organizational Memory to inform a bounded Mission.",
    mission_id="V08-MEMORY-RETRIEVAL-SURFACE-001",
    consumer="human",
    purpose="Review prior decisions for this Mission.",
    organizational_mode="project",
    actor_roles=["project_owner"],
    authority_scope="project:context-os",
    retention_policies=retention_policies,
    memory_metadata_by_id=memory_metadata,
)

resolution = RetentionResolutionEngine(".").run(
    memory_item,
    retention_policies,
    consumer="memory_retrieval",
)
```

Machine schemas:

- `contextos.memory.continuity_report/1`
- `contextos.memory.retrieval_result/1`
- `contextos.memory.retrieval_check/1`
- `contextos.memory.retention_policy/1` (input)
- `contextos.memory.retention_resolution/1`
- `contextos.memory.retention_resolution_check/1`

## CLI

```bash
./contextos memory --goal "Retrieve relevant prior art" --mission-id MISSION-ID
./contextos memory --goal "Retrieve relevant prior art" --format json
./contextos memory --goal "Retrieve relevant prior art" \
  --purpose "Review prior Mission evidence" \
  --organizational-mode project \
  --actor-role project_owner \
  --authority-scope project:context-os \
  --retention-policy policy.json \
  --memory-metadata memory-metadata.json
./contextos memory --check-retrieval retrieval.json \
  --retention-policy policy.json \
  --memory-metadata memory-metadata.json
```

## Boundary

- The report is a derived, read-only continuity view. It is not SSOT.
- Mission, decision, evidence, outcome, learning, and context-state memory remain distinct forms.
- Current, historical, superseded, remembered, canonical, and useful are not synonyms.
- Prior-art relevance is deterministic and explainable, but remains a derived hypothesis.
- Relevant candidates are evaluated by `RetentionResolutionEngine` before any
  candidate-specific Retrieval metadata is exposed.
- Access, Retrieval, and Activation remain independent. Exposure requires
  normal access, normal Retrieval, and sufficient metadata visibility;
  `elevated_authority`, `excluded`, `prohibited`, and `unknown` do not expose a
  candidate. No applicable policy means `unknown`, never allowed.
- Restricted outcomes use metadata-safe explanations; protected identities,
  titles, paths, snippets, hashes, and evidence references are withheld.
- Retrieval eligibility does not imply visibility or Activation eligibility,
  and retrieved memory is never added automatically to Governing Context.
- Pattern candidates remain suggested hypotheses until governed review and Context Construction.
- Missing time, supersession, usefulness, and retention evidence remains explicit.
- Retention Resolution evaluates supplied explicit policy independently for
  access, Retrieval, Activation, retention transition, and destructive action.
- Resolution grants no authority, performs no legal interpretation, and never
  changes memory, access, retention state, holds, or canonical context.
- Missing policy, unknown applicability, source drift, holds, and conflicting
  preservation/removal duties remain explicit and cannot become permission.
- No storage service, embedding, vector database, GraphRAG, Context Graph Runtime, Knowledge Engine, agent, or deletion behavior is introduced.

## Tests

```bash
python3 tools/memory/test_memory_continuity.py
python3 tools/memory/test_memory_retrieval.py
python3 tools/memory/test_memory_retrieval_policy.py
python3 tools/memory/test_memory_retention_resolution.py
```
