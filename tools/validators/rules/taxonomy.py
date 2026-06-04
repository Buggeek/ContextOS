from __future__ import annotations

import re

from engine.findings import DOC_FOLDER_PREFIXES, TAXONOMY_PREFIXES, ValidationContext, first_heading, is_ssot_doc, make_finding, normalize_rel, ssot_tree_roots


def ssot_artifact_id(filename: str) -> str | None:
    if filename == "README.md":
        return None
    if re.match(r"^EPIC-\d{3}_.+\.md$", filename):
        return filename.split("_", 1)[0]
    match = re.match(r"^([A-Z])\.(\d+)_.*\.md$", filename)
    if match and match.group(1) in TAXONOMY_PREFIXES:
        return f"{match.group(1)}.{match.group(2)}"
    return None


def ssot_filename_prefix(ctx: ValidationContext) -> list:
    findings = []
    for tree in ssot_tree_roots(ctx.root):
        for path in sorted(tree.rglob("*.md")):
            rel = normalize_rel(path.relative_to(ctx.root))
            if path.name == "README.md":
                continue
            if path.parent.name == "epics" and re.match(r"^EPIC-\d{3}_.+\.md$", path.name):
                continue
            if ssot_artifact_id(path.name) is None:
                findings.append(
                    make_finding(
                        "taxonomy.ssot_filename_prefix",
                        "error",
                        "SSOT Markdown filename does not match a known taxonomy prefix.",
                        rel,
                        evidence={"known_prefixes": sorted(TAXONOMY_PREFIXES)},
                        suggested_fix="Rename the artifact to use a known taxonomy prefix.",
                    )
                )
    return findings


def ssot_h1_matches_file(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        if not is_ssot_doc(doc) or doc.path.name == "README.md":
            continue
        artifact_id = ssot_artifact_id(doc.path.name)
        if artifact_id is None:
            continue
        first = first_heading(doc)
        if first is None:
            continue
        line_no, title, _anchor = first
        normalized = title.replace("—", "-").strip()
        if not normalized.startswith(artifact_id):
            findings.append(
                make_finding(
                    "taxonomy.ssot_h1_matches_file",
                    "error",
                    "SSOT H1 does not start with the artifact ID from the filename.",
                    doc.rel_path,
                    line_no,
                    evidence={"artifact_id": artifact_id, "h1": title},
                    suggested_fix=f"Start the H1 with '{artifact_id}'.",
                )
            )
    return findings


def docs_folder_prefix(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        if not doc.rel_path.startswith("docs/"):
            continue
        parts = doc.rel_path.split("/")
        if len(parts) < 3:
            continue
        folder = parts[1]
        expected = DOC_FOLDER_PREFIXES.get(folder)
        if expected is None:
            continue
        name = parts[-1]
        if name in {"README.md"}:
            continue
        if folder == "3.x_operation" and parts[-2] in {"roles"}:
            continue
        if not name.startswith(expected):
            findings.append(
                make_finding(
                    "taxonomy.docs_folder_prefix",
                    "warn",
                    "Documentation filename does not match its taxonomy folder prefix.",
                    doc.rel_path,
                    evidence={"folder": folder, "expected_prefix": expected},
                    suggested_fix="Rename the file or document the exception in taxonomy.",
                )
            )
    return findings
