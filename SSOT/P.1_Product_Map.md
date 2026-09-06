# P.1 Product Map
## Version: 0.1.3
Last Updated: 2026-09-06
Owner: Context OS Maintainers

---

## Purpose

Define the product surfaces and user journeys of the Context OS project as a
usable Organizational Context Runtime repository.

---

## Product Surfaces

- Canonical AI-native organization theory
  (`docs/0.x_foundations/0.9_COS_Theory_of_the_AI_Native_Organization.md`)
- Framework docs (`docs/`)
- Templates (`templates/`)
- Examples (`examples/`)
- Ops rules (`ops/`)
- Runtime contracts (`docs/1.x_architecture/1.5_runtime_contracts/`)
- Validator Engine tooling (`tools/validators/`)
- Context Readiness tooling (`tools/readiness/`)
- Guided Bootstrap plan/approval/preflight/create-only apply (`tools/bootstrap/`)
- Local Discovery, Construction and Builder Python APIs (`tools/discovery/`,
  `tools/construction/`, `tools/builder/`)
- Governed External Adoption Profiles (`tools/adoption/`)
- Context Activation package tooling (`tools/activation/`)
- Context Health & Learning tooling (`tools/health/`)
- Organizational Memory continuity tooling (`tools/memory/`)
- Organizational Memory retention-governance, read-only policy resolution, and
  policy-before-exposure Retrieval tooling
- Immutable Context Version capture planning and historical verification
- Governed Contextual Assessment tooling (`tools/reasoning/`)
- Runtime CLI tooling (`tools/cli/`, `contextos`)

---

## Current product and users

Context OS is an Organizational Context Runtime, currently a **design-partner
alpha** with developer access. The [current product definition](../docs/5.x_strategy/5.6_COS_Current_Product_Definition.md)
owns user/organization fit, capability limits, experience boundaries and value
gates. The [post-v1 roadmap](P.2_Product_Roadmap.md#post-v1-productization-roadmap)
owns progression. Architecture and the historical v1.0 release do not establish
independent self-service adoption.

## Core User Journeys (High-Level)

1. Technical operator chooses a bounded need and authorized local source scope.
2. Existing organizations map current canon with a governed External Adoption
   Profile; native projects may choose templates and create-only bootstrap.
3. Operator assesses context and interprets applicable findings and unknowns.
4. Actor obtains a checked working brief with sources, gaps and action bounds.
5. Human/agent performs separately authorized work and records additional
   retrieval, actual use, outcome and human intervention.
6. Operator reviews Health, policy-authorized Memory and advisory Reasoning,
   rechecking materially changed context before consequential reuse.
7. Contributor proposes changes; maintainers review diffs, evidence and
   publication authority before merging.

Discovery, Construction, Builder, Context Version capture, Mission-use
production and Work Ownership currently require Python APIs and explicit
inputs. Work Ownership is not an automatic CLI guard. These capabilities
support the journey but remain advanced developer/operator surfaces.

---

## Key Capabilities

- Provide a minimal, coherent MOM definition
- Provide stable taxonomy + naming conventions
- Provide templates that map to taxonomy
- Provide examples demonstrating minimal vs strict compliance
- Provide validator, CLI, and readiness contracts with scoped runtime tooling
- Provide read-only bootstrap planning as the first Guided Bootstrap surface
- Provide read-only bootstrap proposal generation as the preserved bridge from
  plan to apply approval
- Provide read-only bootstrap approval record drafts before apply
- Provide explicit read-only bootstrap approval acceptance before apply
- Provide read-only apply preflight before apply
- Provide governed create-only bootstrap apply with explicit preflight-bound
  confirmation
- Define proposal-approved apply as the only write-capable Guided
  Bootstrap path
- Provide read-only Activation Packages that make canonical context consumable
  without creating a parallel SSOT
- Provide a read-only `contextos activate` surface for generating and checking
  mission-bound working context packages
- Provide package-backed Activation Handoffs for humans, Codex, Claude Code,
  IDE assistants, and future consumers
- Provide Activation Handoff checks so a saved handoff can govern work only
  while its package binding, selected sources, and Validator gate remain valid
- Provide a single Mission Context model that separates Governing Context from
  bounded Execution Context without creating a second SSOT or package family
- Provide a read-only Context Health Report that exposes evidence, unknowns,
  and non-canonical update candidates without an opaque score
- Provide Mission-use evidence that binds context participation to an exact
  Activation Package, Handoff, Mission, and consumer
- Resolve whether an explicit need is already owned by materially current work
  before recommending parallel Goal or Mission qualification
- Provide a read-only human and machine Health CLI without remediation or
  canonical mutation
- Provide a read-only Memory Continuity report with source hashes, temporal
  unknowns, explicit supersession, explainable prior art, and non-canonical
  pattern candidates
- Define retention state independently from truth, sensitivity, access,
  retrieval eligibility, and Activation eligibility
- Block unresolved preservation-versus-deletion duties for accountable human
  governance instead of inventing legal precedence
- Provide deterministic, metadata-safe read-only retention resolution with
  policy/source drift invalidation and no implicit permission
- Provide bounded human and machine Memory retrieval with exact Activation and
  Continuity bindings, selection rationale, exclusions, and invalidation checks
- Apply Retention Resolution before exposing relevant memory, preserving
  independent normal, elevated, excluded, prohibited, unknown, visibility, and
  Activation outcomes
- Provide deterministic read-only Context Version planning, capture, and checks
  with content-free source manifests, optional implementation evidence, and
  explicit historical gaps
- Bind Memory Continuity and policy-aware Retrieval to exact Context Versions
  while preserving partial/unknown history and independently governing version
  metadata exposure
- Provide a read-only Contextual Assessment that composes Activation, Health,
  authorized Memory, and Context Version evidence while preserving reasoning,
  Decision, authority, and truth boundaries
- Provide `contextos reason` human/JSON output and exact saved-Assessment
  validation without adding Decision, execution, or mutation authority

---

## Primary User Roles

- Technical adopter/operator (maps existing canon or chooses native formation with assistance)
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
- Context-layer risk if bounded execution retrieval becomes broad search or a
  second context system
- Health risk if narrative evidence is mistaken for measured usefulness or if
  update candidates bypass governed Construction
- Memory risk if storage, retrieval, GraphRAG, or historical summaries become a
  second SSOT or drop authority, temporal, supersession, and retention context
- Context Version risk if Git history, Activation Packages, or retrospective
  narratives are mistaken for universal or complete historical context
- Historical Retrieval risk if version lineage leaks restricted source metadata
  or if supersession is presented as semantic invalidity
- Reasoning risk if interpretation, hypothesis, or recommendation is mistaken
  for evidence, Decision authority, or canonical organizational truth
- Saved-reasoning risk if a prior Assessment is reused after source, policy,
  authority, evidence, or temporal drift without an exact check

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

- 2026-09-06 - v0.1.3 - Reconciled current adoption journeys, technical assistance, API surfaces and implemented bootstrap wording.

- 2026-08-11 — v0.1.1 — Added readiness/bootstrap planning surfaces and GENESIS alignment
- 2026-08-11 — v0.1.1 — Added Context Activation Package surface
- 2026-08-11 — v0.1.1 — Added Activation Package CLI and package check surface
- 2026-08-11 — v0.1.1 — Added package-backed Activation Handoff surface
- 2026-08-11 — v0.1.1 — Added Activation Handoff check surface
- 2026-08-11 — v0.1.1 — Added Mission Context layer model
- 2026-08-15 — v0.1.1 — Added Context Health & Learning report surface
- 2026-08-16 — v0.1.1 — Added structured Mission-use evidence surface
- 2026-08-20 — v0.1.1 — Added the read-only Context Health CLI surface
- 2026-08-20 — v0.1.1 — Added the canonical AI-native organization theory and
  the governed Organizational Memory journey boundary
- 2026-08-21 — v0.1.1 — Added the first read-only Organizational Memory
  continuity report capability
- 2026-08-21 — v0.1.1 — Added the bounded Organizational Memory retrieval and
  saved-result check surface
- 2026-08-23 — v0.1.1 — Integrated retention eligibility before Memory
  exposure and added metadata-safe policy outcomes to the public surface
- 2026-08-23 — v0.1.1 — Added immutable Context Version capture/checks and
  explicit historical continuity-gap handling
- 2026-08-23 — v0.1.1 — Integrated exact Context Version evidence into Memory
  Continuity and policy-aware Retrieval without semantic comparison
- 2026-08-24 — v0.1.1 — Added the first read-only governed Contextual
  Assessment product capability
- 2026-08-24 — v0.1.1 — Added the `contextos reason` human/machine surface and
  saved-Assessment check
- 2026-09-05 — v0.1.2 — Added ownership-aware work qualification before
  parallel Goal or Mission recommendations
- 2026-08-11 — v0.1.1 — Added Guided Bootstrap apply approval boundary
- 2026-08-11 — v0.1.1 — Added Bootstrap Proposal Engine product capability
- 2026-08-11 — v0.1.1 — Added Bootstrap Proposal Review Surface to product
  journey
- 2026-08-11 — v0.1.1 — Added Bootstrap Approval Record Draft to product
  journey
- 2026-02-19 — v0.1.0 — Initial creation
