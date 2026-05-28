# EPIC-006 — Context Builder

- **Epic ID:** EPIC-006
- **Version:** v0.3 — Runtime Foundation
- **Status:** Planned
- **Owner:** Runtime Owner

---

## Objective

Build the **Context Builder v0**: the Runtime component that composes MOM
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

- `contextos build-mom` implementation per the CLI Contract.
- `contextos build-ssot` implementation per the CLI Contract.
- Mapping rules from Discovery Bundle + Interpretation drafts to MOM
  artifact classes (System Map, Data Entities, Product Map, Vision draft).
- Hypothesis vs Verified tagging applied to every produced artifact.
- Change Proposal emission per the Governance Protocol §4.

---

## Out of Scope

- Full Context Graph runtime (deferred to v0.6+).
- Knowledge interpretation logic (EPIC-005).
- Validator (EPIC-007); Builder consumes the Validator but does not
  implement rules.
- Long-term draft storage UI.

---

## Expected Outcomes

- A fresh repository can run `init → sources add → scan → build-mom →
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
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.3_Context_Graph_Schema.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.3_Context_Graph_Schema.md)
- [`../../docs/3.x_operation/3.7_COS_Governance_Protocol.md`](../../docs/3.x_operation/3.7_COS_Governance_Protocol.md)

---

## Success Criteria

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

- Mapping rules from Discovery + Knowledge to MOM classes are documented.
- Hypothesis vs Verified tagging convention is published in `3.5 POM`.
- CLI surface for `build-mom` and `build-ssot` matches the CLI Contract.
- Governance roster requirement is enforced before `build-ssot` runs.

---

## Definition of Done (DoD)

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
- [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
