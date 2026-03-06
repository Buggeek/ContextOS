# Validators

This folder defines **validator specifications** for Context OS repositories.

No validator code is implemented yet.

---

## Scope (v0)

Validators apply to two different targets:

1. **SSOT trees** (primary):
	- Any `SSOT/` folder in the repository root.
	- Example SSOT trees under `examples/**/SSOT/`.

2. **Framework docs** (secondary, light-touch):
	- Files under `docs/`, `templates/`, and `examples/`.
	- Only **hygiene + link integrity** checks apply here (no taxonomy enforcement).

---

## Compliance Profiles

SSOT validation supports the compliance profiles defined in the taxonomy:

- `minimal`
- `strict`

The profile must be declared by the SSOT implementation (recommended location: `SSOT/README.md`), or inferred by convention in examples.

---

## Planned Checks (v0)

### A) Repo Hygiene (repo-wide)

- No OS/editor junk files tracked (e.g. `.DS_Store`).

### B) Internal Link Integrity (framework + SSOT)

- No broken relative links in Markdown files.
- Links must be repository-relative or relative to the current file.

### C) SSOT Taxonomy Conformance (SSOT only)

For each SSOT document:

- File name matches a known taxonomy prefix (`S.*`, `P.*`, `A.*`, `G.*`, `O.*`, `E.*`, `F.*`, etc.).
- Document includes a **Version**.
- Document includes an **Owner**.

For `strict` SSOT:

- Document includes `Last Updated`.
- Document includes a `Change Log` section with at least one entry.
- Document includes `Dependencies` and/or `Linked Artifacts` where applicable.

---

## Definition of Pass/Fail

- **Fail**: Any broken links, missing required header fields, unknown doc prefixes in SSOT, or tracked hygiene files.
- **Pass**: All required checks satisfied for the chosen compliance profile.

---

## Non-Goals (v0)

- Enforcing taxonomy rules on framework docs under `docs/`.
- Enforcing perfect completeness of content.
- Automatic rewriting of documents (validators should report diffs/suggestions).
