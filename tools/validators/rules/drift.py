from __future__ import annotations

from engine.findings import ValidationContext, make_finding, normalize_rel


def discovery_bundle_available(ctx: ValidationContext) -> list:
    if ctx.discovery is None:
        return [
            make_finding(
                "drift.discovery_bundle_available",
                "info",
                "No Discovery output bundle supplied; drift validation skipped.",
                evidence={"input": "--discovery"},
            )
        ]
    if not ctx.discovery.exists():
        return [
            make_finding(
                "drift.discovery_bundle_available",
                "error",
                "Discovery output bundle path does not exist.",
                normalize_rel(ctx.discovery),
                evidence={"input": str(ctx.discovery)},
                suggested_fix="Provide an existing Discovery bundle path or omit --discovery.",
            )
        ]
    return [
        make_finding(
            "drift.discovery_bundle_available",
            "info",
            "Discovery output bundle supplied; semantic drift checks are deferred in v0.",
            normalize_rel(ctx.discovery),
            evidence={"input": str(ctx.discovery)},
        )
    ]
