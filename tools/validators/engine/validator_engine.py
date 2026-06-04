from __future__ import annotations

from pathlib import Path

from engine.findings import SEVERITIES, ValidationContext, collect_markdown, make_finding, tracked_files
from engine.report_builder import build_report, exit_code_for
from engine.rule_registry import RULES
from engine.selectors import parse_rule_selector


VALID_MODES = ("install-check", "pre-bootstrap", "full", "gate")


def mode_in(rule, mode: str) -> bool:
    return mode in rule.modes or "all" in rule.modes


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


def run_rules(ctx: ValidationContext, selected_rules: set[str]) -> tuple[list, int]:
    findings: list = []
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


class ValidatorEngine:
    """Reusable Validator Engine facade for future Runtime callers."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

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
        ctx = build_context(self.root, mode, manifest, discovery)
        findings, rules_run = run_rules(ctx, selected_rules)
        exit_code = exit_code_for(mode, findings)
        return build_report(ctx, findings, rules_run, exit_code)
