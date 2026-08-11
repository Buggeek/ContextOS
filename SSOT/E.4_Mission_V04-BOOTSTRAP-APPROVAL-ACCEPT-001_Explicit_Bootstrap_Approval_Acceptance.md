# E.4 Mission V04-BOOTSTRAP-APPROVAL-ACCEPT-001 - Explicit Bootstrap Approval Acceptance
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Implement the explicit, human-driven, non-mutating acceptance step for v0.4
Guided Bootstrap.

This mission moves the governed transition from:

```text
Plan -> Proposal -> Decision/Approval Draft
```

to:

```text
Plan -> Proposal -> Decision/Approval Draft -> Accepted Decision
```

without authorizing or performing repository mutation.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V04-BOOTSTRAP-APPROVAL-ACCEPT-001
  title: Explicit Bootstrap Approval Acceptance
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

Convert a valid Bootstrap Approval Record Draft into a durable accepted
decision artifact only when an explicit human identity and authority role are
provided and the preserved proposal still matches the approved intent.

---

## Slice

v0.4 implementation slice:

- implement `contextos.bootstrap.accepted_decision/1`,
- require explicit approving human identity,
- require explicit approving authority role,
- verify proposal identity, source plan identity, repository fingerprint,
  proposal file hash, drift status, prohibited action classification, and
  required evidence,
- embed a `contextos.decision/1` Decision Record,
- expose acceptance through `contextos init --accept-approval <approval.json>`,
- preserve read-only behavior and existing plan/proposal/approval draft
  behavior.

No apply, rollback execution, ledger runtime, scaffold write, or repository
mutation is included.

---

## Authority

| Role | Authority | Bound |
|---|---|---|
| Mission Owner | Approval authority | Context OS Maintainers |
| Codex | L3 bounded implementation | Acceptance engine, report renderer, CLI read-only surface, tests, and SSOT alignment |
| Codex | L4 read-only verification | Local tests, validator gate, JSON purity, CLI smoke checks |
| Human approver | L3 approval decision | Must provide explicit identity and required authority role |
| Future apply implementer | L0 for apply mutation | No mutation authority granted |

---

## Constraints

- No silent mutation.
- No unapproved writes.
- No apply behavior.
- No silent approval.
- No inferred approver.
- No auto-accept.
- No regeneration of approved intent.
- No generic workflow engine.
- No agent orchestration.
- No future-release scope.
- Discoveries outside this mission enter the Evolution Inbox.

---

## Acceptance Criteria

1. `contextos.bootstrap.accepted_decision/1` exists as an implemented runtime
   object.
2. Acceptance is read-only.
3. Acceptance requires explicit human identity.
4. Acceptance requires an explicit role satisfying the approval record's
   required authority.
5. Proposal id and identity hash remain unchanged.
6. Source plan hash remains unchanged.
7. Repository fingerprint remains valid.
8. Proposal file hash remains unchanged when a file hash is available.
9. Proposal drift blocks acceptance.
10. Prohibited actions remain prohibited and cannot become approvable through
    acceptance.
11. Required evidence is present.
12. The accepted artifact embeds a `contextos.decision/1` Decision Record.
13. The accepted artifact approves the proposal but does not authorize apply.
14. CLI output supports human, JSON, and JSON-out forms.
15. Existing shipped capabilities remain green.
16. Objective evidence is captured.
17. Evolution Inbox captures deferred work.

---

## Decision

Use `contextos init --accept-approval <approval.json>` as the explicit
non-mutating approval acceptance surface.

Rationale:

- Guided Bootstrap remains under `init` while v0.4 is bootstrap-focused.
- The input is a preserved approval record file, so the command cannot silently
  regenerate proposal intent.
- Acceptance requires explicit human identity and role.
- The output is an accepted decision artifact, not an apply authorization.

---

## Capability Delivered

CLI:

```text
contextos init --root . --accept-approval <approval.json> --accepted-by <human> --accepted-role <role>
contextos init --root . --accept-approval <approval.json> --accepted-by <human> --accepted-role <role> --format json
contextos init --root . --accept-approval <approval.json> --accepted-by <human> --accepted-role <role> --json-out <path>
```

Optional metadata:

- `--rationale`

---

## Evidence Plan

- Run acceptance tests.
- Run approval record, proposal, plan, validator, readiness, and CLI
  regression tests.
- Generate proposal, approval-record draft, and accepted decision against
  Context OS.
- Validate JSON output with `python3 -m json.tool`.
- Verify `contextos validate --mode gate` remains exit code 0.
- Run `git diff --check`.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Acceptance engine implemented | `tools/bootstrap/bootstrap_engine/acceptance_engine.py` |
| Acceptance report renderer implemented | `tools/bootstrap/bootstrap_engine/acceptance_report_builder.py` |
| Acceptance tests added | `tools/bootstrap/test_bootstrap_acceptance.py` |
| CLI acceptance surface implemented | `tools/cli/contextos_cli.py` |
| CLI tests extended | `tools/cli/test_contextos_cli.py` |
| CLI contract aligned | `1.5.2 CLI Contract` documents accepted decision output |
| Apply approval contract aligned | `1.5.7 Bootstrap Apply Approval Contract` documents accepted decision artifact |
| Bootstrap docs aligned | `tools/bootstrap/README.md` |
| System map aligned | `SSOT/A.1_System_Map.md` |
| Data entities aligned | `SSOT/A.4_Data_Entities.md` |
| Evolution Inbox updated | Deferred durable ledger/persistence questions kept outside active scope |
| Acceptance tests | `python3 tools/bootstrap/test_bootstrap_acceptance.py` passed, 8 tests |
| Bootstrap regressions | Approval, proposal, and plan tests passed, 20 tests |
| CLI tests | `python3 tools/cli/test_contextos_cli.py` passed, 23 tests |
| Readiness tests | Repository inventory, scoring, and recommendations passed, 14 tests |
| Validator tests | `python3 tools/validators/test_contextos_validator.py` passed, 11 tests |
| Gate validation | `contextos validate --mode gate --format json` returned exit_code 0, error 0, fatal 0 |
| Acceptance JSON smoke | `contextos init --accept-approval <approval.json> --format json` emitted pure `contextos.bootstrap.accepted_decision/1` JSON |
| Context OS dogfood | Accepted decision generated with 21 actions, all acceptance checks passing, writes_performed false, apply_authorized false |
| Whitespace validation | `git diff --check` passed |

Command evidence is captured in the final mission response and repository
history for the commit containing this artifact.

---

## Learning

- Approval acceptance is a human decision artifact, not a write permission.
- The accepted decision must preserve proposal and approval identity so future
  apply can verify intent instead of regenerating it.
- Role satisfaction must be explicit before apply exists; inferred approvers
  would weaken the Human-Agent Authority Model.
- The next mission should define apply preflight against an accepted decision
  before any repository mutation is implemented.

---

## Roadmap Impact

No release goal change.

v0.4 now supports:

```text
Plan -> Proposal -> Decision/Approval Draft -> Accepted Decision
```

Remaining v0.4 work begins at apply preflight, then create-only apply.

---

## Change Log

- 2026-08-11 - v0.1.0 - Implemented and closed explicit Bootstrap Approval
  Acceptance mission.
