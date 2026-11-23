# -*- coding: utf-8 -*-
"""Verifie la repartition des etudiants dans les ecosystemes et les roles.

Lancement :  python tests/test_places.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.dont_write_bytecode = True

from eco import rules as R
from eco.engine import Game

FAILS = []


def check(label, got, want):
    if got != want:
        FAILS.append(label)
        print("  ECHEC  %-56s %r != %r" % (label, got, want))
    else:
        print("  ok     %-56s %r" % (label, got))


def seat_sizes(g):
    m = g.seat_map()
    return {k: len(v) for k, v in m.items() if k[0] in g.active_teams()}


def report(n):
    g = Game()
    for i in range(n):
        g.join("E%02d" % i, g.state["code"])
    sizes = seat_sizes(g)
    teams = g.active_teams()
    empty = sorted(k for k, v in sizes.items() if v == 0)
    pairs = sorted(k for k, v in sizes.items() if v > 1)
    orphan_mobi = [t for t in teams if sizes[(t, "MOBI")] == 0]
    print(
        "\n%d etudiants -> %d ecosystemes, %d sieges vacants, %d binomes"
        % (n, len(teams), len(empty), len(pairs))
    )
    return g, sizes, teams, empty, pairs, orphan_mobi


print("Repartition automatique")
for n, want_teams, want_empty in [
    (10, 2, 0),
    (12, 2, 0),
    (15, 3, 0),
    (17, 3, 0),
    (20, 4, 0),
    (23, 4, 0),
    (8, 2, 2),
    (25, 5, 0),
]:
    g, sizes, teams, empty, pairs, orphan = report(n)
    check("  %d etudiants : nombre d'ecosystemes" % n, len(teams), want_teams)
    check("  %d etudiants : sieges vacants" % n, len(empty), want_empty)
    check("  %d etudiants : chaque equipe a son MOBI" % n, orphan, [])
    check("  %d etudiants : tous places" % n, sum(sizes.values()), n)
    spread = [sum(sizes[(t, r)] for r in R.ROLES) for t in teams]
    check(
        "  %d etudiants : equipes equilibrees (ecart <= 1)" % n,
        max(spread) - min(spread) <= 1,
        True,
    )

print("\nUn siege vacant est joue automatiquement")
g = Game()
for i in range(9):
    g.join("E%d" % i, g.state["code"])
vac = [(t, r) for t in g.active_teams() for r in R.ROLES if g.is_bot(t, r)]
check("  9 etudiants : un seul siege vacant", len(vac), 1)
check("  ce n'est jamais MOBI", [r for _, r in vac if r == "MOBI"], [])

print("\nL'enseignant peut fixer le nombre d'ecosystemes")
g = Game()
for i in range(20):
    g.join("E%02d" % i, g.state["code"])
with g.lock:
    g.set_team_count(2)
check("  reduit a 2 ecosystemes", len(g.active_teams()), 2)
sizes = seat_sizes(g)
check("  les 20 etudiants sont toujours places", sum(sizes.values()), 20)
check("  aucun siege vacant", [k for k, v in sizes.items() if v == 0], [])
check("  le reglage manuel desactive l'automatisme", g.state["auto_teams"], False)

with g.lock:
    g.set_team_count(4)
sizes = seat_sizes(g)
check("  reouvert a 4 : aucun siege vacant", [k for k, v in sizes.items() if v == 0], [])
check("  reouvert a 4 : aucun binome", [k for k, v in sizes.items() if v > 1], [])

print("\nRedistribution des roles")
g = Game()
for i in range(20):
    g.join("E%02d" % i, g.state["code"])
before = {p["id"]: (p["team"], p["role"]) for p in g.state["players"].values()}
g.shuffle()
after = {p["id"]: (p["team"], p["role"]) for p in g.state["players"].values()}
check("  tout le monde a toujours une place", len(after), 20)
check("  toutes les places sont distinctes", len(set(after.values())), 20)
check("  au moins un joueur a change de place", any(before[k] != after[k] for k in before), True)

print()
if FAILS:
    print("%d ECHEC(S) : %s" % (len(FAILS), ", ".join(FAILS)))
    sys.exit(1)
print("Repartition conforme.")
