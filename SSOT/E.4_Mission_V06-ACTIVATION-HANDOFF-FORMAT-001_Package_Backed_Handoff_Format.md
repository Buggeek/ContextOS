# E.4 Mission V06-ACTIVATION-HANDOFF-FORMAT-001 - Package-Backed Handoff Format
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Define and implement the smallest universal package-backed handoff format that
allows a human, Codex, Claude Code, IDE assistant, or future organizational
consumer to begin work from a valid Context Activation Package without manually
reconstructing context.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V06-ACTIVATION-HANDOFF-FORMAT-001
  title: Package-Backed Handoff Format
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

## Mission Decision

The approved representation is a paired human + machine format:

- machine schema: `contextos.activation.handoff/1`,
- human representation: compact Markdown rendered from the same machine report.

This avoids a Codex-specific prompt format while still giving humans and agents
a usable operating brief. The handoff points to canonical sources and preserves
hashes; it does not copy full canonical content or become a second SSOT.

---

## Capability Delivered

Implemented package-backed handoff generation in:

```text
tools/activation/activation_engine/package_engine.py
```

The handoff is exposed through the existing activation CLI:

```bash
./contextos activate \
  --root . \
  --check-package /tmp/contextos-activation-package.json \
  --handoff
```

Fresh package plus handoff is also supported:

```bash
./contextos activate \
  --root . \
  --goal "Plan the next mission" \
  --consumer codex \
  --mission-id V06-ACTIVATION-HANDOFF-FORMAT-001 \
  --handoff
```

No new command, adapter, agent runtime, Knowledge Engine behavior, Graph
runtime, mutation, or background synchronization was introduced.

---

## Handoff Contract

The handoff preserves:

- package id and identity hash,
- package check evidence,
- consumer,
- goal and Mission id,
- selected canonical source paths and hashes,
- selected source roles, authority tiers, lifecycle states, titles, and owners,
- bounded exclusions,
- known gaps,
- allowed and prohibited permissions,
- freshness and invalidation state,
- provenance and source hash lineage,
- evidence and exit conditions for Mission closure.

The handoff explicitly records:

- `not_ssot: true`,
- `duplicates_full_canonical_content: false`,
- `writes_performed: false`,
- `canonical_context_mutated: false`,
- `automatic_context_mutation: false`.

---

## Dogfood Result

A fresh package and handoff were generated against the Context OS repository
after implementation.

Package check result:

```text
handoff_ready=true
package_valid_now=true
```

The handoff selected 12 canonical sources and excluded lower-ranked sources.
The only gap was:

```text
activation.gap.validator_warnings_present
```

This is non-blocking because validator warnings do not prevent activation.

The handoff is materially smaller than the package because it preserves source
identity, hashes, and instructions without carrying selected content excerpts.

---

## Automatically Selected Context

The dogfood handoff selected the active roadmap, core SSOT anchors, GENESIS,
Definitions of Ready/Done, prior v0.6 Mission evidence, and this Mission
evidence. Exact source identities are preserved in the generated handoff report
rather than duplicated here, so this Mission artifact does not create a
self-invalidating package/hash loop.

Representative selected context included:

- `SSOT/P.2_Product_Roadmap.md`,
- `SSOT/A.1_System_Map.md`,
- `SSOT/P.1_Product_Map.md`,
- `SSOT/S.1_Vision.md`,
- `README.md`,
- `docs/0.x_foundations/0.8_COS_GENESIS.md`,
- `SSOT/G.1_Definition_of_Ready.md`,
- `SSOT/G.2_Definition_of_Done.md`,
- `SSOT/E.4_Mission_V06-ACTIVATION-HANDOFF-FORMAT-001_Package_Backed_Handoff_Format.md`,
- `SSOT/E.4_Mission_V06-ACTIVATION-PACKAGE-USE-001_Package_First_Mission_Execution.md`,
- `SSOT/E.4_Mission_V06-CONTEXT-ACTIVATION-PLAN-001_Context_Activation_Package.md`,
- `SSOT/E.4_Mission_V06-ACTIVATION-PACKAGE-CLI-001_Activation_Package_CLI.md`.

Additional implementation context was required for:

- `tools/activation/activation_engine/package_engine.py`,
- `tools/activation/activation_engine/report_builder.py`,
- `tools/activation/test_activation_package.py`,
- `tools/cli/contextos_cli.py`,
- `tools/cli/test_contextos_cli.py`,
- `tools/activation/README.md`,
- `SSOT/E.5_Evolution_Inbox.md`.

Reason: the package selected the canonical product and contract context, but
runtime/test files were needed for precise implementation and verification.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Handoff schema implemented | `contextos.activation.handoff/1` |
| Handoff derived from package check | yes |
| Human rendering implemented | yes |
| CLI `--handoff` surface added | yes |
| JSON output purity | parseable by `python3 -m json.tool` |
| Package drift invalidates handoff | tested |
| Handoff omits full source excerpts | tested |
| Existing activation package behavior | unchanged by regression tests |
| Read-only activation boundary | no target repository writes |
| Validator gate | no errors or fatals on Context OS repo |

---

## Prompt / Handoff Compression

This Mission still began from a detailed human prompt because the handoff format
did not exist yet.

After implementation, the handoff can carry package identity, selected sources,
constraints, gaps, exclusions, evidence obligations, and invalidation state in
one compact artifact. A future Mission can begin with a shorter instruction
such as:

```text
Use handoff <handoff-id> derived from package <package-id>; revalidate before
acting and execute the bound Mission.
```

Exact source reads remain necessary for file edits, but handoff-first execution
avoids re-stating the whole roadmap, authority, and context-selection surface in
the prompt.

---

## Learning

- A package-backed handoff is the correct next primitive after package-first
  Mission use.
- The handoff should be universal and consumer-agnostic; Codex, Claude Code,
  IDE assistants, and humans can render the same machine report differently.
- The handoff should not include full canonical excerpts by default.
- Source selection is good enough for product/contract orientation, but
  implementation missions still need explicit runtime/test file reads.

---

## Evolution Impact

This Mission advances v0.6 from package generation/checking into practical
working-context transfer. It does not alter the v0.6 product goal and does not
start adapters, agents, Graph runtime, Knowledge Engine expansion, or automatic
context mutation.

---

## Next Mission Recommended

```text
V06-ACTIVATION-HANDOFF-USE-001
```

Use a package-backed handoff as the authoritative starting context for the next
real self-hosted Mission and measure whether the Mission can begin from a
handoff reference plus a materially smaller instruction.
