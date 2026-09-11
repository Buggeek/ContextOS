"""Spanish first reading of an existing checked record, not a new Runtime gate.

Codex/the operator supplies source-faithful Spanish wording. Exact bindings and
coverage checks cannot certify translation or semantic fidelity. Original data,
machine status and detailed rendering remain untouched and separately available.
"""
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "adoption"))
from adoption_engine.profile import stable_hash


def wording_binding(record):
    """Bind facts and controls; exclude display clocks and per-run artifact ids."""
    keys = ("target_id", "intent", "claims", "gaps", "interpretations", "governing_decisions",
            "observations", "proposal_fit", "ownership_disposition", "continuation",
            "profile_hash", "work_binding", "input_hash", "status", "runtime_details", "authority")
    view = {key: record.get(key) for key in keys}
    view["sources"] = {key: record.get("provenance", {}).get(key)
                       for key in ("root", "repository", "source_hashes", "missing_sources")}
    view["review"] = {key: value for key, value in record.get("proposal_review", {}).items()
                      if key != "authority_checked_at"}
    view["context_available"] = record.get("version") is not None
    return stable_hash(view)


def covered_wording(items, entries):
    """Every item needs wording, including different revisions of the same id."""
    if not isinstance(entries, list) or any(not isinstance(e, dict) or not isinstance(e.get("text"), str)
                                           or not e["text"].strip() for e in entries):
        return False
    return Counter(stable_hash(item) for item in items) == Counter(e.get("binding") for e in entries)


def wording_issues(record, wording):
    if not isinstance(wording, dict):
        return ["Spanish wording not supplied"]
    issues = []
    if wording.get("binding") != wording_binding(record):
        issues.append("wording does not bind the current facts and controls")
    if wording.get("language") != "es" or not wording.get("authored_by"):
        issues.append("attributed Spanish wording required; language is operator-declared")
    for field in ("case", "work", "objective", "beneficiaries"):
        if not isinstance(wording.get(field), str) or not wording[field].strip():
            issues.append("missing reader context: " + field)
    for field in ("decision_owner", "proposal", "proposal_missing", "clarification_question"):
        if field in wording and not isinstance(wording[field], str):
            issues.append("reader wording must be text: " + field)
    if wording.get("case_kind") not in {"synthetic", "documentary", "unknown"}:
        issues.append("case provenance must be explicit")
    if record.get("proposal_review", {}).get("proposal"):
        if not wording.get("proposal") or wording.get("proposal_detail") not in {"described", "insufficient"}:
            issues.append("proposal description and detail limit required")
        if wording.get("proposal_detail") == "insufficient" and not (wording.get("proposal_missing") and wording.get("clarification_question")):
            issues.append("missing proposal detail must be explained")
    for field, source in (("restrictions", "governing_decisions"), ("unknowns", "gaps")):
        if not covered_wording(record.get(source, []), wording.get(field)):
            issues.append("incomplete wording coverage: " + source)
    return issues


def render_reader(record, wording=None):
    """One continuation, controlled by the original record; never an approval."""
    status = record.get("status")
    has_proposal = bool(record.get("proposal_review", {}).get("proposal"))
    existing_work = bool(record.get("claims", {}).get("existing_work"))
    private = bool(record.get("runtime_details") or any(
        item.get("missing_evidence") == "evidence_not_visible" for item in record.get("governing_decisions", [])))
    if private:
        return ("Parte de la información de este trabajo no se puede mostrar. Las restricciones pendientes siguen vigentes; "
                "este resumen no permite dar la información por completa.\n\n"
                "Siguiente paso: pedir a la persona responsable de la información una explicación que pueda compartirse. "
                "Esta orientación no concede permisos adicionales.")
    issues = wording_issues(record, wording)
    if issues:
        if status == "reanchor_required":
            situation = "Cambió la información del trabajo. La referencia anterior es histórica y su revisión ya no puede reutilizarse como vigente."
            action = "revisar el cambio y preparar una explicación actual antes de retomar el trabajo"
        else:
            situation = "Falta una explicación en español, comprobada contra la información disponible, para presentar este trabajo con claridad."
            action = "preparar esa explicación para poder revisar el trabajo"
        if record.get("governing_decisions"):
            situation += " Hay restricciones que deben conservarse y explicarse antes de continuar."
        if record.get("gaps"):
            situation += " También queda información por aclarar."
        return situation + "\n\nSiguiente paso: " + action + ". Esto no autoriza acciones ni decisiones adicionales."

    lines = []
    kind = wording["case_kind"]
    prefix = {"synthetic": "Caso ficticio. ",
              "documentary": "Caso basado en las fuentes disponibles. ",
              "unknown": "El origen del caso necesita aclaración. "}[kind]
    lines.append(prefix + wording["case"])
    lines.append(wording["objective"] + " " + wording["beneficiaries"])
    lines.append(wording["work"])
    owner_known = bool(record.get("claims", {}).get("next") and wording.get("decision_owner"))
    if not owner_known:
        lines.append("Falta explicar quién interviene en el siguiente paso y bajo qué condición.")
    elif has_proposal:
        lines.append("Esa responsabilidad no se te atribuye por estar leyendo este resumen.")
    if has_proposal and wording.get("proposal"):
        if existing_work:
            lines.append("El trabajo existente conserva sus condiciones. La revisión del cambio asociado se trata por separado y no lo aprueba.")
        lines.append(wording["proposal"])
        if wording["proposal_detail"] == "insufficient":
            lines.append(wording["proposal_missing"])
    elif has_proposal:
        lines.append("La información disponible no permite describir una propuesta concreta.")
    elif not existing_work:
        lines.append("La información disponible no permite establecer qué trabajo existente se retoma.")
    remaining = list(wording["restrictions"])
    for item in record.get("governing_decisions", []):
        entry = next(entry for entry in remaining if entry["binding"] == stable_hash(item))
        remaining.remove(entry)
        text = entry["text"]
        if item.get("status") == "unverifiable":
            text += " No se ha podido comprobar esta restricción; " + ("la propuesta sigue condicionada por ella." if has_proposal else "la continuidad sigue condicionada por ella.")
        lines.append(text)
    lines.extend(dict.fromkeys(entry["text"] for entry in wording["unknowns"]))

    fit = record.get("proposal_fit")
    ownership = record.get("ownership_disposition")
    # Inspect existing control results only. An incomplete change review does
    # not invalidate verified operation context; an unknown rule still does.
    operation_context_available = bool(
        has_proposal and existing_work and record.get("version")
        and all(record.get("claims", {}).get(k) for k in ("objective", "state", "next"))
        and record.get("governing_decisions")
        and all(d.get("status") == "verified_citation" for d in record["governing_decisions"]))
    if has_proposal and existing_work:
        if fit == "requires_product_architecture_decision":
            lines.append("Hay una decisión pendiente sobre el cambio propuesto; requiere revisión explícita de producto o arquitectura.")
        elif fit == "unverified_constraints":
            lines.append("El cambio asociado todavía necesita comprobar sus restricciones y su revisión.")
    if status == "reanchor_required":
        lines.append("La referencia anterior sigue siendo histórica y no puede reutilizarse como vigente ante este cambio.")
        action = "revisar las fuentes y las restricciones para establecer una nueva referencia"
    elif (status != "brief_prepared_for_review" or fit == "unverified_constraints") and not operation_context_available:
        # Use the already bound explanation of the actual gap. A missing
        # benefit/indicator alone is not a material continuation condition.
        material_gaps = [g for g in record.get("gaps", [])
                         if not g.startswith(("value:", "indicator:"))]
        details = [e["text"] for g in material_gaps for e in wording["unknowns"]
                   if e["binding"] == stable_hash(g)]
        action = "reunir la información pendiente: " + " ".join(dict.fromkeys(details)) if details else (
            "comprobar la referencia de contexto y las restricciones pendientes antes de continuar")
    elif ownership in {"OWNERSHIP_UNKNOWN", "OWNERSHIP_CONFLICT"} or not owner_known:
        action = "aclarar quién tiene a cargo este trabajo y su próxima revisión"
        if ownership == "OWNERSHIP_CONFLICT":
            action += "; las responsabilidades declaradas están en conflicto"
    elif not existing_work and not has_proposal:
        action = "aclarar qué trabajo se retoma y en qué situación está"
    else:
        # Existing attributed field: explain the sourced next step, its actor
        # and condition. Do not replace known specifics with a generic action.
        # The binding proves provenance/coverage, not this wording's semantics.
        action = wording["decision_owner"]
        if has_proposal and not existing_work:
            if fit == "requires_product_architecture_decision":
                action += " El cambio requiere una decisión explícita de producto o arquitectura."
            if wording.get("proposal_detail") == "insufficient":
                action += " Antes de esa revisión falta aclarar: «" + wording["clarification_question"] + "»"
    # A sourced next step does not resolve a separate structured wait. Keep
    # that state visible even if the attributed action wording omits it.
    wait_limit = {
        "AWAIT_EVIDENCE": "El trabajo sigue a la espera de evidencia; esta recomendación no da esa condición por resuelta.",
        "AWAIT_HUMAN_DECISION": "El trabajo sigue a la espera de una decisión humana; esta recomendación no sustituye esa decisión.",
        "BLOCKED_BY_CURRENT_OWNER": "El trabajo sigue bloqueado por su responsable actual; esta recomendación no levanta ese bloqueo.",
        "WAIT_FOR_EXISTING_WORK": "El trabajo permanece aplazado; esta recomendación no da su condición de retorno por cumplida.",
    }.get(ownership)
    recommendation = "La continuación recomendada es: " + action.rstrip(".") + "."
    if wait_limit:
        recommendation += " " + wait_limit
    lines.insert(2, recommendation)
    if has_proposal and fit == "documented_human_exception; authenticity_not_verified":
        lines.append("Hay una excepción documentada para este alcance, pero no se ha autenticado quién la aprobó. No autoriza su ejecución.")
    elif has_proposal:
        lines.append("Preparar esa revisión no significa que la propuesta esté aceptada ni te da permiso para aprobarla o implementarla.")
    else:
        lines.append("Esta orientación no añade permisos a los indicados.")
    if has_proposal:
        lines.append("No se ha demostrado un beneficio con este recorrido.")
    return "\n\n".join(lines)
