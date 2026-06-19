#!/usr/bin/env python3
"""Context OS Repository Inventory report generator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

READINESS_ROOT = Path(__file__).resolve().parent
if str(READINESS_ROOT) not in sys.path:
    sys.path.insert(0, str(READINESS_ROOT))

from inventory_engine.report_builder import render_human, write_json_report  # noqa: E402
from inventory_engine.repository_inventory import RepositoryInventoryEngine  # noqa: E402


VALID_FORMATS = ("human", "json")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Context OS Repository Inventory")
    parser.add_argument("--root", default=".", help="Repository root to inventory.")
    parser.add_argument("--format", default="human", choices=VALID_FORMATS, help="Output format.")
    parser.add_argument("--json-out", default=None, help="Write the machine report JSON to this path.")
    return parser.parse_args(argv)


def error_payload(code: int, category: str, message: str, evidence: dict | None = None) -> dict:
    error = {
        "code": code,
        "category": category,
        "message": message,
    }
    if evidence is not None:
        error["evidence"] = evidence
    return {"error": error}


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        payload = error_payload(
            9,
            "misconfiguration",
            "Repository root does not exist or is not a directory.",
            {"root": str(root)},
        )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 9

    report = RepositoryInventoryEngine(root).run()
    if args.json_out:
        write_json_report(args.json_out, report)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_human(report, args.json_out), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
