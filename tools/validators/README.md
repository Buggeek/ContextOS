# Context OS Validator Engine v0

This folder contains the first implementation of the Context OS Validator
Engine for EPIC-007.

The implementation is intentionally small:

- stdlib-only Python 3
- read-only repository inspection
- no full Runtime CLI
- no external connectors
- no automatic fixes

The Runtime CLI wraps this surface as `contextos validate`.

External targets may pass `--adoption-profile <contextos.adoption.profile/1>`.
Profile-aware reports preserve stable rule IDs while distinguishing `passed`,
`violated`, `mapped_equivalent`, `not_applicable`, and `unknown`; skipped native
rules retain rationale and equivalent-control evidence.

---

## Commands

Run the validator from the repository root:

```bash
python3 tools/validators/contextos_validator.py --root . --mode full --format human
python3 tools/validators/contextos_validator.py --root . --mode gate --format json
```

Run tests:

```bash
python3 tools/validators/test_contextos_validator.py
```

Write a machine report while rendering a human report:

```bash
python3 tools/validators/contextos_validator.py \
  --root . \
  --mode full \
  --format human \
  --json-out /tmp/contextos-validator-report.json
```

---

## Architecture

The validator is split into a reusable Runtime component and a thin CLI
wrapper:

```text
tools/validators/
├── engine/
│   ├── validator_engine.py
│   ├── rule_registry.py
│   ├── report_builder.py
│   ├── findings.py
│   └── selectors.py
├── rules/
│   ├── structure.py
│   ├── naming.py
│   ├── links.py
│   ├── taxonomy.py
│   ├── mom.py
│   ├── ownership.py
│   ├── governance.py
│   ├── authority.py
│   ├── hypothesis.py
│   └── drift.py
├── contextos_validator.py
└── test_contextos_validator.py
```

Future Runtime callers can use the engine directly:

```python
from engine.validator_engine import ValidatorEngine

engine = ValidatorEngine(".")
report = engine.run(mode="gate")
```

---

## Modes

| Mode | Use |
|---|---|
| `install-check` | Scaffolding and install readiness checks |
| `pre-bootstrap` | Pre-bootstrap SSOT/governance checks |
| `full` | Full v0 repository validation |
| `gate` | Blocking gate for `error` and `fatal` findings |

In v0, `gate` reports warnings but exits non-zero only for blocking
`error`/`fatal` findings. This keeps the current dogfooding repository
gateable while non-blocking drift remains visible.

---

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | No blocking findings |
| `7` | One or more `error` findings |
| `8` | One or more `fatal` findings |
| `9` | Validator misconfiguration |

---

## Rule Selection

Use `--rules` with comma-separated selectors:

```bash
python3 tools/validators/contextos_validator.py --root . --rules links.*,mom.*
python3 tools/validators/contextos_validator.py --root . --rules all,-ownership.framework_owner_present
```

Supported selector forms:

- `all`
- `category`
- `category.*`
- `category.rule`
- `-category.rule` or `-category.*` to exclude

Unknown selectors return exit code `9`.

---

## Machine Report

The JSON report uses schema `contextos.validator.report/1`:

```json
{
  "schema": "contextos.validator.report/1",
  "generated_at": "2026-06-02T00:00:00Z",
  "mode": "full",
  "root": "/absolute/repo/path",
  "summary": {
    "rules_run": 23,
    "info": 0,
    "warn": 0,
    "error": 0,
    "fatal": 0,
    "exit_code": 0
  },
  "findings": []
}
```

Finding IDs are deterministic SHA-256-derived IDs based on rule, severity,
location, message, anchor, and evidence. `generated_at` is run metadata and is
expected to change between invocations.

---

## Stable Rule IDs

| Rule ID | Severity | Modes | Description |
|---|---|---|---|
| `structure.required_roots` | error | install-check, pre-bootstrap, full, gate | Requires `docs/`, `SSOT/`, `ops/`, and `templates/` roots |
| `structure.runtime_manifest` | warn/error | install-check, pre-bootstrap, full, gate | Reports missing `.contextos/manifest.yaml`; blocking only in `install-check` |
| `structure.tracked_junk_absent` | error | install-check, pre-bootstrap, full, gate | Fails tracked OS/editor junk files |
| `structure.markdown_h1_present` | error/warn | full, gate | Requires Markdown H1 headings; SSOT is blocking |
| `structure.legacy_paths` | warn | full, gate | Detects legacy paths and identifiers, with explicit allowlists |
| `naming.contextos_convention` | warn | full, gate | Detects suspicious `Context OS` naming convention drift |
| `naming.doctrine_terms` | error | full, gate | Blocks legacy `Agent Operating Model` prose outside explicit historical references |
| `links.relative_paths_resolve` | error | full, gate | Blocks broken internal relative Markdown links |
| `links.anchors_resolve` | error | full, gate | Blocks links to missing Markdown heading anchors |
| `links.heading_anchor_unique` | warn | full | Reports duplicate heading anchor bases |
| `taxonomy.ssot_filename_prefix` | error | pre-bootstrap, full, gate | Requires known SSOT taxonomy filename prefixes |
| `taxonomy.ssot_h1_matches_file` | error | full, gate | Requires SSOT H1 to start with the artifact ID |
| `taxonomy.docs_folder_prefix` | warn | full | Reports docs whose filename prefix does not match the taxonomy folder |
| `mom.required_artifacts` | error | pre-bootstrap, full, gate | Requires MOM artifacts in each SSOT tree |
| `mom.required_fields` | error/warn | full, gate | Blocks missing SSOT `Version`/`Owner`; warns on strict-profile date/change-log drift |
| `mom.epic_required_sections` | error | full, gate | Requires the 13 epic readiness sections/metadata from the Codex checklist |
| `ownership.ssot_owner_present` | error | pre-bootstrap, full, gate | Blocks missing or placeholder SSOT owners |
| `ownership.framework_owner_present` | warn | full | Reports framework artifacts without explicit owners |
| `governance.dor_dod_present` | error | pre-bootstrap, full, gate | Requires `G.1` and `G.2` in each SSOT tree |
| `governance.agent_rules_present` | error | install-check, pre-bootstrap, full, gate | Requires `ops/AGENT_RULES.md` |
| `authority.model_present` | error | pre-bootstrap, full, gate | Requires the Human-Agent Authority Model and L0-L5 declarations |
| `hypothesis.product_status_fields` | warn | full | Reports missing product artifact status and explicit hypothesis criteria |
| `drift.discovery_bundle_available` | info/error | full, gate | Skips drift if no Discovery bundle is supplied; blocks unreadable supplied paths |

---

## Legacy Reference Allowlist

`structure.legacy_paths` supports explicit allowlists for historical and
forbidden-list references. The v0 built-in allowlist includes:

- `docs/3.x_mom/README.md`
- `docs/3.x_mom/Minimum_Operational_Map.md`
- `SSOT/E.1_User_Story_US-001_Structure_Canonical_Paths.md`
- `SSOT/P.5_Epic_Structural_Integrity.md`
- `SSOT/epics/EPIC-001_Structural_Integrity.md`

It also suppresses lines that clearly describe historical, legacy, forbidden,
or explicit rename contexts.

---

## v0 Limits

- Markdown parsing uses a compact regex scanner, not a full Markdown AST.
- Framework ownership is warning-only.
- Strict-profile `Last Updated` and `Change Log` drift is warning-only for
  the current dogfooding repository.
- Discovery drift is only checked for bundle presence in v0.
- Runtime event emission is represented by the report itself; no event bus
  exists yet.
