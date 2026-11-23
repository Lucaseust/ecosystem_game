# -*- coding: utf-8 -*-
"""Verifie que le moteur reproduit exactement les chiffres de concept.md.

Lancement :  python tests/test_scores.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.dont_write_bytecode = True

from eco import rules as R
from eco.engine import score_simple, score_round3, round3_value

FAILS = []


def check(label, got, want):
    if got != want:
        FAILS.append("%s : obtenu %r, attendu %r" % (label, got, want))
        print("  ECHEC  %-52s %r != %r" % (label, got, want))
    else:
        print("  ok     %-52s %r" % (label, got))


# --- concept.md, §9 : rationalite du round 1 -------------------------------

print("\nRound 1 - scores individuels si l'ecosysteme reussit (§9)")
all_join = {r: "JOIN" for r in R.ROLES}
r1 = score_simple(all_join, R.R1_REVENUE)
check("MOBI participe  10-3+14", r1["scores"]["MOBI"], 21)
check("AUTO participe  10-5+10", r1["scores"]["AUTO"], 15)
check("BRAIN participe 10-4+6", r1["scores"]["BRAIN"], 12)
check("GRID participe  10-4+6", r1["scores"]["GRID"], 12)
check("FLEET participe 10-5+4", r1["scores"]["FLEET"], 9)
check("valeur collective 40-21", r1["ecosystem"], 19)

print("\nRound 1 - scores si l'acteur sort (§9)")
none_join = {r: "OUT" for r in R.ROLES}
out = score_simple(none_join, R.R1_REVENUE)
check("MOBI sort  10+0", out["scores"]["MOBI"], 10)
check("AUTO sort  10+3", out["scores"]["AUTO"], 13)
check("BRAIN sort 10+4", out["scores"]["BRAIN"], 14)
check("GRID sort  10+2", out["scores"]["GRID"], 12)
check("FLEET sort 10+4", out["scores"]["FLEET"], 14)
check("aucun investissement realise", out["ecosystem"], 0)

print("\nRound 1 - un seul refus fait echouer tout l'ecosysteme (§8)")
mix = {r: "JOIN" for r in R.ROLES}
mix["FLEET"] = "OUT"
m = score_simple(mix, R.R1_REVENUE)
check("service non lance", m["success"], False)
check("MOBI a investi sans revenu 10-3", m["scores"]["MOBI"], 7)
check("BRAIN a investi sans revenu 10-4", m["scores"]["BRAIN"], 6)
check("FLEET a pris son exterieur 10+4", m["scores"]["FLEET"], 14)
check("score collectif = -investissements", m["ecosystem"], -(3 + 5 + 4 + 4))

# --- concept.md, §9 : le surplus existe bel et bien ------------------------

print("\nSurplus theorique disponible (§9)")
check("somme des couts", sum(R.COST.values()), 21)
check("somme des options exterieures", sum(R.OUTSIDE.values()), 13)
check("surplus 40-21-13", R.V_BASE - 21 - 13, 6)

# --- concept.md, §10 : seuils de participation -----------------------------

print("\nSeuils de participation R >= C + O (§10)")
check("MOBI", R.THRESHOLDS["MOBI"], 3)
check("AUTO", R.THRESHOLDS["AUTO"], 8)
check("BRAIN", R.THRESHOLDS["BRAIN"], 8)
check("GRID", R.THRESHOLDS["GRID"], 6)
check("FLEET", R.THRESHOLDS["FLEET"], 9)
check("total minimal", sum(R.THRESHOLDS.values()), 34)
check("surplus negociable 40-34", R.V_BASE - 34, 6)

print("\nUn acteur paye exactement son seuil est indifferent")
contract = dict(R.THRESHOLDS)
contract["MOBI"] += 6  # MOBI capte tout le surplus
r2 = score_simple(all_join, contract)
for role in R.ROLES:
    if role == "MOBI":
        continue
    check("%s : JOIN vaut son option exterieure" % role, r2["scores"][role], 10 + R.OUTSIDE[role])
check("MOBI capte les 6 points de surplus", r2["scores"]["MOBI"], 10 - 3 + 9)
check("valeur collective inchangee", r2["ecosystem"], 19)

# --- concept.md, §11 : round 3 ---------------------------------------------

print("\nRound 3 - valeurs du service selon architecture et solution (§11)")
check("proprietaire, BRAIN conserve", round3_value("PROPRIETARY", "KEEP"), 46)
check("proprietaire, BRAIN remplace 46-12", round3_value("PROPRIETARY", "REPLACE"), 34)
check("modulaire, BRAIN conserve", round3_value("MODULAR", "KEEP"), 40)
check("modulaire, BRAIN remplace", round3_value("MODULAR", "REPLACE"), 40)


def r3(arch, resolution, revenues, standard=None, integration=None, decisions=None):
    roles = R.ROLES if resolution != "REPLACE" else ["MOBI", "AUTO", "GRID", "FLEET"]
    return score_round3(
        {
            "architecture": arch,
            "standard": standard or {r: 0 for r in R.ROLES},
            "resolution": resolution,
            "contract": revenues,
            "integration": integration or {r: 0 for r in R.ROLES},
            "decisions": decisions or {r: "JOIN" for r in roles},
        }
    )


print("\nRound 3 - architecture proprietaire sans remplacement : 46-21-6 = 19 (§11)")
keep_p = r3("PROPRIETARY", "KEEP", {"MOBI": 10, "AUTO": 8, "BRAIN": 14, "GRID": 6, "FLEET": 8})
check("valeur collective", keep_p["ecosystem"], 19)
check("service lance", keep_p["success"], True)
check("BRAIN paie sa mise en conformite 10-4-6+14", keep_p["scores"]["BRAIN"], 14)
check("FLEET 10-5+8", keep_p["scores"]["FLEET"], 13)

print("\nRound 3 - architecture proprietaire avec remplacement : 46-12-21-8 = 5 (§11)")
repl_p = r3(
    "PROPRIETARY",
    "REPLACE",
    {"MOBI": 8, "AUTO": 8, "GRID": 6, "FLEET": 4, "ALT_AI": 8},
    integration={"MOBI": 4, "AUTO": 2, "GRID": 1, "FLEET": 1, "BRAIN": 0},
)
check("valeur du service apres retard", repl_p["value"], 34)
check("valeur collective", repl_p["ecosystem"], 5)
check("BRAIN ecarte prend son exterieur 10+4", repl_p["scores"]["BRAIN"], 14)
check("MOBI 10-3-4+8", repl_p["scores"]["MOBI"], 11)

print("\nRound 3 - architecture modulaire avec remplacement : 40-21-6-2 = 11 (§11)")
repl_m = r3(
    "MODULAR",
    "REPLACE",
    {"MOBI": 10, "AUTO": 9, "GRID": 7, "FLEET": 6, "ALT_AI": 8},
    standard={"MOBI": 2, "AUTO": 1, "BRAIN": 1, "GRID": 1, "FLEET": 1},
    integration={"MOBI": 1, "AUTO": 1, "GRID": 0, "FLEET": 0, "BRAIN": 0},
)
check("valeur du service", repl_m["value"], 40)
check("valeur collective", repl_m["ecosystem"], 11)
check("BRAIN ecarte 10-1(standard)+4", repl_m["scores"]["BRAIN"], 13)
check("MOBI 10-2(standard)-1(integration)-3+10", repl_m["scores"]["MOBI"], 14)

print("\nRound 3 - architecture modulaire avec BRAIN conserve : 40-21-6-6 = 7")
keep_m = r3(
    "MODULAR",
    "KEEP",
    {"MOBI": 6, "AUTO": 8, "BRAIN": 14, "GRID": 6, "FLEET": 6},
    standard={"MOBI": 6, "AUTO": 0, "BRAIN": 0, "GRID": 0, "FLEET": 0},
)
check("valeur collective", keep_m["ecosystem"], 7)

print("\nRound 3 - ALT-AI refuse en dessous de 8 points")
low = r3(
    "MODULAR",
    "REPLACE",
    {"MOBI": 12, "AUTO": 9, "GRID": 7, "FLEET": 5, "ALT_AI": 7},
    integration={"MOBI": 2, "AUTO": 0, "GRID": 0, "FLEET": 0, "BRAIN": 0},
)
check("service non lance", low["success"], False)

print("\nRound 3 - abandon : chacun reprend son option exterieure (§11)")
ab = score_round3(
    {
        "architecture": "MODULAR",
        "resolution": "ABANDON",
        "standard": {"MOBI": 3, "AUTO": 3, "BRAIN": 0, "GRID": 0, "FLEET": 0},
        "contract": None,
        "integration": {},
        "decisions": {},
    }
)
check("MOBI 10-3+0", ab["scores"]["MOBI"], 7)
check("FLEET 10-0+4", ab["scores"]["FLEET"], 14)
check("le standard reste perdu", ab["ecosystem"], -6)

print("\nRound 3 - un refus fait echouer malgre l'accord")
fail = r3(
    "PROPRIETARY",
    "KEEP",
    {"MOBI": 10, "AUTO": 8, "BRAIN": 14, "GRID": 6, "FLEET": 8},
    decisions={"MOBI": "JOIN", "AUTO": "JOIN", "BRAIN": "JOIN", "GRID": "JOIN", "FLEET": "OUT"},
)
check("service non lance", fail["success"], False)
check("FLEET a pris son exterieur", fail["scores"]["FLEET"], 14)
check("BRAIN a paye 4+6 pour rien", fail["scores"]["BRAIN"], 0)
check("score collectif = -investissements", fail["ecosystem"], -(3 + 5 + 10 + 4))

# --- coherence generale -----------------------------------------------------

print("\nCoherence : somme des scores individuels et valeur collective")
# quand tout le monde participe, la somme des scores vaut 50 + valeur collective
tot = sum(keep_p["scores"].values())
check("round 3 proprietaire conserve : 5x10 + 19", tot, 50 + 19)
tot2 = sum(r1["scores"].values())
check("round 1 reussi : 5x10 + 19", tot2, 50 + 19)

print()
if FAILS:
    print("%d ECHEC(S)" % len(FAILS))
    sys.exit(1)
print("Tous les controles passent.")
