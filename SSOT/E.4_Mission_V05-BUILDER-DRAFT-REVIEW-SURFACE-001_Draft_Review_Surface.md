# E.4 Mission V05-BUILDER-DRAFT-REVIEW-SURFACE-001 - Draft Review Surface
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Establish the first governed, read-only human review surface for Draft
Workspace artifacts.

The review surface lets a human understand what Context OS created, why it was
created, what evidence supports it, what remains uncertain, and what cannot
happen next without additional authority.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V05-BUILDER-DRAFT-REVIEW-SURFACE-001
  title: Draft Review Surface
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

Added `BuilderDraftReviewEngine`, a read-only review engine for draft artifacts
created by `BuilderDraftCreateEngine`.

Machine report schema:

```text
contextos.builder.draft_review/1
```

The review surface consumes:

```text
contextos.builder.draft_write_result/1
```

It does not mutate the draft, persist a review decision, approve context, or
promote anything into SSOT.

---

## Review Model

Each review exposes:

- draft identity,
- Draft Workspace path,
- target organizational context artifact,
- lifecycle state,
- canonical status,
- content representation,
- source Mission,
- source Draft Workspace preflight,
- source Builder Draft Plan hash,
- Discovery/Construction provenance,
- evidence references,
- support classification,
- unknowns,
- missing evidence,
- contradictions,
- validation evidence,
- no-overwrite evidence from the write result,
- promotion restrictions,
- authority still required,
- recommended next action.

---

## Truth Boundary

The review object explicitly separates:

| State | Meaning |
|---|---|
| observed | Source evidence and draft file existence were observed |
| inferred | Classification and support are planning interpretations |
| suggested | Target context artifact came from a construction/draft plan |
| drafted | Non-canonical draft envelope exists in the Draft Workspace |
| unknown | Unknowns, missing evidence, and contradictions remain unresolved |
| approved truth | No approved or canonical truth is created by review |

This answers the central product question: a human can distinguish observed,
inferred, suggested, drafted, unknown, and approved truth states from the review
surface itself.

---

## Interface Decision

This mission adds an engine/report surface only.

A Runtime CLI surface is deferred because the smallest coherent product proof
is the reusable review object plus human renderer. Future CLI, web, IDE,
workflow, or non-filesystem organizational surfaces can consume the same
`contextos.builder.draft_review/1` object.

---

## Boundaries

The review surface does not:

- mutate draft artifacts,
- imply acceptance,
- persist review decisions,
- approve context,
- promote context,
- write SSOT,
- write canonical context,
- use Knowledge Engine,
- use Context Graph,
- use agents,
- use external connectors.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| `BuilderDraftReviewEngine` implemented | `contextos.builder.draft_review/1` created |
| Human renderer implemented | Review names truth boundary and read-only guarantee |
| Read-only tests | Review does not mutate draft files |
| Provenance tests | Source preflight, Builder Draft Plan, Discovery/Construction evidence visible |
| Uncertainty tests | Unknowns, missing evidence, and contradictions visible |
| Authority tests | Review/approval/promotion authority remains required |
| Unsafe metadata tests | Draft claiming canonical status blocks review |
| Missing draft tests | Missing artifact produces blocked review |
| Isolated dogfood | Review exercised after real draft write in temporary Context OS copy |
| Regression tests | Builder, Discovery, Construction, Readiness, Bootstrap, Validator, and CLI tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Whitespace validation | `git diff --check` passed |

---

## Learning

- Review should be a reusable product object before it is a CLI command.
- Draft review must not collapse uncertainty into acceptance.
- A draft envelope that claims canonical/reviewed/approved state is unsafe and
  should block review.
- The next lifecycle transition is a governed review decision, not promotion.

---

## Current v0.5 Impact

v0.5 now supports create-only draft writing in controlled targets and a
read-only review surface that explains the draft before any approval or
promotion exists.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the Draft Review Surface mission.
