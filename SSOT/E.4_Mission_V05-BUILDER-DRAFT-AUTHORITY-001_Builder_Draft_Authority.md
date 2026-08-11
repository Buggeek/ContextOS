# E.4 Mission V05-BUILDER-DRAFT-AUTHORITY-001 - Builder Draft Authority
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Define the governed authority model required before any Builder draft can be
written during Release v0.5 Context Construction.

This mission answers:

> Under what exact conditions may Context OS create a draft context artifact
> without crossing the boundary from evidence-supported proposal into
> unapproved organizational truth?

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V05-BUILDER-DRAFT-AUTHORITY-001
  title: Builder Draft Authority
  initiating_lifecycle: release
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed:done
  created_at: 2026-08-11
```

---

## Release

v0.5 - Context Construction

---

## Goal

Create a decision-complete authority contract for future Builder draft writes,
while preserving the rule that evidence-supported drafts are not
organizational truth.

---

## Scope

In scope:

- define write authority conditions,
- define evidence sufficiency rules,
- define human review and authority requirements,
- define no-overwrite guarantees,
- define target-path scope,
- define draft lifecycle boundary,
- define validation gates before and after write,
- define conflict and unknown handling,
- define rollback and reversibility expectations,
- define promotion prohibition,
- define proposal/plan identity binding,
- define repository drift handling,
- update v0.5 roadmap/epic/inbox references.

Out of scope:

- write-capable Builder behavior,
- CLI surfaces,
- `build-mom`,
- `build-ssot`,
- draft file creation,
- automatic promotion,
- Knowledge Engine,
- Context Graph runtime,
- agents,
- external connectors.

---

## Authority

| Role | Authority | Bound |
|---|---|---|
| Mission Owner | Release execution authority | Context OS Maintainers |
| Codex | L3 bounded documentation/canonicalization | Runtime contract, mission evidence, roadmap/epic/inbox alignment |
| Codex | L0 Builder writes | No MOM/SSOT or draft artifact mutation |
| Codex | L0 CLI/runtime expansion | No construction CLI or write-capable runtime behavior |

Human authority for this mission was granted by the user request.

---

## Draft Authority Model

Future Builder draft creation requires:

- explicit L2 draft authority,
- a human-approved Mission Packet,
- a preserved Builder Draft Plan item,
- a preserved Discovery Bundle source fingerprint,
- a preserved Construction Plan candidate,
- a human Draft Authorization bound to exact item, path, plan identity, and
  rationale,
- no contradictions,
- preserved unknowns and missing evidence,
- Validator gate success,
- no-overwrite target checks,
- repository drift checks,
- post-write validation,
- rollback metadata.

Draft creation may only move context to `draft`.

It cannot review, approve, promote, overwrite, delete, repair, or reinterpret
truth.

---

## Lifecycle Boundary

Allowed:

```text
suggested -> draft
draft -> draft
```

Prohibited:

```text
observed -> reviewed
observed -> approved
observed -> canonical/verified
suggested -> reviewed
suggested -> approved
suggested -> canonical/verified
draft -> reviewed
draft -> approved
draft -> canonical/verified
```

---

## Evidence Sufficiency Rules

A future draft item may be written only when:

1. item status is `draftable`,
2. support is at least `moderate`,
3. provenance includes Discovery source id and fingerprint,
4. provenance includes at least one evidence ref,
5. unknowns are preserved,
6. missing evidence is preserved,
7. contradictions are empty,
8. relevant construction blockers are absent,
9. Validator gate has no `error` or `fatal`.

Evidence sufficiency permits only a draft proposal, not truth.

---

## Human Review and Approval Requirements

Before draft creation:

- an accountable human must authorize draft creation at L2,
- the authorization must name the draft item id and target path,
- the authorization must bind the current plan/fingerprint identity,
- the authorizing role must satisfy the artifact/domain authority bound.

After draft creation:

- human review is still required,
- human approval is still required for any later promotion,
- canonical verification is still required before context becomes canonical.

---

## No-Overwrite and Drift Guarantees

Future Builder draft writes must:

- use draft-only target scope,
- refuse canonical target overwrite,
- refuse replacement, deletion, and repair,
- refuse unexpected existing paths,
- refuse symlink traversal outside approved root,
- invalidate on Discovery fingerprint drift,
- invalidate on Builder Draft Plan identity drift,
- invalidate on Construction Plan candidate drift,
- invalidate on target path drift,
- invalidate on expired or changed authority,
- never regenerate a new plan silently at write time.

---

## Validation and Rollback

Pre-write validation:

- schemas valid,
- identities bound,
- authority valid,
- evidence sufficient,
- target safe,
- Validator gate passing.

Post-write validation:

- only approved draft paths created,
- draft lifecycle state is explicit,
- provenance, unknowns, and missing evidence preserved,
- no canonical context modified,
- Validator gate outcome recorded.

Rollback:

- remove only artifacts created by the same draft write operation,
- remove only when current hash matches recorded post-write hash,
- never remove pre-existing content,
- never remove canonical context.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| GENESIS inspected | Evidence promotes belief only under governance |
| Human-Agent Authority Model inspected | L2 draft authority is the minimum write level for drafts |
| Governance Protocol inspected | Promotion still requires Change Proposal and Decision Record |
| Mission Contract inspected | Future write authority must be mission-scoped and evidence-bound |
| Builder Draft Plan inspected | Existing plan already carries support, unknowns, contradictions, and promotion restrictions |
| Runtime contract created | `docs/1.x_architecture/1.5_runtime_contracts/1.5.8_Builder_Draft_Authority_Contract.md` |
| Runtime contract index updated | `docs/1.x_architecture/1.5_runtime_contracts/README.md` |
| Roadmap/epic aligned | v0.5 and EPIC-006 reference Builder Draft Authority |
| Evolution Inbox updated | Future implementation and draft-surface decisions captured |
| Regression tests | Existing Builder, Discovery, Construction, Readiness, Bootstrap, Validator, and CLI tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Whitespace validation | `git diff --check` passed |

---

## Decision

The authority model is decision-complete enough for a future implementation
mission to build a read-only preflight/authorization object for Builder draft
writes.

Write-capable Builder behavior is not implemented in this mission.

A human decision is still required before write-capable Builder implementation
because the exact draft surface is not yet selected.

---

## Learning

- Draft creation is an L2 authority problem, while canonical promotion remains
  a Governance Protocol Change Proposal problem.
- The Guided Bootstrap apply model is reusable, but Builder draft creation is
  narrower: it must create only draft surfaces and must not imply successful
  bootstrap or canonical context.
- The next hard decision is draft surface selection, not content generation.
- Builder write behavior should begin with a preflight/authorization object,
  not direct `build-mom` writes.

---

## Roadmap Impact

v0.5 remains on track.

The release now has the authority contract needed before write-capable Builder
draft behavior. No release sequencing change is required.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the Builder Draft Authority
  mission.
