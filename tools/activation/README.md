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

## Runtime CLI Surface

Slice `V06-ACTIVATION-PACKAGE-CLI-001` exposes the package through:

```bash
./contextos activate \
  --root . \
  --goal "Plan the next mission" \
  --consumer codex \
  --mission-id V06-ACTIVATION-PACKAGE-CLI-001
```

Machine output:

```bash
./contextos activate --root . --goal "Plan the next mission" --format json
```

Persist the machine package:

```bash
./contextos activate \
  --root . \
  --goal "Plan the next mission" \
  --json-out /tmp/contextos-activation-package.json
```

Check a package for drift/invalidation:

```bash
./contextos activate \
  --root . \
  --check-package /tmp/contextos-activation-package.json \
  --format json
```

Package checks emit:

```text
contextos.activation.package_check/1
```

Exit codes:

- `0` when the package is generated or checked successfully,
- `7` when activation is blocked or an existing package is invalidated,
- `9` for CLI/configuration errors.

## Package-First Mission Use

A self-hosted Mission may begin from an Activation Package instead of a long
manual source list when it follows this sequence:

1. Generate or resolve the package for the exact Mission.
2. Run `./contextos activate --check-package <package.json>`.
3. Use the package's selected sources, constraints, gaps, exclusions, and
   provenance as working context.
4. Fetch additional repository context only when the package identifies a gap or
   the Mission objectively requires exact file content for an edit.
5. Record the package id, identity hash, selected sources, additional context,
   and validation evidence in the Mission Packet.
6. Treat source changes during the Mission as invalidating the package; generate
   and check a fresh package before continuing from the changed context.

The package is authoritative for the Mission's working context, not a second
SSOT.
