from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


SEVERITIES = ("info", "warn", "error", "fatal")

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


def ssot_doc_profile(ctx: ValidationContext, doc: MarkdownDocument) -> str:
    for tree in ssot_tree_roots(ctx.root):
        try:
            doc.path.relative_to(tree)
        except ValueError:
            continue
        return compliance_profile_for_tree(tree)
    return "strict"


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
