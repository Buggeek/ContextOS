"""Presentation fidelity/boundary tests; never evidence of human comprehension."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from continue_work import ROOT, read_json, render, run, write_json
from reader_brief import render_reader, wording_binding, wording_issues
from adoption_engine.profile import stable_hash
from synthetic_example import create, bind_review, accept_synthetic_exception


def spanish_copy(record):
    """Attributed test wording, not a production translation lookup."""
    return {"binding": wording_binding(record), "language": "es", "authored_by": "test operator",
            "case_kind": "synthetic", "case": "Un equipo de soporte trabaja con voluntarios.",
            "work": "Existe un trabajo en curso a cargo del equipo de soporte.",
            "objective": "Se busca ayudar a los voluntarios que regresan a continuar su trabajo.",
            "beneficiaries": "Los beneficiarios son los voluntarios.",
            "decision_owner": "El responsable de producto tiene pendiente revisar la propuesta.",
            "proposal": "Se propone añadir ayuda para retomar el trabajo dentro de las tarjetas existentes.",
            "proposal_detail": "insufficient", "proposal_missing": "Falta concretar qué información mostrarían las tarjetas.",
            "clarification_question": "¿Qué información mostrarían las tarjetas para ayudar a retomar el trabajo?",
            "restrictions": [{"binding": stable_hash(item), "text": "Las tarjetas deben seguir siendo la superficie principal; cambiarla requiere una decisión de producto."}
                             for item in record.get("governing_decisions", [])],
            "unknowns": [{"binding": stable_hash(gap), "text": "Falta información para completar la revisión; no se debe asumir que está resuelta."}
                         for gap in record.get("gaps", [])]}


class ReaderBriefTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = create(Path(self.temp.name) / "case")
        self.config = read_json(self.workspace / "work.json")
        self.target = Path(self.config["source"]["root"])

    def record(self, **kwargs):
        write_json(self.workspace / "work.json", self.config)
        return run(self.workspace, **kwargs)

    def test_context_and_roles_precede_honestly_incomplete_proposal(self):
        record = self.record()
        before = copy.deepcopy(record)
        text = render_reader(record, spanish_copy(record))
        self.assertLess(text.index("trabajo en curso"), text.index("Se propone"))
        self.assertLess(text.index("Los beneficiarios"), text.index("responsable de producto"))
        self.assertIn("Esa responsabilidad no se te atribuye", text)
        self.assertIn("Falta concretar", text)
        self.assertEqual(text.count("Lo que puedes hacer ahora"), 1)
        self.assertIn("preparar", text)
        self.assertIn("no significa que la propuesta esté aceptada", text)
        self.assertIn("Caso ficticio", text)
        self.assertIn("No se ha demostrado un beneficio", text)
        for technical in ("Propuesta A.1", "synthetic-", "--format", "JSON", "baseline", "schema", record["input_hash"]):
            self.assertNotIn(technical, text)
        self.assertEqual(record, before)
        self.assertFalse(record["proposal_review"]["execution_authorized"])

    def test_missing_wording_is_spanish_uncertainty_not_raw_foreign_text(self):
        record = self.record()
        text = render_reader(record)
        self.assertIn("Falta una explicación en español", text)
        self.assertIn("Hay restricciones", text)
        self.assertNotIn("Help returning", text)
        self.assertNotIn("Lo que puedes hacer ahora", text)
        self.assertIn("no autoriza", text)

    def test_stale_wording_cannot_reuse_old_proposal_after_source_change(self):
        record = self.record(); wording = spanish_copy(record)
        source = self.target / "docs/work.md"
        source.write_text(source.read_text() + "\nMaterial constraint: another review is needed.\n")
        current = self.record()
        self.assertEqual(current["status"], "reanchor_required")
        text = render_reader(current, wording)
        self.assertIn("referencia anterior es histórica", text)
        self.assertIn("Hay restricciones", text)
        self.assertNotIn(wording["proposal"], text)

    def test_incomplete_translation_coverage_cannot_hide_known_restriction(self):
        record = self.record(); wording = spanish_copy(record)
        wording["restrictions"] = []
        self.assertTrue(wording_issues(record, wording))
        text = render_reader(record, wording)
        self.assertIn("Hay restricciones", text)
        self.assertNotIn("Lo que puedes hacer ahora", text)
        self.assertEqual(len(record["governing_decisions"]), 1)

    def test_unverifiable_restriction_keeps_its_meaning_and_limits_continuation(self):
        self.config["governing_decisions"][0]["citations"][0]["quote"] = "Missing quote"
        record = self.record(); wording = spanish_copy(record)
        text = render_reader(record, wording)
        self.assertIn("Las tarjetas deben seguir siendo la superficie principal", text)
        self.assertIn("No se ha podido comprobar esta restricción", text)
        self.assertIn("reunir la información pendiente", text)
        self.assertNotIn("preparar la propuesta para su revisión", text)
        self.assertEqual(record["status"], "needs_clarification")
        self.assertIn("quote_not_found", render(record))  # original technical explanation preserved

    def test_unknowns_must_be_covered_and_owner_cannot_be_assigned_to_reader(self):
        del self.config["ownership"]
        record = self.record(); wording = spanish_copy(record)
        text = render_reader(record, wording)
        self.assertIn("aclarar quién tiene a cargo", text)
        wording["unknowns"] = []
        self.assertTrue(wording_issues(record, wording))
        self.assertNotIn(wording["proposal"], render_reader(record, wording))
        self.assertEqual(record["ownership_disposition"], "OWNERSHIP_UNKNOWN")

    def test_private_record_never_echoes_custom_copy_id_hash_or_count(self):
        self.record()
        self.config["source"]["visible_sources"].remove("docs/work.md")
        self.config["source"]["withheld_sources"] = ["docs/work.md"]
        record = self.record()
        wording = spanish_copy(record)
        for key in ("case", "work", "proposal", "decision_owner"):
            wording[key] = "PRIVATE_CANARY_ID_HASH_COUNT"
        text = render_reader(record, wording)
        self.assertNotIn("CANARY", text)
        self.assertNotIn("docs/work.md", text)
        self.assertIn("información de este trabajo no se puede mostrar", text)
        self.assertFalse(record["proposal_review"]["execution_authorized"])

    def test_conflict_and_exception_keep_distinct_limits_and_single_action(self):
        self.config["proposal"]["content"] = "Dominant surface replacing cards"
        self.config["review"]["fit"] = "conflict"
        bind_review(self.config)
        conflict = self.record()
        wording = spanish_copy(conflict)
        wording.update(proposal="Se propone reemplazar las tarjetas como superficie principal.", proposal_detail="described")
        self.assertIn("decisión pendiente sobre el cambio propuesto", render_reader(conflict, wording))
        accept_synthetic_exception(self.config)
        exception = self.record(reanchor=True, reason="Existing synthetic exception test")
        wording = spanish_copy(exception)
        wording.update(proposal="Se propone una superficie dominante para este ensayo.", proposal_detail="described")
        text = render_reader(exception, wording)
        self.assertIn("excepción documentada", text)
        self.assertIn("no se ha autenticado", text)
        self.assertIn("No autoriza su ejecución", text)
        self.assertEqual(text.count("Lo que puedes hacer ahora"), 1)
        self.assertFalse(exception["proposal_review"]["execution_authorized"])

    def test_unrelated_domain_uses_same_renderer_without_fixture_dictionary(self):
        # Renderer-only input; not a claim that another organization ran Runtime.
        record = copy.deepcopy(self.record())
        record.update(target_id="library-unit-case", intent="Review the loan reminder", observations=[], governing_decisions=[])
        record["claims"] = {"objective": {"text": "Clarify loan reminders"}, "state": {"text": "A library review is pending"},
                            "audience": {"text": "Library members"}, "next": {"text": "Library coordinator reviews"}}
        record["proposal_review"]["proposal"]["content"] = "Describe a due-date reminder"
        wording = spanish_copy(record)
        wording.update(case="Una biblioteca prepara avisos para sus socios.", work="Hay una revisión pendiente.",
                       objective="Se busca aclarar el aviso de vencimiento de préstamos.", beneficiaries="Los beneficiarios son los socios de la biblioteca.",
                       decision_owner="La coordinación de la biblioteca debe revisar el aviso.",
                       proposal="Se propone describir un aviso de vencimiento.", proposal_detail="described")
        text = render_reader(record, wording)
        self.assertIn("biblioteca", text)
        for special in ("voluntarios", "tarjetas", "soporte", "M-7", "A.1"):
            self.assertNotIn(special, text)

    def test_detail_is_preserved_and_default_cli_uses_bound_copy_without_machine_mutation(self):
        record = self.record(); wording = spanish_copy(record)
        write_json(self.workspace / "brief.es.json", wording)
        command = [sys.executable, str(ROOT / "tools/continuity/continue_work.py"), str(self.workspace)]
        outputs = {}
        for mode in ("human", "detail", "json"):
            result = subprocess.run(command + ["--format", mode], capture_output=True, text=True,
                                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(result.stderr, "")
            outputs[mode] = result.stdout
        self.assertIn("Lo que puedes hacer ahora", outputs["human"])
        self.assertNotIn("--format json", outputs["human"])
        self.assertIn("--format json", outputs["detail"])
        checked = json.loads(outputs["json"])
        self.assertEqual(wording_binding(record), wording_binding(checked))
        self.assertEqual(record["governing_decisions"], checked["governing_decisions"])
        self.assertEqual(record["proposal_fit"], checked["proposal_fit"])
        self.assertFalse(checked["proposal_review"]["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
