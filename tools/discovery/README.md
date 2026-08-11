# Context OS Discovery Tools

This folder contains the first Release v0.5 Discovery capability.

Slice 1 implements **Local Discovery Bundle** only:

- no Runtime CLI integration
- no external connectors
- no source registry
- no semantic generation
- no Knowledge Engine
- no Context Graph runtime
- no agents
- no writes to target repositories

Public API:

```python
from discovery_engine.local_discovery import LocalDiscoveryBundleEngine
from discovery_engine.report_builder import render_human

bundle = LocalDiscoveryBundleEngine(".").run()
human = render_human(bundle)
```

Machine report schema:

```text
contextos.discovery.bundle/1
```

The bundle captures local repository evidence:

- source identity and fingerprint
- discovered artifacts
- paths and observable metadata
- inferred path-based classifications
- directly observed ownership fields
- filesystem containment relationships
- literal local markdown references
- provenance and limitations

The bundle preserves this boundary:

- observed evidence is evidence of existence or literal text;
- inferred classification is path/name-derived and not organizational truth;
- unknown information remains explicit;
- no context is promoted to canonical truth.
