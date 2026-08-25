from __future__ import annotations

import sys
from pathlib import Path

from engine.findings import Finding, SEVERITIES, ValidationContext, collect_markdown, make_finding, tracked_files
from engine.report_builder import build_report, exit_code_for
from engine.rule_registry import RULES
from engine.selectors import parse_rule_selector


VALID_MODES = ("install-check", "pre-bootstrap", "full", "gate")

ADOPTION_ROOT = Path(__file__).resolve().parents[2] / "adoption"
if str(ADOPTION_ROOT) not in sys.path:
    sys.path.insert(0, str(ADOPTION_ROOT))

from adoption_engine import load_adoption_profile  # noqa: E402


def mode_in(rule, mode: str) -> bool:
    return mode in rule.modes or "all" in rule.modes


def build_context(
    root: Path,
    mode: str,
    manifest: str | None,
    discovery: str | None,
    adoption_profile=None,
) -> ValidationContext:
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
        adoption_profile=adoption_profile,
    )


def _profile_finding(finding: Finding, decision: dict, profile) -> Finding:
    severity = finding.severity
    if decision["enforcement"] == "advisory" and severity in {"error", "fatal"}:
        severity = "warn"
    evidence = dict(finding.evidence or {})
    evidence["adoption_profile"] = {
        "id": profile.id,
        "identity_hash": profile.identity_hash,
        "applicability": decision["applicability"],
        "enforcement": decision["enforcement"],
        "equivalent_control_refs": decision.get("equivalent_control_refs", []),
        "original_severity": finding.severity,
    }
    return Finding(
        rule=finding.rule,
        severity=severity,
        message=finding.message,
        path=finding.path,
        line=finding.line,
        anchor=finding.anchor,
        evidence=evidence,
        suggested_fix=finding.suggested_fix,
    )


def run_rules(ctx: ValidationContext, selected_rules: set[str]) -> tuple[list, int, list[dict]]:
    findings: list = []
    rules_run = 0
    rule_results: list[dict] = []
    for rule in sorted(RULES, key=lambda item: item.id):
        if rule.id not in selected_rules or not mode_in(rule, ctx.mode):
            continue
        rules_run += 1
        decision = ctx.adoption_profile.rule_decision(rule.id) if ctx.adoption_profile else None
        if decision and decision["applicability"] in {"mapped_equivalent", "not_applicable", "unknown"}:
            rule_results.append(
                {
                    "rule": rule.id,
                    "status": decision["applicability"],
                    "enforcement": decision["enforcement"],
                    "rationale": decision["rationale"],
                    "equivalent_control_refs": decision.get("equivalent_control_refs", []),
                    "gap": bool(decision.get("gap", decision["applicability"] == "unknown")),
                    "finding_count": 0,
                }
            )
            continue
        try:
            produced = rule.run(ctx)
            if decision:
                produced = [_profile_finding(finding, decision, ctx.adoption_profile) for finding in produced]
            findings.extend(produced)
            result_status = "violated" if produced else "passed"
            if produced and all(finding.message.lower().startswith(("could not inspect", "could not determine")) for finding in produced):
                result_status = "unknown"
            rule_results.append(
                {
                    "rule": rule.id,
                    "status": result_status,
                    "enforcement": decision["enforcement"] if decision else rule.severity,
                    "rationale": decision["rationale"] if decision else "Context OS native validation behavior.",
                    "equivalent_control_refs": decision.get("equivalent_control_refs", []) if decision else [],
                    "gap": bool(produced),
                    "finding_count": len(produced),
                }
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            findings.append(
                make_finding(
                    rule.id,
                    "fatal",
                    f"Rule failed to execute: {exc}",
                    evidence={"exception": exc.__class__.__name__},
                )
            )
            rule_results.append(
                {
                    "rule": rule.id,
                    "status": "violated",
                    "enforcement": "blocking",
                    "rationale": "Rule execution failed.",
                    "equivalent_control_refs": [],
                    "gap": True,
                    "finding_count": 1,
                }
            )
    findings.sort(key=lambda f: (SEVERITIES.index(f.severity), f.rule, f.path or "", f.line or 0, f.message))
    return findings, rules_run, rule_results


class ValidatorEngine:
    """Reusable Validator Engine facade for future Runtime callers."""

    def __init__(self, root: str | Path = ".", adoption_profile=None) -> None:
        self.root = Path(root)
        self.adoption_profile = load_adoption_profile(adoption_profile)

    def run(
        self,
        mode: str = "full",
        rules: str | None = None,
        manifest: str | None = None,
        discovery: str | None = None,
    ) -> dict:
        selected_rules, selector_error = parse_rule_selector(rules)
        if selector_error:
            raise ValueError(selector_error)
        ctx = build_context(self.root, mode, manifest, discovery, self.adoption_profile)
        findings, rules_run, rule_results = run_rules(ctx, selected_rules)
        exit_code = exit_code_for(mode, findings)
        return build_report(ctx, findings, rules_run, exit_code, rule_results)
