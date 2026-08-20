# E.4 Mission V07-CONTEXT-HEALTH-CLI-001 - Context Health CLI
## Version: 0.1.0
Last Updated: 2026-08-20
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Expose Context Health & Learning as a narrow, read-only human and machine
product surface without moving interpretation or remediation into the CLI.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V07-CONTEXT-HEALTH-CLI-001
  title: Context Health CLI
  release: v0.7-context-health-and-learning
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed:done
  authority: human_granted_read_only_health_cli_implementation
  created_at: 2026-08-20
```

Exit conditions required human and pure machine output, optional exact
Mission-use evidence, Validator exit-code preservation, read-only proof,
epistemic safeguards, dogfooding, regressions, learning, and no remediation.

---

## Governing Activation Context

The Mission began from the valid Handoff:

```text
activation.handoff.c9fe6a5806bdf149
activation.package.9094ed2ffd98c6da
V07-CONTEXT-HEALTH-CLI-001
consumer=codex
```

The Handoff passed identity, package binding, source freshness, and Validator
checks before implementation.

---

## Decision

Accepted: add one read-only command:

```text
contextos health
```

Supported inputs and outputs:

```text
--root <path>
--mission-use-evidence <context-use.json>
--format text|human|json
--json-out <path>
```

The CLI contains no Health rules. It loads optional evidence, calls
`ContextHealthEngine`, renders the report, and preserves embedded Validator
exit codes `0`, `7`, `8`, and CLI/configuration code `9`.

---

## Human Experience

The report answers what needs attention, why, and what to consider next through:

- overall and per-dimension status,
- prioritized blocked, attention, and unknown signals,
- explicit evidence semantics and references,
- complete Integrity, Usefulness, and Learning views,
- governed Context Update Candidates,
- observability limits,
- an explicit statement that no automatic change occurred,
- the mandatory route through Context Construction for accepted changes.

---

## Machine Experience

JSON stdout is pure `contextos.health.report/1`. `--json-out` writes the same
full report outside the assessed target when requested. The optional input must
be `contextos.mission.context_use_evidence/1` and match the assessed root.

---

## Dogfood Result

Context OS was assessed using:

```text
mission.context_use_evidence.13125aa9ec5ccb79
```

Result:

| View | Status | Meaning |
|---|---|---|
| Overall | attention | Non-blocking evidence requires consideration |
| Context Integrity | attention | Validator warnings, ownership, and Readiness caps |
| Context Usefulness | attention | Participation is traceable; one gap and one stale observation exist |
| Organizational Learning | healthy | Mission learning and Evolution Inbox capture are present |

The report contained 15 signals: 10 healthy, 4 attention, 0 blocked, and 1
unknown. Actual usefulness remained unknown because there were zero supported
usefulness assertions. Two high-priority, non-canonical Context Update
Candidates were shown for warning triage and Readiness constraints.

Human, JSON stdout, and `--json-out` runs returned exit 0. JSON reports parsed,
and the target diff remained unchanged.

---

## Regression Evidence

| Evidence | Result |
|---|---|
| Existing Health tests | 8 passed |
| Mission-use evidence tests | 10 passed |
| Runtime CLI tests | 46 passed |
| Full Runtime regression methods | 225 passed |
| Validator gate | exit 0; 0 errors; 0 fatals |
| Health JSON stdout | pure and parseable |
| Health `--json-out` | full report, parseable |
| Health target mutation | none |
| Canonical signal belief states | observed, declared, derived, unknown only |
| Governing Handoff after selected-source edits | invalidated as expected |
| `git diff --check` | passed |

---

## Epistemic And Governance Boundary

```text
Observed != Declared != Derived != Unknown
Selected != Retrieved != Consumed != Used != Useful
```

The CLI does not infer usefulness, score Health, mutate context, execute
remediation, create drafts or Missions, or bypass governed Construction.

---

## Learning

- Prioritized attention makes the existing Health report operational without a
  dashboard.
- Machine and human consumers can share one report schema and engine.
- Explicit Mission-use evidence materially improves explanation, but does not
  justify a causal usefulness claim.
- The next responsible step is release-level verification, not another feature
  slice assumed in advance.

---

## Evolution Impact

INBOX-089 through INBOX-091 preserve release verification, evidence-input
ergonomics, and future presentation ideas without expanding this Mission.

---

## Next Mission Recommended

```text
V07-CONTEXT-HEALTH-RELEASE-VERIFY-001
```

Verify the complete v0.7 journey and decide whether report history/comparison
or explicit Mission-use capture ergonomics are true release requirements or
intentional deferrals.

---

## Change Log

- 2026-08-20 - v0.1.0 - Implemented, dogfooded, and verified the read-only
  Context Health CLI.
