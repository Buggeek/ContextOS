from __future__ import annotations

import copy
import datetime as dt
from pathlib import Path

from .continuity_engine import file_hash, stable_hash
from .retention_resolution_report_builder import CHECK_SCHEMA, build_report, generated_timestamp


MEMORY_FORMS = {"mission", "decision", "evidence", "outcome", "learning", "context_state", "evolution_inbox"}
RETENTION_STATES = {"active", "historical", "archived", "operationally_forgotten", "content_removed", "unknown"}
SENSITIVITY = {"public", "internal", "confidential", "restricted", "unknown"}
OUTCOMES = {"normal", "elevated_authority", "excluded", "prohibited", "unknown"}
OPERATIONS = ("access", "retrieval", "activation", "retention_transition", "destructive_action")
OUTCOME_RANK = {"unknown": -1, "normal": 0, "elevated_authority": 1, "excluded": 2, "prohibited": 3}
VISIBILITY = {"full", "identity_only", "none"}


def _normalized(value: object) -> object:
    return copy.deepcopy(value)


def _restrictive(current: str, proposed: str) -> str:
    if current == "unknown":
        return proposed
    if proposed == "unknown":
        return current
    return proposed if OUTCOME_RANK[proposed] > OUTCOME_RANK[current] else current


def _display_id(value: str, visibility: str) -> str:
    if visibility == "none":
        return "<restricted>"
    return value


def _parse_timestamp(value: str) -> dt.datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _policy_ref(policy: dict) -> str:
    if policy.get("explanation_visibility", "id_only") == "none":
        return "<restricted>"
    return policy["id"]


class RetentionResolutionEngine:
    """Resolve explicit memory policies without changing memory or authority."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def run(
        self,
        memory_item: dict,
        policies: list[dict],
        *,
        consumer: str,
        actor_roles: list[str] | tuple[str, ...] = (),
        requested_operations: list[str] | tuple[str, ...] = OPERATIONS,
        organizational_mode: str | None = None,
        authority_scope: str | None = None,
        evaluation_time: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        memory = _normalized(memory_item)
        policy_inputs = _normalized(policies)
        roles = sorted(set(actor_roles))
        operations = list(dict.fromkeys(requested_operations))
        self._validate(memory, policy_inputs, consumer, operations)
        evaluated_at = evaluation_time or generated_at or generated_timestamp()

        source_evidence, source_fingerprint = self._source_evidence(memory, policy_inputs)
        applied, not_applied, applicability_unknowns = self._applicable_policies(
            memory, policy_inputs, evaluated_at
        )
        required_policy_refs = sorted(set(memory.get("required_policy_refs", [])))
        applied_ids = {policy["id"] for policy in applied}
        applied_bindings = sorted(_policy_ref(policy) for policy in applied)
        policy_by_id = {policy["id"]: policy for policy in policy_inputs}

        def safe_required_ref(policy_id: str) -> str:
            supplied = policy_by_id.get(policy_id)
            if supplied is not None:
                return _policy_ref(supplied)
            if memory.get("metadata_visibility", "identity_only") == "full":
                return policy_id
            return "<restricted>"

        unresolved = list(applicability_unknowns)
        missing_required = [policy_id for policy_id in required_policy_refs if policy_id not in applied_ids]
        for policy_id in missing_required:
            safe_ref = safe_required_ref(policy_id)
            unresolved.append(
                {
                    "id": f"retention.unresolved.required_policy.{stable_hash(policy_id)[:12]}",
                    "kind": "required_policy_missing",
                    "message": f"Required policy {safe_ref} was not proven applicable.",
                    "required_authority": ["policy_owner"],
                }
            )
        if not applied:
            unresolved.append(
                {
                    "id": "retention.unresolved.no_policy_applies",
                    "kind": "no_policy_applies",
                    "message": "No supplied policy was proven applicable; absence does not permit an operation.",
                    "required_authority": ["policy_owner", "governance_role"],
                }
            )
        for evidence in source_evidence:
            if not evidence["matches"]:
                unresolved.append(
                    {
                        "id": f"retention.unresolved.source_state.{stable_hash(evidence)[:12]}",
                        "kind": "source_state_invalid",
                        "message": "A bound source is missing or no longer matches its expected hash.",
                        "required_authority": ["memory_owner"],
                    }
                )

        preservation, holds, conflicts = self._obligations(applied)
        results, authority = self._operation_results(memory, applied, holds, conflicts, unresolved, roles, operations)
        status = self._status(results, conflicts, unresolved)
        visibility = memory.get("metadata_visibility", "identity_only")
        evidence = self._safe_evidence(memory, visibility)
        memory_hash = stable_hash(memory)
        policy_input_bindings = [
            {"identity_hash": stable_hash(policy["id"]), "version": policy["version"], "hash": stable_hash(policy)}
            for policy in policy_inputs
        ]
        policy_hashes = [
            {
                "display_id": _policy_ref(policy),
                "identity_hash": stable_hash(policy["id"])
                if policy.get("explanation_visibility", "id_only") != "none"
                else None,
                "version": policy["version"],
                "hash": stable_hash(policy)
                if policy.get("explanation_visibility", "id_only") != "none"
                else None,
            }
            for policy in policy_inputs
        ]
        input_fingerprint = stable_hash(
            {
                "memory_metadata_hash": memory_hash,
                "policies": policy_input_bindings,
                "consumer": consumer,
                "actor_roles": roles,
                "requested_operations": operations,
                "organizational_mode": organizational_mode,
                "authority_scope": authority_scope,
                "evaluation_time": evaluated_at,
                "source_fingerprint": source_fingerprint,
            }
        )
        memory_summary = {
            "display_id": _display_id(memory["id"], visibility),
            "identity_hash": stable_hash(memory["id"]) if visibility != "none" else None,
            "metadata_hash": memory_hash,
            "form": memory["form"] if visibility != "none" else None,
            "tier": memory.get("tier") if visibility == "full" else None,
            "owner": memory.get("owner") if visibility == "full" else None,
            "organization": memory.get("organization") if visibility == "full" else None,
            "operation": memory.get("operation") if visibility == "full" else None,
            "jurisdiction": memory.get("jurisdiction") if visibility == "full" else None,
            "affected_parties": memory.get("affected_parties", []) if visibility == "full" else [],
            "sensitivity": memory["sensitivity"] if visibility != "none" else None,
            "retention_state": memory["retention_state"] if visibility != "none" else None,
            "temporal": memory.get("temporal", {}) if visibility == "full" else {},
            "truth": memory.get("truth", {}) if visibility == "full" else {},
            "metadata_visibility": visibility,
        }
        policy_evaluation = {
            "applied": [self._policy_summary(policy) for policy in applied],
            "not_applied": not_applied,
            "required_policy_refs": [safe_required_ref(policy_id) for policy_id in required_policy_refs],
            "policy_hashes": policy_hashes,
            "applied_bindings": applied_bindings,
        }
        resolution_material = {
            "status": status,
            "memory": memory_summary,
            "operation_results": results,
            "policy_evaluation": policy_evaluation,
            "preservation_requirements": preservation,
            "holds": holds,
            "authority": authority,
            "conflicts": conflicts,
            "unresolved_requirements": unresolved,
            "evidence": evidence,
        }
        identity_hash = stable_hash({"input_fingerprint": input_fingerprint, "resolution": resolution_material})
        report = {
            "id": f"memory.retention_resolution.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            "read_only": True,
            "derived_view": True,
            "request": {
                "consumer": consumer,
                "actor_roles": roles,
                "requested_operations": operations,
                "organizational_mode": organizational_mode,
                "authority_scope": authority_scope,
                "evaluation_time": evaluated_at,
            },
            "memory": memory_summary,
            "summary": {
                "status": status,
                "policies_supplied": len(policy_inputs),
                "policies_applied": len(applied),
                "conflicts": len(conflicts),
                "unresolved_requirements": len(unresolved),
                "active_holds": len(holds),
            },
            "policy_evaluation": policy_evaluation,
            "preservation_requirements": preservation,
            "holds": holds,
            "operation_results": results,
            "authority": {
                "resolver_level": "L1",
                "authority_granted": False,
                "approval_recorded": False,
                "by_operation": authority,
                "legal_interpretation_performed": False,
            },
            "conflicts": conflicts,
            "unresolved_requirements": unresolved,
            "evidence": evidence,
            "bindings": {
                "memory_metadata_hash": memory_hash,
                "input_fingerprint": input_fingerprint,
                "source_fingerprint": source_fingerprint,
                "source_checks": source_evidence,
            },
            "mutation": {
                "occurred": False,
                "memory_content_changed": False,
                "retention_state_changed": False,
                "access_changed": False,
                "holds_changed": False,
                "canonical_context_changed": False,
            },
            "invalidation": {
                "conditions": [
                    "Memory identity, metadata, sensitivity, retention state, temporal state, or lineage changes.",
                    "An evaluated policy identity, version, scope, effect, obligation, hold, or provenance changes.",
                    "Consumer, actor roles, requested operations, evaluation time, or organizational scope changes.",
                    "A bound source hash changes or becomes unavailable.",
                    "Applicable authority or legal/compliance interpretation changes.",
                ]
            },
            "limitations": [
                "Resolution evaluates supplied explicit policy; it does not create policy or legal interpretation.",
                "No result grants authority, approves a transition, or mutates memory.",
                "No-policy and unknown-policy states never become implicit permission.",
                "Restricted metadata is omitted according to the supplied metadata visibility boundary.",
                "Retrieval and Activation remain separate derived consumers of this result.",
            ],
        }
        return build_report(self.root, report, generated_at)

    def check_resolution(
        self,
        report: dict,
        memory_item: dict,
        policies: list[dict],
        *,
        consumer: str,
        actor_roles: list[str] | tuple[str, ...] = (),
        requested_operations: list[str] | tuple[str, ...] = OPERATIONS,
        organizational_mode: str | None = None,
        authority_scope: str | None = None,
        evaluation_time: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if report.get("schema") != "contextos.memory.retention_resolution/1":
            raise ValueError("Retention resolution check requires contextos.memory.retention_resolution/1 input.")
        identity_valid = report.get("identity_hash") == stable_hash(self._identity_payload(report))
        current = self.run(
            memory_item,
            policies,
            consumer=consumer,
            actor_roles=actor_roles,
            requested_operations=requested_operations,
            organizational_mode=organizational_mode,
            authority_scope=authority_scope,
            evaluation_time=evaluation_time,
            generated_at=generated_at,
        )
        input_unchanged = report.get("bindings", {}).get("input_fingerprint") == current["bindings"]["input_fingerprint"]
        source_state_unchanged = report.get("bindings", {}).get("source_fingerprint") == current["bindings"]["source_fingerprint"]
        resolution_unchanged = report.get("identity_hash") == current["identity_hash"]
        failed = []
        if not identity_valid:
            failed.append("retention_resolution_check.identity_hash_mismatch")
        if not input_unchanged:
            failed.append("retention_resolution_check.input_changed")
        if not source_state_unchanged:
            failed.append("retention_resolution_check.source_state_changed")
        if not resolution_unchanged:
            failed.append("retention_resolution_check.resolution_changed")
        valid = not failed
        return {
            "schema": CHECK_SCHEMA,
            "generated_at": generated_at or generated_timestamp(),
            "root": str(self.root),
            "read_only": True,
            "resolution": {"id": report.get("id"), "identity_hash": report.get("identity_hash")},
            "checks": {
                "identity_valid": identity_valid,
                "input_unchanged": input_unchanged,
                "source_state_unchanged": source_state_unchanged,
                "resolution_unchanged": resolution_unchanged,
            },
            "current": {
                "id": current["id"],
                "identity_hash": current["identity_hash"],
                "input_fingerprint": current["bindings"]["input_fingerprint"],
                "source_fingerprint": current["bindings"]["source_fingerprint"],
            },
            "result": {"valid": valid, "invalidated": not valid, "failed_checks": failed},
        }

    def _validate(self, memory: dict, policies: list[dict], consumer: str, operations: list[str]) -> None:
        if not isinstance(memory, dict) or not memory.get("id"):
            raise ValueError("Retention resolution requires memory.id.")
        if memory.get("form") not in MEMORY_FORMS:
            raise ValueError(f"Unsupported memory form: {memory.get('form')!r}.")
        if memory.get("retention_state") not in RETENTION_STATES:
            raise ValueError(f"Unsupported retention state: {memory.get('retention_state')!r}.")
        if memory.get("sensitivity") not in SENSITIVITY:
            raise ValueError(f"Unsupported sensitivity: {memory.get('sensitivity')!r}.")
        visibility = memory.get("metadata_visibility", "identity_only")
        if visibility not in VISIBILITY:
            raise ValueError(f"Unsupported metadata visibility: {visibility!r}.")
        if not consumer or not consumer.strip():
            raise ValueError("Retention resolution requires a consumer.")
        if not operations or any(operation not in OPERATIONS for operation in operations):
            raise ValueError("Retention resolution requested an unsupported operation.")
        if not isinstance(policies, list):
            raise ValueError("Retention policies must be a list.")
        for policy in policies:
            if policy.get("schema") != "contextos.memory.retention_policy/1":
                raise ValueError("Every policy must use contextos.memory.retention_policy/1.")
            if not policy.get("id") or not policy.get("version"):
                raise ValueError("Every retention policy requires id and version.")
            for operation, outcome in policy.get("effects", {}).items():
                if operation not in OPERATIONS or outcome not in OUTCOMES:
                    raise ValueError(f"Invalid policy effect {operation!r}: {outcome!r}.")

    def _applicable_policies(
        self, memory: dict, policies: list[dict], evaluated_at: str
    ) -> tuple[list[dict], list[dict], list[dict]]:
        applied = []
        not_applied = []
        unresolved = []
        supplied_ids = {policy["id"] for policy in policies if policy.get("status") == "active"}
        for policy in sorted(policies, key=lambda item: (item["id"], item["version"])):
            visibility = policy.get("explanation_visibility", "id_only")
            display_id = _display_id(policy["id"], "none" if visibility == "none" else "identity_only")
            if policy.get("status") != "active":
                not_applied.append({"display_id": display_id, "reason": "policy_not_active"})
                continue
            temporal, temporal_reason = self._temporal_match(policy, evaluated_at)
            if temporal is None:
                unresolved.append(
                    {
                        "id": f"retention.unresolved.temporal.{stable_hash(policy['id'])[:12]}",
                        "kind": "policy_temporal_applicability_unknown",
                        "message": "Policy temporal applicability could not be established from supplied values.",
                        "required_authority": ["policy_owner"],
                    }
                )
                not_applied.append({"display_id": display_id, "reason": temporal_reason})
                continue
            if not temporal:
                not_applied.append({"display_id": display_id, "reason": temporal_reason})
                continue
            missing_parent = next((parent for parent in policy.get("inherits_from", []) if parent not in supplied_ids), None)
            if missing_parent:
                unresolved.append(
                    {
                        "id": f"retention.unresolved.missing_parent.{stable_hash(policy['id'])[:12]}",
                        "kind": "policy_inheritance_missing",
                        "message": "An inherited policy required for resolution was not supplied as active.",
                        "required_authority": ["policy_owner"],
                    }
                )
                not_applied.append({"display_id": display_id, "reason": "inherited_policy_missing"})
                continue
            outcome, reason = self._scope_match(memory, policy.get("scope", {}))
            if outcome is None:
                unresolved.append(
                    {
                        "id": f"retention.unresolved.applicability.{stable_hash(policy['id'])[:12]}",
                        "kind": "policy_applicability_unknown",
                        "message": "Policy applicability could not be established from supplied metadata.",
                        "required_authority": ["policy_owner"],
                    }
                )
                not_applied.append({"display_id": display_id, "reason": "policy_applicability_unknown"})
            elif outcome:
                applied.append(policy)
                review_due = policy.get("review_due")
                if review_due:
                    try:
                        due = _parse_timestamp(review_due)
                        if _parse_timestamp(evaluated_at) >= due:
                            unresolved.append(
                                {
                                    "id": f"retention.unresolved.review_due.{stable_hash(policy['id'])[:12]}",
                                    "kind": "policy_review_due",
                                    "message": "An applicable policy is due for accountable human review.",
                                    "required_authority": ["policy_owner"],
                                }
                            )
                    except (TypeError, ValueError):
                        unresolved.append(
                            {
                                "id": f"retention.unresolved.review_condition.{stable_hash(policy['id'])[:12]}",
                                "kind": "policy_review_condition_unresolved",
                                "message": "The supplied policy review condition requires accountable interpretation.",
                                "required_authority": ["policy_owner"],
                            }
                        )
            else:
                not_applied.append({"display_id": display_id, "reason": reason})
        return applied, not_applied, unresolved

    @staticmethod
    def _temporal_match(policy: dict, evaluated_at: str) -> tuple[bool | None, str]:
        try:
            evaluated = _parse_timestamp(evaluated_at)
            effective_from = policy.get("effective_from")
            effective_until = policy.get("effective_until")
            if effective_from and evaluated < _parse_timestamp(effective_from):
                return False, "policy_not_yet_effective"
            if effective_until and evaluated >= _parse_timestamp(effective_until):
                return False, "policy_no_longer_effective"
        except (TypeError, ValueError):
            return None, "policy_temporal_applicability_unknown"
        return True, "policy_temporally_applicable"

    @staticmethod
    def _scope_match(memory: dict, scope: dict) -> tuple[bool | None, str]:
        checks = (
            ("organization", "organizations"),
            ("operation", "operations"),
            ("form", "memory_forms"),
            ("tier", "memory_tiers"),
            ("id", "memory_ids"),
            ("sensitivity", "sensitivities"),
            ("jurisdiction", "jurisdictions"),
        )
        for memory_key, scope_key in checks:
            allowed = scope.get(scope_key, [])
            if not allowed:
                continue
            value = memory.get(memory_key)
            if value is None or value == "unknown":
                return None, f"missing_{memory_key}"
            if value not in allowed:
                return False, f"scope_mismatch_{memory_key}"
        return True, "scope_matched"

    @staticmethod
    def _obligations(applied: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
        preservation = []
        holds = []
        preserve_policies = set()
        removal_policies = set()
        interpretation = []
        for policy in applied:
            for obligation in policy.get("obligations", []):
                kind = obligation.get("kind")
                if kind == "preserve":
                    preserve_policies.add(policy["id"])
                    obligation_id = obligation["id"] if policy.get("explanation_visibility") != "none" else "<restricted>"
                    preservation.append({"id": obligation_id, "policy_id": _policy_ref(policy), "kind": kind})
                elif kind in {"delete", "delete_or_minimize", "minimize"}:
                    removal_policies.add(policy["id"])
                if obligation.get("requires_interpretation"):
                    interpretation.append((policy["id"], obligation["id"]))
            for hold in policy.get("holds", []):
                if hold.get("active"):
                    holds.append(
                        {
                            "id_hash": stable_hash(hold["id"])
                            if hold.get("metadata_visibility") != "none"
                            else None,
                            "display_id": _display_id(hold["id"], "none" if hold.get("metadata_visibility") == "none" else "identity_only"),
                            "policy_id": _policy_ref(policy),
                            "required_roles": sorted(set(hold.get("required_roles", ["legal_compliance_role"]))),
                        }
                    )
                    preserve_policies.add(policy["id"])
                    hold_ref = f"hold:{stable_hash(hold['id'])[:12]}" if hold.get("metadata_visibility") != "none" else "<restricted>"
                    preservation.append({"id": hold_ref, "policy_id": _policy_ref(policy), "kind": "hold"})
        conflicts = []
        if preserve_policies and removal_policies:
            conflicts.append(
                {
                    "id": "retention.conflict.preservation_vs_removal",
                    "kind": "preservation_vs_deletion_or_minimization",
                    "message": "Preservation and deletion/minimization duties conflict; no legal precedence was inferred.",
                    "policy_ids": sorted(
                        _policy_ref(policy)
                        for policy in applied
                        if policy["id"] in preserve_policies | removal_policies
                    ),
                    "affected_operations": ["retention_transition", "destructive_action"],
                    "required_authority": ["governance_role", "legal_compliance_role"],
                }
            )
        for policy_id, obligation_id in interpretation:
            conflicts.append(
                {
                    "id": f"retention.conflict.interpretation.{stable_hash({'policy': policy_id, 'obligation': obligation_id})[:12]}",
                    "kind": "legal_or_compliance_interpretation_required",
                    "message": "A supplied obligation explicitly requires accountable human interpretation.",
                    "policy_ids": [
                        _policy_ref(next(policy for policy in applied if policy["id"] == policy_id))
                    ],
                    "affected_operations": list(OPERATIONS),
                    "required_authority": ["legal_compliance_role", "governance_role"],
                }
            )
        return preservation, holds, conflicts

    def _operation_results(
        self,
        memory: dict,
        applied: list[dict],
        holds: list[dict],
        conflicts: list[dict],
        unresolved: list[dict],
        actor_roles: list[str],
        operations: list[str],
    ) -> tuple[dict, dict]:
        results = {}
        authority = {}
        for operation in operations:
            outcome = "unknown"
            reasons = []
            policy_ids = []
            required_roles = set()
            for policy in applied:
                effect = policy.get("effects", {}).get(operation)
                if effect:
                    outcome = _restrictive(outcome, effect)
                    reasons.append(f"policy_effect:{_policy_ref(policy)}")
                    policy_ids.append(_policy_ref(policy))
                required_roles.update(policy.get("required_authority", {}).get(operation, []))

            state_outcome, state_reason = self._state_baseline(memory["retention_state"], operation)
            if state_outcome:
                outcome = _restrictive(outcome, state_outcome)
                reasons.append(state_reason)
            sensitivity_outcome, sensitivity_reason = self._sensitivity_baseline(
                memory["sensitivity"], operation, memory.get("metadata_visibility", "identity_only")
            )
            if sensitivity_outcome:
                outcome = _restrictive(outcome, sensitivity_outcome)
                reasons.append(sensitivity_reason)

            if operation in {"retention_transition", "destructive_action"} and not applied:
                outcome = "prohibited"
                reasons.append("missing_policy_blocks_mutation")
            if operation == "retention_transition":
                outcome = _restrictive(outcome, "elevated_authority")
                reasons.append("human_L3_decision_required")
            if operation == "destructive_action":
                outcome = "prohibited"
                reasons.append("destructive_execution_contract_absent")
            if holds and operation in {"retention_transition", "destructive_action"}:
                outcome = "prohibited"
                reasons.append("active_hold_blocks_transition")
                for hold in holds:
                    required_roles.update(hold["required_roles"])
            affected_conflicts = [conflict for conflict in conflicts if operation in conflict["affected_operations"]]
            if affected_conflicts:
                outcome = "prohibited" if operation in {"retention_transition", "destructive_action"} else "unknown"
                reasons.append("policy_conflict_blocks_operation")
                for conflict in affected_conflicts:
                    required_roles.update(conflict["required_authority"])
            if unresolved and outcome == "normal":
                outcome = "elevated_authority"
                reasons.append("unresolved_policy_input")
            missing_roles = sorted(required_roles - set(actor_roles))
            if missing_roles and outcome == "normal":
                outcome = "elevated_authority"
                reasons.append("required_authority_missing")
            if not applied and outcome == "unknown":
                reasons.append("no_policy_permission")

            results[operation] = {
                "outcome": outcome,
                "reason_codes": sorted(set(reasons)),
                "policy_ids": sorted(set(policy_ids)),
                "required_roles": sorted(required_roles),
                "authority_granted": False,
            }
            authority[operation] = {
                "required_roles": sorted(required_roles),
                "present_roles": sorted(set(actor_roles) & required_roles),
                "missing_roles": missing_roles,
                "roles_present": not missing_roles,
                "authority_granted": False,
            }
        return results, authority

    @staticmethod
    def _state_baseline(state: str, operation: str) -> tuple[str | None, str]:
        if state == "historical" and operation == "activation":
            return "excluded", "historical_excluded_from_activation_by_default"
        if state == "archived":
            if operation == "retrieval":
                return "elevated_authority", "archived_requires_explicit_retrieval"
            if operation == "activation":
                return "excluded", "archived_excluded_from_activation"
        if state == "operationally_forgotten" and operation in {"retrieval", "activation"}:
            return "excluded", "operationally_forgotten_excluded_from_normal_use"
        if state == "content_removed" and operation in {"access", "retrieval", "activation", "destructive_action"}:
            return "prohibited", "content_removed_unavailable"
        if state == "unknown" and operation in {"access", "retrieval", "activation"}:
            return "unknown", "retention_state_unknown"
        return None, ""

    @staticmethod
    def _sensitivity_baseline(sensitivity: str, operation: str, visibility: str) -> tuple[str | None, str]:
        label = sensitivity if visibility != "none" else "protected"
        if sensitivity in {"confidential", "restricted", "unknown"}:
            if operation in {"access", "retrieval"}:
                return "elevated_authority", f"{label}_sensitivity_requires_elevated_authority"
            if operation == "activation":
                return "excluded", f"{label}_sensitivity_excluded_from_activation_by_default"
        return None, ""

    def _source_evidence(self, memory: dict, policies: list[dict]) -> tuple[list[dict], str]:
        evidence = []
        raw_evidence = []
        sources = [("memory", memory.get("provenance", {}), memory.get("metadata_visibility") == "none")]
        sources.extend(
            ("policy", policy.get("provenance", {}), policy.get("explanation_visibility") == "none")
            for policy in policies
        )
        for kind, source, restricted in sources:
            path_value = source.get("path") if isinstance(source, dict) else None
            expected = source.get("source_hash") if isinstance(source, dict) else None
            if not path_value:
                continue
            candidate = (self.root / path_value).resolve()
            inside_root = candidate == self.root or self.root in candidate.parents
            exists = inside_root and candidate.is_file()
            current = file_hash(candidate) if exists else None
            raw = {
                "kind": kind,
                "path": path_value,
                "expected_hash": expected,
                "current_hash": current,
                "exists": exists,
                "inside_root": inside_root,
                "matches": exists and expected is not None and current == expected,
            }
            raw_evidence.append(raw)
            evidence.append(
                {
                    "kind": kind,
                    "path_hash": None if restricted else stable_hash(path_value),
                    "expected_hash": None if restricted else expected,
                    "current_hash": None if restricted else current,
                    "exists": exists,
                    "inside_root": inside_root,
                    "matches": raw["matches"],
                    "metadata_redacted": restricted,
                }
            )
        safe = sorted(evidence, key=lambda item: (item["kind"], item["path_hash"] or ""))
        return safe, stable_hash(sorted(raw_evidence, key=lambda item: (item["kind"], item["path"])))

    @staticmethod
    def _safe_evidence(memory: dict, visibility: str) -> dict:
        refs = memory.get("evidence_refs", []) if visibility == "full" else []
        return {
            "refs": refs,
            "ref_count": len(memory.get("evidence_refs", [])),
            "metadata_redacted": visibility != "full",
            "provenance_bound": bool(memory.get("provenance")),
        }

    @staticmethod
    def _policy_summary(policy: dict) -> dict:
        visibility = policy.get("explanation_visibility", "id_only")
        return {
            "display_id": _display_id(policy["id"], "none" if visibility == "none" else "identity_only"),
            "identity_hash": stable_hash(policy["id"]) if visibility != "none" else None,
            "version": policy["version"],
            "policy_hash": stable_hash(policy) if visibility != "none" else None,
            "scope": copy.deepcopy(policy.get("scope", {})) if visibility != "none" else {},
            "reason_codes": ["active", "scope_matched", "explicit_policy_input"],
        }

    @staticmethod
    def _status(results: dict, conflicts: list[dict], unresolved: list[dict]) -> str:
        if conflicts:
            return "blocked"
        outcomes = {item["outcome"] for item in results.values()}
        if outcomes == {"unknown"}:
            return "unknown"
        if unresolved or "unknown" in outcomes or "elevated_authority" in outcomes:
            return "partially_resolved"
        return "resolved"

    @staticmethod
    def _identity_payload(report: dict) -> dict:
        return {
            "input_fingerprint": report.get("bindings", {}).get("input_fingerprint"),
            "resolution": {
                "status": report.get("summary", {}).get("status"),
                "memory": report.get("memory"),
                "operation_results": report.get("operation_results"),
                "policy_evaluation": report.get("policy_evaluation"),
                "preservation_requirements": report.get("preservation_requirements"),
                "holds": report.get("holds"),
                "authority": report.get("authority", {}).get("by_operation"),
                "conflicts": report.get("conflicts"),
                "unresolved_requirements": report.get("unresolved_requirements"),
                "evidence": report.get("evidence"),
            },
        }
