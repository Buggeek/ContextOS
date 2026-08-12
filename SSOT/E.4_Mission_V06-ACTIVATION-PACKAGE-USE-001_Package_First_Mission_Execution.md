# E.4 Mission V06-ACTIVATION-PACKAGE-USE-001 - Package-First Mission Execution
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Prove that a real self-hosted Context OS Mission can be understood, executed,
validated, learned from, and closed from an activated working-context package
instead of a manually reconstructed prompt.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V06-ACTIVATION-PACKAGE-USE-001
  title: Package-First Mission Execution
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

## Activation Package Used

Initial package:

```text
activation.package.f2bc9b9afcf126c0
```

Identity hash:

```text
f2bc9b9afcf126c0117a91e3a2428fc2b6a75414857257cff57610b4cdfbb7a2
```

Command:

```bash
./contextos activate \
  --root . \
  --goal "Use a Context Activation Package as the authoritative working context for a real self-hosted v0.6 mission" \
  --consumer codex \
  --mission-id V06-ACTIVATION-PACKAGE-USE-001 \
  --format json
```

Package check:

```text
contextos.activation.package_check/1 valid=true
```

Activation was allowed because Validator gate had no errors or fatals.

---

## Automatically Selected Context

The package selected 12 artifacts:

- `SSOT/P.2_Product_Roadmap.md`,
- `SSOT/A.1_System_Map.md`,
- `SSOT/P.1_Product_Map.md`,
- `README.md`,
- `SSOT/S.1_Vision.md`,
- `docs/0.x_foundations/0.8_COS_GENESIS.md`,
- `SSOT/G.1_Definition_of_Ready.md`,
- `SSOT/G.2_Definition_of_Done.md`,
- `SSOT/E.4_Mission_V06-ACTIVATION-PACKAGE-CLI-001_Activation_Package_CLI.md`,
- `SSOT/E.4_Mission_V06-CONTEXT-ACTIVATION-PLAN-001_Context_Activation_Package.md`,
- `docs/5.x_strategy/5.4_COS_Product_Roadmap.md`,
- `docs/1.x_architecture/1.5_runtime_contracts/1.5.9_Context_Activation_Package_Contract.md`.

The package excluded 50 lower-ranked relevant artifacts. This avoided
reloading all v0.3-v0.5 mission history, builder internals, bootstrap internals,
and unrelated strategy material.

---

## Additional Context Required

Additional exact repository context was required only for files that the package
selected and this Mission needed to edit:

- `docs/1.x_architecture/1.5_runtime_contracts/1.5.9_Context_Activation_Package_Contract.md`,
- `tools/activation/README.md`,
- `SSOT/P.2_Product_Roadmap.md`,
- `SSOT/E.5_Evolution_Inbox.md`.

Reason: the package excerpts identified the correct canonical sources and
constraints, but exact file content was required for precise patches.

No unselected runtime code, Builder internals, Bootstrap internals, Knowledge
Engine, Graph, agent, connector, or IDE adapter context was needed.

---

## Capability Delivered

Established the package-first Mission use protocol:

1. generate/resolve the Mission-bound package,
2. verify package validity,
3. use selected sources as authoritative working context,
4. limit additional context to selected sources or objective gaps,
5. record package id/hash, selected context, exclusions, gaps, and evidence,
6. treat source changes as invalidating the package,
7. generate a fresh package when continuing after source changes.

This capability is documentation/contract-level because the runtime package and
CLI already existed. No new runtime behavior was required.

---

## Package Validity and Invalidation Evidence

Initial package check passed before edits.

This Mission then modified selected canonical sources. That invalidated the
initial package by changing included source hashes.

The correct behavior is to generate and check a fresh package before using the
updated context as authoritative working context.

---

## Manual Prompt Reduction

Previous self-hosted Missions required prompts that manually restated:

- release name,
- mission id,
- roadmap status,
- canonical sources,
- governance constraints,
- runtime boundaries,
- evidence requirements,
- exclusions,
- validation requirements.

With package-first execution, a future Mission can begin with a compact
instruction shaped like:

```text
Use activation package <package-id> as authoritative working context for
<mission-id>; check package validity before acting.
```

This reduces manual source reconstruction while preserving correctness because
the package carries source identity, hashes, constraints, gaps, exclusions,
provenance, and validator evidence.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Initial package generated | `contextos.activation.package/1` |
| Initial package check | valid |
| Selected sources inspected | 12 |
| Excluded artifacts recorded | 50 |
| Additional context needed | selected files only |
| Contract updated | package-first Mission use protocol added |
| Activation README updated | package-first Mission use sequence added |
| Initial package invalidation | expected after selected source edits |
| Fresh package check | required after this commit |
| Regression tests | Activation, CLI, Validator, and gate checks passed |
| Read-only activation boundary | no runtime mutation or external activation performed |

---

## Learning

- An Activation Package can materially replace manual source reconstruction for
  mission orientation.
- The package is sufficient for deciding mission scope and boundaries.
- Exact file reads are still required for safe edits, but those reads can be
  constrained to selected package sources.
- Source edits during execution invalidate the package; package-first execution
  must include a fresh package check before any follow-on mission uses the
  changed context.

---

## Evolution Impact

This Mission keeps v0.6 focused on read-only activation. It does not introduce
agents, adapters, Graph runtime, Knowledge Engine expansion, or prompt
generation.

---

## Next Mission Recommended

```text
V06-ACTIVATION-HANDOFF-FORMAT-001
```

Define the smallest package-backed handoff format for humans, Codex, Claude
Code, and IDE assistants so future Missions can start from a package reference
plus a compact instruction.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the package-first Mission execution
  proof.
