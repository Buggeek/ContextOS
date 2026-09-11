"""Operational/proposal counterexamples; no human acceptance is simulated."""
import copy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from continue_work import ROOT, render, run, write_json
from reader_brief import render_reader, wording_binding
from adoption_engine.profile import file_hash, stable_hash
from review_evidence import review_binding

sys.path.insert(0, str(ROOT / "tools/activation"))
import test_activation_package as activation_fixture


class WorkCompositionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.target, self.work = self.base / "target", self.base / "work"
        with activation_fixture.ContextActivationPackageTestCase().make_repo() as source:
            shutil.copytree(source, self.target)
        self.work.mkdir()
        self.source = self.target / "docs/turno.md"
        statements = {
            "objective": "El equipo informa a sus visitantes de una hora de atención confirmada.",
            "audience": "Las personas visitantes necesitan organizar su visita.",
            "state": "El turno de soporte está activo y una solicitud sigue abierta.",
            "existing_work": "El equipo mantiene el turno vigente y su registro aunque un cambio de formato espere revisión.",
            "next": "La coordinación confirma disponibilidad; la persona voluntaria puede solicitar esa información.",
            "value": "La intención es informar con disponibilidad vigente; no se ha medido un beneficio.",
            "indicator": "Se podría contrastar la explicación con el registro vigente; no hay una medición realizada.",
        }
        self.rule = "Solo se comunica una hora confirmada por la coordinación; se conserva abierto el registro mientras falte esa confirmación."
        self.source.write_text("# Turno ficticio para pruebas\n" + "\n".join(statements.values()) + "\n" + self.rule + "\n")
        self.config = {
            "target_id": "synthetic-operation", "intent": "Retomar el turno de soporte ficticio",
            "source": {"kind": "local_corpus", "root": str(self.target),
                       "visible_sources": sorted(str(p.relative_to(self.target)) for p in self.target.rglob("*") if p.is_file())},
            "claims": {k: {"text": v, "citations": [{"path": "docs/turno.md", "quote": v}]} for k, v in statements.items()},
            "governing_decisions": [{"id": "confirmed-time", "text": self.rule,
                                      "checked_by": "operador de prueba", "check_scope": "Regla del turno ficticio",
                                      "citations": [{"path": "docs/turno.md", "quote": self.rule, "source_hash": file_hash(self.source)}]}],
            "ownership": {
                "need": {"id": "need.turn", "statement": "Atender solicitud vigente", "scope": "support", "evidence_refs": ["source.turn"]},
                "work_items": [{"id": "operation.turn", "kind": "operation", "title": "Turno vigente", "owner": "equipo de soporte",
                                "lifecycle_state": "active", "currentness": "current", "need_refs": ["need.turn"],
                                "parent_work_id": None, "source_ids": ["source.turn"], "authority_status": "target_authority",
                                "return_condition": "Disponibilidad confirmada", "evidence_refs": ["source.turn"]}],
                "source_declarations": [{"id": "source.turn", "locator": "docs/turno.md", "concept": "active_work"}],
                "coverage": {"status": "complete", "scope": "support", "source_ids": ["source.turn"],
                             "authority_status": "governed_test_coverage", "evidence_refs": ["source.turn"]}},
        }

    def record(self):
        write_json(self.work / "work.json", self.config)
        return run(self.work)

    def wording(self, record):
        return {"binding": wording_binding(record), "language": "es", "authored_by": "operador de pruebas",
                "case_kind": "synthetic", "case": "Una persona voluntaria retoma el turno de soporte.",
                "work": record["claims"].get("existing_work", {}).get("text", "Falta establecer qué trabajo se retoma."),
                "objective": self.config["claims"]["objective"]["text"], "beneficiaries": self.config["claims"]["audience"]["text"],
                "decision_owner": self.config["claims"].get("next", {}).get("text", "Falta explicar el siguiente paso."),
                "proposal": "Se propone cambiar el formato de respuestas.", "proposal_detail": "described",
                "restrictions": [{"binding": stable_hash(d), "text": d["text"]} for d in record["governing_decisions"]],
                "unknowns": [{"binding": stable_hash(g), "text": "La información indicada como pendiente sigue sin aclararse."} for g in record["gaps"]]}

    def add_proposal(self, fit="compatible"):
        self.config["proposal"] = {"id": "format-change", "version": "1", "content": "Cambiar el formato de respuestas",
                                   "author": "autor de prueba", "scope": "support"}
        self.config["review"] = {"fit": fit, "reviewed_by": "revisor de prueba", "rationale": "Juicio atribuido sobre este cambio ficticio",
                                 "constraint_refs": self.config["governing_decisions"][0]["citations"]}
        self.config["review"]["binding"] = review_binding(self.config, self.target, self.config["source"]["visible_sources"])

    def test_existing_operation_without_proposal_in_machine_and_reader(self):
        record = self.record()
        text = render_reader(record, self.wording(record))
        self.assertEqual(record["proposal_fit"], "no_proposal_submitted")
        self.assertNotIn("proposal", record["continuation"])
        self.assertNotIn("propuesta", text)
        self.assertNotIn("revisión", text.replace(self.config["claims"]["existing_work"]["text"], ""))
        self.assertIn(self.config["claims"]["next"]["text"], text)
        self.assertFalse(record["proposal_review"]["execution_authorized"])

    def test_real_proposal_without_existing_operation_keeps_review(self):
        del self.config["claims"]["existing_work"]
        self.config["ownership"]["work_items"] = []
        next_step = "Prepara para la persona responsable del formato la revisión de la propuesta; cambiarlo requiere su aprobación."
        self.source.write_text(self.source.read_text() + next_step + "\n")
        self.config["claims"]["next"] = {"text": next_step, "citations": [{"path": "docs/turno.md", "quote": next_step}]}
        self.config["governing_decisions"][0]["citations"][0]["source_hash"] = file_hash(self.source)
        self.add_proposal()
        record = self.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["continuation"], "prepare_proposal_for_review")
        self.assertIn(next_step, text)
        self.assertIn("no significa que la propuesta esté aceptada", text)

    def test_associated_change_does_not_replace_operational_continuity(self):
        self.add_proposal("conflict")
        record = self.record(); text = render_reader(record, self.wording(record))
        self.assertIn("resume_existing_work", record["continuation"])
        self.assertIn("await_explicit_product_architecture_decision", record["continuation"])
        self.assertIn(self.config["claims"]["next"]["text"], text)
        self.assertIn("decisión pendiente sobre el cambio propuesto", text)
        self.assertFalse(record["proposal_review"]["execution_authorized"])

    def test_operational_evidence_wait_is_not_product_approval(self):
        self.config["ownership"]["work_items"][0]["lifecycle_state"] = "awaiting_evidence"
        record = self.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["continuation"], "AWAIT_EVIDENCE")
        self.assertIn("confirm", text)
        self.assertIn(self.config["claims"]["next"]["text"], text)
        self.assertIn("sigue a la espera de evidencia", text)
        self.assertNotIn("propuesta", text)

    def test_unknown_work_does_not_default_to_a_product_proposal(self):
        del self.config["claims"]["existing_work"]
        self.config["ownership"]["work_items"] = []
        record = self.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["continuation"], "clarify_work_situation")
        self.assertIn("aclarar qué trabajo se retoma", text)
        self.assertNotIn("propuesta", text)

    def test_contradictory_ownership_remains_a_limit(self):
        second = copy.deepcopy(self.config["ownership"]["work_items"][0])
        second.update(id="operation.other", owner="otro equipo")
        self.config["ownership"]["work_items"].append(second)
        record = self.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["ownership_disposition"], "OWNERSHIP_CONFLICT")
        self.assertIn("aclarar quién tiene a cargo", text)
        self.assertNotIn("propuesta", text)

    def test_unverifiable_operational_rule_does_not_invent_proposal_review(self):
        self.config["governing_decisions"][0]["citations"][0]["quote"] = "Cita inexistente"
        record = self.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["status"], "needs_clarification")
        self.assertEqual(record["proposal_fit"], "no_proposal_submitted")
        self.assertNotIn("Proposal review", " ".join(record["gaps"]))
        self.assertIn("No se ha podido comprobar esta restricción", text)
        self.assertIn(self.rule, text)
        self.assertNotIn("propuesta", text)
        self.assertNotIn("propuesta", render(record).lower())

    def test_unreviewed_associated_change_retains_verified_operation(self):
        self.add_proposal()
        del self.config["review"]
        record = self.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["status"], "needs_clarification")
        self.assertEqual(record["proposal_fit"], "unverified_constraints")
        self.assertIn("resume_existing_work", record["continuation"])
        self.assertIn(self.config["claims"]["next"]["text"], text)
        self.assertIn("cambio asociado", text)
        self.assertFalse(record["proposal_review"]["execution_authorized"])

    def test_unreviewed_associated_change_retains_operational_wait(self):
        self.add_proposal()
        del self.config["review"]
        self.config["ownership"]["work_items"][0]["lifecycle_state"] = "awaiting_evidence"
        record = self.record(); text = render_reader(record, self.wording(record))
        self.assertIn("AWAIT_EVIDENCE", record["continuation"])
        self.assertIn(self.config["claims"]["next"]["text"], text)
        self.assertIn("sigue a la espera de evidencia", text)
        self.assertEqual(record["status"], "needs_clarification")

    def test_proposal_only_keeps_unknown_and_conflicting_owner_conditions(self):
        for unknown in (True, False):
            with self.subTest(unknown=unknown):
                f = WorkCompositionTest(); f.setUp()
                try:
                    del f.config["claims"]["existing_work"]
                    if unknown:
                        del f.config["ownership"]
                    else:
                        second = copy.deepcopy(f.config["ownership"]["work_items"][0])
                        second.update(id="operation.other", owner="otro equipo")
                        f.config["ownership"]["work_items"].append(second)
                    f.add_proposal()
                    record = f.record(); text = render_reader(record, f.wording(record))
                    self.assertIn("clarify_ownership", record["continuation"])
                    self.assertIn("prepare_proposal_for_review", record["continuation"])
                    self.assertIn("aclarar quién tiene a cargo", text)
                finally:
                    f.doCleanups()

    def test_orphan_review_is_incomplete_evidence_not_a_new_proposal(self):
        self.add_proposal()
        del self.config["proposal"]
        record = self.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["status"], "needs_clarification")
        self.assertEqual(record["proposal_fit"], "unverified_constraints")
        self.assertIsNone(record["proposal_review"].get("proposal"))
        self.assertNotIn("proposal", record["continuation"])
        self.assertIn("clarify", record["continuation"])
        self.assertNotIn("propuesta", text)
        self.assertNotIn("propuesta", render(record).lower())

    def test_unknown_operational_rule_still_limits_associated_continuity(self):
        self.add_proposal()
        del self.config["review"]
        self.config["governing_decisions"][0]["citations"][0]["quote"] = "Cita inexistente"
        record = self.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["status"], "needs_clarification")
        self.assertIn("clarify_current_work_constraints", record["continuation"])
        self.assertIn("No se ha podido comprobar esta restricción", text)
        self.assertNotIn("La continuación recomendada es: " + self.config["claims"]["next"]["text"], text)

    def test_material_change_never_reuses_old_operational_wording(self):
        record = self.record(); wording = self.wording(record)
        self.source.write_text(self.source.read_text() + "\nCambio material del turno ficticio.\n")
        current = self.record(); text = render_reader(current, wording)
        self.assertEqual(current["status"], "reanchor_required")
        self.assertIn("referencia anterior es histórica", text)
        self.assertNotIn("propuesta", text)
        self.assertNotIn(wording["work"], text)


if __name__ == "__main__":
    unittest.main()
