from __future__ import annotations

from engine.findings import (
    EPIC_REQUIRED_METADATA,
    EPIC_REQUIRED_SECTIONS,
    MOM_REQUIRED,
    ValidationContext,
    has_field,
    has_heading,
    is_ssot_doc,
    make_finding,
    normalize_rel,
    ssot_doc_profile,
    ssot_tree_roots,
)


def required_artifacts(ctx: ValidationContext) -> list:
    findings = []
    for tree in ssot_tree_roots(ctx.root):
        tree_rel = normalize_rel(tree.relative_to(ctx.root))
        for filename in MOM_REQUIRED:
            if not (tree / filename).exists():
                findings.append(
                    make_finding(
                        "mom.required_artifacts",
                        "error",
                        "MOM required artifact is missing from this SSOT tree.",
                        f"{tree_rel}/{filename}",
                        evidence={"ssot_tree": tree_rel, "required": filename},
                        suggested_fix="Create the missing MOM artifact from its template.",
                    )
                )
    return findings


def required_fields(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        if not is_ssot_doc(doc) or doc.path.name == "README.md":
            continue
        profile = ssot_doc_profile(ctx, doc)
        required = ["Version", "Owner"]
        for field_name in required:
            if has_field(doc, field_name):
                continue
            findings.append(
                make_finding(
                    "mom.required_fields",
                    "error",
                    f"SSOT artifact is missing required field '{field_name}'.",
                    doc.rel_path,
                    1,
                    evidence={"profile": profile, "field": field_name},
                    suggested_fix=f"Add a populated '{field_name}:' field near the top of the artifact.",
                )
            )
        if profile == "strict" and not has_field(doc, "Last Updated"):
            findings.append(
                make_finding(
                    "mom.required_fields",
                    "warn",
                    "Strict SSOT artifact is missing recommended field 'Last Updated'.",
                    doc.rel_path,
                    1,
                    evidence={"profile": profile, "field": "Last Updated"},
                    suggested_fix="Add a populated 'Last Updated:' field near the top of the artifact.",
                )
            )
        if profile == "strict" and not has_heading(doc, "Change Log"):
            findings.append(
                make_finding(
                    "mom.required_fields",
                    "warn",
                    "Strict SSOT artifact is missing a Change Log section.",
                    doc.rel_path,
                    evidence={"profile": profile, "field": "Change Log"},
                    suggested_fix="Add a Change Log section with at least one entry.",
                )
            )
    return findings


def epic_required_sections(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        if "/epics/EPIC-" not in doc.rel_path:
            continue
        for field_name in EPIC_REQUIRED_METADATA:
            if not has_field(doc, field_name):
                findings.append(
                    make_finding(
                        "mom.epic_required_sections",
                        "error",
                        f"Epic artifact is missing required metadata '{field_name}'.",
                        doc.rel_path,
                        1,
                        evidence={"field": field_name},
                        suggested_fix=f"Add '- **{field_name}:** <value>' metadata near the top.",
                    )
                )
        for title in EPIC_REQUIRED_SECTIONS:
            if not has_heading(doc, title):
                findings.append(
                    make_finding(
                        "mom.epic_required_sections",
                        "error",
                        f"Epic artifact is missing required section '{title}'.",
                        doc.rel_path,
                        evidence={"section": title},
                        suggested_fix=f"Add a '## {title}' section.",
                    )
                )
    return findings
