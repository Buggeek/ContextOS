from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from inventory_engine.report_builder import build_report


EXCLUDED_DIRS = {".git", ".mypy_cache", ".pytest_cache", "__pycache__"}
SCAN_ROOTS = ("README.md", "docs", "SSOT", "ops", "templates", "examples", "tools", "contextos", ".contextos")

DOC_TAXONOMY_CLASSES = {
    "0.x_foundations": "foundations",
    "1.x_architecture": "architecture",
    "2.x_taxonomy": "taxonomy",
    "3.x_operation": "operation",
    "4.x_adoption": "adoption",
    "5.x_strategy": "strategy",
}

SSOT_PREFIX_CLASSES = {
    "S": "ssot-strategy",
    "P": "ssot-product",
    "A": "ssot-architecture",
    "G": "ssot-governance",
    "E": "ssot-execution",
}


def relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def iter_inventory_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for name in SCAN_ROOTS:
        candidate = root / name
        if not candidate.exists():
            continue
        if candidate.is_file():
            files.append(candidate)
            continue
        for path in candidate.rglob("*"):
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            if path.is_file():
                files.append(path)
    return sorted(files, key=lambda path: relative_path(root, path))


def read_title(path: Path) -> str | None:
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


def taxonomy_class_for(rel_path: str) -> str | None:
    parts = rel_path.split("/")
    if rel_path == "README.md":
        return "repository-readme"
    if parts[0] == "docs" and len(parts) > 1:
        return DOC_TAXONOMY_CLASSES.get(parts[1])
    if parts[0] == "SSOT":
        if len(parts) > 1 and parts[1] == "epics":
            return "ssot-epic"
        stem = Path(parts[-1]).stem
        if "." in stem:
            return SSOT_PREFIX_CLASSES.get(stem.split(".", 1)[0])
    if parts[0] == "templates":
        return "template"
    if parts[0] == "ops":
        return "operation"
    if parts[0] == "examples":
        return "example"
    return None


def kind_for(path: Path, rel_path: str) -> str:
    if rel_path == "contextos":
        return "runtime-executable"
    if path.suffix == ".py":
        return "python-source"
    if path.suffix == ".md":
        return "markdown"
    if path.suffix in {".yaml", ".yml"}:
        return "runtime-config"
    if path.suffix == ".json":
        return "json"
    return "file"


def runtime_component_for(rel_path: str) -> str | None:
    if rel_path == "contextos":
        return "runtime-cli"
    if rel_path.startswith("tools/cli/"):
        return "runtime-cli"
    if rel_path.startswith("tools/validators/"):
        return "validator-engine"
    if rel_path.startswith("tools/readiness/"):
        return "context-readiness-engine"
    if rel_path.startswith("docs/1.x_architecture/1.5_runtime_contracts/"):
        return "runtime-contract"
    if rel_path.startswith(".contextos/"):
        return "runtime-config"
    return None


def governance_kind_for(rel_path: str) -> str | None:
    name = Path(rel_path).name
    if rel_path == "ops/AGENT_RULES.md":
        return "agent-rules"
    if rel_path.startswith("SSOT/G."):
        return "ssot-governance"
    if rel_path.startswith("docs/3.x_operation/3.6_"):
        return "authority-model"
    if rel_path.startswith("docs/3.x_operation/3.7_"):
        return "governance-protocol"
    if rel_path.startswith("SSOT/epics/"):
        return "epic-governance"
    if rel_path.startswith("templates/governance/"):
        return "governance-template"
    if name in {"G.1_Definition_of_Ready.md", "G.2_Definition_of_Done.md"}:
        return "governance-template"
    return None


def roadmap_kind_for(rel_path: str) -> str | None:
    if rel_path == "SSOT/P.2_Product_Roadmap.md":
        return "ssot-roadmap"
    if rel_path == "SSOT/P.1_Product_Map.md":
        return "product-map"
    if rel_path.startswith("SSOT/epics/"):
        return "epic-backlog"
    if rel_path == "docs/5.x_strategy/5.0_COS_Roadmap.md":
        return "legacy-roadmap"
    if rel_path == "docs/5.x_strategy/5.4_COS_Product_Roadmap.md":
        return "product-roadmap"
    if rel_path == "docs/5.x_strategy/5.5_COS_Runtime_Maturity_Model.md":
        return "maturity-roadmap"
    return None


def artifact_for(root: Path, path: Path) -> dict:
    rel_path = relative_path(root, path)
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
        "path": rel_path,
        "kind": kind_for(path, rel_path),
        "taxonomy_class": taxonomy_class_for(rel_path),
        "title": read_title(path),
        "roles": roles,
    }


def compact_artifact(artifact: dict, **extra: str) -> dict:
    item = {
        "path": artifact["path"],
        "artifact_kind": artifact["kind"],
        "taxonomy_class": artifact["taxonomy_class"],
        "title": artifact["title"],
    }
    item.update(extra)
    return item


class RepositoryInventoryEngine:
    """Read-only repository inventory engine for Context Readiness."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(self, generated_at: str | None = None) -> dict:
        resolved_root = self.root.resolve()
        artifacts = [artifact_for(resolved_root, path) for path in iter_inventory_files(resolved_root)]

        class_paths: dict[str, list[str]] = defaultdict(list)
        runtime_artifacts: list[dict] = []
        governance_artifacts: list[dict] = []
        roadmap_artifacts: list[dict] = []

        for artifact in artifacts:
            taxonomy_class = artifact["taxonomy_class"]
            if taxonomy_class:
                class_paths[taxonomy_class].append(artifact["path"])

            runtime_component = runtime_component_for(artifact["path"])
            if runtime_component:
                runtime_artifacts.append(compact_artifact(artifact, component=runtime_component))

            governance_kind = governance_kind_for(artifact["path"])
            if governance_kind:
                governance_artifacts.append(compact_artifact(artifact, kind=governance_kind))

            roadmap_kind = roadmap_kind_for(artifact["path"])
            if roadmap_kind:
                roadmap_artifacts.append(compact_artifact(artifact, kind=roadmap_kind))

        detected = {
            "artifacts": artifacts,
            "taxonomy_classes": [
                {"id": taxonomy_class, "count": len(paths), "paths": sorted(paths)}
                for taxonomy_class, paths in sorted(class_paths.items())
            ],
            "runtime_artifacts": sorted(runtime_artifacts, key=lambda item: item["path"]),
            "governance_artifacts": sorted(governance_artifacts, key=lambda item: item["path"]),
            "roadmap_artifacts": sorted(roadmap_artifacts, key=lambda item: item["path"]),
        }
        return build_report(resolved_root, detected, generated_at=generated_at)
