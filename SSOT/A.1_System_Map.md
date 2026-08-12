# A.1 System Map
## Version: 0.1.0
Last Updated: 2026-02-19  
Owner: Context OS Maintainers  

---

## Purpose

Make the Context OS repository “system” visible: its modules, boundaries, and how they evolve under governance.

---

## System Overview

Context OS is a repository-first Organizational Context Runtime with
framework documents, SSOT artifacts, runtime contracts, validator tooling,
CLI tooling, templates, examples, and operational rules.

The primary output is a coherent contextual operating layer that humans and
agents can use to assess, bootstrap, construct, activate, learn from, and
reason over shared context.

---

## Architecture Style

Modular monolith (documentation modules + tooling modules in one repository).

---

## Modules / Services Catalog (High-Level)

| Name | Type (Module/Service) | Responsibility | Owned By | Notes |
|------|------------------------|----------------|----------|------|
| docs | Module | Framework specification (foundations→strategy) | Maintainers | Conceptual layer
| templates | Module | SSOT artifact templates aligned to taxonomy | Maintainers | Practical adoption layer
| examples | Module | Reference SSOT implementations | Maintainers | Must declare compliance profiles
| ops | Module | Governance + agent rules for contributions | Maintainers | Evidence-based workflow
| tools/validators | Module | Validator Engine implementation and tests | Maintainers | Scope-controlled
| tools/readiness | Module | Context Readiness inventory, scoring, recommendations, and reports | Maintainers | v0.3 Runtime component
| tools/bootstrap | Module | Guided Bootstrap planning, proposal generation, approval-record drafts, accepted decisions, apply preflight, create-only apply, and reports | Maintainers | v0.4 plan/proposal/approval/acceptance/preflight/apply component
| tools/activation | Module | Read-only Context Activation Package, package check, and handoff implementation and tests | Maintainers | v0.6 working-context package component
| tools/cli | Module | Runtime CLI implementation and tests | Maintainers | Current surfaces: validate, assess, init plan, init proposal, init approval-record draft, init accepted decision, init apply preflight, init create-only apply, activate package, activate package check, activate handoff
| contextos | Executable | Root Runtime CLI entry point | Maintainers | Current surfaces: help/version/validate/assess/init plan/init proposal/init approval-record draft/init accepted decision/init apply preflight/init create-only apply/activate package/activate package check/activate handoff
| SSOT | Module | Dogfooding SSOT for the Context OS project | Maintainers | Minimal MOM only

---

## Key Data Stores

| Name | Type | Owned By | Notes |
|------|------|----------|------|
| Git repository | VCS | Maintainers | Diff-based governance

---

## External Dependencies

| Provider/System | Purpose | Interface (API/Webhook/etc.) | Risk Notes |
|----------------|---------|-------------------------------|------------|
| GitHub | Hosting + review workflow | PRs/issues | Process drift if not codified

---

## Critical System Flows

1. Framework change proposal → PR → review → merge
2. Template update -> example alignment -> validator contract update (if needed)
3. Taxonomy change -> template mapping update -> example adjustments
4. Runtime contract update -> epic alignment -> implementation mission
5. Validator/CLI change -> local tests -> gate validation -> commit
6. Readiness assessment -> bootstrap plan -> bootstrap proposal -> approval record draft -> accepted decision -> apply preflight -> explicit apply confirmation -> create-only apply result
7. Canonical context -> activation selection -> working context package -> consumer execution context
8. Context activation package -> package check -> source drift / validator gate validity decision
9. Valid activation package -> package-backed handoff -> consumer starts work from compact governed context

---

## Known Gaps / Drift

- No Knowledge Engine, Context Graph runtime, activation adapters, or agent
  runtime exists yet
- Template coverage does not yet span every possible taxonomy doc type

---

## Linked Artifacts

- A.4 Data Entities
- P.1 Product Map
- G.1 Definition of Ready
- G.2 Definition of Done

---

## Change Log

- 2026-08-11 — v0.1.1 — Aligned implemented Runtime surfaces and GENESIS direction
- 2026-08-11 — v0.1.1 — Added read-only Bootstrap Proposal Engine to system map
- 2026-08-11 — v0.1.1 — Added read-only Bootstrap Proposal Review Surface
  to system map
- 2026-08-11 — v0.1.1 — Added read-only Bootstrap Approval Record Draft to
  system map
- 2026-08-11 — v0.1.1 — Added read-only Context Activation Package to system
  map
- 2026-08-11 — v0.1.1 — Added Activation Package CLI and package check to
  system map
- 2026-08-11 — v0.1.1 — Added package-backed Activation Handoff to system map
- 2026-02-19 — v0.1.0 — Initial creation
