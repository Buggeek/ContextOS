from __future__ import annotations

import re

from engine.findings import MarkdownDocument, ValidationContext, has_field, is_ssot_doc, make_finding


def is_product_artifact(doc: MarkdownDocument) -> bool:
    name = doc.path.name
    if name.startswith("P."):
        return True
    if "/epics/EPIC-" in doc.rel_path:
        return True
    return False


def product_status_fields(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        if not is_ssot_doc(doc) or not is_product_artifact(doc) or doc.path.name == "README.md":
            continue
        if not has_field(doc, "Status"):
            findings.append(
                make_finding(
                    "hypothesis.product_status_fields",
                    "warn",
                    "Product artifact does not declare a Status field.",
                    doc.rel_path,
                    1,
                    suggested_fix="Add a Status field when product artifacts move under hypothesis/verified tagging.",
                )
            )
        text_lower = doc.text.lower()
        explicit_hypothesis = re.search(r"\bstatus\s*:\s*hypothesis\b", text_lower) or "belief state: hypothesis" in text_lower
        if explicit_hypothesis:
            if "success criterion" not in text_lower and "success criteria" not in text_lower:
                findings.append(
                    make_finding(
                        "hypothesis.product_status_fields",
                        "warn",
                        "Hypothesis product artifact does not declare a success criterion.",
                        doc.rel_path,
                        evidence={"missing": "success criterion"},
                    )
                )
            if "kill criterion" not in text_lower:
                findings.append(
                    make_finding(
                        "hypothesis.product_status_fields",
                        "warn",
                        "Hypothesis product artifact does not declare a kill criterion.",
                        doc.rel_path,
                        evidence={"missing": "kill criterion"},
                    )
                )
    return findings
