"""Informations revelees aux participants, distinctes de la vue enseignant."""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.dont_write_bytecode = True
from eco.engine import Game, new_state
from eco import rules as R


class ParticipantInformationTest(unittest.TestCase):
    def setUp(self):
        self.game = Game(new_state(code="TEST", team_count=2))
        self.game.state["auto_teams"] = False
        for i in range(10):
            self.game.join("Joueur %d" % i, "TEST")
        self.tokens = {
            p["role"]: token
            for token, p in self.game.state["players"].items()
            if p["team"] == "BLUE"
        }

    def view(self, role="MOBI"):
        return self.game.player_view(self.tokens[role])

    def test_lobby_has_only_role_and_raw_private_numbers(self):
        for role in R.ROLES:
            view = self.view(role)
            self.assertEqual(view["me"]["cost"], R.COST[role])
            self.assertEqual(view["me"]["outside"], R.OUTSIDE[role])
            self.assertNotIn("threshold", view["me"])
            self.assertIsNone(view["me"]["power"])
            self.assertIsNone(view["market"])
            self.assertIsNone(view["shock_warning"])
            self.assertEqual(view["team"]["rounds"], {})

    def test_rounds_appear_only_when_opened(self):
        for phase, expected in [
            ("R1_NEGO", {"1"}),
            ("R2_NEGO", {"1", "2"}),
            ("MARKET", {"1", "2"}),
            ("R3_ARCH", {"1", "2", "3"}),
        ]:
            self.game.set_phase(phase)
            self.assertEqual(set(self.view()["team"]["rounds"]), expected)

    def test_powers_arrive_with_relevant_phase_without_future_schedule(self):
        for role in R.ROLES:
            first = min(R.PHASE_KEYS.index(ph) for ph in R.POWERS[role]["phases"])
            self.game.set_phase(R.PHASE_KEYS[first - 1])
            self.assertIsNone(self.view(role)["me"]["power"])
            self.game.set_phase(R.PHASE_KEYS[first])
            power = self.view(role)["me"]["power"]
            self.assertEqual(power["name"], R.POWERS[role]["name"])
            self.assertNotIn("phases", power)
            self.assertNotIn("round", power["text"].lower())

    def test_market_rules_are_hidden_until_market(self):
        self.game.set_phase("R2_NEGO")
        self.assertIsNone(self.view("BRAIN")["market"])
        self.game.set_phase("MARKET")
        self.assertEqual(self.view("BRAIN")["market"]["switch_cost"], R.SWITCH_COST)

    def test_badges_are_reserved_for_final_review(self):
        self.game.set_phase("R2_NEGO")
        self.game.submit_contract(
            self.tokens["MOBI"], dict(MOBI=4, AUTO=8, BRAIN=12, GRID=8, FLEET=8)
        )
        self.assertEqual(self.view()["team"]["badges"], [])
        self.assertIn(
            "HOLD_UP", [b["key"] for b in self.game.host_view()["teams"]["BLUE"]["badges"]]
        )
        self.game.set_phase("FINAL")
        self.assertIn("HOLD_UP", [b["key"] for b in self.view()["team"]["badges"]])

    def test_rewinding_saved_game_does_not_reveal_future(self):
        self.game.set_phase("R3_ARCH")
        self.game.submit_architecture(self.tokens["MOBI"], "PROPRIETARY", {})
        self.game.set_phase("R3_SHOCK")
        self.game.force_shock("REGULATION")
        self.game.set_phase("R3_NEGO")
        self.game.submit_resolution(self.tokens["MOBI"], "ABANDON", {}, {})
        restored = Game(copy.deepcopy(self.game.state))
        restored.set_phase("R3_ARCH")
        view = restored.player_view(self.tokens["MOBI"])
        third = view["team"]["rounds"]["3"]
        self.assertIsNone(view["shock"])
        self.assertIsNone(third["shock"])
        self.assertIsNone(third["resolution"])
        self.assertEqual(third["history"], [])
        restored.set_phase("LOBBY")
        self.assertEqual(restored.player_view(self.tokens["MOBI"])["team"]["rounds"], {})
        self.assertEqual(restored.state["teams"]["BLUE"]["rounds"]["3"]["resolution"], "ABANDON")


if __name__ == "__main__":
    unittest.main()
