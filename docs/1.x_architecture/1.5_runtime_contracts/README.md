# 1.5 — Runtime Contracts

This folder contains the **architecture-level contracts** that the Context OS
Runtime must satisfy. These contracts are **specifications**, not
implementations. They define the surface area Codex (or any implementer) is
expected to build against.

| Contract | Purpose | Implemented by |
|---|---|---|
| [Validator Contract](1.5.1_Validator_Contract.md) | Rule categories, inputs/outputs, error schema, exit codes | EPIC-007 Validator Engine |
| [CLI Contract](1.5.2_CLI_Contract.md) | `contextos` command surface, I/O shapes | EPIC-008 Runtime CLI |
| [Context Graph Schema](1.5.3_Context_Graph_Schema.md) | Node/edge types, identity, derivation, invariants | EPIC-006 Context Builder + future Graph Runtime |
| [Mission Contract](1.5.4_Mission_Contract.md) | Mission Packet structure, lifecycle states, ownership | Orchestrator + Mission Lifecycle |
| [Runtime Event Model](1.5.5_Runtime_Event_Model.md) | Event taxonomy, payload shapes, ordering, observability | Runtime event bus |
| [Context Readiness Assessment Contract](1.5.6_Context_Readiness_Assessment_Contract.md) | v0.3 readiness dimensions, scoring, report schema, recommendations | EPIC-004 + EPIC-006 + EPIC-007 + EPIC-008 |
| [Bootstrap Apply Approval Contract](1.5.7_Bootstrap_Apply_Approval_Contract.md) | Proposal identity, approval, validation, rollback, and evidence rules for future Guided Bootstrap apply | EPIC-006 + EPIC-007 + EPIC-008 |
| [Builder Draft Authority Contract](1.5.8_Builder_Draft_Authority_Contract.md) | Authority, evidence, no-overwrite, drift, validation, and rollback rules before Builder draft writes | EPIC-006 + EPIC-007 |
| [Context Activation Package Contract](1.5.9_Context_Activation_Package_Contract.md) | Mission-bound working-context package identity, provenance, freshness, permissions, and invalidation | EPIC-008 + Activation Layer |
| [Context Health Report Contract](1.5.10_Context_Health_Report_Contract.md) | Evidence-first integrity, usefulness, learning signals, and governed context update candidates | Context Health Engine + EPIC-007 |

## Rules

1. Contracts are **versioned**. Breaking changes require a governance decision.
2. Contracts are **observable**: every contract declares what is visible at
   runtime and how it is observed.
3. Contracts **bind to autonomy levels**: each action surface declares the
   minimum authority required per
   [`3.6 Human-Agent Authority Model`](../../3.x_operation/3.6_COS_Human_Agent_Authority_Model.md).
4. Contracts are **transport-agnostic**. They describe shapes, not protocols.
5. Contracts are **the only spec** an implementer needs to satisfy for the
   covered surface.

## Cross-References

- [`1.4 Context Runtime Architecture`](../1.4_COS_Context_Runtime_Architecture.md)
- [`3.4 Operational Lifecycle`](../../3.x_operation/3.4_COS_Operational_Lifecycle.md)
- [`3.6 Human-Agent Authority Model`](../../3.x_operation/3.6_COS_Human_Agent_Authority_Model.md)
- [`5.4 Product Roadmap`](../../5.x_strategy/5.4_COS_Product_Roadmap.md)
