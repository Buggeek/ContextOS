# Context OS Readiness Tools

This folder contains small runtime components that support Release v0.3
Context Readiness.

The first implemented slices are intentionally narrow:

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

## Readiness Scoring

Public API:

```python
from readiness_engine.readiness_scoring import ReadinessScoringEngine

report = ReadinessScoringEngine(".").run()
```

Machine report schema:

```text
contextos.readiness.report/1
```

The Slice 2 report contains:

- overall readiness score
- R0-R5 readiness level
- dimension scores for `inventory`, `structure`, `governance`,
  `operational_map`, `runtime`, and `source_evidence`
- signals, gaps, and evidence references for each dimension
- embedded inventory summary
- embedded validator summary

Recommendations and the `contextos assess` CLI are deliberately deferred.
