# E.4 Mission V05-BUILDER-DRAFT-SURFACE-DECISION-001 - Draft Workspace Decision
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Resolve the draft surface decision required before any write-capable Builder
behavior can create draft context artifacts.

This mission canonizes the Draft Workspace as the universal abstraction for
generated or co-created organizational context that is not yet canonical
organizational truth.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V05-BUILDER-DRAFT-SURFACE-DECISION-001
  title: Draft Workspace Decision
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

Adopt **Draft Workspace** as the canonical abstraction for non-canonical
generated or co-created context.

For the current local filesystem runtime, map the Draft Workspace to:

```text
.contextos/drafts/
```

`.contextos/drafts/` is a physical implementation detail. The concept must not
be reduced to Git branches, worktrees, or filesystem directories.

---

## Alternatives Evaluated

| Alternative | Decision | Reason |
|---|---|---|
| Write drafts directly into `SSOT/` | Rejected as default | `SSOT/` represents canonical/verified context and should not be polluted by unapproved generated drafts |
| Git branch | Implementation mechanism only | Useful for software repositories but too technology-specific as a universal organizational model |
| Git worktree | Implementation mechanism only | Strong isolation for local runtime, but not meaningful for non-code organizational systems |
| Temporary scratch directory | Insufficient alone | Useful mechanically, but lacks lifecycle, authority, retention, and promotion semantics |
| `.contextos/drafts/` | Accepted physical mapping for local runtime | Provides local isolation while preserving conceptual separation from canonical SSOT |
| Governed Draft Workspace | Accepted canonical model | Generalizes across organizational domains and storage systems |

---

## Canonical Draft Workspace Model

A Draft Workspace is a governed, non-canonical workspace where generated or
co-created organizational context can exist before review, approval, and
canonical verification.

It may contain:

- draft context artifacts,
- draft manifests and metadata,
- provenance chains,
- source evidence references,
- unknowns and missing evidence,
- contradiction records,
- human review notes,
- supersession and rejection records,
- validation evidence,
- rollback metadata.

It may never contain:

- canonical SSOT context,
- immutable decision records,
- authority ledgers,
- hidden generated truth,
- untracked overwrites of existing canonical artifacts,
- artifacts represented as approved or canonical merely because they were
  written.

---

## Lifecycle Model

Draft Workspace artifact states:

```text
draft -> review_requested -> reviewed -> rejected | superseded | promoted | expired
```

The workspace must not use `approved` or `canonical/verified` as local states.
Approval and canonical verification are governance outcomes outside the Draft
Workspace.

---

## SSOT Boundary

`SSOT/` remains the canonical/verified organizational context surface.

Draft Workspace artifacts may reference SSOT artifacts as evidence. They must
not overwrite SSOT artifacts and must not become SSOT artifacts by being moved
or renamed.

---

## Review and Promotion Boundary

Draft creation requires L2 draft authority.

Promotion requires the Governance Protocol:

```text
Propose -> Stage -> Validate -> Review -> Decide -> Apply -> Record -> Emit
```

Promotion derives canonical context from a reviewed and approved draft. The
canonical artifact may be copied, materialized, synthesized, or otherwise
derived according to the target runtime, but the promotion action is separate
from draft creation.

---

## Provenance and Isolation Guarantees

Every Draft Workspace artifact must bind to:

- Mission Packet id,
- Builder Draft Plan identity/hash,
- draft item id,
- Discovery source id and fingerprint,
- Construction candidate id,
- human Draft Authorization,
- target canonical artifact class,
- unknowns and missing evidence,
- contradictions if any.

The workspace must preserve isolation:

- drafts are non-canonical,
- drafts cannot overwrite canonical artifacts,
- drafts cannot suppress conflicting evidence,
- drafts cannot hide uncertainty,
- drafts cannot be promoted silently.

---

## Drift Handling

Promotion must pause when any of these drift after draft creation:

- source evidence,
- Discovery fingerprint,
- Builder Draft Plan identity,
- draft artifact content,
- target canonical path,
- authority,
- Validator gate result.

Stale drafts may be superseded, rejected, or revalidated, but they must not be
silently promoted.

---

## Domain Implications

Draft Workspace is universal across organizational domains.

The current local runtime maps it to `.contextos/drafts/`; future runtimes may
map it to:

- document-management draft folders,
- CMS draft collections,
- CRM/RevOps sandboxes,
- policy review workspaces,
- finance planning workspaces,
- legal redline workspaces,
- people-operations policy draft areas,
- data catalog proposal spaces,
- other domain-native draft surfaces.

The abstraction remains stable: isolated, provenance-bound, authority-bound,
reviewable, rejectable, supersedable, and non-canonical until governance
promotion.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| GENESIS inspected | Context mutation and memory promotion require governance |
| Context Construction Loops inspected | Hypothesis/draft context must not become verified truth without validation |
| Builder Draft Authority Contract updated | Draft Workspace canonized in `1.5.8` |
| Roadmap/epic aligned | v0.5 and EPIC-006 reference Draft Workspace |
| Evolution Inbox updated | Future implementation and policy work captured |
| Regression tests | Existing Builder, Discovery, Construction, Readiness, Bootstrap, Validator, and CLI tests passed |
| Gate validation | `./contextos validate --root . --mode gate --format json` returned exit code 0 |
| Whitespace validation | `git diff --check` passed |

---

## Learning

- The product abstraction is not "branch" or "worktree"; it is a governed
  Draft Workspace.
- `.contextos/drafts/` is appropriate for the local runtime because it keeps
  generated drafts out of canonical SSOT while remaining inspectable.
- Promotion should derive canonical context from drafts through governance,
  not move drafts into canonical truth.
- The same model fits legal redlines, finance plans, product drafts, strategy
  proposals, and technical MOM drafts.

---

## Current v0.5 Impact

v0.5 is closer to write-capable Builder behavior, but the Builder still may
not write its first draft until a future mission implements a draft
preflight/authorization object and receives explicit write authority.

---

## Change Log

- 2026-08-11 - v0.1.0 - Created and closed the Draft Workspace decision.
