# E.4 Mission V04-BOOTSTRAP-APPLY-001 - Guided Bootstrap Apply Approval Model
## Version: 0.2.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Define the governed transition from a read-only Bootstrap Plan to a future
write-capable Bootstrap Apply operation.

This mission answers:

Under what conditions may Context OS modify a repository during Guided
Bootstrap?

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V04-BOOTSTRAP-APPLY-001
  title: Guided Bootstrap Apply Approval Model
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

Establish the approval, authority, evidence, validator-gate, proposal identity,
drift, no-overwrite, idempotency, and reversibility rules required before any
future Guided Bootstrap apply operation may write to a repository.

---

## Slice

v0.4 governance slice:

- define Bootstrap Proposal lifecycle,
- define authority by mode,
- define action classes,
- define pre-apply and post-apply evidence,
- define validator gates,
- define no-overwrite and idempotency rules,
- define rollback and drift behavior,
- define approval-state storage using existing Context OS mechanisms.

No write-capable implementation is included in this mission.

---

## Authority

| Role | Authority | Bound |
|---|---|---|
| Mission Owner | Approval authority | Accepts mission scope and closure |
| Codex | L3 bounded documentation execution | May update contracts, SSOT, and roadmap alignment |
| Codex | L4 read-only verification | May run validator, readiness, bootstrap, CLI, and diff checks |
| Future apply implementer | L0 for apply mutation in this mission | No apply behavior is authorized here |

---

## Constraints

- Do not implement write-capable bootstrap behavior.
- Do not add apply CLI behavior.
- Do not create a workflow engine.
- Do not create agent orchestration.
- Do not create speculative infrastructure.
- Do not change the v0.4 product goal.
- Do not reopen GENESIS unless a contradiction is discovered.
- Preserve shipped v0.3 and current v0.4 behavior.

---

## Acceptance Criteria

1. Bootstrap Proposal lifecycle is defined from `planned` through acceptance,
   failure, or rollback.
2. Transition authority is defined.
3. Minimum authority data is defined for local, project, organization, and
   embedded modes.
4. Automatic, approval-required, prohibited, and manual action boundaries are
   defined.
5. Pre-apply evidence is defined.
6. Post-apply evidence is defined.
7. Validator gates are defined before and after mutation.
8. No-overwrite guarantees are defined.
9. Idempotency expectations are defined.
10. Rollback and reversibility expectations are defined.
11. Repository drift behavior between plan and apply is defined.
12. Proposal identity and preservation rules are defined.
13. Approval-state storage is resolved using existing Context OS mechanisms.
14. Evolution Inbox is updated with newly discovered risks and deferred work.
15. Mission closes only with evidence of alignment to GENESIS, authority,
    governance, validator, bootstrap, and runtime contracts.

---

## Decision

Context OS may modify a repository during Guided Bootstrap only when all of the
following are true:

1. A read-only `contextos.bootstrap.plan/1` exists.
2. A preserved `contextos.bootstrap.proposal/1` has been generated from that
   exact plan and stores the source plan hash.
3. The proposal has a Mission Packet and an authority grant scoped to target
   root, allowed paths, prohibited paths, mode, approvers, and expiry.
4. The proposal has been human reviewed and approved by the required authority
   for its mode.
5. Pre-apply Validator gates have run and do not prohibit mutation.
6. Repository state still matches the proposal fingerprint.
7. Apply performs only approved actions and never silently regenerates a new
   plan.
8. No existing user content is overwritten.
9. Every action has idempotency and rollback behavior.
10. Post-apply Validator gates run and are preserved as evidence.
11. The result is accepted, failed, or rolled back with a Decision Record and,
    when available, an Accountability Ledger entry.

Mission evidence alone is sufficient for planning-only missions. It is not
sufficient for write-capable apply.

---

## Canonical Approval Lifecycle

```text
planned -> reviewed -> approved -> applied -> validated -> accepted
                                             |            |
                                             |            -> failed -> rolled_back
                                             -> failed -> rolled_back
```

| State | Authority |
|---|---|
| planned | Runtime may produce from read-only plan |
| reviewed | Named human reviewer for the selected mode |
| approved | Mission Owner plus required mode authority |
| applied | L3 execute-with-approval within proposal scope |
| validated | Validator L4 read-only |
| accepted | Mission Owner plus required mode authority |
| failed | Runtime or reviewer records failure |
| rolled_back | L3 within approved rollback scope |

---

## Authority Model by Mode

| Mode | Minimum authority data | Approval authority |
|---|---|---|
| local | operator id, target root, allowed/prohibited paths, proposal id, mission id, repository fingerprint | Mission Owner acting as local Runtime Owner |
| project | Mission Owner, Product Owner, Runtime Owner, code-owner or maintainer policy, allowed/prohibited paths, expiry | Mission Owner plus Product Owner or Runtime Owner by artifact class |
| organization | governance roster, Runtime Owner, Product Owner, Maintainers, affected repositories, source scope, expiry, decision target | Runtime Owner plus Governance Role; Product Owner for product/SSOT artifacts |
| embedded | host identity, user identity, tenant/project id, delegated scopes, callback approval handle, allowed/prohibited paths, expiry | Host-confirmed human approver mapped to Mission Owner or Runtime Owner |

---

## Action Boundary

| Class | May apply? | Rule |
|---|---|---|
| automatic | Yes, after full proposal approval | Deterministic create/skip only; no overwrite |
| approval_required | Yes, only if explicitly named in approved proposal | Human reviewer must see rationale and evidence |
| prohibited | No | Blocks or invalidates proposal |
| manual | No | Reported for human remediation outside apply |

Automatic never means unapproved.

---

## Evidence Plan

Required pre-apply evidence:

- source plan reference and canonical hash,
- readiness summary,
- Validator gate report,
- repository state fingerprint,
- action list with before/after expectations,
- no-overwrite proof,
- blocked/manual actions,
- authority grant,
- Decision Record placeholder or reference,
- rollback plan.

Required post-apply evidence:

- proposal id and source plan hash,
- action outcome list,
- file-level before/after hashes,
- post-apply Validator gate report,
- Git diff or equivalent delta when VCS exists,
- Decision Record,
- Accountability Ledger reference when ledger runtime exists,
- final state.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| GENESIS inspected | Bootstrap remains explicit, governed, and non-inventive |
| Mission Contract inspected | Mission Packet remains scope and evidence authority |
| Authority Model inspected | L3+ mutation requires human approval and evidence |
| Governance Protocol inspected | Change Proposal, Decision Record, and Ledger are existing mechanisms |
| Bootstrap Plan implementation inspected | Current plan is read-only and classifies required/skipped/blocked/manual actions |
| CLI Contract inspected | `contextos init` remains read-only in v0.4 |
| Validator Contract inspected | Pre/post gates use gate mode and preserve reports |
| Approval contract created | `1.5.7 Bootstrap Apply Approval Contract` defines full apply approval model |
| Roadmap/product/adoption alignment updated | v0.4 remains unchanged; future apply now points to approval contract |
| Evolution Inbox updated | New implementation risks and deferred work captured without scope expansion |
| Validator tests | `python3 tools/validators/test_contextos_validator.py` passed, 11 tests |
| Readiness tests | Repository inventory, scoring, and recommendation tests passed, 14 tests |
| Bootstrap tests | `python3 tools/bootstrap/test_bootstrap_plan.py` passed, 5 tests |
| CLI tests | `python3 tools/cli/test_contextos_cli.py` passed, 12 tests |
| Gate validation | `contextos validate --mode gate --format json` returned exit_code 0, error 0, fatal 0 |
| Readiness smoke | Context OS assessed as R3 Bootstrap Ready, score 74, can_bootstrap true |
| Bootstrap smoke | Current plan remained read-only, required 2, skipped 15, blocked 0, manual 4 |
| Whitespace validation | `git diff --check` passed |

Command evidence is captured in the final mission response and repository
history for the commit containing this artifact.

---

## Learning

- The required model already exists in Context OS pieces: Mission Packet,
  Change Proposal, Decision Record, Accountability Ledger, Validator report,
  and Bootstrap Plan.
- The missing object is not a workflow engine; it is a preserved Bootstrap
  Proposal that binds a plan hash, repository state, authority, and action list.
- `contextos init` should remain safe and read-only. Future apply must be a
  distinct proposal-approved surface.
- v0.4 can continue toward write-capable bootstrap only after proposal identity
  and approval evidence exist.

---

## Roadmap Impact

No release goal change.

v0.4 remains Guided Bootstrap. The next implementation slice should create the
read-only Bootstrap Proposal artifact/report before any apply mutation is
implemented.

---

## Change Log

- 2026-08-11 - v0.2.0 - Closed mission with proposal-approved apply model and
  evidence.
- 2026-08-11 - v0.1.0 - Proposed next v0.4 Mission Packet.
