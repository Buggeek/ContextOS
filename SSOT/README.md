# Context OS Project SSOT

Compliance profile: `strict`

This folder is the **Single Source of Truth (SSOT)** for the Context OS project itself.

It is a **dogfooding SSOT**: it intentionally goes beyond the Minimum Operational Map (MOM) to include execution artifacts that govern the framework's own evolution.

## Minimum Operational Map (MOM)

- S.1 Vision
- P.1 Product Map
- A.1 System Map
- A.4 Data Entities
- G.1 Definition of Ready
- G.2 Definition of Done

## Execution Artifacts (Dogfooding)

- P.2 Product Roadmap — versioned releases (v0.1 -> v1.0) toward the Organizational Context Runtime
- P.5 Epic — Structural Integrity
- E.1 User Story — US-001 Canonicalize Operational Docs Path
- `epics/` — Epic backlog derived from the roadmap (see [`epics/README.md`](epics/README.md))

These artifacts demonstrate Context OS governing its own structural changes.

> Narrative strategy (Framework vs. Runtime, long-term vision) lives in
> [`../docs/1.x_architecture/1.0_COS_Architecture.md`](../docs/1.x_architecture/1.0_COS_Architecture.md),
> [`../docs/5.x_strategy/5.3_COS_Runtime_Strategy.md`](../docs/5.x_strategy/5.3_COS_Runtime_Strategy.md)
> and [`../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../docs/5.x_strategy/5.4_COS_Product_Roadmap.md).
> The SSOT roadmap stays concise and execution-oriented.

> **SSOT taxonomy note.** In this dogfooding SSOT, `P.2` is used for **Product Roadmap**.
> The framework taxonomy ([`../docs/2.x_taxonomy/2.0_COS_Document_Taxonomy.md`](../docs/2.x_taxonomy/2.0_COS_Document_Taxonomy.md))
> reserves `P.2` for Feature Catalog and `P.3` for Roadmap; Context OS does not yet
> need a Feature Catalog, so the Product layer is collapsed to `P.1 Product Map`,
> `P.2 Product Roadmap`, `P.5 Epic_[Name]`. A future taxonomy update may reconcile this.
