"""Contrats, intentions, confidentialité et reprise : python tests/test_negociation.py."""

import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.dont_write_bytecode = True
from eco.engine import Game, GameError, new_state, score_simple, score_round3
from eco import rules as R


class NegotiationTest(unittest.TestCase):
    def setUp(self):
        self.g = Game(new_state(code="TEST", team_count=2))
        self.g.state["auto_teams"] = False
        for i in range(10):
            self.g.join("Joueur %d" % i, "TEST")
        self.tokens = {
            (p["team"], p["role"]): token for token, p in self.g.state["players"].items()
        }
        self.mobi = self.tokens[("BLUE", "MOBI")]
        self.fleet = self.tokens[("BLUE", "FLEET")]
        self.contract = dict(MOBI=6, AUTO=9, BRAIN=9, GRID=6, FLEET=10)

    def rd(self, n=2):
        return self.g.state["teams"]["BLUE"]["rounds"][str(n)]

    def publish(self):
        self.g.set_phase("R2_NEGO")
        self.g.submit_contract(self.mobi, self.contract)

    def test_revisions_reset_intentions_and_keep_history(self):
        self.publish()
        self.g.signal(self.fleet, "DISCUSS", 1)
        updated = dict(self.contract, MOBI=5, FLEET=11)
        self.g.submit_contract(self.mobi, updated)
        self.assertEqual(self.rd()["revision"], 2)
        self.assertEqual(self.rd()["signals"], {})
        self.assertEqual(self.rd()["history"][0]["contract"], self.contract)
        with self.assertRaises(GameError):
            self.g.signal(self.fleet, "READY", 1)

    def test_signals_do_not_vote_or_change_scores(self):
        self.publish()
        self.g.signal(self.fleet, "READY", 1)
        self.assertEqual(self.rd()["decisions"], {})
        self.assertEqual(self.g.state["teams"]["BLUE"]["adjust"]["FLEET"], 0)
        self.g.signal(self.fleet, "CLEAR", 1)
        self.assertEqual(self.rd()["signals"], {})

    def test_team_visibility_and_host_aggregates(self):
        self.publish()
        self.g.signal(self.fleet, "DISCUSS", 1)
        own = self.g.player_view(self.mobi)["team"]["rounds"]["2"]
        other = self.g.player_view(self.tokens[("GREEN", "MOBI")])["team"]["rounds"]["2"]
        host = self.g.host_view()["teams"]["BLUE"]["rounds"]["2"]
        self.assertEqual(own["signals"], {"FLEET": "DISCUSS"})
        self.assertEqual(other["signals"], {})
        self.assertNotIn("signals", host)
        self.assertEqual(host["discuss_count"], 1)

    def test_secret_vote_until_results_and_frozen_contract(self):
        self.publish()
        self.g.set_phase("R2_DECIDE")
        self.g.decide(self.fleet, "OUT")
        host = self.g.host_view()["teams"]["BLUE"]["rounds"]["2"]
        self.assertEqual(host["answered"], 1)
        self.assertNotIn("decisions", host)
        self.assertNotIn("decisions", self.g.player_view(self.mobi)["team"]["rounds"]["2"])
        with self.assertRaises(GameError):
            self.g.submit_contract(self.mobi, self.contract)
        self.g.set_phase("R2_RESULTS")
        self.assertEqual(
            self.g.host_view()["teams"]["BLUE"]["rounds"]["2"]["decisions"]["FLEET"], "OUT"
        )

    def test_invalid_or_out_of_phase_signals(self):
        with self.assertRaises(GameError):
            self.g.signal(self.fleet, "READY", 0)
        self.g.set_phase("R2_NEGO")
        with self.assertRaises(GameError):
            self.g.signal(self.fleet, "READY", 0)
        self.publish()
        with self.assertRaises(GameError):
            self.g.signal(self.fleet, "JOIN", 1)
        self.g.set_phase("R2_DECIDE")
        with self.assertRaises(GameError):
            self.g.signal(self.fleet, "READY", 1)

    def test_round3_freeze_and_replaced_partner(self):
        self.g.set_phase("R3_ARCH")
        self.g.submit_architecture(self.mobi, "PROPRIETARY", {})
        self.g.set_phase("R3_SHOCK")
        self.g.force_shock("INFRA_FAILURE")
        self.g.set_phase("R3_NEGO")
        revenues = dict(MOBI=4, AUTO=8, BRAIN=8, FLEET=6, ALT_AI=8)
        integration = dict(MOBI=10, AUTO=0, BRAIN=0, FLEET=0)
        self.g.submit_resolution(self.mobi, "REPLACE", revenues, integration)
        with self.assertRaises(GameError):
            self.g.signal(self.tokens[("BLUE", "GRID")], "READY", 1)
        self.g.signal(self.fleet, "DISCUSS", 1)
        self.g.set_phase("R3_DECIDE")
        self.g.decide(self.fleet, "OUT")
        with self.assertRaises(GameError):
            self.g.submit_resolution(self.mobi, "ABANDON", {}, {})
        self.assertEqual(self.rd(3)["decisions"]["FLEET"], "OUT")

    def test_resume_and_migrate_old_saves(self):
        self.publish()
        self.g.signal(self.fleet, "READY", 1)
        resumed = Game(copy.deepcopy(self.g.state))
        self.assertEqual(
            resumed.player_view(self.fleet)["team"]["rounds"]["2"]["signals"], {"FLEET": "READY"}
        )
        old = copy.deepcopy(self.g.state)
        for team in old["teams"].values():
            for rd in team["rounds"].values():
                for key in ("revision", "signals", "history"):
                    rd.pop(key)
        migrated = Game(old)
        self.assertEqual(migrated.player_view(self.fleet)["team"]["rounds"]["2"]["revision"], 0)
        self.assertEqual(migrated.state["teams"]["BLUE"]["rounds"]["2"]["contract"], self.contract)

    def test_reopening_round_clears_signals_and_history(self):
        self.publish()
        self.g.signal(self.fleet, "READY", 1)
        self.g.set_phase("R2_DECIDE")
        self.g.set_phase("R2_RESULTS")
        self.g.unlock_round(2)
        self.assertEqual(self.rd()["history"], [])
        self.assertEqual(self.rd()["signals"], {})
        self.assertIsNone(self.rd()["result"])

    def test_readme_practice_rounds_1_and_2(self):
        choices = {r: "JOIN" for r in R.ROLES}
        choices["FLEET"] = "OUT"
        r1 = score_simple(choices, R.R1_REVENUE)
        self.assertEqual(list(r1["scores"].values()), [7, 5, 6, 6, 14])
        self.assertEqual(r1["ecosystem"], -16)
        r2 = score_simple({r: "JOIN" for r in R.ROLES}, self.contract)
        self.assertEqual(list(r2["scores"].values()), [13, 14, 15, 12, 15])
        self.assertEqual(r2["ecosystem"], 19)

    def test_readme_practice_architecture_comparison(self):
        blue = score_round3(
            dict(
                architecture="MODULAR",
                resolution="REPLACE",
                shock="AI_FAILURE",
                standard=dict(MOBI=2, AUTO=1, BRAIN=1, GRID=1, FLEET=1),
                integration=dict(MOBI=2, AUTO=0, BRAIN=0, GRID=0, FLEET=0),
                contract=dict(MOBI=9, AUTO=9, GRID=6, FLEET=8, ALT_AI=8),
                decisions={r: "JOIN" for r in R.ROLES if r != "BRAIN"},
            )
        )
        green = score_round3(
            dict(
                architecture="PROPRIETARY",
                resolution="KEEP",
                shock="AI_FAILURE",
                contract=dict(MOBI=6, AUTO=9, BRAIN=14, GRID=6, FLEET=11),
                decisions={r: "JOIN" for r in R.ROLES},
            )
        )
        self.assertTrue(blue["success"] and green["success"])
        self.assertEqual(blue["ecosystem"], 11)
        self.assertEqual(green["ecosystem"], 19)
        self.assertEqual(list(blue["scores"].values()), [12, 13, 13, 11, 12])
        self.assertEqual(list(green["scores"].values()), [13, 14, 14, 12, 16])


if __name__ == "__main__":
    unittest.main()
