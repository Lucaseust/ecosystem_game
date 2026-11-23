"""Comparer quatre politiques sur des circonstances identiques, sans donnees de cours."""

from collections import defaultdict
from statistics import mean
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.dont_write_bytecode = True
from eco.campaign import Game, new_state
from eco import rules as R


def simulate(seed, architecture, launch):
    g = Game(new_state(seed=seed))
    g.set_team_count(2)
    g.step()
    c = g.c("BLUE")
    shares = dict(MOBI=19, AUTO=20, BRAIN=20, GRID=20, FLEET=21)
    extra = (600 if architecture == "MODULAR" else 0) + (300 if launch == "PILOT" else 0)
    g.submit(
        "BLUE",
        "MOBI",
        dict(
            kind="INSTALL",
            architecture=architecture,
            launch=launch,
            allocations={
                r: g.capacity_revenue("BLUE", architecture, None, False) * v // 100
                for r, v in shares.items()
            },
            funding={"MOBI": extra},
        ),
    )
    assert c["installed"]
    for _ in range(4):
        if c["incident"]:
            need = g.quote("BLUE", "REPAIR")
            funding = {r: 0 for r in R.ROLES}
            for role in R.ROLES:
                take = min(need, c["cash"][role])
                funding[role] = take
                need -= take
            if not need:
                g.submit(
                    "BLUE",
                    "MOBI",
                    dict(
                        kind="REPAIR",
                        allocations={r: g.gross("BLUE") * v // 100 for r, v in shares.items()},
                        funding=funding,
                    ),
                )
        elif c["proposal"]["date"] != g.state["phase"]:
            g.submit(
                "BLUE",
                "MOBI",
                dict(
                    kind="REVISE",
                    allocations={r: g.gross("BLUE") * v // 100 for r, v in shares.items()},
                    funding={},
                ),
            )
        g.step()
    assert c["created"] == c["revenue"] - c["expenses"]
    return c["created"] / 100


def main():
    policies = [
        (architecture, launch)
        for architecture in ("INTEGRATED", "MODULAR")
        for launch in ("EARLY", "PILOT")
    ]
    results = defaultdict(list)
    wins = defaultdict(int)
    for number in range(80):
        row = {p: simulate("balance-%d" % number, *p) for p in policies}
        best = max(row.values())
        for policy, value in row.items():
            results[policy].append(value)
            if value == best:
                wins[policy] += 1
    for policy, values in results.items():
        print(
            policy,
            "mean",
            round(mean(values), 2),
            "min",
            min(values),
            "max",
            max(values),
            "best_cases",
            wins[policy],
        )
    assert all(wins[p] > 0 for p in policies), (
        "Une politique ne gagne dans aucun des cas testes : revoir les parametres."
    )
    print(
        "320 campagnes synthetiques : chaque combinaison gagne dans au moins un contexte. Ce controle ne prouve pas un equilibre universel."
    )


if __name__ == "__main__":
    main()
