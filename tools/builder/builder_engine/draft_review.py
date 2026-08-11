from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from builder_engine.draft_create import SCHEMA as DRAFT_WRITE_SCHEMA
from builder_engine.draft_workspace import path_state, stable_hash
from builder_engine.report_builder import generated_timestamp


TOOLS_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from engine.validator_engine import ValidatorEngine  # noqa: E402


SCHEMA = "contextos.builder.draft_review/1"
METADATA_PATTERN = re.compile(r"```json\n(?P<json>.*?)\n```", re.DOTALL)


def draft_review_payload(review: dict) -> dict:
    return {
        "schema": review["schema"],
        "source_write_result": review["source_write_result"],
        "draft_reviews": review["draft_reviews"],
        "boundaries": review["boundaries"],
        "result": review["result"],
    }


def draft_review_id(review: dict) -> str:
    return f"builder.draft_review.{stable_hash(draft_review_payload(review))[:16]}"


def extract_metadata(content: str) -> dict:
    match = METADATA_PATTERN.search(content)
    if not match:
        raise ValueError("Draft artifact does not contain a JSON metadata block.")
    return json.loads(match.group("json"))


def body_after_metadata(content: str) -> str:
    match = METADATA_PATTERN.search(content)
    if not match:
        return content.strip()
    return content[match.end() :].strip()


def content_summary(content: str) -> dict:
    body = body_after_metadata(content)
    lines = [line for line in body.splitlines() if line.strip()]
    return {
        "representation": "markdown_with_json_metadata",
        "line_count": len(content.splitlines()),
        "body_line_count": len(lines),
        "body_preview": lines[:8],
        "contains_generated_truth_claim": False,
    }


def truth_boundary_from(metadata: dict) -> dict:
    return {
        "observed": {
            "meaning": "Source evidence and file existence were observed.",
            "evidence_refs": metadata.get("plan_binding", {}).get("evidence_refs", []),
            "discovery_source_id": metadata.get("plan_binding", {}).get("source_discovery_id"),
            "discovery_fingerprint": metadata.get("plan_binding", {}).get("source_discovery_fingerprint"),
        },
        "inferred": {
            "meaning": "Classification and support are planning interpretations, not organizational truth.",
            "artifact_class": metadata.get("artifact_class"),
            "operation_domain": metadata.get("operation_domain"),
            "support": metadata.get("support", {}),
        },
        "suggested": {
            "meaning": "The target context artifact came from a construction/draft plan and remains a suggestion until reviewed.",
            "target_context_artifact": metadata.get("target_context_artifact"),
            "construction_candidate_id": metadata.get("plan_binding", {}).get("source_construction_candidate_id"),
        },
        "drafted": {
            "meaning": "A non-canonical draft envelope exists in the Draft Workspace.",
            "lifecycle_state": metadata.get("lifecycle_state"),
            "draft_item_id": metadata.get("draft_item_id"),
            "target_identity": metadata.get("target_identity"),
        },
        "unknown": {
            "meaning": "Unknowns and missing evidence remain unresolved.",
            "unknowns": metadata.get("unknowns", []),
            "missing_evidence": metadata.get("missing_evidence", []),
            "contradictions": metadata.get("contradictions", []),
        },
        "approved_truth": {
            "meaning": "No approved or canonical organizational truth is created by this review.",
            "reviewed": metadata.get("reviewed") is True,
            "approved": metadata.get("approved") is True,
            "canonical_verified": metadata.get("canonical_verified") is True,
            "canonical": metadata.get("canonical") is True,
        },
    }


def recommended_next_action(metadata: dict, validation_summary: dict) -> dict:
    if metadata.get("canonical") or metadata.get("approved") or metadata.get("canonical_verified"):
        return {
            "state": "blocked",
            "action": "Stop and investigate: draft metadata claims a canonical or approved state.",
        }
    if metadata.get("contradictions"):
        return {
            "state": "resolve_contradictions",
            "action": "Resolve contradictions before requesting review or approval.",
        }
    if validation_summary.get("error") or validation_summary.get("fatal"):
        return {
            "state": "resolve_validation",
            "action": "Resolve Validator gate findings before any future review or promotion.",
        }
    return {
        "state": "ready_for_human_review",
        "action": "A human may review the draft content and provenance; approval or promotion requires a separate governed mission.",
    }


def review_for_mutation(root: Path, mutation: dict, validation_summary: dict) -> dict:
    draft_path = root / mutation["target_path"]
    state = path_state(draft_path)
    if not state["exists"] or state["kind"] != "file":
        return {
            "draft_item_id": mutation["draft_item_id"],
            "draft_path": mutation["target_path"],
            "status": "missing",
            "reviewable": False,
            "errors": ["Draft artifact is missing."],
        }
    content = draft_path.read_text(encoding="utf-8")
    metadata = extract_metadata(content)
    canonical_flags = {
        "canonical": metadata.get("canonical") is True,
        "reviewed": metadata.get("reviewed") is True,
        "approved": metadata.get("approved") is True,
        "canonical_verified": metadata.get("canonical_verified") is True,
        "promotion_authorized": metadata.get("promotion_authorized") is True,
    }
    errors = []
    if metadata.get("schema") != "contextos.builder.draft_artifact/1":
        errors.append("Draft metadata schema is not contextos.builder.draft_artifact/1.")
    if metadata.get("lifecycle_state") != "draft":
        errors.append("Draft lifecycle state is not draft.")
    if any(canonical_flags.values()):
        errors.append("Draft metadata implies review, approval, promotion, or canonical truth.")
    if metadata.get("source_preflight_id") != mutation["provenance"]["preflight_id"]:
        errors.append("Draft source preflight id does not match mutation provenance.")
    if metadata.get("source_builder_draft_plan_hash") != mutation["provenance"]["builder_draft_plan_hash"]:
        errors.append("Draft source Builder Draft Plan hash does not match mutation provenance.")
    return {
        "draft_item_id": mutation["draft_item_id"],
        "draft_path": mutation["target_path"],
        "target_context_artifact": mutation["target_context_artifact"],
        "status": "reviewable" if not errors else "blocked",
        "reviewable": not errors,
        "errors": errors,
        "identity": {
            "target_identity": metadata.get("target_identity"),
            "file_hash": state["hash"],
            "created_hash": mutation.get("after", {}).get("hash"),
            "hash_matches_write_result": state["hash"] == mutation.get("after", {}).get("hash"),
        },
        "lifecycle": {
            "state": metadata.get("lifecycle_state"),
            "canonical": metadata.get("canonical"),
            "reviewed": metadata.get("reviewed"),
            "approved": metadata.get("approved"),
            "canonical_verified": metadata.get("canonical_verified"),
        },
        "content": content_summary(content),
        "source": {
            "mission_id": metadata.get("mission_id"),
            "source_preflight_id": metadata.get("source_preflight_id"),
            "source_preflight_hash": metadata.get("source_preflight_hash"),
            "source_builder_draft_plan_hash": metadata.get("source_builder_draft_plan_hash"),
            "draft_item_id": metadata.get("draft_item_id"),
        },
        "provenance": metadata.get("plan_binding", {}),
        "support": metadata.get("support", {}),
        "evidence_refs": metadata.get("plan_binding", {}).get("evidence_refs", []),
        "uncertainty": {
            "unknowns": metadata.get("unknowns", []),
            "missing_evidence": metadata.get("missing_evidence", []),
            "contradictions": metadata.get("contradictions", []),
        },
        "validation": {
            "write_before": mutation.get("before"),
            "write_after": mutation.get("after"),
            "no_overwrite": mutation.get("before", {}).get("exists") is False,
            "post_write_validator_summary": validation_summary,
        },
        "promotion_restrictions": metadata.get("promotion_restrictions", []),
        "authority_still_required": {
            "review_required": True,
            "approval_required": True,
            "promotion_authority_required": True,
            "canonical_write_authority_required": True,
            "draft_authority": metadata.get("authority_required", {}),
        },
        "truth_boundary": truth_boundary_from(metadata),
        "recommended_next_action": recommended_next_action(metadata, validation_summary),
    }


class BuilderDraftReviewEngine:
    """Read-only review surface for Draft Workspace artifacts."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(self, draft_write_result: dict, *, generated_at: str | None = None) -> dict:
        if draft_write_result.get("schema") != DRAFT_WRITE_SCHEMA:
            raise ValueError("Draft review requires contextos.builder.draft_write_result/1 input.")
        root = self.root.resolve()
        before = {path.relative_to(root).as_posix(): path_state(path) for path in root.rglob("*") if path.is_file()}
        validator_report = ValidatorEngine(root).run(mode="gate")
        validation_summary = validator_report["summary"]
        reviews = [review_for_mutation(root, mutation, validation_summary) for mutation in draft_write_result.get("mutations", [])]
        after = {path.relative_to(root).as_posix(): path_state(path) for path in root.rglob("*") if path.is_file()}
        errors = [error for item in reviews for error in item.get("errors", [])]
        review = {
            "schema": SCHEMA,
            "id": "",
            "generated_at": generated_at or generated_timestamp(),
            "root": str(root),
            "read_only": True,
            "source_write_result": {
                "id": draft_write_result["id"],
                "identity_hash": draft_write_result["identity_hash"],
                "schema": draft_write_result["schema"],
                "preflight_id": draft_write_result["preflight"]["id"],
                "preflight_hash": draft_write_result["preflight"]["identity_hash"],
                "builder_draft_plan_hash": draft_write_result["preflight"]["builder_draft_plan_hash"],
                "authorization": {
                    "authorized_by": draft_write_result["authorization"]["authorized_by"],
                    "authorized_role": draft_write_result["authorization"]["authorized_role"],
                    "authorized_mission_id": draft_write_result["authorization"]["authorized_mission_id"],
                    "authorized_capability": draft_write_result["authorization"]["authorized_capability"],
                },
            },
            "summary": {
                "draft_count": len(reviews),
                "reviewable_count": sum(1 for item in reviews if item.get("reviewable")),
                "blocked_count": sum(1 for item in reviews if not item.get("reviewable")),
                "unknown_count": sum(len(item.get("uncertainty", {}).get("unknowns", [])) for item in reviews),
                "missing_evidence_count": sum(len(item.get("uncertainty", {}).get("missing_evidence", [])) for item in reviews),
                "contradiction_count": sum(len(item.get("uncertainty", {}).get("contradictions", [])) for item in reviews),
            },
            "draft_reviews": reviews,
            "validation": {
                "validator": {
                    "schema": validator_report["schema"],
                    "summary": validation_summary,
                },
                "read_only_unchanged": before == after,
            },
            "boundaries": {
                "review_is_not_approval": True,
                "review_does_not_promote": True,
                "review_does_not_mutate_draft": True,
                "draft_is_not_canonical_truth": True,
                "observed_inferred_suggested_draft_approved_are_separate": True,
            },
            "result": {
                "state": "review_ready" if reviews and not errors else "blocked",
                "success": bool(reviews) and not errors and before == after,
                "errors": errors,
            },
            "constraints": {
                "writes_performed": False,
                "drafts_mutated": False,
                "review_record_persisted": False,
                "approval_performed": False,
                "promotion_performed": False,
                "ssot_writes_performed": False,
                "canonical_context_writes_performed": False,
                "knowledge_engine_used": False,
                "graph_runtime_used": False,
                "agents_used": False,
                "external_connectors_used": False,
            },
        }
        review["id"] = draft_review_id(review)
        review["identity_hash"] = stable_hash(draft_review_payload(review))
        return review


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def render_human(review: dict) -> str:
    summary = review["summary"]
    lines = [
        "# Context OS Draft Review",
        "",
        f"- Schema: `{review['schema']}`",
        f"- Root: `{review['root']}`",
        f"- Read-only: {yes_no(review['read_only'])}",
        f"- Drafts: {summary['draft_count']}",
        f"- Reviewable: {summary['reviewable_count']}",
        f"- Blocked: {summary['blocked_count']}",
        f"- Unknowns: {summary['unknown_count']}",
        f"- Missing evidence: {summary['missing_evidence_count']}",
        f"- Contradictions: {summary['contradiction_count']}",
        "",
        "## Drafts",
    ]
    for item in review["draft_reviews"]:
        lines.append(f"- `{item['draft_item_id']}` -> `{item['draft_path']}`")
        lines.append(f"  Target: `{item.get('target_context_artifact')}`")
        lines.append(f"  State: {item.get('lifecycle', {}).get('state')} / canonical={yes_no(item.get('lifecycle', {}).get('canonical') is True)}")
        lines.append(f"  Support: {item.get('support', {}).get('level', 'unknown')}")
        lines.append(f"  Unknowns: {len(item.get('uncertainty', {}).get('unknowns', []))}")
        lines.append(f"  Missing evidence: {len(item.get('uncertainty', {}).get('missing_evidence', []))}")
        lines.append(f"  Contradictions: {len(item.get('uncertainty', {}).get('contradictions', []))}")
        lines.append(f"  Next: {item.get('recommended_next_action', {}).get('action')}")
    if not review["draft_reviews"]:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Truth Boundary",
            "- Observed evidence, inferred classification, suggested context, draft content, unknowns, and approved truth remain separate.",
            "- This review does not approve, promote, or persist a review decision.",
            "- Canonical SSOT remains unchanged.",
            "",
            "## Validator Summary",
            f"- Findings: info={review['validation']['validator']['summary']['info']}, "
            f"warn={review['validation']['validator']['summary']['warn']}, "
            f"error={review['validation']['validator']['summary']['error']}, "
            f"fatal={review['validation']['validator']['summary']['fatal']}",
            "",
            "## Read-Only Guarantee",
            f"- Repository file state unchanged: {yes_no(review['validation']['read_only_unchanged'])}",
            "- Draft review did not mutate draft files.",
        ]
    )
    return "\n".join(lines) + "\n"
