from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.inventory.report/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(root: Path, detected: dict, generated_at: str | None = None) -> dict:
    taxonomy_classes = detected["taxonomy_classes"]
    runtime_artifacts = detected["runtime_artifacts"]
    governance_artifacts = detected["governance_artifacts"]
    roadmap_artifacts = detected["roadmap_artifacts"]
    artifacts = detected["artifacts"]
    return {
        "schema": SCHEMA,
        "generated_at": generated_at or generated_timestamp(),
        "root": str(root.resolve()),
        "summary": {
            "artifact_count": len(artifacts),
            "taxonomy_class_count": len(taxonomy_classes),
            "runtime_artifact_count": len(runtime_artifacts),
            "governance_artifact_count": len(governance_artifacts),
            "roadmap_artifact_count": len(roadmap_artifacts),
        },
        "detected": detected,
    }


def render_human(report: dict, machine_report_path: str | None = None) -> str:
    summary = report["summary"]
    lines = [
        "# Context OS Repository Inventory",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Root: `{report['root']}`",
        f"- Artifacts: {summary['artifact_count']}",
        f"- Taxonomy classes: {summary['taxonomy_class_count']}",
        f"- Runtime artifacts: {summary['runtime_artifact_count']}",
        f"- Governance artifacts: {summary['governance_artifact_count']}",
        f"- Roadmap artifacts: {summary['roadmap_artifact_count']}",
    ]
    if machine_report_path:
        lines.append(f"- Machine report: `{machine_report_path}`")

    lines.extend(["", "## Taxonomy Classes"])
    for item in report["detected"]["taxonomy_classes"]:
        lines.append(f"- `{item['id']}`: {item['count']}")

    lines.extend(["", "## Runtime Artifacts"])
    for item in report["detected"]["runtime_artifacts"][:20]:
        lines.append(f"- `{item['path']}` ({item['component']})")

    lines.extend(["", "## Governance Artifacts"])
    for item in report["detected"]["governance_artifacts"][:20]:
        lines.append(f"- `{item['path']}` ({item['kind']})")

    lines.extend(["", "## Roadmap Artifacts"])
    for item in report["detected"]["roadmap_artifacts"][:20]:
        lines.append(f"- `{item['path']}` ({item['kind']})")
    return "\n".join(lines) + "\n"


def write_json_report(path: str, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
