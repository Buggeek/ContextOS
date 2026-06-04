from __future__ import annotations

import re

from engine.findings import FRAMEWORK_OWNER_ALLOWLIST, ValidationContext, find_field_line, has_field, is_framework_doc, is_ssot_doc, make_finding


def ssot_owner_present(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        if not is_ssot_doc(doc) or doc.path.name == "README.md":
            continue
        line_no = find_field_line(doc, "Owner")
        if line_no is None:
            findings.append(
                make_finding(
                    "ownership.ssot_owner_present",
                    "error",
                    "SSOT artifact does not declare an owner.",
                    doc.rel_path,
                    1,
                    suggested_fix="Add a populated 'Owner:' field.",
                )
            )
            continue
        line = doc.lines[line_no - 1]
        if re.search(r"Owner(?:\*\*)?\s*:\s*(?:$|<|TBD|TODO|Unknown)", line, re.IGNORECASE):
            findings.append(
                make_finding(
                    "ownership.ssot_owner_present",
                    "error",
                    "SSOT artifact owner is not populated.",
                    doc.rel_path,
                    line_no,
                    suggested_fix="Replace the placeholder with an accountable role or person.",
                )
            )
    return findings


def framework_owner_present(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        if not is_framework_doc(doc):
            continue
        if doc.rel_path in FRAMEWORK_OWNER_ALLOWLIST:
            continue
        if has_field(doc, "Owner"):
            continue
        findings.append(
            make_finding(
                "ownership.framework_owner_present",
                "warn",
                "Framework artifact does not declare an explicit owner.",
                doc.rel_path,
                1,
                suggested_fix="Add ownership metadata when this artifact moves under strict governance.",
            )
        )
    return findings
