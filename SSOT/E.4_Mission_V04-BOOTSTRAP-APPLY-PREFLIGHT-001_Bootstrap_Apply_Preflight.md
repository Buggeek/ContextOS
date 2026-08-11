# E.4 Mission V04-BOOTSTRAP-APPLY-PREFLIGHT-001 - Bootstrap Apply Preflight
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Implement the final governed, non-mutating preflight between an Accepted
Decision and any future Guided Bootstrap repository mutation.

This mission moves the governed transition from:

```text
Plan -> Proposal -> Decision/Approval Draft -> Accepted Decision
```

to:

```text
Plan -> Proposal -> Decision/Approval Draft -> Accepted Decision -> Apply Preflight
```

without authorizing or performing repository mutation.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V04-BOOTSTRAP-APPLY-PREFLIGHT-001
  title: Bootstrap Apply Preflight
  initiating_lifecycle: release
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed:done
  created_at: 2026-08-11
```

---

## Release

v0.4 - Guided Bootstrap

---

## Goal

Determine whether a previously accepted Bootstrap decision is still safe and
valid to execute now, while freezing the exact mutation set and remaining
fully read-only.

---

## Slice

v0.4 implementation slice:

- implement `contextos.bootstrap.apply_preflight/1`,
- verify Accepted Decision identity and preservation,
- verify Approval Record identity and file hash,
- verify Proposal identity, file hash, source plan hash, repository
  fingerprint, and drift state,
- verify authority remains valid,
- freeze the executable mutation set,
- prove actions remain inside approved scope,
- prove prohibited actions cannot enter the mutation set,
- prove no-overwrite and rollback expectations still hold,
- run the Validator gate,
- expose preflight through `contextos init --preflight <accepted.json>`,
- preserve existing plan, proposal, approval, acceptance, readiness,
  validator, and CLI behavior.

No apply, rollback execution, scaffold write, repository mutation, generic
workflow engine, or future-release capability is included.

---

## Authority

| Role | Authority | Bound |
|---|---|---|
| Mission Owner | Approval authority | Context OS Maintainers |
| Codex | L3 bounded implementation | Preflight engine, report renderer, CLI read-only surface, tests, and SSOT alignment |
| Codex | L4 read-only verification | Local tests, validator gate, JSON purity, CLI smoke checks |
| Human approver | L3 approval decision | Already captured in Accepted Decision |
| Future apply operator | L0 for apply mutation | No mutation authority granted by this mission |

---

## Constraints

- No silent mutation.
- No unapproved writes.
- No apply behavior.
- No silent approval.
- No regeneration of approved intent.
- No broadening of mutation scope.
- No generic workflow engine.
- No agent orchestration.
- No future-release scope.
- Discoveries outside this mission enter the Evolution Inbox.

---

## Acceptance Criteria

1. `contextos.bootstrap.apply_preflight/1` exists as an implemented runtime
   object.
2. Preflight is read-only.
3. Accepted Decision identity is verified.
4. Approval Record identity and file hash are verified.
5. Proposal identity and file hash are verified.
6. Source plan hash remains bound.
7. Repository fingerprint remains valid.
8. Proposal drift blocks apply eligibility.
9. Human authority remains valid.
10. Executable actions remain inside approved scope.
11. Prohibited actions remain impossible.
12. No-overwrite guarantees still hold.
13. Rollback expectations are present.
14. Validator gate is satisfied.
15. All evidence required for future apply exists.
16. The exact executable mutation set is frozen and hashed.
17. Preflight may mark apply eligible but does not authorize apply.
18. CLI output supports human, JSON, and JSON-out forms.
19. Existing shipped capabilities remain green.
20. Objective evidence is captured.
21. Evolution Inbox captures deferred work.

---

## Decision

Use `contextos init --preflight <accepted.json>` as the read-only final gate
before any future apply implementation.

Rationale:

- Guided Bootstrap remains under `init` while v0.4 is bootstrap-focused.
- The input is a preserved accepted decision file, so preflight cannot silently
  regenerate accepted intent.
- The output freezes the executable mutation set and explains apply
  eligibility.
- Even successful preflight does not authorize apply; a future apply command
  still requires explicit human authority.

---

## Capability Delivered

CLI:

```text
contextos init --root . --preflight <accepted.json>
contextos init --root . --preflight <accepted.json> --format json
contextos init --root . --preflight <accepted.json> --json-out <path>
```

Machine report:

```text
contextos.bootstrap.apply_preflight/1
```

---

## Evidence Plan

- Run preflight tests.
- Run acceptance, approval, proposal, plan, validator, readiness, and CLI
  regression tests.
- Generate proposal, approval-record draft, accepted decision, and apply
  preflight against Context OS.
- Validate JSON output with `python3 -m json.tool`.
- Verify `contextos validate --mode gate` remains exit code 0.
- Run `git diff --check`.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Preflight engine implemented | `tools/bootstrap/bootstrap_engine/preflight_engine.py` |
| Preflight report renderer implemented | `tools/bootstrap/bootstrap_engine/preflight_report_builder.py` |
| Preflight tests added | `tools/bootstrap/test_bootstrap_preflight.py` |
| CLI preflight surface implemented | `tools/cli/contextos_cli.py` |
| CLI tests extended | `tools/cli/test_contextos_cli.py` |
| CLI contract aligned | `1.5.2 CLI Contract` documents apply preflight output |
| Apply approval contract aligned | `1.5.7 Bootstrap Apply Approval Contract` documents preflight before apply |
| Bootstrap docs aligned | `tools/bootstrap/README.md` |
| System map aligned | `SSOT/A.1_System_Map.md` |
| Data entities aligned | `SSOT/A.4_Data_Entities.md` |
| Evolution Inbox updated | Future apply execution and ledger questions kept outside active scope |
| Preflight tests | `python3 tools/bootstrap/test_bootstrap_preflight.py` passed, 5 tests |
| Bootstrap regressions | Acceptance, approval, proposal, and plan tests passed, 28 tests |
| CLI tests | `python3 tools/cli/test_contextos_cli.py` passed, 27 tests |
| Readiness tests | Repository inventory, scoring, and recommendations passed, 14 tests |
| Validator tests | `python3 tools/validators/test_contextos_validator.py` passed, 11 tests |
| Gate validation | `contextos validate --mode gate --format json` returned exit_code 0, error 0, fatal 0 |
| Preflight JSON smoke | `contextos init --preflight <accepted.json> --format json` emitted pure `contextos.bootstrap.apply_preflight/1` JSON |
| Context OS dogfood | Apply preflight generated with eligible true, apply_authorized false, all 17 checks passing, frozen mutation set present |
| Whitespace validation | `git diff --check` passed |

Command evidence is captured in the final mission response and repository
history for the commit containing this artifact.

---

## Learning

- Apply eligibility and apply authorization must remain separate concepts.
- The executable mutation set belongs in preflight, not acceptance, because it
  must be checked against the current repository state immediately before
  mutation.
- The first future apply implementation should consume the preflight report and
  require a fresh human apply confirmation instead of deriving scope from the
  original plan.

---

## Roadmap Impact

No release goal change.

v0.4 now supports:

```text
Plan -> Proposal -> Decision/Approval Draft -> Accepted Decision -> Apply Preflight
```

Remaining v0.4 work begins at create-only apply.

---

## Change Log

- 2026-08-11 - v0.1.0 - Implemented and closed Bootstrap Apply Preflight
  mission.
