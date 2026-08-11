# EPIC-006 — Context Builder

- **Epic ID:** EPIC-006
- **Version:** v0.4/v0.5 — Guided Bootstrap and Context Construction
- **Status:** Active
- **Owner:** Runtime Owner

---

## Product Journey Position

Builder work is split between guidance and construction.

- v0.3 Context Readiness may use Builder-owned mapping rules only to turn
  findings into recommended next actions.
- v0.4 Guided Bootstrap uses Builder slices for scaffolds and reviewable
  draft artifacts.
- v0.5 Context Construction implements the governed construction path from
  structured Discovery output to MOM/SSOT drafts.

The Builder must not become the first v0.3 value moment; users need assessment
before generated artifacts.

---

## Objective

Build the **Context Builder**: the Runtime component that composes MOM
drafts and promotes them into SSOT, fusing Discovery output, Knowledge
interpretations, and existing SSOT under the governance protocol.

---

## Problem

Discovery and Knowledge produce inputs, but no Runtime component composes
them into the canonical SSOT shape. Today, Bootstrap Steps 6 and 7 are
manual — a Maintainer hand-edits MOM and SSOT files. This is not
repeatable, not auditable, and does not scale.

---

## Scope

v0.3 Context Readiness slice:

- Recommendation mapping from readiness findings to next bootstrap,
  remediation, or construction actions.
- No repository mutation.
- Recommendation ids, priorities, categories, and target journey steps follow
  the
  [`Context Readiness Assessment Contract`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md).

v0.4 Guided Bootstrap slice:

- Draft/scaffold generation for required Context OS artifacts.
- Hypothesis vs Verified tagging applied to generated drafts.
- Validator gate checks before any promotion path is offered.

v0.5 Context Construction expansion:

- `contextos.construction.plan/1` planning object that turns readiness,
  inventory, validator, and bootstrap evidence into governed construction
  candidates without writing files or promoting truth.
- `contextos.builder.draft_plan/1` planning object that determines which
  candidates can responsibly become future drafts, with provenance, support
  level, unknowns, contradictions, authority requirements, and promotion
  restrictions.
- Builder Draft Authority Contract defining conditions before any draft write:
  L2 draft authority, human review, evidence sufficiency, target-scope,
  no-overwrite, drift, validation, rollback, and promotion prohibition.
- Draft Workspace decision defining the universal non-canonical workspace for
  generated/co-created draft context. The current local runtime maps this to
  `.contextos/drafts/`.
- `contextos.builder.draft_workspace_preflight/1` read-only runtime object
  that resolves `.contextos/drafts/`, checks target isolation, no-overwrite,
  plan drift, Validator gate, and future L2 draft eligibility before any write.
- `contextos.builder.draft_write_result/1` create-only write result for
  explicitly authorized draft artifacts inside `.contextos/drafts/`, preserving
  provenance, unknowns, missing evidence, contradictions, and non-canonical
  lifecycle state.
- `contextos.builder.draft_review/1` read-only review object that exposes
  identity, evidence, observed/inferred/suggested/draft boundaries,
  uncertainty, validation, no-overwrite evidence, authority still required, and
  promotion restrictions.
- `contextos.builder.draft_review_decision/1` governed human review-decision
  object that records an explicit L2 `builder.draft.review` outcome for an
  exact draft review and draft content hash without approving, promoting, or
  canonicalizing the draft.
- `contextos.builder.draft_approval_decision/1` governed human
  approval-decision object that records explicit L3 `builder.draft.approve`
  approval for an exact eligible Review Decision without promoting, writing
  SSOT, or canonicalizing the draft.
- `contextos build-mom` implementation per the CLI Contract.
- `contextos build-ssot` implementation per the CLI Contract.
- Mapping rules from Discovery Bundle + Interpretation drafts to MOM
  artifact classes (System Map, Data Entities, Product Map, Vision draft).
- Change Proposal emission per the Governance Protocol §4.

---

## Out of Scope

- Full Context Graph runtime (deferred to Organizational Memory / later
  Runtime releases).
- Knowledge interpretation logic (EPIC-005).
- Validator (EPIC-007); Builder consumes the Validator but does not
  implement rules.
- Long-term draft storage UI.
- Any v0.3 automatic write or promotion behavior.

---

## Expected Outcomes

- v0.3: readiness findings can be translated into clear next actions using
  the canonical recommendation taxonomy.
- v0.4: a fresh repository can move from readiness to guided bootstrap
  drafts.
- v0.5 first slice: a repository can produce a construction plan that
  preserves observed/inferred/suggested/draft/reviewed/approved/canonical
  boundaries before any Builder writes.
- v0.5 Builder planning slice: a repository can produce a Builder Draft Plan
  that explains draftability without creating or promoting context.
- v0.5 Builder authority slice: write-capable draft generation has a
  decision-complete authority model before any Builder writes are implemented.
- v0.5 Draft Workspace decision: unapproved generated drafts have a governed
  non-canonical home before write-capable Builder behavior.
- v0.5 Draft Workspace runtime slice: future draft targets can be preflighted
  against `.contextos/drafts/` without creating directories, drafts, or SSOT
  artifacts.
- v0.5 create-only draft write slice: an exact eligible preflight plus explicit
  L2 `builder.draft.create` authority can create a non-canonical draft envelope
  in isolated/controlled targets only.
- v0.5 draft review slice: humans can inspect created draft envelopes without
  mutating, accepting, approving, or promoting them.
- v0.5 draft review decision slice: an explicitly identified and authorized
  human can record `reviewed_ready_for_next_governance_step`,
  `changes_requested`, `rejected`, `insufficient_evidence`, or `superseded`
  against the exact reviewed draft while preserving non-canonical status.
- v0.5 draft approval decision slice: an explicitly identified and authorized
  human can record `approved_for_promotion_proposal`, `approval_rejected`, or
  `approval_deferred` against the exact eligible Review Decision while leaving
  promotion and canonical context writes unauthorized.
- v0.5 later slices: a repository can run `init -> sources add -> scan -> build-mom ->
  build-ssot` end-to-end and produce a usable SSOT skeleton.
- Every produced artifact carries the required ownership and belief-state
  metadata.
- Promotion (`build-ssot`) is governed by Change Proposals, not silent
  writes.

---

## Dependencies

- EPIC-004 (Discovery Engine)
- EPIC-005 (Knowledge Engine)
- EPIC-007 (Validator Engine) — Builder calls Validator in `gate` mode at
  promotion time.
- EPIC-008 (Runtime CLI)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.3_Context_Graph_Schema.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.3_Context_Graph_Schema.md)
- [`../../docs/3.x_operation/3.7_COS_Governance_Protocol.md`](../../docs/3.x_operation/3.7_COS_Governance_Protocol.md)

---

## Success Criteria

- v0.3 readiness recommendations use stable ids of the form
  `readiness.<category>.<action>`.
- `build-mom` produces MOM drafts that conform to existing templates under
  `templates/`.
- `build-ssot` emits Change Proposals for every artifact write above L2.
- Promotion is blocked when Validator returns `error` findings in `gate`
  mode.
- Re-running `build-mom` on unchanged inputs produces identical drafts.
- Worked example: bootstrap of `examples/sample_solo_founder` completes
  end-to-end.

---

## Definition of Ready (DoR)

- v0.3 recommendation taxonomy is current in the Context Readiness Assessment
  Contract.
- Mapping rules from Discovery + Knowledge to MOM classes are documented.
- Hypothesis vs Verified tagging convention is published in `3.5 POM`.
- CLI surface for `build-mom` and `build-ssot` matches the CLI Contract.
- Governance roster requirement is enforced before `build-ssot` runs.

---

## Definition of Done (DoD)

- v0.3 slice: readiness recommendations are generated without writing files
  and are covered by tests.
- End-to-end bootstrap demonstrated on both example organizations.
- Every produced artifact is owned, taxonomy-compliant, and traceable.
- Change Proposals recorded for every promotion.
- Validator gate enforced on promotion.
- `builder.mom.proposed` and `builder.ssot.promoted` events emitted.

---

## Related Artifacts

- [`../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md) §Steps 6–7
- [`../../docs/3.x_operation/3.5_COS_Product_Operating_Model.md`](../../docs/3.x_operation/3.5_COS_Product_Operating_Model.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md)
- [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
