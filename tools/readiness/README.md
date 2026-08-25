# Context OS Readiness Tools

This folder contains small runtime components that support Release v0.3
Context Readiness.

The implemented v0.3 slices are intentionally narrow:

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
from readiness_engine.report_builder import render_human

report = ReadinessScoringEngine(".").run()
human = render_human(report)
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
- recommendations using stable `readiness.<category>.<action>` IDs
- a human-readable report renderer

CLI surface:

```bash
./contextos assess --root .
./contextos assess --root . --format json
./contextos assess --root . --json-out /tmp/contextos-readiness-report.json
```

`contextos assess` is read-only and emits `contextos.readiness.report/1`.

`--adoption-profile <profile.json>` evaluates mapped organizational capability
equivalence rather than requiring Context OS-native directories or filenames.
