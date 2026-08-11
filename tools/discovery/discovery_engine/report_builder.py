from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.discovery.bundle/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(
    root: Path,
    source: dict,
    artifacts: list[dict],
    relationships: list[dict],
    ownership_evidence: list[dict],
    provenance: dict,
    limitations: list[str],
    generated_at: str | None = None,
) -> dict:
    inferred_classification_count = sum(1 for artifact in artifacts if artifact["classification"]["taxonomy_class"])
    return {
        "schema": SCHEMA,
        "generated_at": generated_at or generated_timestamp(),
        "root": str(root.resolve()),
        "mode": "local",
        "read_only": True,
        "source": source,
        "summary": {
            "artifact_count": len(artifacts),
            "relationship_count": len(relationships),
            "ownership_evidence_count": len(ownership_evidence),
            "inferred_classification_count": inferred_classification_count,
            "unknown_count": len(limitations),
        },
        "artifacts": sorted(artifacts, key=lambda item: item["path"]),
        "relationships": sorted(relationships, key=lambda item: (item["type"], item["from"], item["to"])),
        "ownership_evidence": sorted(ownership_evidence, key=lambda item: (item["path"], item["line"])),
        "provenance": provenance,
        "boundaries": {
            "observed_evidence": "File existence, path, size, hash, title text, direct owner fields, and literal local references.",
            "inferred_classification": "Artifact kind, taxonomy class, and runtime roles derived from path/name conventions only.",
            "unknown_information": "Completeness, correctness, semantic meaning, current ownership authority, and organizational truth are not inferred.",
            "truth_promotion": "This bundle is an input to construction; it never promotes context to canonical truth.",
        },
        "limitations": limitations,
        "constraints": {
            "writes_performed": False,
            "external_connectors_used": False,
            "knowledge_engine_used": False,
            "graph_runtime_used": False,
            "agents_used": False,
            "semantic_generation_performed": False,
            "organizational_truth_created": False,
        },
    }


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(bundle: dict) -> str:
    summary = bundle["summary"]
    lines = [
        "# Context OS Local Discovery Bundle",
        "",
        f"- Schema: `{bundle['schema']}`",
        f"- Root: `{bundle['root']}`",
        f"- Read-only: {yes_no(bundle['read_only'])}",
        f"- Source type: `{bundle['source']['type']}`",
        f"- Source fingerprint: `{bundle['source']['fingerprint']}`",
        f"- Artifacts: {summary['artifact_count']}",
        f"- Relationships: {summary['relationship_count']}",
        f"- Ownership evidence: {summary['ownership_evidence_count']}",
        f"- Inferred classifications: {summary['inferred_classification_count']}",
        "",
        "## Observed Artifacts",
    ]
    for artifact in bundle["artifacts"][:20]:
        taxonomy = artifact["classification"]["taxonomy_class"] or "unknown"
        lines.append(f"- `{artifact['path']}` ({taxonomy})")
        lines.append(f"  Evidence: `{artifact['id']}` hash={artifact['observed']['sha256']}")
    if not bundle["artifacts"]:
        lines.append("- None.")

    lines.extend(["", "## Ownership Evidence"])
    for item in bundle["ownership_evidence"][:20]:
        lines.append(f"- `{item['path']}:{item['line']}` {item['field']}: {item['value']}")
    if not bundle["ownership_evidence"]:
        lines.append("- None observed.")

    lines.extend(["", "## Boundaries"])
    for key, value in bundle["boundaries"].items():
        lines.append(f"- `{key}`: {value}")

    lines.extend(["", "## Limitations"])
    for item in bundle["limitations"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def write_json_report(path: str, report: dict) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
