# E.5 Evolution Inbox
## Version: 0.1.0
Last Updated: 2026-08-11
Owner: Context OS Maintainers
Status: Active

---

## Purpose

Capture ideas, discoveries, risks, technical debt, opportunities, and
hypotheses that emerge during Context OS execution without allowing them to
disrupt the active mission.

The Evolution Inbox is not a roadmap, backlog, or approval queue. It is a
quarantine and triage surface for context that may deserve future action.

---

## Intake Rules

1. Inbox items must not change the scope of the active mission.
2. Every item must declare a source mission or source observation.
3. Items must be triaged before they become roadmap, epic, release, or mission
   work.
4. Items that require authority must remain `decision-needed` until a human
   owner accepts, rejects, or defers them.
5. Items promoted to execution must link to a Mission Packet.
6. Items may be deleted only through a recorded governance decision; otherwise
   they should be marked `rejected` or `superseded`.

---

## Triage States

| State | Meaning |
|---|---|
| new | Captured but not reviewed |
| accepted | Worth preserving, but not yet scheduled |
| decision-needed | Requires human authority before action |
| linked-to-mission | Promoted into a Mission Packet |
| deferred | Intentionally postponed |
| rejected | Reviewed and declined |
| superseded | Replaced by a better item or completed artifact |

---

## Inbox Items

| ID | Type | State | Source | Summary | Suggested disposition |
|---|---|---|---|---|---|
| INBOX-001 | technical-debt | accepted | SELFHOST-001 | Mission Packet and Evolution Inbox templates are missing. | Defer until two mission packets have been executed and audited. |
| INBOX-002 | architecture | linked-to-mission | SELFHOST-001 | Guided Bootstrap apply must define approval, evidence, and rollback before any write-capable `init` behavior. | Represented by V04-BOOTSTRAP-APPLY-001. |
| INBOX-003 | product-risk | accepted | SELFHOST-001 | Mission Runtime and `contextos mission` are tempting but premature for v0.4. | Revisit during Activate or Human-Agent Runtime releases. |
| INBOX-004 | governance | decision-needed | SELFHOST-001 | Mission closure could eventually require a first-class authority ledger entry for L3+ agent actions. | Decide before automating Mission Runtime. |
| INBOX-005 | taxonomy | accepted | SELFHOST-001 | E.4 and E.5 were added before templates exist. | Keep explicit template deferral until mission artifact shape stabilizes. |
| INBOX-006 | implementation | accepted | V04-BOOTSTRAP-APPLY-001 | A read-only Bootstrap Proposal generator is needed before any apply implementation. | Promote to the next v0.4 mission. |
| INBOX-007 | governance | accepted | V04-BOOTSTRAP-APPLY-001 | Apply approval needs durable Decision Record and Ledger support, but Mission Runtime does not exist yet. | Use mission evidence and commit history temporarily; require ledger integration before automated Mission Runtime. |
| INBOX-008 | product-risk | accepted | V04-BOOTSTRAP-APPLY-001 | Users may expect `contextos init` to write files. | Preserve read-only default and require an explicit proposal-approved apply surface. |
| INBOX-009 | technical-debt | accepted | V04-BOOTSTRAP-APPLY-001 | Proposal canonical hashing and repository fingerprinting need deterministic implementation rules. | Define during Bootstrap Proposal Engine implementation. |
| INBOX-010 | governance | deferred | V04-BOOTSTRAP-APPLY-001 | Replacement or overwrite actions are prohibited for v0.4 but may be needed later for repair workflows. | Revisit after create-only apply is proven. |
| INBOX-011 | implementation | superseded | V04-BOOTSTRAP-PROPOSAL-001 | Proposal persistence and CLI exposure are not implemented. | CLI exposure and user-selected JSON-out implemented by V04-BOOTSTRAP-PROPOSAL-REVIEW-001; durable approval storage remains future work. |
| INBOX-012 | technical-debt | accepted | V04-BOOTSTRAP-PROPOSAL-001 | Proposal identity currently depends on canonical JSON hashing and repository fingerprints; schema changes must preserve compatibility or version the proposal. | Treat breaking hash changes as proposal schema changes. |
| INBOX-013 | governance | accepted | V04-BOOTSTRAP-PROPOSAL-001 | Future proposal approval should require a clean repository state or an explicit dirty-state waiver. | Decide in the approval/persistence mission before apply. |
| INBOX-014 | implementation | superseded | V04-BOOTSTRAP-PROPOSAL-001 | Proposal engine has no human renderer yet. | Implemented by V04-BOOTSTRAP-PROPOSAL-REVIEW-001. |
| INBOX-015 | governance | accepted | V04-BOOTSTRAP-PROPOSAL-REVIEW-001 | Approval needs a read-only Decision/Approval record that binds proposal id, identity hash, approvers, authority mode, and expiry before apply exists. | Promote to the next v0.4 mission. |
| INBOX-016 | implementation | accepted | V04-BOOTSTRAP-PROPOSAL-REVIEW-001 | Proposal review has JSON-out preservation but no first-class approval-state transition command. | Define approval record before apply implementation. |
| INBOX-017 | governance | linked-to-mission | V04-BOOTSTRAP-APPROVAL-001 | Approval record draft exists, but accepted approval still requires an explicit human authority action. | Represented by V04-BOOTSTRAP-APPROVAL-ACCEPT-001. |
| INBOX-018 | implementation | superseded | V04-BOOTSTRAP-APPROVAL-001 | Approval records are generated from proposal files but are not yet persisted as immutable Decision Records. | Accepted decision output now embeds `contextos.decision/1`; durable ledger storage remains future work. |
| INBOX-019 | technical-debt | accepted | V04-BOOTSTRAP-APPROVAL-001 | Proposal drift comparison previously used path tree hash instead of full fingerprint hash. | Fixed in this mission; keep regression coverage. |
| INBOX-020 | implementation | linked-to-mission | V04-BOOTSTRAP-APPROVAL-ACCEPT-001 | Future apply must consume an accepted decision artifact and revalidate proposal identity, source plan hash, repository fingerprint, file hashes, and drift before any mutation. | Represented by V04-BOOTSTRAP-APPLY-PREFLIGHT-001. |
| INBOX-021 | governance | accepted | V04-BOOTSTRAP-APPROVAL-ACCEPT-001 | Accepted decisions are portable JSON artifacts but not yet written to an Accountability Ledger. | Require ledger integration before automated Mission Runtime or multi-actor apply. |
| INBOX-022 | implementation | linked-to-mission | V04-BOOTSTRAP-APPLY-PREFLIGHT-001 | Future apply should consume a fresh eligible preflight report, not an accepted decision directly. | Represented by V04-BOOTSTRAP-APPLY-CREATE-ONLY-001. |
| INBOX-023 | governance | linked-to-mission | V04-BOOTSTRAP-APPLY-PREFLIGHT-001 | A successful preflight establishes eligibility but still does not provide final human apply confirmation. | Represented by V04-BOOTSTRAP-APPLY-CREATE-ONLY-001. |
| INBOX-024 | governance | decision-needed | V04-BOOTSTRAP-APPLY-CREATE-ONLY-001 | A real apply against the canonical Context OS repository requires target-specific human authorization bound to exact proposal, accepted decision, and fresh preflight. | Decide after release verification; do not infer from implementation authority. |
| INBOX-025 | product-risk | deferred | V04-BOOTSTRAP-APPLY-CREATE-ONLY-001 | Repair, overwrite, replacement, and deletion workflows are intentionally excluded from v0.4 create-only apply. | Revisit after create-only apply is proven in real target use. |
| INBOX-026 | governance | decision-needed | V04-GUIDED-BOOTSTRAP-RELEASE-VERIFY-001 | v0.4 is release-ready without canonical Context OS apply, but maintainers may still choose to run canonical apply as a separate target-specific decision. | Do not block release; require exact target authorization if pursued. |
| INBOX-027 | product | accepted | V04-GUIDED-BOOTSTRAP-RELEASE-VERIFY-001 | v0.5 should start from construction tasks derived from readiness/bootstrap evidence rather than broad Knowledge Engine scope. | Promote to v0.5 planning mission. |
| INBOX-028 | implementation | accepted | V05-CONTEXT-CONSTRUCTION-PLAN-001 | `contextos.construction.plan/1` needs a future Runtime CLI surface before non-developer users can request construction plans directly. | Consider after the planning engine is audited; do not add before the first Builder draft mission is shaped. |
| INBOX-029 | architecture | accepted | V05-CONTEXT-CONSTRUCTION-PLAN-001 | Construction planning currently uses the standard MOM artifact set; future organizational operations will need domain-specific artifact mappings without changing the lifecycle model. | Defer until the first non-technology operating-domain construction slice. |
| INBOX-030 | implementation | accepted | V05-CONTEXT-CONSTRUCTION-PLAN-001 | Full Discovery Bundle remains required before Builder draft generation can safely use source observations beyond existing inventory/readiness/bootstrap evidence. | Promote to the next v0.5 mission. |
| INBOX-031 | implementation | accepted | V05-DISCOVERY-BUNDLE-LOCAL-001 | `contextos scan` and source registry remain absent even though the local Discovery Bundle engine exists. | Defer until the engine is consumed by the first Builder draft mission or a user-facing construction CLI mission. |
| INBOX-032 | architecture | accepted | V05-DISCOVERY-BUNDLE-LOCAL-001 | Discovery currently captures literal local links and containment only; semantic relationships must wait for Knowledge/Graph maturity. | Preserve as a boundary for v0.5; revisit in Organizational Memory. |
| INBOX-033 | implementation | accepted | V05-DISCOVERY-BUNDLE-LOCAL-001 | Builder draft generation now has a stable local discovery input and should be shaped next without external connectors. | Promote to the next v0.5 mission. |
| INBOX-034 | implementation | accepted | V05-BUILDER-DRAFT-PLAN-001 | Builder Draft Plan has no Runtime CLI surface, so users cannot request it directly yet. | Consider a read-only construction CLI only after the first Builder write boundary is decided. |
| INBOX-035 | governance | accepted | V05-BUILDER-DRAFT-PLAN-001 | Write-capable Builder draft creation will require an explicit authority and no-overwrite model similar to Guided Bootstrap apply. | Promote before any `build-mom` or `build-ssot` write behavior. |
| INBOX-036 | architecture | accepted | V05-BUILDER-DRAFT-PLAN-001 | Confidence/support levels are planning aids and need a stable taxonomy before cross-domain Builder expansion. | Defer until first non-technology context construction slice or Builder draft generation hardening. |
| INBOX-037 | implementation | accepted | V05-BUILDER-DRAFT-AUTHORITY-001 | Builder draft writes need an implementation object equivalent to preflight/authorization before any file creation occurs. | Promote to the next v0.5 mission if write-capable draft behavior is authorized. |
| INBOX-038 | governance | decision-needed | V05-BUILDER-DRAFT-AUTHORITY-001 | The exact draft surface for future Builder writes is not yet selected. | Human authority should choose branch/worktree/scratch/draft directory before implementation. |
| INBOX-039 | implementation | accepted | V05-BUILDER-DRAFT-AUTHORITY-001 | Builder Draft Authority should eventually be enforced by tests and runtime preflight rather than documentation only. | Implement in the next Builder write-boundary mission. |
| INBOX-040 | implementation | accepted | V05-BUILDER-DRAFT-SURFACE-DECISION-001 | Local Draft Workspace support needs a runtime object that resolves `.contextos/drafts/` paths and enforces non-canonical scope. | Promote before first draft write implementation. |
| INBOX-041 | governance | accepted | V05-BUILDER-DRAFT-SURFACE-DECISION-001 | Draft retention, cleanup, and expiration policy needs more precise defaults after drafts exist. | Defer until draft artifacts are produced and audited. |
| INBOX-042 | architecture | accepted | V05-BUILDER-DRAFT-SURFACE-DECISION-001 | Future non-filesystem Draft Workspace adapters should preserve the same conceptual model across document, CRM, legal, finance, people, and data systems. | Defer until Activation or connector work. |
| INBOX-043 | implementation | accepted | V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001 | Future Builder draft creation should consume `contextos.builder.draft_workspace_preflight/1` rather than a raw Builder Draft Plan. | Promote when explicit write-capable Builder authority is granted. |
| INBOX-044 | product | accepted | V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001 | Builder Draft Plan and Draft Workspace preflight remain developer-only surfaces without Runtime CLI exposure. | Consider after first write-capable draft behavior is proven. |
| INBOX-045 | technical-debt | accepted | V05-BUILDER-DRAFT-WORKSPACE-RUNTIME-001 | Draft Workspace local mapping is fixed to `.contextos/drafts/`; future configurable workspace mappings need authority and adapter rules. | Defer until non-filesystem or multi-workspace runtime appears. |
| INBOX-046 | product | accepted | V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001 | Builder draft creation exists as an engine but has no user-facing CLI surface. | Promote to a governed CLI/review mission only after canonical target authorization is decided. |
| INBOX-047 | implementation | accepted | V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001 | The first draft artifact is a non-canonical envelope without generated domain content. | Future Builder content generation must remain evidence-supported and separately authorized. |
| INBOX-048 | governance | decision-needed | V05-BUILDER-DRAFT-CREATE-AUTHORIZED-001 | Creating a real draft in the canonical Context OS repository requires target-specific authority bound to exact preflight, draft item, and path. | Do not infer from implementation authority; require explicit human decision. |
| INBOX-049 | product | accepted | V05-BUILDER-DRAFT-REVIEW-SURFACE-001 | Draft review exists as an engine/human renderer but has no CLI or user-facing workflow surface. | Consider after review-decision authority is defined. |
| INBOX-050 | governance | accepted | V05-BUILDER-DRAFT-REVIEW-SURFACE-001 | A future review decision must persist separately from review rendering and must not imply approval or promotion. | Promote before any approval/promotion mission. |
| INBOX-051 | UX | accepted | V05-BUILDER-DRAFT-REVIEW-SURFACE-001 | Future review surfaces should visually separate observed, inferred, suggested, drafted, unknown, and approved truth states. | Defer to CLI/web/IDE review surface design. |
| INBOX-052 | product | accepted | V05-BUILDER-DRAFT-REVIEW-DECISION-001 | Review Decision exists as an engine/object but has no user-facing CLI or workflow surface. | Consider after the next lifecycle transition is defined. |
| INBOX-053 | governance | accepted | V05-BUILDER-DRAFT-REVIEW-DECISION-001 | Approval and promotion must consume exact Review Decisions without regenerating draft intent or treating review as approval. | Promote before any draft approval or canonical SSOT mutation mission. |
| INBOX-054 | product | accepted | V05-BUILDER-DRAFT-APPROVAL-DECISION-001 | Approval Decision exists as an engine/object but has no user-facing CLI or workflow surface. | Consider after promotion preflight is defined. |
| INBOX-055 | governance | accepted | V05-BUILDER-DRAFT-APPROVAL-DECISION-001 | Promotion must consume exact Approval Decisions and still require separate authority, validation, and canonical write boundaries. | Promote before any SSOT or canonical context mutation mission. |

---

## Change Log

- 2026-08-11 - v0.1.0 - Added Guided Bootstrap apply approval follow-up items.
- 2026-08-11 - v0.1.0 - Added Bootstrap Proposal Engine follow-up items.
- 2026-08-11 - v0.1.0 - Added Bootstrap Proposal Review Surface follow-up
  items.
- 2026-08-11 - v0.1.0 - Added Bootstrap Approval Record follow-up items.
- 2026-08-11 - v0.1.0 - Created Evolution Inbox for self-hosted execution.
- 2026-08-11 - v0.1.0 - Added Context Construction planning follow-up items.
- 2026-08-11 - v0.1.0 - Added Local Discovery Bundle follow-up items.
- 2026-08-11 - v0.1.0 - Added Builder Draft Planning follow-up items.
- 2026-08-11 - v0.1.0 - Added Builder Draft Authority follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Workspace decision follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Workspace runtime follow-up items.
- 2026-08-11 - v0.1.0 - Added create-only Builder draft write follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Review Surface follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Review Decision follow-up items.
- 2026-08-11 - v0.1.0 - Added Draft Approval Decision follow-up items.
