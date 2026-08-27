from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


PLAN_SCHEMA = "contextos.context.version_capture_plan/1"
PLAN_CHECK_SCHEMA = "contextos.context.version_capture_plan_check/1"
VERSION_SCHEMA = "contextos.context.version/1"
VERSION_CHECK_SCHEMA = "contextos.context.version_check/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(root: Path, report: dict, schema: str, generated_at: str | None = None) -> dict:
    report["schema"] = schema
    report["generated_at"] = generated_at or generated_timestamp()
    report["root"] = str(root.resolve())
    return report


def render_human(report: dict) -> str:
    schema = report.get("schema")
    if schema == PLAN_SCHEMA:
        return render_plan_human(report)
    if schema == PLAN_CHECK_SCHEMA:
        return render_plan_check_human(report)
    if schema == VERSION_SCHEMA:
        return render_version_human(report)
    if schema == VERSION_CHECK_SCHEMA:
        return render_version_check_human(report)
    raise ValueError(f"Unsupported Context Version report schema: {schema}")


def render_plan_human(report: dict) -> str:
    lines = [
        "# Context OS Context Version Capture Plan",
        "",
        f"- Plan: `{report['id']}`",
        f"- Status: `{report['status']}`",
        f"- Event: `{report['capture']['event_type']}`",
        f"- Mission: `{report['capture']['mission_id'] or '<none>'}`",
        f"- Organization: `{report['scope']['organization']}`",
        f"- Domain: `{report['scope']['domain']}`",
        f"- Tier: `{report['scope']['tier']}`",
        f"- Capture basis: `{report['temporal']['capture_at']}`",
        f"- Sources: {report['summary']['source_count']}",
        f"- Content embedded: no",
        f"- Writes performed: no",
        "",
        "## Why Capture",
        report["capture"]["reason"],
        "",
        "## Governed Sources",
    ]
    for source in report["source_manifest"]:
        lines.append(
            f"- `{source['source_of_record']['locator']}` "
            f"[{source['authority_tier']}, {source['lifecycle_state']}] "
            f"`{source['fingerprint']['value'][:16]}...`"
        )
    lines.extend(["", "## Bindings"])
    for name in ("activation_package", "activation_handoff", "parent_version"):
        value = report["bindings"].get(name)
        lines.append(f"- {name.replace('_', ' ').title()}: `{value['id'] if value else '<none>'}`")
    lines.extend(["", "## Capture Gates"])
    for gate, value in report["gates"].items():
        lines.append(f"- `{gate}`: {'pass' if value else 'blocked'}")
    lines.extend(["", "## Continuity Gaps"])
    if report["continuity_gaps"]:
        for gap in report["continuity_gaps"]:
            lines.append(f"- `{gap['id']}`: {gap['message']}")
    else:
        lines.append("- None observed.")
    lines.extend(
        [
            "",
            "## Boundary",
            "- This plan freezes references and fingerprints; it does not copy canonical content.",
            "- Capture requires this exact plan to remain valid.",
            "- The plan grants no authority and performs no persistence or mutation.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_plan_check_human(report: dict) -> str:
    lines = [
        "# Context OS Context Version Capture Plan Check",
        "",
        f"- Plan: `{report['plan']['id']}`",
        f"- Valid: {'yes' if report['result']['valid'] else 'no'}",
        f"- Invalidated: {'yes' if report['result']['invalidated'] else 'no'}",
        "",
        "## Failed Checks",
    ]
    lines.extend(f"- `{item}`" for item in report["result"]["failed_checks"])
    if not report["result"]["failed_checks"]:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def render_version_human(report: dict) -> str:
    lines = [
        "# Context OS Context Version",
        "",
        f"- Version: `{report['id']}`",
        f"- Identity hash: `{report['identity_hash']}`",
        f"- Captured at: `{report['temporal']['captured_at']}`",
        f"- Effective from: `{report['temporal']['effective_from']}`",
        f"- Event: `{report['capture']['event_type']}`",
        f"- Mission: `{report['capture']['mission_id'] or '<none>'}`",
        f"- Organization/domain: `{report['scope']['organization']}` / `{report['scope']['domain']}`",
        f"- Sources: {report['summary']['source_count']}",
        f"- Immutable: yes",
        f"- Content embedded: no",
        "",
        "## Source State",
    ]
    for source in report["source_manifest"]:
        lines.append(
            f"- `{source['source_of_record']['locator']}` "
            f"`{source['fingerprint']['value'][:16]}...` "
            f"[{source['authority_tier']}, {source['lifecycle_state']}]"
        )
    lines.extend(
        [
            "",
            "## Lineage",
            f"- Parent: `{report['lineage']['parent_version']['id'] if report['lineage']['parent_version'] else '<none>'}`",
            f"- Supersedes: `{report['lineage']['supersedes'] or '<none>'}`",
            "- Superseding version: unknown at capture; later lineage must not rewrite this object.",
            "",
            "## Authority And Truth",
            "- Historical identity grants no authority.",
            "- Current canonical context governs current work.",
            "- Source truth axes remain as captured; missing states remain unclassified.",
            "- Retention of version metadata does not imply referenced content is retrievable.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_version_check_human(report: dict) -> str:
    lines = [
        "# Context OS Context Version Check",
        "",
        f"- Version: `{report['version']['id']}`",
        f"- Immutable identity: `{report['result']['immutable_identity']}`",
        f"- Historical verification: `{report['result']['historical_verification']}`",
        f"- Current applicability: `{report['result']['current_applicability']}`",
        f"- Selected-source content: `{report['result']['selected_source_content_currentness']}`",
        f"- Adoption Profile: `{report['result']['profile_currentness']}`",
        f"- Target canonical context: `{report['result']['target_canonical_currentness']}`",
        f"- Repository tip: `{report['result']['repository_tip_state']}` "
        f"(`{report['result']['repository_tip_relevance']}`)",
        f"- Material drift: {'yes' if report['result']['material_drift'] else 'no'}",
        f"- Irrelevant repository advancement: {'yes' if report['result']['irrelevant_repository_advancement'] else 'no'}",
        f"- Historically valid identity: {'yes' if report['result']['historically_valid_identity'] else 'no'}",
        f"- All historical sources resolvable: {'yes' if report['result']['all_historical_sources_resolvable'] else 'no'}",
        "",
        "## Source Resolution",
    ]
    for source in report["source_checks"]:
        lines.append(
            f"- `{source['locator']}`: `{source['resolution']}` "
            f"(current match: {'yes' if source['current_match'] else 'no'})"
        )
    if report["continuity_gaps"]:
        lines.extend(["", "## Continuity Gaps"])
        for gap in report["continuity_gaps"]:
            lines.append(f"- `{gap['id']}`: {gap['message']}")
    return "\n".join(lines) + "\n"


def write_json_report(path: str | Path, report: dict) -> None:
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
