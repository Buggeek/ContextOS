# Context OS Agent Rules

## Purpose
This document defines how automated agents (and humans using agent tooling) can contribute safely to Context OS.

Goals:
- Keep changes small, reviewable, and reversible.
- Preserve the meaning of existing documents.
- Maintain link integrity, taxonomy consistency, and versioning hygiene.

Non-goals:
- Introducing new frameworks, principles, or long-form strategy docs.
- Rewriting existing content for style or tone.

---

## Scope
These rules apply to any change proposed by an agent in this repository.

Special protection:
- `/docs/**`, `/templates/**`, `/examples/**`
  - No rewrites or rephrasing.
  - Only tiny formatting fixes when strictly required (e.g., broken markdown rendering).

---

## Working Method (Required)

### 1) Diff-based edits
- Prefer minimal, line-scoped diffs.
- Avoid wholesale reformatting, reorganizing headings, or changing wording.

### 2) Small PRs
- One coherent intent per PR.
- Prefer a single topic and a short changelog-style description.

### 3) No orphan docs
A doc is "orphaned" if it is added/renamed without being reachable from the taxonomy or without an explicit home.
- New docs must be placed under an existing taxonomy area.
- If a doc can’t be mapped to the taxonomy, don’t add it.

### 4) Taxonomy mapping
- Any new or moved documentation must map to the existing document taxonomy (see `/docs/2.x_taxonomy/`).
- Use the closest existing category; do not invent new categories.

### 5) DoR / DoD alignment
All proposed work should meet the intent of:
- `templates/governance/G.1_Definition_of_Ready.template.md`
- `templates/governance/G.2_Definition_of_Done.template.md`

Practical minimum for docs/meta changes:
- Clear objective and scope.
- Testable “acceptance criteria” (what changed and why).
- Impacted files listed.
- Validation plan (at least: link check + render sanity check).

### 6) Link integrity
- Update or remove links if paths change.
- Prefer relative links within the repo.
- Do not introduce broken links.

### 7) Version headers + change logs (when applicable)
If a document has a version header and/or change log section:
- Keep the format consistent.
- Update the version and/or change log when the change is meaningfully content-affecting.

---

## Allowed Actions
Agents MAY:
- Add minimal governance/ops guardrails (markdown/yaml/plaintext only).
- Add or refine contributor workflow scaffolding (e.g., PR templates).
- Fix broken internal links (without altering intent).
- Apply tiny formatting fixes that are strictly required for correct rendering.
- Add placeholders that clearly state they are placeholders (no implied commitments).

---

## Forbidden Actions
Agents MUST NOT:
- Rewrite, rephrase, or “improve” the narrative of documents in `/docs`, `/templates`, or `/examples`.
- Introduce new framework documents (new thesis/principles/architecture treatises) or expand scope beyond the request.
- Rename/move large doc trees without an explicit migration plan.
- Add new file types beyond markdown/yaml/plaintext.
- Add generated assets, binaries, screenshots, or large media.
- Change meaning via “small” edits (e.g., redefining terms, acceptance criteria, principles).
- Merge to `main` without required human review gates.

---

## Review Gates (Human Approval Required)
The following require explicit human approval before merge:
- Any change touching `/docs/**`, `/templates/**`, or `/examples/**`.
- Any taxonomy change or new doc addition.
- Any change that modifies definitions, policies, or governance criteria.
- Any change that affects repository-wide workflows (CI, release process, branching).

At review time, the human reviewer should confirm:
- The change is minimal and aligned to the stated goal.
- Links render and resolve.
- The PR scope is coherent and not a disguised rewrite.
- Version headers / change logs are updated when required.

---

## Expected PR Hygiene
A PR created by an agent should include:
- Summary of intent.
- Type of change.
- Acceptance criteria (what changed and why).
- Explicit list of impacted files.
- Validation notes (e.g., “checked links”, “rendered markdown”).

If any rule above cannot be met, stop and request human direction instead of guessing.
