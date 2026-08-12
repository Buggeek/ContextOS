# E.4 Mission V06-ACTIVATION-HANDOFF-USE-001 - Handoff-First Mission Execution
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Prove that a real self-hosted Mission can begin from a valid Activation Handoff
as its governing working context, with only minimal additional human instruction.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V06-ACTIVATION-HANDOFF-USE-001
  title: Handoff-First Mission Execution
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

## Minimal Human Instruction

```text
Use the current valid Activation Handoff and continue v0.6.
```

The handoff supplied the active release, Mission identity, authority boundary,
selected canonical sources, exclusions, gaps, and evidence obligations.

---

## Activation Handoff Used

Initial handoff generated for this Mission:

```text
contextos.activation.handoff/1
```

Initial handoff status:

```text
handoff_ready=true
package_valid_now=true
```

The initial handoff became invalid after this Mission modified selected
canonical sources. This is expected and demonstrates that source mutation during
handoff-first execution requires a fresh handoff/check before follow-on work.

Exact current package and handoff ids are generated evidence, not canonical
truth, and are reported at Mission closeout rather than hard-coded into this
artifact.

---

## Mission Selected

```text
V06-ACTIVATION-HANDOFF-CHECK-001
```

Reason:

The handoff proved sufficient for Mission orientation, but the runtime could
only check the package used to create a handoff. A future consumer also needs to
verify the saved handoff itself before beginning work from it.

---

## Capability Delivered

Implemented `contextos.activation.handoff_check/1`.

The handoff check validates:

- handoff identity hash,
- selected canonical source hashes,
- Validator gate state,
- package file reference when available,
- source package id/hash binding,
- referenced package validity,
- read-only/no-mutation/no-selection-regeneration boundaries.

Runtime CLI surface:

```bash
./contextos activate \
  --root . \
  --check-handoff /tmp/contextos-activation-handoff.json \
  --format json
```

---

## Context Classes

### Governing Context

Governing context came from the Activation Handoff:

- active release: v0.6 Context Activation,
- Mission: `V06-ACTIVATION-HANDOFF-USE-001`,
- goal: continue v0.6 from a valid handoff,
- canonical SSOT/foundation/mission sources,
- authority: read canonical context and use working context only,
- prohibited authority: canonical mutation, promotion, delegation,
- constraints: no agents, no Graph runtime, no Knowledge Engine expansion, no
  adapter implementation, no background synchronization,
- evidence obligations: selected sources, exclusions, additional reads,
  validation, learning, Evolution Inbox.

The handoff was sufficient for orientation.

### Execution Context

Additional exact context was required for implementation:

- `tools/activation/activation_engine/package_engine.py`,
- `tools/activation/activation_engine/report_builder.py`,
- `tools/activation/test_activation_package.py`,
- `tools/cli/contextos_cli.py`,
- `tools/cli/test_contextos_cli.py`,
- `docs/1.x_architecture/1.5_runtime_contracts/1.5.9_Context_Activation_Package_Contract.md`,
- `tools/activation/README.md`,
- `SSOT/P.1_Product_Map.md`,
- `SSOT/A.1_System_Map.md`,
- `SSOT/P.2_Product_Roadmap.md`,
- `SSOT/E.5_Evolution_Inbox.md`.

Reason:

These files were needed to implement, expose, document, and verify the handoff
check. Their retrieval was execution-driven rather than orientation-driven.

### Irrelevant Context

The Mission did not require:

- v0.3 readiness internals,
- v0.4 bootstrap internals beyond regression execution,
- v0.5 builder/construction internals beyond regression execution,
- Knowledge Engine,
- Context Graph runtime,
- agent runtime,
- IDE adapter implementation,
- external connectors,
- historical release-cut details.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Initial handoff generated | `contextos.activation.handoff/1` |
| Initial handoff ready | yes |
| Handoff check schema implemented | `contextos.activation.handoff_check/1` |
| Handoff check validates identity | yes |
| Handoff check validates selected source hashes | yes |
| Handoff check validates package ref/binding when present | yes |
| Handoff check validates Validator gate | yes |
| Handoff check avoids context reselection | yes |
| Handoff check performs mutation | no |
| CLI `--check-handoff` added | yes |
| JSON output purity | verified |
| Drift invalidation | tested |
| Prior release behavior | regression-tested |

---

## Context Sufficiency Observations

- Handoff-first execution reduced the human instruction to a short directive.
- The handoff was sufficient to identify release, Mission, scope, authority,
  constraints, selected sources, gaps, and evidence obligations.
- Runtime implementation still required code/test/document reads that were not
  all selected as governing context.
- This suggests Context OS may eventually distinguish governing activation from
  execution activation while preserving one coherent Mission context model.

---

## Learning

Minimum Sufficient Context is not the smallest prompt or the largest package.
For implementation Missions, governing context and execution context are
different layers:

- governing context explains what should be done and under which authority,
- execution context enables safe code/docs changes,
- irrelevant context should remain excluded unless evidence proves otherwise.

The activation model should preserve this distinction without creating parallel
Mission models.

---

## Evolution Impact

This Mission advances v0.6 by proving handoff-first execution and adding the
missing check that lets a saved handoff remain a governed working-context
artifact. It does not introduce adapters, agents, Graph runtime, Knowledge
Engine expansion, broad RAG, automatic mutation, or future-release scope.

---

## Next Mission Recommended

```text
V06-ACTIVATION-CONTEXT-LAYERS-001
```

Define and implement the smallest activation-layer distinction between
governing context and execution context, if release scope confirms it is
necessary before v0.6 release verification.
