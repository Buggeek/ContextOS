from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

from bootstrap_engine.proposal_engine import BootstrapProposalEngine, canonical_json, stable_hash


SCHEMA = "contextos.bootstrap.approval_record/1"


def generated_timestamp() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def approval_identity_payload(record: dict) -> dict:
    return {
        "schema": record["schema"],
        "proposal": record["proposal"],
        "authority": {
            "mode": record["authority"]["mode"],
            "authority_level": record["authority"]["authority_level"],
            "required_roles": record["authority"]["required_roles"],
            "approver_candidates": record["authority"]["approver_candidates"],
        },
        "decision": {
            "status": record["decision"]["status"],
            "decision_kind": record["decision"]["decision_kind"],
        },
    }


def approval_record_id(record: dict) -> str:
    return f"bootstrap.approval.{stable_hash(approval_identity_payload(record))[:16]}"


def proposal_file_hash(path: str | Path | None) -> str | None:
    if path is None:
        return None
    material = Path(path).read_bytes()
    return hashlib.sha256(material).hexdigest()


class BootstrapApprovalRecordEngine:
    """Read-only engine that drafts the decision record required before apply."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        proposal: dict,
        *,
        proposal_ref: str | None = None,
        generated_at: str | None = None,
        approver_candidates: list[str] | None = None,
        rationale: str | None = None,
    ) -> dict:
        if proposal.get("schema") != "contextos.bootstrap.proposal/1":
            raise ValueError("Approval record requires contextos.bootstrap.proposal/1 input.")

        drift = BootstrapProposalEngine(self.root).check_drift(proposal)
        required_roles = list(proposal["authority"]["approving_roles"])
        candidates = approver_candidates or []
        blockers = approval_blockers(proposal, drift, candidates)
        record = {
            "schema": SCHEMA,
            "id": "",
            "generated_at": generated_at or generated_timestamp(),
            "root": str(self.root.resolve()),
            "read_only": True,
            "proposal": {
                "id": proposal["id"],
                "identity_hash": proposal["identity_hash"],
                "schema": proposal["schema"],
                "ref": proposal_ref,
                "file_hash": proposal_file_hash(proposal_ref),
                "mission_id": proposal["mission_id"],
                "release": proposal["release"],
                "goal": proposal["goal"],
                "source_plan_hash": proposal["source_plan"]["plan_hash"],
                "repository_fingerprint_hash": proposal["repository_state"]["fingerprint_hash"],
                "status": proposal["status"],
            },
            "authority": {
                "mode": proposal["mode"],
                "authority_level": "L3",
                "required_roles": required_roles,
                "approver_candidates": candidates,
                "decision_ref": None,
                "ledger_ref": None,
            },
            "decision": {
                "status": "draft",
                "decision_kind": "pending",
                "approved": False,
                "apply_authorized": False,
                "rationale": rationale or "Pending human decision.",
                "required_decision_record_schema": "contextos.decision/1",
                "decision_record_draft": decision_record_draft(proposal, candidates, rationale),
            },
            "drift": drift,
            "blockers": blockers,
            "constraints": {
                "writes_performed": False,
                "approval_implied": False,
                "apply_authorized": False,
                "human_authority_required": True,
                "external_connectors_used": False,
                "agents_used": False,
            },
        }
        record["id"] = approval_record_id(record)
        record["identity_hash"] = stable_hash(approval_identity_payload(record))
        return record


def approval_blockers(proposal: dict, drift: dict, approver_candidates: list[str]) -> list[dict]:
    blockers: list[dict] = []
    if drift["invalidated"]:
        blockers.append(
            {
                "id": "approval.blocker.proposal_drift",
                "severity": "error",
                "message": "Proposal drift is present; approval must not proceed.",
                "evidence": drift["checks"],
            }
        )
    if proposal["repository_state"]["dirty_state"] != "clean":
        blockers.append(
            {
                "id": "approval.blocker.repository_dirty",
                "severity": "warn",
                "message": "Repository state is dirty; approval requires a clean state or explicit human waiver.",
                "evidence": {"dirty_state": proposal["repository_state"]["dirty_state"]},
            }
        )
    if not approver_candidates:
        blockers.append(
            {
                "id": "approval.blocker.no_approver_candidate",
                "severity": "warn",
                "message": "No approver candidate was supplied; human authority is still required.",
                "evidence": {"required_roles": proposal["authority"]["approving_roles"]},
            }
        )
    prohibited = [action["id"] for action in proposal.get("actions", []) if action["class"] == "prohibited"]
    if prohibited:
        blockers.append(
            {
                "id": "approval.blocker.prohibited_actions",
                "severity": "error",
                "message": "Proposal contains prohibited actions.",
                "evidence": {"actions": prohibited},
            }
        )
    return blockers


def decision_record_draft(proposal: dict, approver_candidates: list[str], rationale: str | None) -> dict:
    return {
        "schema": "contextos.decision/1",
        "id": None,
        "title": f"Approve Guided Bootstrap Proposal {proposal['id']}",
        "context_version": None,
        "proposal_id": proposal["id"],
        "decided_by": approver_candidates,
        "decided_at": None,
        "rationale": rationale or "Pending human decision.",
        "alternatives_considered": [
            "Reject proposal and regenerate after remediation.",
            "Request changes to bootstrap scope before approval.",
            "Defer apply until missing governance evidence exists.",
        ],
        "consequences": [
            "If approved by a human authority later, apply must use the exact proposal identity hash.",
            "This draft does not approve or authorize apply.",
        ],
        "links": [
            proposal["id"],
            proposal["identity_hash"],
            proposal["mission_id"],
        ],
    }


def approval_record_hash(record: dict) -> str:
    return hashlib.sha256(canonical_json(record).encode("utf-8")).hexdigest()
