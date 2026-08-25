# External Mission Handoff: LUKSPEED-ACTIVE-EXECUTION-INDEX-RECONCILIATION-001

## Handoff State

```text
PREPARED_BY_CONTEXT_OS
TARGET_EXECUTION = NOT_STARTED
TARGET_ELIGIBILITY = PENDING_RECEIVER_PREFLIGHT
AUTHORITY = AUTHORIZED_FOR_DOCS_ONLY
REMOTE_PUBLICATION = NOT_AUTHORIZED
MERGE = NOT_AUTHORIZED
```

This Handoff was prepared in Context OS. It does not execute the target
Mission, become Lukspeed SSOT, or transfer Context OS repository authority into
the target repository.

## Binding

| Field | Exact value |
|---|---|
| Context OS runtime | `Buggeek/ContextOS@db0a74ecbb54bfd841cd8b733280adae061fe060` |
| External Adoption Profile | `adoption.profile.lukspeed.v1` |
| Profile version | `1.0.0` |
| Profile identity | `7903beb239f2fc3bc26dd19732ab9aad1f877b2d87c63a5669cb9cf4a23ae75d` |
| Profile source | `examples/adoption_profiles/lukspeed.json` at the published Context OS SHA |
| Target organization | Lukspeed |
| Target repository | `LKSPDEV/lukspeed` |
| Mission | `LUKSPEED-ACTIVE-EXECUTION-INDEX-RECONCILIATION-001` |
| Machine packet | `lukspeed-active-execution-index-reconciliation-001.json` |

The accepted source evidence is
`SSOT/E.4_Mission_POST-V1-EXTERNAL-ADOPTION-PROFILE-001_External_Adoption_Portability.md`.
Its decision is
`GO_FOR_SEPARATELY_AUTHORIZED_READ_ONLY_OR_DOCS_ONLY_TARGET_MISSION`.

## Goal

Make the read-first Lukspeed active-work surface match current merged and
governed reality without changing product direction or opening implementation.

## Authority

The receiving project may perform one L3, docs-only, staged execution in a
clean isolated Lukspeed lane. It may read exact target-native authority and Git
evidence, edit only `docs/BACKLOG_PRIORIZADO.md`, validate the result, and
prepare one local docs-only commit.

This Handoff does not authorize remote publication, PR creation, merge, or any
other GitHub mutation. Those transitions require separate Lukspeed authority
and a fresh target repository preflight. Context OS authority and identity must
never be used for target operations.

## Permitted Scope

- Read the target-native governing sources selected by a fresh valid Activation
  Package.
- Read exact commit and merged-PR evidence needed to verify active-state labels.
- Create or use a clean isolated lane after Lukspeed repository preflight.
- Edit only `docs/BACKLOG_PRIORIZADO.md`.
- Run read-only Context OS diagnostics using the exact published runtime and
  profile.
- Validate and prepare one local docs-only commit.

## Prohibited Scope

- Every target path except `docs/BACKLOG_PRIORIZADO.md`.
- Product/runtime, web, backend, database, workflow, CI, provider, secret, or
  environment changes.
- Staging, production, customer, or rider-data access.
- Roadmap or product-priority changes.
- Cleaning, stashing, resetting, rebasing, reusing, or modifying the
  pre-existing active Lukspeed worktree.
- Reopening closed work without exact current authority.
- Overwriting or discarding existing user work.
- Using the Context OS repository identity for Lukspeed operations.
- Remote publication, PR creation, or merge without separate target authority.

## Target-Native Authority Map

| Purpose | Lukspeed source | Authority |
|---|---|---|
| Active work source of record | `docs/BACKLOG_PRIORIZADO.md` | Lukspeed Product Owner / target execution canon |
| Product truth | `docs/strategy/Lukspeed_Current_Product_Capabilities.md` | Lukspeed Product Owner / target product canon |
| Roadmap orientation | `docs/strategy/Lukspeed_Roadmap_v3.md` | Lukspeed Product Owner / target strategy canon; backlog wins on active-state conflict |
| Canon classification | `docs/DOCUMENTATION_GUIDE.md` | Lukspeed Documentation Authority |
| Human-agent authority | `docs/delivery-ops/CODEX_BUILD_AUTHORIZATION_MODEL.md` | Lukspeed Human Authority |
| Goal/Mission execution | `docs/delivery-ops/WAY_OF_WORK_V2_GOAL_DRIVEN_AUTONOMOUS_EXECUTION.md` | Lukspeed Delivery Authority |
| Evidence closure | `docs/delivery-ops/Lukspeed_Closure_Model.md` | Lukspeed Delivery Authority |

## Required Entry Gate

The Lukspeed Codex project must:

1. Confirm its current repository is exactly `LKSPDEV/lukspeed`.
2. Run `repo-authority-preflight LKSPDEV/lukspeed` and require
   `AUTHORITY_OK`; on mismatch, stop with `AUTHORITY_MISMATCH` and do not switch
   identities automatically.
3. Record exact target `origin/main` before analysis.
4. Establish a clean isolated lane without using or modifying the pre-existing
   active worktree.
5. Resolve the exact Context OS runtime and Adoption Profile binding above.
6. Generate a mission-start `contextos.context.version/1` over the exact target
   state and target-native authority sources.
7. Generate and validate fresh target-bound
   `contextos.activation.package/1` and `contextos.activation.handoff/1`
   artifacts for this Goal, Mission, and `codex` consumer.
8. Stop if the profile, Context Version, package, Handoff, source fingerprint,
   repository identity, authority, or Validator gate is invalid.

The operator must not manually nominate a replacement governing source set.
Context OS selects bounded target-native context from the Mission, Goal,
profile, and current target state.

## Acceptance And Evidence

- Record exact target `origin/main`, authority preflight, isolated-lane state,
  published Context OS SHA, and profile identity.
- Preserve machine-readable Context Version, Activation Package, Package Check,
  Handoff, and Handoff Check evidence.
- Inventory the active index before and after reconciliation.
- Cite exact merged PR, commit, closure, or canonical evidence for every changed
  status.
- Keep unknown, contradictory, or Product Owner-dependent states explicit.
- Prove the active index contains only open, queued, or ready work supported by
  current evidence.
- Do not reopen closed work, invent priority, or rewrite historical sections.
- Make one next active lane explicit or state honestly that it is unknown.
- Record before/after hash for `docs/BACKLOG_PRIORIZADO.md` and prove zero diff
  outside that path.
- Run applicable documentation checks and Context OS Validator gate under the
  exact target profile.
- Record the local docs-only commit and stop before publication or merge.

## Rollback And Stop Boundary

Before commit, restore only the isolated copy of the permitted file. After a
local commit, revert that exact single docs commit or discard the isolated lane
after preserving evidence. Rollback must never remove or rewrite pre-existing
user content.

Stop immediately on identity mismatch, inability to isolate active work,
conflicting evidence requiring Product Owner judgment, any required out-of-scope
file or system, invalid Context OS evidence, or a request to publish or merge
without separate target authority.

## Exact Receiving-Project Instruction

```text
Execute LUKSPEED-ACTIVE-EXECUTION-INDEX-RECONCILIATION-001 using the governed
external Mission Handoff artifact supplied with this instruction, machine id
external.mission_handoff.4677296e6d63bc20. Use the exact published Context OS
runtime and Adoption Profile from
Buggeek/ContextOS@db0a74ecbb54bfd841cd8b733280adae061fe060. Do not substitute
a newer runtime, profile, or manually reconstructed packet.

Authority is AUTHORIZED_FOR_DOCS_ONLY. Before any target access or mutation,
confirm cwd/repository, canonical LKSPDEV/lukspeed remote, repository-bound
LKSPDEV identity, and run repo-authority-preflight LKSPDEV/lukspeed. On any
mismatch, stop with AUTHORITY_MISMATCH and do not switch accounts.

Create or use a clean isolated lane. Do not use, clean, stash, reset, rebase,
or modify the pre-existing active Lukspeed worktree. Bind the exact published
Context OS runtime and adoption.profile.lukspeed.v1 profile, then generate and
validate a fresh target-bound Context Version, Activation Package, and Handoff
for the exact Mission and Goal before execution.

You may edit only docs/BACKLOG_PRIORIZADO.md and prepare one local docs-only
commit. Preserve target-native authority, cite exact evidence for every status
change, keep uncertainty explicit, prove zero diff outside the permitted file,
and stop before push, PR creation, or merge. Do not access runtime, production,
providers, secrets, customer/rider data, or any prohibited surface. Return the
evidence packet and the exact separate Lukspeed authority required next.
```
