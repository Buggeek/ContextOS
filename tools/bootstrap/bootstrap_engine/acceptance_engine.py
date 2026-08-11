from __future__ import annotations

import hashlib
from pathlib import Path

from bootstrap_engine.approval_engine import (
    approval_identity_payload,
    approval_record_hash,
    approval_record_id,
    generated_timestamp,
    load_json,
    proposal_file_hash,
)
from bootstrap_engine.proposal_engine import BootstrapProposalEngine, canonical_json, identity_payload, stable_hash


SCHEMA = "contextos.bootstrap.accepted_decision/1"


def accepted_decision_payload(decision: dict) -> dict:
    return {
        "schema": decision["schema"],
        "approval_record": decision["approval_record"],
        "proposal": decision["proposal"],
        "authority": decision["authority"],
        "decision": {
            "status": decision["decision"]["status"],
            "decision_kind": decision["decision"]["decision_kind"],
            "approved": decision["decision"]["approved"],
            "apply_authorized": decision["decision"]["apply_authorized"],
            "accepted_by": decision["decision"]["accepted_by"],
            "accepted_role": decision["decision"]["accepted_role"],
            "rationale": decision["decision"]["rationale"],
        },
    }


def accepted_decision_id(decision: dict) -> str:
    return f"bootstrap.accepted_decision.{stable_hash(accepted_decision_payload(decision))[:16]}"


def approval_file_hash(path: str | Path | None) -> str | None:
    if path is None:
        return None
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def role_options(required_role: str) -> list[str]:
    return [part.strip() for part in required_role.split(" or ") if part.strip()]


def role_satisfies(accepted_role: str, required_roles: list[str]) -> bool:
    normalized = accepted_role.strip().lower()
    for required in required_roles:
        if normalized == required.strip().lower():
            return True
        for option in role_options(required):
            if normalized == option.lower():
                return True
    return False


def required_evidence_present(record: dict, proposal: dict) -> bool:
    required_values = [
        record.get("id"),
        record.get("identity_hash"),
        record.get("proposal", {}).get("id"),
        record.get("proposal", {}).get("identity_hash"),
        record.get("proposal", {}).get("source_plan_hash"),
        record.get("proposal", {}).get("repository_fingerprint_hash"),
        proposal.get("id"),
        proposal.get("identity_hash"),
        proposal.get("source_plan", {}).get("plan_hash"),
        proposal.get("repository_state", {}).get("fingerprint_hash"),
    ]
    return all(value is not None and value != "" for value in required_values)


def action_summary(proposal: dict) -> dict:
    counts = {"automatic": 0, "approval_required": 0, "manual": 0, "prohibited": 0}
    for action in proposal.get("actions", []):
        counts[action["class"]] = counts.get(action["class"], 0) + 1
    return {
        "count": len(proposal.get("actions", [])),
        "by_class": counts,
        "ids": [action["id"] for action in proposal.get("actions", [])],
        "prohibited_ids": [action["id"] for action in proposal.get("actions", []) if action["class"] == "prohibited"],
    }


class BootstrapApprovalAcceptanceEngine:
    """Read-only engine that records an explicit human approval decision."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        approval_record: dict,
        *,
        approval_record_ref: str | None = None,
        accepted_by: str,
        accepted_role: str,
        rationale: str | None = None,
        accepted_at: str | None = None,
    ) -> dict:
        if approval_record.get("schema") != "contextos.bootstrap.approval_record/1":
            raise ValueError("Approval acceptance requires contextos.bootstrap.approval_record/1 input.")
        if not accepted_by or not accepted_by.strip():
            raise ValueError("Approval acceptance requires an explicit approving human identity.")
        if not accepted_role or not accepted_role.strip():
            raise ValueError("Approval acceptance requires an explicit approving role.")

        timestamp = accepted_at or generated_timestamp()
        proposal = self._load_proposal(approval_record)
        checks = self._acceptance_checks(approval_record, proposal, accepted_by.strip(), accepted_role.strip())
        failures = [check for check in checks if not check["passed"]]
        if failures:
            failure_ids = ", ".join(check["id"] for check in failures)
            raise ValueError(f"Approval acceptance blocked: {failure_ids}")

        record_hash = approval_file_hash(approval_record_ref) if approval_record_ref else approval_record_hash(approval_record)
        decision_record = build_decision_record(
            approval_record,
            proposal,
            accepted_by=accepted_by.strip(),
            accepted_role=accepted_role.strip(),
            rationale=rationale,
            accepted_at=timestamp,
        )
        accepted = {
            "schema": SCHEMA,
            "id": "",
            "accepted_at": timestamp,
            "root": str(self.root.resolve()),
            "read_only": True,
            "approval_record": {
                "id": approval_record["id"],
                "identity_hash": approval_record["identity_hash"],
                "schema": approval_record["schema"],
                "ref": approval_record_ref,
                "file_hash": record_hash,
            },
            "proposal": {
                "id": proposal["id"],
                "identity_hash": proposal["identity_hash"],
                "schema": proposal["schema"],
                "ref": approval_record["proposal"]["ref"],
                "file_hash": proposal_file_hash(approval_record["proposal"]["ref"]),
                "mission_id": proposal["mission_id"],
                "release": proposal["release"],
                "goal": proposal["goal"],
                "source_plan_hash": proposal["source_plan"]["plan_hash"],
                "repository_fingerprint_hash": proposal["repository_state"]["fingerprint_hash"],
                "action_summary": action_summary(proposal),
            },
            "authority": {
                "mode": approval_record["authority"]["mode"],
                "authority_level": approval_record["authority"]["authority_level"],
                "required_roles": approval_record["authority"]["required_roles"],
                "accepted_by": accepted_by.strip(),
                "accepted_role": accepted_role.strip(),
                "role_satisfied": True,
            },
            "decision": {
                "status": "accepted",
                "decision_kind": "approve_bootstrap_proposal",
                "approved": True,
                "apply_authorized": False,
                "repository_mutation_authorized": False,
                "accepted_by": accepted_by.strip(),
                "accepted_role": accepted_role.strip(),
                "rationale": rationale or "Explicit human approval recorded for the preserved Bootstrap Proposal.",
                "decision_record": decision_record,
            },
            "validation": {
                "checks": checks,
                "drift": BootstrapProposalEngine(self.root).check_drift(proposal),
            },
            "constraints": {
                "writes_performed": False,
                "approval_implied": False,
                "apply_authorized": False,
                "repository_mutation_authorized": False,
                "human_authority_required": True,
                "external_connectors_used": False,
                "agents_used": False,
            },
        }
        accepted["id"] = accepted_decision_id(accepted)
        accepted["identity_hash"] = stable_hash(accepted_decision_payload(accepted))
        accepted["decision"]["decision_record"]["id"] = f"decision.{accepted['identity_hash'][:16]}"
        return accepted

    def _load_proposal(self, approval_record: dict) -> dict:
        proposal_ref = approval_record.get("proposal", {}).get("ref")
        if not proposal_ref:
            raise ValueError("Approval acceptance requires the preserved proposal file reference.")
        proposal_path = Path(proposal_ref)
        if not proposal_path.is_absolute():
            proposal_path = self.root / proposal_path
        proposal = load_json(proposal_path)
        if proposal.get("schema") != "contextos.bootstrap.proposal/1":
            raise ValueError("Approval acceptance proposal reference is not contextos.bootstrap.proposal/1.")
        return proposal

    def _acceptance_checks(self, record: dict, proposal: dict, accepted_by: str, accepted_role: str) -> list[dict]:
        current_proposal_hash = proposal_file_hash(record["proposal"]["ref"])
        drift = BootstrapProposalEngine(self.root).check_drift(proposal)
        prohibited = [action["id"] for action in proposal.get("actions", []) if action["class"] == "prohibited"]
        blocking_record_blockers = [
            blocker["id"]
            for blocker in record.get("blockers", [])
            if blocker.get("id") != "approval.blocker.prohibited_actions"
            and blocker.get("severity") == "error"
        ]
        checks = [
            check(
                "acceptance.check.approval_record_identity_valid",
                record["id"] == approval_record_id(record)
                and record["identity_hash"] == stable_hash(approval_identity_payload(record)),
                {"record_id": record["id"], "record_identity_hash": record["identity_hash"]},
            ),
            check(
                "acceptance.check.proposal_identity_valid",
                proposal["id"] == f"bootstrap.proposal.{stable_hash(identity_payload(proposal))[:16]}"
                and proposal["identity_hash"] == stable_hash(identity_payload(proposal)),
                {"proposal_id": proposal["id"], "proposal_identity_hash": proposal["identity_hash"]},
            ),
            check(
                "acceptance.check.approval_record_draft",
                record["decision"]["status"] == "draft" and not record["decision"]["approved"],
                {"status": record["decision"]["status"], "approved": record["decision"]["approved"]},
            ),
            check(
                "acceptance.check.proposal_identity_unchanged",
                record["proposal"]["id"] == proposal["id"] and record["proposal"]["identity_hash"] == proposal["identity_hash"],
                {"record": record["proposal"]["identity_hash"], "proposal": proposal["identity_hash"]},
            ),
            check(
                "acceptance.check.source_plan_identity_unchanged",
                record["proposal"]["source_plan_hash"] == proposal["source_plan"]["plan_hash"],
                {"record": record["proposal"]["source_plan_hash"], "proposal": proposal["source_plan"]["plan_hash"]},
            ),
            check(
                "acceptance.check.repository_fingerprint_valid",
                record["proposal"]["repository_fingerprint_hash"] == proposal["repository_state"]["fingerprint_hash"],
                {
                    "record": record["proposal"]["repository_fingerprint_hash"],
                    "proposal": proposal["repository_state"]["fingerprint_hash"],
                },
            ),
            check(
                "acceptance.check.proposal_file_hash_unchanged",
                record["proposal"]["file_hash"] in {None, current_proposal_hash},
                {"record": record["proposal"]["file_hash"], "current": current_proposal_hash},
            ),
            check(
                "acceptance.check.no_drift",
                not drift["invalidated"],
                drift["checks"],
            ),
            check(
                "acceptance.check.approving_human_identity_present",
                bool(accepted_by),
                {"accepted_by": accepted_by},
            ),
            check(
                "acceptance.check.approving_role_satisfies_required_authority",
                role_satisfies(accepted_role, record["authority"]["required_roles"]),
                {"accepted_role": accepted_role, "required_roles": record["authority"]["required_roles"]},
            ),
            check(
                "acceptance.check.decision_explicit_and_auditable",
                record["decision"]["decision_kind"] == "pending",
                {"input_decision_kind": record["decision"]["decision_kind"], "output_decision_kind": "approve_bootstrap_proposal"},
            ),
            check(
                "acceptance.check.prohibited_actions_remain_prohibited",
                all(action["class"] == "prohibited" for action in proposal.get("actions", []) if action["id"] in prohibited),
                {"prohibited_actions": prohibited},
            ),
            check(
                "acceptance.check.required_evidence_present",
                required_evidence_present(record, proposal),
                {"required": ["approval identity", "proposal identity", "source plan hash", "repository fingerprint hash"]},
            ),
            check(
                "acceptance.check.approval_record_has_no_blocking_blockers",
                not blocking_record_blockers,
                {"blocking_record_blockers": blocking_record_blockers},
            ),
        ]
        return checks


def check(identifier: str, passed: bool, evidence: dict) -> dict:
    return {"id": identifier, "passed": bool(passed), "evidence": evidence}


def build_decision_record(
    approval_record: dict,
    proposal: dict,
    *,
    accepted_by: str,
    accepted_role: str,
    rationale: str | None,
    accepted_at: str | None,
) -> dict:
    return {
        "schema": "contextos.decision/1",
        "id": None,
        "title": f"Accept Guided Bootstrap Approval for {proposal['id']}",
        "context_version": None,
        "proposal_id": proposal["id"],
        "proposal_identity_hash": proposal["identity_hash"],
        "approval_record_id": approval_record["id"],
        "approval_record_identity_hash": approval_record["identity_hash"],
        "decision_kind": "approve_bootstrap_proposal",
        "outcome": "accepted",
        "decided_by": accepted_by,
        "deciding_role": accepted_role,
        "decided_at": accepted_at,
        "rationale": rationale or "Explicit human approval recorded for the preserved Bootstrap Proposal.",
        "alternatives_considered": approval_record["decision"]["decision_record_draft"]["alternatives_considered"],
        "consequences": [
            "The proposal is accepted as the exact future apply candidate.",
            "This decision does not authorize or perform repository mutation.",
            "Future apply must consume this accepted decision and revalidate identity and drift.",
        ],
        "links": [
            proposal["id"],
            proposal["identity_hash"],
            approval_record["id"],
            approval_record["identity_hash"],
            proposal["mission_id"],
        ],
    }


def accepted_decision_hash(decision: dict) -> str:
    return hashlib.sha256(canonical_json(decision).encode("utf-8")).hexdigest()
