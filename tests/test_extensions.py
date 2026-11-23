# -*- coding: utf-8 -*-
"""Verifie les mecaniques ajoutees : marche, chocs, pouvoirs, badges.

Lancement :  python tests/test_extensions.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.dont_write_bytecode = True

from eco import rules as R
from eco import engine
from eco.engine import Game, GameError, new_state, score_round3, round3_value, adaptation_cost

FAILS = []


def check(label, got, want):
    if got != want:
        FAILS.append("%s : obtenu %r, attendu %r" % (label, got, want))
        print("  ECHEC  %-58s %r != %r" % (label, got, want))
    else:
        print("  ok     %-58s %r" % (label, got))


def ok(label, cond):
    check(label, bool(cond), True)


def raises(label, fn, *a, **kw):
    """Verifie qu'une regle est bien refusee, et renvoie le message."""
    try:
        fn(*a, **kw)
    except GameError as exc:
        print("  ok     %-58s refuse" % label)
        return str(exc)
    FAILS.append("%s : aurait du etre refuse" % label)
    print("  ECHEC  %-58s accepte a tort" % label)
    return ""


# ---------------------------------------------------------------------------
# Fabrique de parties
# ---------------------------------------------------------------------------


def build(team_count=3):
    """Partie complete : un joueur par siege, aucun bot."""
    g = Game(new_state(code="TEST", team_count=team_count))
    g.state["auto_teams"] = False
    tok = {}
    for t in R.TEAMS[:team_count]:
        for role in R.ROLES:
            token = "tok-%s-%s" % (t, role)
            g.state["players"][token] = {
                "id": token,
                "name": "%s-%s" % (role, t[0]),
                "team": t,
                "role": role,
                "joined": 0,
                "seen": 0,
            }
            tok[(t, role)] = token
    return g, tok


def play_r2(g, tok, contract=None):
    """Deroule les rounds 1 et 2 jusqu'a R2_RESULTS, tout le monde JOIN."""
    contract = contract or {"MOBI": 8, "AUTO": 8, "BRAIN": 8, "GRID": 8, "FLEET": 8}
    for phase in ("R1_NEGO", "R1_DECIDE"):
        g.set_phase(phase)
    for (_t, _role), token in tok.items():
        g.decide(token, "JOIN")
    g.set_phase("R1_RESULTS")
    g.set_phase("R2_NEGO")
    for t in g.active_teams():
        g.submit_contract(tok[(t, "MOBI")], contract)
    g.set_phase("R2_DECIDE")
    for (_t, _role), token in tok.items():
        g.decide(token, "JOIN")
    g.set_phase("R2_RESULTS")


# ---------------------------------------------------------------------------
# 1. Marche des ecosystemes
# ---------------------------------------------------------------------------

print("\n1. MARCHE - un BRAIN change d'ecosysteme (echange croise)")
g, tok = build(3)
play_r2(g, tok)
g.set_phase("MARKET")

g.make_offer(tok[("BLUE", "MOBI")], "GREEN", 5)
g.make_offer(tok[("GREEN", "MOBI")], "BLUE", 3)
g.market_decide(tok[("GREEN", "BRAIN")], "BLUE")
g.market_decide(tok[("BLUE", "BRAIN")], "GREEN")
g.market_decide(tok[("RED", "BRAIN")], "STAY")
g.set_phase("R3_ARCH")

mk = g.state["market"]
check("deux transferts croises appliques", len(mk["moves"]), 2)
check("aucune acceptation annulee", mk["voided"], [])
check(
    "le BRAIN de GREEN est passe chez BLUE",
    g.state["players"][tok[("GREEN", "BRAIN")]]["team"],
    "BLUE",
)
check(
    "son ecosysteme d'origine est memorise",
    g.state["players"][tok[("GREEN", "BRAIN")]]["origin_team"],
    "GREEN",
)
check("BLUE a paye 5 points a son nouveau BRAIN", g.state["teams"]["BLUE"]["adjust"]["MOBI"], -5)
check(
    "le BRAIN arrive touche 5 moins le cout de changement",
    g.state["teams"]["BLUE"]["adjust"]["BRAIN"],
    5 - R.SWITCH_COST,
)
check("BLUE est marque comme ayant perdu son BRAIN", g.state["teams"]["BLUE"]["lost_brain"], True)
check("RED n'a pas bouge", g.state["teams"]["RED"]["lost_brain"], False)

print("\n   les scores des rounds 1 et 2 restent acquis a l'ecosysteme d'origine")
g.set_phase("FINAL")
players, eco = g.totals()
moved = next(r for r in players if r["role"] == "BRAIN" and r["origin_team"] == "GREEN")
check("le BRAIN transfere garde ses points de R1", moved["rounds"]["1"], 12)
check("il touche l'ajustement du marche", moved["adjust"], 3)

print("\n1b. MARCHE - un depart sans contrepartie est annule")
g, tok = build(3)
play_r2(g, tok)
g.set_phase("MARKET")
g.make_offer(tok[("BLUE", "MOBI")], "GREEN", 4)
g.market_decide(tok[("GREEN", "BRAIN")], "BLUE")  # BLUE garde son propre BRAIN
g.set_phase("R3_ARCH")
check("aucun transfert : le siege vise est occupe", g.state["market"]["moves"], [])
check("l'acceptation est signalee comme annulee", g.state["market"]["voided"], ["GREEN"])
check("GREEN garde donc son BRAIN", g.state["teams"]["GREEN"]["lost_brain"], False)

print("\n1d. MARCHE - deux BRAIN vises par le meme ecosysteme")
g, tok = build(3)
play_r2(g, tok)
g.set_phase("MARKET")
# BLUE mise sur les deux BRAIN concurrents ; les deux acceptent
g.make_offer(tok[("BLUE", "MOBI")], "GREEN", 2)
g.make_offer(tok[("BLUE", "MOBI")], "RED", 5)
g.market_decide(tok[("GREEN", "BRAIN")], "BLUE")
g.market_decide(tok[("RED", "BRAIN")], "BLUE")
# le siege de BLUE doit lui-meme se liberer
g.make_offer(tok[("RED", "MOBI")], "BLUE", 3)
g.market_decide(tok[("BLUE", "BRAIN")], "RED")
g.set_phase("R3_ARCH")
check(
    "un seul transfert entrant chez BLUE",
    [m["from"] for m in g.state["market"]["moves"] if m["to"] == "BLUE"],
    ["RED"],
)
check("l'offre la plus elevee l'emporte", g.state["players"][tok[("RED", "BRAIN")]]["team"], "BLUE")
check("l'autre BRAIN reste chez lui", g.state["players"][tok[("GREEN", "BRAIN")]]["team"], "GREEN")
check("son acceptation est signalee annulee", g.state["market"]["voided"], ["GREEN"])


print("\n1c. MARCHE - regles d'acces")
g, tok = build(3)
play_r2(g, tok)
raises("offre hors phase de marche", g.make_offer, tok[("BLUE", "MOBI")], "GREEN", 3)
g.set_phase("MARKET")
raises("seul BRAIN change d'ecosysteme", g.market_decide, tok[("BLUE", "GRID")], "STAY")
raises("seul MOBI fait une offre", g.make_offer, tok[("BLUE", "AUTO")], "GREEN", 3)
raises("on ne recrute pas son propre BRAIN", g.make_offer, tok[("BLUE", "MOBI")], "BLUE", 3)
raises("offre au-dessus du plafond", g.make_offer, tok[("BLUE", "MOBI")], "GREEN", R.OFFER_MAX + 1)
raises(
    "BRAIN ne peut accepter une offre inexistante", g.market_decide, tok[("RED", "BRAIN")], "BLUE"
)

print("\n   confidentialite des offres")
g.make_offer(tok[("BLUE", "MOBI")], "GREEN", 4)
v_green = g.player_view(tok[("GREEN", "BRAIN")])
v_red = g.player_view(tok[("RED", "BRAIN")])
v_grid = g.player_view(tok[("GREEN", "GRID")])
check("le BRAIN cible voit l'offre", v_green["market"]["received"], {"BLUE": 4})
check("un autre BRAIN ne la voit pas", v_red["market"]["received"], {})
check("les autres roles ne voient aucune offre", v_grid["market"]["received"], {})
check(
    "le tableau de bord ne montre que le nombre d'offres", g.host_view()["market"]["offer_count"], 1
)

print("\n   un BRAIN ne change qu'une fois")
g.make_offer(tok[("GREEN", "MOBI")], "BLUE", 4)
g.market_decide(tok[("GREEN", "BRAIN")], "BLUE")
g.market_decide(tok[("BLUE", "BRAIN")], "GREEN")
g.set_phase("R3_ARCH")
check("le marche est clos", g.state["market"]["resolved"], True)
raises("plus aucune decision apres cloture", g.market_decide, tok[("GREEN", "BRAIN")], "STAY")
before = dict(g.state["teams"]["BLUE"]["adjust"])
g._resolve_market()
check("une seconde resolution ne rejoue rien", g.state["teams"]["BLUE"]["adjust"], before)


# ---------------------------------------------------------------------------
# 2. Exclusivite
# ---------------------------------------------------------------------------

print("\n2. EXCLUSIVITE")
g, tok = build(3)
play_r2(g, tok)
g.set_phase("MARKET")

g.use_power(tok[("BLUE", "BRAIN")])
check("la proposition est en attente", g.state["teams"]["BLUE"]["pending_exclusive"], True)
check("le pouvoir n'est pas encore consomme", g.state["teams"]["BLUE"]["powers"].get("BRAIN"), None)

g.respond_exclusivity(tok[("BLUE", "MOBI")], False)
check("apres refus, BRAIN peut reproposer", g.power_available("BLUE", "BRAIN")[0], True)

g.use_power(tok[("BLUE", "BRAIN")])
g.respond_exclusivity(tok[("BLUE", "MOBI")], True)
bonus = R.POWERS["BRAIN"]["max"]
check("BRAIN gagne %d points" % bonus, g.state["teams"]["BLUE"]["adjust"]["BRAIN"], bonus)
check("MOBI les paie sur sa part", g.state["teams"]["BLUE"]["adjust"]["MOBI"], -bonus)
check("l'ecosysteme est verrouille", g.state["teams"]["BLUE"]["exclusive"], True)

g.make_offer(tok[("GREEN", "MOBI")], "BLUE", R.OFFER_MAX)
raises("un BRAIN exclusif refuse toute offre", g.market_decide, tok[("BLUE", "BRAIN")], "GREEN")
g.set_phase("R3_ARCH")
check("il est donc reste", g.state["teams"]["BLUE"]["lost_brain"], False)
raises("l'exclusivite ne se rejoue pas", g.respond_exclusivity, tok[("BLUE", "MOBI")], True)


# ---------------------------------------------------------------------------
# 3. Les trois chocs
# ---------------------------------------------------------------------------

print("\n3. CHOCS - valeur du service")
check(
    "AI_FAILURE proprietaire, BRAIN conserve", round3_value("PROPRIETARY", "KEEP", "AI_FAILURE"), 46
)
check(
    "AI_FAILURE proprietaire, BRAIN remplace (retard 12)",
    round3_value("PROPRIETARY", "REPLACE", "AI_FAILURE"),
    34,
)
check(
    "AI_FAILURE modulaire, BRAIN remplace (aucun retard)",
    round3_value("MODULAR", "REPLACE", "AI_FAILURE"),
    40,
)
check(
    "INFRA_FAILURE proprietaire, GRID remplace",
    round3_value("PROPRIETARY", "REPLACE", "INFRA_FAILURE"),
    34,
)
check(
    "REGULATION proprietaire, mise en conformite",
    round3_value("PROPRIETARY", "KEEP", "REGULATION"),
    34,
)
check("REGULATION modulaire, mise en conformite", round3_value("MODULAR", "KEEP", "REGULATION"), 40)
check("abandon : aucune valeur", round3_value("PROPRIETARY", "ABANDON", "REGULATION"), 0)

print("\n   couts d'adaptation")
check(
    "AI_FAILURE remplacement proprietaire",
    adaptation_cost("PROPRIETARY", "AI_FAILURE", "REPLACE"),
    8,
)
check("AI_FAILURE remplacement modulaire", adaptation_cost("MODULAR", "AI_FAILURE", "REPLACE"), 2)
check(
    "AI_FAILURE conservation : rien de collectif",
    adaptation_cost("PROPRIETARY", "AI_FAILURE", "KEEP"),
    0,
)
check("INFRA_FAILURE proprietaire", adaptation_cost("PROPRIETARY", "INFRA_FAILURE", "REPLACE"), 10)
check("INFRA_FAILURE modulaire", adaptation_cost("MODULAR", "INFRA_FAILURE", "REPLACE"), 4)
check("REGULATION proprietaire", adaptation_cost("PROPRIETARY", "REGULATION", "KEEP"), 8)
check("REGULATION modulaire", adaptation_cost("MODULAR", "REGULATION", "KEEP"), 3)
check(
    "STANDARD READY retire 2 points",
    adaptation_cost("MODULAR", "REGULATION", "KEEP", discount=2),
    1,
)


def r3(arch, resolution, shock, revenues, standard=None, integration=None):
    """Round 3 reussi : tout le monde JOIN, contrat valide."""
    sp = engine.shock_spec(shock)
    parts = [r for r in R.ROLES if not (resolution == "REPLACE" and r == sp["target"])]
    rd = {
        "architecture": arch,
        "resolution": resolution,
        "shock": shock,
        "standard": standard or {r: 0 for r in R.ROLES},
        "integration": integration or {r: 0 for r in R.ROLES},
        "adapt_cost": sum((integration or {}).values()),
        "contract": revenues,
        "decisions": {r: "JOIN" for r in parts},
    }
    return score_round3(rd)


print("\n   choc A : AI FAILURE")
std = {"MOBI": 6, "AUTO": 0, "BRAIN": 0, "GRID": 0, "FLEET": 0}
a = r3(
    "PROPRIETARY",
    "KEEP",
    "AI_FAILURE",
    {"MOBI": 10, "AUTO": 10, "BRAIN": 10, "GRID": 8, "FLEET": 8},
)
check("PROPRIETARY + KEEP : 46 - (21+6)", a["ecosystem"], 19)
ok("service lance", a["success"])
b = r3(
    "MODULAR",
    "REPLACE",
    "AI_FAILURE",
    {"MOBI": 8, "AUTO": 8, "GRID": 8, "FLEET": 8, "ALT_AI": 8},
    standard=std,
    integration={"MOBI": 2},
)
check("MODULAR + REPLACE : 40 - 17 - 4 - 2 - 6", b["ecosystem"], 11)
check("BRAIN evince reprend son exterieur", b["scores"]["BRAIN"], R.RESOURCES + R.OUTSIDE["BRAIN"])
check("BRAIN n'est pas compte comme participant", b["joined"]["BRAIN"], False)

print("\n   choc B : INFRA FAILURE")
c = r3(
    "PROPRIETARY",
    "REPLACE",
    "INFRA_FAILURE",
    {"MOBI": 6, "AUTO": 6, "BRAIN": 6, "FLEET": 6, "ALT_AI": 10},
    integration={"MOBI": 10},
)
check("PROPRIETARY : 34 - 17 - 4 - 10", c["ecosystem"], 3)
check("GRID est le role remplace", c["joined"]["GRID"], False)
check("GRID reprend son exterieur", c["scores"]["GRID"], R.RESOURCES + R.OUTSIDE["GRID"])
d = r3(
    "MODULAR",
    "REPLACE",
    "INFRA_FAILURE",
    {"MOBI": 8, "AUTO": 8, "BRAIN": 8, "FLEET": 8, "ALT_AI": 8},
    standard=std,
    integration={"MOBI": 4},
)
check("MODULAR : 40 - 17 - 4 - 4 - 6", d["ecosystem"], 9)

print("\n   choc C : NEW REGULATION")
e = r3(
    "PROPRIETARY",
    "KEEP",
    "REGULATION",
    {"MOBI": 8, "AUTO": 6, "BRAIN": 6, "GRID": 6, "FLEET": 8},
    integration={"MOBI": 8},
)
check("PROPRIETARY : 34 - 21 - 8", e["ecosystem"], 5)
check("personne n'est evince", all(e["joined"].values()), True)
f = r3(
    "MODULAR",
    "KEEP",
    "REGULATION",
    {"MOBI": 8, "AUTO": 8, "BRAIN": 8, "GRID": 8, "FLEET": 8},
    standard=std,
    integration={"MOBI": 3},
)
check("MODULAR : 40 - 21 - 3 - 6", f["ecosystem"], 10)

print("\n   equilibre : aucune architecture ne domine en esperance")
prop = [19, 3, 5]
modu = [11, 9, 10]
check("esperance PROPRIETARY", round(sum(prop) / 3.0, 2), 9.0)
check("esperance MODULAR", round(sum(modu) / 3.0, 2), 10.0)
ok("l'ecart d'esperance reste sous 2 points", abs(sum(prop) - sum(modu)) / 3.0 < 2)
ok(
    "chaque architecture gagne au moins un choc",
    any(p > m for p, m in zip(prop, modu, strict=True))
    and any(m > p for p, m in zip(prop, modu, strict=True)),
)

print("\n   tirage et options imposees par le choc")
g, tok = build(2)
play_r2(g, tok)
g.set_phase("MARKET")
g.set_phase("R3_ARCH")
for t in g.active_teams():
    g.submit_architecture(tok[(t, "MOBI")], "PROPRIETARY", {})
check("aucun choc avant R3_SHOCK", g.state["shock"], None)
g.set_phase("R3_SHOCK")
ok("un choc a ete tire", g.state["shock"] in R.SHOCK_KEYS)
check(
    "il est le meme pour toute la classe",
    len({g.state["teams"][t]["rounds"]["3"]["shock"] for t in g.active_teams()}),
    1,
)
g.force_shock("INFRA_FAILURE")
g.set_phase("R3_NEGO")
msg = raises(
    "KEEP impossible face a INFRA FAILURE",
    g.submit_resolution,
    tok[("BLUE", "MOBI")],
    "KEEP",
    {r: 9 for r in R.ROLES},
    {},
)
ok("le message nomme le choc", "INFRA FAILURE" in msg)
raises(
    "le cout d'adaptation doit etre reparti",
    g.submit_resolution,
    tok[("BLUE", "MOBI")],
    "REPLACE",
    {"MOBI": 6, "AUTO": 6, "BRAIN": 6, "FLEET": 6, "ALT_AI": 10},
    {"MOBI": 3},
)
g.submit_resolution(
    tok[("BLUE", "MOBI")],
    "REPLACE",
    {"MOBI": 6, "AUTO": 6, "BRAIN": 6, "FLEET": 6, "ALT_AI": 10},
    {"MOBI": 10},
)
check("resolution acceptee", g.state["teams"]["BLUE"]["rounds"]["3"]["resolution"], "REPLACE")
raises("GRID remplace ne decide plus", g.decide, tok[("BLUE", "GRID")], "JOIN")


# ---------------------------------------------------------------------------
# 4. Pouvoirs de role
# ---------------------------------------------------------------------------

print("\n4. POUVOIRS")
print("\n   MOBI - SUBVENTION")
g, tok = build(2)
g.set_phase("R1_NEGO")
g.use_power(tok[("BLUE", "MOBI")], target="FLEET", amount=3)
check("FLEET recoit 3 points", g.state["teams"]["BLUE"]["adjust"]["FLEET"], 3)
check("MOBI les perd", g.state["teams"]["BLUE"]["adjust"]["MOBI"], -3)
check("le pouvoir est marque utilise", g.state["teams"]["BLUE"]["powers"]["MOBI"]["used"], True)
raises(
    "un pouvoir ne sert qu'une fois", g.use_power, tok[("BLUE", "MOBI")], target="AUTO", amount=1
)
raises(
    "au-dela du plafond",
    g.use_power,
    tok[("GREEN", "MOBI")],
    target="AUTO",
    amount=R.POWERS["MOBI"]["max"] + 1,
)
raises(
    "on ne se subventionne pas soi-meme",
    g.use_power,
    tok[("GREEN", "MOBI")],
    target="MOBI",
    amount=2,
)

print("\n   AUTO - MULTI-HOMING")
g, tok = build(2)
play_r2(g, tok)
raises("multi-homing hors du marche", g.use_power, tok[("BLUE", "AUTO")])
g.set_phase("MARKET")
g.use_power(tok[("BLUE", "AUTO")])
gain = R.POWERS["AUTO"]["max"]
check("AUTO gagne %d points" % gain, g.state["teams"]["BLUE"]["adjust"]["AUTO"], gain)
check(
    "l'ecosysteme perd autant de valeur collective", g.state["teams"]["BLUE"]["eco_adjust"], -gain
)
check("AUTO reste membre", g.state["players"][tok[("BLUE", "AUTO")]]["team"], "BLUE")
raises("multi-homing ne se rejoue pas", g.use_power, tok[("BLUE", "AUTO")])

print("\n   FLEET - VETO D'ARCHITECTURE")
g, tok = build(2)
play_r2(g, tok)
g.set_phase("MARKET")
raises("le veto ne s'utilise qu'au choix d'architecture", g.use_power, tok[("BLUE", "FLEET")])
g.set_phase("R3_ARCH")
g.use_power(tok[("BLUE", "FLEET")])
check("le veto est pose", g.state["teams"]["BLUE"]["veto"], True)
raises(
    "PROPRIETARY devient impossible",
    g.submit_architecture,
    tok[("BLUE", "MOBI")],
    "PROPRIETARY",
    {},
)
g.submit_architecture(
    tok[("BLUE", "MOBI")], "MODULAR", {"MOBI": 6, "AUTO": 0, "BRAIN": 0, "GRID": 0, "FLEET": 0}
)
check("MODULAR reste ouvert", g.state["teams"]["BLUE"]["rounds"]["3"]["architecture"], "MODULAR")
g.submit_architecture(tok[("GREEN", "MOBI")], "PROPRIETARY", {})
check(
    "les autres ecosystemes ne sont pas concernes",
    g.state["teams"]["GREEN"]["rounds"]["3"]["architecture"],
    "PROPRIETARY",
)
raises("le veto ne se rejoue pas", g.use_power, tok[("BLUE", "FLEET")])

print("\n   GRID - STANDARD READY")
g, tok = build(2)
play_r2(g, tok)
g.set_phase("MARKET")
g.set_phase("R3_ARCH")
g.submit_architecture(
    tok[("BLUE", "MOBI")], "MODULAR", {"MOBI": 6, "AUTO": 0, "BRAIN": 0, "GRID": 0, "FLEET": 0}
)
g.submit_architecture(tok[("GREEN", "MOBI")], "PROPRIETARY", {})
raises("STANDARD READY ne s'utilise qu'au round 3", g.use_power, tok[("BLUE", "GRID")])
g.set_phase("R3_SHOCK")
g.force_shock("REGULATION")
g.set_phase("R3_NEGO")
raises("STANDARD READY est ferme aux proprietaires", g.use_power, tok[("GREEN", "GRID")])
g.use_power(tok[("BLUE", "GRID")])
check("pouvoir utilise", g.state["teams"]["BLUE"]["powers"]["GRID"]["used"], True)
raises(
    "le cout plein n'est plus exige",
    g.submit_resolution,
    tok[("BLUE", "MOBI")],
    "KEEP",
    {r: 8 for r in R.ROLES},
    {"MOBI": 3},
)
g.submit_resolution(tok[("BLUE", "MOBI")], "KEEP", {r: 8 for r in R.ROLES}, {"MOBI": 1})
check(
    "cout de conformite reduit de 3 a 1", g.state["teams"]["BLUE"]["rounds"]["3"]["adapt_cost"], 1
)
raises("STANDARD READY ne se rejoue pas", g.use_power, tok[("BLUE", "GRID")])

print("\n   confidentialite et affichage des pouvoirs")
g, tok = build(2)
g.set_phase("R1_NEGO")
v = g.player_view(tok[("BLUE", "MOBI")])
check("MOBI voit son pouvoir", v["me"]["power"]["name"], "SUBVENTION")
check("il est disponible", v["me"]["power"]["available"], True)
check("il n'est pas encore utilise", v["me"]["power"]["used"], False)
v = g.player_view(tok[("BLUE", "FLEET")])
check("le veto de FLEET n'est pas encore revele", v["me"]["power"], None)
g.use_power(tok[("BLUE", "MOBI")], target="FLEET", amount=2)
v = g.player_view(tok[("BLUE", "MOBI")])
check("puis marque utilise", v["me"]["power"]["used"], True)
hv = g.host_view()
check("le tableau de bord signale l'activation", hv["powers"]["BLUE"]["MOBI"]["name"], "SUBVENTION")
ok("sans divulguer le detail prive", "detail" not in hv["powers"]["BLUE"]["MOBI"])


# ---------------------------------------------------------------------------
# 5. Badges
# ---------------------------------------------------------------------------

print("\n5. BADGES")


def keys_of(g, team):
    return [b["key"] for b in g.team_badges(team)]


print("\n   HOLD-UP")
g, tok = build(2)
play_r2(g, tok, contract={"MOBI": 4, "AUTO": 8, "BRAIN": 12, "GRID": 8, "FLEET": 8})
ok("BRAIN a capte 12 des 40 points", "HOLD_UP" in keys_of(g, "BLUE"))
g, tok = build(2)
play_r2(g, tok, contract={"MOBI": 5, "AUTO": 8, "BRAIN": 11, "GRID": 8, "FLEET": 8})
ok("11 points ne suffisent pas", "HOLD_UP" not in keys_of(g, "BLUE"))

print("\n   FAILED BARGAIN")
g, tok = build(2)
g.set_phase("R1_NEGO")
g.set_phase("R1_DECIDE")
for (t, role), token in tok.items():
    g.decide(token, "OUT" if (t, role) == ("BLUE", "FLEET") else "JOIN")
g.set_phase("R1_RESULTS")
ok("un seul OUT suffit", "FAILED_BARGAIN" in keys_of(g, "BLUE"))
ok("l'ecosysteme complet ne l'a pas", "FAILED_BARGAIN" not in keys_of(g, "GREEN"))

print("\n   POACHED")
g, tok = build(3)
play_r2(g, tok)
g.set_phase("MARKET")
g.make_offer(tok[("BLUE", "MOBI")], "GREEN", 4)
g.make_offer(tok[("GREEN", "MOBI")], "BLUE", 4)
g.market_decide(tok[("GREEN", "BRAIN")], "BLUE")
g.market_decide(tok[("BLUE", "BRAIN")], "GREEN")
g.set_phase("R3_ARCH")
ok("GREEN a perdu son BRAIN", "POACHED" in keys_of(g, "GREEN"))
ok("RED ne l'a pas", "POACHED" not in keys_of(g, "RED"))

print("\n   LOCK-IN et RESILIENT ECOSYSTEM")
g, tok = build(2)
play_r2(g, tok)
g.set_phase("MARKET")
g.set_phase("R3_ARCH")
g.submit_architecture(
    tok[("BLUE", "MOBI")], "MODULAR", {"MOBI": 6, "AUTO": 0, "BRAIN": 0, "GRID": 0, "FLEET": 0}
)
g.submit_architecture(tok[("GREEN", "MOBI")], "PROPRIETARY", {})
g.set_phase("R3_SHOCK")
g.force_shock("REGULATION")
g.set_phase("R3_NEGO")
g.submit_resolution(tok[("BLUE", "MOBI")], "KEEP", {r: 8 for r in R.ROLES}, {"MOBI": 3})
# GREEN est proprietaire : la recertification coute 12 de retard, valeur 34
g.submit_resolution(
    tok[("GREEN", "MOBI")],
    "KEEP",
    {"MOBI": 6, "AUTO": 7, "BRAIN": 7, "GRID": 7, "FLEET": 7},
    {"MOBI": 8},
)
g.set_phase("R3_DECIDE")
for (_t, _role), token in tok.items():
    g.decide(token, "JOIN")
g.set_phase("R3_RESULTS")
ok("le modulaire qui encaisse le choc est resilient", "RESILIENT" in keys_of(g, "BLUE"))
ok("il n'est pas verrouille", "LOCK_IN" not in keys_of(g, "BLUE"))
ok("le proprietaire qui survit est verrouille", "LOCK_IN" in keys_of(g, "GREEN"))
ok("il n'est pas resilient", "RESILIENT" not in keys_of(g, "GREEN"))

print("\n   les badges ne touchent pas aux scores")
players, eco = g.totals()
blue = g.state["teams"]["BLUE"]["rounds"]["3"]["result"]
check("valeur collective de BLUE inchangee", eco["BLUE"]["rounds"]["3"], blue["ecosystem"])
check("aucun ajustement parasite", eco["BLUE"]["adjust"], 0)
brain = next(r for r in players if r["team"] == "GREEN" and r["role"] == "BRAIN")
check(
    "le score individuel ne depend pas des badges",
    brain["total"],
    sum(
        g.state["teams"]["GREEN"]["rounds"][n]["result"]["scores"]["BRAIN"] for n in ("1", "2", "3")
    ),
)
ok("les badges sont bien remontes au joueur", "LOCK_IN" in brain["badges"])
ok("chaque badge porte une explication", all(len(b["text"]) > 10 for b in g.team_badges("GREEN")))


# ---------------------------------------------------------------------------
# 6. Persistance
# ---------------------------------------------------------------------------

print("\n6. RECONNEXION - les decisions survivent a un rechargement")
import json

g, tok = build(3)
play_r2(g, tok)
g.set_phase("MARKET")
g.make_offer(tok[("BLUE", "MOBI")], "GREEN", 4)
g.market_decide(tok[("GREEN", "BRAIN")], "BLUE")
g.use_power(tok[("BLUE", "AUTO")])

saved = json.loads(json.dumps(g.state))
g2 = engine.Game(saved)
check("l'offre est conservee", g2.state["market"]["offers"]["BLUE"]["GREEN"], 4)
check("la decision secrete du BRAIN aussi", g2.state["market"]["decisions"]["GREEN"], "BLUE")
check("le pouvoir reste marque utilise", g2.state["teams"]["BLUE"]["powers"]["AUTO"]["used"], True)
check(
    "l'ajustement est conserve",
    g2.state["teams"]["BLUE"]["adjust"]["AUTO"],
    R.POWERS["AUTO"]["max"],
)
raises("le pouvoir ne se rejoue pas apres reconnexion", g2.use_power, tok[("BLUE", "AUTO")])

print("\n   une partie enregistree avant la mise a jour se recharge")
old = json.loads(json.dumps(new_state(code="OLD", team_count=2)))
for key in ("market", "shock"):
    old.pop(key, None)
for t in old["teams"].values():
    for key in (
        "adjust",
        "eco_adjust",
        "powers",
        "veto",
        "exclusive",
        "pending_exclusive",
        "lost_brain",
    ):
        t.pop(key, None)
    t["rounds"]["3"].pop("shock", None)
g3 = engine.Game(old)
check("le marche est recree", g3.state["market"]["resolved"], False)
check(
    "les ajustements sont remis a zero",
    g3.state["teams"]["BLUE"]["adjust"],
    {r: 0 for r in R.ROLES},
)
ok("le tableau de bord se construit", bool(g3.host_view()["teams"]))


# ---------------------------------------------------------------------------
# 7. Toutes les vues, dans toutes les phases, pour les trois chocs
# ---------------------------------------------------------------------------

print("\n7. VUES - aucune phase ne casse l'affichage")

for shock in R.SHOCK_KEYS:
    g, tok = build(2)
    seen = []
    for phase in R.PHASE_KEYS:
        g.set_phase(phase)
        if phase == "R3_SHOCK":
            g.force_shock(shock)
        if phase == "R3_ARCH":
            g.submit_architecture(
                tok[("BLUE", "MOBI")],
                "MODULAR",
                {"MOBI": 6, "AUTO": 0, "BRAIN": 0, "GRID": 0, "FLEET": 0},
            )
            g.submit_architecture(tok[("GREEN", "MOBI")], "PROPRIETARY", {})
        g.host_view()
        for token in tok.values():
            v = g.player_view(token)
            seen.append(v["phase_label"])
    ok(
        "%s : les %d phases s'affichent" % (shock, len(R.PHASE_KEYS)),
        len(set(seen)) == len(R.PHASE_KEYS),
    )

print("\n   l'avertissement ne trahit pas le choc")
g, tok = build(2)
g.set_phase("R3_ARCH")
v = g.player_view(tok[("BLUE", "MOBI")])
check("aucun choc revele avant le tirage", v["shock"], None)
ok("seul l'avertissement generique est envoye", "lequel" in v["shock_warning"])
for key in R.SHOCK_KEYS:
    ok(
        "le nom du choc %s n'apparait pas" % key,
        key not in repr(v) and R.SHOCKS[key]["label"] not in repr(v),
    )
g.set_phase("R3_SHOCK")
v = g.player_view(tok[("BLUE", "MOBI")])
ok("le choc est revele apres le tirage", v["shock"] in R.SHOCK_KEYS)


# ---------------------------------------------------------------------------

print("")
if FAILS:
    print("%d ECHEC(S) : %s" % (len(FAILS), " | ".join(FAILS)))
    sys.exit(1)
print("Toutes les mecaniques ajoutees sont conformes.")
