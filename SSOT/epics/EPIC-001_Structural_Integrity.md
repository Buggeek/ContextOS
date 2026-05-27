# EPIC-001 — Structural Integrity

- **Epic ID:** EPIC-001
- **Version:** v0.2 — Framework Hardening
- **Status:** Active
- **Owner:** Context OS Maintainers

---

## Objective

Establish and maintain a structurally coherent repository so that humans and
agents can navigate, validate, and extend Context OS without ambiguity.

---

## Problem

Early drafts of Context OS accumulated parallel naming schemes, duplicated
operation docs, orphaned folders, and broken cross-references. Without a
canonical structure, adoption is unreliable and downstream tooling
(validator, CLI, Runtime) cannot be built on a stable substrate.

---

## Scope

- Canonical folder layout under `docs/` (foundations → strategy).
- Canonical filename and prefix conventions (numeric prefixes for framework
  docs; role docs unprefixed under `roles/`).
- Single source per doctrine (one Agentic Operating Model, one Runtime
  Architecture, one Product Roadmap per audience).
- Cross-reference hygiene (no broken links, no stale paths).
- Naming convention enforcement: `Context OS` in prose, `ContextOS` only for
  repo/package/machine identifiers, `contextos` for CLI examples.

---

## Out of Scope

- Validator implementation (EPIC-007).
- Runtime CLI (EPIC-008).
- New conceptual frameworks or doctrines.
- Re-styling existing prose for tone.

---

## Expected Outcomes

- A single canonical tree under `docs/3.x_operation/` (3.1 AOM, 3.2 agent
  system, 3.3 execution primitives).
- A single roadmap surface: narrative in `docs/5.x_strategy/5.4_*` and
  execution in `SSOT/P.2_Product_Roadmap.md`.
- Zero broken internal links in committed documentation.
- Zero stale path references to removed folders (`3.1_agents`,
  `3.2_toolbox`, `3.3_skillbox`, legacy `P.1_Product_Roadmap`).
- Naming convention applied repo-wide across `docs/`, `SSOT/`, and `ops/`.

---

## Dependencies

- [`../A.1_System_Map.md`](../A.1_System_Map.md)
- [`../../docs/2.x_taxonomy/2.0_COS_Document_Taxonomy.md`](../../docs/2.x_taxonomy/2.0_COS_Document_Taxonomy.md)
- [`../G.1_Definition_of_Ready.md`](../G.1_Definition_of_Ready.md)
- [`../G.2_Definition_of_Done.md`](../G.2_Definition_of_Done.md)

---

## Success Criteria

- `git status` is clean after each structural change.
- `find docs -name "*.md"` matches the documented canonical layout.
- Grep checks return zero matches for legacy paths and legacy doctrine terms
  (`Agent Operating Model` outside of `Agentic Operating Model`).
- Every renumbered doc has its H1 prefix aligned with its filename prefix.
- All affected references are updated in the same commit as the structural
  change.

---

## Definition of Ready (DoR)

- Migration matrix exists and lists every old→new path.
- Scope is bounded to structure, naming, and references.
- No conceptual changes are proposed.
- Reversal path is git-based (single revert).

---

## Definition of Done (DoD)

- Canonical layout committed.
- All cross-references updated.
- Verification grep + tree outputs included in the commit description or
  associated report.
- SSOT taxonomy notes updated when SSOT-local conventions diverge from the
  framework taxonomy.
- No regressions in previously canonicalized areas.

---

## Related Artifacts

- [`../P.5_Epic_Structural_Integrity.md`](../P.5_Epic_Structural_Integrity.md) — original P.5 form (superseded by this epic file).
- [`../E.1_User_Story_US-001_Structure_Canonical_Paths.md`](../E.1_User_Story_US-001_Structure_Canonical_Paths.md) — first user story under this epic.
- Commits `1862940` (Phase 1) and `481eb88` (Phase 2) are evidence of work
  delivered under this epic.
