# E.4 Mission V09-CONTEXTUAL-REASONING-SURFACE-001 - Reasoning CLI And Check
## Version: 0.1.0
Last Updated: 2026-08-24
Owner: Context OS Maintainers
Status: closed

---

## Purpose

Expose the proven Contextual Assessment as a narrow read-only human/machine
product surface and provide deterministic saved-assessment validation before
reuse.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V09-CONTEXTUAL-REASONING-SURFACE-001
  title: Contextual Reasoning CLI And Saved Assessment Check
  initiating_lifecycle: release
  release: v0.9-contextual-reasoning
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed
  authority: implement_validate_capture_evidence_and_commit_without_push
  depends_on:
    - V09-CONTEXTUAL-REASONING-USE-001
    - V09-STRUCTURED-REASONING-EVIDENCE-001
  constraints:
    - read_only
    - no_reasoning_logic_in_cli
    - pure_machine_output
    - no_free_form_generation
    - no_decision_execution_or_canonical_mutation
    - no_graphrag_or_future_scope
  acceptance_criteria:
    - contextos_reason_emits_useful_human_assessment
    - contextos_reason_emits_pure_machine_report
    - exact_json_inputs_preserve_authority_and_provenance
    - saved_assessment_check_detects_material_drift
    - prior_cli_surfaces_remain_stable
```

---

## Exit Conditions

- CLI wraps `ContextualAssessmentEngine` directly;
- Goal is mandatory and Mission/consumer/context inputs are explicit;
- Context Version, policy, metadata, structured evidence, and focus inputs can
  be supplied without CLI reinterpretation;
- `--check-assessment` verifies identity and regenerates exact bound inputs or
  returns explicit invalidation;
- human and JSON outputs remain read-only and authority-safe;
- all released regressions remain green.

---

## Governing Context Evidence

```text
activation.package.b5cc83b3d4d3bd0a
package hash: b5cc83b3d4d3bd0af27b80ede7dc0492b8a4e3f7ab6cde2ad57ab73352825434
activation.handoff.963c0dd6b806f60a
handoff hash: 963c0dd6b806f60acd6767a9e61716b0bfefacf18a062e9852ae6ab500b6d33c
context.version.95be7c4b50e3fff1
version hash: 95be7c4b50e3fff108e1c6d3b1e52ccc2542955b1d2ce772b0b361259327c097
```

Package and Handoff were valid. The Version bound 44 exact sources and was
immutable, historically verified, and an exact current match at capture.

---

## Capability Delivered

`contextos reason` wraps `ContextualAssessmentEngine` directly and supports:

- Goal, Mission, question, purpose, consumer, mode, roles, and authority scope;
- retention-policy and memory-metadata JSON;
- exact Context Versions and Mission-use evidence;
- `contextos.reasoning.evidence_set/1` and focus entities;
- explicit temporal basis and bounded Memory result count;
- human, pure JSON, and `--json-out` output;
- `--check-assessment` deterministic reuse validation.

The CLI contains no reasoning, Retrieval, Health, policy, or authority logic.
It remains read-only and returns released exit semantics: 0 success/exact
check, 7 blocking gate or invalidation, 8 fatal, and 9 misconfiguration.

`ContextualAssessmentEngine.check_assessment(...)` verifies immutable identity
and reproduces exact preserved query, Context Versions, Mission-use evidence,
structured evidence, temporal basis, and current Runtime state. Policy and
metadata inputs must be supplied again; changed or missing inputs invalidate
reuse.

---

## Dogfood Evidence

| Evidence | Result |
|---|---|
| Human `contextos reason` | exit `0`; all epistemic and authority sections visible |
| JSON stdout | exit `0`; pure parseable `contextos.reasoning.assessment/1` |
| Saved Assessment | `reasoning.assessment.323b62a5eecdac2c` |
| Immediate check | `reasoning.assessment_check.8047afacecdd8dc1`; exact match; exit `0` |
| Human/JSON mutation | none |
| CLI version | `contextos 0.9.0-cli-v0` |

Separate fresh invocations without explicit `evaluation_time` may produce
different identities because policy-aware Memory uses invocation time as its
temporal basis. Saved validation reproduces the preserved basis exactly.

---

## Validation Evidence

| Evidence | Result |
|---|---|
| CLI suite | 57 passed including five Reasoning cases |
| Assessment/check tests | 8 passed |
| Pure stdout JSON and `json.tool` | passed |
| Saved exact check and source-drift invalidation | passed |
| Tamper invalidation | passed |
| Prior CLI behavior | CLI suite green |
| Full regressions | 335 tests passed across 37 test programs |
| Validator gate | exit `0`; zero errors and fatals |
| Whitespace | `git diff --check` passed |

---

## Learning

A public surface became justified only after benchmark and self-hosted use
evidence. The smallest coherent surface includes saved-result validation;
otherwise a machine-readable working assessment could silently outlive its
governing inputs.

Temporal evaluation is part of reasoning context. Determinism means same exact
inputs, including time basis, not merely unchanged repository files.

---

## Next Mission Recommended

```text
V09-CONTEXTUAL-REASONING-RELEASE-VERIFY-001
```

Goal: verify the complete v0.9 product journey, benchmark, self-hosting use,
truth/authority boundaries, invalidation, GraphRAG deferral, Theory claims, and
v0.3-v0.8 regressions before declaring release readiness.

---

## Mission Decision

```text
CLOSED_DONE
```
