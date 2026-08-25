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
| BootstrapApplyResult | A governed create-only apply evidence report | tools/bootstrap apply output | id, preflight, confirmation, mutation_set, mutations, validation, rollback, result | N | Records explicit result state after create-only apply and validation |
| MemoryRetentionPolicy | A versioned governance policy for preservation, sensitivity, access, holds, retrieval, Activation, forgetting, and recovery | organization policy / future Runtime input | id, version, scope, owner, purpose, rules, inheritance, authority, evidence | Context-dependent | Defines bounds; never executes a retention transition |
| MemoryRetentionDecision | A memory-specific immutable Decision Record resolving exact policies and constraints for exact memory items | governance decision evidence | id, item_ids, source_hashes, policy_resolution, states, holds, authority, evidence, reversibility, lineage | Context-dependent | Does not authorize execution unless a separate transition contract explicitly does so |
| MemoryRetentionResolution | A deterministic read-only derived evaluation of explicit policies against exact memory metadata | tools/memory retention-resolution output | id, input_fingerprint, policy_hashes, operation_results, holds, conflicts, unknowns, authority, invalidation | Context-dependent | Grants no authority and performs no transition, deletion, forgetting, or canonical mutation |
| ContextVersion | An immutable, content-free identity and provenance record for governed context at a meaningful event | tools/memory Context Version output / future governed version store | id, identity_hash, scope, capture, source_manifest, source_fingerprint, bindings, lineage, truth_summary, retention, continuity_gaps | Context-dependent | Identifies historical source state; it is not copied context, an Activation Package, a Git commit, or authority |
| ContextualAssessment | A deterministic read-only advisory view derived from governed Runtime evidence for an exact Goal/Mission and consumer | tools/reasoning Contextual Assessment output | id, identity_hash, query, bindings, observations, prior_art, context_changes, contradictions, interpretations, hypotheses, recommendations, unknowns, required_decisions, evidence, authority, invalidation | Context-dependent | Derived working view; never a Decision, authority, canonical truth, or second SSOT |

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
- BootstrapApplyPreflight → may become BootstrapApplyResult only with explicit preflight-bound apply confirmation
- BootstrapApplyResult → may become ChangeRequest evidence only after validated apply
- BootstrapApprovalRecord → may become DecisionRecord only after human authority
- MemoryRetentionPolicy → constrains Memory Retrieval, Context Activation, and future retention transitions
- MemoryRetentionDecision → specializes DecisionRecord and binds an exact policy resolution without changing canonical truth
- MemoryRetentionResolution → constrains Memory Retrieval before candidate exposure and future Activation/transition review without executing policy
- ContextVersion → binds Missions, Decisions, Approvals, Promotions, releases,
  and other consequential events to exact governed source identities and hashes
- ContextVersion → may reference Activation Package/Handoff evidence without
  becoming working context or granting historical authority
- ContextVersion → may become `context_state` Organizational Memory while its
  metadata and referenced content remain independently retention-governed
- MissionPacket and Mission-derived memory → may bind an exact ContextVersion,
  partial historical evidence, or an explicit unknown without reconstruction
- Memory Retrieval → may expose ContextVersion identity and lineage only after
  independent policy resolution; Retrieval grants no historical authority
- ContextualAssessment → consumes Activation, Health, policy-aware Memory, and
  ContextVersion evidence without changing their authority
- ContextualAssessment → may propose a Decision or Mission candidate only
  through existing human authority and governance lifecycles

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
- 2026-08-21 — v0.1.0 — Added policy-only MemoryRetentionPolicy and
  MemoryRetentionDecision entities.
- 2026-08-21 — v0.1.0 — Added read-only MemoryRetentionResolution derived-view
  entity.
- 2026-08-23 — v0.1.0 — Bound MemoryRetentionResolution to policy-before-exposure
  Retrieval while preserving independent Activation eligibility.
- 2026-08-23 — v0.1.0 — Added immutable, content-free ContextVersion and its
  Mission, Activation, Memory, supersession, and retention boundaries.
- 2026-08-23 — v0.1.0 — Added exact/partial/unknown Memory bindings and
  policy-before-exposure ContextVersion Retrieval relationships.
- 2026-08-24 — v0.1.0 — Added ContextualAssessment as a deterministic,
  non-canonical, non-decisional derived reasoning entity.
