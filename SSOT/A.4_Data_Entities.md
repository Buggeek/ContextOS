# A.4 Data Entities
## Version: 0.1.0
Last Updated: 2026-02-19  
Owner: Context OS Maintainers  

---

## Purpose

Define the core “entities” Context OS operates on so taxonomy, templates, examples, and validators stay aligned.

---

## Entity Registry

| Entity | Description | Source of Truth (Service/DB) | Key Fields | PII? (Y/N) | Notes |
|--------|-------------|------------------------------|------------|------------|------|
| DocumentType | A taxonomy-defined artifact type | docs/2.x_taxonomy | prefix, name, required_fields | N | Governs naming + structure
| Template | A reusable SSOT doc scaffold | templates/ | type, version, sections | N | Must map to DocumentType
| SSOTDocument | An implementation artifact in SSOT | SSOT/ and examples/**/SSOT | owner, version, links | N | Governed by compliance profile
| ComplianceProfile | Validation mode for SSOT | docs/2.x_taxonomy | minimal/strict | N | Controls validator strictness
| ValidatorRule | A check applied to a target scope | tools/validators | rule_id, scope, severity | N | Must be explicit and minimal
| ChangeRequest | A proposed change to framework/SSOT | PRs | diff, rationale, evidence | N | Requires governance
| MissionPacket | A bounded accountable execution contract | SSOT/E.4_Mission_[ID].md | id, release, goal, slice, authority, constraints, acceptance_criteria, evidence, decision, learning | N | Canonical unit for self-hosted work before Mission Runtime exists
| EvolutionInboxItem | A deferred idea, risk, debt item, opportunity, or hypothesis | SSOT/E.5_Evolution_Inbox.md | id, type, state, source, summary, disposition | N | Prevents active mission drift while preserving learning
| BootstrapProposal | A preserved apply candidate produced from a read-only Bootstrap Plan | future contextos bootstrap apply surface / report output | id, source_plan_hash, repository_state, authority, actions, gates, status | N | Required before any Guided Bootstrap repository mutation
| BootstrapApprovalRecord | A read-only approval record draft binding a Bootstrap Proposal to human authority and a Decision Record draft | tools/bootstrap approval output | id, proposal, authority, decision, drift, blockers | N | Does not approve or authorize apply
| BootstrapAcceptedDecision | A read-only accepted human decision artifact for an exact Bootstrap Proposal identity | tools/bootstrap acceptance output | id, approval_record, proposal, authority, decision, validation, constraints | N | Approves preserved intent but does not authorize or perform apply
| BootstrapApplyPreflight | A read-only final gate that verifies an accepted decision and freezes the executable mutation set | tools/bootstrap preflight output | id, accepted_decision, approval_record, proposal, authority, frozen_mutation_set, validation, eligibility | N | May mark apply eligible but does not authorize or perform apply

---

## Relationships (High-Level)

- DocumentType → has Template(s)
- SSOTDocument → conforms to DocumentType (under a ComplianceProfile)
- ValidatorRule → validates SSOTDocument (and link/hygiene across repo)
- ChangeRequest → modifies DocumentType/Template/SSOTDocument under governance
- MissionPacket → executes Release Goal through bounded Slice Plan
- EvolutionInboxItem → may become MissionPacket only after triage and authority
- BootstrapProposal → may become BootstrapApprovalRecord after review
- BootstrapApprovalRecord → may become BootstrapAcceptedDecision only through explicit human authority
- BootstrapAcceptedDecision → may become BootstrapApplyPreflight before apply
- BootstrapApplyPreflight → may become ChangeRequest only during a future apply mission
- BootstrapApprovalRecord → may become DecisionRecord only after human authority

---

## Ownership Boundaries

- Maintainers own taxonomy, templates, validators, and examples.
- Contributors may propose changes via PRs, but cannot bypass governance.

---

## Data Constraints

- Versioning must be explicit in SSOT docs.
- Cross-references must be resolvable (no broken links).
- Compliance profile must be declared to avoid ambiguous enforcement.

---

## Known Gaps / Unknowns

- How strict version bump rules should be for framework docs vs SSOT docs
- How to represent non-Markdown artifacts (diagrams) while keeping governance auditable
- When to promote MissionPacket and EvolutionInbox templates after artifact
  shape stabilizes

---

## Linked Artifacts

- A.1 System Map
- P.1 Product Map
- tools/validators (validator specs)

---

## Change Log

- 2026-02-19 — v0.1.0 — Initial creation
- 2026-08-11 — v0.1.0 — Added MissionPacket and EvolutionInboxItem entities
  for self-hosted execution.
- 2026-08-11 — v0.1.0 — Added BootstrapProposal entity for governed Guided
  Bootstrap apply approval.
- 2026-08-11 — v0.1.0 — Added BootstrapApprovalRecord entity for read-only
  approval drafts.
