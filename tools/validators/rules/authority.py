from __future__ import annotations

from engine.findings import ValidationContext, make_finding, read_text


def model_present(ctx: ValidationContext) -> list:
    rel = "docs/3.x_operation/3.6_COS_Human_Agent_Authority_Model.md"
    path = ctx.root / rel
    if not path.exists():
        return [
            make_finding(
                "authority.model_present",
                "error",
                "Human-Agent Authority Model is missing.",
                rel,
                suggested_fix="Restore the authority model document.",
            )
        ]
    text = read_text(path)
    missing = [level for level in ("L0", "L1", "L2", "L3", "L4", "L5") if level not in text]
    if missing:
        return [
            make_finding(
                "authority.model_present",
                "error",
                "Human-Agent Authority Model does not declare every autonomy level.",
                rel,
                evidence={"missing_levels": missing},
                suggested_fix="Declare autonomy levels L0 through L5.",
            )
        ]
    return []
