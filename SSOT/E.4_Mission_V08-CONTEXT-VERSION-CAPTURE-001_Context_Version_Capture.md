# E.4 Mission V08-CONTEXT-VERSION-CAPTURE-001 - Context Version Capture
## Version: 0.1.0
Last Updated: 2026-08-23
Owner: Context OS Maintainers
Status: closed

---

## Purpose

Establish the smallest governed Context Version primitive that can identify
the exact organizational context in force at a meaningful event without
copying canonical content, treating Git as the universal model, or deriving
authority from history.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V08-CONTEXT-VERSION-CAPTURE-001
  title: Immutable Context Version Capture
  initiating_lifecycle: release
  release: v0.8-organizational-memory
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed
  authority: publish_policy_aware_retrieval_then_implement_and_commit_context_version_without_push
  depends_on:
    - V08-MEMORY-RETRIEVAL-POLICY-INTEGRATION-001
    - V08-ORGANIZATIONAL-MEMORY-PLAN-001
    - THEORY-AI-NATIVE-ORGANIZATION-V01
  created_at: 2026-08-23
```

Authority included publication of accepted Policy-Aware Memory Retrieval
commit `3be8aab1474a881634979949d9fef7fbdd25c768`, refreshed Activation context,
read-only Context Version planning/capture/checks, controlled dogfood,
canonical alignment, evidence capture, Mission closure, and a local commit.

Authority excluded publication of the new commit, release tagging, automatic
capture, a version registry, semantic historical comparison, retention
transitions, Graph/RAG/vector/Knowledge work, agents, and v0.9 capability.

---

## Governing Activation Context

After Retrieval publication, the Mission generated and validated:

```text
activation.package.7c2b3fa6c2918506
package hash: 7c2b3fa6c291850654c071e42d13dadc3d4fb19b71886d41d04b735448d2b921
activation.handoff.b4aaec170a324c80
handoff hash: b4aaec170a324c8037bdaf1f42c1e6090597e6eb13a7fe6506d0abb635f83556
```

Both were valid before implementation. The Package selected twelve canonical
sources, excluded 71, and exposed one gap. The Context Versioning foundation,
Theory, Mission/Authority/Governance contracts, Memory contracts, Runtime
implementation, tests, historical Missions, and release tags were bounded
Execution Context because exact design, implementation, or evidence required
them.

Expected canonical edits later invalidated both artifacts with exit `7`,
proving source-drift detection rather than allowing stale working context.

---

## Decision

Adopt `contextos.context.version/1` as an immutable, content-free identity and
provenance record. It is created from an exact valid
`contextos.context.version_capture_plan/1`; capture never regenerates the
approved plan.

Accepted explicit capture events are Mission start, consequential Decision,
accepted Approval, canonical promotion, release cut, material policy or
governance change, and explicit human checkpoint. Routine edits, commands,
reads, reports, and timed background capture are rejected.

The current filesystem adapter uses stable logical source identities, opaque
locators, SHA-256 fingerprints, declared lifecycle/authority metadata, and
optional exact Git evidence. Git proves an implementation snapshot only. It
does not define the universal Context Version or organizational authority.

---

## Capability Delivered

`ContextVersionEngine` provides four read-only operations:

- `plan(...)` binds event, scope, time, Mission/Goal, exact source manifest,
  authority/policy refs, optional Activation evidence, optional parent, Git
  implementation evidence, Validator gate, gaps, and limitations.
- `check_plan(...)` recomputes those explicit inputs and blocks capture on
  source, package, Handoff, scope, event, parent, policy, authority, or time
  drift.
- `capture(...)` consumes the exact valid plan and produces deterministic,
  idempotent `contextos.context.version/1` without persistence or mutation.
- `check_version(...)` independently evaluates immutable identity, historical
  source verification, and current applicability.

Human and machine reports expose state, reason, source versions, policy and
authority references, source availability, lineage, truth-axis evidence, and
continuity gaps without embedding canonical content.

---

## Self-Hosting Evidence

An exact controlled capture against published commit `3be8aab` produced:

| Evidence | Result |
|---|---|
| Capture plan | `context.version_capture_plan.eb6b0a8f733c94f6` |
| Plan hash | `eb6b0a8f733c94f6ea8920210033ab6b557439301ce26068579a87c0af69e846` |
| Context Version | `context.version.d0552c6ba5ccbf11` |
| Version hash | `d0552c6ba5ccbf11d656286267093567c1572252fc6c519e85c34ad00c6340c8` |
| Governed source references | 22 |
| Embedded content | false |
| Plan ready / check valid | true / true |
| Historical verification | verified |
| Current applicability at capture | exact current match |
| Runtime writes | false |

Re-running unchanged inputs reproduced the exact plan and version identities.
Changing a current source invalidated the plan. After capture, the same change
preserved immutable identity and historical verification through the exact old
Git blob while changing current applicability to `superseded_or_drifted`.
Removing an unrecoverable source produced a continuity gap; no current content
was substituted.

---

## Retrospective Assessment

| Event | Finding |
|---|---|
| v0.7 release cut | Partially reconstructable: exact release commit and Activation identities exist, but no full governed source manifest |
| v0.6 release cut | Partially reconstructable under the same boundary |
| v0.5 canonical promotion | Isolated fixture evidence exists; no canonical Context OS promotion state should be invented |
| AI-native Organization Theory decision | Exact implementation commit and Activation identities exist, but no Context Version manifest |
| v0.3 and v0.4 releases | Not reconstructed; required governed-context evidence is insufficient |

Explicit capture is therefore stronger than retrospective reconstruction. Git
and narrative evidence remain useful provenance, but cannot silently become a
complete historical Context Version.

---

## Theory Claims Tested

| Claim | Status | Evidence |
|---|---|---|
| Memory can bind Missions and Decisions to exact historical context without duplicating content | supported for the capture primitive | content-free 22-source manifest and Mission/event bindings |
| Context Version is implementation-independent even when Git supplies evidence | supported by schema; partially tested beyond filesystem | universal source identity/fingerprint model plus optional Git adapter evidence |
| Explicit capture is stronger than retrospective reconstruction | supported | exact current capture versus partial historical event evidence |
| Superseded context remains historically valid without current authority | supported | drift test preserved identity/verification and changed applicability only |
| Activation and Context Version answer complementary questions | supported | Package/Handoff bindings remain separate from governed source-state identity |
| Context Version supplies necessary evidence for future reasoning | partially supported | exact temporal/provenance inputs exist; semantic comparison remains unimplemented |

---

## Validation Evidence

| Evidence | Result |
|---|---|
| Focused Context Version tests | 12 passed |
| Full regressions | 296 tests passed across 32 test programs |
| Validator gate | exit `0`; zero errors and fatals |
| Dogfood JSON reports | plan, plan check, version, and version check all parseable |
| Drift evidence | stale Package/Handoff exit `7`; captured version remains historically valid |
| Whitespace | `git diff --check` passed |
| Canonical content copy/mutation | none |
| Automatic persistence/hooks | none |
| New implementation push/tag | not performed |

---

## Evolution Inbox

`INBOX-133` through `INBOX-139` preserve retrospective gaps, explicit trigger
discipline, future persistence and adapters, independent retention, and the
next Memory integration dependency without expanding this Mission.

---

## Learning

Historical continuity needs two independent answers: whether an immutable
record is authentic, and whether its referenced sources remain available.
Neither answer determines whether that context applies now.

A source fingerprint plus event/authority/policy bindings is sufficient for a
useful universal primitive. Persistence, automatic hooks, and semantic
comparison are separate product decisions. Starting prospective capture now
is more truthful than backfilling polished versions from incomplete history.

---

## Next Mission Recommended

```text
V08-MEMORY-CONTEXT-VERSION-INTEGRATION-001
```

Goal: make Memory Continuity and policy-aware Retrieval consume preserved
Context Version evidence so a Mission or Decision can expose exact historical
state, availability, and applicability gaps without semantic comparison or
returning authority to old context.

This requires separate human implementation authority. Publication of this
Mission commit also requires separate authority.

---

## Mission Decision

```text
CLOSED_DONE
```

---

## Change Log

- 2026-08-23 - v0.1.0 - Closed with deterministic read-only Context Version
  planning, capture, checks, exact self-hosting evidence, retrospective gap
  assessment, and no canonical mutation.
