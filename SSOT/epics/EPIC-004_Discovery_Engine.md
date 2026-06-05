# EPIC-004 — Discovery Engine

- **Epic ID:** EPIC-004
- **Version:** v0.3/v0.5 — Context Readiness and Context Construction
- **Status:** Planned
- **Owner:** Runtime Owner

---

## Product Journey Position

Discovery is sliced across the product journey.

- v0.3 Context Readiness uses a read-only local repository inventory to help
  answer "what context exists here?"
- v0.5 Context Construction expands Discovery into a structured Discovery
  Bundle consumed by the Builder.

External connectors, conflict events, and broad source registry behavior are
not required for the v0.3 readiness outcome.

---

## Objective

Build the **Discovery Engine** in progressive slices: first a local repository
inventory for Context Readiness, then a structured Discovery Bundle consumed
by the Context Builder.

---

## Problem

Today, organizational context is scattered across disconnected systems. Any
Context OS instance starts from a blank SSOT and must be hand-bootstrapped.
Without discovery, Bootstrap Step 3 has no machine-readable input, and
hypotheses can never be cross-checked against reality.

---

## Scope

v0.3 Context Readiness slice:

- Local repository inventory of Context OS-relevant artifacts, directories,
  runtime files, and documentation signals.
- Read-only structured output that can feed a Context Readiness Assessment.
- Gap signals for missing context, governance, ownership, and source evidence.
- No writes and no external authentication.

v0.5 Context Construction expansion:

- Connector Manifest schema and CLI surface
  (`contextos sources add|list|remove`).
- Reference connectors for at least: local filesystem (a repository),
  GitHub repository metadata, and a generic JSON/YAML import.
- Discovery Bundle output schema (artifacts, entities, systems, owners,
  raw observations) with `belief_state = observed`.
- Idempotent scans (`contextos scan`) with `--source` filter.
- Conflict reporting against existing SSOT.

---

## Out of Scope

- Knowledge Engine interpretation (EPIC-005).
- SSOT promotion of discovered facts (EPIC-006).
- Validator drift rule implementation against discovery output (EPIC-007).
- Long-lived watcher / push-based subscriptions.
- Authentication beyond basic credentials/token via environment.
- Any v0.3 requirement to scan external systems.

---

## Expected Outcomes

- v0.3: a reproducible local inventory that helps a user understand current
  repository context and readiness gaps.
- v0.5: a reproducible scan of a target organization producing a valid
  Discovery Bundle in <60s for a small org (≤50 sources).
- Discovery Bundle schema is stable enough for the Context Builder to
  consume without per-connector branching.
- Conflicts between Discovery output and SSOT are surfaced as
  `discovery.conflict.detected` events
  (see [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md)).

---

## Dependencies

- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md)
- [`../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md) §Step 3
- EPIC-008 (CLI skeleton) is a soft precondition.

---

## Success Criteria

- v0.3 readiness inventory is read-only, deterministic on unchanged input,
  and consumable by the Context Readiness Assessment.
- Three reference connectors implemented and covered by tests.
- `contextos scan` returns exit code 0 on success, exit code 4 on connector
  failure, and writes a Discovery Bundle to a deterministic path.
- Discovery Bundle validates against its declared schema.
- Conflict detection emits the canonical event with `evidence_refs`
  populated.
- Re-running `contextos scan` with no changes produces an identical bundle
  (bit-for-bit modulo timestamps).

---

## Definition of Ready (DoR)

- v0.3 readiness inventory fields are agreed before implementation.
- Connector Manifest schema is frozen.
- Discovery Bundle schema is frozen.
- Reference connectors and target sources are agreed.
- CLI surface for `sources` and `scan` is unambiguous per the CLI Contract.

---

## Definition of Done (DoD)

- v0.3 slice: local inventory feeds a Context Readiness Assessment and is
  covered by tests.
- All three reference connectors merged, tested, and documented.
- `contextos scan` integrated with the event bus per the Runtime Event Model.
- Bundle output included in the Bootstrap walkthrough.
- A worked example under `examples/` demonstrates a successful scan.
- Validator drift rule (EPIC-007) has a stable input from this engine.

---

## Related Artifacts

- [`../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md)
- [`../../docs/4.x_adoption/4.5_COS_Runtime_Installation.md`](../../docs/4.x_adoption/4.5_COS_Runtime_Installation.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md)
- [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
