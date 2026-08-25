from __future__ import annotations

import datetime as _dt
from pathlib import Path


SCHEMA = "contextos.reasoning.assessment/1"
BENCHMARK_SCHEMA = "contextos.reasoning.benchmark/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(root: Path, report: dict, generated_at: str | None = None) -> dict:
    report["schema"] = SCHEMA
    report["generated_at"] = generated_at or generated_timestamp()
    report["root"] = str(root.resolve())
    return report


def build_benchmark_report(report: dict, generated_at: str | None = None) -> dict:
    report["schema"] = BENCHMARK_SCHEMA
    report["generated_at"] = generated_at or generated_timestamp()
    return report


def render_benchmark_human(report: dict) -> str:
    lines = [
        "# Context OS Reasoning Benchmark",
        "",
        f"- Benchmark: `{report['id']}`",
        f"- Status: `{report['summary']['status']}`",
        f"- Cases: {report['summary']['case_count']}",
        f"- Passed: {report['summary']['passed_count']}",
        f"- Release gaps: {report['summary']['release_gap_count']}",
        "",
        "## Reasoning Classes",
    ]
    for case in report["cases"]:
        status = "PASS" if case["passed"] else "GAP"
        lines.append(f"- [{status}] `{case['reasoning_class']}`: {case['question']}")
        for check in case["checks"]:
            if not check["passed"]:
                lines.append(f"  Failed: `{check['id']}`")
    lines.extend(
        [
            "",
            "## GraphRAG Decision",
            f"- Decision: `{report['graphrag']['decision']}`",
            f"- {report['graphrag']['rationale']}",
            "",
            "## Boundary",
            "- Benchmark failure is evidence of a gap, not authority to add infrastructure.",
            "- The benchmark cannot decide, execute, or mutate canonical context.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_human(report: dict) -> str:
    lines = [
        "# Context OS Contextual Assessment",
        "",
        f"- Assessment: `{report['id']}`",
        f"- Goal: {report['query']['goal']}",
        f"- Mission: `{report['query']['mission_id'] or '<none>'}`",
        f"- Consumer: `{report['query']['consumer']}`",
        f"- Status: `{report['summary']['status']}`",
        f"- Read-only: {'yes' if report['read_only'] else 'no'}",
        f"- Assertions: {report['summary']['assertion_count']}",
        f"- Unknowns: {report['summary']['unknown_count']}",
        "",
        "## Assessment Boundary",
        "- Evidence, observation, interpretation, hypothesis, recommendation, Decision, authority, and canonical truth remain distinct.",
        "- Historical context and retrieved memory provide prior art; neither overrides current Governing Context.",
        "- This assessment may suggest. It cannot decide, approve, execute, or mutate canonical context.",
    ]
    sections = (
        ("Observed Facts", "observations"),
        ("Relevant Prior Art", "prior_art"),
        ("Context Changes", "context_changes"),
        ("Contradictions", "contradictions"),
        ("Interpretations", "interpretations"),
        ("Hypotheses", "hypotheses"),
        ("Recommendations", "recommendations"),
        ("Unknowns And Gaps", "unknowns"),
        ("Required Human Decisions", "required_decisions"),
        ("Additional Evidence Required", "additional_evidence"),
    )
    for title, key in sections:
        lines.extend(["", f"## {title}"])
        items = report["reasoning"][key]
        if not items:
            lines.append("- None supported by current evidence.")
            continue
        for item in items:
            lines.append(f"- `{item['id']}` [{item['epistemic_support']} / {item['support_state']}]: {item['statement']}")
            if item["evidence_refs"]:
                preview = ", ".join(f"`{ref}`" for ref in item["evidence_refs"][:3])
                lines.append(f"  Evidence: {preview}")
                if len(item["evidence_refs"]) > 3:
                    lines.append(f"  Additional evidence references in JSON: {len(item['evidence_refs']) - 3}")
    lines.extend(
        [
            "",
            "## Governing Inputs",
            f"- Activation Package: `{report['bindings']['activation_package']['id']}`",
            f"- Health Report: `{report['bindings']['health_report']['id']}`",
            f"- Memory Retrieval: `{report['bindings']['memory_retrieval']['id']}`",
            f"- Context Version evidence supplied: {report['bindings']['context_versions']['supplied_count']}",
            f"- Structured claims: {report['bindings']['reasoning_evidence']['claim_count']}",
            f"- Structured relationships: {report['bindings']['reasoning_evidence']['relationship_count']}",
            "",
            "## Invalidation",
        ]
    )
    lines.extend(f"- {condition}" for condition in report["invalidation"]["conditions"])
    return "\n".join(lines) + "\n"
