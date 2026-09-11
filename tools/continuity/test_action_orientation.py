"""Source-bound action orientation; technical evidence, not human acceptance."""
import copy
from pathlib import Path
import unittest

import test_work_composition as fixture
from continue_work import run, write_json
from reader_brief import render_reader, wording_binding
from adoption_engine.profile import file_hash, stable_hash


class ActionOrientationTest(unittest.TestCase):
    def setUp(self):
        self.f = fixture.WorkCompositionTest()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.facts = {
            "objective": "Preparar un inventario fiable para que el taller reponga material faltante.",
            "audience": "El equipo del taller utiliza este inventario para preparar su trabajo.",
            "state": "Llegó una caja con etiqueta ilegible; su contenido sigue sin identificar.",
            "existing_work": "El equipo mantiene el inventario abierto y conserva la anotación de la caja pendiente.",
            "next": "Pide a almacén que identifique el contenido de la caja antes de incorporarlo al inventario como comprobado.",
            "value": "No se ha medido ningún beneficio de esta orientación.",
            "indicator": "No hay un indicador definido en las fuentes de este caso.",
        }
        self.rule = "No marques la caja como comprobada sin identificar su contenido; conserva la anotación pendiente."
        self.f.source.write_text("# Inventario sintético\n" + "\n".join(self.facts.values()) + "\n" + self.rule + "\n")
        self.f.config["claims"] = {k: {"text": v, "citations": [{"path": "docs/turno.md", "quote": v}]}
                                   for k, v in self.facts.items()}
        self.f.config["governing_decisions"] = [{"id": "unidentified-box", "text": self.rule,
            "checked_by": "operador de prueba", "check_scope": "Regla ficticia de inventario",
            "citations": [{"path": "docs/turno.md", "quote": self.rule, "source_hash": file_hash(self.f.source)}]}]
        item = self.f.config["ownership"]["work_items"][0]
        item.update(title="Inventario del taller", owner="equipo del taller", return_condition="Contenido identificado por almacén")

    def wording(self, record):
        words = self.f.wording(record)
        words.update(case="Eres quien retoma el inventario del taller.", work=self.facts["state"] + " " + self.facts["existing_work"],
                     objective=self.facts["objective"], beneficiaries=self.facts["audience"], decision_owner=self.facts["next"])
        words["unknowns"] = [{"binding": stable_hash(g), "text": {
            "next": "Falta saber quién debe identificar la caja y qué comprobación debe aportar.",
            "value": "No hay evidencia de beneficio medido.",
            "indicator": "No hay un indicador definido; no se inventa uno."
        }.get(g.split(":")[0], "Queda pendiente comprobar la información o restricción indicada.")} for g in record["gaps"]]
        return words

    def primary_action(self, text):
        return next(p for p in text.split("\n\n") if p.startswith("La continuación recomendada"))

    def test_known_action_leads_with_purpose_actor_and_condition(self):
        record = self.f.record(); words = self.wording(record); before = copy.deepcopy(record)
        text = render_reader(record, words)
        self.assertIn(self.facts["next"], self.primary_action(text))
        self.assertLess(text.index(self.facts["objective"]), text.index(self.facts["next"]))
        self.assertLess(text.index(self.facts["next"]), text.index(self.facts["state"]))
        self.assertEqual(text.count(self.facts["next"]), 1)
        self.assertNotIn("persona responsable", self.primary_action(text))
        self.assertIn(self.rule, text)
        self.assertEqual(record, before)
        self.assertEqual(record["claims"]["next"]["text"], self.facts["next"])
        self.assertFalse(record["proposal_review"]["execution_authorized"])

    def test_actual_wait_uses_known_pending_condition(self):
        self.f.config["ownership"]["work_items"][0]["lifecycle_state"] = "awaiting_evidence"
        record = self.f.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["continuation"], "AWAIT_EVIDENCE")
        self.assertIn(self.facts["next"], self.primary_action(text))
        self.assertIn("sigue a la espera de evidencia", self.primary_action(text))
        self.assertNotIn("propuesta", text)

    def test_structured_waits_remain_visible_even_when_next_omits_them(self):
        states = {
            "awaiting_evidence": ("AWAIT_EVIDENCE", "sigue a la espera de evidencia"),
            "awaiting_human_decision": ("AWAIT_HUMAN_DECISION", "sigue a la espera de una decisión humana"),
            "blocked": ("BLOCKED_BY_CURRENT_OWNER", "sigue bloqueado por su responsable actual"),
            "deferred": ("WAIT_FOR_EXISTING_WORK", "permanece aplazado"),
        }
        for lifecycle, (disposition, limit) in states.items():
            with self.subTest(lifecycle=lifecycle):
                case = ActionOrientationTest(); case.setUp()
                try:
                    step = "Actualiza la lista de inventario para retomar el trabajo."
                    case.f.source.write_text(case.f.source.read_text() + step + "\n")
                    case.f.config["claims"]["next"] = {"text": step, "citations": [{"path": "docs/turno.md", "quote": step}]}
                    case.f.config["governing_decisions"][0]["citations"][0]["source_hash"] = file_hash(case.f.source)
                    case.f.config["ownership"]["work_items"][0]["lifecycle_state"] = lifecycle
                    record = case.f.record(); words = case.wording(record)
                    words["decision_owner"] = step
                    text = render_reader(record, words)
                    self.assertEqual(record["ownership_disposition"], disposition)
                    self.assertIn(limit, case.primary_action(text))
                    self.assertIn("no", case.primary_action(text).lower())
                    self.assertFalse(record["proposal_review"]["execution_authorized"])
                finally:
                    case.doCleanups()

    def test_missing_next_shows_specific_gap_not_supplied_unchecked_action(self):
        del self.f.config["claims"]["next"]
        record = self.f.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["status"], "needs_clarification")
        self.assertIn("Falta saber quién debe identificar", self.primary_action(text))
        self.assertNotIn(self.facts["next"], text)

    def test_unknown_owner_is_not_filled_by_attributed_wording(self):
        del self.f.config["ownership"]
        record = self.f.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["ownership_disposition"], "OWNERSHIP_UNKNOWN")
        self.assertIn("aclarar quién tiene a cargo", self.primary_action(text))
        self.assertNotIn(self.facts["next"], self.primary_action(text))

    def test_conflicting_sources_preserve_uncertainty(self):
        second = copy.deepcopy(self.f.config["ownership"]["work_items"][0])
        second.update(id="inventory.other", owner="otro equipo")
        self.f.config["ownership"]["work_items"].append(second)
        record = self.f.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["ownership_disposition"], "OWNERSHIP_CONFLICT")
        self.assertIn("conflicto", text)
        self.assertNotIn(self.facts["next"], self.primary_action(text))

    def test_material_change_does_not_reuse_specific_action(self):
        record = self.f.record(); words = self.wording(record)
        self.f.source.write_text(self.f.source.read_text() + "\nLa identificación de la caja cambió.\n")
        current = self.f.record(); text = render_reader(current, words)
        self.assertEqual(current["status"], "reanchor_required")
        self.assertNotIn(self.facts["next"], text)
        self.assertIn("histórica", text)

    def test_missing_measurements_stay_unknown_without_blocking_known_action(self):
        del self.f.config["claims"]["value"]
        del self.f.config["claims"]["indicator"]
        record = self.f.record(); text = render_reader(record, self.wording(record))
        self.assertEqual(record["status"], "brief_prepared_for_review")
        self.assertIn(self.facts["next"], self.primary_action(text))
        self.assertIn("No hay evidencia de beneficio medido", text)
        self.assertIn("No hay un indicador definido", text)
        self.assertIsNone(record["human_measurements"])

    def test_real_proposal_keeps_named_approval_boundary(self):
        del self.f.config["claims"]["existing_work"]
        self.f.config["ownership"]["work_items"] = []
        approval = "Prepara para la jefatura del taller la revisión del cambio de inventario; debe aprobarlo antes de aplicarlo."
        self.f.source.write_text(self.f.source.read_text() + approval + "\n")
        self.f.config["claims"]["next"] = {"text": approval, "citations": [{"path": "docs/turno.md", "quote": approval}]}
        self.f.config["governing_decisions"][0]["citations"][0]["source_hash"] = file_hash(self.f.source)
        self.f.add_proposal()
        record = self.f.record(); words = self.wording(record)
        words.update(decision_owner=approval, proposal="Se propone cambiar el formato del inventario.")
        text = render_reader(record, words)
        self.assertIn(approval, self.primary_action(text))
        self.assertIn("no significa que la propuesta esté aceptada", text)
        self.assertFalse(record["proposal_review"]["execution_authorized"])

    def test_orientation_has_no_renderer_instructions_for_scoring_trial(self):
        record = self.f.record(); text = render_reader(record, self.wording(record))
        self.assertIn("Caso ficticio", text)
        self.assertNotIn("para este ensayo", text)
        self.assertNotIn("episodio", text)
        self.assertNotIn("¿Qué harías", text)


if __name__ == "__main__":
    unittest.main()
