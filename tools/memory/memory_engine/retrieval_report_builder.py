from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path


SCHEMA = "contextos.memory.retrieval_result/1"
CHECK_SCHEMA = "contextos.memory.retrieval_check/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_report(root: Path, report: dict, generated_at: str | None = None) -> dict:
    report["schema"] = SCHEMA
    report["generated_at"] = generated_at or generated_timestamp()
    report["root"] = str(root.resolve())
    return report


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _known(value: object) -> str:
    return str(value) if value is not None else "<unknown>"


def render_human(report: dict) -> str:
    if report.get("schema") == CHECK_SCHEMA:
        return render_check_human(report)
    query = report["query"]
    summary = report["summary"]
    activation = report["bindings"]["activation_package"]
    continuity = report["bindings"]["memory_continuity"]
    lines = [
        "# Context OS Memory Retrieval",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Retrieval: `{report['id']}`",
        f"- Goal: {query['goal']}",
        f"- Mission: `{query['mission_id'] or '<none>'}`",
        f"- Consumer: `{query['consumer']}`",
        f"- Purpose: {query['purpose']}",
        f"- Organizational mode: `{query['organizational_mode']}`",
        f"- Actor roles: {', '.join(query['actor_roles']) or 'none supplied'}",
        f"- Authority scope: `{query['authority_scope'] or '<none>'}`",
        f"- Read-only: {_yes_no(report['read_only'])}",
        f"- Fresh at generation: {_yes_no(report['freshness']['fresh_at_generation'])}",
        f"- Activation Package: `{activation['id']}`",
        f"- Memory Continuity: `{continuity['id']}`",
        f"- Selected candidates: {summary['selected_count']}",
        f"- Relevant candidates evaluated: {summary['relevant_candidate_count']}",
        f"- Excluded candidates: {summary['excluded_count']}",
        "",
        "## Authority Boundary",
        "- The Activation Package provides current Governing Context.",
        "- Retrieved memory is bounded prior art and never overrides current canonical context.",
        "- Selection does not prove applicability, authority, or usefulness.",
        "- Relevance is evaluated before eligibility; policy eligibility is evaluated before exposure.",
        "- Retrieved items are not silently added to Governing Context.",
        "",
        "## Retrieved Memory Candidates",
    ]
    if not report["items"]:
        lines.append("- No candidate crossed the deterministic relevance threshold.")
    for index, item in enumerate(report["items"], start=1):
        lines.extend(
            [
                f"### {index}. {item['title']}",
                f"- Memory form: `{item['memory_form']}`",
                f"- Temporal status: `{item['temporal_status']}`",
                f"- Applicability: `{item['applicability']['status']}`",
                f"- Authority now: `{item['authority']['current_authority']}`",
                f"- Retrieval eligibility: `{item['retrieval_eligibility']['retrieval_outcome']}`",
                f"- Activation eligibility: `{item['retrieval_eligibility']['activation_outcome']}`",
                f"- Why selected: {item['selection']['rationale']}",
                f"- Matched terms: {', '.join(item['selection']['matched_terms'])}",
                f"- Mission: `{item['mission_id'] or '<none>'}`",
                f"- Release: `{item['release'] or '<unknown>'}`",
                f"- Valid from: `{_known(item['temporal'].get('valid_from'))}`",
                f"- Valid to: `{_known(item['temporal'].get('valid_to'))}`",
                f"- Observed at: `{_known(item['temporal'].get('observed_at'))}`",
                f"- Supersession: `{item['supersession']['status']}`",
                f"- Current-context conflict: `{item['current_context_comparison']['status']}`",
                f"- Epistemic: `{_known(item['truth'].get('epistemic_support'))}`",
                f"- Governance: `{_known(item['truth'].get('governance_lifecycle'))}`",
                f"- Strategic belief: `{_known(item['truth'].get('strategic_belief'))}`",
                f"- Summary: {item['summary'] or '<restricted>'}",
            ]
        )
        if item.get("provenance"):
            lines.append(f"- Source: `{item['provenance']['path']}`")
            lines.append(f"- Source hash: `{item['provenance']['source_hash']}`")
        if item["supersession"].get("detail"):
            lines.append(f"- Superseded by: {item['supersession']['detail']}")

    lines.extend(["", "## Continuity Gaps"])
    for gap in report["continuity_gaps"]:
        lines.append(f"- `{gap['id']}` [{gap['status']}]: {gap['message']}")
    if not report["continuity_gaps"]:
        lines.append("- None observed.")

    lines.extend(["", "## Policy Eligibility"])
    outcomes = summary["policy_outcomes"]
    for outcome in ("normal", "elevated_authority", "excluded", "prohibited", "unknown"):
        lines.append(f"- `{outcome}`: {outcomes.get(outcome, 0)}")
    if not report["bindings"]["retention_policy_context"]["policies_supplied"]:
        lines.append("- No retention policy was supplied; relevant memory remains unknown and unexposed.")

    lines.extend(["", "## Intentional Exclusions"])
    for exclusion in report["exclusions"]["items"][:12]:
        lines.append(
            f"- `{exclusion['candidate']}`: {exclusion['reason']} "
            f"(access `{exclusion['access_outcome']}`, Retrieval `{exclusion['retrieval_outcome']}`, unresolved {exclusion['unresolved_count']}, "
            f"conflicts {exclusion['conflict_count']})"
        )
    omitted = len(report["exclusions"]["items"]) - min(12, len(report["exclusions"]["items"]))
    if omitted:
        lines.append(f"- {omitted} more exclusions are preserved in JSON.")
    if not report["exclusions"]["items"]:
        lines.append("- None.")
    relevance = report["exclusions"]["relevance"]
    lines.append(f"- Non-relevant/self candidates withheld without identity exposure: {relevance['count']}.")

    lines.extend(
        [
            "",
            "## Interpretation Limits",
            "- Historical does not mean invalid; superseded does not mean deleted.",
            "- Remembered does not mean canonical; repeated does not mean useful.",
            "- Semantic conflict with current canonical context remains unknown without governed interpretation.",
            "- Missing policy remains explicit; no deletion, archival, or forgetting occurred.",
            "",
            "## Freshness And Invalidation",
        ]
    )
    for condition in report["invalidation"]["conditions"]:
        lines.append(f"- {condition}")
    return "\n".join(lines) + "\n"


def render_check_human(report: dict) -> str:
    lines = [
        "# Context OS Memory Retrieval Check",
        "",
        f"- Schema: `{report['schema']}`",
        f"- Retrieval: `{report['retrieval']['id']}`",
        f"- Read-only: {_yes_no(report['read_only'])}",
        f"- Valid: {_yes_no(report['result']['valid'])}",
        f"- Invalidated: {_yes_no(report['result']['invalidated'])}",
        f"- Retrieval identity valid: {_yes_no(report['checks']['identity_valid'])}",
        f"- Activation Package valid: {_yes_no(report['checks']['activation_package_valid'])}",
        f"- Continuity state unchanged: {_yes_no(report['checks']['continuity_state_unchanged'])}",
        f"- Selection unchanged: {_yes_no(report['checks']['selection_unchanged'])}",
        f"- Policy context unchanged: {_yes_no(report['checks'].get('policy_context_unchanged', False))}",
        f"- Temporal basis unchanged: {_yes_no(report['checks'].get('temporal_basis_unchanged', False))}",
        "",
        "## Failed Checks",
    ]
    if report["result"]["failed_checks"]:
        lines.extend(f"- `{failure}`" for failure in report["result"]["failed_checks"])
    else:
        lines.append("- None.")
    return "\n".join(lines) + "\n"


def write_json_report(path: str | Path, report: dict) -> None:
    Path(path).write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
