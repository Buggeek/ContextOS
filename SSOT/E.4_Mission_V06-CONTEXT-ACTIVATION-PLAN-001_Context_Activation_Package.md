# E.4 Mission V06-CONTEXT-ACTIVATION-PLAN-001 - Context Activation Package
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Begin Release v0.6 Context Activation by establishing the first governed
working-context capability.

This mission answers:

> How should Context OS activate canonical context into a working surface so an
> actor can use the right context for a specific goal or mission without
> manually reconstructing it?

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V06-CONTEXT-ACTIVATION-PLAN-001
  title: Context Activation Package
  initiating_lifecycle: release
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed:done
  created_at: 2026-08-11
```

---

## Release

v0.6 - Context Activation

---

## Capability

Added `ContextActivationPackageEngine`, a read-only package engine that emits:

```text
contextos.activation.package/1
```

The package turns canonical Context OS sources into mission-bound working
context for a declared consumer.

Public API:

```python
from activation_engine.package_engine import ContextActivationPackageEngine

package = ContextActivationPackageEngine(".").run(
    goal="Define the next activation mission",
    consumer="codex",
    mission_id="V06-CONTEXT-ACTIVATION-PLAN-001",
)
```

---

## Context Activation Definition

Context Activation is governed delivery of canonical context into a working
surface.

Activation does not create truth. It selects, packages, orders, and explains
context for a consumer while preserving source authority, provenance, freshness,
permissions, and invalidation conditions.

The v0.6 activation primitive is:

```text
Canonical Context
-> Activation Selection
-> Working Context Package
-> Consumer
-> Execution
-> Evidence / Feedback
-> Context Update Candidate
```

This mission implements the first three stages only.

---

## Canonical vs Working Context Boundary

The package preserves this boundary:

| Context Type | Meaning |
|---|---|
| Canonical Context | Source artifacts under canonical authority, primarily SSOT, architecture, governance, runtime contracts, and strategy |
| Working Context Package | Derived, mission-bound context for a consumer; may include excerpts, ordering, and relevance selection |

The Working Context Package:

- is not SSOT,
- must not silently become canonical truth,
- must be invalidated when source hashes or gates change,
- must preserve source paths and hashes,
- must preserve consumer permissions and prohibited actions,
- must expose gaps and validator gate status.

---

## Package Model

The package contains:

- package id and identity hash,
- goal and optional mission id,
- consumer and permission boundary,
- included canonical source artifacts,
- excluded relevant artifacts,
- source hashes,
- source fingerprint,
- bounded working-context excerpts,
- freshness metadata,
- context gaps,
- Validator gate summary,
- provenance and evidence lineage,
- invalidation conditions,
- constraints proving no mutation or parallel SSOT creation.

---

## Consumer Model

Consumers are declared as strings in v0.6 Slice 1:

- `human`,
- `codex`,
- `claude_code`,
- `ide_assistant`,
- `cli_tool`,
- future organizational surfaces.

The model is intentionally consumer-agnostic. It grants only:

```text
read_canonical_context
use_working_context
```

It prohibits:

```text
mutate_canonical_context
promote_context
delegate_authority
```

---

## Provenance, Freshness, and Invalidation

Every included artifact records:

- source path,
- source hash,
- authority tier,
- lifecycle state,
- activation role,
- owner when directly observed,
- bounded excerpt,
- provenance block.

The package is invalidated by:

- any included source hash change,
- Validator gate errors or fatals,
- goal, mission id, consumer, or permission changes,
- authority tier or lifecycle-state changes.

---

## Authority Boundary

This mission is read-only.

No human authority beyond bounded implementation authority is required because
the package does not mutate source context, create canonical context, invoke
agents, or activate external tools.

Future CLI/adapters must preserve the same package identity and invalidation
model before they perform any surface-specific activation.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Runtime implementation | `tools/activation/activation_engine/package_engine.py` |
| Machine schema | `contextos.activation.package/1` |
| Human report | `tools/activation/activation_engine/report_builder.py` |
| README | `tools/activation/README.md` |
| Activation tests | `python3 tools/activation/test_activation_package.py` passed |
| Dogfood | Context OS generated an activation package for `V06-CONTEXT-ACTIVATION-PLAN-001` |
| Validator gate | Package dogfood used Validator gate with error=0 and fatal=0 |
| Regression tests | Validator, CLI, release verification, Discovery, Construction, and Builder tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Read-only guarantee | Activation tests snapshot files before/after and report no writes |
| Whitespace validation | `git diff --check` passed |

---

## Decision

The first v0.6 capability is a read-only Context Activation Package, not
`contextos activate`, IDE integration, agent orchestration, or Context Graph.

This is the smallest universal activation primitive that creates real value:
actors can consume mission-bound canonical context without manually rebuilding
the context bundle and without creating a second SSOT.

---

## Learning

- Activation should start with context delivery, not adapters.
- Mission-bound packages give humans and agents useful working context while
  preserving canonical authority.
- The package selection algorithm should remain simple until real activation
  usage produces evidence for more advanced selection strategies.
- Technology can be the first operating domain while the package model remains
  usable for Strategy, Product, Marketing, Sales, Finance, Legal, People,
  Operations, Research, Data, and Customer Success.

---

## Next Mission Recommended

```text
V06-ACTIVATION-PACKAGE-CLI-001
```

Expose the read-only activation package through a narrow Runtime CLI surface
without adding adapters, agents, Graph runtime, or mutation.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the first v0.6 Context Activation
  mission.
