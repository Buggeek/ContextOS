# A.1 System Map
## Version: 0.1.1
Last Updated: 2026-08-21
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

The system serves the organizational model defined by the Theory of the
AI-Native Organization. No current runtime module may claim that broader
outcome by itself.

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
| tools/activation | Module | Read-only Context Activation Package, package check, handoff, and handoff check implementation and tests | Maintainers | v0.6 working-context package component
| tools/health | Module | Read-only Context Health report and Mission-use evidence across integrity, usefulness, learning, and non-canonical update candidates | Maintainers | v0.7 evidence-first health component
| tools/memory | Module | Read-only Organizational Memory continuity, policy-aware Retrieval, retention-policy resolution, immutable Context Version capture/checks, and exact/partial/unknown historical-context bindings | Maintainers | v0.8 continuity/retrieval/resolution/version component; no semantic comparison, restored historical authority, retention transition, or destructive behavior
| tools/reasoning | Module | Read-only governed Contextual Assessment over Activation, Health, policy-aware Memory, and Context Version evidence | Maintainers | v0.9 advisory reasoning component; no Decision, execution, canonical mutation, or GraphRAG
| tools/runtime | Module | Internal integrated Organizational Context Runtime benchmark and proof report | Maintainers | v1.0 read-only integration evidence; not a product orchestration surface
| tools/cli | Module | Runtime CLI implementation and tests | Maintainers | Current surfaces: validate, assess, init plan/proposal/approval/preflight/apply, activate package/check/handoff, health report, memory retrieval/check, contextual reasoning/check
| contextos | Executable | Root Runtime CLI entry point | Maintainers | Current surfaces: help/version/validate/assess/init/activate/health/memory/reason
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
10. Saved activation handoff -> handoff check -> handoff identity / source drift / package binding / validator gate validity decision
11. Mission Context -> Governing Context orientation -> bounded Execution Context retrieval only when execution requires it
12. Execution evidence -> Context Health signals -> non-canonical Context Update Candidate -> existing governed Construction lifecycle
13. Activation Package + Handoff + explicit Mission records -> Mission-use evidence -> explainable Context Usefulness signals
14. Validator + Readiness + Mission-use evidence -> `contextos health` -> human or machine Health report -> governed consideration
15. Mission + decision + evidence + outcome + learning + Inbox records -> Memory Continuity report -> explainable prior art and governed pattern candidates
16. Goal/Mission + current Activation Package + Memory Continuity -> private relevance candidates -> exact Retention Resolution -> metadata-safe bounded prior art -> retrieval validity check
17. Applicable retention policies + exact memory identity + consumer/authority/holds/time -> deterministic read-only policy resolution -> independent Retrieval/Activation eligibility or explicit blocked conflict
18. Governed source state + meaningful event + optional Activation evidence -> read-only Context Version capture plan -> immutable content-free Context Version -> historical verification and Memory lineage
19. Exact Context Version + governed Mission records -> Continuity binding -> independent version-metadata policy gate -> bounded historical Retrieval with no current authority
20. Goal/Mission + Activation + Health + policy-authorized Memory + Context Versions -> Contextual Assessment -> evidence-backed observations, hypotheses, recommendations, unknowns, and required human decisions
21. Exact structured claims + declared relationships + focus entities -> bounded comparison/traversal -> cited contradiction and impact assertions without graph authority
22. Goal/Mission + exact reasoning inputs -> `contextos reason` -> human or machine Assessment -> saved Assessment check before reuse
23. Released runtime APIs + exact accepted write-stage evidence -> integrated runtime benchmark -> explicit release blockers or coherent end-to-end proof

---

## Known Gaps / Drift

- No semantic Knowledge Engine, Context Graph runtime, activation adapters, or
  agent runtime exists yet; Contextual Assessment is bounded structured
  reasoning rather than free-form truth generation
- Organizational Memory provides continuity, policy-aware bounded retrieval,
  canonical retention-governance semantics, read-only policy resolution, and
  explicit Context Version capture/checks, and policy-safe historical bindings;
  no durable version registry, automatic capture, retention execution,
  forgetting, semantic historical comparison, Graph runtime, or learned ranking
  exists yet
- Template coverage does not yet span every possible taxonomy doc type
- The integrated runtime benchmark passes, but the first self-hosted v1.0 case
  now has post-change Context Version, fresh Activation, re-reasoning, and
  formal re-anchor evidence; final release verification remains pending

---

## Linked Artifacts

- A.4 Data Entities
- P.1 Product Map
- G.1 Definition of Ready
- G.2 Definition of Done
- [`0.9 Theory of the AI-Native Organization`](../docs/0.x_foundations/0.9_COS_Theory_of_the_AI_Native_Organization.md)

---

## Change Log

- 2026-08-24 - v0.1.1 - Added the internal v1.0 integrated runtime benchmark
  and the remaining self-hosted temporal closure dependency
- 2026-08-24 - v0.1.1 - Recorded temporal closure and re-anchor of the first
  complete v1.0 self-hosted evolution case

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
- 2026-08-11 — v0.1.1 — Added Activation Handoff Check to system map
- 2026-08-11 — v0.1.1 — Added Mission Context layer model to system map
- 2026-08-15 — v0.1.1 — Added read-only Context Health & Learning report
  component
- 2026-08-16 — v0.1.1 — Added structured Mission-use evidence input and flow
- 2026-08-20 — v0.1.1 — Added read-only Context Health CLI surface
- 2026-08-20 — v0.1.1 — Linked the AI-native organizational theory and
  clarified the unimplemented Organizational Memory boundary
- 2026-08-21 — v0.1.1 — Added the read-only Organizational Memory continuity
  report and derived-view boundary
- 2026-08-21 — v0.1.1 — Added bounded Activation-bound Memory retrieval and
  deterministic retrieval checks
- 2026-08-21 — v0.1.1 — Added the policy-only Organizational Memory
  retention-governance model and explicit no-execution boundary
- 2026-08-21 — v0.1.1 — Added deterministic read-only retention resolution,
  metadata-safe explanations, and drift checks
- 2026-08-23 — v0.1.1 — Integrated exact Retention Resolution before Memory
  candidate exposure with safe exclusions and policy-context invalidation
- 2026-08-23 — v0.1.1 — Added immutable, content-free Context Version capture
  planning, deterministic identity, source fingerprints, and historical checks
- 2026-08-23 — v0.1.1 — Integrated exact Context Version evidence into Memory
  Continuity and policy-aware Retrieval with partial/unknown gap preservation
- 2026-08-24 — v0.1.1 — Added the first read-only governed Contextual
  Assessment component and its explicit reasoning/authority boundaries
- 2026-08-24 — v0.1.1 — Added universal structured claims and bounded
  relationship traversal without introducing GraphRAG or a Context Graph
- 2026-08-24 — v0.1.1 — Added the read-only `contextos reason` surface and
  deterministic saved-Assessment validation
- 2026-02-19 — v0.1.0 — Initial creation
