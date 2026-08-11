# E.4 Mission V05-BUILDER-DRAFT-PROMOTION-PREFLIGHT-001 - Draft Promotion Preflight
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Establish the final read-only Promotion Preflight required before an approved
Draft Workspace artifact may become eligible for canonical promotion.

The preflight answers:

```text
Is this exact approved draft still safe, valid, authorized, and semantically
eligible to be considered for canonical promotion now?
```

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V05-BUILDER-DRAFT-PROMOTION-PREFLIGHT-001
  title: Draft Promotion Preflight
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

Added `BuilderDraftPromotionPreflightEngine`, a read-only promotion-preflight
engine for exact Draft Approval Decisions.

Machine report schema:

```text
contextos.builder.draft_promotion_preflight/1
```

The preflight consumes:

```text
contextos.builder.draft_approval_decision/1
```

It may determine that an approved draft is eligible for a future promotion
confirmation, but it does not authorize promotion, authorize canonical mutation,
write SSOT, mutate canonical context, or mutate the draft.

---

## Eligibility Model

Promotion Preflight requires:

- exact Approval Decision identity/hash,
- exact Review Decision identity/hash,
- successful approval outcome `approved_for_promotion_proposal`,
- exact draft content hash unchanged since approval,
- exact Draft Workspace path unchanged,
- Builder Draft Plan identity preserved,
- Discovery/Construction provenance preserved,
- L3 `builder.draft.approve` authority still valid,
- no unresolved contradictions,
- unknowns and missing evidence preserved,
- explicit target canonical artifact/path,
- target canonical state unchanged since approval,
- Validator gate with no errors or fatals,
- explicit promotion scope,
- no-overwrite or governed replacement-policy stance.

The preflight sets:

```text
eligible_for_promotion: true
```

only when all checks pass.

It always keeps:

```text
promotion_authorized: false
canonical_mutation_authorized: false
```

---

## Canonical Target Model

The current local runtime uses the approved draft's
`target_context_artifact` as the candidate canonical path.

The preflight captures:

- target canonical path,
- target state at approval time,
- current target state,
- whether target state changed since approval.

For v0.5, promotion execution is not implemented. The preflight may freeze one
of two candidate write-set actions:

| Action | Meaning |
|---|---|
| `create_canonical_candidate` | Target is missing and create-only promotion could be proposed later |
| `propose_governed_replacement_candidate` | Target exists and a future governed replacement review would be required |

Neither action authorizes mutation.

---

## Drift and Invalidation

Promotion eligibility is invalidated by:

- Approval Decision identity change,
- Review Decision identity change,
- draft content hash change,
- Draft Workspace path change,
- Builder Draft Plan hash change,
- Discovery/Construction provenance change,
- canonical target state change,
- Validator gate failure,
- authority change,
- promotion scope change.

The preflight must not silently regenerate approved intent or reinterpret the
draft.

---

## Boundary

This mission preserves:

```text
Approved != Promoted
Promoted != Canonical Truth until governed validation succeeds
```

Promotion Preflight performs no:

- promotion execution,
- SSOT write,
- canonical context mutation,
- draft mutation,
- Knowledge Engine reasoning,
- Context Graph runtime,
- agent orchestration,
- external connector use.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| `BuilderDraftPromotionPreflightEngine` implemented | `contextos.builder.draft_promotion_preflight/1` created |
| Eligibility tests | Eligible preflight keeps promotion/canonical mutation unauthorized |
| Canonical policy tests | Create-only blocks existing canonical target without replacement stance |
| Draft drift tests | Draft content changes block preflight |
| Canonical target drift tests | Target canonical state changes block preflight |
| Approval state tests | Deferred/non-approved decisions cannot preflight as eligible |
| Persistence tests | JSON preflight can be written without mutating target repo |
| Human renderer tests | Human report names approved-not-promoted boundary |
| Regression tests | Builder, Discovery, Construction, Readiness, Bootstrap, Validator, and CLI tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Whitespace validation | `git diff --check` passed |

---

## Learning

- Promotion preflight needs canonical target baseline evidence from the Approval
  Decision; the approval artifact now records canonical target state.
- Existing canonical targets should not be silently overwritten. v0.5 can only
  freeze a governed replacement candidate; execution remains future work.
- Preflight eligibility is still weaker than promotion authority. A separate
  human promotion confirmation and canonical-write mission are required.

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
```

The chain still stops before promotion execution and canonical SSOT mutation.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the Draft Promotion Preflight mission.
