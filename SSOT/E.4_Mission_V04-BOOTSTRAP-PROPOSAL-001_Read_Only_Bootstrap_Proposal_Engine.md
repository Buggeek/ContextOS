# E.4 Mission V04-BOOTSTRAP-PROPOSAL-001 - Read-Only Bootstrap Proposal Engine
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Implement the read-only Bootstrap Proposal Engine for v0.4 Guided Bootstrap.

The engine converts an existing `contextos.bootstrap.plan/1` into a preserved
`contextos.bootstrap.proposal/1` that freezes one exact future apply candidate
without approving or applying it.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V04-BOOTSTRAP-PROPOSAL-001
  title: Read-Only Bootstrap Proposal Engine
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

Create the governed, immutable proposal object that bridges a Bootstrap Plan
and a future approved Bootstrap Apply operation.

---

## Slice

v0.4 implementation slice:

- implement a read-only `BootstrapProposalEngine`,
- implement `contextos.bootstrap.proposal/1`,
- preserve source plan hash and proposal identity,
- fingerprint repository state relevant to proposed actions,
- preserve exact action set, evidence lineage, authority requirements, action
  classification, no-overwrite expectations, and rollback metadata,
- implement drift checking,
- test determinism, idempotency, drift invalidation, read-only behavior, and
  prohibited action handling.

No CLI surface or apply behavior is included.

---

## Authority

| Role | Authority | Bound |
|---|---|---|
| Mission Owner | Approval authority | Context OS Maintainers |
| Codex | L3 bounded implementation | `tools/bootstrap` proposal engine, tests, and related docs/SSOT alignment |
| Codex | L4 read-only verification | Local tests, validator gate, CLI smoke checks |
| Future apply implementer | L0 for apply mutation | No write-capable bootstrap behavior is authorized |

---

## Constraints

- Do not implement approval execution.
- Do not implement apply behavior.
- Do not add `--apply`, `--confirm`, file creation, manifest creation, artifact
  scaffolding, rollback execution, ledger runtime, agent orchestration,
  workflow engine, external connectors, or future-release functionality.
- Keep proposal generation fully read-only.
- Preserve existing `contextos assess`, `contextos init`, Validator, Readiness,
  and Bootstrap Plan behavior.

---

## Acceptance Criteria

1. `contextos.bootstrap.proposal/1` exists as an implemented runtime object.
2. Proposal generation is read-only.
3. Proposal and plan identity are preserved.
4. Repository fingerprinting exists.
5. Action classifications and authority requirements are preserved.
6. Drift invalidation is demonstrable.
7. Rollback metadata is represented.
8. Tests demonstrate determinism and idempotency expectations.
9. Existing shipped capabilities remain green.
10. Dogfooding demonstrates proposal generation against Context OS.
11. Mission evidence and learning are captured.
12. Evolution Inbox is updated where appropriate.

---

## Decision

Implement the proposal surface as a public Python API in `tools/bootstrap`:

```python
from bootstrap_engine.plan_engine import BootstrapPlanEngine
from bootstrap_engine.proposal_engine import BootstrapProposalEngine

plan = BootstrapPlanEngine(".").run()
proposal = BootstrapProposalEngine(".").run(plan)
```

Do not add CLI integration yet. The next mission can expose or persist
proposals only after the engine proves deterministic and read-only.

---

## Proposal Model

The implemented proposal contains:

- schema,
- deterministic proposal id,
- identity hash,
- mission id,
- release and goal,
- source plan hash,
- repository fingerprint,
- readiness evidence,
- validator evidence,
- authority block,
- exact action set,
- pre/post gate references,
- drift invalidation conditions,
- planned status,
- read-only constraints.

---

## Evidence Plan

- Add focused proposal-engine tests.
- Run all existing validator, readiness, bootstrap, and CLI tests.
- Generate a dogfood proposal for the Context OS repository.
- Validate JSON purity for generated proposal output.
- Run `contextos validate --mode gate`.
- Run `git diff --check`.
- Capture evidence in this Mission Packet.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Proposal engine implemented | `tools/bootstrap/bootstrap_engine/proposal_engine.py` |
| Proposal tests added | `tools/bootstrap/test_bootstrap_proposal.py` |
| Public API documented | `tools/bootstrap/README.md` |
| System map aligned | `SSOT/A.1_System_Map.md` |
| Product map aligned | `SSOT/P.1_Product_Map.md` |
| Roadmap self-hosting reference aligned | `SSOT/P.2_Product_Roadmap.md` |
| Evolution Inbox updated | Proposal persistence and future approval/apply work captured |
| Proposal tests | `python3 tools/bootstrap/test_bootstrap_proposal.py` passed, 7 tests |
| Bootstrap plan tests | `python3 tools/bootstrap/test_bootstrap_plan.py` passed, 5 tests |
| Validator tests | `python3 tools/validators/test_contextos_validator.py` passed, 11 tests |
| Readiness tests | Repository inventory, scoring, and recommendations passed, 14 tests |
| CLI tests | `python3 tools/cli/test_contextos_cli.py` passed, 12 tests |
| Gate validation | `contextos validate --mode gate --format json` returned exit_code 0, error 0, fatal 0 |
| Assess smoke | Context OS assessed as R3 Bootstrap Ready, score 74 |
| Init smoke | Current bootstrap plan remains read-only, required 2, skipped 15, blocked 0, manual 4 |
| Dogfood proposal | Generated `contextos.bootstrap.proposal/1` with 21 actions: 6 automatic, 11 approval_required, 4 manual |
| Proposal state | Dogfood proposal status `planned`, read_only true, approval implied false, apply authorized false |
| Drift tests | Plan drift and repository drift both invalidate proposals |

Command evidence is captured in the final mission response and repository
history for the commit containing this artifact.

---

## Learning

- Proposal identity must exclude generation timestamp but include the source
  plan hash, action identity, authority scope, and repository fingerprint.
- Proposal generation is useful before CLI integration because it stabilizes the
  core runtime object without changing user-facing behavior.
- Dirty working-tree state is part of proposal evidence; apply approval should
  be generated from a clean or explicitly accepted repository state in a future
  mission.
- Persistence is intentionally deferred. A proposal can be emitted as JSON by
  API today; a later CLI/report mission can decide where it should be stored.

---

## Roadmap Impact

No release goal change.

v0.4 remains Guided Bootstrap. The release now has the read-only proposal
object required before approval/apply can be implemented.

---

## Change Log

- 2026-08-11 - v0.1.0 - Implemented and closed read-only Bootstrap Proposal
  Engine mission.
