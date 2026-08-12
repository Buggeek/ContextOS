from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

from activation_engine.report_builder import CHECK_SCHEMA, HANDOFF_SCHEMA, build_report, generated_timestamp


TOOLS_ROOT = Path(__file__).resolve().parents[2]
VALIDATORS_ROOT = TOOLS_ROOT / "validators"
if str(VALIDATORS_ROOT) not in sys.path:
    sys.path.insert(0, str(VALIDATORS_ROOT))

from engine.validator_engine import ValidatorEngine  # noqa: E402


DEFAULT_SOURCE_PATHS = [
    "README.md",
    "SSOT/S.1_Vision.md",
    "SSOT/P.1_Product_Map.md",
    "SSOT/P.2_Product_Roadmap.md",
    "SSOT/A.1_System_Map.md",
    "SSOT/G.1_Definition_of_Ready.md",
    "SSOT/G.2_Definition_of_Done.md",
    "docs/0.x_foundations/0.8_COS_GENESIS.md",
]

ACTIVATION_SOURCE_PATHS = [
    "docs/1.x_architecture/1.0_COS_Architecture.md",
    "docs/1.x_architecture/1.4_COS_Context_Runtime_Architecture.md",
    "docs/1.x_architecture/Runtime_Model.md",
    "docs/5.x_strategy/5.3_COS_Runtime_Strategy.md",
    "docs/5.x_strategy/5.4_COS_Product_Roadmap.md",
    "docs/5.x_strategy/5.5_COS_Runtime_Maturity_Model.md",
    "SSOT/epics/EPIC-008_Runtime_CLI.md",
    "SSOT/E.5_Evolution_Inbox.md",
]

CANONICAL_PREFIXES = ("SSOT/", "docs/", "ops/")
MAX_EXCERPT_CHARS = 2400


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: dict) -> str:
    return sha256_text(json.dumps(value, sort_keys=True, separators=(",", ":")))


def title_for(content: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip() or None
    return None


def owner_for(content: str) -> str | None:
    for line in content.splitlines()[:80]:
        match = re.match(r"^\s*(Owner|Maintainer|Product Owner|Runtime Owner)\s*:\s*(.+?)\s*$", line, re.IGNORECASE)
        if match:
            return match.group(2).strip()
    return None


def tokens_for(value: str) -> set[str]:
    stop = {"and", "the", "for", "with", "into", "from", "that", "this", "contextos", "context", "mission"}
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 2 and token not in stop}


def candidate_paths(root: Path) -> list[str]:
    paths: set[str] = set()
    for path in DEFAULT_SOURCE_PATHS + ACTIVATION_SOURCE_PATHS:
        if (root / path).is_file():
            paths.add(path)
    for base in ("SSOT", "docs/1.x_architecture/1.5_runtime_contracts", "ops"):
        folder = root / base
        if not folder.exists():
            continue
        for path in folder.rglob("*.md"):
            paths.add(path.relative_to(root).as_posix())
    return sorted(paths)


def authority_tier(path: str) -> str:
    if path.startswith("SSOT/"):
        return "ssot"
    if path.startswith("docs/1.x_architecture/1.5_runtime_contracts/"):
        return "runtime_contract"
    if path.startswith("docs/0.x_foundations/"):
        return "foundation"
    if path.startswith("docs/1.x_architecture/"):
        return "architecture"
    if path.startswith("docs/5.x_strategy/"):
        return "strategy"
    if path.startswith("ops/"):
        return "governance"
    if path == "README.md":
        return "repository_entrypoint"
    return "supporting_context"


def lifecycle_state(path: str) -> str:
    if path.startswith("SSOT/"):
        return "canonical_verified"
    return "canonical_reference"


def activation_role(path: str) -> str:
    if path.endswith("S.1_Vision.md"):
        return "intent_anchor"
    if path.endswith("P.2_Product_Roadmap.md"):
        return "release_anchor"
    if path.endswith("0.8_COS_GENESIS.md"):
        return "first_principles_authority"
    if "runtime_contracts" in path:
        return "runtime_contract"
    if "EPIC-008" in path:
        return "cli_surface_context"
    if "Evolution_Inbox" in path:
        return "deferred_context"
    if "Architecture" in path or "architecture" in path:
        return "architecture_context"
    return "working_context_source"


def excerpt_for(content: str, goal_tokens: set[str]) -> str:
    paragraphs = re.split(r"\n\s*\n", content.strip())
    scored: list[tuple[int, int, str]] = []
    for index, paragraph in enumerate(paragraphs):
        paragraph_tokens = tokens_for(paragraph)
        score = len(goal_tokens & paragraph_tokens)
        if paragraph.lstrip().startswith("#"):
            score += 1
        scored.append((score, -index, paragraph.strip()))
    selected = [text for score, _index, text in sorted(scored, reverse=True) if score > 0]
    if not selected:
        selected = [paragraphs[0].strip()] if paragraphs else []
    excerpt = "\n\n".join(selected)
    if len(excerpt) > MAX_EXCERPT_CHARS:
        excerpt = excerpt[:MAX_EXCERPT_CHARS].rstrip() + "\n[excerpt truncated]"
    return excerpt


def score_path(path: str, content: str, goal_tokens: set[str]) -> int:
    score = 0
    if path in DEFAULT_SOURCE_PATHS:
        score += 6
    if path in ACTIVATION_SOURCE_PATHS:
        score += 8
    if path.startswith("SSOT/E.4_Mission_V05") or path.startswith("SSOT/E.4_Mission_SELFHOST"):
        score += 2
    score += len(goal_tokens & tokens_for(path.replace("/", " "))) * 3
    score += len(goal_tokens & tokens_for(content[:8000]))
    return score


class ContextActivationPackageEngine:
    """Read-only activation package builder for mission-bound working context."""

    def __init__(self, root: str | Path = ".") -> None:
        self.root = Path(root)

    def run(
        self,
        *,
        goal: str,
        consumer: str = "human",
        mission_id: str | None = None,
        max_artifacts: int = 12,
        generated_at: str | None = None,
    ) -> dict:
        if not goal or not goal.strip():
            raise ValueError("Activation package requires a goal.")
        if not consumer or not consumer.strip():
            raise ValueError("Activation package requires a consumer.")
        if max_artifacts < 1:
            raise ValueError("Activation package requires at least one artifact.")

        root = self.root.resolve()
        validator_report = ValidatorEngine(root).run(mode="gate")
        goal_tokens = tokens_for(goal + " " + (mission_id or "") + " " + consumer)
        selected, excluded = self._select_sources(root, goal_tokens, max_artifacts)
        source_material = [
            {
                "path": item["path"],
                "hash": item["source_hash"],
                "authority_tier": item["authority_tier"],
                "lifecycle_state": item["lifecycle_state"],
            }
            for item in selected
        ]
        source_fingerprint = stable_hash({"sources": source_material})
        activation_allowed = validator_report["summary"]["error"] == 0 and validator_report["summary"]["fatal"] == 0
        context_gaps = self._context_gaps(selected, activation_allowed, validator_report)
        package = {
            "id": "",
            "identity_hash": "",
            "read_only": True,
            "mode": "package",
            "goal": {
                "statement": goal.strip(),
                "mission_id": mission_id,
                "binding": "mission_bound" if mission_id else "goal_bound",
            },
            "consumer": {
                "type": consumer.strip(),
                "audience": consumer.strip(),
                "surface": "runtime_api",
                "permissions": ["read_canonical_context", "use_working_context"],
                "prohibited_permissions": ["mutate_canonical_context", "promote_context", "delegate_authority"],
            },
            "source_fingerprint": source_fingerprint,
            "summary": {
                "activation_allowed": activation_allowed,
                "included_artifact_count": len(selected),
                "excluded_artifact_count": len(excluded),
                "context_gap_count": len(context_gaps),
                "working_context_is_ssot": False,
            },
            "canonical_sources": source_material,
            "working_context": {
                "representation": "ordered_excerpts_with_source_hashes",
                "not_ssot": True,
                "items": selected,
            },
            "exclusions": excluded,
            "context_gaps": context_gaps,
            "validator": {
                "schema": validator_report["schema"],
                "summary": validator_report["summary"],
            },
            "freshness": {
                "source_fingerprint": source_fingerprint,
                "source_count": len(selected),
                "validator_exit_code": validator_report["summary"]["exit_code"],
                "fresh_at_generation": activation_allowed,
            },
            "provenance": {
                "generated_by": "ContextActivationPackageEngine",
                "source_authority": "canonical_sources_remain_authoritative",
                "evidence_lineage": [item["path"] for item in selected],
            },
            "invalidation": {
                "conditions": [
                    "Any included source hash changes.",
                    "The Validator gate reports errors or fatals.",
                    "The package goal, mission id, consumer, or permissions change.",
                    "A source artifact changes lifecycle state or authority tier.",
                ],
                "source_hashes": {item["path"]: item["source_hash"] for item in selected},
            },
            "boundaries": {
                "canonical_source_authority_preserved": True,
                "working_context_is_derived": True,
                "working_context_is_not_ssot": True,
                "generated_working_context_can_be_invalidated": True,
                "automatic_context_mutation": False,
                "knowledge_engine_used": False,
                "graph_runtime_used": False,
                "agents_orchestrated": False,
                "external_connectors_used": False,
            },
            "constraints": {
                "writes_performed": False,
                "canonical_context_mutated": False,
                "parallel_ssot_created": False,
                "automatic_truth_creation": False,
            },
        }
        package["id"] = f"activation.package.{stable_hash(self._identity_payload(package))[:16]}"
        package["identity_hash"] = stable_hash(self._identity_payload(package))
        return build_report(root, package, generated_at=generated_at)

    def check_package(self, package: dict, *, generated_at: str | None = None) -> dict:
        if package.get("schema") != "contextos.activation.package/1":
            raise ValueError("Activation package check requires contextos.activation.package/1 input.")
        root = self.root.resolve()
        validator_report = ValidatorEngine(root).run(mode="gate")
        identity_valid = package.get("identity_hash") == stable_hash(self._identity_payload(package))
        source_checks = []
        for source in package.get("canonical_sources", []):
            rel_path = source.get("path")
            current_path = root / rel_path
            exists = current_path.is_file()
            current_hash = sha256_file(current_path) if exists else None
            source_checks.append(
                {
                    "path": rel_path,
                    "expected_hash": source.get("hash"),
                    "current_hash": current_hash,
                    "exists": exists,
                    "matches": exists and current_hash == source.get("hash"),
                }
            )
        validator_ok = validator_report["summary"]["error"] == 0 and validator_report["summary"]["fatal"] == 0
        failed = []
        if not identity_valid:
            failed.append("activation_package_check.identity_hash_mismatch")
        failed.extend(f"activation_package_check.source_hash_changed:{check['path']}" for check in source_checks if not check["matches"])
        if not validator_ok:
            failed.append("activation_package_check.validator_gate_blocked")
        current_fingerprint = stable_hash(
            {
                "sources": [
                    {
                        "path": check["path"],
                        "hash": check["current_hash"],
                        "authority_tier": source.get("authority_tier"),
                        "lifecycle_state": source.get("lifecycle_state"),
                    }
                    for check, source in zip(source_checks, package.get("canonical_sources", []))
                ]
            }
        )
        return {
            "schema": CHECK_SCHEMA,
            "generated_at": generated_at or generated_timestamp(),
            "root": str(root),
            "read_only": True,
            "package": {
                "id": package.get("id"),
                "identity_hash": package.get("identity_hash"),
                "goal": package.get("goal"),
                "consumer": package.get("consumer"),
                "source_fingerprint": package.get("source_fingerprint"),
            },
            "current_source_fingerprint": current_fingerprint,
            "validator": {
                "schema": validator_report["schema"],
                "summary": validator_report["summary"],
            },
            "checks": {
                "identity_valid": identity_valid,
                "source_hashes_match": all(check["matches"] for check in source_checks),
                "validator_gate_ok": validator_ok,
                "source_checks": source_checks,
            },
            "result": {
                "valid": not failed,
                "invalidated": bool(failed),
                "failed_checks": failed,
            },
            "constraints": {
                "writes_performed": False,
                "canonical_context_mutated": False,
                "parallel_ssot_created": False,
            },
        }

    def build_handoff(
        self,
        package: dict,
        *,
        package_ref: str | None = None,
        generated_at: str | None = None,
    ) -> dict:
        if package.get("schema") != "contextos.activation.package/1":
            raise ValueError("Activation handoff requires contextos.activation.package/1 input.")
        root = self.root.resolve()
        package_check = self.check_package(package, generated_at=generated_at)
        selected_context = [
            {
                "path": item["path"],
                "source_hash": item["source_hash"],
                "authority_tier": item["authority_tier"],
                "lifecycle_state": item["lifecycle_state"],
                "activation_role": item["activation_role"],
                "title": item.get("title"),
                "owner": item.get("owner"),
                "provenance": item.get("provenance", {}),
            }
            for item in package.get("working_context", {}).get("items", [])
        ]
        omitted_exclusions = max(0, len(package.get("exclusions", [])) - 20)
        handoff = {
            "schema": HANDOFF_SCHEMA,
            "id": "",
            "identity_hash": "",
            "generated_at": generated_at or generated_timestamp(),
            "root": str(root),
            "read_only": True,
            "mode": "handoff",
            "source_package": {
                "id": package.get("id"),
                "identity_hash": package.get("identity_hash"),
                "ref": package_ref,
                "schema": package.get("schema"),
                "source_fingerprint": package.get("source_fingerprint"),
            },
            "package_check": package_check,
            "consumer": package.get("consumer", {}),
            "mission": {
                "mission_id": package.get("goal", {}).get("mission_id"),
                "goal": package.get("goal", {}).get("statement"),
                "binding": package.get("goal", {}).get("binding"),
            },
            "working_instruction": (
                "Use this handoff as a compact pointer to the valid Activation Package. "
                "Use the selected canonical sources as governing context, fetch exact source "
                "content only when needed, preserve listed constraints and authority boundaries, "
                "record evidence and learning, and revalidate before acting if any invalidation "
                "condition may have changed."
            ),
            "selected_context": selected_context,
            "exclusions": {
                "count": len(package.get("exclusions", [])),
                "items": [
                    {
                        "path": item["path"],
                        "reason": item["reason"],
                        "source_hash": item["source_hash"],
                    }
                    for item in package.get("exclusions", [])[:20]
                ],
                "truncated": omitted_exclusions > 0,
                "omitted_count": omitted_exclusions,
            },
            "known_gaps": package.get("context_gaps", []),
            "authority": {
                "allowed_permissions": package.get("consumer", {}).get("permissions", []),
                "prohibited_permissions": package.get("consumer", {}).get("prohibited_permissions", []),
                "authority_boundary": "handoff_does_not_expand_package_permissions",
            },
            "constraints": {
                "not_ssot": True,
                "duplicates_full_canonical_content": False,
                "writes_performed": False,
                "canonical_context_mutated": False,
                "automatic_context_mutation": False,
                "consumer_specific_adapter": False,
            },
            "provenance": {
                "generated_by": "ContextActivationPackageEngine.build_handoff",
                "derived_from_package": package.get("id"),
                "derived_from_package_hash": package.get("identity_hash"),
                "evidence_lineage": package.get("provenance", {}).get("evidence_lineage", []),
                "selected_source_hashes": package.get("invalidation", {}).get("source_hashes", {}),
            },
            "freshness": {
                "package_valid_at_handoff": package_check["result"]["valid"],
                "current_source_fingerprint": package_check["current_source_fingerprint"],
                "package_source_fingerprint": package.get("source_fingerprint"),
                "validator_exit_code": package_check["validator"]["summary"]["exit_code"],
            },
            "invalidation": {
                "conditions": [
                    "The source Activation Package check becomes invalid.",
                    "Any selected canonical source hash changes.",
                    "The Validator gate reports errors or fatals.",
                    "The consumer, goal, Mission id, or authority boundary changes.",
                    "The handoff is used for a Mission other than its bound Mission or goal.",
                ],
                "source_hashes": package.get("invalidation", {}).get("source_hashes", {}),
            },
            "evidence_and_exit_conditions": [
                "Record the package id and identity hash used for the Mission.",
                "Record selected sources, exclusions, gaps, and additional context reads.",
                "Validate relevant runtime/test gates before Mission closure.",
                "Capture learning and out-of-scope discoveries in the Evolution Inbox.",
            ],
            "metrics": {
                "selected_source_count": len(selected_context),
                "excluded_source_count": len(package.get("exclusions", [])),
                "gap_count": len(package.get("context_gaps", [])),
            },
            "result": {
                "handoff_ready": package_check["result"]["valid"],
                "invalidated": package_check["result"]["invalidated"],
                "failed_checks": package_check["result"]["failed_checks"],
            },
        }
        handoff["id"] = f"activation.handoff.{stable_hash(self._handoff_identity_payload(handoff))[:16]}"
        handoff["identity_hash"] = stable_hash(self._handoff_identity_payload(handoff))
        return handoff

    def _select_sources(self, root: Path, goal_tokens: set[str], max_artifacts: int) -> tuple[list[dict], list[dict]]:
        scored: list[tuple[int, str, str, str]] = []
        for rel_path in candidate_paths(root):
            path = root / rel_path
            try:
                content = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            scored.append((score_path(rel_path, content, goal_tokens), rel_path, content, sha256_file(path)))
        scored.sort(key=lambda item: (-item[0], item[1]))
        default_raw = [item for item in scored if item[1] in DEFAULT_SOURCE_PATHS]
        optional_raw = [item for item in scored if item[1] not in DEFAULT_SOURCE_PATHS and item[0] > 0]
        selected_raw = (default_raw + optional_raw)[:max_artifacts]
        selected_paths = {path for _score, path, _content, _hash in selected_raw}
        selected = [
            {
                "path": rel_path,
                "source_hash": file_hash,
                "authority_tier": authority_tier(rel_path),
                "lifecycle_state": lifecycle_state(rel_path),
                "activation_role": activation_role(rel_path),
                "title": title_for(content),
                "owner": owner_for(content),
                "content_excerpt": excerpt_for(content, goal_tokens),
                "provenance": {
                    "source_path": rel_path,
                    "source_hash": file_hash,
                    "source_authority_tier": authority_tier(rel_path),
                },
            }
            for _score, rel_path, content, file_hash in selected_raw
        ]
        excluded = [
            {
                "path": rel_path,
                "reason": "lower_relevance_for_goal_or_package_limit",
                "source_hash": file_hash,
            }
            for score, rel_path, _content, file_hash in scored
            if score > 0 and rel_path not in selected_paths
        ]
        return selected, excluded

    def _context_gaps(self, selected: list[dict], activation_allowed: bool, validator_report: dict) -> list[dict]:
        gaps: list[dict] = []
        if not activation_allowed:
            gaps.append(
                {
                    "id": "activation.gap.validator_gate_blocked",
                    "severity": "blocker",
                    "message": "Validator gate has errors or fatals; activation package cannot be treated as safe working context.",
                    "evidence_refs": ["validator.summary"],
                }
            )
        if not any(item["authority_tier"] == "ssot" for item in selected):
            gaps.append(
                {
                    "id": "activation.gap.no_ssot_source_selected",
                    "severity": "warning",
                    "message": "No SSOT source was selected for the working context package.",
                    "evidence_refs": [],
                }
            )
        if not any(item["activation_role"] == "first_principles_authority" for item in selected):
            gaps.append(
                {
                    "id": "activation.gap.genesis_not_selected",
                    "severity": "info",
                    "message": "GENESIS was not selected; first-principles authority may need to be added for architecture missions.",
                    "evidence_refs": [],
                }
            )
        if validator_report["summary"]["warn"]:
            gaps.append(
                {
                    "id": "activation.gap.validator_warnings_present",
                    "severity": "info",
                    "message": "Validator warnings exist; package is usable but consumers should preserve caution.",
                    "evidence_refs": ["validator.summary"],
                }
            )
        return gaps

    def _identity_payload(self, package: dict) -> dict:
        return {
            "goal": package["goal"],
            "consumer": package["consumer"],
            "source_fingerprint": package["source_fingerprint"],
            "canonical_sources": package["canonical_sources"],
            "boundaries": package["boundaries"],
        }

    def _handoff_identity_payload(self, handoff: dict) -> dict:
        return {
            "source_package": handoff["source_package"],
            "consumer": handoff["consumer"],
            "mission": handoff["mission"],
            "selected_context": handoff["selected_context"],
            "authority": handoff["authority"],
            "constraints": handoff["constraints"],
            "invalidation": handoff["invalidation"],
        }
