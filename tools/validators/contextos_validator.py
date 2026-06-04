#!/usr/bin/env python3
"""Context OS Validator Engine v0 CLI wrapper."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from engine.report_builder import SCHEMA, render_human, write_json_report
from engine.rule_registry import RULES
from engine.selectors import parse_rule_selector
from engine.validator_engine import VALID_MODES, ValidatorEngine


VALID_FORMATS = ("human", "json")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Context OS Validator Engine v0")
    parser.add_argument("--root", default=".", help="Repository root to validate.")
    parser.add_argument("--mode", default="full", choices=VALID_MODES, help="Validation mode.")
    parser.add_argument("--format", default="human", choices=VALID_FORMATS, help="Output format.")
    parser.add_argument("--rules", default=None, help="Comma-separated rule selectors, e.g. links.*,mom.*,-links.anchors_resolve.")
    parser.add_argument("--manifest", default=None, help="Runtime manifest path. Defaults to .contextos/manifest.yaml.")
    parser.add_argument("--discovery", default=None, help="Optional Discovery output bundle path.")
    parser.add_argument("--json-out", default=None, help="Write the machine report JSON to this path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        error_report = {
            "error": {
                "code": 9,
                "category": "misconfiguration",
                "message": "Repository root does not exist or is not a directory.",
                "evidence": {"root": str(root)},
            }
        }
        print(json.dumps(error_report, indent=2, sort_keys=True))
        return 9

    _selected_rules, selector_error = parse_rule_selector(args.rules)
    if selector_error:
        error_report = {
            "error": {
                "code": 9,
                "category": "rules",
                "message": selector_error,
                "evidence": {"rules": args.rules},
            }
        }
        print(json.dumps(error_report, indent=2, sort_keys=True))
        return 9

    report = ValidatorEngine(root).run(
        mode=args.mode,
        rules=args.rules,
        manifest=args.manifest,
        discovery=args.discovery,
    )

    if args.json_out:
        write_json_report(args.json_out, report)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_human(report, args.json_out), end="")
    return report["summary"]["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
