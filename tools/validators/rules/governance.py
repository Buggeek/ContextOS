from __future__ import annotations

from engine.findings import ValidationContext, make_finding, normalize_rel, ssot_tree_roots


def dor_dod_present(ctx: ValidationContext) -> list:
    findings = []
    for tree in ssot_tree_roots(ctx.root):
        tree_rel = normalize_rel(tree.relative_to(ctx.root))
        for filename in ("G.1_Definition_of_Ready.md", "G.2_Definition_of_Done.md"):
            if not (tree / filename).exists():
                findings.append(
                    make_finding(
                        "governance.dor_dod_present",
                        "error",
                        "SSOT tree is missing a governance gate artifact.",
                        f"{tree_rel}/{filename}",
                        evidence={"ssot_tree": tree_rel, "required": filename},
                        suggested_fix="Create both G.1 Definition of Ready and G.2 Definition of Done.",
                    )
                )
    return findings


def agent_rules_present(ctx: ValidationContext) -> list:
    if (ctx.root / "ops" / "AGENT_RULES.md").exists():
        return []
    return [
        make_finding(
            "governance.agent_rules_present",
            "error",
            "Agent-facing governance rules are missing.",
            "ops/AGENT_RULES.md",
            suggested_fix="Restore ops/AGENT_RULES.md.",
        )
    ]
