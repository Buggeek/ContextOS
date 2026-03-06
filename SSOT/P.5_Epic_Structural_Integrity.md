# P.5 Epic — Structural Integrity (Paths, Profiles, Validators)
## ID: EPIC-001
Version: 0.1.0  
Last Updated: 2026-02-19  
Owner: ContextOS Maintainers  
Status: In Progress  

---

## 1. Objective

Ensure the ContextOS framework repository is structurally coherent and self-consistent so adoption and governance are reliable.

- Linked Vision: S.1
- Linked Product Map: P.1

---

## 2. Problem Statement

Today, structural drift can occur between:
- repo navigation vs actual folder structure,
- taxonomy vs templates/examples,
- declared compliance profiles vs actual document contents.

This creates broken onboarding, reduces trust, and makes evidence-based governance harder.

---

## 3. Scope

- Included:
  - Canonical operational docs path (`docs/3.x_operation`) + legacy alias (`docs/3.x_mom`)
  - Compliance profiles (`minimal` vs `strict`) made explicit in taxonomy/examples
  - Strict example SSOT aligned with required fields
  - Validator spec defined with explicit scope and pass/fail
  - Dogfooding SSOT created for the project

---

## 4. Out of Scope

- Not included:
  - Implementing a full validator toolchain (v0 spec only)
  - Adding new doc types beyond what templates/examples can support

---

## 5. Impacted Systems

- A.1 System Map — impacted modules:
  - docs/
  - examples/
  - tools/validators/
  - SSOT/
- A.4 Data Entities — impacted entities:
  - SSOTDocument
  - ComplianceProfile
  - ValidatorRule
- A.5 Integration Map — impacted integrations:
  - N/A
- Permissions impact:
  - N/A

---

## 6. Dependencies

- Governance: G.1 / G.2
- Taxonomy: docs/2.x_taxonomy/
- Templates: templates/

---

## 7. Risks / Unknowns

- Risk: enforcing strictness too broadly (scope creep)
- Unknown: best “version bump” policy for framework docs vs SSOT docs
- Assumption: `docs/3.x_operation/` is the canonical operational path

---

## 8. Success Criteria

- Onboarding links point to real, versioned paths.
- Examples explicitly declare compliance profile and match it.
- Validator spec is explicit about scope and what fails.

---

## 9. User Stories

- E.1 User Story — US-001

---

## 10. Governance Checks

- [x] Meets Definition of Ready (G.1)
- [x] Architecture impact reviewed
- [ ] Data entity changes validated

---

## 11. Change Log

- 2026-02-19 — v0.1.0 — Initial creation
