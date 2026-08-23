# E.4 Mission V08-MEMORY-RETRIEVAL-POLICY-INTEGRATION-001 - Policy-Aware Memory Retrieval
## Version: 0.1.0
Last Updated: 2026-08-23
Owner: Context OS Maintainers
Status: closed

---

## Purpose

Make Organizational Memory Retrieval consume exact read-only Retention
Resolution before exposing relevant memory to a consumer, while preserving
independent relevance, retrieval, visibility, Activation, applicability,
authority, and canonical-context states.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V08-MEMORY-RETRIEVAL-POLICY-INTEGRATION-001
  title: Policy-Aware Organizational Memory Retrieval
  initiating_lifecycle: release
  release: v0.8-organizational-memory
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed
  authority: publish_retention_resolution_then_implement_policy_aware_retrieval_and_commit_without_push
  depends_on:
    - V08-MEMORY-RETENTION-RESOLUTION-001
    - V08-MEMORY-RETENTION-GOVERNANCE-001
    - V08-MEMORY-RETRIEVAL-SURFACE-001
    - V08-ORGANIZATIONAL-MEMORY-PLAN-001
  created_at: 2026-08-23
```

Authority included publication of accepted Retention Resolution commit
`07f14815af2f16cc42bb54be822bd0378e3ec17c`, refreshed Activation context,
read-only Retrieval integration, controlled policy fixtures, CLI/API changes,
tests, contract alignment, evidence capture, Mission closure, and a local
implementation commit.

Authority excluded publication of the new implementation, policy creation for
the Context OS organization, retention transition, archival, deletion,
forgetting, redaction, legal interpretation, automatic Activation inclusion,
GraphRAG, Context Graph, embeddings, vector storage, broad RAG, Knowledge
expansion, agents, and v0.9 work.

---

## Governing Activation Context

After Retention Resolution publication, the Mission generated and validated:

```text
activation.package.1be82159ed4bba76
package hash: 1be82159ed4bba761279192dc71d52ba480f36ed862b8f5a2d30c0a1f878df40
activation.handoff.418ffa7d973fb704
handoff hash: 418ffa7d973fb7044c8bf08c131c9d8d724806b94ff4c39ded16865cee406799
```

Both checks returned valid before implementation. The Package selected twelve
canonical sources, excluded 72, and preserved one explicit gap. Exact Memory
Retrieval, Retention Resolution, CLI, and test files were bounded Execution
Context because implementation required their current interfaces.

---

## Decision

Integrate `RetentionResolutionEngine` directly into
`MemoryRetrievalEngine`. Relevance may identify a private candidate, but no
candidate-specific result content or exclusion metadata may be emitted until
the exact candidate has an independent `access`, `retrieval`, and `activation`
resolution.

```text
Relevant != Retrievable
Retrievable != Visible
Visible != Activatable
Applicable != Authoritative
Remembered != Canonical
```

Only candidates with normal access, normal Retrieval, and sufficient policy
visibility enter `items`.
`elevated_authority`, `excluded`, `prohibited`, and `unknown` remain excluded.
No applicable policy becomes `unknown`, never allowed. Retrieval records the
missing authority but never grants it.

The existing `contextos memory` surface now accepts exact purpose,
organizational mode, actor roles, authority scope, versioned retention-policy
files, memory metadata, and an explicit evaluation time. Saved-result checks
must receive the same governed policy context and invalidate on material
policy, metadata, source, authority, or temporal drift.

---

## Exposure And Activation Boundaries

- Protected identities, titles, paths, snippets, source hashes, evidence
  references, policy identities, and sensitive metadata are withheld from
  policy evaluations and exclusion explanations.
- Safe reports may retain aggregate outcome counts and visibility-permitted
  authority requirements.
- The embedded Activation Package remains the independent source of current
  Governing Context. Its canonical sources are not Memory Retrieval exposure.
- A `normal` Retrieval outcome does not imply a normal Activation outcome.
- Retrieved memory is never inserted automatically into Governing Context.
- Every report and check remains read-only and performs no policy, memory,
  retention, hold, access, Activation, or canonical mutation.

---

## Controlled Self-Hosting Exercise

Current Context OS has no approved organization-specific retention policy or
complete per-memory policy metadata. The truthful repository result therefore
remained closed:

| Evidence | Result |
|---|---|
| Relevant candidates | 214 |
| Policy outcome | 214 `unknown` |
| Exposed candidates | 0 |
| Implicit allow | none |

A controlled, explicitly non-canonical fixture over representative Context OS
memory then exercised one normal, one elevated-authority, one excluded, one
prohibited, one conflict-driven unknown, and missing-policy unknown candidates.

| Evidence | Result |
|---|---|
| Controlled relevant candidates | 214 |
| Outcomes | 1 normal, 1 elevated, 1 excluded, 1 prohibited, 210 unknown |
| Exposed candidates | 1 normal candidate |
| Protected metadata exposed | false |
| Added to Governing Context | false |
| Writes | false |
| Unchanged saved-result check | valid |
| Policy version drift | invalidated with policy-context and selection failures |

The broad Goal intentionally produced many relevant candidates to prove that
uncovered memory remains unknown rather than inheriting permission from the
few controlled policies.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Retention Resolution publication | exact commit `07f14815af2f16cc42bb54be822bd0378e3ec17c` published to `origin/main` |
| Fresh Activation Package/Handoff | exact identities above; both initially valid |
| Existing Retrieval tests | 8 passed |
| Policy-integration tests | 6 passed: five outcomes, missing policy, role difference, access prohibition, metadata safety, read-only behavior, independent Activation, and drift |
| CLI tests | 51 passed, including policy input and pure JSON behavior |
| Full regressions | 284 tests passed across 31 test programs |
| Dogfood machine output | `/tmp/contextos-v08-policy-retrieval-dogfood.json` parsed successfully |
| Validator gate | exit `0`; zero errors and fatals |
| Runtime mutation | none |
| Canonical Context mutation from Retrieval | none |
| Retention transition or destructive action | none |
| Whitespace | `git diff --check` passed |
| Implementation push/tag | not performed |

---

## Theory Claims Tested

| Claim | Status | Evidence |
|---|---|---|
| Memory relevance and policy eligibility are independent | supported | relevant candidates remained unknown/excluded until exact policy resolution |
| The same memory may be retrievable for one role and elevated for another without the Runtime granting authority | supported | controlled role-difference test |
| Current canonical Context remains authoritative when historical memory is retrieved | supported | embedded Activation remains governing and Retrieval items remain `canonical: false` |
| Retention governance can constrain ordinary memory use without mutating memory | supported for read-only Retrieval | policy outcomes changed exposure while source snapshots remained unchanged |
| Minimum Sufficient Authorized Memory can avoid broad exposure | supported in controlled local retrieval | only the one normal visible candidate crossed the policy boundary |
| Organization-wide Retention policy is operational | not supported | no approved organization-specific policy values or complete metadata exist |
| Policy-aware Retrieval proves memory usefulness | not supported | retrieval and visibility do not establish use or usefulness |

---

## Evolution Inbox

- `INBOX-128` preserves the future source-adapter access boundary.
- `INBOX-129` records absent organization-approved policies and metadata.
- `INBOX-130` defers policy-profile and registry ergonomics.
- `INBOX-131` preserves explicit separation from Activation inclusion.
- `INBOX-132` promotes immutable Context Version capture as the next release
  dependency.

---

## Learning

Policy-aware Retrieval is not a filter applied after presentation. It is the
gate between private relevance and candidate exposure, including exclusions.
Safe absence is an aggregate outcome, not a redacted copy of protected
metadata.

The current local runtime may inspect repository evidence under existing local
read authority before policy presentation. That implementation assumption
cannot generalize to external or partitioned memory stores; future source
adapters must enforce access before protected content is loaded.

Context OS can now retrieve governed prior art, but historical Missions still
do not uniformly bind immutable Context Versions. Without that object, exact
reconstruction of the context under which a decision was made remains
incomplete even when Retrieval policy is correct.

---

## Next Mission Recommended

```text
V08-CONTEXT-VERSION-CAPTURE-001
```

Goal: implement the smallest read-only `contextos.context.version/1` capture
and validity-check capability that binds an immutable canonical artifact set,
source hashes, tier, producer, parent relationship, and truth summary without
creating a second SSOT or mutating canonical Context.

This recommendation requires separate human implementation authority and
publication authority for this Mission commit.

---

## Mission Decision

```text
CLOSED_DONE
```

---

## Change Log

- 2026-08-23 - v0.1.0 - Closed with policy-before-exposure Memory Retrieval,
  metadata-safe exclusions, consumer/authority/temporal bindings, controlled
  self-hosting evidence, and no mutation.
