# EPIC-008 — Runtime CLI

- **Epic ID:** EPIC-008
- **Version:** v0.3+ — Runtime CLI across the product journey
- **Status:** Active
- **Owner:** Runtime Owner

---

## Product Journey Position

The CLI is the stable runtime entry surface across the product journey.

- v0.3 has shipped `contextos --help`, `contextos --version`, and
  `contextos validate`.
- v0.3 Context Readiness exposes `contextos assess` through the CLI without
  duplicating ValidatorEngine logic.
- v0.4 adds guided bootstrap surfaces.
- v0.5 adds construction surfaces.
- v0.6+ adds activation, health, mission, and reasoning surfaces only when
  their product release requires them.

The CLI must remain a wrapper around runtime components, not a place where
component logic is reimplemented.

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

Completed v0.3 validate slice:

- `contextos --help`.
- `contextos --version`.
- `contextos validate` wrapping ValidatorEngine directly.
- Validator-compatible flags: `--root`, `--mode`, `--format`, `--rules`,
  `--json-out`.
- Exit code preservation for ValidatorEngine.

Upcoming release slices:

- Context Readiness assessment surface.
- `contextos assess --root <path> --format text|human|json --json-out <path>`
  per the
  [`Context Readiness Assessment Contract`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md).
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
- IDE/Copilot surface activation before the v0.6 Context Activation slice.
- TUI / interactive shells.
- Web UI for Context Health Report.
- Runtime component logic inside the CLI.

---

## Expected Outcomes

- v0.3: validation is invokable via the CLI and preserves ValidatorEngine
  behavior.
- v0.3: assessment is invokable via the CLI and produces
  `contextos.readiness.report/1` without writing to the repository.
- v0.4/v0.5: Bootstrap and construction steps from
  [`4.4`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md) become
  invokable via the CLI as their release slices ship.
- Output is consistently structured: `result` or `error` under `--format
  json`.
- The CLI is the single integration point for other Runtime components.

---

## Dependencies

- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.5_Runtime_Event_Model.md)
- [`../../docs/4.x_adoption/4.5_COS_Runtime_Installation.md`](../../docs/4.x_adoption/4.5_COS_Runtime_Installation.md)
- Validator Engine (EPIC-007) for `validate` / `health`.

---

## Success Criteria

- Completed v0.3 validate slice is tested and JSON-pure.
- `contextos assess --format json` is JSON-pure and conforms to
  `contextos.readiness.report/1`.
- Low readiness returns exit code 0 when the report is generated; fatal input
  failures return exit code 8 and misconfiguration returns exit code 9.
- Release-specific commands are implemented with their declared exit codes
  when their slice becomes active.
- `contextos validate` exit codes match the Validator Engine's outputs.
- `--format json` returns schema-valid output for every command.
- Help text for every command and subcommand is present and consistent.
- A scripted end-to-end bootstrap completes against
  `examples/sample_solo_founder` using only the CLI.

---

## Definition of Ready (DoR)

- CLI Contract is current for the active release slice.
- Context Readiness Assessment Contract is current for the active release
  slice.
- Exit code map matches Validator Contract.
- Authority levels per command are reflected in confirmation prompts.

---

## Definition of Done (DoD)

- Active release commands shipped, tested, and documented, including
  `contextos assess` for v0.3.
- JSON output schema validated in CI.
- `cli.run` event emitted on every invocation with `authority` populated.
- Installation walkthrough (`4.5`) updated to reference CLI behavior
  faithfully.

---

## Related Artifacts

- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.2_CLI_Contract.md)
- [`../../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md`](../../docs/1.x_architecture/1.5_runtime_contracts/1.5.6_Context_Readiness_Assessment_Contract.md)
- [`../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md`](../../docs/4.x_adoption/4.4_COS_Runtime_Bootstrap.md)
- [`../../docs/4.x_adoption/4.5_COS_Runtime_Installation.md`](../../docs/4.x_adoption/4.5_COS_Runtime_Installation.md)
- [`../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md`](../../docs/5.x_strategy/5.4_COS_Product_Roadmap.md)
