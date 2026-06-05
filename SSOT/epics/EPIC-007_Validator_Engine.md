# EPIC-007 — Validator Engine

- **Epic ID:** EPIC-007
- **Version:** v0.3/v0.7 — Context Readiness and Context Health & Learning
- **Status:** Active
- **Owner:** Runtime Owner

---

## Product Journey Position

Validator is a foundational rail for multiple releases.

- v0.3 Context Readiness uses the shipped ValidatorEngine and
  `contextos validate` surface to produce structural and governance signals.
- v0.4/v0.5 use the Validator as the bootstrap and construction gate.
- v0.7 expands Validator output into routine Context Health and drift
  remediation workflows.

The v0 engine and reusable runtime component have shipped. Remaining contract
hardening is release-sliced instead of blocking the v0.3 readiness outcome.

---

## Objective

Build the **Validator Engine** that progressively implements the
[`Validator Contract`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.1_Validator_Contract.md):
a deterministic, read-only engine that protects contextual integrity by
evaluating a versioned rule set against SSOT, the runtime manifest, and
(when available) Discovery output.

---

## Problem

Structural integrity, naming conventions, taxonomy alignment, hypothesis
closure, and ownership coverage are currently enforced by hand and by
hand-grep. This does not scale. Without an automated Validator, every other
Runtime component lacks a trustworthy gate.

---

## Scope

Completed v0.3 foundation slice:

- Markdown/document structure validation.
- Naming convention validation.
- Internal reference/path validation.
- SSOT artifact required-field validation.
- Runtime doctrine term validation.
- Legacy path detection with allowlist support.
- JSON and human-readable report output.
- Non-zero exit code on blocking failures.
- Reusable `ValidatorEngine` runtime API.
- `contextos validate` integration through EPIC-008.

Future hardening slices:

- Implementation of the rule categories declared in §Rule Categories of the
  Validator Contract: `structure`, `naming`, `links`, `taxonomy`, `mom`,
  `hypothesis`, `authority`, `ownership`, `drift`, `governance`.
- Context Health Report producer (machine + human formats).
- Exit code surface (0 / 7 / 8 / 9) per Contract.
- Mode surface: `install-check`, `pre-bootstrap`, `full`, `gate`.
- Rule selection (`--rules <selector>`).
- `validation.*` event emission per the Runtime Event Model.

---

## Out of Scope

- Semantic prose evaluation.
- Automatic fixers (suggested fixes only; no application).
- Validator-driven mutations of any kind.
- Cross-repository validation in a single run (deferred).

---

## Expected Outcomes

- The Validator is the **gate** that other Runtime components consult.
- v0.3: local validation can run through both the ValidatorEngine API and
  `contextos validate`.
- `contextos validate` produces a deterministic Context Health Report on
  any repository under a Runtime manifest.
- The Validator is invoked at Bootstrap Step 8 and after every L3+
  Change Proposal application.

---

## Dependencies

- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.1_Validator_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.1_Validator_Contract.md)
- [`../../docs/2.x_taxonomy/2.0_COS_Document_Taxonomy.md`](../../docs/2.x_taxonomy/2.0_COS_Document_Taxonomy.md)
- [`../../docs/3.x_operation/3.7_COS_Governance_Protocol.md`](../../docs/3.x_operation/3.7_COS_Governance_Protocol.md)
- EPIC-008 (CLI surface).

---

## Success Criteria

- All ten rule categories implemented with at least one rule each.
- Validator produces stable report ids and stable finding ids across runs.
- `contextos validate --mode gate` blocks promotion in the Builder when
  any `error` finding exists.
- Validator runs to completion on both example organizations with zero
  fatal findings.
- Validator never writes to the repository.

---

## Definition of Ready (DoR)

- Validator Contract is current.
- Rule selector grammar is published.
- Report schema is versioned as `contextos.validator.report/1`.
- Exit code map matches the CLI Contract.

---

## Definition of Done (DoD)

- All declared rule categories shipped, documented, and tested.
- Reports validated against schema in CI.
- Documented integration points used by Builder, CLI `health`, and the
  Bootstrap walkthrough.
- `validation.run` event emitted on every invocation.

---

## Related Artifacts

- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.1_Validator_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.1_Validator_Contract.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md)
- [`../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md) §Step 8
- [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
