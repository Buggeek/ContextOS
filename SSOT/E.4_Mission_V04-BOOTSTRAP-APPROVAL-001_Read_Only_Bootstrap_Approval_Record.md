# E.4 Mission V04-BOOTSTRAP-APPROVAL-001 - Read-Only Bootstrap Approval Record
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Implement the read-only Bootstrap Approval Record Draft for v0.4 Guided
Bootstrap.

This mission moves the governed transition from:

```text
Plan -> Proposal
```

to:

```text
Plan -> Proposal -> Decision/Approval Draft
```

without approving a proposal or authorizing apply.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V04-BOOTSTRAP-APPROVAL-001
  title: Read-Only Bootstrap Approval Record
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

Create a read-only approval record draft that binds a preserved Bootstrap
Proposal to required authority, drift status, blockers, and a Decision Record
draft before any apply implementation exists.

---

## Slice

v0.4 implementation slice:

- implement `contextos.bootstrap.approval_record/1`,
- bind approval record draft to proposal id and identity hash,
- include required authority roles and approver candidates,
- embed a `contextos.decision/1` Decision Record draft,
- perform proposal drift checks before approval can proceed,
- report blockers without authorizing mutation,
- expose the draft through `contextos init --approval-record <proposal.json>`,
- preserve existing plan/proposal behavior.

No actual approval, apply, rollback execution, ledger runtime, or repository
mutation is included.

---

## Authority

| Role | Authority | Bound |
|---|---|---|
| Mission Owner | Approval authority | Context OS Maintainers |
| Codex | L3 bounded implementation | Approval record engine, report renderer, CLI read-only surface, tests, and SSOT alignment |
| Codex | L4 read-only verification | Local tests, validator gate, JSON purity, CLI smoke checks |
| Future apply implementer | L0 for apply mutation | No mutation authority granted |

---

## Constraints

- No silent mutation.
- No unapproved writes.
- No actual approval execution.
- No apply behavior.
- No regeneration of approved intent.
- No generic workflow engine.
- No agent orchestration.
- No future-release scope.
- Discoveries outside this mission enter the Evolution Inbox.

---

## Acceptance Criteria

1. `contextos.bootstrap.approval_record/1` exists as an implemented runtime
   object.
2. Approval record generation is read-only.
3. The record binds proposal id, identity hash, source plan hash, repository
   fingerprint, mission, release, and goal.
4. The record includes authority requirements and approver candidates.
5. The record embeds a `contextos.decision/1` Decision Record draft.
6. Proposal drift blocks approval progression.
7. Prohibited actions block approval progression.
8. The record does not approve the proposal or authorize apply.
9. CLI output supports human, JSON, and JSON-out forms.
10. Existing shipped capabilities remain green.
11. Objective evidence is captured.
12. Evolution Inbox captures deferred work.

---

## Decision

Use `contextos init --approval-record <proposal.json>` as the read-only
approval-record draft surface.

Rationale:

- Guided Bootstrap remains under `init` while v0.4 is still bootstrap-focused.
- The input is a preserved proposal file, so the command cannot silently
  regenerate proposal intent.
- The output is a draft record, not a decision. Human authority is still
  required before approval and apply.

---

## Capability Delivered

CLI:

```text
contextos init --root . --approval-record <proposal.json>
contextos init --root . --approval-record <proposal.json> --format json
contextos init --root . --approval-record <proposal.json> --json-out <path>
```

Optional metadata:

- `--approver`
- `--rationale`

---

## Evidence Plan

- Run approval record tests.
- Run proposal, plan, validator, readiness, and CLI regression tests.
- Generate proposal and approval-record draft against Context OS.
- Validate JSON output with `python3 -m json.tool`.
- Verify `contextos validate --mode gate` remains exit code 0.
- Run `git diff --check`.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Approval record engine implemented | `tools/bootstrap/bootstrap_engine/approval_engine.py` |
| Approval report renderer implemented | `tools/bootstrap/bootstrap_engine/approval_report_builder.py` |
| Approval tests added | `tools/bootstrap/test_bootstrap_approval.py` |
| CLI approval surface implemented | `tools/cli/contextos_cli.py` |
| CLI tests extended | `tools/cli/test_contextos_cli.py` |
| Proposal drift check fixed | Repository drift comparison now uses full fingerprint hash |
| CLI contract aligned | `1.5.2 CLI Contract` documents approval-record draft output |
| Bootstrap docs aligned | `tools/bootstrap/README.md` |
| Approval tests | `python3 tools/bootstrap/test_bootstrap_approval.py` passed, 6 tests |
| Proposal tests | `python3 tools/bootstrap/test_bootstrap_proposal.py` passed, 9 tests |
| Bootstrap plan tests | `python3 tools/bootstrap/test_bootstrap_plan.py` passed, 5 tests |
| CLI tests | `python3 tools/cli/test_contextos_cli.py` passed, 19 tests |
| Validator tests | `python3 tools/validators/test_contextos_validator.py` passed, 11 tests |
| Readiness tests | Repository inventory, scoring, and recommendations passed, 14 tests |
| Gate validation | `contextos validate --mode gate --format json` returned exit_code 0, error 0, fatal 0 |
| Approval JSON smoke | `contextos init --approval-record <proposal.json> --format json` emitted pure `contextos.bootstrap.approval_record/1` JSON |
| Approval human smoke | `contextos init --approval-record <proposal.json> --json-out` rendered a human draft and wrote valid JSON |
| Plan/proposal compatibility | Existing plan and proposal surfaces remained read-only |
| Drift behavior | Saved proposals reuse the source plan timestamp and compare full repository fingerprints |
| Whitespace validation | `git diff --check` passed |

Command evidence is captured in the final mission response and repository
history for the commit containing this artifact.

---

## Learning

- Actual approval is a human authority boundary; the runtime can prepare the
  exact approval record but cannot decide it.
- The approval draft should bind proposal identity and decision shape before
  apply exists.
- Drift checks must use the full repository fingerprint, not only relevant path
  hashes, because dirty state and base ref affect approval safety.
- The next mission can implement approval acceptance only if it remains
  explicit, human-driven, and still non-mutating.

---

## Roadmap Impact

No release goal change.

v0.4 now supports:

```text
Plan -> Proposal -> Decision/Approval Draft
```

Remaining v0.4 work begins at human approval acceptance, then apply preflight.

---

## Change Log

- 2026-08-11 - v0.1.0 - Implemented and closed read-only Bootstrap Approval
  Record mission.
