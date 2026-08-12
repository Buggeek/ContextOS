# E.4 Mission V06-ACTIVATION-CONTEXT-LAYERS-001 - Mission Context Layers
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Determine whether Context Activation requires an explicit distinction between
Governing Context and Execution Context, and implement the minimum coherent
model only if evidence from package-first and handoff-first execution
demonstrates necessity.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V06-ACTIVATION-CONTEXT-LAYERS-001
  title: Mission Context Layers
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

## Decision

Accepted, with one constraint:

Context OS should distinguish Governing Context and Execution Context as layers
inside one coherent Mission Context.

The distinction should not create:

- a second SSOT,
- a second Mission identity,
- a second activation package family,
- broad repository search,
- an execution-specific runtime branch.

---

## Canonical Mission Context Model

```text
Mission Context
├─ Governing Context
└─ Execution Context
```

Governing Context is selected at activation time.

Execution Context is retrieved only when execution requires it.

Both layers preserve the same Mission identity, consumer binding, authority
model, source provenance, freshness rules, invalidation behavior, and evidence
obligations.

---

## Governing Context

Governing Context tells an actor:

- what outcome is intended,
- why it matters,
- which canonical context governs the work,
- what authority exists,
- what constraints apply,
- what gaps exist,
- what evidence defines completion.

In this Mission, Governing Context came from the Activation Handoff and was
sufficient for orientation.

---

## Execution Context

Execution Context provides bounded material objectively required to perform the
Mission.

In software missions this may include code, runtime state, tests, interfaces,
and operational dependencies.

In other organizational domains this may include campaign assets, account
records, tickets, financial records, contracts, employee/process records,
operational telemetry, research material, or customer records.

Execution Context is not selected broadly by default. Each retrieved source must
be explainable.

---

## Bounded Retrieval Model

Every additional execution source should record:

- why it was required,
- what Mission need justified retrieval,
- what authority permitted access,
- whether it was actually used,
- whether it became part of evidence,
- when it becomes stale.

The initial runtime representation records an empty `retrieved_sources` list and
a retrieval policy inside `contextos.activation.handoff/1`. Mission evidence is
responsible for recording actual retrievals.

---

## Capability Delivered

Updated Activation Handoff reports to include:

```text
mission_context.model = single_mission_context_with_governing_and_execution_layers
```

The model contains:

- `governing_context`,
- `execution_context`,
- `irrelevant_context`.

The handoff check includes this model in handoff identity, so changing the
context-layer contract invalidates saved handoffs rather than silently changing
their meaning.

---

## Dogfood Evidence

Initial package and handoff were generated for:

```text
V06-ACTIVATION-CONTEXT-LAYERS-001
```

Initial state:

```text
handoff_ready=true
handoff_check_valid=true
```

Selected Governing Context:

- active roadmap,
- repository entrypoint,
- GENESIS,
- system/product/vision SSOT,
- Definition of Ready,
- Definition of Done,
- recent v0.6 package/handoff Mission evidence.

Execution Context additionally retrieved:

- `tools/activation/activation_engine/package_engine.py`,
- `tools/activation/activation_engine/report_builder.py`,
- `tools/activation/test_activation_package.py`,
- activation contract,
- activation README,
- roadmap/product/system maps,
- Evolution Inbox.

Reason:

The handoff oriented the Mission, but implementation required exact runtime,
test, and documentation files.

---

## Irrelevant Context Avoided

This Mission did not require:

- Context Graph runtime,
- Knowledge Engine expansion,
- autonomous agent orchestration,
- broad RAG,
- IDE-specific adapters,
- background synchronization,
- v0.3 readiness internals beyond regression execution,
- v0.4 bootstrap internals beyond regression execution,
- v0.5 construction internals beyond regression execution,
- external connectors.

---

## Context Sufficiency Observation

Governing Context was sufficient for orientation.

Execution Context retrieval remained bounded and explainable.

The combined context was sufficient to complete the Mission.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Governing/Execution layer decision | accepted inside one Mission Context |
| Handoff schema updated | `mission_context` added |
| Execution retrieval broad search | not introduced |
| Handoff identity includes context model | yes |
| Human handoff report names layers | yes |
| Runtime mutation | none |
| Future-release scope | not introduced |

---

## Learning

Context Activation should optimize for Minimum Sufficient Context:

- Governing Context should orient the actor.
- Execution Context should be retrieved only when execution requires it.
- Irrelevant Context should remain excluded unless evidence proves otherwise.

This is not software-specific. Technology is only the first operating domain.

---

## Evolution Impact

The two-layer model should be used by future activation work and release
verification. Adapter-specific packaging, Graph-backed retrieval, Knowledge
Engine ranking, and background synchronization remain deferred.

---

## Next Mission Recommended

```text
V06-CONTEXT-ACTIVATION-RELEASE-VERIFY-001
```

Verify v0.6 end to end across package generation, package check, handoff,
handoff check, Mission Context layers, invalidation, and handoff-first
execution.
