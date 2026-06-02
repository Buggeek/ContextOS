#!/usr/bin/env python3
"""Context OS Validator Engine v0.

This is intentionally small and dependency-free. It implements the first
read-only validator surface before the full Runtime CLI exists.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import unquote, urlparse


SCHEMA = "contextos.validator.report/1"
SEVERITIES = ("info", "warn", "error", "fatal")
VALID_MODES = ("install-check", "pre-bootstrap", "full", "gate")
VALID_FORMATS = ("human", "json")

CHECK_ROOTS = ("docs", "SSOT", "ops", "templates")
MARKDOWN_ROOTS = ("docs", "SSOT", "ops", "templates", "examples")
REPO_JUNK_FILENAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
MOM_REQUIRED = (
    "S.1_Vision.md",
    "P.1_Product_Map.md",
    "A.1_System_Map.md",
    "A.4_Data_Entities.md",
    "G.1_Definition_of_Ready.md",
    "G.2_Definition_of_Done.md",
)
EPIC_REQUIRED_SECTIONS = (
    "Objective",
    "Problem",
    "Scope",
    "Out of Scope",
    "Expected Outcomes",
    "Dependencies",
    "Success Criteria",
    "Definition of Ready",
    "Definition of Done",
    "Related Artifacts",
)
EPIC_REQUIRED_METADATA = ("Epic ID", "Version", "Status", "Owner")

TAXONOMY_PREFIXES = {
    "S": "strategy",
    "B": "business",
    "P": "product",
    "A": "architecture",
    "O": "operation",
    "G": "governance",
    "E": "execution",
    "F": "feedback",
}
DOC_FOLDER_PREFIXES = {
    "0.x_foundations": "0.",
    "1.x_architecture": "1.",
    "2.x_taxonomy": "2.",
    "3.x_operation": "3.",
    "4.x_adoption": "4.",
    "5.x_strategy": "5.",
}
FRAMEWORK_OWNER_ROOTS = ("docs", "templates", "ops")
FRAMEWORK_OWNER_ALLOWLIST = {
    "ops/AGENT_RULES.md",
}

LEGACY_PATH_TERMS = (
    "docs/3.x_mom",
    "/docs/3.x_mom",
    "../3.x_mom",
    "../../docs/3.x_mom",
    "3.x_mom",
    "docs/1.x_architecture/Runtime_Model.md",
    "docs/5.x_strategy/5.0_COS_Roadmap.md",
    "P.1_Product_Roadmap",
    "3.2_toolbox",
    "3.3_skillbox",
)
LEGACY_ALLOWLIST = {
    "docs/3.x_mom/README.md",
    "docs/3.x_mom/Minimum_Operational_Map.md",
    "SSOT/E.1_User_Story_US-001_Structure_Canonical_Paths.md",
    "SSOT/P.5_Epic_Structural_Integrity.md",
    "SSOT/epics/EPIC-001_Structural_Integrity.md",
}
LEGACY_REFERENCE_ALLOWLIST_PATTERNS = (
    "legacy",
    "forbidden",
    "grep checks",
    "older links",
    "canonicalize operational docs path",
    "legacy alias",
    "legacy path",
    "path is legacy",
)

URL_SCHEMES = {"http", "https", "mailto", "tel"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str
    path: str | None = None
    line: int | None = None
    anchor: str | None = None
    evidence: dict | None = None
    suggested_fix: str | None = None

    @property
    def id(self) -> str:
        material = "|".join(
            [
                self.rule,
                self.severity,
                self.path or "",
                str(self.line or ""),
                self.anchor or "",
                self.message,
                canonical_json(self.evidence) if self.evidence is not None else "",
            ]
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()[:26]

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
            "line": self.line,
            "anchor": self.anchor,
            "evidence": self.evidence,
            "suggested_fix": self.suggested_fix,
        }


@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    severity: str
    modes: tuple[str, ...]
    run: Callable[["ValidationContext"], list[Finding]]


@dataclass
class MarkdownDocument:
    path: Path
    rel_path: str
    text: str
    lines: list[str]
    headings: list[tuple[int, str, str]] = field(default_factory=list)
    anchors: set[str] = field(default_factory=set)


@dataclass
class ValidationContext:
    root: Path
    mode: str
    manifest: Path | None
    discovery: Path | None
    markdown_docs: list[MarkdownDocument]
    markdown_by_rel: dict[str, MarkdownDocument]
    tracked_files: set[str] | None


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def normalize_rel(path: Path | str) -> str:
    value = Path(path).as_posix()
    if value.startswith("./"):
        return value[2:]
    return value


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def markdown_anchor(heading: str) -> str:
    slug = heading.strip().lower()
    slug = re.sub(r"`([^`]*)`", r"\1", slug)
    slug = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", slug)
    slug = re.sub(r"[^a-z0-9 _.-]", "", slug)
    slug = slug.replace(" ", "-")
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def heading_text(line: str) -> str | None:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
    if not match:
        return None
    text = match.group(2).strip()
    text = re.sub(r"\s+#+$", "", text).strip()
    return text


def parse_markdown(path: Path, root: Path) -> MarkdownDocument:
    rel = normalize_rel(path.relative_to(root))
    text = read_text(path)
    lines = text.splitlines()
    headings: list[tuple[int, str, str]] = []
    anchors: set[str] = set()
    counts: dict[str, int] = {}

    for index, line in enumerate(lines, start=1):
        title = heading_text(line)
        if title is None:
            continue
        base = markdown_anchor(title)
        anchor = base
        if base in counts:
            counts[base] += 1
            anchor = f"{base}-{counts[base]}"
        else:
            counts[base] = 0
        headings.append((index, title, anchor))
        anchors.add(anchor)

    return MarkdownDocument(path=path, rel_path=rel, text=text, lines=lines, headings=headings, anchors=anchors)


def iter_markdown_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for rel_root in MARKDOWN_ROOTS:
        base = root / rel_root
        if not base.exists():
            continue
        for path in base.rglob("*.md"):
            if ".git" not in path.parts:
                paths.append(path)
    if (root / "README.md").exists():
        paths.append(root / "README.md")
    return sorted(set(paths), key=lambda p: normalize_rel(p.relative_to(root)))


def collect_markdown(root: Path) -> tuple[list[MarkdownDocument], dict[str, MarkdownDocument]]:
    docs = [parse_markdown(path, root) for path in iter_markdown_files(root)]
    by_rel = {doc.rel_path: doc for doc in docs}
    return docs, by_rel


def tracked_files(root: Path) -> set[str] | None:
    try:
        proc = subprocess.run(
            ["git", "ls-files"],
            cwd=root,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def find_field_line(doc: MarkdownDocument, field_name: str) -> int | None:
    pattern = re.compile(rf"^\s*(?:#{{1,6}}\s*)?(?:[-*]\s*)?(?:\*\*)?{re.escape(field_name)}(?:\*\*)?\s*:", re.IGNORECASE)
    for index, line in enumerate(doc.lines, start=1):
        if pattern.search(line):
            return index
    return None


def has_field(doc: MarkdownDocument, field_name: str) -> bool:
    return find_field_line(doc, field_name) is not None


def has_heading(doc: MarkdownDocument, title: str) -> bool:
    wanted = title.lower()
    return any(wanted in heading.lower() for _, heading, _ in doc.headings)


def first_heading(doc: MarkdownDocument) -> tuple[int, str, str] | None:
    return doc.headings[0] if doc.headings else None


def is_ssot_doc(doc: MarkdownDocument) -> bool:
    return doc.rel_path.startswith("SSOT/") or "/SSOT/" in doc.rel_path


def is_framework_doc(doc: MarkdownDocument) -> bool:
    return doc.rel_path.startswith(FRAMEWORK_OWNER_ROOTS)


def ssot_tree_roots(root: Path) -> list[Path]:
    trees: list[Path] = []
    root_ssot = root / "SSOT"
    if root_ssot.exists():
        trees.append(root_ssot)
    examples = root / "examples"
    if examples.exists():
        for candidate in examples.rglob("SSOT"):
            if candidate.is_dir():
                trees.append(candidate)
    return sorted(trees, key=lambda p: normalize_rel(p.relative_to(root)))


def compliance_profile_for_tree(tree: Path) -> str:
    parent_readme = tree.parent / "README.md"
    ssot_readme = tree / "README.md"
    for path in (ssot_readme, parent_readme):
        if not path.exists():
            continue
        text = read_text(path)
        match = re.search(r"Compliance profile:\s*`?(minimal|strict)`?", text, flags=re.IGNORECASE)
        if match:
            return match.group(1).lower()
    if "examples" in tree.parts:
        return "minimal"
    return "strict"


def mode_in(rule: Rule, mode: str) -> bool:
    return mode in rule.modes or "all" in rule.modes


def make_finding(
    rule: str,
    severity: str,
    message: str,
    path: str | None = None,
    line: int | None = None,
    anchor: str | None = None,
    evidence: dict | None = None,
    suggested_fix: str | None = None,
) -> Finding:
    if severity not in SEVERITIES:
        raise ValueError(f"invalid severity: {severity}")
    return Finding(
        rule=rule,
        severity=severity,
        message=message,
        path=path,
        line=line,
        anchor=anchor,
        evidence=evidence,
        suggested_fix=suggested_fix,
    )


def rule_structure_required_roots(ctx: ValidationContext) -> list[Finding]:
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


def rule_structure_runtime_manifest(ctx: ValidationContext) -> list[Finding]:
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


def rule_structure_tracked_junk_absent(ctx: ValidationContext) -> list[Finding]:
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


def rule_structure_markdown_h1_present(ctx: ValidationContext) -> list[Finding]:
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


def rule_structure_legacy_paths(ctx: ValidationContext) -> list[Finding]:
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


def rule_naming_contextos_convention(ctx: ValidationContext) -> list[Finding]:
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


def rule_naming_doctrine_terms(ctx: ValidationContext) -> list[Finding]:
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


def strip_markdown_code(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`]*`", "", text)


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


def rule_links_relative_paths_resolve(ctx: ValidationContext) -> list[Finding]:
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


def rule_links_anchors_resolve(ctx: ValidationContext) -> list[Finding]:
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


def rule_links_heading_anchor_unique(ctx: ValidationContext) -> list[Finding]:
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


def ssot_artifact_id(filename: str) -> str | None:
    if filename == "README.md":
        return None
    if re.match(r"^EPIC-\d{3}_.+\.md$", filename):
        return filename.split("_", 1)[0]
    match = re.match(r"^([A-Z])\.(\d+)_.*\.md$", filename)
    if match and match.group(1) in TAXONOMY_PREFIXES:
        return f"{match.group(1)}.{match.group(2)}"
    return None


def rule_taxonomy_ssot_filename_prefix(ctx: ValidationContext) -> list[Finding]:
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


def rule_taxonomy_ssot_h1_matches_file(ctx: ValidationContext) -> list[Finding]:
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


def rule_taxonomy_docs_folder_prefix(ctx: ValidationContext) -> list[Finding]:
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


def rule_mom_required_artifacts(ctx: ValidationContext) -> list[Finding]:
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


def ssot_doc_profile(ctx: ValidationContext, doc: MarkdownDocument) -> str:
    for tree in ssot_tree_roots(ctx.root):
        try:
            doc.path.relative_to(tree)
        except ValueError:
            continue
        return compliance_profile_for_tree(tree)
    return "strict"


def rule_mom_required_fields(ctx: ValidationContext) -> list[Finding]:
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


def rule_mom_epic_required_sections(ctx: ValidationContext) -> list[Finding]:
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


def rule_ownership_ssot_owner_present(ctx: ValidationContext) -> list[Finding]:
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


def rule_ownership_framework_owner_present(ctx: ValidationContext) -> list[Finding]:
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


def rule_governance_dor_dod_present(ctx: ValidationContext) -> list[Finding]:
    findings = []
    for tree in ssot_tree_roots(ctx.root):
        tree_rel = normalize_rel(tree.relative_to(ctx.root))
        for filename in ("G.1_Definition_of_Ready.md", "G.2_Definition_of_Done.md"):
            if not (tree / filename).exists():
                findings.append(
                    make_finding(
                        "governance.dor_dod_present",
                        "error",
                        "SSOT tree is missing a governance gate artifact.",
                        f"{tree_rel}/{filename}",
                        evidence={"ssot_tree": tree_rel, "required": filename},
                        suggested_fix="Create both G.1 Definition of Ready and G.2 Definition of Done.",
                    )
                )
    return findings


def rule_governance_agent_rules_present(ctx: ValidationContext) -> list[Finding]:
    if (ctx.root / "ops" / "AGENT_RULES.md").exists():
        return []
    return [
        make_finding(
            "governance.agent_rules_present",
            "error",
            "Agent-facing governance rules are missing.",
            "ops/AGENT_RULES.md",
            suggested_fix="Restore ops/AGENT_RULES.md.",
        )
    ]


def rule_authority_model_present(ctx: ValidationContext) -> list[Finding]:
    rel = "docs/3.x_operation/3.6_COS_Human_Agent_Authority_Model.md"
    path = ctx.root / rel
    if not path.exists():
        return [
            make_finding(
                "authority.model_present",
                "error",
                "Human-Agent Authority Model is missing.",
                rel,
                suggested_fix="Restore the authority model document.",
            )
        ]
    text = read_text(path)
    missing = [level for level in ("L0", "L1", "L2", "L3", "L4", "L5") if level not in text]
    if missing:
        return [
            make_finding(
                "authority.model_present",
                "error",
                "Human-Agent Authority Model does not declare every autonomy level.",
                rel,
                evidence={"missing_levels": missing},
                suggested_fix="Declare autonomy levels L0 through L5.",
            )
        ]
    return []


def is_product_artifact(doc: MarkdownDocument) -> bool:
    name = doc.path.name
    if name.startswith("P."):
        return True
    if "/epics/EPIC-" in doc.rel_path:
        return True
    return False


def rule_hypothesis_product_status_fields(ctx: ValidationContext) -> list[Finding]:
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


def rule_drift_discovery_bundle_available(ctx: ValidationContext) -> list[Finding]:
    if ctx.discovery is None:
        return [
            make_finding(
                "drift.discovery_bundle_available",
                "info",
                "No Discovery output bundle supplied; drift validation skipped.",
                evidence={"input": "--discovery"},
            )
        ]
    if not ctx.discovery.exists():
        return [
            make_finding(
                "drift.discovery_bundle_available",
                "error",
                "Discovery output bundle path does not exist.",
                normalize_rel(ctx.discovery),
                evidence={"input": str(ctx.discovery)},
                suggested_fix="Provide an existing Discovery bundle path or omit --discovery.",
            )
        ]
    return [
        make_finding(
            "drift.discovery_bundle_available",
            "info",
            "Discovery output bundle supplied; semantic drift checks are deferred in v0.",
            normalize_rel(ctx.discovery),
            evidence={"input": str(ctx.discovery)},
        )
    ]


RULES: tuple[Rule, ...] = (
    Rule("structure.required_roots", "structure", "error", ("install-check", "pre-bootstrap", "full", "gate"), rule_structure_required_roots),
    Rule("structure.runtime_manifest", "structure", "warn", ("install-check", "pre-bootstrap", "full", "gate"), rule_structure_runtime_manifest),
    Rule("structure.tracked_junk_absent", "structure", "error", ("install-check", "pre-bootstrap", "full", "gate"), rule_structure_tracked_junk_absent),
    Rule("structure.markdown_h1_present", "structure", "error", ("full", "gate"), rule_structure_markdown_h1_present),
    Rule("structure.legacy_paths", "structure", "warn", ("full", "gate"), rule_structure_legacy_paths),
    Rule("naming.contextos_convention", "naming", "warn", ("full", "gate"), rule_naming_contextos_convention),
    Rule("naming.doctrine_terms", "naming", "error", ("full", "gate"), rule_naming_doctrine_terms),
    Rule("links.relative_paths_resolve", "links", "error", ("full", "gate"), rule_links_relative_paths_resolve),
    Rule("links.anchors_resolve", "links", "error", ("full", "gate"), rule_links_anchors_resolve),
    Rule("links.heading_anchor_unique", "links", "warn", ("full",), rule_links_heading_anchor_unique),
    Rule("taxonomy.ssot_filename_prefix", "taxonomy", "error", ("pre-bootstrap", "full", "gate"), rule_taxonomy_ssot_filename_prefix),
    Rule("taxonomy.ssot_h1_matches_file", "taxonomy", "error", ("full", "gate"), rule_taxonomy_ssot_h1_matches_file),
    Rule("taxonomy.docs_folder_prefix", "taxonomy", "warn", ("full",), rule_taxonomy_docs_folder_prefix),
    Rule("mom.required_artifacts", "mom", "error", ("pre-bootstrap", "full", "gate"), rule_mom_required_artifacts),
    Rule("mom.required_fields", "mom", "error", ("full", "gate"), rule_mom_required_fields),
    Rule("mom.epic_required_sections", "mom", "error", ("full", "gate"), rule_mom_epic_required_sections),
    Rule("ownership.ssot_owner_present", "ownership", "error", ("pre-bootstrap", "full", "gate"), rule_ownership_ssot_owner_present),
    Rule("ownership.framework_owner_present", "ownership", "warn", ("full",), rule_ownership_framework_owner_present),
    Rule("governance.dor_dod_present", "governance", "error", ("pre-bootstrap", "full", "gate"), rule_governance_dor_dod_present),
    Rule("governance.agent_rules_present", "governance", "error", ("install-check", "pre-bootstrap", "full", "gate"), rule_governance_agent_rules_present),
    Rule("authority.model_present", "authority", "error", ("pre-bootstrap", "full", "gate"), rule_authority_model_present),
    Rule("hypothesis.product_status_fields", "hypothesis", "warn", ("full",), rule_hypothesis_product_status_fields),
    Rule("drift.discovery_bundle_available", "drift", "info", ("full", "gate"), rule_drift_discovery_bundle_available),
)


def categories() -> set[str]:
    return {rule.category for rule in RULES}


def rule_ids() -> set[str]:
    return {rule.id for rule in RULES}


def parse_rule_selector(selector: str | None) -> tuple[set[str], str | None]:
    available = rule_ids()
    available_categories = categories()
    if not selector or selector.strip() in {"", "all", "*"}:
        return set(available), None

    selected: set[str] = set()
    saw_positive = False
    tokens = [token.strip() for token in selector.split(",") if token.strip()]
    for raw_token in tokens:
        exclude = raw_token.startswith("-")
        token = raw_token[1:] if exclude else raw_token
        matches: set[str]
        if token in {"all", "*"}:
            matches = set(available)
        elif token.endswith(".*"):
            category = token[:-2]
            if category not in available_categories:
                return set(), f"Unknown rule category '{category}'."
            matches = {rule_id for rule_id in available if rule_id.startswith(f"{category}.")}
        elif token in available_categories:
            matches = {rule_id for rule_id in available if rule_id.startswith(f"{token}.")}
        elif token in available:
            matches = {token}
        else:
            return set(), f"Unknown rule selector '{token}'."

        if exclude:
            if not saw_positive and not selected:
                selected = set(available)
            selected -= matches
        else:
            saw_positive = True
            selected |= matches

    if not selected:
        return set(), "Rule selector disabled every rule."
    return selected, None


def build_context(root: Path, mode: str, manifest: str | None, discovery: str | None) -> ValidationContext:
    resolved_root = root.resolve()
    docs, by_rel = collect_markdown(resolved_root)
    manifest_path = Path(manifest).resolve() if manifest else None
    discovery_path = Path(discovery).resolve() if discovery else None
    return ValidationContext(
        root=resolved_root,
        mode=mode,
        manifest=manifest_path,
        discovery=discovery_path,
        markdown_docs=docs,
        markdown_by_rel=by_rel,
        tracked_files=tracked_files(resolved_root),
    )


def run_rules(ctx: ValidationContext, selected_rules: set[str]) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    rules_run = 0
    for rule in sorted(RULES, key=lambda item: item.id):
        if rule.id not in selected_rules or not mode_in(rule, ctx.mode):
            continue
        rules_run += 1
        try:
            findings.extend(rule.run(ctx))
        except Exception as exc:  # pragma: no cover - defensive guard
            findings.append(
                make_finding(
                    rule.id,
                    "fatal",
                    f"Rule failed to execute: {exc}",
                    evidence={"exception": exc.__class__.__name__},
                )
            )
    findings.sort(key=lambda f: (SEVERITIES.index(f.severity), f.rule, f.path or "", f.line or 0, f.message))
    return findings, rules_run


def exit_code_for(mode: str, findings: list[Finding]) -> int:
    if any(f.severity == "fatal" for f in findings):
        return 8
    if any(f.severity == "error" for f in findings):
        return 7
    return 0


def summary_for(findings: list[Finding], rules_run: int, exit_code: int) -> dict:
    counts = {severity: 0 for severity in SEVERITIES}
    for finding in findings:
        counts[finding.severity] += 1
    return {
        "rules_run": rules_run,
        "info": counts["info"],
        "warn": counts["warn"],
        "error": counts["error"],
        "fatal": counts["fatal"],
        "exit_code": exit_code,
    }


def build_report(ctx: ValidationContext, findings: list[Finding], rules_run: int, exit_code: int) -> dict:
    generated_at = _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "schema": SCHEMA,
        "generated_at": generated_at,
        "mode": ctx.mode,
        "root": str(ctx.root),
        "summary": summary_for(findings, rules_run, exit_code),
        "findings": [finding.as_dict() for finding in findings],
    }


def render_human(report: dict, machine_report_path: str | None = None) -> str:
    summary = report["summary"]
    lines = [
        "# Context OS Validator Report",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Mode: `{report['mode']}`",
        f"- Root: `{report['root']}`",
        f"- Rules run: {summary['rules_run']}",
        f"- Findings: info={summary['info']}, warn={summary['warn']}, error={summary['error']}, fatal={summary['fatal']}",
        f"- Exit code: {summary['exit_code']}",
    ]
    if machine_report_path:
        lines.append(f"- Machine report: `{machine_report_path}`")

    findings = report["findings"]
    lines.extend(["", "## Top Findings"])
    if not findings:
        lines.append("")
        lines.append("No findings.")
    else:
        severity_order = {"fatal": 0, "error": 1, "warn": 2, "info": 3}
        top = sorted(findings, key=lambda f: (severity_order[f["severity"]], f["rule"], f["path"] or "", f["line"] or 0))[:10]
        for finding in top:
            location = finding["path"] or "<repo>"
            if finding["line"]:
                location = f"{location}:{finding['line']}"
            lines.append("")
            lines.append(f"- [{finding['severity']}] `{finding['rule']}` at `{location}`")
            lines.append(f"  {finding['message']}")
            if finding.get("suggested_fix"):
                lines.append(f"  Suggested fix: {finding['suggested_fix']}")
    return "\n".join(lines) + "\n"


def write_json_report(path: str, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Context OS Validator Engine v0")
    parser.add_argument("--root", default=".", help="Repository root to validate.")
    parser.add_argument("--mode", default="full", choices=VALID_MODES, help="Validation mode.")
    parser.add_argument("--format", default="human", choices=VALID_FORMATS, help="Output format.")
    parser.add_argument("--rules", default=None, help="Comma-separated rule selectors, e.g. links.*,mom.*,-links.anchors_resolve.")
    parser.add_argument("--manifest", default=None, help="Runtime manifest path. Defaults to .contextos/manifest.yaml.")
    parser.add_argument("--discovery", default=None, help="Optional Discovery output bundle path.")
    parser.add_argument("--json-out", default=None, help="Write the machine report JSON to this path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        error_report = {
            "error": {
                "code": 9,
                "category": "misconfiguration",
                "message": "Repository root does not exist or is not a directory.",
                "evidence": {"root": str(root)},
            }
        }
        print(json.dumps(error_report, indent=2, sort_keys=True))
        return 9

    selected_rules, selector_error = parse_rule_selector(args.rules)
    if selector_error:
        error_report = {
            "error": {
                "code": 9,
                "category": "rules",
                "message": selector_error,
                "evidence": {"rules": args.rules},
            }
        }
        print(json.dumps(error_report, indent=2, sort_keys=True))
        return 9

    ctx = build_context(root, args.mode, args.manifest, args.discovery)
    findings, rules_run = run_rules(ctx, selected_rules)
    exit_code = exit_code_for(args.mode, findings)
    report = build_report(ctx, findings, rules_run, exit_code)

    if args.json_out:
        write_json_report(args.json_out, report)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_human(report, args.json_out), end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
