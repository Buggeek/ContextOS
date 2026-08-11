# E.4 Mission V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001 - Draft Workspace Runtime
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Implement the minimum read-only Draft Workspace runtime required before any
Builder draft write is possible.

This mission turns the canonical Draft Workspace decision into executable
runtime checks for the current local filesystem runtime without creating
directories, drafts, SSOT artifacts, or canonical organizational truth.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001
  title: Draft Workspace Runtime
  initiating_lifecycle: release
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed:done
  created_at: 2026-08-11
```

---

## Release

v0.5 - Context Construction

---

## Decision

Add `DraftWorkspaceRuntime` as the read-only runtime preflight for future
Builder draft creation.

Machine report schema:

```text
contextos.builder.draft_workspace_preflight/1
```

The report determines:

- the local Draft Workspace mapping,
- the exact future draft target path per draft item,
- whether the target remains inside the governed Draft Workspace,
- whether path traversal or escape is possible,
- whether a target already exists,
- whether no-overwrite guarantees hold,
- whether the Builder Draft Plan identity remains bound,
- whether Discovery or Construction state drifted,
- whether the Validator gate remains passing,
- whether the item is eligible for future L2 draft creation authority.

---

## Runtime Model

For the current local filesystem runtime, the Draft Workspace maps to:

```text
.contextos/drafts/
```

Future draft targets are resolved as:

```text
.contextos/drafts/<mission_id>/artifacts/<target_context_artifact>
```

This preserves the canonical target artifact lineage while ensuring the draft
surface remains non-canonical.

The runtime does not create `.contextos/drafts/`. Existence is observed only.

---

## Guarantees

`DraftWorkspaceRuntime` is read-only and must not:

- create directories,
- create draft artifacts,
- write or mutate SSOT,
- mutate canonical context,
- retarget draft paths silently,
- overwrite existing draft targets,
- promote drafts,
- escalate authority,
- use Knowledge Engine, Graph runtime, agents, or external connectors.

---

## Identity and Drift

The runtime computes a stable Builder Draft Plan hash that excludes
`generated_at` and binds:

- source Discovery Bundle identity and fingerprint,
- Construction Plan summary,
- draft items,
- lifecycle boundaries,
- truth boundaries,
- read-only constraints.

The runtime re-runs Builder Draft Planning against current repository state and
marks the preflight ineligible if the supplied plan no longer matches the fresh
plan.

---

## Eligibility Model

A target is eligible only when:

1. the draft item status is `draftable`,
2. the target resolves inside `.contextos/drafts/`,
3. the target cannot traverse outside the workspace,
4. the target is not a canonical/prohibited surface,
5. the target does not already exist,
6. no-overwrite is satisfied,
7. support is `moderate` or `strong`,
8. evidence references are present,
9. contradictions are empty.

Overall future draft creation eligibility also requires:

- workspace checks pass,
- drift checks pass,
- Validator gate has no `error` or `fatal`,
- every target is eligible.

Eligibility does not authorize draft creation. Explicit L2 human draft
authority remains required.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Builder Draft Authority Contract inspected | Draft Workspace runtime follows `1.5.8` |
| Draft Workspace decision inspected | `.contextos/drafts/` used as local mapping only |
| `DraftWorkspaceRuntime` implemented | `contextos.builder.draft_workspace_preflight/1` created |
| Read-only tests | Runtime creates no directories or draft artifacts |
| Path isolation tests | Traversal and workspace escape are blocked |
| No-overwrite tests | Existing draft target blocks eligibility |
| Drift tests | Stale Builder Draft Plan invalidates eligibility |
| Dogfood test | Context OS repo produces preflight with Validator gate passing |
| Regression tests | Builder, Discovery, Construction, Readiness, Bootstrap, Validator, and CLI tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Whitespace validation | `git diff --check` passed |

---

## Learning

- Draft Workspace enforcement belongs between Builder Draft Plan and any future
  write-capable Builder operation.
- The runtime should preserve canonical target lineage inside the draft path
  rather than inventing a new draft taxonomy.
- A preflight can prove path safety, no-overwrite, drift, and Validator gates
  without implying authority or mutating the repository.
- The first write-capable Builder mission should consume this preflight rather
  than accepting a raw Builder Draft Plan directly.

---

## Current v0.5 Impact

v0.5 now has an executable read-only boundary for future draft writes.

The Builder still may not write a real draft until explicit human authority is
granted for a write-capable mission bound to an exact Draft Workspace preflight,
draft item set, mission id, target repository, and no-overwrite result.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the Draft Workspace runtime mission.
