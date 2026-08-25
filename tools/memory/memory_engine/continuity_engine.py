from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

from .report_builder import build_report


TOOLS_ROOT = Path(__file__).resolve().parents[2]
ADOPTION_ROOT = TOOLS_ROOT / "adoption"
if str(ADOPTION_ROOT) not in sys.path:
    sys.path.insert(0, str(ADOPTION_ROOT))

from adoption_engine import load_adoption_profile  # noqa: E402


MISSION_GLOB = "E.4_Mission_*.md"
FIELD_PATTERN = re.compile(r"^(?P<name>[A-Za-z][A-Za-z ]+):\s*(?P<value>.+?)\s*$", re.MULTILINE)
YAML_FIELD_PATTERN = re.compile(r"^\s{2}(?P<name>[a-z_]+):\s*(?P<value>.+?)\s*$", re.MULTILINE)
HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{2,}")
STOP_WORDS = {
    "and", "the", "for", "from", "with", "that", "this", "into", "must", "context", "contextos",
    "mission", "release", "current", "existing", "through", "without", "required", "model", "runtime",
}
SECTION_FORMS = {
    "decision": ("Decision", "Release Decision", "Mission Decision"),
    "evidence": ("Evidence Captured", "Validation Evidence", "Pre-Cut Evidence", "Evidence"),
    "outcome": ("Outcome", "Release Notes", "Mission Decision", "Release Decision"),
    "learning": ("Learning",),
}
PATTERN_TOPICS = {
    "authority_boundary": ("authority", "authorization", "permission"),
    "drift_invalidation": ("drift", "invalidat", "stale"),
    "evidence_provenance": ("evidence", "provenance", "traceab"),
    "read_only_boundary": ("read-only", "non-mutating", "no mutation"),
    "truth_boundary": ("canonical truth", "organizational truth", "second ssot", "non-canonical"),
}


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_scalar(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().strip("`\"'")


def sections(text: str) -> dict[str, str]:
    matches = list(HEADING_PATTERN.finditer(text))
    result: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        result[match.group(2).strip()] = text[start:end].strip()
    return result


def summarize(text: str, limit: int = 420) -> str:
    lines = []
    in_fence = False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not line or line.startswith(("|---", "---")):
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^\|\s*|\s*\|$", "", line)
        lines.append(line)
        if sum(len(part) for part in lines) >= limit:
            break
    value = " ".join(lines)
    return value[: limit - 1].rstrip() + "…" if len(value) > limit else value


def source_ref(root: Path, path: Path, heading: str | None = None) -> dict:
    return {
        "path": path.relative_to(root).as_posix(),
        "source_hash": file_hash(path),
        "section": heading,
    }


def truth(epistemic: str = "observed", governance: str | None = None, strategic: str | None = None) -> dict:
    return {
        "epistemic_support": epistemic,
        "governance_lifecycle": governance,
        "strategic_belief": strategic,
        "index_status": "recorded",
        "canonical": False,
    }


def parse_mission(root: Path, path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    field_values = {match.group("name").lower().replace(" ", "_"): clean_scalar(match.group("value")) for match in FIELD_PATTERN.finditer(text)}
    yaml_values = {match.group("name"): clean_scalar(match.group("value")) for match in YAML_FIELD_PATTERN.finditer(text)}
    heading = next((match.group(2) for match in HEADING_PATTERN.finditer(text) if len(match.group(1)) == 1), path.stem)
    mission_id = yaml_values.get("id") or path.stem.removeprefix("E.4_Mission_").split("_", 1)[0]
    status = field_values.get("status") or yaml_values.get("status") or "unknown"
    created_at = yaml_values.get("created_at")
    recorded_at = field_values.get("last_updated")
    release = yaml_values.get("release") or "unknown"
    parsed_sections = sections(text)
    return {
        "mission_id": mission_id,
        "title": heading.removeprefix("E.4 Mission ").strip(),
        "status": status,
        "release": release,
        "created_at": created_at,
        "recorded_at": recorded_at,
        "temporal": {
            "valid_from": created_at,
            "valid_to": None,
            "observed_at": recorded_at,
            "ceased_current_at": None,
            "temporal_unknowns": [name for name, value in (("valid_from", created_at), ("observed_at", recorded_at), ("ceased_current_at", None)) if value is None],
        },
        "applicability": "historical" if status.startswith("closed") else "current",
        "source": source_ref(root, path),
        "sections": parsed_sections,
        "raw_text": text,
    }


def memory_entry(form: str, mission: dict, heading: str, body: str) -> dict:
    identity = {"form": form, "mission_id": mission["mission_id"], "source_hash": mission["source"]["source_hash"], "section": heading}
    return {
        "id": f"memory.{form}.{stable_hash(identity)[:16]}",
        "form": form,
        "mission_id": mission["mission_id"],
        "release": mission["release"],
        "summary": summarize(body),
        "applicability": mission["applicability"],
        "temporal": mission["temporal"],
        "truth": truth(),
        "source": {**mission["source"], "section": heading},
        "retention_class": f"{form}_record",
        "context_evidence": mission["context_evidence"],
    }


def extract_form_entries(missions: list[dict]) -> dict[str, list[dict]]:
    result = {form: [] for form in ("mission", "decision", "evidence", "outcome", "learning", "context_state")}
    for mission in missions:
        result["mission"].append(
            {
                "id": f"memory.mission.{stable_hash({'mission_id': mission['mission_id'], 'source_hash': mission['source']['source_hash']})[:16]}",
                "form": "mission",
                "mission_id": mission["mission_id"],
                "title": mission["title"],
                "status": mission["status"],
                "release": mission["release"],
                "applicability": mission["applicability"],
                "temporal": mission["temporal"],
                "truth": truth(),
                "source": mission["source"],
                "retention_class": "mission_record",
                "context_evidence": mission["context_evidence"],
            }
        )
        for form, headings in SECTION_FORMS.items():
            for heading in headings:
                body = mission["sections"].get(heading)
                if body:
                    result[form].append(memory_entry(form, mission, heading, body))
                    break
        if "RELEASE-CUT" in mission["mission_id"]:
            release_heading = "Release Decision" if mission["sections"].get("Release Decision") else "Release"
            release_body = mission["sections"].get(release_heading)
            if release_body:
                result["context_state"].append(memory_entry("context_state", mission, release_heading, release_body))
    return result


def parse_inbox(root: Path) -> tuple[list[dict], list[dict]]:
    path = root / "SSOT" / "E.5_Evolution_Inbox.md"
    if not path.is_file():
        return [], []
    items = []
    supersession = []
    source = source_ref(root, path)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("| INBOX-"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            continue
        item = {
            "id": cells[0],
            "category": cells[1],
            "status": cells[2],
            "source_mission": cells[3],
            "summary": cells[4],
            "disposition": cells[5],
            "owner": cells[6] if len(cells) > 6 else None,
            "truth": truth("declared", None, "hypothesis" if cells[1] == "hypothesis" else None),
            "source": {**source, "section": cells[0]},
        }
        items.append(item)
        if item["status"] == "superseded":
            supersession.append(
                {
                    **item,
                    "superseded_at": None,
                    "superseded_by": item["disposition"],
                    "temporal_unknowns": ["superseded_at"],
                }
            )
    return items, supersession


def active_release(root: Path) -> str:
    path = root / "SSOT" / "P.2_Product_Roadmap.md"
    if not path.is_file():
        return "unknown"
    match = re.search(r"^# Current Version\s+\n+([^\n]+)", path.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


def release_history_gap(root: Path, context_states: list[dict]) -> dict | None:
    path = root / "SSOT" / "P.2_Product_Roadmap.md"
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8")
    current_match = re.search(r"^# Current Version\s+\n+v(?P<major>\d+)\.(?P<minor>\d+)", text, re.MULTILINE)
    if not current_match:
        return None
    current = (int(current_match.group("major")), int(current_match.group("minor")))
    listed = {
        (int(match.group("major")), int(match.group("minor")))
        for match in re.finditer(r"^\|\s*v(?P<major>\d+)\.(?P<minor>\d+)\s*\|", text, re.MULTILINE)
    }
    represented_text = " ".join(
        f"{item['mission_id']} {item['release']} {item['summary']}" for item in context_states
    ).lower()
    missing = [version for version in sorted(listed) if version < current and f"v{version[0]}.{version[1]}" not in represented_text]
    if not missing:
        return None
    labels = [f"v{major}.{minor}" for major, minor in missing]
    return {
        "id": "memory.gap.release_transition_records",
        "status": "unknown",
        "message": f"Released roadmap states lack explicit release-cut continuity records: {', '.join(labels)}.",
        "evidence_refs": [path.relative_to(root).as_posix()] + [item["source"]["path"] for item in context_states],
    }


def terms(value: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(value.lower()) if token not in STOP_WORDS and not token.isdigit()}


def select_prior_art(missions: list[dict], mission_id: str | None, goal: str, limit: int = 12) -> list[dict]:
    query_terms = terms(f"{mission_id or ''} {goal}")
    selected = []
    for mission in missions:
        if mission["mission_id"] == mission_id:
            continue
        candidate_terms = terms(f"{mission['mission_id']} {mission['title']} {mission['release']} {summarize(mission['raw_text'], 1200)}")
        matched = sorted(query_terms & candidate_terms)
        if not matched:
            continue
        selected.append(
            {
                "mission_id": mission["mission_id"],
                "title": mission["title"],
                "status": mission["status"],
                "release": mission["release"],
                "relevance": {"method": "deterministic_term_overlap", "score": len(matched), "matched_terms": matched},
                "truth": truth("derived", "suggested", "hypothesis"),
                "source": mission["source"],
            }
        )
    return sorted(selected, key=lambda item: (-item["relevance"]["score"], item["mission_id"]))[:limit]


def pattern_candidates(learning_entries: list[dict], missions_by_id: dict[str, dict]) -> list[dict]:
    candidates = []
    for topic, needles in PATTERN_TOPICS.items():
        refs = []
        for entry in learning_entries:
            if entry.get("mission_id") not in missions_by_id:
                continue
            text = missions_by_id[entry["mission_id"]]["sections"].get("Learning", "").lower()
            if any(needle in text for needle in needles):
                refs.append(f"{entry['source']['path']}#Learning")
        refs = sorted(set(refs))
        if len(refs) < 3:
            continue
        candidates.append(
            {
                "id": f"memory.pattern.{topic}",
                "title": topic.replace("_", " ").title(),
                "support_count": len(refs),
                "evidence_refs": refs,
                "truth": truth("derived", "suggested", "hypothesis"),
                "canonical": False,
                "promotion_route": "human_review_then_existing_context_construction_lifecycle",
                "automatic_consolidation_prohibited": True,
            }
        )
    return candidates


def profile_memory_forms(root: Path, profile) -> dict[str, list[dict]]:
    result = {form: [] for form in ("mission", "decision", "evidence", "outcome", "learning", "context_state")}
    form_for_concept = {
        "goals_missions": "mission",
        "active_work": "context_state",
        "evidence_closure": "evidence",
        "organizational_memory": "learning",
        "current_roadmap": "context_state",
    }
    for record in profile.source_records(root):
        form = form_for_concept.get(record["concept"])
        if form is None or not record["exists"] or "memory" not in record.get("applicable_operations", []):
            continue
        path = root / record["locator"]
        text = path.read_text(encoding="utf-8")
        title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), path.stem.replace("_", " "))
        identity = {
            "profile": profile.identity_hash,
            "concept": record["concept"],
            "path": record["locator"],
            "source_hash": record["source_hash"],
            "form": form,
        }
        applicability = "historical" if record.get("currentness") == "historical" else "current"
        result[form].append(
            {
                "id": f"memory.{form}.{stable_hash(identity)[:16]}",
                "form": form,
                "mission_id": None,
                "title": title,
                "status": record.get("currentness", "unknown"),
                "release": None,
                "summary": summarize(text),
                "applicability": applicability,
                "temporal": {
                    "valid_from": None,
                    "valid_to": None,
                    "observed_at": None,
                    "ceased_current_at": None,
                    "temporal_unknowns": ["valid_from", "observed_at", "ceased_current_at"],
                },
                "truth": truth(epistemic=record["mapping_support"], governance=record["lifecycle_state"]),
                "source": {"path": record["locator"], "source_hash": record["source_hash"], "section": None},
                "retention_class": f"external_{form}_record",
                "context_evidence": None,
                "adoption_mapping": {
                    "profile_id": profile.id,
                    "profile_identity_hash": profile.identity_hash,
                    "concept": record["concept"],
                    "authority_owner": record["authority_owner"],
                    "supersession_status": record.get("supersession_status", "unknown"),
                },
            }
        )
    return result


class OrganizationalMemoryEngine:
    """Build a governed, read-only continuity view over explicit Context OS records."""

    def __init__(self, root: str | Path = ".", adoption_profile=None) -> None:
        self.root = Path(root).resolve()
        self.adoption_profile = load_adoption_profile(adoption_profile)

    def run(
        self,
        *,
        mission_id: str | None = None,
        goal: str = "",
        context_versions: list[dict] | tuple[dict, ...] = (),
        generated_at: str | None = None,
    ) -> dict:
        from .context_version_integration import integrate_context_versions

        mission_dir = self.root / "SSOT"
        missions = [parse_mission(self.root, path) for path in sorted(mission_dir.glob(MISSION_GLOB))] if mission_dir.is_dir() else []
        missions, context_version_index, context_version_gaps = integrate_context_versions(
            self.root, missions, context_versions
        )
        forms = extract_form_entries(missions)
        if self.adoption_profile:
            mapped_forms = profile_memory_forms(self.root, self.adoption_profile)
            for form, entries in mapped_forms.items():
                forms[form].extend(entries)
        inbox, supersession = parse_inbox(self.root)
        prior_art = select_prior_art(missions, mission_id, goal)
        by_id = {mission["mission_id"]: mission for mission in missions}
        patterns = pattern_candidates(forms["learning"], by_id)
        roadmap_path = self.root / "SSOT" / "P.2_Product_Roadmap.md"
        roadmap_source = (
            [{"path": roadmap_path.relative_to(self.root).as_posix(), "source_hash": file_hash(roadmap_path)}]
            if roadmap_path.is_file()
            else []
        )
        sources = sorted(
            [{"path": item["source"]["path"], "source_hash": item["source"]["source_hash"]} for item in missions]
            + ([{"path": "SSOT/E.5_Evolution_Inbox.md", "source_hash": inbox[0]["source"]["source_hash"]}] if inbox else [])
            + roadmap_source,
            key=lambda item: item["path"],
        )
        if self.adoption_profile:
            mapped_sources = [
                {"path": item["locator"], "source_hash": item["source_hash"]}
                for item in self.adoption_profile.source_records(self.root)
                if item["exists"] and "memory" in item.get("applicable_operations", [])
            ]
            sources = sorted({item["path"]: item for item in sources + mapped_sources}.values(), key=lambda item: item["path"])
        source_fingerprint = stable_hash(sources)
        gaps = list(context_version_gaps)
        if any(entry["temporal"]["valid_from"] is None for entry in forms["mission"]):
            gaps.append({"id": "memory.gap.mission_valid_from", "status": "unknown", "message": "Some Mission records do not declare when their continuity became valid."})
        if not supersession:
            gaps.append({"id": "memory.gap.explicit_supersession", "status": "unknown", "message": "No explicit supersession records were observed; absence is not proof that nothing was superseded."})
        if context_version_index["mission_binding_counts"]["partial"] or context_version_index["mission_binding_counts"]["unknown"]:
            gaps.append(
                {
                    "id": "memory.gap.context_versions",
                    "status": "partial" if context_version_index["mission_binding_counts"]["exact"] else "unknown",
                    "message": "Mission history contains partial or unknown Context Version bindings; no historical version was fabricated.",
                }
            )
        gaps.extend(
            [
                {"id": "memory.gap.retention_policy", "status": "decision_needed", "message": "Operational retention, sensitivity, expiration, archival, and forgetting policy remains undecided."},
                {"id": "memory.gap.outcome_effectiveness", "status": "unknown", "message": "Recorded outcomes do not by themselves prove usefulness or causal effectiveness."},
            ]
        )
        release_gap = release_history_gap(self.root, forms["context_state"])
        if release_gap:
            gaps.append(release_gap)
        counts = {form: len(entries) for form, entries in forms.items()}
        current = sum(1 for item in forms["mission"] if item["applicability"] == "current")
        historical = len(forms["mission"]) - current
        identity_input = {
            "source_fingerprint": source_fingerprint,
            "mission_id": mission_id,
            "goal": goal,
            "forms": counts,
            "prior_art": [item["mission_id"] for item in prior_art],
            "supersession": [item["id"] for item in supersession],
            "context_version_index_hash": context_version_index["identity_hash"],
            "adoption_profile": self.adoption_profile.binding() if self.adoption_profile else None,
        }
        identity_hash = stable_hash(identity_input)
        report = {
            "id": f"memory.continuity.{identity_hash[:16]}",
            "identity_hash": identity_hash,
            "read_only": True,
            "derived_view": True,
            "authoritative_source": "canonical_and_governed_source_artifacts",
            "source_fingerprint": source_fingerprint,
            "scope": {"active_release": active_release(self.root), "mission_id": mission_id, "goal": goal, "corpus": "local_contextos_governed_records"},
            "summary": {
                "source_count": len(sources),
                "memory_form_counts": counts,
                "current_record_count": current,
                "historical_record_count": historical,
                "prior_art_count": len(prior_art),
                "supersession_count": len(supersession),
                "pattern_candidate_count": len(patterns),
                "gap_count": len(gaps),
                "context_version_bindings": context_version_index["mission_binding_counts"],
            },
            "truth_model": {
                "epistemic_support": ["observed", "declared", "inferred", "derived", "unknown"],
                "governance_lifecycle": ["suggested", "draft", "reviewed", "approved", "canonical"],
                "strategic_belief": ["hypothesis", "verified", "deprecated"],
                "missing_axis_value": None,
                "rule": "Memory preserves source truth metadata and never promotes an indexed or repeated assertion to canon.",
            },
            "memory_forms": forms,
            "inbox_memory": inbox,
            "prior_art": prior_art,
            "supersession": supersession,
            "pattern_candidates": patterns,
            "context_versions": context_version_index,
            "retention": {
                "policy_state": "decision_needed",
                "classes_observed": sorted({entry["retention_class"] for entries in forms.values() for entry in entries}),
                "automated_deletion": False,
                "automated_compaction": False,
                "automated_forgetting": False,
                "silent_indefinite_retention": False,
                "governance_required_before_destructive_behavior": True,
            },
            "continuity_gaps": gaps,
            "theory_claims": [
                {"claim": "Mission evidence can become durable organizational memory without losing provenance.", "status": "supported" if forms["mission"] and forms["evidence"] else "partially_supported", "evidence_refs": [item["source"]["path"] for item in forms["evidence"][:5]]},
                {"claim": "Memory can preserve continuity without becoming a second SSOT.", "status": "supported", "evidence_refs": ["contextos.memory.continuity_report/1.read_only", "contextos.memory.continuity_report/1.derived_view"]},
                {"claim": "Self-hosting history can provide useful prior art for future Missions.", "status": "partially_supported" if prior_art else "not_yet_tested", "evidence_refs": [item["source"]["path"] for item in prior_art]},
                {"claim": "Learning can be retained without becoming canonical truth automatically.", "status": "supported" if forms["learning"] and all(not item["truth"]["canonical"] for item in forms["learning"]) else "partially_supported", "evidence_refs": [item["source"]["path"] for item in forms["learning"][:5]]},
                {"claim": "Organizational memory can support future reasoning while remaining governed.", "status": "not_yet_tested", "evidence_refs": []},
            ],
            "sources": sources,
            "limitations": [
                "The report indexes explicit Markdown records; it does not reconstruct unrecorded decisions or conversations.",
                "Deterministic term overlap suggests prior art relevance but does not prove applicability or usefulness.",
                "Pattern frequency creates a review candidate only; repeated evidence is not proven reusable practice.",
                "Temporal and supersession fields remain unknown unless source artifacts state them explicitly.",
                "No retention, archival, forgetting, graph traversal, semantic interpretation, or canonical mutation is performed.",
            ],
        }
        if self.adoption_profile:
            report["adoption_profile"] = self.adoption_profile.binding()
            report["scope"]["corpus"] = "target_native_governed_records_mapped_by_adoption_profile"
            report["invalidation"] = {
                "profile_identity_hash": self.adoption_profile.identity_hash,
                "target_source_fingerprint": self.adoption_profile.state(self.root)["source_fingerprint"],
                "conditions": self.adoption_profile.data["invalidation"]["conditions"],
            }
        return build_report(self.root, report, generated_at)
