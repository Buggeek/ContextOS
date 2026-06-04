from __future__ import annotations

from pathlib import Path

from engine.findings import (
    CHECK_ROOTS,
    LEGACY_ALLOWLIST,
    LEGACY_PATH_TERMS,
    LEGACY_REFERENCE_ALLOWLIST_PATTERNS,
    REPO_JUNK_FILENAMES,
    MarkdownDocument,
    ValidationContext,
    first_heading,
    is_ssot_doc,
    make_finding,
    normalize_rel,
)


def required_roots(ctx: ValidationContext) -> list:
    findings = []
    for rel in CHECK_ROOTS:
        if not (ctx.root / rel).is_dir():
            findings.append(
                make_finding(
                    "structure.required_roots",
                    "error",
                    f"Required repository root '{rel}/' is missing.",
                    rel,
                    suggested_fix=f"Create the '{rel}/' directory or run Context OS initialization.",
                )
            )
    return findings


def runtime_manifest(ctx: ValidationContext) -> list:
    manifest = ctx.manifest or (ctx.root / ".contextos" / "manifest.yaml")
    if manifest.exists():
        return []
    severity = "warn"
    if ctx.mode == "install-check":
        severity = "error"
    return [
        make_finding(
            "structure.runtime_manifest",
            severity,
            "Runtime manifest is not present.",
            normalize_rel(manifest.relative_to(ctx.root)) if manifest.is_relative_to(ctx.root) else str(manifest),
            evidence={"default_manifest": ".contextos/manifest.yaml"},
            suggested_fix="Create the Runtime manifest during EPIC-008 CLI initialization.",
        )
    ]


def tracked_junk_absent(ctx: ValidationContext) -> list:
    if ctx.tracked_files is None:
        return [
            make_finding(
                "structure.tracked_junk_absent",
                "warn",
                "Could not inspect git tracked files; skipping tracked junk check.",
                evidence={"command": "git ls-files"},
            )
        ]
    findings = []
    for rel in sorted(ctx.tracked_files):
        if Path(rel).name in REPO_JUNK_FILENAMES:
            findings.append(
                make_finding(
                    "structure.tracked_junk_absent",
                    "error",
                    f"Tracked junk file '{Path(rel).name}' is present.",
                    rel,
                    suggested_fix="Remove this file from version control.",
                )
            )
    return findings


def markdown_h1_present(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        if first_heading(doc):
            continue
        severity = "error" if is_ssot_doc(doc) else "warn"
        findings.append(
            make_finding(
                "structure.markdown_h1_present",
                severity,
                "Markdown file does not declare an H1 heading.",
                doc.rel_path,
                1,
                suggested_fix="Add a single top-level H1 heading.",
            )
        )
    return findings


def legacy_reference_is_allowed(doc: MarkdownDocument, term: str, line: str) -> bool:
    if doc.rel_path in LEGACY_ALLOWLIST:
        return True
    lowered = line.lower()
    if any(pattern in lowered for pattern in LEGACY_REFERENCE_ALLOWLIST_PATTERNS):
        return True
    if term == "3.x_mom" and "docs/3.x_mom" in line:
        return False
    return False


def legacy_paths(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        for index, line in enumerate(doc.lines, start=1):
            for term in LEGACY_PATH_TERMS:
                if term not in line:
                    continue
                if legacy_reference_is_allowed(doc, term, line):
                    continue
                findings.append(
                    make_finding(
                        "structure.legacy_paths",
                        "warn",
                        f"Legacy path or identifier reference '{term}' is present.",
                        doc.rel_path,
                        index,
                        evidence={"term": term},
                        suggested_fix="Use the canonical path or document the reference in the validator allowlist.",
                    )
                )
    return findings
