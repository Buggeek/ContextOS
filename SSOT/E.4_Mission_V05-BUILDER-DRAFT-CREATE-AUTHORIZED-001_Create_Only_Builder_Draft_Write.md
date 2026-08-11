# E.4 Mission V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001 - Create-Only Builder Draft Write
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Implement the first governed, create-only Builder draft write capability.

This mission proves that Context OS can create non-canonical draft artifacts
inside the governed Draft Workspace after explicit L2 human authorization while
preserving the boundary between evidence-supported drafts and canonical
organizational truth.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001
  title: Create-Only Builder Draft Write
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

Added `BuilderDraftCreateEngine`, a create-only writer gated by:

```text
contextos.builder.draft_workspace_preflight/1
```

Machine result schema:

```text
contextos.builder.draft_write_result/1
```

Rollback schema:

```text
contextos.builder.draft_rollback_result/1
```

---

## Governed Chain

The capability preserves:

```text
Discovery Bundle
-> Construction Plan
-> Builder Draft Plan
-> Draft Authority
-> Draft Workspace
-> Draft Workspace Preflight
-> Explicit Human Draft Authorization
-> Create-only Draft Write
-> Post-write Validation
-> Evidence
-> Result
```

It consumes the preflight as the executable boundary. It does not regenerate
approved intent during write.

---

## Authorization Model

Draft creation requires explicit human authorization bound to:

- Mission id,
- Draft Workspace preflight id,
- Draft Workspace preflight identity hash,
- Builder Draft Plan hash,
- authorized draft item ids,
- authorized Draft Workspace target paths,
- L2 authority level,
- `builder.draft.create` capability,
- authorizing human identity,
- authorizing role satisfying the required target role.

Authorization does not imply review, approval, promotion, or canonical write
authority.

---

## Draft Artifact Representation

The first written draft representation is a visible non-canonical draft
envelope:

```text
contextos.builder.draft_artifact/1
```

It is written under:

```text
.contextos/drafts/<mission_id>/artifacts/<target_context_artifact>
```

The artifact explicitly declares:

- lifecycle state `draft`,
- `canonical: false`,
- reviewed false,
- approved false,
- canonical verified false,
- promotion authorized false,
- source preflight id/hash,
- source Builder Draft Plan hash,
- draft item id,
- target context artifact,
- provenance chain,
- evidence refs,
- unknowns,
- missing evidence,
- contradictions.

No organizational truth content is synthesized in this first write slice.

---

## Safeguards

The writer refuses to proceed when:

- explicit create confirmation is missing,
- L2 authority is missing,
- capability is not `builder.draft.create`,
- preflight identity/hash is invalid,
- preflight file is not preserved,
- preflight is not eligible,
- source plan identity is not bound,
- preflight validation checks failed,
- authorization is not bound to the exact mission/preflight/plan,
- authorized item ids or target paths differ,
- target role is not satisfied,
- target already exists,
- target is outside `.contextos/drafts/`,
- Validator gate has `error` or `fatal`.

Writes are create-only. The writer performs no overwrite, replacement,
deletion, SSOT write, canonical context write, review, approval, or promotion.

---

## Rollback

Rollback removes only draft artifacts created by the exact write result when
the current file hash still matches the recorded created hash.

Rollback may remove empty directories created by the same operation. It must
not remove pre-existing or user-modified content.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| `BuilderDraftCreateEngine` implemented | `contextos.builder.draft_write_result/1` created |
| Explicit L2 authorization tests | Missing/wrong authority blocks |
| Exact identity binding tests | Wrong preflight id blocks |
| Create-only tests | Draft created only under `.contextos/drafts/` in isolated copy |
| Non-canonical artifact tests | Draft declares `canonical: false` and lifecycle `draft` |
| No-overwrite tests | Repeated execution blocks |
| Ineligible preflight tests | No mutation when preflight is ineligible |
| Rollback tests | Removes matching created draft only |
| Modified rollback tests | User-modified draft is preserved |
| Post-write validation | Validator gate runs after write |
| Isolated dogfood | Real write exercised only in temporary Context OS copies |
| Regression tests | Builder, Discovery, Construction, Readiness, Bootstrap, Validator, and CLI tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Whitespace validation | `git diff --check` passed |

---

## Learning

- The first write-capable Builder slice should write a draft envelope, not
  generated organizational truth.
- Draft creation and promotion must remain separate operations with separate
  authority.
- A preserved Draft Workspace preflight is the right executable boundary for
  create-only draft writes.
- Real canonical Context OS draft creation remains a separate target-specific
  human decision.

---

## Current v0.5 Impact

v0.5 now has the first governed Builder write capability in isolated,
controlled form. It is not exposed through CLI and has not been applied to the
canonical Context OS repository.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the create-only Builder draft write mission.
