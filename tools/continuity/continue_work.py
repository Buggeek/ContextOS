#!/usr/bin/env python3
"""One local, assisted continuation route; derived files, never target writes.

No language understanding or approval inference lives here. The operator's
interpretations are inputs; the existing Runtime checks their context bindings.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
for component in ("activation", "adoption", "memory", "reasoning"):
    sys.path.insert(0, str(ROOT / "tools" / component))
from activation_engine.package_engine import ContextActivationPackageEngine
from adoption_engine import AdoptionProfile
from adoption_engine.profile import file_hash, safe_locator, stable_hash
from memory_engine import ContextVersionEngine
from reasoning_engine import WorkOwnershipResolver
from review_evidence import citation_problem, evaluate_review, governing_constraints, same_restriction


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + "." + uuid4().hex)
    with temporary.open("x", encoding="utf-8") as stream:
        os.chmod(temporary, 0o600)
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def command(args, root):
    result = subprocess.run(args, cwd=root, capture_output=True, timeout=45,
                            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "GIT_NO_REPLACE_OBJECTS": "1"})
    if result.returncode:
        # Never surface arbitrary subprocess stderr (credentials or target data).
        raise ValueError("Source authority/read check failed; operator must inspect it separately.")
    return result.stdout


def inside(path, root):
    return path == root or root in path.parents


def plain_path(root, locator):
    path = root / safe_locator(locator)
    if not inside(path.resolve(), root) or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Symlink or source outside the authorized corpus.")
    return path


def snapshot(config, destination):
    """Copy an explicit read allowlist. No target code, fetch, checkout or writes."""
    source = config["source"]
    root = Path(source["root"]).resolve()
    kind = source["kind"]
    provenance = {"kind": kind, "root": str(root), "observed_at": datetime.now(timezone.utc).isoformat()}
    if kind == "published_git_docs":
        repository = source["repository"]
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
            raise ValueError("Invalid repository identity.")
        proof = command(["repo-authority-preflight", repository], root).decode()
        expected = f"AUTHORITY_OK repository={repository} identity={source['identity']}"
        if expected not in proof.splitlines():
            raise ValueError("Repository-bound authority mismatch.")
        remote = command(["git", "ls-remote", "origin", "refs/heads/main"], root).decode().split()
        if len(remote) != 2 or remote[1] != "refs/heads/main" or not re.fullmatch(r"[0-9a-f]{40}", remote[0]):
            raise ValueError("Published main is not uniquely resolvable.")
        tip = remote[0]
        command(["git", "cat-file", "-e", tip + "^{commit}"], root)
        provenance.update(repository=repository, published_sha=tip, authority=expected)
    elif kind == "local_corpus":
        # Already-authorized local corpus, not a claim about any published target.
        if (root / ".git").exists():
            provenance["local_tip"] = command(["git", "rev-parse", "HEAD"], root).decode().strip()
    else:
        raise ValueError("Use a local_corpus or published_git_docs source.")
    allowed = set(source["visible_sources"])
    denied = set(source.get("withheld_sources", []))
    if not allowed or allowed & denied:
        raise ValueError("Source visibility must be explicit and non-overlapping.")
    manifest, missing = {}, []
    for locator in sorted(allowed):
        safe_locator(locator)
        if not locator.endswith((".md", ".txt", ".yaml", ".yml")):
            raise ValueError("Only declared documentary sources are supported.")
        if kind == "published_git_docs":
            if not locator.startswith("docs/"):
                raise ValueError("Published read authority is limited to docs/.")
            tree = command(["git", "ls-tree", tip, "--", locator], root).decode()
            if not tree:
                missing.append(locator)
                continue
            if not tree.startswith("100644 blob ") or tree.count("\n") != 1:
                raise ValueError("Published source missing or not a regular document.")
            content = command(["git", "show", tip + ":" + locator], root)
        else:
            path = plain_path(root, locator)
            if not path.exists():
                missing.append(locator)
                continue
            content = path.read_bytes()
        content.decode("utf-8")
        path = destination / locator
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        path.chmod(0o600)
        manifest[locator] = file_hash(path)
    provenance["source_hashes"] = manifest
    provenance["missing_sources"] = missing
    provenance["memory"] = "not_retrieved; visibility is not evidence of absent work"
    return provenance


def citations_valid(citations, corpus, allowed):
    return citation_problem(citations, corpus, allowed) is None


def load_anchor(workspace, recover, visible=None):
    pointer = workspace / "anchor.json"
    partial_pointer = False
    if not pointer.exists():
        if (workspace / "runs").exists() and any((workspace / "runs").iterdir()):
            # A partial orientation deliberately never replaced/created a usable
            # anchor. Its checked last record preserves that fact across processes.
            if not (workspace / "last.json").exists() and recover:
                return None
            if not (workspace / "last.json").exists():
                raise ValueError("Local evidence missing. Use --recover after review; prior history remains unknown.")
            pointer, partial_pointer = workspace / "last.json", True
        else:
            return None
    try:
        reference = read_json(pointer)
        path = plain_path(workspace, reference["path"])
        record = read_json(path)
        if stable_hash(record) != reference["hash"]:
            raise ValueError("Local evidence integrity mismatch.")
        if partial_pointer and not record.get("runtime_details"):
            raise ValueError("A usable anchor was lost; explicit recovery required.")
        for locator, fingerprint in record["provenance"]["source_hashes"].items():
            if visible is not None and locator not in visible:
                continue  # revoked visibility never triggers a historical source read
            if file_hash(plain_path(path.parent / "corpus", locator)) != fingerprint:
                raise ValueError("Local source evidence integrity mismatch.")
        return record
    except (OSError, KeyError, ValueError) as exc:
        if recover:
            return None
        raise ValueError("Local evidence missing or altered. Explicit --recover required; do not invent history.") from exc


def run(workspace, *, reanchor=False, reason=None, recover=False):
    started = time.perf_counter()
    workspace = Path(workspace).resolve()
    if any(path.is_symlink() for path in workspace.rglob("*")):
        raise ValueError("Evidence workspace must not contain symlinks.")
    config = read_json(workspace / "work.json")
    target = Path(config["source"]["root"]).resolve()
    if inside(workspace, target) or inside(target, workspace) or inside(workspace, ROOT):
        raise ValueError("Evidence workspace must be separate from target and Context OS canon.")
    if (reanchor or recover) and not reason:
        raise ValueError("An explicit operator review/recovery reason is required.")
    workspace.chmod(0o700)
    with (workspace / ".lock").open("a") as lock:
        os.chmod(workspace / ".lock", 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        visible = set(config["source"]["visible_sources"])
        anchor = load_anchor(workspace, recover, visible)
        if recover and anchor is not None and not anchor.get("runtime_details"):
            raise ValueError("The local anchor is intact. Use ordinary return or a reviewed re-anchor.")
        if anchor and (anchor["target_id"] != config["target_id"] or
                       anchor["provenance"]["root"] != str(target) or
                       anchor["provenance"].get("repository") != config["source"].get("repository")):
            raise ValueError("This folder is bound to another target. Use a separate continuity folder.")
        profile = AdoptionProfile(config["profile"]) if config.get("profile") else None
        if profile and (profile.data["target"]["id"] != config["target_id"] or
                        profile.data["lifecycle"]["state"] not in {"approved", "canonical"}):
            raise ValueError("Adoption Profile is not approved for this target.")
        if config["source"]["kind"] == "published_git_docs" and not profile:
            raise ValueError("Published external sources require an approved Adoption Profile.")
        run_dir = workspace / "runs" / uuid4().hex
        corpus = run_dir / "corpus"
        corpus.mkdir(parents=True, mode=0o700)
        provenance = snapshot(config, corpus)
        runtime_started = time.perf_counter()
        allowed = provenance["source_hashes"]
        decisions = governing_constraints(config.get("governing_decisions", []), corpus, visible)
        decision_ids = [d["id"] for d in decisions if d.get("id")]
        if len(decision_ids) != len(set(decision_ids)):
            for d in decisions:
                d.update(status="unverifiable", missing_evidence="duplicate_restriction_identity",
                         limitation="dependent_proposal_not_sufficient")
        authority_sources = {s["locator"] for m in profile.data["mappings"]
                             if m["concept"] in {"governance", "authority_boundaries"} and m.get("recognized_as_canonical")
                             for s in m["sources"] if s.get("currentness") == "current" and s.get("lifecycle_state") == "canonical"} if profile else None
        proposal_review = evaluate_review(config, corpus, visible, decisions, profile.identity_hash if profile else None, authority_sources)
        # A removed restriction is still known from the anchor. Re-anchoring alone
        # cannot erase it; a new folder is not a decision approving its removal.
        previous_decisions = anchor.get("governing_decisions", []) if anchor else []
        for old in previous_decisions:
            if not old.get("id") and not old.get("text") and any(not d.get("id") and not d.get("text") for d in decisions):
                continue  # preserve one opaque existence notice, never accumulate it
            if not any(same_restriction(old, d) for d in decisions):
                retained = governing_constraints([old], corpus, visible)[0]
                retained.update(status="unverifiable", missing_evidence="previous_restriction_omitted",
                                limitation="dependent_proposal_not_sufficient")
                decisions.append(retained)
        hidden_refs = [r for d in config.get("governing_decisions", []) for r in d.get("citations", []) if r.get("path") not in visible]
        hidden_refs += [r for key in ("constraint_refs", "authority_refs", "decision_refs")
                        for r in config.get("review", {}).get(key, []) if r.get("path") not in visible]
        privacy_limited = bool(config["source"].get("withheld_sources") or hidden_refs or
                               (anchor and set(anchor["provenance"]["source_hashes"]) - visible))
        # Empty directories carry no invented canon; native Validator needs roots.
        for folder in ("docs", "SSOT", "ops", "templates"):
            (corpus / folder).mkdir(exist_ok=True)
        activation = ContextActivationPackageEngine(corpus, profile)
        versions = ContextVersionEngine(corpus, profile)
        checks = {}
        if anchor and not privacy_limited and anchor.get("package"):
            checks["package"] = activation.check_package(anchor["package"])
            if anchor.get("version"):
                checks["version"] = versions.check_version(anchor["version"])
        changed_sources = sorted(set(allowed) | set(anchor["provenance"]["source_hashes"])) if anchor else []
        changed_sources = [p for p in changed_sources if allowed.get(p) != anchor["provenance"]["source_hashes"].get(p)]
        material = bool(anchor and (changed_sources or anchor["input_hash"] != stable_hash(config) or
                        anchor["profile_hash"] != (profile.identity_hash if profile else None)))
        if checks.get("package") and not checks["package"]["result"]["valid"]:
            material = True
        if checks.get("version") and checks["version"]["result"]["current_applicability"] != "exact_current_match":
            material = True
        claims, gaps = {}, []
        for key in ("objective", "audience", "state", "existing_work", "next", "value", "indicator"):
            claim = config.get("claims", {}).get(key)
            if claim and citations_valid(claim.get("citations", []), corpus, allowed):
                claims[key] = claim
            else:
                gaps.append(key + ": unknown or citation unavailable; operator clarification required")
        goal = config.get("intent", "").strip()
        if not goal:
            raise ValueError("What bounded work should we resume? An intention is required.")
        package = activation.run(goal=goal, consumer="codex")
        handoff = activation.build_handoff(package)
        plan = versions.plan(scope={"organization": config["target_id"], "domain": "work-continuity",
                                    "tier": "working", "context_root": "authorized-corpus"},
                             event_type="explicit_human_checkpoint", reason=reason or "Assisted work orientation",
                             capture_at=datetime.now(timezone.utc).isoformat(), goal=goal,
                             activation_package=package, activation_handoff=handoff,
                             parent_version=anchor.get("version") if anchor and not privacy_limited else None,
                             additional_source_paths=sorted(allowed))
        version = versions.capture(plan, activation_package=package, activation_handoff=handoff,
                                   parent_version=anchor.get("version") if anchor and not privacy_limited else None) if plan["status"] == "ready" else None
        ownership = None
        if config.get("ownership") and (not profile or profile.data.get("work_ownership")):
            ownership = WorkOwnershipResolver(corpus, profile).run(**config["ownership"])
        disposition = ownership["result"]["disposition"] if ownership else "OWNERSHIP_UNKNOWN"
        if not ownership:
            gaps.append("Ownership coverage/mapping not established; existing work may still exist.")
        fit = proposal_review["fit"]
        uncertain_constraints = any(d["status"] == "unverifiable" for d in decisions)
        if uncertain_constraints:
            gaps.append("Known governing restriction unverifiable; dependent proposal is not sufficient.")
            fit = "unverified_constraints"
            proposal_review["fit"] = fit
        if fit == "unverified_constraints":
            gaps.append("Proposal review requires evidence or a new attributed judgement; re-anchor is not approval.")
        continuation = "review_existing_work_brief"
        if disposition in {"OWNERSHIP_UNKNOWN", "OWNERSHIP_CONFLICT"}:
            continuation = "clarify_ownership; do_not_create_duplicate_work"
        if disposition in {"AWAIT_HUMAN_DECISION", "AWAIT_EVIDENCE"}:
            continuation = disposition
        if fit == "requires_product_architecture_decision":
            continuation = "await_explicit_product_architecture_decision"
        elif fit == "unverified_constraints":
            continuation = "review_constraints_before_presenting_proposal"
        if privacy_limited:
            status = "needs_clarification"
        elif material and not reanchor:
            status = "reanchor_required"
            # Stale operator interpretation must not masquerade as a fresh brief.
            claims = {}
        elif not version or uncertain_constraints or fit == "unverified_constraints" or privacy_limited or any(key not in claims for key in ("objective", "state", "next")):
            status = "needs_clarification"
        else:
            status = "brief_prepared_for_review"
        record = {"status": status, "intent": goal, "target_id": config["target_id"],
                  "claims": claims, "gaps": gaps, "interpretations": config.get("interpretations", []) if status != "reanchor_required" and fit != "unverified_constraints" else [],
                  "proposal_fit": fit if status != "reanchor_required" else "reanchor_required",
                  "governing_decisions": decisions,
                  "proposal_review": proposal_review,
                  "ownership_disposition": disposition, "ownership": ownership,
                  "continuation": continuation if status != "reanchor_required" else "review_material_change",
                  "provenance": provenance, "input_hash": stable_hash(config),
                  "profile_hash": profile.identity_hash if profile else None,
                  "package": package, "handoff": handoff, "plan": plan, "version": version,
                  "prior_checks": checks, "changed_sources": changed_sources,
                  "prior_reference": anchor["version"]["id"] if anchor and anchor.get("version") else None,
                  "history": "recovery; prior history unknown" if recover else "checked prior partial orientation; prior protected context unknown" if anchor and anchor.get("runtime_details") else "checked prior local anchor" if anchor else "no prior reference",
                  "operator_review_reason": reason, "authority": "prepare_only; no implementation or canonical mutation authorized",
                  "human_measurements": None,
                  "source_acquisition_seconds": round(runtime_started - started, 4),
                  "runtime_seconds": round(time.perf_counter() - runtime_started, 4),
                  "total_seconds": round(time.perf_counter() - started, 4)}
        if privacy_limited:
            # Runtime artifacts may contain profile metadata or historical refs.
            # Expose a safe partial brief, never those unsanitized structures.
            for key in ("package", "handoff", "plan", "version", "ownership", "prior_reference", "profile_hash", "input_hash"):
                record[key] = None
            record.update(prior_checks={}, changed_sources=[p for p in changed_sources if p in visible],
                          interpretations=[], runtime_details="withheld; scoped evidence review required")
            record["gaps"].append("Runtime detail withheld to preserve visibility; orientation is partial.")
            if hidden_refs:
                record["proposal_review"] = {"fit": "unverified_constraints", "issues": ["evidence_not_visible"],
                                             "execution_authorized": False}
                record["proposal_fit"] = "unverified_constraints"
        if config["source"]["kind"] == "local_corpus":
            if any(file_hash(plain_path(target, p)) != h for p, h in allowed.items()):
                raise ValueError("Local sources changed during the run; retry after stabilizing the corpus.")
        write_json(run_dir / "record.json", record)
        pointer = {"path": str((run_dir / "record.json").relative_to(workspace)), "hash": stable_hash(record)}
        write_json(workspace / "last.json", pointer)
        if not privacy_limited and status != "reanchor_required" and (anchor is None or reanchor):
            write_json(workspace / "anchor.json", pointer)
        return record


def render(record):
    states = {"brief_prepared_for_review": "Brief preparado para revisión.",
              "needs_clarification": "Orientación limitada: falta completar la evidencia.",
              "reanchor_required": "Hay un cambio material: revisar antes de continuar."}
    history = {"no prior reference": "Sin referencia anterior.", "checked prior local anchor": "Referencia local anterior comprobada.",
               "checked prior partial orientation; prior protected context unknown": "Orientación parcial anterior comprobada; contexto protegido anterior desconocido.",
               "recovery; prior history unknown": "Nueva referencia tras pérdida de evidencia; historia anterior desconocida."}
    lines = [record["intent"], states[record["status"]], history[record["history"]]]
    if record["status"] == "reanchor_required":
        lines.append("Cambió el contexto material. Revisar fuentes y restricciones antes de continuar.")
    else:
        labels = {"objective": "Buscamos", "audience": "Para", "state": "Las fuentes declaran",
                  "existing_work": "Trabajo existente", "next": "Siguiente decisión/condición",
                  "value": "Resultado buscado (sin causalidad demostrada)", "indicator": "Evidencia/indicador"}
        shown = set()
        for key, claim in record["claims"].items():
            if claim["text"] not in shown:
                lines.append(labels[key] + ": " + claim["text"])
                shown.add(claim["text"])
        for item in record["interpretations"]:
            lines.append("Interpretación del operador, no verdad validada: " + item)
    for item in record["governing_decisions"]:
        if item.get("status") == "unverifiable":
            lines.append("Restricción conocida, NO VERIFICABLE: " + item.get("text", "existencia conservada; detalle no disponible") +
                         ". Falta: " + item["missing_evidence"] + ". La propuesta dependiente no es suficiente para continuar.")
        else:
            review = "cita comprobada; revisión semántica declarada por " + item["checked_by"] if item.get("checked_by") else "leída; restricción no comprobada"
            lines.append("Decisión rectora (" + review + "): " + item["text"])
    ownership = {"OWNERSHIP_UNKNOWN": "Responsable no resuelto; no inferir ausencia de trabajo.",
                 "OWNERSHIP_CONFLICT": "Hay responsables en conflicto; resolver antes de abrir trabajo.",
                 "OBSERVE_EXISTING_WORK": "Continuar dentro del trabajo existente; no duplicarlo.",
                 "AWAIT_HUMAN_DECISION": "El trabajo existente espera una decisión humana.",
                 "AWAIT_EVIDENCE": "El trabajo existente espera evidencia.",
                 "QUALIFY_NEW_WORK": "La cobertura declarada permite evaluar una necesidad; no autoriza crear trabajo."}
    lines.append(ownership.get(record["ownership_disposition"], "Revisar el límite del trabajo existente."))
    fits = {"unverified_constraints": "Encaje no comprobado: revisar restricciones antes de presentar una propuesta.",
            "requires_product_architecture_decision": "La propuesta requiere una decisión explícita de producto/arquitectura.",
            "operator_declares_compatible; product_acceptance_not_inferred": "El operador declara encaje; aceptación de producto pendiente.",
            "documented_human_exception; authenticity_not_verified": "Excepción humana documentada y vinculada al alcance; autenticidad no verificada. No autoriza ejecución."}
    if record["proposal_fit"] in fits:
        lines.append(fits[record["proposal_fit"]])
    review = record.get("proposal_review", {})
    proposal = review.get("proposal")
    if isinstance(proposal, dict):
        lines.append("Propuesta " + proposal.get("version", "sin versión") + ": " + proposal.get("content", "desconocida"))
        lines.append("Alcance: " + proposal.get("scope", "desconocido") + "; autor declarado: " + proposal.get("author", "desconocido"))
    if review.get("judgement"):
        lines.append("Juicio semántico de " + review["judgement"].get("reviewed_by", "actor desconocido") + ": " +
                     review["judgement"].get("rationale", "sin justificación; no comprobado"))
    if review.get("review_relationship") == "self_review":
        lines.append("Autoevaluación del autor; no es una revisión independiente.")
    if review.get("decision"):
        d = review["decision"]
        lines.append("Decisión documental de " + d["human_owner"] + "; alcance " + d["scope"] + "; vigente hasta " + d["valid_until"] + ".")
    for issue in review.get("issues", []):
        lines.append("Revisión pendiente: " + issue)
    if record["changed_sources"]:
        lines.append("Fuentes con cambios: " + str(len(record["changed_sources"])) + "; ver detalle.")
    elif record["history"] == "checked prior local anchor" and not record.get("runtime_details"):
        lines.append("Sin cambios materiales en las fuentes permitidas respecto a la referencia.")
    required = {"objective": "objetivo", "state": "estado", "next": "siguiente decisión/condición"}
    missing = [label for key, label in required.items() if key not in record["claims"]]
    if missing and record["status"] != "reanchor_required":
        lines.append("Pregunta material: confirmar " + ", ".join(missing) + ".")
    if "indicator" not in record["claims"]:
        lines.append("Indicador y baseline: desconocidos; no se infieren resultados.")
    if record["version"] is None:
        lines.append("Captura de contexto bloqueada: revisar gates en el detalle; orientación limitada.")
    lines.append("Solo preparación. Lectura/citas no prueban encaje, aceptación, valor ni permiso para ejecutar.")
    lines.append("Memoria no recuperada; no equivale a ausencia de trabajo. Detalle: --format json.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--format", choices=("human", "json"), default="human")
    parser.add_argument("--reanchor", action="store_true")
    parser.add_argument("--recover", action="store_true")
    parser.add_argument("--reason")
    args = parser.parse_args()
    try:
        record = run(args.workspace, reanchor=args.reanchor, reason=args.reason, recover=args.recover)
        print(json.dumps(record, ensure_ascii=False) if args.format == "json" else render(record))
        return 2 if record["status"] in {"reanchor_required", "needs_clarification"} else 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        error = {"status": "blocked", "message": str(exc), "execution_authorized": False}
        print(json.dumps(error, ensure_ascii=False) if args.format == "json" else "Bloqueado: " + str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
