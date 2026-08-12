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

Package-backed handoff schema:

```text
contextos.activation.handoff/1
```

Handoff check schema:

```text
contextos.activation.handoff_check/1
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

Generate a compact package-backed handoff from a checked package:

```bash
./contextos activate \
  --root . \
  --check-package /tmp/contextos-activation-package.json \
  --handoff
```

Check a saved handoff before use:

```bash
./contextos activate \
  --root . \
  --check-handoff /tmp/contextos-activation-handoff.json \
  --format json
```

The handoff check validates handoff identity, selected source hashes, Validator
gate status, and package binding when the handoff has a package file reference.
It does not regenerate context selection.

Generate a fresh package and immediately render its handoff:

```bash
./contextos activate \
  --root . \
  --goal "Plan the next mission" \
  --consumer codex \
  --mission-id V06-ACTIVATION-HANDOFF-FORMAT-001 \
  --handoff
```

The handoff is a compact operating brief. It preserves the exact package id and
hash, selected canonical sources, exclusions, gaps, permissions, provenance,
freshness, invalidation conditions, and Mission evidence obligations without
duplicating full canonical content.

It also carries a single Mission Context model:

- **Governing Context** is selected at activation time and orients the consumer
  to outcome, authority, constraints, source authority, gaps, and evidence.
- **Execution Context** is not selected broadly at activation time. It is
  retrieved only when the Mission objectively requires additional material such
  as code, tests, interfaces, operational records, or domain assets.

Each retrieved execution source should be recorded in Mission evidence with the
reason, authority, usage, evidence role, and staleness condition.

Exit codes:

- `0` when the package is generated, checked successfully, a handoff is ready,
  or a handoff check is valid,
- `7` when activation is blocked, an existing package is invalidated, a handoff
  is not ready, or a handoff check is invalidated,
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

## Package-Backed Handoff

A handoff lets a human, Codex, Claude Code, IDE assistant, or future
organizational consumer begin from a package reference rather than a manually
reconstructed prompt.

It answers:

- what the consumer is trying to achieve,
- which package and canonical sources govern the work,
- what the consumer may and may not do,
- where exact selected context lives,
- which gaps, exclusions, and invalidation conditions apply,
- what evidence and exit conditions must be captured.

The handoff remains consumer-agnostic. Future adapters may render the same
machine report for specific tools, but they must not weaken the package
authority boundary or turn the handoff into a parallel SSOT.

The handoff does not create a second Mission model. Governing and execution
context remain layers of one package-backed Mission Context.
