# E.4 Mission V04-BOOTSTRAP-PROPOSAL-REVIEW-001 - Read-Only Bootstrap Proposal Review Surface
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Expose the read-only Bootstrap Proposal as a reviewable and preservable Runtime
CLI surface without authorizing approval or apply.

This mission moves v0.4 from an internal proposal engine to a user-visible
proposal review surface in the governed transition:

```text
Plan -> Proposal -> Decision/Approval -> Apply -> Validate -> Learn
```

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V04-BOOTSTRAP-PROPOSAL-REVIEW-001
  title: Read-Only Bootstrap Proposal Review Surface
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

Allow an operator to generate, inspect, and preserve the exact Bootstrap
Proposal that could later enter approval, without mutating the target
repository or implying approval.

---

## Slice

v0.4 implementation slice:

- expose proposal generation through `contextos init --proposal`,
- preserve default `contextos init` planning behavior,
- support human and JSON proposal output,
- support `--json-out` for preserving the proposal artifact,
- support proposal authority metadata flags,
- keep proposal generation read-only,
- add CLI tests for proposal human output, pure JSON, and JSON-out behavior.

No approval execution, apply behavior, confirmation, scaffold write, rollback
execution, ledger runtime, or agent orchestration is included.

---

## Authority

| Role | Authority | Bound |
|---|---|---|
| Mission Owner | Approval authority | Context OS Maintainers |
| Codex | L3 bounded implementation | CLI read-only proposal surface, proposal report renderer, tests, contract/docs/SSOT alignment |
| Codex | L4 read-only verification | Local tests, validator gate, smoke commands, JSON purity checks |
| Future apply implementer | L0 for apply mutation | No mutation authority granted |

---

## Constraints

- No silent mutation.
- No unapproved writes.
- No regeneration of approved intent.
- No apply mode.
- No confirmation or approval execution.
- No file, directory, manifest, or scaffold creation.
- No generic workflow engine.
- No future-release scope.
- Existing `validate`, `assess`, `init` plan, Validator, Readiness, Bootstrap
  Plan, and Bootstrap Proposal Engine behavior must remain stable.

---

## Acceptance Criteria

1. `contextos init --proposal --root .` renders a human-readable Bootstrap
   Proposal.
2. `contextos init --proposal --format json` emits pure
   `contextos.bootstrap.proposal/1` JSON.
3. `contextos init --proposal --json-out <path>` writes a valid machine
   proposal.
4. The proposal output states that it is read-only and does not imply approval
   or authorize apply.
5. Default `contextos init` remains a Bootstrap Plan, not a proposal.
6. Existing runtime tests remain green.
7. Context OS dogfood proposal generation works.
8. Evolution Inbox captures deferred work without expanding this mission.

---

## Decision

Use `contextos init --proposal` as the read-only proposal review surface.

Rationale:

- `contextos init` is already the Guided Bootstrap entry point.
- `--proposal` makes the transition explicit without changing the safe default.
- A separate apply/approval command is still deferred until the proposal review
  surface proves stable.
- JSON-out provides a simple preservation mechanism without inventing a storage
  subsystem.

---

## Capability Delivered

CLI:

```text
contextos init --root . --proposal
contextos init --root . --proposal --format json
contextos init --root . --proposal --json-out <path>
```

Additional proposal metadata flags:

- `--mission-id`
- `--requested-by`
- `--proposal-mode local|project|organization|embedded`

---

## Evidence Plan

- Run CLI proposal tests.
- Run bootstrap proposal and plan tests.
- Run validator, readiness, and CLI regression tests.
- Run `contextos validate --mode gate`.
- Smoke `contextos init`, `contextos init --proposal --format json`, and
  `contextos init --proposal --json-out`.
- Validate generated JSON with `python3 -m json.tool`.
- Run `git diff --check`.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| CLI proposal surface implemented | `tools/cli/contextos_cli.py` |
| Human proposal renderer implemented | `tools/bootstrap/bootstrap_engine/proposal_report_builder.py` |
| CLI proposal tests added | `tools/cli/test_contextos_cli.py` |
| CLI contract aligned | `docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md` |
| Bootstrap docs aligned | `tools/bootstrap/README.md` |
| Product/system roadmap aligned | `SSOT/P.1`, `SSOT/P.2`, `SSOT/A.1` |
| CLI tests | `python3 tools/cli/test_contextos_cli.py` passed, 15 tests |
| Bootstrap proposal tests | `python3 tools/bootstrap/test_bootstrap_proposal.py` passed, 7 tests |
| Bootstrap plan tests | `python3 tools/bootstrap/test_bootstrap_plan.py` passed, 5 tests |
| Validator tests | `python3 tools/validators/test_contextos_validator.py` passed, 11 tests |
| Readiness tests | Repository inventory, scoring, and recommendations passed, 14 tests |
| Gate validation | `contextos validate --mode gate --format json` returned exit_code 0, error 0, fatal 0 |
| Proposal JSON smoke | `contextos init --proposal --format json` emitted pure `contextos.bootstrap.proposal/1` JSON |
| Proposal human smoke | `contextos init --proposal --json-out` rendered a human proposal and wrote valid JSON |
| Plan compatibility smoke | `contextos init --format json` still returned `contextos.bootstrap.plan/1` |
| Whitespace validation | `git diff --check` passed |

Command evidence is captured in the final mission response and repository
history for the commit containing this artifact.

---

## Learning

- The proposal review surface is a necessary dependency before approval/apply:
  the user must be able to preserve exactly what will be approved.
- `--proposal` is lower risk than a new command because it keeps Guided
  Bootstrap under the existing `init` entry point while preserving safe default
  behavior.
- JSON-out is enough for v0.4 preservation; durable approval storage remains a
  separate governance mission.

---

## Roadmap Impact

No release goal change.

v0.4 now supports the first two operational stages of the governed transition:

```text
Plan -> Proposal
```

Decision/Approval remains the next release gap before any apply implementation.

---

## Change Log

- 2026-08-11 - v0.1.0 - Implemented and closed read-only Bootstrap Proposal
  Review Surface mission.
