# E.4 Mission V05-BUILDER-DRAFT-APPROVAL-DECISION-001 - Draft Approval Decision
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Establish the minimum governed Approval Decision capability for reviewed Draft
Workspace artifacts.

The Approval Decision records explicit organizational approval of an exact
reviewed draft without promoting it, writing canonical context, or mutating
SSOT.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V05-BUILDER-DRAFT-APPROVAL-DECISION-001
  title: Draft Approval Decision
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

Added `BuilderDraftApprovalDecisionEngine`, a governed approval-decision engine
for exact Draft Review Decisions.

Machine report schema:

```text
contextos.builder.draft_approval_decision/1
```

The decision consumes:

```text
contextos.builder.draft_review_decision/1
```

It may be persisted as a JSON governance/evidence artifact, but it does not
mutate the draft, promote context, write SSOT, or create canonical truth.

---

## Allowed Outcomes

| Outcome | Meaning | Next permitted transition |
|---|---|---|
| `approved_for_promotion_proposal` | Draft is approved as input to a separate governed promotion proposal | `promotion_proposal_allowed` |
| `approval_rejected` | Approval is declined | `draft_revision_or_review_required` |
| `approval_deferred` | Approval waits for more evidence or authority | `evidence_or_authority_required` |

No outcome grants promotion, canonical verification, or SSOT mutation authority.

---

## Authority Model

An Approval Decision requires explicit human L3 authority:

```text
capability: builder.draft.approve
authority_level: L3
approved_by: explicit human identity
approver_role: role satisfying the draft's required role
approval_scope: draft_for_future_promotion_proposal
rationale: explicit approver rationale
```

The approver role must satisfy the role required by the source Review Decision.

---

## Eligibility Rules

Approval may be recorded only when:

- the Review Decision is authentic and unchanged,
- the Review Decision result succeeded,
- the Review Decision outcome is `reviewed_ready_for_next_governance_step`,
- the Draft Workspace artifact content hash is unchanged,
- the draft remains non-canonical,
- Builder Draft Plan identity is preserved,
- Discovery/Construction provenance is present,
- contradictions are absent for approval,
- Validator gate has no errors or fatals,
- authority and approval scope match exactly.

Unknowns and missing evidence remain visible in the Approval Decision; they are
not resolved by approval.

---

## Identity Binding

The decision binds to:

- Approval Decision id/hash,
- Review Decision id/hash,
- draft item id,
- Draft Workspace path,
- draft content hash,
- source Mission,
- source draft write result id/hash,
- source Draft Workspace preflight id/hash,
- source Builder Draft Plan hash,
- Discovery/Construction provenance,
- reviewer identity and rationale,
- approver identity and rationale,
- evidence references,
- unresolved uncertainty.

A changed draft, changed Review Decision, material provenance drift, authority
mismatch, scope change, or Validator gate failure invalidates approval
eligibility.

---

## Lifecycle Boundary

This mission preserves:

```text
Review Decision != Approval Decision
Approval Decision != Promotion
Promotion != Canonical Truth until governed validation succeeds
```

Approval can establish:

```text
draft -> approved
```

inside a governance/evidence artifact only.

It does not perform:

- `approved -> promoted`,
- `promoted -> canonical/verified`,
- SSOT mutation,
- canonical context mutation.

Approved draft content remains:

```text
canonical: false
promotion_authorized: false
```

---

## Evidence Captured

| Evidence | Result |
|---|---|
| `BuilderDraftApprovalDecisionEngine` implemented | `contextos.builder.draft_approval_decision/1` created |
| Allowed outcome tests | Every outcome preserves promotion boundary |
| Eligibility tests | Only `reviewed_ready_for_next_governance_step` can be approved |
| Authority tests | L3 `builder.draft.approve` and satisfying approver role required |
| Identity tests | Approval binds Review Decision and draft content hash |
| Invalidation tests | Changed draft blocks and invalidates approval |
| Persistence tests | JSON governance artifact can be written without mutating the draft |
| Boundary tests | Approval does not promote, canonicalize, or write SSOT |
| Human renderer tests | Human report names approval-not-promotion boundary |
| Regression tests | Builder, Discovery, Construction, Readiness, Bootstrap, Validator, and CLI tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Whitespace validation | `git diff --check` passed |

---

## Learning

- Approval must consume a Review Decision, not a raw draft or regenerated
  review.
- L3 `builder.draft.approve` is the correct authority boundary because the
  decision changes lifecycle status while still avoiding repository mutation.
- Approval should make promotion proposal possible, not perform promotion.
- Unknowns and missing evidence can remain visible through approval; unresolved
  contradictions block approval.

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
```

The chain still stops before promotion and canonical SSOT mutation.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the Draft Approval Decision mission.
