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

---

## Change Log

- 2026-08-11 - v0.1.0 - Created Evolution Inbox for self-hosted execution.
