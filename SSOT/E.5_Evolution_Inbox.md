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
| INBOX-022 | implementation | accepted | V04-BOOTSTRAP-APPLY-PREFLIGHT-001 | Future apply should consume a fresh eligible preflight report, not an accepted decision directly. | Promote to the create-only apply mission. |
| INBOX-023 | governance | accepted | V04-BOOTSTRAP-APPLY-PREFLIGHT-001 | A successful preflight establishes eligibility but still does not provide final human apply confirmation. | Require explicit apply confirmation in the future apply mission. |

---

## Change Log

- 2026-08-11 - v0.1.0 - Added Guided Bootstrap apply approval follow-up items.
- 2026-08-11 - v0.1.0 - Added Bootstrap Proposal Engine follow-up items.
- 2026-08-11 - v0.1.0 - Added Bootstrap Proposal Review Surface follow-up
  items.
- 2026-08-11 - v0.1.0 - Added Bootstrap Approval Record follow-up items.
- 2026-08-11 - v0.1.0 - Created Evolution Inbox for self-hosted execution.
