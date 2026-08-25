from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable
from urllib.parse import unquote, urlparse

from engine.findings import MarkdownDocument, ValidationContext, line_for_offset, make_finding, markdown_anchor, normalize_rel


URL_SCHEMES = {"http", "https", "mailto", "tel"}


def strip_markdown_code(text: str) -> str:
    def preserve_lines(match: re.Match[str]) -> str:
        return "\n" * match.group(0).count("\n")

    text = re.sub(r"```.*?```", preserve_lines, text, flags=re.DOTALL)
    return re.sub(r"`[^`]*`", lambda match: " " * len(match.group(0)), text)


def extract_markdown_links(doc: MarkdownDocument) -> Iterable[tuple[str, int, str, str]]:
    text = strip_markdown_code(doc.text)
    patterns = [
        re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)"),
        re.compile(r"!\[[^\]]*\]\(([^)]+)\)"),
    ]
    for pattern in patterns:
        for match in pattern.finditer(text):
            target = match.group(1).strip()
            if not target:
                continue
            line_no = line_for_offset(text, match.start())
            yield target, line_no, match.group(0), "image" if pattern.pattern.startswith("!") else "link"


def is_external_target(target: str) -> bool:
    parsed = urlparse(target)
    if parsed.scheme in URL_SCHEMES:
        return True
    if parsed.scheme and parsed.scheme not in {"", "file"}:
        return True
    return False


def split_target(target: str) -> tuple[str, str | None]:
    cleaned = target.strip()
    cleaned = cleaned.split("?", 1)[0]
    if "#" in cleaned:
        path_part, anchor = cleaned.split("#", 1)
        return unquote(path_part), unquote(anchor)
    return unquote(cleaned), None


def resolve_internal_target(doc: MarkdownDocument, path_part: str, root: Path) -> Path:
    if not path_part:
        return doc.path
    if path_part.startswith("/"):
        return (root / path_part.lstrip("/")).resolve()
    return (doc.path.parent / path_part).resolve()


def is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def relative_paths_resolve(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        for target, line_no, raw, kind in extract_markdown_links(doc):
            if is_external_target(target):
                continue
            path_part, _anchor = split_target(target)
            if not path_part:
                continue
            resolved = resolve_internal_target(doc, path_part, ctx.root)
            if not is_within_root(resolved, ctx.root):
                findings.append(
                    make_finding(
                        "links.relative_paths_resolve",
                        "error",
                        "Internal link resolves outside the repository root.",
                        doc.rel_path,
                        line_no,
                        evidence={"target": target, "raw": raw},
                        suggested_fix="Use a repository-local relative link.",
                    )
                )
                continue
            if not resolved.exists():
                findings.append(
                    make_finding(
                        "links.relative_paths_resolve",
                        "error",
                        "Internal link target does not exist.",
                        doc.rel_path,
                        line_no,
                        evidence={"target": target, "resolved": normalize_rel(resolved.relative_to(ctx.root)), "kind": kind},
                        suggested_fix="Update the relative path or restore the target file.",
                    )
                )
    return findings


def anchors_resolve(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        for target, line_no, raw, kind in extract_markdown_links(doc):
            if is_external_target(target):
                continue
            path_part, anchor = split_target(target)
            if not anchor:
                continue
            if anchor.startswith(":~:"):
                continue
            resolved = resolve_internal_target(doc, path_part, ctx.root)
            if not resolved.exists() or resolved.is_dir():
                continue
            if resolved.suffix.lower() != ".md":
                continue
            rel = normalize_rel(resolved.relative_to(ctx.root))
            target_doc = ctx.markdown_by_rel.get(rel)
            if target_doc is None:
                continue
            normalized_anchor = markdown_anchor(anchor)
            if normalized_anchor not in target_doc.anchors:
                findings.append(
                    make_finding(
                        "links.anchors_resolve",
                        "error",
                        "Internal link anchor does not match a heading in the target file.",
                        doc.rel_path,
                        line_no,
                        anchor=anchor,
                        evidence={"target": target, "target_file": rel, "kind": kind},
                        suggested_fix="Update the fragment to match an existing heading anchor.",
                    )
                )
    return findings


def heading_anchor_unique(ctx: ValidationContext) -> list:
    findings = []
    for doc in ctx.markdown_docs:
        seen: dict[str, int] = {}
        for line_no, title, _anchor in doc.headings:
            base = markdown_anchor(title)
            if base in seen:
                findings.append(
                    make_finding(
                        "links.heading_anchor_unique",
                        "warn",
                        "Duplicate heading anchor base may make manual links ambiguous.",
                        doc.rel_path,
                        line_no,
                        anchor=base,
                        evidence={"first_line": seen[base], "heading": title},
                        suggested_fix="Make duplicate headings more specific.",
                    )
                )
            else:
                seen[base] = line_no
    return findings
