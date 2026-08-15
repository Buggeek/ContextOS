# E.4 Mission V07-CONTEXT-HEALTH-PLAN-001 - Context Health and Learning
## Version: 0.1.0
Last Updated: 2026-08-15
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Begin v0.7 by establishing the minimum governed capability that measures
Context Integrity, Context Usefulness, and Organizational Learning without
silently changing canonical truth.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V07-CONTEXT-HEALTH-PLAN-001
  title: Context Health and Learning
  initiating_lifecycle: release
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed:done
  created_at: 2026-08-15
```

---

## Release

v0.7 - Context Health & Learning

---

## Decision

Context Health & Learning is one evidence-first observation and recommendation
capability with three dimensions:

- Context Integrity,
- Context Usefulness,
- Organizational Learning.

These dimensions do not require separate engines. The initial capability is a
read-only Health Report with no numerical health score.

---

## Capability Delivered

Implemented `ContextHealthEngine` and:

```text
contextos.health.report/1
```

The report:

- reuses Validator and Readiness reports,
- observes closed Mission and Activation evidence,
- observes Evolution Inbox learning capture,
- reports `healthy`, `attention`, `blocked`, or `unknown` signals,
- preserves evidence references and belief boundaries,
- emits stable, non-canonical Context Update Candidates,
- routes candidates to the existing Context Construction lifecycle,
- remains fully read-only.

No CLI, Graph, Knowledge Engine, agent, connector, broad RAG, dashboard, or
automatic mutation capability was added.

---

## Health Model

| Dimension | Meaning | First evidence sources |
|---|---|---|
| Context Integrity | Structural and epistemic trustworthiness | Validator, Readiness, ownership evidence |
| Context Usefulness | Whether activated context supported bounded Mission work | Activation Missions, drift/invalidation evidence, Execution Context evidence |
| Organizational Learning | What execution captured for governed evolution | Mission Learning sections, Evolution Inbox, Construction route |

An unknown signal prevents a dimension from being labeled healthy. This is
especially important when narrative evidence cannot prove actual use or
effectiveness.

---

## Learning Boundary

The canonical loop is:

```text
Execution Evidence
-> Health Observation
-> Learning Candidate
-> Context Update Candidate
-> Human/Governed Review
-> Existing Context Construction Lifecycle
-> Canonical Validation
```

Health may recommend. It cannot write, approve, promote, or canonicalize.

---

## Authority

| Actor | Authority | Boundary |
|---|---|---|
| Context OS Maintainers | Mission authority | v0.7 first capability |
| Codex | L3 bounded implementation | engine, report, tests, contract, Mission evidence |
| ContextHealthEngine | L1 suggest | read evidence, report signals, suggest candidates |
| Human reviewer | future decision authority | candidate admission into Construction |

No authority for canonical mutation or automatic remediation was granted.

---

## Self-Hosting Findings

This Mission began from a valid package-backed Activation Handoff:

```text
package: activation.package.c35b221b83120671
handoff: activation.handoff.e96ce114eb99fd96
package_check: valid
handoff_check: valid
```

The package supplied GENESIS, active roadmap, product/system maps, readiness and
done criteria, Activation contract, self-hosting Mission evidence, and Runtime
strategy as Governing Context. Execution Context was then bounded to the
Validator/Readiness/Discovery/Activation implementations, Mission evidence,
Construction lifecycle, tests, and directly updated canonical artifacts.

The initial package and handoff became stale when this Mission changed selected
canonical sources. That is expected v0.6 behavior; a fresh package is required
before the next Mission uses the updated state.

The initial Context OS dogfood report observed:

- 0 blocking Validator findings,
- 153 Validator warnings across 7 rule groups,
- ownership warnings requiring attention,
- 2 explainable Readiness caps,
- 31 closed Mission artifacts,
- 27 closed Missions with explicit Learning sections,
- 8 closed v0.6 Activation Mission artifacts,
- drift/invalidation evidence in 24 closed Missions,
- bounded Execution Context discussion in 5 closed Missions,
- 80 Evolution Inbox observations across 8 categories,
- no machine-verifiable per-source selected-versus-used evidence.

The result is not a score. It is an explainable current-state report:

- Integrity: attention,
- Usefulness: unknown because source use remains narrative,
- Learning: healthy evidence capture,
- Overall: attention,
- Context Update Candidates: 3.

---

## Context Update Candidates

The dogfood report suggested:

1. review recurring Validator warning groups,
2. review Readiness caps for ownership and runtime manifest,
3. structure selected-versus-used Activation evidence before claiming trends or
   effectiveness.

All candidates remain `suggested`, `canonical: false`, and promotion-prohibited
inside the Health capability.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Runtime engine | `tools/health/health_engine/health_engine.py` |
| Human report | `tools/health/health_engine/report_builder.py` |
| Machine schema | `contextos.health.report/1` |
| Contract | `1.5.10_Context_Health_Report_Contract.md` |
| Focused tests | 7 passed |
| Read-only snapshot | passed |
| Determinism with fixed time | passed |
| Blocking integrity fixture | passed |
| Missing-usefulness evidence fixture | remains `unknown` |
| Candidate truth boundary | suggested, non-canonical, Construction-routed |
| Dogfood JSON | parseable |

---

## Learning

- Integrity, usefulness, and learning are dimensions of one Health capability,
  not independent engines.
- Existing evidence already reveals meaningful organizational health signals.
- Narrative Mission evidence is sufficient to discover patterns but not to
  prove per-source use or causal effectiveness.
- Health needs explicit historical evidence before it can claim improvement or
  degradation over time.
- The existing Construction lifecycle is the correct governance path for every
  accepted context update candidate.

---

## Evolution Impact

The first v0.7 capability is established. The next dependency is structured,
read-only Mission-use evidence, not a dashboard, score, Graph, or Knowledge
Engine.

---

## Next Mission Recommended

```text
V07-CONTEXT-USE-EVIDENCE-001
```

Define the minimum read-only evidence object for what activated context was
selected, actually used, additionally retrieved, missing, stale, or irrelevant
during a Mission so Health can measure usefulness without inference.

---

## Change Log

- 2026-08-15 - v0.1.0 - Implemented and dogfooded the first Context Health &
  Learning capability.
