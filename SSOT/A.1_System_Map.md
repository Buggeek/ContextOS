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
| tools/bootstrap | Module | Read-only Guided Bootstrap planning engine and reports | Maintainers | v0.4 planning component
| tools/cli | Module | Runtime CLI implementation and tests | Maintainers | Current surfaces: validate, assess, init plan
| contextos | Executable | Root Runtime CLI entry point | Maintainers | Current surfaces: help/version/validate/assess/init
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
6. Readiness assessment -> bootstrap plan -> governed future apply decision

---

## Known Gaps / Drift

- No write-capable Guided Bootstrap apply surface exists yet
- No Discovery Bundle, Knowledge Engine, Context Builder, Context Graph
  runtime, Activation Layer, or agent runtime exists yet
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
- 2026-02-19 — v0.1.0 — Initial creation
