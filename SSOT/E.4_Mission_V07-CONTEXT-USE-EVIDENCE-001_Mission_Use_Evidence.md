# E.4 Mission V07-CONTEXT-USE-EVIDENCE-001 - Mission-Use Evidence
## Version: 0.1.0
Last Updated: 2026-08-16
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Establish the minimum governed evidence required for Context OS to observe how
context participates in a real Mission without inferring usefulness.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V07-CONTEXT-USE-EVIDENCE-001
  title: Mission-Use Evidence
  release: v0.7-context-health-and-learning
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed:done
  authority: read_and_implement_non_mutating_health_evidence
  created_at: 2026-08-16
```

Exit conditions required a read-only evidence object, exact Activation
bindings, explicit evidence semantics, Health integration, dogfood evidence,
regression proof, learning capture, and no inferred usefulness.

---

## Governing Activation Context

The Mission began from the valid Handoff:

```text
activation.handoff.078950fb776dfcdf
```

bound to:

```text
activation.package.b4c40452ebca420d
V07-CONTEXT-USE-EVIDENCE-001
consumer=codex
```

The package and Handoff passed identity, source-hash, package-binding, and
Validator checks before implementation.

---

## Decision

Accepted: Context OS needs one explicit, consumer-supplied Mission-use evidence
object. It does not need ambient telemetry or a monitoring subsystem.

Canonical schema:

```text
contextos.mission.context_use_evidence/1
```

The object preserves:

```text
Selected != Retrieved != Consumed != Used != Useful
```

Every assertion is `observed`, `declared`, `derived`, or `unknown`.

---

## Capability Delivered

`MissionContextUseEvidenceEngine` binds an exact Activation Package, Handoff,
Mission, and consumer to:

- selected Governing Context,
- explicit selected-source access evidence,
- bounded Execution Context retrieval and reasons,
- missing, stale, invalid, and excluded context,
- use and contribution assertions,
- Mission outcome,
- source freshness and provenance,
- explicit observability limits.

It is read-only and installs no telemetry.

Health may consume the object and explain package/handoff integrity, traceable
participation, execution gaps, contributions, and usefulness limits. Health
does not produce an aggregate usefulness score.

---

## Self-Hosting Evidence

Dogfood evidence object:

```text
mission.context_use_evidence.f5c419e306f5a448
```

At capture time:

| Observation | Result |
|---|---:|
| Package valid | yes |
| Handoff valid | yes |
| Governing sources selected | 12 |
| Selected sources with access evidence | 4 |
| Additional Execution Context retrievals | 9 |
| Context gaps | 1 |
| Stale context observations | 0 |
| Traceable contributions | 2 |
| Explicit use assertions | 2 |
| Explicit usefulness assertions | 0 |

The Handoff oriented the Mission. Execution additionally required the Health
runtime, tests, contract, activation validity implementation, Health README,
Evolution Inbox, and exact package/Handoff artifacts. Each retrieval recorded
its Mission need, reason, authority, evidence semantics, and freshness rule.

The exact Health contract was required but not selected automatically. This is
recorded as a gap, not silently hidden or used to expand selection scope.

After canonical Mission evidence and maps changed, the original Handoff was
correctly invalidated by selected-source hash drift. A fresh valid package and
Handoff were generated for the recommended next Mission:

```text
activation.package.9094ed2ffd98c6da
activation.handoff.c9fe6a5806bdf149
V07-CONTEXT-HEALTH-CLI-001
```

---

## Health Result

Before structured Mission-use evidence, Context Usefulness was `unknown`
because Mission evidence was narrative.

After integration:

- package/Handoff integrity is `healthy`,
- per-source participation traceability is `healthy`,
- contribution traceability is `healthy`,
- the observed selection gap is `attention`,
- actual usefulness effect remains `unknown`.

The dimension becomes more informative without claiming that access or Mission
success proved usefulness.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Focused Mission-use tests | 10 passed |
| Existing Health tests | 7 passed |
| Full Runtime regression methods | 218 passed |
| Validator gate | exit 0; 0 errors; 0 fatals |
| Deterministic identity | passed |
| Package/Handoff invalidation | explicit |
| Unselected access binding | rejected |
| Declared vs observed semantics | preserved |
| JSON dogfood report | parseable |
| Original Handoff after selected-source edits | invalidated as expected |
| Fresh next-Mission Handoff | valid |
| Canonical mutation | none |
| Telemetry or surveillance | none |

---

## Learning

- Explicit participation evidence is valuable even when usefulness remains
  unknown.
- Access is objectively recordable today; cognitive consumption generally is
  not.
- A successful Mission cannot establish causal usefulness by itself.
- Governing Context selection and bounded Execution Context retrieval remain
  one coherent Mission Context, but they require different evidence records.
- The next product bottleneck is access to the Health report, not a score,
  learned ranking, Graph, or telemetry platform.

---

## Evolution Impact

INBOX-086 through INBOX-088 preserve observability limits, the user-facing
Health opportunity, and selector evidence without expanding this Mission.

---

## Next Mission Recommended

```text
V07-CONTEXT-HEALTH-CLI-001
```

Expose the existing Health engine and optional structured Mission-use evidence
through a narrow, read-only human and machine Runtime CLI surface.

---

## Change Log

- 2026-08-16 - v0.1.0 - Implemented and dogfooded structured Mission-use
  evidence with explainable Health integration.
