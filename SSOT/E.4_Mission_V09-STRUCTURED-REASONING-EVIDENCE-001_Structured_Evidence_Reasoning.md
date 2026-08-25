# E.4 Mission V09-STRUCTURED-REASONING-EVIDENCE-001 - Structured Evidence Reasoning
## Version: 0.1.0
Last Updated: 2026-08-24
Owner: Context OS Maintainers
Status: closed

---

## Purpose

Add the minimum universal claim and relationship evidence input required to
close measured contradiction, impact, and multi-hop reasoning gaps without
semantic invention, GraphRAG, or a new authoritative graph.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V09-STRUCTURED-REASONING-EVIDENCE-001
  title: Structured Evidence Reasoning
  initiating_lifecycle: release
  release: v0.9-contextual-reasoning
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed
  authority: implement_validate_capture_evidence_and_commit_without_push
  depends_on:
    - V09-CONTEXTUAL-REASONING-BENCHMARK-001
    - V09-CONTEXTUAL-REASONING-PLAN-001
  constraints:
    - explicit_evidence_only
    - no_semantic_truth_generation
    - no_authoritative_graph
    - bounded_explainable_traversal
    - no_graphrag_or_external_dependency
    - no_decision_or_canonical_authority
  acceptance_criteria:
    - exact_claims_and_relationships_preserve_provenance
    - contradictions_require_explicit_comparable_claims
    - impact_requires_explicit_relationships
    - bounded_multi_hop_paths_are_explainable
    - benchmark_gaps_close_without_hardcoded_answers
    - regressions_remain_green
```

---

## Exit Conditions

- a universal structured reasoning-evidence input is contract-defined;
- exact claims retain their truth-axis, temporal, authority, and source data;
- contradictions compare only matching explicit subjects/predicates/scopes;
- impact and multi-hop results cite every relationship in the path;
- unsupported semantic applicability remains unknown;
- the unchanged benchmark expectations pass through actual engine behavior;
- Mission evidence, learning, Inbox, and regressions are closed.

---

## Governing Context Evidence

```text
activation.package.30fed2d8818cf2f5
package hash: 30fed2d8818cf2f50ba5fd12c4dddd6495497cc3ba5407f4ba3a08eacb6510ba
activation.handoff.6f12723c5b98f852
handoff hash: 6f12723c5b98f85222779900774ed5d49aafc685afb33313b9a48be87b2aee3b
context.version.e7f0dc5e3e89154f
version hash: e7f0dc5e3e89154f44d65aa620ce180840b4479d7fb26102974ae63801acd8ef
```

Package and Handoff were valid. The Context Version bound 41 exact sources and
was immutable, historically verified, and an exact current match at capture.

---

## Capability Delivered

`contextos.reasoning.evidence_set/1` supplies exact claims and declared
relationships to Contextual Assessment. The engine:

- binds normalized evidence identity and focus entities to Assessment identity;
- rejects missing fields, unsupported support states, and duplicate ids;
- compares only exact subject, predicate, scope, and temporal-basis peers;
- reports differing values as an unresolved explicit-value conflict;
- traverses only declared impact relationship types to a maximum of three hops;
- cites every claim, relationship, and source reference used;
- preserves unsupported semantics and missing paths as unknown;
- grants no graph, Decision, execution, or canonical authority.

---

## Benchmark Result

```text
reasoning.benchmark.a3a021b1428e7963
identity hash: a3a021b1428e7963579ec74a80d2fb5eac643d68aab709ea759df32175ee3145
required classes: 10/10
passed: 10
failed: 0
release gaps: 0
```

The same benchmark classes now pass through actual Assessment behavior.
Contradiction compares exact claims, impact follows a direct declared edge, and
multi-hop follows a two-edge declared path with both evidence refs.

---

## GraphRAG Decision

```text
DEFER
```

Bounded traversal over supplied structured relationships satisfied the
controlled multi-hop case. No graph-aware comparison was needed and no
material graph advantage was proven. Reconsider only when a real-corpus case
misses authorized indirect evidence and a controlled comparison can isolate
Retrieval topology as the cause.

---

## Validation Evidence

| Evidence | Result |
|---|---|
| Structured evidence tests | 6 passed |
| Controlled benchmark tests | 4 passed |
| Existing Assessment tests | 6 passed |
| Exact scope/time comparison | passed |
| Duplicate-id and unsupported-relation safety | passed |
| Full regressions | 328 tests passed across 37 test programs |
| Validator gate | exit `0`; zero errors and fatals |
| Whitespace | `git diff --check` passed |

---

## Learning

The universal primitive is not a graph database. It is an exact, governed set
of claims and declared relationships whose provenance and truth axes survive
reasoning. A small bounded traversal closes the demonstrated product gap while
remaining explainable and portable beyond Technology.

Contradiction detection must report disagreement, not select a winner. A
relationship path demonstrates declared dependency/impact lineage, not causal
effectiveness or semantic applicability.

---

## Next Mission Recommended

```text
V09-CONTEXTUAL-REASONING-USE-001
```

Goal: execute a real self-hosted v0.9 Mission from a valid Contextual
Assessment, measure whether its recommendations and unknowns improve Mission
selection without becoming Decisions, and prove the full reasoning-to-evidence
learning loop.

---

## Mission Decision

```text
CLOSED_DONE
```
