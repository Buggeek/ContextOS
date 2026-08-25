from __future__ import annotations

from collections import Counter

from .assessment_engine import stable_hash
from .report_builder import BENCHMARK_SCHEMA, build_benchmark_report


REQUIRED_CLASSES = {
    "current_state",
    "historical_applicability",
    "contradiction_detection",
    "impact_analysis",
    "hypothesis_formation",
    "recommendation_generation",
    "missing_evidence",
    "prior_art",
    "policy_authority",
    "multi_hop_relationship",
}


class ReasoningBenchmarkEngine:
    """Evaluate controlled Contextual Assessments without generating answers."""

    def run(self, cases: list[dict], *, generated_at: str | None = None) -> dict:
        classes = {case.get("reasoning_class") for case in cases}
        missing_classes = sorted(REQUIRED_CLASSES - classes)
        results = [self._evaluate_case(case) for case in cases]
        counts = Counter("passed" if item["passed"] else "failed" for item in results)
        unexpected = [item["id"] for item in results if not item["expectation_matched"]]
        graph_decision = self._graph_decision(results)
        identity_payload = {
            "cases": [
                {
                    "id": item["id"],
                    "reasoning_class": item["reasoning_class"],
                    "assessment": item["assessment"],
                    "expected_result": item["expected_result"],
                    "checks": item["checks"],
                }
                for item in results
            ],
            "missing_classes": missing_classes,
            "graph_decision": graph_decision,
        }
        identity_hash = stable_hash(identity_payload)
        report = {
            "id": f"reasoning.benchmark.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            "read_only": True,
            "deterministic": True,
            "summary": {
                "status": "complete" if not missing_classes and not unexpected else "invalid",
                "case_count": len(results),
                "passed_count": counts["passed"],
                "failed_count": counts["failed"],
                "missing_required_classes": missing_classes,
                "unexpected_result_count": len(unexpected),
                "release_gap_count": counts["failed"],
            },
            "cases": results,
            "graphrag": graph_decision,
            "authority": {
                "level": "L1_inspect",
                "benchmark_may_change_architecture": False,
                "benchmark_may_adopt_dependency": False,
                "human_architecture_authority_required_for_adoption": True,
            },
            "limitations": [
                "The benchmark evaluates supplied assessments; it does not generate or repair reasoning answers.",
                "A failed class remains a release gap even when the failure was expected.",
                "GraphRAG cannot be adopted without a controlled structured-versus-graph comparison.",
            ],
        }
        return build_benchmark_report(report, generated_at)

    def _evaluate_case(self, case: dict) -> dict:
        assessment = case.get("assessment")
        if not isinstance(assessment, dict) or assessment.get("schema") != "contextos.reasoning.assessment/1":
            raise ValueError(f"Benchmark case {case.get('id', '<unknown>')} requires a Contextual Assessment.")
        expected = case.get("expected", {})
        checks = []

        for assertion_type, minimum in sorted(expected.get("minimum_assertions", {}).items()):
            actual = len(assessment["reasoning"].get(assertion_type, []))
            checks.append(self._check(f"minimum_assertions.{assertion_type}", actual >= minimum, minimum, actual))

        for assertion_type, fragments in sorted(expected.get("statement_fragments", {}).items()):
            statements = [item["statement"].lower() for item in assessment["reasoning"].get(assertion_type, [])]
            for fragment in fragments:
                matched = any(fragment.lower() in statement for statement in statements)
                checks.append(self._check(f"statement.{assertion_type}.{fragment}", matched, fragment, statements))

        if "minimum_selected_memory" in expected:
            actual = assessment["evidence"]["memory_retrieval"]["summary"]["selected_count"]
            minimum = expected["minimum_selected_memory"]
            checks.append(self._check("minimum_selected_memory", actual >= minimum, minimum, actual))

        if expected.get("unknowns_preserved"):
            actual = assessment["summary"]["unknown_count"]
            checks.append(self._check("unknowns_preserved", actual > 0, "> 0", actual))

        if expected.get("authority_boundary", True):
            authority_safe = not any(
                assessment["authority"].get(key, False)
                for key in ("may_decide", "may_approve", "may_execute", "may_mutate_canonical_context")
            )
            checks.append(self._check("authority_boundary", authority_safe, True, authority_safe))

        assertions = [item for values in assessment["reasoning"].values() for item in values]
        unsupported = [item["id"] for item in assertions if not item.get("evidence_refs")]
        checks.append(self._check("material_assertions_have_evidence", not unsupported, [], unsupported))

        passed = all(check["passed"] for check in checks)
        expected_result = case.get("expected_result", "pass")
        if expected_result not in {"pass", "fail"}:
            raise ValueError("Benchmark expected_result must be pass or fail.")
        return {
            "id": case["id"],
            "reasoning_class": case["reasoning_class"],
            "question": case["question"],
            "assessment": {
                "id": assessment["id"],
                "identity_hash": assessment["identity_hash"],
            },
            "expected_result": expected_result,
            "passed": passed,
            "expectation_matched": passed == (expected_result == "pass"),
            "checks": checks,
            "unsupported_claim_count": len(unsupported),
            "unknown_count": assessment["summary"]["unknown_count"],
        }

    @staticmethod
    def _check(check_id: str, passed: bool, expected: object, actual: object) -> dict:
        return {"id": check_id, "passed": passed, "expected": expected, "actual": actual}

    @staticmethod
    def _graph_decision(results: list[dict]) -> dict:
        multi_hop = next((item for item in results if item["reasoning_class"] == "multi_hop_relationship"), None)
        if multi_hop and multi_hop["passed"]:
            rationale = (
                "Bounded traversal over explicitly supplied structured relationships satisfied the controlled multi-hop case; "
                "graph infrastructure is not required."
            )
        else:
            rationale = (
                "The multi-hop case failed, but no structured-versus-graph comparison isolates Retrieval topology as the cause. "
                "Adding GraphRAG would be premature; first close explicit evidence/relationship reasoning gaps."
            )
        return {
            "decision": "defer",
            "structured_multi_hop_passed": bool(multi_hop and multi_hop["passed"]),
            "graph_comparison_performed": False,
            "material_graph_advantage_proven": False,
            "rationale": rationale,
            "reconsider_when": [
                "A controlled real-corpus multi-hop case fails because relevant indirect evidence is not supplied or recovered.",
                "A structured-versus-graph comparison preserves policy, provenance, authority, and explainability.",
            ],
        }
