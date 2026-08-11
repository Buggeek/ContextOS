from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

from discovery_engine.report_builder import build_report


DISCOVERY_ROOT = Path(__file__).resolve().parents[1]
TOOLS_ROOT = Path(__file__).resolve().parents[2]
READINESS_ROOT = TOOLS_ROOT / "readiness"
if str(READINESS_ROOT) not in sys.path:
    sys.path.insert(0, str(READINESS_ROOT))

from inventory_engine.repository_inventory import (  # noqa: E402
    artifact_for,
    governance_kind_for,
    iter_inventory_files,
    roadmap_kind_for,
    runtime_component_for,
)


OWNER_PATTERN = re.compile(r"^\s*(Owner|Maintainer|Product Owner|Runtime Owner)\s*:\s*(.+?)\s*$", re.IGNORECASE)
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def artifact_id(path: str, file_hash: str) -> str:
    return f"discovery.artifact.{stable_hash(path + ':' + file_hash)[:16]}"


def relationship_id(rel_type: str, source: str, target: str) -> str:
    return f"discovery.relationship.{stable_hash(rel_type + ':' + source + ':' + target)[:16]}"


def source_id(root: Path, fingerprint: str) -> str:
    return f"discovery.source.local.{stable_hash(str(root.resolve()) + ':' + fingerprint)[:16]}"


def tree_fingerprint(items: list[dict]) -> str:
    material = "\n".join(f"{item['path']}:{item['observed']['sha256']}" for item in sorted(items, key=lambda value: value["path"]))
    return stable_hash(material)


def observed_title(path: Path) -> str | None:
    if path.suffix.lower() != ".md":
        return None
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip() or None
    except UnicodeDecodeError:
        return None
    return None


def line_count(path: Path) -> int | None:
    if path.suffix.lower() not in {".md", ".py", ".yaml", ".yml", ".json", ".txt"}:
        return None
    try:
        return len(path.read_text(encoding="utf-8").splitlines())
    except UnicodeDecodeError:
        return None


def classification_for(root: Path, path: Path) -> dict:
    base = artifact_for(root, path)
    rel_path = base["path"]
    roles: list[str] = []
    runtime_component = runtime_component_for(rel_path)
    governance_kind = governance_kind_for(rel_path)
    roadmap_kind = roadmap_kind_for(rel_path)
    if runtime_component:
        roles.append("runtime")
    if governance_kind:
        roles.append("governance")
    if roadmap_kind:
        roles.append("roadmap")
    return {
        "kind": base["kind"],
        "taxonomy_class": base["taxonomy_class"],
        "roles": sorted(roles),
        "runtime_component": runtime_component,
        "governance_kind": governance_kind,
        "roadmap_kind": roadmap_kind,
        "belief_state": "inferred",
        "confidence": "path_convention",
        "truth_boundary": "Classification is inferred from path/name conventions and is not organizational truth.",
    }


def artifact_observation(root: Path, path: Path) -> dict:
    rel_path = rel(root, path)
    file_hash = sha256_file(path)
    return {
        "id": artifact_id(rel_path, file_hash),
        "path": rel_path,
        "source_type": "local_file",
        "observed": {
            "exists": True,
            "size_bytes": path.stat().st_size,
            "sha256": file_hash,
            "suffix": path.suffix,
            "title": observed_title(path),
            "line_count": line_count(path),
            "belief_state": "observed",
        },
        "classification": classification_for(root, path),
        "provenance": {
            "source": "local_filesystem",
            "observed_path": rel_path,
            "evidence_ref": f"file://{rel_path}",
        },
    }


def ownership_for(path: Path, rel_path: str) -> list[dict]:
    if path.suffix.lower() != ".md":
        return []
    evidence: list[dict] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return evidence
    for index, line in enumerate(lines[:80], start=1):
        match = OWNER_PATTERN.match(line)
        if not match:
            continue
        field = match.group(1).strip()
        value = match.group(2).strip()
        evidence.append(
            {
                "id": f"discovery.ownership.{stable_hash(rel_path + ':' + str(index) + ':' + field + ':' + value)[:16]}",
                "path": rel_path,
                "line": index,
                "field": field,
                "value": value,
                "belief_state": "observed",
                "truth_boundary": "Direct owner text was observed; authority and correctness are not inferred.",
                "evidence_ref": f"{rel_path}:{index}",
            }
        )
    return evidence


def containment_relationships(artifacts: list[dict]) -> list[dict]:
    relationships: list[dict] = []
    for artifact in artifacts:
        parent = str(Path(artifact["path"]).parent)
        if parent == ".":
            parent = "<repo-root>"
        relationships.append(
            {
                "id": relationship_id("contained_in", artifact["path"], parent),
                "type": "contained_in",
                "from": artifact["path"],
                "to": parent,
                "belief_state": "observed",
                "evidence_refs": [artifact["id"]],
                "truth_boundary": "Containment is a filesystem relationship, not semantic ownership or dependency.",
            }
        )
    return relationships


def markdown_reference_relationships(root: Path, files: list[Path], artifact_paths: set[str]) -> list[dict]:
    relationships: list[dict] = []
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        rel_path = rel(root, path)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for match in MARKDOWN_LINK_PATTERN.finditer(line):
                target = match.group(1).split("#", 1)[0].strip()
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (path.parent / target).resolve()
                try:
                    target_rel = resolved.relative_to(root).as_posix()
                except ValueError:
                    continue
                relationships.append(
                    {
                        "id": relationship_id("references_path", rel_path, target_rel),
                        "type": "references_path",
                        "from": rel_path,
                        "to": target_rel,
                        "belief_state": "observed",
                        "target_observed": target_rel in artifact_paths,
                        "evidence_refs": [f"{rel_path}:{line_number}"],
                        "truth_boundary": "A literal local reference was observed; semantic dependency is not inferred.",
                    }
                )
    return relationships


class LocalDiscoveryBundleEngine:
    """Read-only local filesystem Discovery Bundle engine."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(self, generated_at: str | None = None) -> dict:
        root = self.root.resolve()
        files = iter_inventory_files(root)
        artifacts = [artifact_observation(root, path) for path in files]
        fingerprint = tree_fingerprint(artifacts)
        artifact_paths = {artifact["path"] for artifact in artifacts}
        ownership_evidence = [
            item
            for path in files
            for item in ownership_for(path, rel(root, path))
        ]
        relationships = containment_relationships(artifacts)
        relationships.extend(markdown_reference_relationships(root, files, artifact_paths))
        source = {
            "id": source_id(root, fingerprint),
            "type": "local_filesystem",
            "root": str(root),
            "fingerprint": fingerprint,
            "fingerprint_algorithm": "sha256(path:sha256)",
            "belief_state": "observed",
        }
        provenance = {
            "engine": "LocalDiscoveryBundleEngine",
            "schema": "contextos.discovery.bundle/1",
            "scan_roots": ["README.md", "docs", "SSOT", "ops", "templates", "examples", "tools", "contextos", ".contextos"],
            "excluded": [".git", ".mypy_cache", ".pytest_cache", "__pycache__", ".DS_Store", "Thumbs.db", "desktop.ini"],
        }
        limitations = [
            "Only local filesystem evidence is scanned in this slice.",
            "Classification is inferred from path/name conventions and must not be treated as canonical truth.",
            "Ownership evidence is captured only when explicit owner-like fields are present in scanned markdown.",
            "Relationship detection is limited to filesystem containment and literal local markdown references.",
            "Completeness, freshness, correctness, authority, and semantic meaning remain unknown.",
        ]
        return build_report(root, source, artifacts, relationships, ownership_evidence, provenance, limitations, generated_at)
