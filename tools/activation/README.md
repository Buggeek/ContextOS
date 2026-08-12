# Context OS Activation Tools

This folder contains the first Release v0.6 Context Activation capability.

Slice 1 implements a read-only **Context Activation Package**.

Public API:

```python
from activation_engine.package_engine import ContextActivationPackageEngine
from activation_engine.report_builder import render_human

package = ContextActivationPackageEngine(".").run(
    goal="Plan the next activation mission",
    consumer="codex",
    mission_id="V06-CONTEXT-ACTIVATION-PLAN-001",
)
human = render_human(package)
```

Machine report schema:

```text
contextos.activation.package/1
```

The package turns canonical Context OS sources into mission-bound working
context for a consumer. It preserves:

- canonical source authority,
- source paths and hashes,
- package identity,
- goal/mission binding,
- consumer permissions,
- provenance,
- freshness and invalidation conditions,
- context gaps,
- Validator gate evidence.

The package is not SSOT. It may contain derived excerpts ordered for a mission
or consumer, but canonical source artifacts remain authoritative.

This slice does not implement:

- `contextos activate`,
- IDE adapters,
- autonomous agents,
- Context Graph runtime,
- broad RAG,
- Knowledge Engine expansion,
- background synchronization,
- automatic context mutation,
- parallel SSOT copies.
