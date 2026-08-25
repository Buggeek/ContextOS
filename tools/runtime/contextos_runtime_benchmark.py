#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


RUNTIME_ROOT = Path(__file__).resolve().parent
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from runtime_engine import OrganizationalContextRuntimeBenchmarkEngine  # noqa: E402
from runtime_engine.report_builder import render_human, write_json_report  # noqa: E402


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Run the internal Context OS integrated runtime benchmark.")
    result.add_argument("--root", default=".")
    result.add_argument("--goal", required=True)
    result.add_argument("--mission-id", required=True)
    result.add_argument("--consumer", default="codex")
    result.add_argument("--generated-at")
    result.add_argument("--format", choices=("human", "json"), default="human")
    result.add_argument("--json-out")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        report = OrganizationalContextRuntimeBenchmarkEngine(args.root).run(
            goal=args.goal,
            mission_id=args.mission_id,
            consumer=args.consumer,
            generated_at=args.generated_at,
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"contextos runtime benchmark: {exc}", file=sys.stderr)
        return 9
    if args.json_out:
        write_json_report(args.json_out, report)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_human(report), end="")
    return 0 if report["summary"]["release_blocker_count"] == 0 else 7


if __name__ == "__main__":
    raise SystemExit(main())
