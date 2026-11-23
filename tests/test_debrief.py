"""Les graphiques doivent retrouver les vrais comptes, sans doubler les recettes."""

import os
import sys
import unittest
import uuid
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from eco.campaign import Game, new_state, PROFILES
from eco import rules as R


class DebriefTest(unittest.TestCase):
    def setUp(self):
        self.g = Game(new_state(code="TEST", seed="debrief"))
        for i in range(10):
            self.g.join(code="TEST", first_name="Test", last_name=str(i))
        self.tokens = {(p["team"], p["role"]): p["id"] for p in self.g.state["players"].values()}
        self.g.step()

    def act(self, role, action, **kw):
        self.g.action(
            self.tokens["BLUE", role], dict(action=action, request_id=uuid.uuid4().hex, **kw)
        )

    def sign(self, kind="INSTALL", **kw):
        if kind == "INSTALL":
            for role in R.ROLES:
                self.act(role, "profile", choice=PROFILES[role][0][0])
        self.act(
            "MOBI",
            "propose",
            kind=kind,
            architecture="MODULAR",
            launch="EARLY",
            allocations={
                r: v * (38 if kind == "INSTALL" else self.g.gross("BLUE") // 100)
                for r, v in kw.get("shares", {r: 20 for r in R.ROLES}).items()
            },
            funding={
                r: v * 100
                for r, v in kw.get("funding", {"MOBI": 6} if kind == "INSTALL" else {}).items()
            },
        )
        p = self.g.c("BLUE")["proposal"]
        for role in p["required"]:
            self.act(role, "consent", choice="ACCEPT", revision=p["revision"])

    def advance(self, wanted="ORDINARY"):
        def draw(team, channel):
            if channel != "external_event":
                return 0.99 if channel == "commissioning" else 0.5
            weights = self.g.event_candidates(team)[0]
            selected = wanted if wanted in dict(weights) else weights[0][0]
            lo = 0
            for name, weight in weights:
                if name == selected:
                    return lo + weight / 2
                lo += weight

        with patch.object(self.g, "draw", side_effect=draw):
            self.g.step()

    def finish(self):
        while self.g.state["phase"] != "FINAL":
            self.advance()
        return self.g.host_view()["debrief"]

    def test_data_is_gated_until_final_and_excludes_identities(self):
        self.assertIsNone(self.g.host_view()["debrief"])
        self.assertNotIn("debrief", self.g.player_view(self.tokens["BLUE", "MOBI"]))
        data = self.finish()
        import json

        encoded = json.dumps(data)
        for token in self.tokens.values():
            self.assertNotIn(token, encoded)
        self.assertNotIn('"first_name"', encoded)
        self.assertEqual(len(data["teams"]), 2)

    def test_value_and_company_results_reconcile_with_cash_and_outside(self):
        self.sign()
        data = self.finish()
        for t in data["teams"]:
            f = t["finances"]
            self.assertEqual(f["accounting_gap"], 0)
            self.assertEqual(f["distribution_gap"], 0)
            self.assertEqual(sum(a["project_result"] for a in t["actors"]), f["created"])
            self.assertEqual(t["periods"][-1]["company_result"], f["company_result"])
            self.assertEqual(t["periods"][-1]["created"], f["created"])
        green = next(t for t in data["teams"] if t["team"] == "GREEN")
        self.assertEqual(green["finances"]["created"], 0)
        self.assertEqual(green["finances"]["company_result"], 0)
        self.assertEqual(green["contracts"], [])
        self.assertTrue(all(e["category"] == "context" for e in green["events"]))

    def test_external_provider_is_a_cost_not_a_sixth_human_or_double_income(self):
        self.sign()
        self.advance("INFRA")
        self.sign(
            "REPLACE",
            shares=dict(MOBI=20, AUTO=20, BRAIN=20, FLEET=20, ALT=20),
            funding={"MOBI": 3},
        )
        blue = next(t for t in self.finish()["teams"] if t["team"] == "BLUE")
        f = blue["finances"]
        self.assertGreater(f["supplier"], 0)
        self.assertEqual(f["revenue"], sum(a["revenue"] for a in blue["actors"]) + f["supplier"])
        self.assertEqual(
            f["created"],
            f["revenue"] - f["installation"] - f["adaptation"] - f["operation"] - f["supplier"],
        )
        self.assertEqual(len(blue["actors"]), 5)
        self.assertEqual(blue["contracts"][-1]["allocations"]["ALT"], 760)

    def test_private_shock_and_response_are_in_the_correct_order(self):
        self.sign()
        self.advance("PRIVATE_COST")
        role = next(iter(self.g.c("BLUE")["cost_shocks"]))
        self.act(role, "renegotiate")
        self.act(role, "withdraw")
        blue = next(t for t in self.finish()["teams"] if t["team"] == "BLUE")
        events = blue["events"]
        indices = [
            next(i for i, e in enumerate(events) if e["kind"] == kind)
            for kind in ["event_drawn", "renegotiation_requested", "capacity_withdrawn"]
        ]
        self.assertEqual(indices, sorted(indices))
        shock = events[indices[0]]
        self.assertIn(role, shock["detail"])
        self.assertEqual(shock["category"], "circumstance")
        self.assertEqual(events[indices[1]]["category"], "decision")
        self.assertEqual(blue["finances"]["distribution_gap"], 0)


if __name__ == "__main__":
    unittest.main()
