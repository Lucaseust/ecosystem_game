"""Campagne cumulative, consentements, aléas, confidentialité et exports."""

import copy
import io
import os
import sys
import unittest
import uuid
import zipfile
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.dont_write_bytecode = True
from eco.campaign import Game, GameError, new_state, PROFILES, INITIAL, OPEX
from eco import rules as R


class CampaignTest(unittest.TestCase):
    def setUp(self):
        self.g = Game(new_state(code="TEST", seed="test-campaign"))
        self.g.set_team_count(2)
        for i in range(10):
            self.g.join(code="TEST", first_name="Étudiant", last_name=str(i))
        self.tokens = {
            (p["team"], p["role"]): token for token, p in self.g.state["players"].items()
        }
        self.g.step()

    def act(self, role, action, team="BLUE", **extra):
        body = dict(action=action, request_id=uuid.uuid4().hex, **extra)
        self.g.action(self.tokens[team, role], body)
        return body

    def profiles(self, team="BLUE"):
        for role in R.ROLES:
            self.act(role, "profile", team, choice=PROFILES[role][0][0])

    def propose(
        self,
        kind="INSTALL",
        team="BLUE",
        arch="INTEGRATED",
        launch="EARLY",
        shares=None,
        funding=None,
    ):
        c = self.g.c(team)
        target = (
            ((c["incident"] or {}).get("target") or c["missing"])
            if kind == "REPLACE"
            else c["replaced"]
        )
        if kind == "RETURN":
            target = None
        revenue = self.g.capacity_revenue(
            team,
            arch
            if kind == "INSTALL"
            else "MODULAR"
            if kind == "STANDARDIZE"
            else c["architecture"],
            target,
            c["growth"] or kind == "GROW",
        )
        weights = shares or {r: 20 for r in R.ROLES}
        amounts = {r: revenue * v // 100 for r, v in weights.items()}
        amounts[next(iter(amounts))] += revenue - sum(amounts.values())
        return self.act(
            "MOBI",
            "propose",
            team,
            kind=kind,
            architecture=arch,
            launch=launch,
            allocations=amounts,
            funding={r: round(v * 100) for r, v in (funding or {}).items()},
        )

    def accept(self, team="BLUE"):
        p = self.g.c(team)["proposal"]
        for role in p["required"]:
            self.act(role, "consent", team, choice="ACCEPT", revision=p["revision"])

    def install(self, team="BLUE", arch="INTEGRATED"):
        self.profiles(team)
        self.propose(team=team, arch=arch, funding={"MOBI": 6} if arch == "MODULAR" else {})
        self.accept(team)

    def event(self, name):
        self.g.state["phase"] = "APRIL"
        for i in range(200):
            self.g.state["seed"] = "scenario-%s" % i
            u = self.g.draw("BLUE", "external_event")
            lo, hi = 0, 0
            for candidate, weight in self.g.event_candidates("BLUE")[0]:
                hi = lo + weight
                if candidate == name:
                    break
                lo = hi
            else:
                self.fail("Événement incompatible avec ce scénario : " + name)
            if lo <= u < hi:
                self.g._event("BLUE")
                return
        self.fail("Graine de test introuvable")

    def test_initial_contract_is_free_and_unanimous(self):
        self.profiles()
        self.propose()
        p = self.g.c("BLUE")["proposal"]
        for role in R.ROLES[:-1]:
            self.act(role, "consent", choice="ACCEPT", revision=p["revision"])
        self.assertFalse(self.g.c("BLUE")["installed"])
        self.assertEqual(self.g.c("BLUE")["cash"]["AUTO"], INITIAL)
        self.act("FLEET", "consent", choice="REFUSE", revision=p["revision"])
        self.assertFalse(self.g.c("BLUE")["installed"])
        self.act("FLEET", "consent", choice="ACCEPT", revision=p["revision"])
        self.assertTrue(self.g.c("BLUE")["installed"])
        self.assertEqual(self.g.c("BLUE")["cash"]["AUTO"], INITIAL - 500)

    def test_replaced_company_does_not_supply_intervention_discounts(self):
        self.install(arch="INTEGRATED")
        c = self.g.c("BLUE")
        c["profiles"]["FLEET"] = "PREPARED"
        c["incident"] = {"kind": "AUDIT", "target": None}
        self.assertEqual(self.g.quote("BLUE", "REPAIR"), 500)
        c["replaced"] = "FLEET"
        self.assertEqual(self.g.quote("BLUE", "REPAIR"), 700)
        c["profiles"]["AUTO"] = "FLEXIBLE"
        c["replaced"] = "AUTO"
        c["profiles"]["FLEET"] = "LEAN"
        self.assertEqual(self.g.quote("BLUE", "REPAIR"), 700)

    def test_replaced_fleet_preparation_does_not_reduce_expansion_risk(self):
        self.install()
        c = self.g.c("BLUE")
        c.update(commissioned=True, replaced="FLEET", growth=True, growth_trial_pending=True)
        c["profiles"]["FLEET"] = "PREPARED"
        c["contract"]["allocations"]["ALT"] = c["contract"]["allocations"].pop("FLEET")
        with patch.object(self.g, "draw", return_value=0.2):
            self.g._settle("BLUE")
        expansion = [
            e
            for e in self.g.state["journal"]
            if e["event_type"] == "risk_drawn" and e["data"]["channel"] == "expansion"
        ][-1]
        self.assertEqual(expansion["data"]["probability"], 0.35)
        self.assertEqual(expansion["data"]["selected"], "OVERLOAD")

    def test_bot_does_not_finance_a_suspended_service_using_imagined_revenue(self):
        game = Game(new_state(code="BOTS", seed="bots"))
        game.step()
        shares = dict(MOBI=19, AUTO=20, BRAIN=20, GRID=20, FLEET=21)
        game.submit(
            "BLUE",
            "MOBI",
            dict(
                kind="INSTALL",
                architecture="INTEGRATED",
                launch="EARLY",
                allocations={r: v * 40 for r, v in shares.items()},
                funding={},
            ),
        )
        c = game.c("BLUE")
        self.assertTrue(c["installed"])
        c["operating"] = False
        cash = copy.deepcopy(c["cash"])
        game.submit(
            "BLUE",
            "MOBI",
            dict(
                kind="STANDARDIZE",
                allocations={r: v * 38 for r, v in shares.items()},
                funding={"MOBI": 800},
            ),
        )
        self.assertEqual(c["proposal"]["votes"]["MOBI"], "REFUSE")
        self.assertEqual(c["architecture"], "INTEGRATED")
        self.assertEqual(c["cash"], cash)

    def test_revisions_invalidate_answers_and_stale_vote(self):
        self.profiles()
        self.propose()
        self.act("FLEET", "consent", choice="ACCEPT", revision=1)
        self.propose(shares=dict(MOBI=16, AUTO=20, BRAIN=20, GRID=20, FLEET=24))
        self.assertEqual(self.g.c("BLUE")["proposal"]["votes"], {})
        with self.assertRaises(GameError):
            self.act("FLEET", "consent", choice="ACCEPT", revision=1)

    def test_no_cash_reset_and_no_repeated_installation(self):
        self.install()
        c = self.g.c("BLUE")
        c["commissioned"] = True
        cash = copy.deepcopy(c["cash"])
        self.g.step()
        self.assertEqual(c["cash"]["AUTO"], cash["AUTO"] + 800 - OPEX["AUTO"])
        self.assertEqual(c["architecture"], "INTEGRATED")
        self.assertEqual(
            len([row for row in self.g.state["ledger"] if row["kind"] == "INSTALLATION"]), 5
        )
        with self.assertRaises(GameError):
            self.propose()

    def test_nonagreement_defers_without_mandatory_losses(self):
        self.profiles()
        self.propose()
        self.g.step()
        self.assertFalse(self.g.c("BLUE")["installed"])
        self.assertEqual(self.g.c("BLUE")["cash"]["AUTO"], INITIAL)
        self.assertEqual(self.g.c("BLUE")["proposal"]["status"], "EXPIRED")
        self.assertEqual(self.g.c("BLUE")["created"], 0)

    def test_one_refusing_group_never_blocks_other_territories(self):
        self.install("BLUE")
        self.g.c("BLUE")["commissioned"] = True
        self.profiles("GREEN")
        # Isoler le calendrier des risques : aucun incident pour le service lancé.
        with patch.object(self.g, "draw", return_value=0.1):
            for quarter, following in enumerate(["APRIL", "JULY", "OCTOBER", "FINAL"], 1):
                if quarter > 1:
                    self.propose(kind="REVISE", team="BLUE")
                    self.accept("BLUE")
                self.propose(team="GREEN")
                p = self.g.c("GREEN")["proposal"]
                for role in R.ROLES:
                    self.act(
                        role,
                        "consent",
                        "GREEN",
                        choice="REFUSE" if role == "FLEET" else "ACCEPT",
                        revision=p["revision"],
                    )
                self.g.step()
                self.assertEqual(self.g.state["phase"], following)
                self.assertEqual(p["status"], "EXPIRED")
                for team in ("BLUE", "GREEN"):
                    self.assertEqual(len(self.g.c(team)["settlements"]), quarter)
                self.assertEqual(self.g.c("BLUE")["settlements"][-1]["revenue"], 4000)
                self.assertEqual(self.g.c("GREEN")["settlements"][-1]["revenue"], 0)
                self.assertIn("Sans accord", self.g.c("GREEN")["settlements"][-1]["message"])
                for role in R.ROLES:
                    self.assertEqual(self.g.c("GREEN")["cash"][role], INITIAL)
        self.assertEqual(self.g.c("BLUE")["revenue"], 16000)
        self.assertFalse(self.g.c("GREEN")["installed"])
        self.assertEqual(self.g.c("GREEN")["expenses"], 0)

    def test_late_agreement_starts_service_without_recovering_missed_quarter(self):
        self.g.step()
        self.install("GREEN")
        self.g.c("GREEN")["commissioned"] = True
        with patch.object(self.g, "draw", return_value=0.1):
            self.g.step()
        results = self.g.player_view(self.tokens["GREEN", "AUTO"])["team"]["settlements"]
        self.assertEqual([s["revenue"] for s in results], [0, 4000])
        self.assertIn("Sans accord", results[0]["message"])
        self.assertNotIn("cash", results[0])
        self.assertEqual(self.g.c("GREEN")["revenue"], 4000)

    def test_repeat_request_and_atomic_rollback(self):
        body = self.act("AUTO", "profile", choice="FLEXIBLE")
        count = len(self.g.state["journal"])
        self.g.action(self.tokens["BLUE", "AUTO"], body)
        self.assertEqual(len(self.g.state["journal"]), count)
        with self.assertRaises(GameError):
            self.g.action(self.tokens["BLUE", "AUTO"], dict(body, choice="DEDICATED"))
        self.profiles()
        before = copy.deepcopy(self.g.state)
        with self.assertRaises(GameError):
            self.propose(funding={"MOBI": 1})
        # Le seul changement tolere est la date de derniere connexion.
        for p in self.g.state["players"].values():
            p["seen"] = before["players"][p["id"]]["seen"]
        self.assertEqual(self.g.state, before)

    def test_failed_persistence_rolls_back_commit(self):
        self.profiles()
        self.propose()
        for role in R.ROLES[:-1]:
            self.act(role, "consent", choice="ACCEPT", revision=1)
        before = copy.deepcopy(self.g.c("BLUE"))

        def fail(_):
            raise OSError("disk full")

        self.g._on_change = fail
        with self.assertRaises(OSError):
            self.act("FLEET", "consent", choice="ACCEPT", revision=1)
        self.assertEqual(self.g.c("BLUE"), before)

    def test_private_votes_costs_and_future_events_not_in_views(self):
        self.profiles()
        self.propose()
        self.act("FLEET", "consent", choice="REFUSE", revision=1)
        own = self.g.player_view(self.tokens["BLUE", "FLEET"])
        other = self.g.player_view(self.tokens["BLUE", "MOBI"])
        host = self.g.host_view()
        self.assertEqual(own["team"]["proposal"]["mine"], "REFUSE")
        self.assertIsNone(other["team"]["proposal"]["mine"])
        self.assertNotIn("votes", host["teams"]["BLUE"]["proposal"])
        self.assertIsNone(other["team"]["cash"])
        self.assertNotIn("seed", other)
        self.assertNotIn("journal", other)
        self.assertNotIn("power", other["me"])
        self.assertNotIn("rounds", other["team"])
        self.assertEqual(other["team"]["options"][0]["key"], "INSTALL")
        with self.assertRaises(GameError):
            self.g.export()

    def test_local_draws_are_stable_and_independent_of_action_count(self):
        self.install()
        other = Game(copy.deepcopy(self.g.state))
        self.act("FLEET", "claim", text="Une condition à discuter")
        self.g.step()
        other.step()
        e1 = [e["data"] for e in self.g.state["journal"] if e["event_type"] == "event_drawn"]
        e2 = [e["data"] for e in other.state["journal"] if e["event_type"] == "event_drawn"]
        self.assertEqual(e1, e2)
        self.assertNotEqual(
            self.g.draw("BLUE", "external_event"), self.g.draw("GREEN", "external_event")
        )

    def test_suspension_does_not_repair_incident_for_free(self):
        self.install()
        self.event("INFRA")
        self.propose(kind="PAUSE")
        self.accept()
        self.assertIsNotNone(self.g.c("BLUE")["incident"])
        self.assertNotIn("RESUME", self.g.available("BLUE"))
        self.assertIn("REPAIR", self.g.available("BLUE"))

    def test_investments_change_repair_cost_and_replacement_delay(self):
        self.install()
        self.event("INFRA")
        self.assertEqual(self.g.quote("BLUE", "REPAIR"), 700)
        self.g.c("BLUE")["architecture"] = "MODULAR"
        self.assertEqual(self.g.quote("BLUE", "REPAIR"), 300)
        self.g.c("BLUE")["architecture"] = "INTEGRATED"
        self.propose(
            kind="REPLACE",
            shares=dict(MOBI=20, AUTO=20, BRAIN=20, FLEET=20, ALT=20),
            funding={"MOBI": 9},
        )
        self.accept()
        self.assertEqual(self.g.c("BLUE")["replaced"], "GRID")
        self.assertTrue(self.g.player_view(self.tokens["BLUE", "GRID"])["me"]["outside_position"])
        self.g.step()
        self.assertEqual(self.g.c("BLUE")["settlements"][-1]["revenue"], 0)
        self.act("GRID", "return_request")
        self.assertIn("RETURN", self.g.available("BLUE"))

    def test_exclusivity_and_outside_offer_are_binding(self):
        self.profiles()
        self.act("BRAIN", "profile", choice="COMMITTED")
        self.propose()
        self.accept()
        self.assertNotIn("PARTNER", dict(self.g.event_candidates("BLUE")[0]))
        self.assertFalse(self.g.player_view(self.tokens["BLUE", "BRAIN"])["me"]["can_leave"])
        with self.assertRaises(GameError):
            self.act("BRAIN", "leave")
        self.assertIsNone(self.g.player_view(self.tokens["BLUE", "MOBI"])["me"]["offer"])

    def test_late_start_keeps_commissioning_risk(self):
        self.g.step()
        self.install()
        self.g.step()
        self.assertTrue(self.g.c("BLUE")["commissioned"])
        self.assertTrue(
            any(
                e["event_type"] == "risk_drawn" and e["data"]["channel"] == "commissioning"
                for e in self.g.state["journal"]
            )
        )

    def test_growth_is_unavailable_without_opportunity_then_persists(self):
        self.install()
        self.assertNotIn("GROW", self.g.available("BLUE"))
        self.event("DEMAND")
        self.propose(kind="GROW", funding={"MOBI": 6})
        self.accept()
        self.assertTrue(self.g.c("BLUE")["growth"])
        self.assertNotIn("GROW", self.g.available("BLUE"))
        self.g.step()
        self.assertTrue(self.g.c("BLUE")["growth"])

    def test_ledger_reconstructs_balances_and_export_has_no_tokens(self):
        self.install()
        for _ in range(4):
            self.g.step()
        for t in self.g.active_teams():
            for role in R.ROLES:
                balance = INITIAL + sum(
                    row["amount"]
                    for row in self.g.state["ledger"]
                    if row["ecosystem_id"] == t and row["role"] == role
                )
                self.assertEqual(balance, self.g.c(t)["cash"][role])
            c = self.g.c(t)
            self.assertEqual(c["revenue"] - c["expenses"], c["created"])
        data = self.g.export()
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertEqual(len(archive.namelist()), 8)
            journal = archive.read("journal.jsonl").decode()
            for token in self.tokens.values():
                self.assertNotIn(token, journal)
            self.assertIn('"state_after"', journal)
            self.assertIn('"node_id"', journal)

    def test_calendar_no_rewind_and_roles_frozen(self):
        with self.assertRaises(GameError):
            self.g.step(-1)
        with self.assertRaises(GameError):
            self.g.reassign(self.tokens["BLUE", "MOBI"], "GREEN", "GRID")

    def test_superseding_a_proposal_does_not_reveal_partner_votes(self):
        self.profiles()
        self.propose()
        self.act("FLEET", "consent", choice="REFUSE", revision=1)
        self.act("MOBI", "profile", choice="SUPPORT")
        public = self.g.player_view(self.tokens["BLUE", "MOBI"])["team"]["proposal"]
        self.assertEqual(public["status"], "SUPERSEDED")
        self.assertNotIn("votes", public)
        self.assertNotIn("votes", self.g.host_view()["teams"]["BLUE"]["proposal"])

    def test_repair_clears_current_alert_and_preserves_its_history(self):
        self.install()
        self.event("INFRA")
        self.propose(kind="REPAIR", funding={"MOBI": 7})
        self.accept()
        view = self.g.player_view(self.tokens["BLUE", "GRID"])
        self.assertIsNone(view["team"]["news"])
        self.assertEqual(view["team"]["node"], "OPERATING")
        self.assertTrue(any("recharge" in h["text"] for h in view["team"]["history"]))
        self.assertEqual(self.g.c("BLUE")["intervention_delay"], "APRIL")

    def test_delayed_foundation_is_not_described_as_running_fleet(self):
        self.g.step()
        team = self.g.player_view(self.tokens["BLUE", "AUTO"])["team"]
        self.assertEqual(team["node"], "FOUNDING")
        self.assertIn("mandat", team["news"]["title"])

    def test_standardizing_a_paused_service_does_not_restart_it(self):
        self.install()
        self.propose(kind="PAUSE")
        self.accept()
        self.propose(kind="STANDARDIZE", funding={"MOBI": 8})
        self.accept()
        self.assertEqual(self.g.c("BLUE")["architecture"], "MODULAR")
        self.assertFalse(self.g.c("BLUE")["operating"])

    def test_failed_commissioning_does_not_double_pay_outside_capacity(self):
        self.install()
        for i in range(100):
            self.g.state["seed"] = "failed-launch-%d" % i
            if self.g.draw("BLUE", "commissioning") < 0.45:
                break
        before = copy.deepcopy(self.g.c("BLUE")["cash"])
        self.g._settle("BLUE")
        for r in R.ROLES:
            self.assertEqual(self.g.c("BLUE")["cash"][r], before[r] - OPEX[r])
        self.assertEqual(self.g.c("BLUE")["settlements"][-1]["revenue"], 0)
        self.assertFalse(
            any(
                t["kind"] == "OUTSIDE"
                for t in self.g.state["ledger"]
                if t["ecosystem_id"] == "BLUE"
            )
        )
        size = len(self.g.state["ledger"])
        self.g._settle("BLUE")
        self.assertEqual(len(self.g.state["ledger"]), size)

    def test_published_capacity_revenue_includes_the_offered_architecture(self):
        self.profiles()
        self.act("MOBI", "profile", choice="SUPPORT")
        self.act("BRAIN", "profile", choice="COMMITTED")
        self.propose(arch="MODULAR", funding={"MOBI": 6})
        p = self.g.player_view(self.tokens["BLUE", "FLEET"])["team"]["proposal"]
        self.assertEqual(p["full_capacity_revenue"], 4200)
        self.assertNotIn("votes", p)

    def test_reconfigurable_vehicle_benefit_requires_paid_installation(self):
        self.profiles()
        self.act("AUTO", "profile", choice="FLEXIBLE")
        before = self.g.c("BLUE")["cash"]["AUTO"]
        self.g.step()
        self.assertEqual(self.g.c("BLUE")["cash"]["AUTO"] - before, 0)
        self.propose()
        self.accept()
        self.propose(kind="PAUSE")
        self.accept()
        before = self.g.c("BLUE")["cash"]["AUTO"]
        self.g.step()
        self.assertEqual(self.g.c("BLUE")["cash"]["AUTO"] - before, 400)

    def test_private_cost_changes_actual_expense_without_leaking_other_costs(self):
        self.install()
        self.event("PRIVATE_COST")
        c = self.g.c("BLUE")
        role = next(iter(c["cost_shocks"]))
        shock = c["cost_shocks"][role]
        own = self.g.player_view(self.tokens["BLUE", role])
        self.assertEqual(own["me"]["operating_cost"], OPEX[role] + shock["increase"])
        for other in R.ROLES:
            view = self.g.player_view(self.tokens["BLUE", other])
            self.assertNotIn("cost_shocks", view["team"])
            if other != role:
                self.assertIsNone(view["me"]["private_shock"])
        self.assertNotIn("cost_shocks", self.g.host_view()["teams"]["BLUE"])
        c["commissioned"] = True
        self.propose(kind="REVISE")
        self.accept()
        before = c["cash"][role]
        self.g._settle("BLUE")
        self.assertEqual(c["cash"][role] - before, 800 - OPEX[role] - shock["increase"])
        self.assertEqual(c["created"], c["revenue"] - c["expenses"])
        public = self.g.player_view(self.tokens["BLUE", "MOBI"])["team"]
        self.assertIsNone(public["created"])
        self.assertIsNone(public["expenses"])
        self.assertNotIn("created", public["settlements"][-1])

    def test_cost_shock_allows_request_withdrawal_replacement_and_return(self):
        self.install()
        self.event("PRIVATE_COST")
        c = self.g.c("BLUE")
        role = next(iter(c["cost_shocks"]))
        self.act(role, "renegotiate")
        self.assertIn(
            role, self.g.player_view(self.tokens["BLUE", "MOBI"])["team"]["renegotiation_requests"]
        )
        self.assertEqual(c["contract"]["revision"], 1)
        self.act(role, "withdraw")
        self.assertEqual(c["missing"], role)
        self.assertFalse(c["operating"])
        self.assertFalse(self.g.player_view(self.tokens["BLUE", role])["me"]["can_withdraw"])
        self.assertIn("REPLACE", self.g.available("BLUE"))
        before = c["cash"][role]
        self.g._settle("BLUE")
        self.assertEqual(c["cash"][role] - before, 0)
        self.act(role, "return_request")
        self.propose(kind="RETURN")
        self.accept()
        self.assertIsNone(c["missing"])
        self.assertTrue(c["operating"])
        self.assertEqual(c["renegotiation_requests"], {})
        self.assertGreater(self.g.operating_cost("BLUE", role), OPEX[role])

    def test_nonaffected_partner_cannot_withdraw_without_a_mobility_right(self):
        self.install()
        self.event("PRIVATE_COST")
        role = next(r for r in R.ROLES if r not in self.g.c("BLUE")["cost_shocks"])
        with self.assertRaises(GameError):
            self.act(role, "withdraw")

    def test_public_price_shock_changes_proposals_and_settlement_not_percentages(self):
        self.install()
        self.event("PRICE_DROP")
        c = self.g.c("BLUE")
        decrease = -c["revenue_adjustment"]
        self.assertIn(decrease, [600, 1000, 1400])
        self.assertEqual(self.g.gross("BLUE"), 4000 - decrease)
        self.assertEqual(c["contract"]["allocations"], {r: 800 for r in R.ROLES})
        self.assertEqual(
            self.g.player_view(self.tokens["BLUE", "MOBI"])["team"]["node"], "REVENUE_PRESSURE"
        )
        self.propose(kind="REVISE")
        self.assertEqual(c["proposal"]["full_capacity_revenue"], 4000 - decrease)
        self.accept()
        c["commissioned"] = True
        self.g._settle("BLUE")
        self.assertEqual(c["settlements"][-1]["revenue"], 4000 - decrease)
        self.assertEqual(c["revenue"] - c["expenses"], c["created"])
        self.assertNotIn("PRICE_DROP", dict(self.g.event_candidates("BLUE")[0]))

    def test_active_territory_cannot_draw_two_consecutive_quiet_periods(self):
        self.install()
        c = self.g.c("BLUE")
        c["commissioned"] = True
        with patch.object(self.g, "draw", return_value=0):
            self.g.step()
            self.assertEqual(c["last_draw"]["kind"], "ORDINARY")
            self.g.step()
            self.assertNotEqual(c["last_draw"]["kind"], "ORDINARY")
        event = [
            e
            for e in self.g.state["journal"]
            if e["event_type"] == "event_drawn" and e["ecosystem_id"] == "BLUE"
        ][-1]
        self.assertIn("ORDINARY", event["data"]["excluded"])
        self.assertEqual(event["rules_version"], "campaign-3.0")

    def test_old_training_can_resume_without_rewriting_its_draws(self):
        self.install()
        self.event("ORDINARY")
        raw = copy.deepcopy(self.g.state)
        for t in raw["teams"].values():
            for key in [
                "cost_shocks",
                "revenue_adjustment",
                "quiet_streak",
                "renegotiation_requests",
            ]:
                t["campaign"].pop(key, None)
        old_journal = copy.deepcopy(raw["journal"])
        resumed = Game(raw)
        self.assertEqual(resumed.state["journal"], old_journal)
        view = resumed.player_view(self.tokens["BLUE", "FLEET"])
        self.assertIsNone(view["me"]["private_shock"])
        self.assertEqual(view["me"]["operating_cost"], OPEX["FLEET"])
        self.assertNotIn("ORDINARY", dict(resumed.event_candidates("BLUE")[0]))

    def test_credit_amounts_and_investments_accept_cents_without_percentages(self):
        self.profiles()
        amounts = dict(MOBI=801, AUTO=802, BRAIN=803, GRID=804, FLEET=590)
        self.act(
            "MOBI",
            "propose",
            kind="INSTALL",
            architecture="MODULAR",
            launch="EARLY",
            allocations=amounts,
            funding=dict(MOBI=301, AUTO=299),
        )
        self.accept()
        c = self.g.c("BLUE")
        self.assertEqual(c["cash"]["AUTO"], INITIAL - 500 - 299)
        self.assertEqual(c["contract"]["allocations"], amounts)
        self.assertNotIn("shares", c["contract"])
        c["commissioned"] = True
        before = copy.deepcopy(c["cash"])
        self.g._settle("BLUE")
        for role, amount in amounts.items():
            self.assertEqual(c["cash"][role] - before[role], amount - OPEX[role])
        self.assertEqual(c["revenue"], 3800)

    def test_refused_revision_never_falls_back_to_signed_contract(self):
        self.install()
        self.propose(kind="REVISE")
        p = self.g.c("BLUE")["proposal"]
        self.act("AUTO", "consent", choice="REFUSE", revision=p["revision"])
        before = copy.deepcopy(self.g.c("BLUE")["cash"])
        size = len(self.g.state["ledger"])
        self.g._settle("BLUE")
        self.assertEqual(self.g.c("BLUE")["cash"], before)
        self.assertEqual(len(self.g.state["ledger"]), size)
        self.assertEqual(self.g.c("BLUE")["settlements"][-1]["revenue"], 0)
        self.assertFalse(self.g.c("BLUE")["settlements"][-1]["agreement"])

    def test_new_quarter_requires_fresh_agreement_even_without_proposal(self):
        self.install()
        self.g.c("BLUE")["commissioned"] = True
        with patch.object(self.g, "draw", return_value=0.1):
            self.g.step()
        before = copy.deepcopy(self.g.c("BLUE")["cash"])
        self.assertFalse(self.g.team_view("BLUE")["agreement_current"])
        self.g._settle("BLUE")
        self.assertEqual(self.g.c("BLUE")["cash"], before)
        self.assertEqual(self.g.c("BLUE")["settlements"][-1]["revenue"], 0)

    def test_old_percentage_save_converts_live_contract_without_rewriting_journal(self):
        self.install()
        raw = copy.deepcopy(self.g.state)
        c = raw["teams"]["BLUE"]["campaign"]
        for key in ("contract", "proposal"):
            c[key].pop("allocations")
            c[key]["shares"] = {r: 20 for r in R.ROLES}
        raw["rules_version"] = "campaign-2.1"
        journal = copy.deepcopy(raw["journal"])
        resumed = Game(raw)
        self.assertEqual(resumed.state["journal"], journal)
        self.assertEqual(resumed.c("BLUE")["contract"]["allocations"], {r: 800 for r in R.ROLES})
        self.assertNotIn("shares", resumed.team_view("BLUE")["contract"])
        resumed.state["phase"] = "FINAL"
        with zipfile.ZipFile(io.BytesIO(resumed.export())) as archive:
            import json

            metadata = json.loads(archive.read("metadata.json"))
        self.assertIn("campaign-2.1", metadata["rule_sets"])

    def test_conditions_messages_and_explanations_are_shared_and_idempotent(self):
        body = self.act(
            "AUTO",
            "negotiate",
            minimum=875,
            maximum=125,
            text="Je finance si mon investissement est couvert.",
        )
        self.g.action(self.tokens["BLUE", "AUTO"], body)
        self.act("GRID", "discuss", target="AUTO", text="Et si je finance 1 crédit ?")
        self.profiles()
        self.propose()
        self.act("AUTO", "consent", choice="REFUSE", revision=1, reason="Il me faut 8,75 crédits.")
        view = self.g.player_view(self.tokens["BLUE", "MOBI"])["team"]
        self.assertEqual(view["positions"]["AUTO"]["minimum"], 875)
        self.assertEqual(len(view["discussion"]), 3)
        self.assertEqual(view["discussion"][1]["target"], "AUTO")
        self.assertEqual(view["discussion"][-1]["choice"], "REFUSE")
        self.assertFalse(self.g.c("BLUE")["installed"])
        with self.assertRaises(GameError):
            self.act("GRID", "discuss", target="INVALID", text="Message")
        with self.assertRaises(GameError):
            self.act("AUTO", "negotiate", minimum=-1, maximum=0, text="Message")


if __name__ == "__main__":
    unittest.main()
