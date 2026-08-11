from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from bootstrap_engine.acceptance_engine import (
    accepted_decision_id,
    accepted_decision_payload,
    action_summary,
    approval_file_hash,
    role_satisfies,
)
from bootstrap_engine.approval_engine import approval_identity_payload, approval_record_id, load_json, proposal_file_hash
from bootstrap_engine.proposal_engine import (
    BootstrapProposalEngine,
    canonical_json,
    generated_timestamp,
    identity_payload,
    path_state,
    stable_hash,
)


TOOLS_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from engine.validator_engine import ValidatorEngine  # noqa: E402


SCHEMA = "contextos.bootstrap.apply_preflight/1"


def preflight_payload(report: dict) -> dict:
    return {
        "schema": report["schema"],
        "accepted_decision": report["accepted_decision"],
        "approval_record": report["approval_record"],
        "proposal": report["proposal"],
        "authority": report["authority"],
        "frozen_mutation_set": report["frozen_mutation_set"],
        "eligibility": report["eligibility"],
    }


def preflight_id(report: dict) -> str:
    return f"bootstrap.apply_preflight.{stable_hash(preflight_payload(report))[:16]}"


def accepted_file_hash(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_ref(root: Path, ref: str | None, label: str) -> dict:
    if not ref:
        raise ValueError(f"Apply preflight requires preserved {label} file reference.")
    path = Path(ref)
    if not path.is_absolute():
        path = root / path
    return load_json(path)


def executable_actions(proposal: dict) -> list[dict]:
    actions = []
    for action in proposal.get("actions", []):
        if action["class"] in {"automatic", "approval_required"} and action["status"] == "required":
            actions.append(
                {
                    "id": action["id"],
                    "type": action["type"],
                    "target_path": action["target_path"],
                    "class": action["class"],
                    "source_template": action["source_template"],
                    "expected_before": action["expected_before"],
                    "expected_after": action["expected_after"],
                    "no_overwrite": action["no_overwrite"],
                    "reversible": action["reversible"],
                    "rollback_strategy": action["rollback_strategy"],
                    "recommendation_ids": action["recommendation_ids"],
                    "evidence_refs": action["evidence_refs"],
                }
            )
    return sorted(actions, key=lambda item: item["id"])


def mutation_set(actions: list[dict]) -> dict:
    payload = {"actions": actions}
    return {
        "schema": "contextos.bootstrap.mutation_set/1",
        "count": len(actions),
        "actions": actions,
        "hash": stable_hash(payload),
    }


def target_state_matches(root: Path, action: dict) -> bool:
    target_path = action.get("target_path")
    if target_path is None:
        return False
    current = path_state(root.resolve() / target_path)
    expected = action["expected_before"]
    return current["exists"] == expected["exists"] and current["hash"] == expected["hash"]


def target_scope_ok(action: dict, allowed_paths: list[str], prohibited_paths: list[str]) -> bool:
    target = action.get("target_path")
    if not target:
        return False
    return target in allowed_paths and target not in prohibited_paths


def no_overwrite_ok(root: Path, actions: list[dict]) -> bool:
    return all(action["no_overwrite"]["satisfied"] and target_state_matches(root, action) for action in actions)


def rollback_ok(actions: list[dict]) -> bool:
    return all(action["reversible"] and action["rollback_strategy"] != "none" for action in actions)


def failed_checks(checks: list[dict]) -> list[dict]:
    return [check for check in checks if not check["passed"]]


class BootstrapApplyPreflightEngine:
    """Read-only engine that gates an accepted decision before future apply."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        accepted_decision: dict,
        *,
        accepted_decision_ref: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if accepted_decision.get("schema") != "contextos.bootstrap.accepted_decision/1":
            raise ValueError("Apply preflight requires contextos.bootstrap.accepted_decision/1 input.")

        root = self.root.resolve()
        approval_record = load_ref(root, accepted_decision.get("approval_record", {}).get("ref"), "approval record")
        proposal = load_ref(root, accepted_decision.get("proposal", {}).get("ref"), "proposal")
        drift = BootstrapProposalEngine(root).check_drift(proposal)
        validator_report = ValidatorEngine(root).run(mode="gate")
        actions = executable_actions(proposal)
        mutation = mutation_set(actions)
        checks = self._checks(
            accepted_decision,
            approval_record,
            proposal,
            drift,
            validator_report,
            actions,
            accepted_decision_ref,
        )
        failures = failed_checks(checks)
        report = {
            "schema": SCHEMA,
            "id": "",
            "generated_at": generated_at or generated_timestamp(),
            "root": str(root),
            "read_only": True,
            "accepted_decision": {
                "id": accepted_decision["id"],
                "identity_hash": accepted_decision["identity_hash"],
                "schema": accepted_decision["schema"],
                "ref": accepted_decision_ref,
                "file_hash": accepted_file_hash(accepted_decision_ref) if accepted_decision_ref else None,
            },
            "approval_record": {
                "id": approval_record["id"],
                "identity_hash": approval_record["identity_hash"],
                "schema": approval_record["schema"],
                "ref": accepted_decision["approval_record"]["ref"],
                "file_hash": approval_file_hash(accepted_decision["approval_record"]["ref"]),
            },
            "proposal": {
                "id": proposal["id"],
                "identity_hash": proposal["identity_hash"],
                "schema": proposal["schema"],
                "ref": accepted_decision["proposal"]["ref"],
                "file_hash": proposal_file_hash(accepted_decision["proposal"]["ref"]),
                "mission_id": proposal["mission_id"],
                "release": proposal["release"],
                "goal": proposal["goal"],
                "source_plan_hash": proposal["source_plan"]["plan_hash"],
                "repository_fingerprint_hash": proposal["repository_state"]["fingerprint_hash"],
                "action_summary": action_summary(proposal),
            },
            "authority": {
                "mode": accepted_decision["authority"]["mode"],
                "authority_level": accepted_decision["authority"]["authority_level"],
                "required_roles": accepted_decision["authority"]["required_roles"],
                "accepted_by": accepted_decision["authority"]["accepted_by"],
                "accepted_role": accepted_decision["authority"]["accepted_role"],
                "role_satisfied": accepted_decision["authority"]["role_satisfied"],
                "human_apply_confirmation_required": True,
            },
            "frozen_mutation_set": mutation,
            "validation": {
                "checks": checks,
                "drift": drift,
                "validator": {
                    "schema": validator_report["schema"],
                    "summary": validator_report["summary"],
                },
            },
            "eligibility": {
                "eligible_for_apply": not failures,
                "failed_check_count": len(failures),
                "failed_checks": [check["id"] for check in failures],
                "apply_authorized": False,
                "repository_mutation_authorized": False,
                "requires_human_apply_confirmation": True,
            },
            "constraints": {
                "writes_performed": False,
                "apply_performed": False,
                "apply_authorized": False,
                "repository_mutation_authorized": False,
                "approval_implied": False,
                "human_authority_required": True,
                "external_connectors_used": False,
                "agents_used": False,
            },
        }
        report["id"] = preflight_id(report)
        report["identity_hash"] = stable_hash(preflight_payload(report))
        return report

    def _checks(
        self,
        accepted_decision: dict,
        approval_record: dict,
        proposal: dict,
        drift: dict,
        validator_report: dict,
        actions: list[dict],
        accepted_decision_ref: str | None,
    ) -> list[dict]:
        allowed_paths = proposal["authority"]["allowed_write_paths"]
        prohibited_paths = proposal["authority"]["prohibited_write_paths"]
        current_accepted_hash = accepted_file_hash(accepted_decision_ref) if accepted_decision_ref else None
        return [
            check(
                "preflight.check.accepted_decision_identity_valid",
                accepted_decision["id"] == accepted_decision_id(accepted_decision)
                and accepted_decision["identity_hash"] == stable_hash(accepted_decision_payload(accepted_decision)),
                {"accepted_decision_id": accepted_decision["id"], "identity_hash": accepted_decision["identity_hash"]},
            ),
            check(
                "preflight.check.accepted_decision_file_preserved",
                accepted_decision_ref is not None and current_accepted_hash is not None,
                {"ref": accepted_decision_ref, "current_file_hash": current_accepted_hash},
            ),
            check(
                "preflight.check.approval_record_identity_valid",
                approval_record["id"] == approval_record_id(approval_record)
                and approval_record["identity_hash"] == stable_hash(approval_identity_payload(approval_record)),
                {"approval_record_id": approval_record["id"], "identity_hash": approval_record["identity_hash"]},
            ),
            check(
                "preflight.check.approval_record_matches_accepted_decision",
                accepted_decision["approval_record"]["id"] == approval_record["id"]
                and accepted_decision["approval_record"]["identity_hash"] == approval_record["identity_hash"]
                and accepted_decision["approval_record"]["file_hash"] == approval_file_hash(accepted_decision["approval_record"]["ref"]),
                {"accepted": accepted_decision["approval_record"], "loaded_id": approval_record["id"]},
            ),
            check(
                "preflight.check.proposal_identity_valid",
                proposal["id"] == f"bootstrap.proposal.{stable_hash(identity_payload(proposal))[:16]}"
                and proposal["identity_hash"] == stable_hash(identity_payload(proposal)),
                {"proposal_id": proposal["id"], "identity_hash": proposal["identity_hash"]},
            ),
            check(
                "preflight.check.proposal_matches_accepted_decision",
                accepted_decision["proposal"]["id"] == proposal["id"]
                and accepted_decision["proposal"]["identity_hash"] == proposal["identity_hash"]
                and accepted_decision["proposal"]["file_hash"] == proposal_file_hash(accepted_decision["proposal"]["ref"]),
                {"accepted": accepted_decision["proposal"], "loaded_id": proposal["id"]},
            ),
            check(
                "preflight.check.source_plan_bound",
                accepted_decision["proposal"]["source_plan_hash"] == proposal["source_plan"]["plan_hash"],
                {"accepted": accepted_decision["proposal"]["source_plan_hash"], "proposal": proposal["source_plan"]["plan_hash"]},
            ),
            check(
                "preflight.check.repository_fingerprint_valid",
                accepted_decision["proposal"]["repository_fingerprint_hash"] == proposal["repository_state"]["fingerprint_hash"],
                {
                    "accepted": accepted_decision["proposal"]["repository_fingerprint_hash"],
                    "proposal": proposal["repository_state"]["fingerprint_hash"],
                },
            ),
            check(
                "preflight.check.no_drift",
                not drift["invalidated"],
                drift["checks"],
            ),
            check(
                "preflight.check.authority_still_valid",
                accepted_decision["decision"]["approved"]
                and accepted_decision["decision"]["status"] == "accepted"
                and accepted_decision["authority"]["role_satisfied"]
                and role_satisfies(accepted_decision["authority"]["accepted_role"], accepted_decision["authority"]["required_roles"]),
                accepted_decision["authority"],
            ),
            check(
                "preflight.check.actions_within_approved_scope",
                all(target_scope_ok(action, allowed_paths, prohibited_paths) for action in actions),
                {"allowed_paths": allowed_paths, "prohibited_paths": prohibited_paths, "action_count": len(actions)},
            ),
            check(
                "preflight.check.prohibited_actions_impossible",
                all(action["class"] != "prohibited" for action in actions),
                {"mutation_action_ids": [action["id"] for action in actions]},
            ),
            check(
                "preflight.check.no_overwrite_guarantees_hold",
                no_overwrite_ok(self.root, actions),
                {"action_ids": [action["id"] for action in actions]},
            ),
            check(
                "preflight.check.rollback_expectations_present",
                rollback_ok(actions),
                {"action_ids": [action["id"] for action in actions]},
            ),
            check(
                "preflight.check.validator_gate_satisfied",
                validator_report["summary"]["error"] == 0 and validator_report["summary"]["fatal"] == 0,
                validator_report["summary"],
            ),
            check(
                "preflight.check.apply_evidence_complete",
                bool(actions)
                and accepted_decision["approval_record"]["id"] == approval_record["id"]
                and accepted_decision["proposal"]["id"] == proposal["id"],
                {
                    "accepted_decision_id": accepted_decision["id"],
                    "approval_record_id": approval_record["id"],
                    "proposal_id": proposal["id"],
                    "mutation_action_count": len(actions),
                },
            ),
            check(
                "preflight.check.no_mutation_authorized_by_preflight",
                not accepted_decision["decision"]["apply_authorized"]
                and not accepted_decision["decision"]["repository_mutation_authorized"],
                {
                    "accepted_apply_authorized": accepted_decision["decision"]["apply_authorized"],
                    "accepted_repository_mutation_authorized": accepted_decision["decision"]["repository_mutation_authorized"],
                },
            ),
        ]


def check(identifier: str, passed: bool, evidence: dict) -> dict:
    return {"id": identifier, "passed": bool(passed), "evidence": evidence}


def preflight_hash(report: dict) -> str:
    return hashlib.sha256(canonical_json(report).encode("utf-8")).hexdigest()
