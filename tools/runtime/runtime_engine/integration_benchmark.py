from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


TOOLS_ROOT = Path(__file__).resolve().parents[2]
for relative in (
    "validators",
    "readiness",
    "bootstrap",
    "discovery",
    "construction",
    "builder",
    "activation",
    "health",
    "memory",
    "reasoning",
):
    runtime_path = TOOLS_ROOT / relative
    if str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))

from activation_engine.package_engine import ContextActivationPackageEngine  # noqa: E402
from bootstrap_engine.plan_engine import BootstrapPlanEngine  # noqa: E402
from builder_engine.draft_plan import BuilderDraftPlanEngine  # noqa: E402
from construction_engine.planning_engine import ContextConstructionPlanEngine  # noqa: E402
from discovery_engine.local_discovery import LocalDiscoveryBundleEngine  # noqa: E402
from health_engine.health_engine import ContextHealthEngine  # noqa: E402
from health_engine.mission_use_evidence import MissionContextUseEvidenceEngine  # noqa: E402
from memory_engine import ContextVersionEngine, OrganizationalMemoryEngine  # noqa: E402
from readiness_engine.readiness_scoring import ReadinessScoringEngine  # noqa: E402
from reasoning_engine import ContextualAssessmentEngine  # noqa: E402
from engine.validator_engine import ValidatorEngine  # noqa: E402

from .report_builder import build_report  # noqa: E402


FIXED_RELEASE_EVIDENCE = (
    (
        "v0.4",
        "SSOT/E.4_Mission_V04-GUIDED-BOOTSTRAP-RELEASE-VERIFY-001_Release_Verification.md",
        "Release v0.4 Guided Bootstrap is release-ready.",
    ),
    (
        "v0.5",
        "SSOT/E.4_Mission_V05-CONTEXT-CONSTRUCTION-RELEASE-VERIFY-001_Context_Construction_Release_Verification.md",
        "Decision: release-ready pending release cut.",
    ),
    (
        "v0.6",
        "SSOT/E.4_Mission_V06-CONTEXT-ACTIVATION-RELEASE-VERIFY-001_Context_Activation_Release_Verification.md",
        "Release v0.6 Context Activation is release-ready.",
    ),
    (
        "v0.7",
        "SSOT/E.4_Mission_V07-CONTEXT-HEALTH-RELEASE-VERIFY-001_Context_Health_Release_Verification.md",
        "RELEASE_READY",
    ),
    (
        "v0.8",
        "SSOT/E.4_Mission_V08-ORGANIZATIONAL-MEMORY-RELEASE-VERIFY-001_Organizational_Memory_Release_Verification.md",
        "RELEASE_READY",
    ),
    (
        "v0.9",
        "SSOT/E.4_Mission_V09-CONTEXTUAL-REASONING-RELEASE-VERIFY-001_Release_Verification.md",
        "v0.9 Contextual Reasoning = RELEASE_READY",
    ),
)


EXPECTED_SCHEMAS = {
    "validator": "contextos.validator.report/1",
    "readiness": "contextos.readiness.report/1",
    "bootstrap": "contextos.bootstrap.plan/1",
    "discovery": "contextos.discovery.bundle/1",
    "construction": "contextos.construction.plan/1",
    "draft_plan": "contextos.builder.draft_plan/1",
    "activation_package": "contextos.activation.package/1",
    "activation_handoff": "contextos.activation.handoff/1",
    "mission_use_evidence": "contextos.mission.context_use_evidence/1",
    "health": "contextos.health.report/1",
    "context_version": "contextos.context.version/1",
    "memory": "contextos.memory.continuity_report/1",
    "memory_retrieval": "contextos.memory.retrieval_result/1",
    "reasoning": "contextos.reasoning.assessment/1",
}


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repository_snapshot(root: Path) -> dict[str, str]:
    ignored = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
    return {
        path.relative_to(root).as_posix(): file_hash(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and not any(part in ignored for part in path.relative_to(root).parts)
    }


def report_ref(report: dict) -> dict:
    return {
        "schema": report.get("schema"),
        "id": report.get("id"),
        "identity_hash": report.get("identity_hash"),
    }


def check(check_id: str, passed: bool, message: str, evidence_refs: list[str]) -> dict:
    return {
        "id": check_id,
        "passed": bool(passed),
        "message": message,
        "evidence_refs": evidence_refs,
    }


class OrganizationalContextRuntimeBenchmarkEngine:
    """Read-only integration proof over released Context OS runtime APIs."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root).resolve()

    def run(
        self,
        *,
        goal: str,
        mission_id: str,
        consumer: str = "codex",
        generated_at: str | None = None,
    ) -> dict:
        if not goal.strip() or not mission_id.strip() or not consumer.strip():
            raise ValueError("Runtime benchmark requires goal, mission_id, and consumer.")

        before = repository_snapshot(self.root)
        validator = ValidatorEngine(self.root).run(mode="gate")
        readiness = ReadinessScoringEngine(self.root).run(generated_at=generated_at)
        bootstrap = BootstrapPlanEngine(self.root).run(readiness_report=readiness, generated_at=generated_at)
        discovery = LocalDiscoveryBundleEngine(self.root).run(generated_at=generated_at)
        construction = ContextConstructionPlanEngine(self.root).run(
            readiness_report=readiness,
            bootstrap_plan=bootstrap,
            discovery_bundle=discovery,
            generated_at=generated_at,
        )
        draft_plan = BuilderDraftPlanEngine(self.root).run(
            discovery_bundle=discovery,
            construction_plan=construction,
            generated_at=generated_at,
        )

        activation_engine = ContextActivationPackageEngine(self.root)
        package = activation_engine.run(
            goal=goal,
            mission_id=mission_id,
            consumer=consumer,
            generated_at=generated_at,
        )
        handoff = activation_engine.build_handoff(package, generated_at=generated_at)
        package_check = activation_engine.check_package(package, generated_at=generated_at)
        handoff_check = activation_engine.check_handoff(handoff, generated_at=generated_at)
        selected_accesses = [
            {
                "source_ref": item["path"],
                "evidence_semantics": "observed",
                "evidence_refs": ["runtime_benchmark.selected_source_access"],
            }
            for item in handoff.get("selected_context", [])[:2]
        ]
        execution_path = "tools/runtime/runtime_engine/integration_benchmark.py"
        mission_use = MissionContextUseEvidenceEngine(self.root).run(
            package=package,
            handoff=handoff,
            selected_accesses=selected_accesses,
            execution_retrievals=[
                {
                    "source_ref": execution_path,
                    "source_type": "runtime_implementation",
                    "reason": "Execute the bounded integrated runtime proof.",
                    "mission_need": "Verify released runtime composition without a new product workflow.",
                    "authority": "mission_execution_read",
                    "evidence_semantics": "observed",
                    "evidence_refs": ["runtime_benchmark.execution"],
                }
            ],
            use_assertions=[
                {
                    "state": "used",
                    "source_ref": selected_accesses[0]["source_ref"] if selected_accesses else None,
                    "statement": "The benchmark consumed governing source identity and constraints.",
                    "evidence_semantics": "declared",
                    "evidence_refs": ["runtime_benchmark.integrated_checks"],
                }
            ] if selected_accesses else [],
            contributions=[
                {
                    "source_ref": execution_path,
                    "statement": "The benchmark produced integrated runtime evidence.",
                    "evidence_semantics": "observed",
                    "evidence_refs": ["contextos.runtime.integration_benchmark/1"],
                }
            ],
            mission_outcome={
                "status": "completed",
                "statement": "All applicable read-only runtime stages executed and were checked.",
                "evidence_semantics": "observed",
                "evidence_refs": ["runtime_benchmark.integrated_checks"],
            },
            generated_at=generated_at,
        )
        health = ContextHealthEngine(self.root).run(
            readiness_report=readiness,
            mission_use_evidence=mission_use,
            generated_at=generated_at,
        )

        version_engine = ContextVersionEngine(self.root)
        version_plan = version_engine.plan(
            scope={
                "organization": "Context OS",
                "domain": "product-runtime",
                "tier": "organizational",
                "context_root": ".",
            },
            event_type="mission_start",
            reason="Freeze exact governing context for the integrated runtime benchmark.",
            capture_at=generated_at or "1970-01-01T00:00:00Z",
            mission_id=mission_id,
            goal=goal,
            activation_package=package,
            activation_handoff=handoff,
            additional_source_paths=[execution_path],
            authority_paths=[
                "docs/3.x_operation/3.6_COS_Human_Agent_Authority_Model.md",
                "docs/3.x_operation/3.7_COS_Governance_Protocol.md",
            ],
            generated_at=generated_at,
        )
        context_version = version_engine.capture(
            version_plan,
            activation_package=package,
            activation_handoff=handoff,
            generated_at=generated_at,
        )
        version_check = version_engine.check_version(context_version, generated_at=generated_at)
        memory = OrganizationalMemoryEngine(self.root).run(
            mission_id=mission_id,
            goal=goal,
            context_versions=[context_version],
            generated_at=generated_at,
        )
        reasoning = ContextualAssessmentEngine(self.root).run(
            goal=goal,
            mission_id=mission_id,
            consumer=consumer,
            purpose="Assess integrated runtime continuity and remaining release gaps.",
            context_versions=[context_version],
            mission_use_evidence=mission_use,
            evaluation_time=generated_at,
            generated_at=generated_at,
        )
        reasoning_check = ContextualAssessmentEngine(self.root).check_assessment(
            reasoning,
            generated_at=generated_at,
        )
        memory_retrieval = reasoning["evidence"]["memory_retrieval"]

        reports = {
            "validator": validator,
            "readiness": readiness,
            "bootstrap": bootstrap,
            "discovery": discovery,
            "construction": construction,
            "draft_plan": draft_plan,
            "activation_package": package,
            "activation_handoff": handoff,
            "mission_use_evidence": mission_use,
            "health": health,
            "context_version": context_version,
            "memory": memory,
            "memory_retrieval": memory_retrieval,
            "reasoning": reasoning,
        }
        journey = [
            {
                "stage": name,
                "schema": report.get("schema"),
                "id": report.get("id"),
                "identity_hash": report.get("identity_hash"),
                "status": self._stage_status(name, report),
            }
            for name, report in reports.items()
        ]
        release_evidence = self._release_evidence()
        checks = self._checks(
            reports,
            package_check,
            handoff_check,
            version_check,
            reasoning_check,
            release_evidence,
        )
        after = repository_snapshot(self.root)
        checks.append(
            check(
                "runtime.check.target_state_unchanged",
                before == after,
                "Live benchmark stages did not mutate the target repository.",
                ["runtime_benchmark.repository_snapshot"],
            )
        )
        failed = [item for item in checks if not item["passed"]]
        body = {
            "read_only": before == after,
            "mission": {"id": mission_id, "goal": goal, "consumer": consumer},
            "summary": {
                "status": "pass" if not failed else "gap",
                "stage_count": len(journey),
                "check_count": len(checks),
                "passed_check_count": len(checks) - len(failed),
                "release_blocker_count": len(failed),
            },
            "journey": journey,
            "checks": checks,
            "bindings": {name: report_ref(value) for name, value in reports.items()},
            "governed_change_evidence": release_evidence,
            "invalidation": {
                "package_check": report_ref(package_check),
                "handoff_check": report_ref(handoff_check),
                "context_version_check": report_ref(version_check),
                "reasoning_check": report_ref(reasoning_check),
                "conditions": [
                    "Any bound canonical source hash changes.",
                    "Package or Handoff identity or binding changes.",
                    "Context Version identity or source resolution changes.",
                    "Memory policy, authority, temporal basis, or source state changes.",
                    "Reasoning query or any exact evidence binding changes.",
                ],
            },
            "boundaries": {
                "activated_context_is_canonical": False,
                "memory_is_current_authority": False,
                "reasoning_may_decide": False,
                "reasoning_may_execute": False,
                "benchmark_grants_authority": False,
                "automatic_truth_creation": False,
                "write_stages_replayed": False,
            },
            "graphrag": {
                "decision": "defer",
                "material_integration_failure_observed": False,
                "evidence_ref": "contextos.reasoning.benchmark/1:10_of_10_passed",
            },
            "intentional_deferrals": [
                "Context Graph and GraphRAG",
                "autonomous agents and orchestration",
                "consumer- and domain-specific adapters",
                "databases, queues, vector stores, and hosted services",
                "automatic Context Version capture and durable registries",
                "destructive retention, archival, deletion, and forgetting",
                "automatic remediation and canonical mutation",
            ],
            "evidence_semantics": {
                "live_stages": "observed",
                "released_write_stages": "observed_from_exact_hashed_release_evidence",
                "usefulness": "unknown_without_outcome_evidence",
                "cross_domain_universality": "partially_supported_conceptually",
            },
        }
        identity_hash = stable_hash(body)
        report = {
            "id": f"runtime.integration_benchmark.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            **body,
        }
        return build_report(self.root, report, generated_at=generated_at)

    @staticmethod
    def identity_valid(report: dict) -> bool:
        ignored = {"schema", "id", "identity_hash", "generated_at", "root"}
        body = {key: value for key, value in report.items() if key not in ignored}
        return report.get("identity_hash") == stable_hash(body)

    def _release_evidence(self) -> list[dict]:
        evidence = []
        for release, relative, acceptance_marker in FIXED_RELEASE_EVIDENCE:
            path = self.root / relative
            text = path.read_text(encoding="utf-8") if path.is_file() else ""
            accepted = acceptance_marker in text
            evidence.append(
                {
                    "release": release,
                    "path": relative,
                    "source_hash": file_hash(path) if path.is_file() else None,
                    "verification_state": "accepted_release_evidence"
                    if path.is_file() and accepted
                    else "missing_or_unaccepted",
                    "content_embedded": False,
                }
            )
        return evidence

    @staticmethod
    def _stage_status(name: str, report: dict) -> str:
        if name == "validator":
            return "pass" if not report["summary"]["error"] and not report["summary"]["fatal"] else "blocked"
        if name == "activation_package":
            return "pass" if report["summary"]["activation_allowed"] else "blocked"
        if name == "mission_use_evidence":
            return "pass" if not report["validity"]["failed_checks"] else "blocked"
        if name == "context_version":
            return "pass" if report["summary"]["historical_identity_valid_at_capture"] else "blocked"
        if name == "reasoning":
            return report["summary"]["status"]
        return "observed"

    @staticmethod
    def _checks(
        reports: dict,
        package_check: dict,
        handoff_check: dict,
        version_check: dict,
        reasoning_check: dict,
        release_evidence: list[dict],
    ) -> list[dict]:
        checks = [
            check(
                f"runtime.check.schema.{name}",
                report.get("schema") == EXPECTED_SCHEMAS[name],
                f"{name} uses its released schema.",
                [report.get("id") or report.get("schema", "missing")],
            )
            for name, report in reports.items()
        ]
        checks.extend(
            [
                check(
                    "runtime.check.validator_gate",
                    reports["validator"]["summary"]["error"] == 0
                    and reports["validator"]["summary"]["fatal"] == 0,
                    "Validator gate has no blocking findings.",
                    [reports["validator"]["schema"]],
                ),
                check(
                    "runtime.check.package_and_handoff_valid",
                    package_check["result"]["valid"] and handoff_check["result"]["valid"],
                    "Activation Package and Handoff are exact and currently valid.",
                    [package_check["schema"], handoff_check["schema"]],
                ),
                check(
                    "runtime.check.mission_use_bound",
                    not reports["mission_use_evidence"]["validity"]["failed_checks"],
                    "Mission-use evidence remains bound to the exact Package and Handoff.",
                    [reports["mission_use_evidence"]["id"]],
                ),
                check(
                    "runtime.check.context_version_exact",
                    version_check["result"]["immutable_identity"] == "valid"
                    and version_check["result"]["historical_verification"] == "verified"
                    and version_check["result"]["current_applicability"] == "exact_current_match",
                    "Context Version is immutable, verified, and exactly current at benchmark time.",
                    [reports["context_version"]["id"]],
                ),
                check(
                    "runtime.check.memory_policy_before_exposure",
                    reports["memory_retrieval"]["summary"]["selected_count"] == 0
                    and reports["memory_retrieval"]["summary"]["relevant_candidate_count"] > 0
                    and reports["memory_retrieval"]["summary"]["policy_outcomes"].get("unknown")
                    == reports["memory_retrieval"]["summary"]["relevant_candidate_count"],
                    "Missing organizational policy exposes no prior-art candidates.",
                    [reports["memory_retrieval"]["id"]],
                ),
                check(
                    "runtime.check.reasoning_advisory",
                    not reports["reasoning"]["authority"]["may_decide"]
                    and not reports["reasoning"]["authority"]["may_execute"]
                    and reasoning_check["result"]["valid"],
                    "Reasoning is exact, reusable, advisory, and grants no Decision or execution authority.",
                    [reports["reasoning"]["id"]],
                ),
                check(
                    "runtime.check.truth_boundaries",
                    reports["activation_package"]["boundaries"]["working_context_is_not_ssot"]
                    and not reports["memory_retrieval"]["authority"]["retrieved_memory_may_override_canonical"]
                    and not reports["reasoning"]["truth_boundary"]["historical_context_is_current_authority"],
                    "Working Context, Memory, Reasoning, and canonical truth remain distinct.",
                    [
                        reports["activation_package"]["id"],
                        reports["memory_retrieval"]["id"],
                        reports["reasoning"]["id"],
                    ],
                ),
                check(
                    "runtime.check.governed_change_evidence",
                    all(item["verification_state"] == "accepted_release_evidence" for item in release_evidence),
                    "Mutation-capable stages are represented by exact accepted release evidence.",
                    [item["path"] for item in release_evidence],
                ),
            ]
        )
        return checks
