# Context OS Bootstrap Tools

This folder contains read-only bootstrap planning components for Release v0.4
Guided Bootstrap.

Slice 1 implements **Bootstrap Planning** only:

- no `contextos init`
- no CLI integration
- no apply mode
- no manifest creation
- no SSOT, governance, or scaffold writes

Public API:

```python
from bootstrap_engine.plan_engine import BootstrapPlanEngine
from bootstrap_engine.report_builder import render_human

plan = BootstrapPlanEngine(".").run()
human = render_human(plan)
```

Machine report schema:

```text
contextos.bootstrap.plan/1
```

The plan explains required, skipped, blocked, and manual future bootstrap
actions. It is designed to be consumed by later v0.4 apply/CLI slices.
