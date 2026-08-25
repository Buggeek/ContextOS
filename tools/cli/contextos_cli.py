from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = REPO_ROOT / "tools" / "validators"
READINESS_ROOT = REPO_ROOT / "tools" / "readiness"
BOOTSTRAP_ROOT = REPO_ROOT / "tools" / "bootstrap"
ACTIVATION_ROOT = REPO_ROOT / "tools" / "activation"
HEALTH_ROOT = REPO_ROOT / "tools" / "health"
MEMORY_ROOT = REPO_ROOT / "tools" / "memory"
REASONING_ROOT = REPO_ROOT / "tools" / "reasoning"
for runtime_path in (VALIDATORS_ROOT, READINESS_ROOT, BOOTSTRAP_ROOT, ACTIVATION_ROOT, HEALTH_ROOT, MEMORY_ROOT, REASONING_ROOT):
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402
from activation_engine.report_builder import render_human as render_activation_human  # noqa: E402
from activation_engine.report_builder import write_json_report as write_activation_json_report  # noqa: E402
from bootstrap_engine.acceptance_engine import BootstrapApprovalAcceptanceEngine  # noqa: E402
from bootstrap_engine.acceptance_report_builder import render_human as render_acceptance_human  # noqa: E402
from bootstrap_engine.acceptance_report_builder import write_json_report as write_acceptance_json_report  # noqa: E402
from bootstrap_engine.apply_engine import BootstrapApplyEngine  # noqa: E402
from bootstrap_engine.apply_report_builder import render_human as render_apply_human  # noqa: E402
from bootstrap_engine.apply_report_builder import write_json_report as write_apply_json_report  # noqa: E402
from bootstrap_engine.approval_engine import BootstrapApprovalRecordEngine, load_json as load_bootstrap_json  # noqa: E402
from bootstrap_engine.approval_report_builder import render_human as render_approval_human  # noqa: E402
from bootstrap_engine.approval_report_builder import write_json_report as write_approval_json_report  # noqa: E402
from bootstrap_engine.plan_engine import BootstrapPlanEngine  # noqa: E402
from bootstrap_engine.preflight_engine import BootstrapApplyPreflightEngine  # noqa: E402
from bootstrap_engine.preflight_report_builder import render_human as render_preflight_human  # noqa: E402
from bootstrap_engine.preflight_report_builder import write_json_report as write_preflight_json_report  # noqa: E402
from bootstrap_engine.proposal_engine import BootstrapProposalEngine  # noqa: E402
from bootstrap_engine.proposal_report_builder import render_human as render_proposal_human  # noqa: E402
from bootstrap_engine.proposal_report_builder import write_json_report as write_proposal_json_report  # noqa: E402
from bootstrap_engine.report_builder import render_human as render_bootstrap_human  # noqa: E402
from bootstrap_engine.report_builder import write_json_report as write_bootstrap_json_report  # noqa: E402
from engine.report_builder import render_human as render_validator_human  # noqa: E402
from engine.report_builder import write_json_report as write_validator_json_report  # noqa: E402
from engine.selectors import parse_rule_selector  # noqa: E402
from engine.validator_engine import VALID_MODES, ValidatorEngine  # noqa: E402
from health_engine.health_engine import ContextHealthEngine  # noqa: E402
from health_engine.report_builder import render_human as render_health_human  # noqa: E402
from health_engine.report_builder import write_json_report as write_health_json_report  # noqa: E402
from memory_engine.retrieval_engine import MemoryRetrievalEngine  # noqa: E402
from memory_engine.retrieval_report_builder import render_human as render_memory_human  # noqa: E402
from memory_engine.retrieval_report_builder import write_json_report as write_memory_json_report  # noqa: E402
from readiness_engine.readiness_scoring import ReadinessScoringEngine  # noqa: E402
from readiness_engine.report_builder import render_human as render_readiness_human  # noqa: E402
from readiness_engine.report_builder import write_json_report as write_readiness_json_report  # noqa: E402
from reasoning_engine import ContextualAssessmentEngine  # noqa: E402
from reasoning_engine.report_builder import render_check_human as render_reasoning_check_human  # noqa: E402
from reasoning_engine.report_builder import render_human as render_reasoning_human  # noqa: E402
from reasoning_engine.report_builder import write_json_report as write_reasoning_json_report  # noqa: E402


VERSION = "0.9.0-cli-v0"
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
    init.add_argument("--json-out", default=None, help="Write the machine bootstrap report JSON to this path.")
    init.add_argument("--proposal", action="store_true", help="Render a read-only bootstrap proposal instead of a plan.")
    init.add_argument("--approval-record", default=None, help="Render a read-only approval record draft from a proposal JSON file.")
    init.add_argument("--accept-approval", default=None, help="Accept a bootstrap approval record draft without applying changes.")
    init.add_argument("--preflight", default=None, help="Run read-only apply preflight from an accepted decision JSON file.")
    init.add_argument("--apply", default=None, help="Run governed create-only bootstrap apply from a preflight JSON file.")
    init.add_argument("--confirm-apply", action="store_true", help="Explicitly confirm create-only bootstrap apply.")
    init.add_argument("--confirmed-by", default=None, help="Explicit human identity confirming apply.")
    init.add_argument("--confirmed-role", default=None, help="Human authority role confirming apply.")
    init.add_argument("--confirmed-preflight-id", default=None, help="Preflight id explicitly bound to apply confirmation.")
    init.add_argument("--confirmed-preflight-hash", default=None, help="Preflight identity hash explicitly bound to apply confirmation.")
    init.add_argument("--mission-id", default=None, help="Mission id to bind to a bootstrap proposal.")
    init.add_argument("--requested-by", default="operator", help="Requester identity for a bootstrap proposal.")
    init.add_argument("--proposal-mode", default="local", choices=("local", "project", "organization", "embedded"), help="Authority mode for a bootstrap proposal.")
    init.add_argument("--approver", action="append", default=[], help="Approver candidate for an approval record draft. May be repeated.")
    init.add_argument("--accepted-by", default=None, help="Explicit human identity accepting an approval record draft.")
    init.add_argument("--accepted-role", default=None, help="Human authority role accepting an approval record draft.")
    init.add_argument("--rationale", default=None, help="Rationale to include in an approval record draft or accepted decision.")
    init.set_defaults(handler=run_init)

    activate = subparsers.add_parser(
        "activate",
        help="Create or check a read-only Context Activation Package.",
        description="Create or check a read-only Context Activation Package.",
    )
    activate.add_argument("--root", default=".", help="Repository root to activate context from.")
    activate.add_argument("--consumer", default="human", help="Consumer requesting working context, such as human, codex, claude_code, or ide_assistant.")
    activate.add_argument("--goal", default=None, help="Goal statement to bind the activation package to.")
    activate.add_argument("--mission-id", default=None, help="Mission id to bind the activation package to.")
    activate.add_argument("--max-artifacts", type=int, default=12, help="Maximum canonical artifacts to include.")
    activate.add_argument("--check-package", default=None, help="Check an existing activation package JSON for source drift and gate validity.")
    activate.add_argument("--check-handoff", default=None, help="Check an existing activation handoff JSON for source drift, package binding, and gate validity.")
    activate.add_argument("--handoff", action="store_true", help="Render a compact handoff derived from a valid activation package.")
    activate.add_argument("--format", default="human", choices=FORMAT_CHOICES, help="Output format.")
    activate.add_argument("--json-out", default=None, help="Write the machine activation package JSON to this path.")
    activate.set_defaults(handler=run_activate)

    health = subparsers.add_parser(
        "health",
        help="Report Context Health & Learning.",
        description="Report Context Health & Learning without modifying organizational context.",
    )
    health.add_argument("--root", default=".", help="Repository root to assess for Context Health.")
    health.add_argument("--format", default="human", choices=FORMAT_CHOICES, help="Output format.")
    health.add_argument("--mission-use-evidence", default=None, help="Optional contextos.mission.context_use_evidence/1 JSON report.")
    health.add_argument("--json-out", default=None, help="Write the machine Health report JSON to this path.")
    health.set_defaults(handler=run_health)

    memory = subparsers.add_parser(
        "memory",
        help="Retrieve bounded Organizational Memory prior art.",
        description="Retrieve or check read-only Organizational Memory candidates without overriding current context.",
    )
    memory.add_argument("--root", default=".", help="Repository root containing governed Organizational Memory records.")
    memory.add_argument("--goal", default=None, help="Goal that bounds memory retrieval.")
    memory.add_argument("--mission-id", default=None, help="Mission id that binds memory retrieval.")
    memory.add_argument("--question", default=None, help="Optional bounded organizational question.")
    memory.add_argument("--consumer", default="human", help="Consumer requesting prior art, such as human, codex, or claude_code.")
    memory.add_argument("--purpose", default=None, help="Exact purpose for which memory is requested; defaults visibly to the question or Goal.")
    memory.add_argument("--organizational-mode", default="local", choices=("local", "project", "organization", "embedded"), help="Organizational authority mode for policy resolution.")
    memory.add_argument("--actor-role", action="append", default=[], help="Current actor role considered by Retention Resolution. May be repeated.")
    memory.add_argument("--authority-scope", default=None, help="Exact authority scope bound to Retrieval; this does not grant authority.")
    memory.add_argument("--retention-policy", action="append", default=[], help="JSON file containing one contextos.memory.retention_policy/1 object, a list, or a policies list. May be repeated.")
    memory.add_argument("--memory-metadata", default=None, help="JSON file containing defaults and per-memory metadata for Retention Resolution.")
    memory.add_argument("--context-version", action="append", default=[], help="Preserved contextos.context.version/1 JSON object. May be repeated.")
    memory.add_argument("--evaluation-time", default=None, help="Explicit ISO-8601 temporal basis for policy resolution and saved-result checks.")
    memory.add_argument("--limit", type=int, default=12, help="Maximum memory candidates to return (1-50).")
    memory.add_argument("--check-retrieval", default=None, help="Check a saved contextos.memory.retrieval_result/1 JSON report.")
    memory.add_argument("--format", default="human", choices=FORMAT_CHOICES, help="Output format.")
    memory.add_argument("--json-out", default=None, help="Write the machine Memory retrieval report JSON to this path.")
    memory.set_defaults(handler=run_memory)

    reason = subparsers.add_parser(
        "reason",
        help="Create or check a governed Contextual Assessment.",
        description="Create or check a read-only evidence-backed Contextual Assessment.",
    )
    reason.add_argument("--root", default=".", help="Repository root to assess contextually.")
    reason.add_argument("--goal", default=None, help="Goal that bounds contextual reasoning.")
    reason.add_argument("--mission-id", default=None, help="Mission id to bind to the Assessment.")
    reason.add_argument("--question", default=None, help="Optional bounded organizational question.")
    reason.add_argument("--consumer", default="human", help="Consumer receiving the Assessment.")
    reason.add_argument("--purpose", default=None, help="Exact purpose for the Assessment.")
    reason.add_argument("--organizational-mode", default="local", choices=("local", "project", "organization", "embedded"), help="Organizational authority mode.")
    reason.add_argument("--actor-role", action="append", default=[], help="Actor role considered by policy resolution. May be repeated.")
    reason.add_argument("--authority-scope", default=None, help="Exact authority scope; this does not grant authority.")
    reason.add_argument("--retention-policy", action="append", default=[], help="Authorized retention-policy JSON. May be repeated.")
    reason.add_argument("--memory-metadata", default=None, help="Authorized per-memory metadata JSON.")
    reason.add_argument("--context-version", action="append", default=[], help="Exact contextos.context.version/1 JSON. May be repeated.")
    reason.add_argument("--mission-use-evidence", default=None, help="Optional contextos.mission.context_use_evidence/1 JSON.")
    reason.add_argument("--reasoning-evidence", default=None, help="Optional contextos.reasoning.evidence_set/1 JSON.")
    reason.add_argument("--focus-entity", action="append", default=[], help="Entity from which bounded relationship traversal begins. May be repeated.")
    reason.add_argument("--evaluation-time", default=None, help="Explicit temporal basis for policy evaluation.")
    reason.add_argument("--memory-limit", type=int, default=12, help="Maximum policy-authorized Memory candidates (1-50).")
    reason.add_argument("--check-assessment", default=None, help="Check a saved contextos.reasoning.assessment/1 JSON report.")
    reason.add_argument("--format", default="human", choices=FORMAT_CHOICES, help="Output format.")
    reason.add_argument("--json-out", default=None, help="Write the full machine report JSON to this path.")
    reason.set_defaults(handler=run_reason)
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

    if args.apply:
        try:
            preflight = load_bootstrap_json(args.apply)
            result = BootstrapApplyEngine(root).run(
                preflight,
                preflight_ref=args.apply,
                confirm_apply=args.confirm_apply,
                confirmed_by=args.confirmed_by or "",
                confirmed_role=args.confirmed_role or "",
                confirmed_preflight_id=args.confirmed_preflight_id,
                confirmed_preflight_hash=args.confirmed_preflight_hash,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            payload = error_payload(
                9,
                "misconfiguration",
                "Could not run bootstrap apply.",
                {"preflight": args.apply, "error": str(exc)},
            )
            emit_error(payload, args.format)
            return 9
        if args.json_out:
            write_apply_json_report(args.json_out, result)
        if args.format == "json":
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print(render_apply_human(result), end="")
        return 0 if result["result"]["success"] else 7

    if args.preflight:
        try:
            accepted_decision = load_bootstrap_json(args.preflight)
            report = BootstrapApplyPreflightEngine(root).run(
                accepted_decision,
                accepted_decision_ref=args.preflight,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            payload = error_payload(
                9,
                "misconfiguration",
                "Could not run bootstrap apply preflight.",
                {"accepted_decision": args.preflight, "error": str(exc)},
            )
            emit_error(payload, args.format)
            return 9
        if args.json_out:
            write_preflight_json_report(args.json_out, report)
        if args.format == "json":
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(render_preflight_human(report), end="")
        return 0 if report["eligibility"]["eligible_for_apply"] else 7

    if args.accept_approval:
        try:
            record = load_bootstrap_json(args.accept_approval)
            decision = BootstrapApprovalAcceptanceEngine(root).run(
                record,
                approval_record_ref=args.accept_approval,
                accepted_by=args.accepted_by or "",
                accepted_role=args.accepted_role or "",
                rationale=args.rationale,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            payload = error_payload(
                9,
                "misconfiguration",
                "Could not accept bootstrap approval record.",
                {"approval_record": args.accept_approval, "error": str(exc)},
            )
            emit_error(payload, args.format)
            return 9
        if args.json_out:
            write_acceptance_json_report(args.json_out, decision)
        if args.format == "json":
            print(json.dumps(decision, indent=2, sort_keys=True))
        else:
            print(render_acceptance_human(decision), end="")
        return 0

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


def activation_exit_code(report: dict) -> int:
    if report.get("schema") == "contextos.activation.handoff_check/1":
        return 0 if report["result"]["valid"] else 7
    if report.get("schema") == "contextos.activation.handoff/1":
        return 0 if report["result"]["handoff_ready"] else 7
    if report.get("schema") == "contextos.activation.package_check/1":
        return 0 if report["result"]["valid"] else 7
    validator_summary = report["validator"]["summary"]
    if validator_summary["fatal"]:
        return 8
    if validator_summary["error"]:
        return 7
    return 0


def run_activate(args: argparse.Namespace) -> int:
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
    engine = ContextActivationPackageEngine(root)

    try:
        if args.check_handoff:
            handoff = load_bootstrap_json(args.check_handoff)
            report = engine.check_handoff(handoff)
        elif args.check_package:
            package = load_bootstrap_json(args.check_package)
            if args.handoff:
                report = engine.build_handoff(package, package_ref=args.check_package)
            else:
                report = engine.check_package(package)
        else:
            if not args.goal:
                payload = error_payload(
                    9,
                    "misconfiguration",
                    "Activation package requires --goal unless --check-package is used.",
                    {"goal": args.goal},
                )
                emit_error(payload, args.format)
                return 9
            report = engine.run(
                goal=args.goal,
                consumer=args.consumer,
                mission_id=args.mission_id,
                max_artifacts=args.max_artifacts,
            )
            if args.handoff:
                report = engine.build_handoff(report)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        payload = error_payload(
            9,
            "misconfiguration",
            "Could not create or check activation package.",
            {"error": str(exc)},
        )
        emit_error(payload, args.format)
        return 9

    if args.json_out:
        write_activation_json_report(args.json_out, report)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_activation_human(report), end="")
    return activation_exit_code(report)


def health_exit_code(report: dict) -> int:
    validator_summary = report["evidence_sources"]["validator"]["summary"]
    if validator_summary["fatal"]:
        return 8
    if validator_summary["error"]:
        return 7
    return 0


def run_health(args: argparse.Namespace) -> int:
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

    try:
        mission_use_evidence = (
            load_bootstrap_json(args.mission_use_evidence)
            if args.mission_use_evidence
            else None
        )
        report = ContextHealthEngine(root).run(mission_use_evidence=mission_use_evidence)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        payload = error_payload(
            9,
            "misconfiguration",
            "Could not create Context Health report.",
            {"mission_use_evidence": args.mission_use_evidence, "error": str(exc)},
        )
        emit_error(payload, args.format)
        return 9

    if args.json_out:
        write_health_json_report(args.json_out, report)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_health_human(report), end="")
    return health_exit_code(report)


def run_memory(args: argparse.Namespace) -> int:
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

    engine = MemoryRetrievalEngine(root)
    try:
        policies = []
        for policy_path in args.retention_policy:
            payload = load_bootstrap_json(policy_path)
            if isinstance(payload, list):
                policies.extend(payload)
            elif isinstance(payload, dict) and payload.get("schema") == "contextos.memory.retention_policy/1":
                policies.append(payload)
            elif isinstance(payload, dict) and isinstance(payload.get("policies"), list):
                policies.extend(payload["policies"])
            else:
                raise ValueError(f"Retention policy file has no supported policy shape: {policy_path}")
        metadata = load_bootstrap_json(args.memory_metadata) if args.memory_metadata else {}
        if not isinstance(metadata, dict):
            raise ValueError("Memory metadata input must be a JSON object.")
        context_versions = []
        for version_path in args.context_version:
            version = load_bootstrap_json(version_path)
            if not isinstance(version, dict) or version.get("schema") != "contextos.context.version/1":
                raise ValueError(f"Context Version file must use contextos.context.version/1: {version_path}")
            context_versions.append(version)
        if args.check_retrieval:
            saved = load_bootstrap_json(args.check_retrieval)
            report = engine.check_retrieval(
                saved,
                retention_policies=policies,
                memory_metadata_by_id=metadata,
                context_versions=context_versions,
                evaluation_time=args.evaluation_time,
            )
        else:
            if not args.goal:
                payload = error_payload(
                    9,
                    "misconfiguration",
                    "Memory retrieval requires --goal unless --check-retrieval is used.",
                    {"goal": args.goal},
                )
                emit_error(payload, args.format)
                return 9
            report = engine.run(
                goal=args.goal,
                mission_id=args.mission_id,
                question=args.question,
                consumer=args.consumer,
                limit=args.limit,
                purpose=args.purpose,
                organizational_mode=args.organizational_mode,
                actor_roles=args.actor_role,
                authority_scope=args.authority_scope,
                retention_policies=policies,
                memory_metadata_by_id=metadata,
                context_versions=context_versions,
                evaluation_time=args.evaluation_time,
            )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        payload = error_payload(
            9,
            "misconfiguration",
            "Could not retrieve or check Organizational Memory.",
            {"retrieval": args.check_retrieval, "error": str(exc)},
        )
        emit_error(payload, args.format)
        return 9

    if args.json_out:
        write_memory_json_report(args.json_out, report)

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_memory_human(report), end="")

    if report.get("schema") == "contextos.memory.retrieval_check/1":
        return 0 if report["result"]["valid"] else 7
    validator = report["activation_package"]["validator"]["summary"]
    if validator["fatal"]:
        return 8
    if validator["error"]:
        return 7
    return 0


def run_reason(args: argparse.Namespace) -> int:
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

    try:
        policies = []
        for policy_path in args.retention_policy:
            policy_payload = load_bootstrap_json(policy_path)
            if isinstance(policy_payload, list):
                policies.extend(policy_payload)
            elif isinstance(policy_payload, dict) and policy_payload.get("schema") == "contextos.memory.retention_policy/1":
                policies.append(policy_payload)
            elif isinstance(policy_payload, dict) and isinstance(policy_payload.get("policies"), list):
                policies.extend(policy_payload["policies"])
            else:
                raise ValueError(f"Retention policy file has no supported policy shape: {policy_path}")
        metadata = load_bootstrap_json(args.memory_metadata) if args.memory_metadata else {}
        if not isinstance(metadata, dict):
            raise ValueError("Memory metadata input must be a JSON object.")

        engine = ContextualAssessmentEngine(root)
        if args.check_assessment:
            saved = load_bootstrap_json(args.check_assessment)
            report = engine.check_assessment(
                saved,
                retention_policies=policies,
                memory_metadata_by_id=metadata,
            )
        else:
            if not args.goal:
                raise ValueError("Contextual Assessment requires --goal unless --check-assessment is used.")
            context_versions = []
            for version_path in args.context_version:
                version = load_bootstrap_json(version_path)
                if not isinstance(version, dict) or version.get("schema") != "contextos.context.version/1":
                    raise ValueError(f"Context Version file must use contextos.context.version/1: {version_path}")
                context_versions.append(version)
            mission_use = load_bootstrap_json(args.mission_use_evidence) if args.mission_use_evidence else None
            reasoning_evidence = load_bootstrap_json(args.reasoning_evidence) if args.reasoning_evidence else None
            report = engine.run(
                goal=args.goal,
                mission_id=args.mission_id,
                consumer=args.consumer,
                question=args.question,
                purpose=args.purpose,
                organizational_mode=args.organizational_mode,
                actor_roles=args.actor_role,
                authority_scope=args.authority_scope,
                retention_policies=policies,
                memory_metadata_by_id=metadata,
                context_versions=context_versions,
                mission_use_evidence=mission_use,
                reasoning_evidence=reasoning_evidence,
                focus_entities=args.focus_entity,
                memory_limit=args.memory_limit,
                evaluation_time=args.evaluation_time,
            )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        payload = error_payload(
            9,
            "misconfiguration",
            "Could not create or check Contextual Assessment.",
            {"assessment": args.check_assessment, "error": str(exc)},
        )
        emit_error(payload, args.format)
        return 9

    if args.json_out:
        write_reasoning_json_report(args.json_out, report)
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    elif report["schema"] == "contextos.reasoning.assessment_check/1":
        print(render_reasoning_check_human(report), end="")
    else:
        print(render_reasoning_human(report), end="")

    if report["schema"] == "contextos.reasoning.assessment_check/1":
        return 0 if report["result"]["valid"] else 7
    validator = report["evidence"]["memory_retrieval"]["activation_package"]["validator"]["summary"]
    if validator["fatal"]:
        return 8
    if validator["error"]:
        return 7
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 0
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
