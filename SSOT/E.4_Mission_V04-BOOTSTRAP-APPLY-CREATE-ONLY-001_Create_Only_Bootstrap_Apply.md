# E.4 Mission V04-BOOTSTRAP-APPLY-CREATE-ONLY-001 - Create-Only Bootstrap Apply
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: closed:done

---

## Purpose

Implement the first governed write-capable Guided Bootstrap apply operation.

This mission moves the governed transition from:

```text
Plan -> Proposal -> Decision/Approval Draft -> Accepted Decision -> Apply Preflight
```

to:

```text
Plan -> Proposal -> Decision/Approval Draft -> Accepted Decision -> Apply Preflight -> Explicit Apply Confirmation -> Apply -> Validate -> Evidence -> Result
```

The capability is create-only and may be exercised only against isolated test
targets unless a separate target-specific human authorization is granted.

---

## Mission Packet

```yaml
mission_packet:
  schema: contextos.mission.packet/1
  id: V04-BOOTSTRAP-APPLY-CREATE-ONLY-001
  title: Create-Only Bootstrap Apply
  initiating_lifecycle: release
  owner: Context OS Maintainers
  orchestrator: Codex
  status: closed:done
  created_at: 2026-08-11
```

---

## Release

v0.4 - Guided Bootstrap

---

## Goal

Execute only approved create actions from a fresh eligible Bootstrap Apply
Preflight after explicit human apply confirmation, then validate and report the
result with mutation evidence and rollback metadata.

---

## Slice

v0.4 implementation slice:

- implement `contextos.bootstrap.apply_result/1`,
- require explicit `--confirm-apply`,
- require confirming human identity and authority role,
- require confirmation to name the exact preflight id and identity hash,
- consume the supplied preflight mutation set without regenerating approved
  intent,
- execute only `create_directory`, `create_manifest`, and
  `create_from_template` actions,
- refuse overwrite, replacement, deletion, manual actions, and prohibited
  actions,
- record mutation evidence for every created artifact,
- run post-apply Validator gate,
- mark failed validation as a failed result,
- expose rollback capability for created artifacts only,
- expose apply through `contextos init --apply <preflight.json>`,
- preserve existing shipped behavior.

No repair, overwrite, Builder, Knowledge Engine, Discovery, Graph, agents,
external connectors, or future-release capability is included.

---

## Authority

| Role | Authority | Bound |
|---|---|---|
| Mission Owner | Approval authority | Context OS Maintainers |
| Codex | L3 bounded implementation | Apply engine, report renderer, CLI create-only surface, tests, and SSOT alignment |
| Codex | L3 controlled mutation | Isolated temporary/test repositories only |
| Codex | L0 for canonical Context OS apply | No authority to apply against the canonical working repository |
| Human apply confirmer | L3 apply confirmation | Must bind confirmation to exact preflight id and identity hash |

---

## Constraints

- No silent mutation.
- No apply without explicit human confirmation.
- No mutation of the canonical Context OS repository during dogfood.
- No regeneration of approved intent.
- No overwrite.
- No replacement.
- No deletion of pre-existing content.
- No prohibited/manual action execution.
- No future-release scope.
- Discoveries outside this mission enter the Evolution Inbox.

---

## Acceptance Criteria

1. `contextos.bootstrap.apply_result/1` exists as an implemented runtime
   object.
2. Apply consumes the exact supplied preflight.
3. Apply requires explicit confirmation.
4. Confirmation is bound to preflight id and identity hash.
5. Confirming role satisfies required authority.
6. Only approved mutation actions execute.
7. Apply is create-only.
8. No overwrite, replacement, deletion, prohibited action, or manual action
   occurs.
9. Every mutation produces evidence.
10. Every created path is attributable to proposal, preflight, action, and
    Mission evidence.
11. Post-apply validation is mandatory.
12. Failed validation cannot be represented as success.
13. Rollback capability exists for created artifacts.
14. Rollback does not remove pre-existing or user-modified content.
15. Repeated execution with the same preflight is blocked.
16. Repository drift between preflight and mutation invalidates execution.
17. Isolated mutation tests prove behavior without mutating canonical Context
    OS.
18. Existing shipped capabilities remain green.
19. Objective evidence is captured.
20. Evolution Inbox captures deferred work.

---

## Decision

Use `contextos init --apply <preflight.json>` as the first create-only Guided
Bootstrap apply surface.

Rationale:

- Guided Bootstrap remains under `init` while v0.4 is bootstrap-focused.
- Apply must consume a preflight report rather than an accepted decision or
  regenerated plan.
- Apply confirmation must explicitly bind to preflight id and identity hash.
- Apply is intentionally create-only; repair and overwrite workflows remain
  deferred.

---

## Capability Delivered

CLI:

```text
contextos init --root <target> --apply <preflight.json> --confirm-apply --confirmed-by <human> --confirmed-role <role> --confirmed-preflight-id <id> --confirmed-preflight-hash <hash>
contextos init --root <target> --apply <preflight.json> --confirm-apply --confirmed-by <human> --confirmed-role <role> --confirmed-preflight-id <id> --confirmed-preflight-hash <hash> --format json
contextos init --root <target> --apply <preflight.json> --confirm-apply --confirmed-by <human> --confirmed-role <role> --confirmed-preflight-id <id> --confirmed-preflight-hash <hash> --json-out <path>
```

Machine report:

```text
contextos.bootstrap.apply_result/1
```

---

## Evidence Plan

- Run apply tests against isolated temporary repositories.
- Run preflight, acceptance, approval, proposal, plan, validator, readiness,
  and CLI regression tests.
- Run isolated CLI dogfood apply against a copied/test repository only.
- Verify the canonical Context OS repository is not modified by dogfood.
- Verify `contextos validate --mode gate` remains exit code 0.
- Run `git diff --check`.

---

## Evidence Captured

| Evidence | Result |
|---|---|
| Apply engine implemented | `tools/bootstrap/bootstrap_engine/apply_engine.py` |
| Apply report renderer implemented | `tools/bootstrap/bootstrap_engine/apply_report_builder.py` |
| Apply tests added | `tools/bootstrap/test_bootstrap_apply.py` |
| CLI apply surface implemented | `tools/cli/contextos_cli.py` |
| CLI tests extended | `tools/cli/test_contextos_cli.py` |
| Preflight authority scope carried forward | `contextos.bootstrap.apply_preflight/1` now includes allowed/prohibited paths |
| Bootstrap docs aligned | `tools/bootstrap/README.md` |
| CLI contract aligned | `1.5.2 CLI Contract` documents create-only apply |
| Apply approval contract aligned | `1.5.7 Bootstrap Apply Approval Contract` documents fresh preflight and explicit confirmation before apply |
| System map aligned | `SSOT/A.1_System_Map.md` |
| Data entities aligned | `SSOT/A.4_Data_Entities.md` |
| Evolution Inbox updated | Repair/overwrite and canonical target apply authorization kept outside active scope |
| Apply tests | `python3 tools/bootstrap/test_bootstrap_apply.py` passed, 7 tests |
| Bootstrap regressions | Apply, preflight, acceptance, approval, proposal, and plan tests passed, 40 tests |
| CLI tests | `python3 tools/cli/test_contextos_cli.py` passed, 31 tests |
| Readiness tests | Repository inventory, scoring, and recommendations passed, 14 tests |
| Validator tests | `python3 tools/validators/test_contextos_validator.py` passed, 11 tests |
| Gate validation | `contextos validate --mode gate --format json` returned exit_code 0 |
| Isolated CLI dogfood apply | Temporary target returned `contextos.bootstrap.apply_result/1`, state `applied_validated`, success true, 3 mutations, post-validator error 0 and fatal 0 |
| Canonical target boundary | No real apply was executed against canonical Context OS repository |
| Whitespace validation | `git diff --check` passed |

Command evidence is captured in the final mission response and repository
history for the commit containing this artifact.

---

## Learning

- The apply engine should trust only the supplied preflight mutation set and
  local pre-apply checks, not upstream regeneration.
- Idempotency for v0.4 is refusal on reused stale preflight, not silent skip.
- Rollback must be hash-gated so user-modified created artifacts are not
  removed.
- Real target apply needs a separate target-specific authorization packet.

---

## Roadmap Impact

No release goal change.

v0.4 now supports the full governed create-only apply path in controlled
targets:

```text
Plan -> Proposal -> Approval -> Accepted Decision -> Fresh Eligible Preflight -> Explicit Apply Confirmation -> Apply -> Validate -> Evidence -> Result
```

Remaining v0.4 work should focus on release verification, examples, and whether
canonical Context OS should run a real target apply under separate human
authorization.

---

## Change Log

- 2026-08-11 - v0.1.0 - Implemented and closed create-only Bootstrap Apply
  mission.
