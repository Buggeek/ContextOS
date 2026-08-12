# P.1 Product Map
## Version: 0.1.0
Last Updated: 2026-02-19  
Owner: Context OS Maintainers  

---

## Purpose

Define the product surfaces and user journeys of the Context OS project as a
usable Organizational Context Runtime repository.

---

## Product Surfaces

- Framework docs (`docs/`)
- Templates (`templates/`)
- Examples (`examples/`)
- Ops rules (`ops/`)
- Runtime contracts (`docs/1.x_architecture/1.5_runtime_contracts/`)
- Validator Engine tooling (`tools/validators/`)
- Context Readiness tooling (`tools/readiness/`)
- Guided Bootstrap planning/proposal tooling (`tools/bootstrap/`)
- Context Activation package tooling (`tools/activation/`)
- Runtime CLI tooling (`tools/cli/`, `contextos`)

---

## Core User Journeys (High-Level)

1. New adopter reads foundations -> understands MOM -> creates their SSOT
2. Adopter uses templates to build MOM artifacts
3. Contributor proposes a framework change -> validated by governance rules
4. Maintainers review diffs -> merge changes with evidence
5. Operator runs Runtime tooling -> receives validation or readiness feedback
6. Operator runs Guided Bootstrap planning -> receives a read-only bootstrap
   plan before any repository mutation
7. Future operator requests Guided Bootstrap apply -> reviews a preserved
   Bootstrap Proposal before any approved repository mutation
8. Operator preserves the proposal with JSON output before any future approval
   or apply operation
9. Operator generates a read-only approval record draft that binds the proposal
   to human authority before apply exists
10. Operator accepts the approval record with explicit human identity and role,
    producing a read-only accepted decision before apply exists
11. Operator runs apply preflight to verify accepted intent, drift, validator
    gates, no-overwrite guarantees, rollback expectations, and the exact future
    mutation set before apply exists
12. Operator gives explicit apply confirmation bound to the preflight id and
    hash, then Context OS performs create-only bootstrap apply with evidence,
    validation, rollback metadata, and result state
13. Actor requests mission-bound working context, and Context OS produces a
    read-only Activation Package that preserves canonical source hashes,
    provenance, permissions, and invalidation conditions
14. Actor checks an Activation Package before use, and Context OS detects
    source drift or Validator gate invalidation
15. Actor generates a package-backed Activation Handoff, and Context OS provides
    a compact working brief without copying canonical context into a second
    SSOT
16. Actor checks a saved Activation Handoff before use, and Context OS detects
    handoff identity drift, selected source drift, package binding drift, or
    Validator gate invalidation

---

## Key Capabilities

- Provide a minimal, coherent MOM definition
- Provide stable taxonomy + naming conventions
- Provide templates that map to taxonomy
- Provide examples demonstrating minimal vs strict compliance
- Provide validator, CLI, and readiness contracts with scoped runtime tooling
- Provide read-only bootstrap planning as the first Guided Bootstrap surface
- Provide read-only bootstrap proposal generation as the preserved bridge from
  plan to future apply approval
- Provide read-only bootstrap approval record drafts before any apply behavior
- Provide explicit read-only bootstrap approval acceptance before apply behavior
- Provide read-only apply preflight before any apply behavior
- Provide governed create-only bootstrap apply with explicit preflight-bound
  confirmation
- Define proposal-approved apply as the only future write-capable Guided
  Bootstrap path
- Provide read-only Activation Packages that make canonical context consumable
  without creating a parallel SSOT
- Provide a read-only `contextos activate` surface for generating and checking
  mission-bound working context packages
- Provide package-backed Activation Handoffs for humans, Codex, Claude Code,
  IDE assistants, and future consumers
- Provide Activation Handoff checks so a saved handoff can govern work only
  while its package binding, selected sources, and Validator gate remain valid

---

## Primary User Roles

- Adopter (implements SSOT for an org/product)
- Contributor (improves framework, templates, examples)
- Maintainer (governs evolution and coherence)

---

## Critical Constraints

- Avoid expanding taxonomy faster than templates/examples can support
- Keep compliance profiles explicit (`minimal` vs `strict`)
- No silent structural mutation: changes must be diff-reviewable

---

## Known Risks / Unknowns

- Terminology drift across documents over time
- Examples becoming outdated relative to taxonomy/templates
- Validator scope creep (enforcing too much too early)
- Bootstrap surface confusion if read-only planning and future apply are not
  kept distinct
- Apply implementation risk if proposal identity, authority, validator gates,
  and rollback are not preserved before mutation
- Activation risk if working context packages are mistaken for canonical source
  authority
- Handoff risk if compact operating briefs become tool-specific prompts instead
  of package-bound derived context
- Handoff-use risk if consumers skip direct handoff revalidation and rely only
  on a previously valid package check

---

## Dependencies

- A.1 System Map
- A.4 Data Entities
- Governance rules (G.1 / G.2)

---

## Linked Epics

- P.5 Epic — Structural integrity (links, headings, repo navigation)
- P.5 Epic — Validator Engine and runtime tooling

---

## Change Log

- 2026-08-11 — v0.1.1 — Added readiness/bootstrap planning surfaces and GENESIS alignment
- 2026-08-11 — v0.1.1 — Added Context Activation Package surface
- 2026-08-11 — v0.1.1 — Added Activation Package CLI and package check surface
- 2026-08-11 — v0.1.1 — Added package-backed Activation Handoff surface
- 2026-08-11 — v0.1.1 — Added Activation Handoff check surface
- 2026-08-11 — v0.1.1 — Added Guided Bootstrap apply approval boundary
- 2026-08-11 — v0.1.1 — Added Bootstrap Proposal Engine product capability
- 2026-08-11 — v0.1.1 — Added Bootstrap Proposal Review Surface to product
  journey
- 2026-08-11 — v0.1.1 — Added Bootstrap Approval Record Draft to product
  journey
- 2026-02-19 — v0.1.0 — Initial creation
