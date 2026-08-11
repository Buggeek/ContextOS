# E.4 Mission V05-BUILDER-DRAFT-REVIEW-DECISION-001 - Draft Review Decision
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Establish the first governed human Review Decision for Draft Workspace
artifacts.

The decision records the outcome of reviewing an exact draft review object
without approving, promoting, or canonicalizing the draft.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V05-BUILDER-DRAFT-REVIEW-DECISION-001
  title: Draft Review Decision
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

Added `BuilderDraftReviewDecisionEngine`, a governed review-decision engine for
draft artifacts previously exposed through `BuilderDraftReviewEngine`.

Machine report schema:

```text
contextos.builder.draft_review_decision/1
```

The decision consumes:

```text
contextos.builder.draft_review/1
```

It may be persisted as a JSON governance/evidence artifact, but it does not
mutate the reviewed draft, approve context, promote context, or write canonical
SSOT.

---

## Allowed Outcomes

| Outcome | Meaning | Next permitted transition |
|---|---|---|
| `reviewed_ready_for_next_governance_step` | Human review found the draft ready for a separate governance step | `approval_proposal_allowed` |
| `changes_requested` | Human review requires revision before any later governance step | `draft_revision_required` |
| `rejected` | Human rejected the draft for continuation unless new evidence appears | `terminal_rejected_unless_new_evidence` |
| `insufficient_evidence` | Review could not proceed because evidence is insufficient | `evidence_collection_required` |
| `superseded` | A newer draft or evidence set replaces this review target | `newer_draft_required` |

No outcome grants approval, promotion, canonical verification, or SSOT mutation
authority.

---

## Authority Model

A Review Decision requires explicit human L2 authority:

```text
capability: builder.draft.review
authority_level: L2
reviewed_by: explicit human identity
reviewer_role: role satisfying the draft's required review role
rationale: explicit reviewer rationale
```

The reviewer role must satisfy the role required by the draft review and the
role that authorized the source draft write.

---

## Identity Binding

The decision binds to:

- draft review id,
- draft review identity hash,
- draft item id,
- Draft Workspace path,
- draft content hash,
- source Mission,
- source draft write result id/hash,
- source Draft Workspace preflight id/hash,
- source Builder Draft Plan hash,
- Discovery/Construction provenance,
- evidence references,
- reviewer identity and authority.

A changed draft, review identity, Draft Workspace path, source preflight, source
Builder Draft Plan hash, authority, or Validator gate invalidates the decision.

---

## Lifecycle Boundary

This mission preserves:

```text
Review Decision != Approval != Canonical Truth
```

A Review Decision may move the draft review state to a recorded review outcome,
but it does not perform:

- `draft -> approved`,
- `draft -> canonical/verified`,
- promotion to SSOT,
- canonical context mutation.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| `BuilderDraftReviewDecisionEngine` implemented | `contextos.builder.draft_review_decision/1` created |
| Allowed outcome tests | Every outcome has an explicit next permitted transition |
| Authority tests | L2 `builder.draft.review` and satisfying reviewer role required |
| Identity tests | Decision binds review identity and draft content hash |
| Invalidation tests | Changed draft invalidates prior review decision |
| Persistence tests | JSON governance artifact can be written without mutating the draft |
| Boundary tests | Decision does not approve, promote, or canonicalize |
| Human renderer tests | Human report names review-not-approval boundary |
| Regression tests | Builder, Discovery, Construction, Readiness, Bootstrap, Validator, and CLI tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Whitespace validation | `git diff --check` passed |

---

## Learning

- Review Decision is the correct next lifecycle object after read-only review;
  it records human judgment without crossing into approval.
- Binding the decision to the draft content hash is necessary because a draft
  edit must not inherit review state silently.
- The outcome vocabulary should stay small until approval and promotion exist.
- CLI exposure remains premature until the review-decision object is consumed
  by the next governed transition.

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
```

The chain still stops before approval, promotion, and canonical SSOT mutation.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the Draft Review Decision mission.
