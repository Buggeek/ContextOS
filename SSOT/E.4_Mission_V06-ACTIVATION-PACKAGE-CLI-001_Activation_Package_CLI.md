# E.4 Mission V06-ACTIVATION-PACKAGE-CLI-001 - Activation Package CLI
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Expose the read-only Context Activation Package through the Runtime CLI so a
human or coding agent can request mission-bound working context without
manually reconstructing repository context.

The CLI is an enabling surface. The product outcome is governed working
context for a real consumer.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V06-ACTIVATION-PACKAGE-CLI-001
  title: Activation Package CLI
  initiating_lifecycle: release
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed:done
  created_at: 2026-08-11
```

---

## Release

v0.6 - Context Activation

---

## Capability

Added:

```text
contextos activate
```

Supported generation flags:

- `--root`,
- `--goal`,
- `--consumer`,
- `--mission-id`,
- `--max-artifacts`,
- `--format human|text|json`,
- `--json-out`.

Supported package-check flags:

- `--check-package`,
- `--format human|text|json`,
- `--json-out`.

Machine schemas:

```text
contextos.activation.package/1
contextos.activation.package_check/1
```

---

## Consumer Model

The CLI requires the consumer to be explicit.

Examples:

- `human`,
- `codex`,
- `claude_code`,
- `ide_assistant`,
- `cli_tool`.

Consumer values are not authority grants. The package grants only:

```text
read_canonical_context
use_working_context
```

and prohibits:

```text
mutate_canonical_context
promote_context
delegate_authority
```

---

## Selection Model

The CLI does not ask the user to manually list canonical files.

It delegates bounded context selection to `ContextActivationPackageEngine`,
which:

- anchors default canonical sources,
- ranks additional sources by goal, mission id, and consumer tokens,
- includes source paths, hashes, authority tiers, lifecycle states, excerpts,
  and provenance,
- records excluded relevant sources,
- records gaps and Validator gate status.

---

## Invalidation Behavior

`--check-package` verifies:

- package identity hash,
- every included source hash,
- current Validator gate state.

It emits `contextos.activation.package_check/1`.

Exit code:

- `0` when valid,
- `7` when invalidated,
- `9` for invalid input or configuration.

---

## Dogfood Mission

Dogfood target:

```text
V06-ACTIVATION-PACKAGE-USE-001
```

Goal:

```text
Use a Context Activation Package as the authoritative working context for the
next self-hosted v0.6 mission.
```

Dogfood command:

```bash
./contextos activate \
  --root . \
  --goal "Use a Context Activation Package as the authoritative working context for the next self-hosted v0.6 mission" \
  --consumer codex \
  --mission-id V06-ACTIVATION-PACKAGE-USE-001 \
  --format json
```

Dogfood result:

- package id: `activation.package.5937467b1de5a87c`,
- activation allowed: `true`,
- included artifacts: `12`,
- excluded artifacts: `49`,
- context gaps: `activation.gap.validator_warnings_present`,
- package check valid: `true`.

Automatically selected context included:

- `SSOT/P.2_Product_Roadmap.md`,
- `README.md`,
- `SSOT/A.1_System_Map.md`,
- `SSOT/P.1_Product_Map.md`,
- `docs/0.x_foundations/0.8_COS_GENESIS.md`,
- `SSOT/S.1_Vision.md`,
- `SSOT/G.1_Definition_of_Ready.md`,
- `SSOT/G.2_Definition_of_Done.md`,
- `SSOT/E.4_Mission_V06-CONTEXT-ACTIVATION-PLAN-001_Context_Activation_Package.md`,
- `docs/5.x_strategy/5.4_COS_Product_Roadmap.md`,
- `docs/1.x_architecture/1.5_runtime_contracts/1.5.9_Context_Activation_Package_Contract.md`,
- `SSOT/E.4_Mission_SELFHOST-001_Governed_Execution_Loop.md`.

---

## Product Experiment Result

The package contains enough context to understand the next mission's release
anchor, product journey, authority model, activation contract, prior v0.6
mission, and self-hosting loop.

Irrelevant context was avoided by excluding 49 lower-ranked relevant artifacts.

A future self-hosted mission can start from:

```text
Use activation package <package-id> as authoritative working context for
<mission-id>; check package validity before acting.
```

instead of repeating the full source-document list and release history inside a
large prompt.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| CLI implementation | `contextos activate` added |
| Engine check mode | `contextos.activation.package_check/1` added |
| Human package report | passed |
| JSON package output | pure JSON and parseable |
| JSON package check | pure JSON and parseable |
| `--json-out` | writes machine package |
| Drift invalidation test | source hash drift returns exit code 7 |
| CLI tests | `python3 tools/cli/test_contextos_cli.py` passed |
| Activation tests | `python3 tools/activation/test_activation_package.py` passed |
| Regression tests | Builder release verification, Discovery, Construction, Validator, and CLI tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Whitespace validation | `git diff --check` passed |

---

## Learning

- The CLI is valuable only because it lets a consumer request a governed
  package without naming files manually.
- Package validity should be checked before a package is used as mission
  context.
- The next improvement should test execution from a package, not add adapters
  prematurely.

---

## Next Mission Recommended

```text
V06-ACTIVATION-PACKAGE-USE-001
```

Use the CLI-generated package as the authoritative working-context input for a
real self-hosted mission and measure how much manual prompting can be reduced.

---

## Change Log

- 2026-08-11 - v0.1.0 - Added and dogfooded the Activation Package CLI.
