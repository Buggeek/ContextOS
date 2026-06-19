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
- Runtime CLI tooling (`tools/cli/`, `contextos`)

---

## Core User Journeys (High-Level)

1. New adopter reads foundations -> understands MOM -> creates their SSOT
2. Adopter uses templates to build MOM artifacts
3. Contributor proposes a framework change -> validated by governance rules
4. Maintainers review diffs -> merge changes with evidence
5. Operator runs Runtime tooling -> receives validation or readiness feedback

---

## Key Capabilities

- Provide a minimal, coherent MOM definition
- Provide stable taxonomy + naming conventions
- Provide templates that map to taxonomy
- Provide examples demonstrating minimal vs strict compliance
- Provide validator, CLI, and readiness contracts with scoped runtime tooling

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

- 2026-02-19 — v0.1.0 — Initial creation
