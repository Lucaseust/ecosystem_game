"""Identités, demande enseignant et retrait : python tests/test_etudiants.py."""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.dont_write_bytecode = True
from eco.engine import Game, GameError, new_state


class StudentManagementTest(unittest.TestCase):
    def setUp(self):
        self.g = Game(new_state(code="TEST"))
        self.token = self.g.join(code="TEST", first_name="Camille", last_name="D’Arcy")

    def test_registration_keeps_separate_identity_and_full_display(self):
        me = self.g.player_view(self.token)["me"]
        self.assertEqual(me["first_name"], "Camille")
        self.assertEqual(me["last_name"], "D’Arcy")
        self.assertEqual(me["name"], "Camille D’Arcy")
        self.assertFalse(me["identity_required"])

    def test_missing_or_invalid_fields_rejected(self):
        for first, last in [
            ("", "Durand"),
            ("Camille", " "),
            (None, "Durand"),
            ("a" * 41, "Durand"),
            ([], "Durand"),
        ]:
            with self.subTest(first=first, last=last), self.assertRaises(GameError):
                self.g.join(code="TEST", first_name=first, last_name=last)

    def test_request_and_update_keep_role_and_decisions(self):
        self.g.set_phase("R1_DECIDE")
        self.g.decide(self.token, "JOIN")
        before = copy.deepcopy(self.g.state["players"][self.token])
        self.g.request_identity()
        self.assertTrue(self.g.player_view(self.token)["me"]["identity_required"])
        self.g.set_identity(self.token, "  Jean   Pierre ", " Le   Gall ")
        p = self.g.state["players"][self.token]
        self.assertEqual(p["name"], "Jean Pierre Le Gall")
        self.assertEqual(p["role"], before["role"])
        self.assertEqual(p["team"], before["team"])
        self.assertEqual(self.g.player_view(self.token)["me"]["decision"], "JOIN")
        self.assertFalse(p["identity_required"])
        self.assertEqual(self.g.host_view()["players"][0]["last_name"], "Le Gall")

    def test_invalid_update_keeps_request_pending(self):
        self.g.request_identity()
        with self.assertRaises(GameError):
            self.g.set_identity(self.token, "Camille", "")
        self.assertTrue(self.g.state["players"][self.token]["identity_required"])
        self.assertEqual(self.g.state["players"][self.token]["name"], "Camille D’Arcy")

    def test_removal_invalidates_session_and_clears_unfinished_ballot(self):
        p = self.g.state["players"][self.token]
        team, role = p["team"], p["role"]
        self.g.set_phase("R1_NEGO")
        self.g.signal(self.token, "READY", 0)
        self.g.set_claim(self.token, 10, "Demande")
        self.g.set_phase("R1_DECIDE")
        self.g.decide(self.token, "OUT")
        self.g.remove_player(self.token)
        with self.assertRaises(GameError):
            self.g.player_view(self.token)
        rd = self.g.state["teams"][team]["rounds"]["1"]
        self.assertNotIn(role, rd["signals"])
        self.assertNotIn(role, rd["decisions"])
        self.assertNotIn(role, self.g.state["teams"][team]["claims"])
        self.assertTrue(self.g.is_bot(team, role))
        self.g.set_phase("R1_RESULTS")
        self.assertEqual(rd["decisions"][role], "JOIN")

    def test_removal_preserves_shared_seat_ballot(self):
        p = self.g.state["players"][self.token]
        other = self.g.join(code="TEST", first_name="Autre", last_name="Étudiant")
        self.g.reassign(other, p["team"], p["role"])
        self.g.set_phase("R1_DECIDE")
        self.g.decide(self.token, "OUT")
        self.g.remove_player(self.token)
        self.assertEqual(self.g.player_view(other)["me"]["decision"], "OUT")

    def test_removal_preserves_completed_results(self):
        self.g.set_phase("R1_DECIDE")
        self.g.decide(self.token, "JOIN")
        self.g.set_phase("R1_RESULTS")
        team = self.g.state["players"][self.token]["team"]
        before = copy.deepcopy(self.g.state["teams"][team]["rounds"]["1"])
        self.g.remove_player(self.token)
        self.assertEqual(self.g.state["teams"][team]["rounds"]["1"], before)

    def test_old_saves_request_identity_without_guessing_names(self):
        old = copy.deepcopy(self.g.state)
        p = old["players"][self.token]
        for key in ("first_name", "last_name", "identity_required"):
            p.pop(key)
        p["name"] = "Ancien pseudo"
        resumed = Game(old)
        me = resumed.player_view(self.token)["me"]
        self.assertTrue(me["identity_required"])
        self.assertEqual(me["name"], "Ancien pseudo")
        self.assertEqual(me["first_name"], "")
        resumed.set_identity(self.token, "Camille", "Durand")
        reloaded = Game(copy.deepcopy(resumed.state))
        self.assertFalse(reloaded.player_view(self.token)["me"]["identity_required"])


if __name__ == "__main__":
    unittest.main()
