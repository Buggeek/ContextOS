# Context OS Organizational Memory

`--adoption-profile` maps target-native Mission, closure, evidence, learning,
and workstream-memory sources into continuity candidates. Mapping establishes
relevance only; Retention Resolution still runs before exposure.

`tools/memory` provides the first read-only Organizational Memory runtime.

## Public API

```python
from memory_engine import ContextVersionEngine, MemoryRetrievalEngine, OrganizationalMemoryEngine, RetentionResolutionEngine
from memory_engine.report_builder import render_human

report = OrganizationalMemoryEngine(".").run(
    mission_id="V08-ORGANIZATIONAL-MEMORY-PLAN-001",
    goal="Preserve continuity across Missions, decisions, evidence, outcomes, and learning.",
    context_versions=[preserved_context_version],
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
    context_versions=[preserved_context_version],
)

resolution = RetentionResolutionEngine(".").run(
    memory_item,
    retention_policies,
    consumer="memory_retrieval",
)

version_engine = ContextVersionEngine(".")
plan = version_engine.plan(
    scope={"organization": "example", "domain": "product", "tier": "organizational", "context_root": "canonical"},
    event_type="mission_start",
    reason="Freeze governed context for a bounded Mission.",
    capture_at="2026-08-23T00:00:00Z",
    mission_id="MISSION-ID",
    goal="Execute the Mission from exact governed context.",
)
plan_check = version_engine.check_plan(plan)
version = version_engine.capture(plan)
version_check = version_engine.check_version(version)
```

Machine schemas:

- `contextos.memory.continuity_report/1`
- `contextos.memory.retrieval_result/1`
- `contextos.memory.retrieval_check/1`
- `contextos.memory.retention_policy/1` (input)
- `contextos.memory.retention_resolution/1`
- `contextos.memory.retention_resolution_check/1`
- `contextos.context.version_capture_plan/1`
- `contextos.context.version_capture_plan_check/1`
- `contextos.context.version/1`
- `contextos.context.version_check/1`

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
  --memory-metadata memory-metadata.json \
  --context-version preserved-version.json
./contextos memory --check-retrieval retrieval.json \
  --retention-policy policy.json \
  --memory-metadata memory-metadata.json \
  --context-version preserved-version.json
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
- A Context Version is an immutable, content-free identity and provenance
  record for governed context at a meaningful event. It is not a context copy,
  Activation Package, Git commit, Retrieval result, or source of authority.
- Context Version planning, capture, and checks are read-only. Persistence,
  automatic capture, semantic historical comparison, and version registries
  remain outside this primitive.
- Continuity accepts exact preserved Context Version objects and reports exact,
  partial, or unknown Mission bindings without retrospective fabrication.
- Retrieval evaluates Context Version metadata independently before exposing
  identity or lineage. Historical evidence grants no current authority and
  semantic applicability remains `not_evaluated`.

## Tests

```bash
python3 tools/memory/test_memory_continuity.py
python3 tools/memory/test_memory_retrieval.py
python3 tools/memory/test_memory_retrieval_policy.py
python3 tools/memory/test_memory_retention_resolution.py
python3 tools/memory/test_context_version.py
python3 tools/memory/test_memory_context_version_integration.py
python3 tools/memory/test_organizational_memory_release_verify.py
```
