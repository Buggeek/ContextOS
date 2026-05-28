# EPIC-008 — Runtime CLI

- **Epic ID:** EPIC-008
- **Version:** v0.3 — Runtime Foundation
- **Status:** Planned
- **Owner:** Runtime Owner

---

## Objective

Implement the **`contextos` Runtime CLI** as specified by the
[`CLI Contract`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md):
the canonical human and automation entry point to the Runtime.

---

## Problem

Without a CLI, Context OS has no operational surface. Bootstrap, validation,
discovery, builder, and activation cannot be exercised in a uniform,
scriptable way. The CLI is the connective tissue between humans, agents,
and Runtime components.

---

## Scope

- `contextos init` (scaffolding + manifest).
- `contextos sources add|list|remove`.
- `contextos governance set-roster`.
- `contextos scan` (Discovery surface).
- `contextos build-mom`, `contextos build-ssot` (Builder surface).
- `contextos validate`, `contextos health` (Validator surface).
- `contextos activate` (Activation surface).
- Reserved-but-declared `contextos mission new|list|show|close` surface.
- Global flags: `--root`, `--format text|json`, `--quiet`, `--verbose`.
- Exit code map per the CLI Contract.
- `cli.run` event emission per the Runtime Event Model.

---

## Out of Scope

- Long-running daemon mode.
- IDE/Copilot surface activation (deferred to v0.7+).
- TUI / interactive shells.
- Web UI for Context Health Report.

---

## Expected Outcomes

- Every Bootstrap step from
  [`4.4`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md) is invokable
  via the CLI.
- Output is consistently structured: `result` or `error` under `--format
  json`.
- The CLI is the single integration point for other Runtime components.

---

## Dependencies

- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md)
- [`../../docs/4.x_adoption/4.5_COS_Runtime_Installation.md`](../../docs/4.x_adoption/4.5_COS_Runtime_Installation.md)
- Validator Engine (EPIC-007) for `validate` / `health`.

---

## Success Criteria

- All commands enumerated above implemented with their declared exit codes.
- `contextos validate` exit codes match the Validator Engine's outputs.
- `--format json` returns schema-valid output for every command.
- Help text for every command and subcommand is present and consistent.
- A scripted end-to-end bootstrap completes against
  `examples/sample_solo_founder` using only the CLI.

---

## Definition of Ready (DoR)

- CLI Contract is current and frozen for v0.3.
- Exit code map matches Validator Contract.
- Authority levels per command are reflected in confirmation prompts.

---

## Definition of Done (DoD)

- All v0.3 commands shipped, tested, and documented.
- JSON output schema validated in CI.
- `cli.run` event emitted on every invocation with `authority` populated.
- Installation walkthrough (`4.5`) updated to reference CLI behavior
  faithfully.

---

## Related Artifacts

- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md)
- [`../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md)
- [`../../docs/4.x_adoption/4.5_COS_Runtime_Installation.md`](../../docs/4.x_adoption/4.5_COS_Runtime_Installation.md)
- [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
