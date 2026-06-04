from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from engine.findings import Finding, ValidationContext
from rules import authority, drift, governance, hypothesis, links, mom, naming, ownership, structure, taxonomy


@dataclass(frozen=True)
class Rule:
    id: str
    category: str
    severity: str
    modes: tuple[str, ...]
    run: Callable[[ValidationContext], list[Finding]]


RULES: tuple[Rule, ...] = (
    Rule("structure.required_roots", "structure", "error", ("install-check", "pre-bootstrap", "full", "gate"), structure.required_roots),
    Rule("structure.runtime_manifest", "structure", "warn", ("install-check", "pre-bootstrap", "full", "gate"), structure.runtime_manifest),
    Rule("structure.tracked_junk_absent", "structure", "error", ("install-check", "pre-bootstrap", "full", "gate"), structure.tracked_junk_absent),
    Rule("structure.markdown_h1_present", "structure", "error", ("full", "gate"), structure.markdown_h1_present),
    Rule("structure.legacy_paths", "structure", "warn", ("full", "gate"), structure.legacy_paths),
    Rule("naming.contextos_convention", "naming", "warn", ("full", "gate"), naming.contextos_convention),
    Rule("naming.doctrine_terms", "naming", "error", ("full", "gate"), naming.doctrine_terms),
    Rule("links.relative_paths_resolve", "links", "error", ("full", "gate"), links.relative_paths_resolve),
    Rule("links.anchors_resolve", "links", "error", ("full", "gate"), links.anchors_resolve),
    Rule("links.heading_anchor_unique", "links", "warn", ("full",), links.heading_anchor_unique),
    Rule("taxonomy.ssot_filename_prefix", "taxonomy", "error", ("pre-bootstrap", "full", "gate"), taxonomy.ssot_filename_prefix),
    Rule("taxonomy.ssot_h1_matches_file", "taxonomy", "error", ("full", "gate"), taxonomy.ssot_h1_matches_file),
    Rule("taxonomy.docs_folder_prefix", "taxonomy", "warn", ("full",), taxonomy.docs_folder_prefix),
    Rule("mom.required_artifacts", "mom", "error", ("pre-bootstrap", "full", "gate"), mom.required_artifacts),
    Rule("mom.required_fields", "mom", "error", ("full", "gate"), mom.required_fields),
    Rule("mom.epic_required_sections", "mom", "error", ("full", "gate"), mom.epic_required_sections),
    Rule("ownership.ssot_owner_present", "ownership", "error", ("pre-bootstrap", "full", "gate"), ownership.ssot_owner_present),
    Rule("ownership.framework_owner_present", "ownership", "warn", ("full",), ownership.framework_owner_present),
    Rule("governance.dor_dod_present", "governance", "error", ("pre-bootstrap", "full", "gate"), governance.dor_dod_present),
    Rule("governance.agent_rules_present", "governance", "error", ("install-check", "pre-bootstrap", "full", "gate"), governance.agent_rules_present),
    Rule("authority.model_present", "authority", "error", ("pre-bootstrap", "full", "gate"), authority.model_present),
    Rule("hypothesis.product_status_fields", "hypothesis", "warn", ("full",), hypothesis.product_status_fields),
    Rule("drift.discovery_bundle_available", "drift", "info", ("full", "gate"), drift.discovery_bundle_available),
)


def categories() -> set[str]:
    return {rule.category for rule in RULES}


def rule_ids() -> set[str]:
    return {rule.id for rule in RULES}
