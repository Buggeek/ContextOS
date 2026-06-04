from __future__ import annotations

import re

from engine.findings import ValidationContext, line_for_offset, make_finding


def contextos_convention(ctx: ValidationContext) -> list:
    findings = []
    pattern = re.compile(r"\b(ContextOS|Contextos|context OS|Context os)\b")
    for doc in ctx.markdown_docs:
        for match in pattern.finditer(doc.text):
            token = match.group(1)
            line_no = line_for_offset(doc.text, match.start())
            line = doc.lines[line_no - 1]
            if token == "ContextOS":
                if "`ContextOS`" in line or "contextos.validator" in line or "contextos." in line:
                    continue
                if re.search(r"(identifier|repo|package|machine|schema|namespace)", line, flags=re.IGNORECASE):
                    continue
            findings.append(
                make_finding(
                    "naming.contextos_convention",
                    "warn",
                    f"Suspicious Context OS naming form '{token}'.",
                    doc.rel_path,
                    line_no,
                    evidence={"token": token},
                    suggested_fix="Use 'Context OS' in prose, 'ContextOS' for identifiers, and 'contextos' for CLI/schema forms.",
                )
            )
    return findings


def doctrine_terms(ctx: ValidationContext) -> list:
    findings = []
    bad = "Agent Operating Model"
    good = "Agentic Operating Model"
    allowed_context = ("explicit rename", "explicit renames", "no remaining", "legacy", "forbidden")
    for doc in ctx.markdown_docs:
        for match in re.finditer(re.escape(bad), doc.text):
            line_no = line_for_offset(doc.text, match.start())
            line = doc.lines[line_no - 1]
            if good in line:
                continue
            if any(term in line.lower() for term in allowed_context):
                continue
            findings.append(
                make_finding(
                    "naming.doctrine_terms",
                    "error",
                    f"Legacy doctrine term '{bad}' is present.",
                    doc.rel_path,
                    line_no,
                    evidence={"term": bad},
                    suggested_fix=f"Use '{good}' unless the reference is an explicit historical rename.",
                )
            )
    return findings
