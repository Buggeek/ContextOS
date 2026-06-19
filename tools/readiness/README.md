# Context OS Readiness Tools

This folder contains small runtime components that support Release v0.3
Context Readiness.

The first implemented slice is **Repository Inventory**. It is intentionally
narrow:

- no readiness scoring
- no readiness levels
- no recommendations
- no `contextos assess`
- no Builder, Knowledge Engine, Graph, or agents

## Repository Inventory

Public API:

```python
from inventory_engine.repository_inventory import RepositoryInventoryEngine

report = RepositoryInventoryEngine(".").run()
```

Local report command:

```bash
python3 tools/readiness/contextos_inventory.py --root . --format json
```

Machine report schema:

```text
contextos.inventory.report/1
```

Required top-level fields:

- `schema`
- `generated_at`
- `root`
- `summary`
- `detected`

The `detected` object contains:

- `artifacts`
- `taxonomy_classes`
- `runtime_artifacts`
- `governance_artifacts`
- `roadmap_artifacts`

This report is designed to be embedded later inside
`contextos.readiness.report/1`.
