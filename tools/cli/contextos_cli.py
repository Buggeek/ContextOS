from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = REPO_ROOT / "tools" / "validators"
READINESS_ROOT = REPO_ROOT / "tools" / "readiness"
BOOTSTRAP_ROOT = REPO_ROOT / "tools" / "bootstrap"
for runtime_path in (VALIDATORS_ROOT, READINESS_ROOT, BOOTSTRAP_ROOT):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

from bootstrap_engine.approval_engine import BootstrapApprovalRecordEngine, load_json as load_bootstrap_json  # noqa: E402
from bootstrap_engine.approval_report_builder import render_human as render_approval_human  # noqa: E402
from bootstrap_engine.approval_report_builder import write_json_report as write_approval_json_report  # noqa: E402
from bootstrap_engine.plan_engine import BootstrapPlanEngine  # noqa: E402
from bootstrap_engine.proposal_engine import BootstrapProposalEngine  # noqa: E402
from bootstrap_engine.proposal_report_builder import render_human as render_proposal_human  # noqa: E402
from bootstrap_engine.proposal_report_builder import write_json_report as write_proposal_json_report  # noqa: E402
from bootstrap_engine.report_builder import render_human as render_bootstrap_human  # noqa: E402
from bootstrap_engine.report_builder import write_json_report as write_bootstrap_json_report  # noqa: E402
from engine.report_builder import render_human as render_validator_human  # noqa: E402
from engine.report_builder import write_json_report as write_validator_json_report  # noqa: E402
from engine.selectors import parse_rule_selector  # noqa: E402
from engine.validator_engine import VALID_MODES, ValidatorEngine  # noqa: E402
from readiness_engine.readiness_scoring import ReadinessScoringEngine  # noqa: E402
from readiness_engine.report_builder import render_human as render_readiness_human  # noqa: E402
from readiness_engine.report_builder import write_json_report as write_readiness_json_report  # noqa: E402


VERSION = "0.3.0-cli-v0"
FORMAT_CHOICES = ("text", "human", "json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="contextos",
        description="Context OS Runtime CLI v0.",
    )
    parser.add_argument("--version", action="version", version=f"contextos {VERSION}")

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    validate = subparsers.add_parser(
        "validate",
        help="Run the Context OS Validator.",
        description="Run the Context OS Validator.",
    )
    validate.add_argument("--root", default=".", help="Repository root to validate.")
    validate.add_argument("--mode", default="full", choices=VALID_MODES, help="Validation mode.")
    validate.add_argument("--format", default="text", choices=FORMAT_CHOICES, help="Output format.")
    validate.add_argument("--rules", default=None, help="Comma-separated rule selectors.")
    validate.add_argument("--json-out", default=None, help="Write the machine report JSON to this path.")
    validate.set_defaults(handler=run_validate)

    assess = subparsers.add_parser(
        "assess",
        help="Run the Context Readiness Assessment.",
        description="Run the Context Readiness Assessment.",
    )
    assess.add_argument("--root", default=".", help="Repository root to assess.")
    assess.add_argument("--format", default="human", choices=FORMAT_CHOICES, help="Output format.")
    assess.add_argument("--json-out", default=None, help="Write the machine readiness report JSON to this path.")
    assess.set_defaults(handler=run_assess)

    init = subparsers.add_parser(
        "init",
        help="Plan guided Context OS bootstrap.",
        description="Plan guided Context OS bootstrap without modifying the repository.",
    )
    init.add_argument("--root", default=".", help="Repository root to plan bootstrap for.")
    init.add_argument("--format", default="human", choices=FORMAT_CHOICES, help="Output format.")
    init.add_argument("--json-out", default=None, help="Write the machine bootstrap plan/proposal JSON to this path.")
    init.add_argument("--proposal", action="store_true", help="Render a read-only bootstrap proposal instead of a plan.")
    init.add_argument("--approval-record", default=None, help="Render a read-only approval record draft from a proposal JSON file.")
    init.add_argument("--mission-id", default=None, help="Mission id to bind to a bootstrap proposal.")
    init.add_argument("--requested-by", default="operator", help="Requester identity for a bootstrap proposal.")
    init.add_argument("--proposal-mode", default="local", choices=("local", "project", "organization", "embedded"), help="Authority mode for a bootstrap proposal.")
    init.add_argument("--approver", action="append", default=[], help="Approver candidate for an approval record draft. May be repeated.")
    init.add_argument("--rationale", default=None, help="Rationale to include in an approval record draft.")
    init.set_defaults(handler=run_init)
    return parser


def error_payload(code: int, category: str, message: str, evidence: dict | None = None) -> dict:
    error = {
        "code": code,
        "category": category,
        "message": message,
    }
    if evidence is not None:
        error["evidence"] = evidence
    return {"error": error}


def emit_error(payload: dict, output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    error = payload["error"]
    print(f"{error['category']}: {error['message']}", file=sys.stderr)


def run_validate(args: argparse.Namespace) -> int:
    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        payload = error_payload(
            9,
            "misconfiguration",
            "Repository root does not exist or is not a directory.",
            {"root": str(root)},
        )
        emit_error(payload, args.format)
        return 9

    _selected_rules, selector_error = parse_rule_selector(args.rules)
    if selector_error:
        payload = error_payload(9, "rules", selector_error, {"rules": args.rules})
        emit_error(payload, args.format)
        return 9

    report = ValidatorEngine(root).run(
        mode=args.mode,
        rules=args.rules,
    )
    if args.json_out:
        write_validator_json_report(args.json_out, report)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_validator_human(report, args.json_out), end="")
    return report["summary"]["exit_code"]


def assessment_exit_code(report: dict) -> int:
    validator_summary = report["validator"]["summary"]
    if validator_summary["fatal"]:
        return 8
    if validator_summary["error"]:
        return 7
    return 0


def run_assess(args: argparse.Namespace) -> int:
    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        payload = error_payload(
            9,
            "misconfiguration",
            "Repository root does not exist or is not a directory.",
            {"root": str(root)},
        )
        emit_error(payload, args.format)
        return 9

    report = ReadinessScoringEngine(root).run()
    if args.json_out:
        write_readiness_json_report(args.json_out, report)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_readiness_human(report), end="")
    return assessment_exit_code(report)


def bootstrap_exit_code(report: dict) -> int:
    validator = report["validator"]
    if validator["fatal"]:
        return 8
    if validator["error"]:
        return 7
    return 0


def run_init(args: argparse.Namespace) -> int:
    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        payload = error_payload(
            9,
            "misconfiguration",
            "Repository root does not exist or is not a directory.",
            {"root": str(root)},
        )
        emit_error(payload, args.format)
        return 9

    if args.approval_record:
        try:
            proposal = load_bootstrap_json(args.approval_record)
            record = BootstrapApprovalRecordEngine(root).run(
                proposal,
                proposal_ref=args.approval_record,
                approver_candidates=args.approver,
                rationale=args.rationale,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            payload = error_payload(
                9,
                "misconfiguration",
                "Could not create bootstrap approval record draft.",
                {"proposal": args.approval_record, "error": str(exc)},
            )
            emit_error(payload, args.format)
            return 9
        if args.json_out:
            write_approval_json_report(args.json_out, record)
        if args.format == "json":
            print(json.dumps(record, indent=2, sort_keys=True))
        else:
            print(render_approval_human(record), end="")
        return 0

    report = BootstrapPlanEngine(root).run()
    if args.proposal:
        proposal = BootstrapProposalEngine(root).run(
            report,
            mission_id=args.mission_id or "V04-BOOTSTRAP-PROPOSAL-CLI-001",
            requested_by=args.requested_by,
            mode=args.proposal_mode,
        )
        if args.json_out:
            write_proposal_json_report(args.json_out, proposal)
        if args.format == "json":
            print(json.dumps(proposal, indent=2, sort_keys=True))
        else:
            print(render_proposal_human(proposal), end="")
        return bootstrap_exit_code(report)

    if args.json_out:
        write_bootstrap_json_report(args.json_out, report)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_bootstrap_human(report), end="")
    return bootstrap_exit_code(report)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 0
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
