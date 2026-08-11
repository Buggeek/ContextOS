# E.4 Mission V05-BUILDER-DRAFT-PROMOTION-EXECUTE-001 - Draft Promotion Execute
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Implement the first governed canonical promotion capability for approved Draft
Workspace artifacts.

This mission permits controlled implementation and isolated testing only. It
does not authorize promotion of real Draft Workspace artifacts into the
canonical Context OS repository.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V05-BUILDER-DRAFT-PROMOTION-EXECUTE-001
  title: Draft Promotion Execute
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

## Capability

Added `BuilderDraftPromotionEngine`, a governed create-only promotion executor.

Machine report schema:

```text
contextos.builder.draft_promotion_result/1
```

Rollback report schema:

```text
contextos.builder.draft_promotion_rollback_result/1
```

The executor consumes:

```text
contextos.builder.draft_promotion_preflight/1
```

Promotion requires explicit human confirmation and may mutate only an isolated
target repository under controlled testing authority.

---

## Promotion Confirmation Model

Promotion confirmation must bind to:

- exact Mission Packet,
- exact Promotion Preflight id/hash,
- exact Approval Decision id/hash,
- exact draft item id,
- exact draft content hash,
- exact canonical target path,
- exact frozen promotion action,
- exact current canonical target state hash,
- explicit promoting human identity,
- satisfying role,
- L3 `builder.draft.promote` authority,
- canonical mutation scope.

The first supported mutation scope is:

```text
create_canonical_from_approved_draft
```

---

## Mutation Model

The first v0.5 implementation executes only:

```text
create_canonical_candidate
```

when the canonical target does not exist.

Blocked classes:

- existing canonical targets,
- governed replacement candidates,
- overwrites,
- replacements,
- deletions,
- repair workflows.

These remain blocked because the repository does not yet contain a
decision-complete governed replacement execution model.

---

## Epistemic Boundary

This mission preserves:

```text
Approved != Canonical
```

Canonical status may become true only after:

1. exact eligible preflight is consumed,
2. explicit human promotion confirmation is validated,
3. create-only canonical mutation succeeds,
4. post-promotion Validator gate succeeds,
5. final canonical metadata is written,
6. final Validator gate succeeds.

Failed validation is never represented as canonical success.

---

## Promoted Artifact Model

Promoted canonical artifacts include:

- SSOT-compatible H1,
- `Version`,
- `Owner`,
- JSON lineage metadata,
- source Promotion Preflight id/hash,
- source Approval Decision id/hash,
- source Review Decision id/hash,
- source Builder Draft Plan hash,
- source Discovery fingerprint,
- source Construction candidate id,
- source draft path/hash,
- target canonical path,
- evidence refs,
- unknowns,
- missing evidence,
- contradictions,
- exact approved draft content embedded as promoted source material.

---

## Rollback / Recovery

Rollback removes only artifacts created by the exact promotion result when the
current target hash still matches the recorded rollback hash.

Rollback must not remove:

- pre-existing canonical context,
- user-modified promoted artifacts,
- unrelated files,
- Draft Workspace evidence.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| `BuilderDraftPromotionEngine` implemented | `contextos.builder.draft_promotion_result/1` created |
| Confirmation tests | Promotion requires exact preflight and target binding |
| Create-only tests | Missing canonical target can be created and validated |
| Existing-target tests | Existing canonical target blocks without overwrite |
| Drift tests | Draft drift blocks without mutation |
| Idempotency tests | Repeated execution blocks as no-overwrite |
| Validation tests | Canonical success requires post-promotion Validator gate |
| Rollback tests | Rollback removes only matching created artifacts |
| Rollback safety tests | User-modified promoted artifact is not removed |
| Human renderer tests | Human report names canonical boundary and rollback |
| Regression tests | Builder, Discovery, Construction, Readiness, Bootstrap, Validator, and CLI tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Whitespace validation | `git diff --check` passed |

---

## Learning

- Create-only promotion can be implemented safely once it consumes an exact
  eligible preflight and exact human confirmation.
- Existing canonical targets require a separate governed replacement model; they
  should remain blocked rather than treated as a special case.
- Canonical status must be a validation outcome, not merely a write intent.
- Promotion execution needs rollback evidence at the mutation level, not only
  at the mission level.

---

## Current v0.5 Impact

v0.5 now supports this governed construction chain:

```text
Discovery Bundle
-> Construction Plan
-> Builder Draft Plan
-> Draft Workspace Preflight
-> Create-only Draft Write
-> Draft Review
-> Draft Review Decision
-> Draft Approval Decision
-> Draft Promotion Preflight
-> Create-only Canonical Promotion
-> Canonical Validation
-> Promotion Result
```

The chain still does not implement replacement, promotion CLI, Knowledge
Engine, Context Graph, agents, or external connectors.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the Draft Promotion Execute mission.
