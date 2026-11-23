# -*- coding: utf-8 -*-
"""Simule une seance complete a 20 joueurs contre un vrai serveur HTTP.

Lancement :  python tests/test_partie.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.dont_write_bytecode = True

PORT = 8099
BASE = "http://127.0.0.1:%d" % PORT
HOST_KEY = "cle-de-test"
ROLES = ["MOBI", "AUTO", "BRAIN", "GRID", "FLEET"]

FAILS = []


def check(label, got, want):
    if got != want:
        FAILS.append(label)
        print("  ECHEC  %-56s %r != %r" % (label, got, want))
    else:
        print("  ok     %-56s %r" % (label, got))


def ok(label, condition):
    check(label, bool(condition), True)


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def post(path, payload):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8")), r.status
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode("utf-8")), e.code


# ---------------------------------------------------------------------------


def main():
    tmp = tempfile.mkdtemp(prefix="eco-test-")
    proc = subprocess.Popen(
        [
            sys.executable,
            os.path.join(ROOT, "serveur.py"),
            "--port",
            str(PORT),
            "--host",
            "127.0.0.1",
            "--cle",
            HOST_KEY,
            "--nouvelle",
            "--legacy",
            "--donnees",
            tmp,
        ],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        run(tmp)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if FAILS:
        print("%d ECHEC(S) : %s" % (len(FAILS), ", ".join(FAILS)))
        sys.exit(1)
    print("Seance complete simulee sans erreur.")


def wait_up():
    for _ in range(80):
        try:
            return get("/api/info")
        except Exception:
            time.sleep(0.25)
    raise SystemExit("Le serveur n'a pas demarre.")


def run(tmp):
    info = wait_up()
    print("\nServeur demarre, partie %s" % info["code"])

    key = HOST_KEY

    def hact(action, **kw):
        payload = {"cle": key, "action": action}
        payload.update(kw)
        return post("/api/host/action", payload)

    def hstate():
        return get("/api/host?cle=" + key)

    # --- inscriptions ------------------------------------------------------

    print("\nInscription de 20 etudiants")
    code = info["code"]

    res, status = post("/api/join", {"first_name": "Intrus", "last_name": "Test", "code": "ZZZZ"})
    check("code de partie errone refuse", status, 400)
    res, status = post("/api/join", {"first_name": "Intrus", "last_name": "Test"})
    check("inscription sans code refusee", status, 400)
    res, status = post("/api/join", {"name": "", "code": code})
    check("inscription sans prenom refusee", status, 400)
    res, status = post("/api/join", {"first_name": "Intrus", "last_name": "", "code": code})
    check("inscription sans nom refusee", status, 400)

    tokens = {}  # nom -> jeton
    for i in range(20):
        first_name = "Etudiant%02d" % (i + 1)
        name = first_name + " Test"
        res, status = post(
            "/api/join", {"first_name": first_name, "last_name": "Test", "code": code.lower()}
        )
        if i in (0, 19):
            check("inscription %d acceptee" % (i + 1), status, 200)
        tokens[name] = res["token"]

    # les places se stabilisent quand tout le monde est connecte : on les relit
    st = hstate()
    players = {(p["team"], p["role"]): tokens[p["name"]] for p in st["players"]}
    ok(
        "chacun retrouve sa place via /api/state",
        all(get("/api/state?token=" + players[k])["me"]["role"] == k[1] for k in list(players)[:5]),
    )
    check("nombre d'ecosystemes", st["team_count"], 4)
    check("sieges distincts occupes", len(players), 20)
    teams = sorted(st["teams"].keys())
    check("ecosystemes", teams, ["BLUE", "GREEN", "RED", "YELLOW"])
    for t in teams:
        vac = [r for r in ROLES if st["teams"][t]["seats"][r]["bot"]]
        check("%s : aucun siege vacant" % t, vac, [])

    def pact(team, role, action, **kw):
        payload = {"token": players[(team, role)], "action": action}
        payload.update(kw)
        return post("/api/action", payload)

    # --- ROUND 1 -----------------------------------------------------------

    print("\nRound 1 - repartition imposee")
    hact("phase", phase="R1_NEGO")
    res, status = pact("BLUE", "FLEET", "claim", amount=12, text="sinon je sors")
    check("annonce d'exigence acceptee", status, 200)

    res, status = pact("BLUE", "MOBI", "contract", revenues={r: 8 for r in ROLES})
    check("contrat refuse pendant le round 1", status, 400)

    hact("phase", phase="R1_DECIDE")
    # BLUE : tout le monde participe malgre l'accord defavorable
    # GREEN : FLEET refuse (cas du concept)
    # RED : BRAIN et FLEET refusent
    # YELLOW : personne ne repond (abstention = pas d'investissement)
    for r in ROLES:
        pact("BLUE", r, "decide", choice="JOIN")
    for r in ROLES:
        pact("GREEN", r, "decide", choice="OUT" if r == "FLEET" else "JOIN")
    for r in ROLES:
        pact("RED", r, "decide", choice="OUT" if r in ("BRAIN", "FLEET") else "JOIN")

    res, status = pact("BLUE", "AUTO", "decide", choice="MAYBE")
    check("choix invalide refuse", status, 400)

    st = hstate()
    check("BLUE : 5 reponses", st["teams"]["BLUE"]["rounds"]["1"]["answered"], 5)
    check("YELLOW : 0 reponse", st["teams"]["YELLOW"]["rounds"]["1"]["answered"], 0)

    hact("phase", phase="R1_RESULTS")
    st = hstate()
    b1 = st["teams"]["BLUE"]["rounds"]["1"]["result"]
    g1 = st["teams"]["GREEN"]["rounds"]["1"]["result"]
    y1 = st["teams"]["YELLOW"]["rounds"]["1"]["result"]
    check("BLUE : service lance", b1["success"], True)
    check("BLUE : valeur collective", b1["ecosystem"], 19)
    check("BLUE : FLEET 10-5+4", b1["scores"]["FLEET"], 9)
    check("GREEN : service non lance", g1["success"], False)
    check("GREEN : FLEET a pris son exterieur", g1["scores"]["FLEET"], 14)
    check("GREEN : MOBI a investi pour rien", g1["scores"]["MOBI"], 7)
    check("YELLOW : sans reponse, personne n'investit", y1["ecosystem"], 0)
    check("YELLOW : MOBI 10+0", y1["scores"]["MOBI"], 10)

    res, status = pact("BLUE", "MOBI", "decide", choice="OUT")
    check("decision refusee hors phase de decision", status, 400)

    # --- ROUND 2 -----------------------------------------------------------

    print("\nRound 2 - repartition libre")
    hact("phase", phase="R2_NEGO")

    res, status = pact("BLUE", "AUTO", "contract", revenues={r: 8 for r in ROLES})
    check("seul MOBI depose le contrat", status, 403 if status == 403 else 400)

    res, status = pact(
        "BLUE",
        "MOBI",
        "contract",
        revenues={"MOBI": 10, "AUTO": 10, "BRAIN": 10, "GRID": 5, "FLEET": 4},
    )
    check("contrat dont la somme n'est pas 40 refuse", status, 400)

    res, status = pact(
        "BLUE",
        "MOBI",
        "contract",
        revenues={"MOBI": -5, "AUTO": 15, "BRAIN": 10, "GRID": 10, "FLEET": 10},
    )
    check("revenu negatif refuse", status, 400)

    # BLUE : contrat aligne sur les seuils reels (3/8/8/6/9 = 34), surplus a MOBI
    blue_contract = {"MOBI": 9, "AUTO": 8, "BRAIN": 8, "GRID": 6, "FLEET": 9}
    res, status = pact("BLUE", "MOBI", "contract", revenues=blue_contract)
    check("contrat BLUE accepte", status, 200)

    # GREEN : MOBI garde trop, FLEET sous son seuil
    green_contract = {"MOBI": 18, "AUTO": 8, "BRAIN": 8, "GRID": 3, "FLEET": 3}
    pact("GREEN", "MOBI", "contract", revenues=green_contract)
    # RED : partage egal
    pact(
        "RED",
        "MOBI",
        "contract",
        revenues={"MOBI": 8, "AUTO": 8, "BRAIN": 8, "GRID": 8, "FLEET": 8},
    )
    # YELLOW : aucun contrat depose

    st = hstate()
    check(
        "contrat BLUE visible du tableau de bord",
        st["teams"]["BLUE"]["rounds"]["2"]["contract"],
        blue_contract,
    )

    view = get("/api/state?token=" + players[("BLUE", "FLEET")])
    check("FLEET voit le contrat publie", view["team"]["rounds"]["2"]["contract"]["FLEET"], 9)
    check("FLEET ne voit que son propre cout", view["me"]["cost"], 5)
    check("FLEET calcule lui-meme son seuil", "threshold" in view["me"], False)

    hact("phase", phase="R2_DECIDE")
    for r in ROLES:
        pact("BLUE", r, "decide", choice="JOIN")
    for r in ROLES:
        pact("GREEN", r, "decide", choice="OUT" if r in ("GRID", "FLEET") else "JOIN")
    for r in ROLES:
        pact("RED", r, "decide", choice="JOIN")

    res, status = pact(
        "BLUE",
        "MOBI",
        "contract",
        revenues={"MOBI": 20, "AUTO": 5, "BRAIN": 5, "GRID": 5, "FLEET": 5},
    )
    check("contrat non modifiable apres ouverture des decisions", status, 400)

    hact("phase", phase="R2_RESULTS")
    st = hstate()
    b2 = st["teams"]["BLUE"]["rounds"]["2"]["result"]
    r2 = st["teams"]["RED"]["rounds"]["2"]["result"]
    y2 = st["teams"]["YELLOW"]["rounds"]["2"]["result"]
    check("BLUE : service lance", b2["success"], True)
    check("BLUE : FLEET 10-5+9", b2["scores"]["FLEET"], 14)
    check("BLUE : MOBI 10-3+9", b2["scores"]["MOBI"], 16)
    check("BLUE : valeur collective", b2["ecosystem"], 19)
    check("RED : partage egal, service lance", r2["success"], True)
    check("RED : FLEET 10-5+8", r2["scores"]["FLEET"], 13)
    check("YELLOW : sans contrat, aucun accord", y2["success"], False)
    check("YELLOW : chacun reprend son exterieur", y2["scores"]["BRAIN"], 14)

    # --- MARCHE DES ECOSYSTEMES -------------------------------------------

    print("\nMarche des ecosystemes")
    hact("phase", phase="MARKET")

    # GREEN tente de debaucher le BRAIN de BLUE, qui refuse
    res, status = pact("GREEN", "MOBI", "offer", target="BLUE", points=4)
    check("GREEN fait une offre au BRAIN de BLUE", status, 200)
    res, status = pact("BLUE", "BRAIN", "market", choice="STAY")
    check("le BRAIN de BLUE reste", status, 200)

    view = get("/api/state?token=" + players[("BLUE", "BRAIN")])
    check("le BRAIN de BLUE voit l'offre recue", view["market"]["received"].get("GREEN"), 4)
    view = get("/api/state?token=" + players[("RED", "BRAIN")])
    check("un BRAIN sans offre n'en voit aucune", view["market"]["received"], {})

    # pouvoirs de role, par l'API
    res, status = pact("RED", "AUTO", "power")
    check("AUTO active le multi-homing", status, 200)
    res, status = pact("RED", "AUTO", "power")
    check("un pouvoir ne sert qu'une fois", status, 400)

    res, status = pact("RED", "BRAIN", "power")
    check("BRAIN propose l'exclusivite", status, 200)
    res, status = pact("RED", "MOBI", "exclusivity", accept=True)
    check("MOBI accorde l'exclusivite", status, 200)
    st = hstate()
    check("BRAIN de RED gagne 3 points", st["teams"]["RED"]["adjust"]["BRAIN"], 3)
    check("MOBI de RED les paie", st["teams"]["RED"]["adjust"]["MOBI"], -3)
    check(
        "le tableau de bord signale les pouvoirs actives",
        sorted(st["powers"]["RED"]),
        ["AUTO", "BRAIN"],
    )

    hact("phase", phase="R3_ARCH")

    st = hstate()
    check("marche resolu, aucun transfert", st["market"]["moves"], [])
    check("le BRAIN de BLUE est reste", st["teams"]["BLUE"]["lost_brain"], False)

    # --- ROUND 3 : architecture -------------------------------------------

    print("\nRound 3 - architecture")

    res, status = pact(
        "BLUE",
        "MOBI",
        "architecture",
        architecture="MODULAR",
        contributions={"MOBI": 2, "AUTO": 2, "BRAIN": 0, "GRID": 0, "FLEET": 0},
    )
    check("contributions au standard != 6 refusees", status, 400)

    blue_std = {"MOBI": 2, "AUTO": 1, "BRAIN": 1, "GRID": 1, "FLEET": 1}
    res, status = pact(
        "BLUE", "MOBI", "architecture", architecture="MODULAR", contributions=blue_std
    )
    check("BLUE choisit MODULAR", status, 200)
    pact("GREEN", "MOBI", "architecture", architecture="PROPRIETARY", contributions={})
    pact("RED", "MOBI", "architecture", architecture="PROPRIETARY", contributions={})
    pact(
        "YELLOW",
        "MOBI",
        "architecture",
        architecture="MODULAR",
        contributions={"MOBI": 6, "AUTO": 0, "BRAIN": 0, "GRID": 0, "FLEET": 0},
    )

    st = hstate()
    check(
        "architecture BLUE enregistree",
        st["teams"]["BLUE"]["rounds"]["3"]["architecture"],
        "MODULAR",
    )

    # --- ROUND 3 : choc ----------------------------------------------------

    print("\nRound 3 - choc et renegociation")
    hact("phase", phase="R3_SHOCK")
    # le choc est tire au sort : on l'impose pour que la seance soit rejouable
    hact("shock", shock="AI_FAILURE")
    st = hstate()
    check("choc de la classe", st["shock"], "AI_FAILURE")
    hact("phase", phase="R3_NEGO")

    # BLUE (modulaire) remplace BRAIN : valeur 40, integration 2
    res, status = pact(
        "BLUE",
        "MOBI",
        "resolution",
        resolution="REPLACE",
        revenues={"MOBI": 10, "AUTO": 9, "GRID": 7, "FLEET": 6, "ALT_AI": 7},
        integration={"MOBI": 1, "AUTO": 1, "GRID": 0, "FLEET": 0},
    )
    check("ALT-AI refuse 7 points", status, 400)

    res, status = pact(
        "BLUE",
        "MOBI",
        "resolution",
        resolution="REPLACE",
        revenues={"MOBI": 10, "AUTO": 9, "GRID": 7, "FLEET": 6, "ALT_AI": 8},
        integration={"MOBI": 1, "AUTO": 1, "GRID": 0, "FLEET": 0},
    )
    check("BLUE remplace BRAIN par ALT-AI", status, 200)

    # GREEN (proprietaire) conserve BRAIN : valeur 46
    res, status = pact(
        "GREEN",
        "MOBI",
        "resolution",
        resolution="KEEP",
        revenues={"MOBI": 10, "AUTO": 8, "BRAIN": 14, "GRID": 6, "FLEET": 8},
    )
    check("GREEN conserve BRAIN", status, 200)

    # RED (proprietaire) remplace BRAIN : valeur 46-12 = 34, integration 8
    res, status = pact(
        "RED",
        "MOBI",
        "resolution",
        resolution="REPLACE",
        revenues={"MOBI": 8, "AUTO": 8, "GRID": 6, "FLEET": 4, "ALT_AI": 8},
        integration={"MOBI": 4, "AUTO": 2, "GRID": 1, "FLEET": 1},
    )
    check("RED remplace BRAIN malgre le retard", status, 200)

    # YELLOW abandonne
    res, status = pact(
        "YELLOW", "MOBI", "resolution", resolution="ABANDON", revenues={}, integration={}
    )
    check("YELLOW abandonne", status, 200)

    view = get("/api/state?token=" + players[("BLUE", "BRAIN")])
    check(
        "BRAIN de BLUE voit qu'il est remplace",
        view["team"]["rounds"]["3"]["resolution"],
        "REPLACE",
    )

    hact("phase", phase="R3_DECIDE")
    res, status = pact("BLUE", "BRAIN", "decide", choice="JOIN")
    check("BRAIN remplace ne peut plus decider", status, 400)

    for r in ["MOBI", "AUTO", "GRID", "FLEET"]:
        pact("BLUE", r, "decide", choice="JOIN")
    for r in ROLES:
        pact("GREEN", r, "decide", choice="JOIN")
    for r in ["MOBI", "AUTO", "GRID", "FLEET"]:
        pact("RED", r, "decide", choice="JOIN")

    hact("phase", phase="R3_RESULTS")
    st = hstate()
    b3 = st["teams"]["BLUE"]["rounds"]["3"]["result"]
    g3 = st["teams"]["GREEN"]["rounds"]["3"]["result"]
    r3 = st["teams"]["RED"]["rounds"]["3"]["result"]
    y3 = st["teams"]["YELLOW"]["rounds"]["3"]["result"]

    check("BLUE modulaire + remplacement : 40-21-6-2", b3["ecosystem"], 11)
    check("BLUE : BRAIN ecarte 10-1+4", b3["scores"]["BRAIN"], 13)
    check("GREEN proprietaire + BRAIN conserve : 46-21-6", g3["ecosystem"], 19)
    check("GREEN : BRAIN 10-10+14", g3["scores"]["BRAIN"], 14)
    check("RED proprietaire + remplacement : 46-12-21-8", r3["ecosystem"], 5)
    check("YELLOW abandon : standard perdu", y3["ecosystem"], -6)
    check("YELLOW : MOBI a paye les 6 points du standard", y3["scores"]["MOBI"], 4)

    # --- classement final --------------------------------------------------

    print("\nClassement final")
    hact("phase", phase="FINAL")
    st = hstate()
    tot = st["totals"]
    check("20 joueurs classes", len(tot["players"]), 20)
    ecos = tot["eco"]
    check("BLUE cumule 19+19+11", ecos["BLUE"]["total"], 49)
    check(
        "GREEN cumule -16+-17+19",
        ecos["GREEN"]["total"],
        g1["ecosystem"] + st["teams"]["GREEN"]["rounds"]["2"]["result"]["ecosystem"] + 19,
    )
    ok(
        "le classement est trie",
        all(
            tot["players"][i]["total"] >= tot["players"][i + 1]["total"]
            for i in range(len(tot["players"]) - 1)
        ),
    )

    blue_fleet = get("/api/state?token=" + players[("BLUE", "FLEET")])
    my = blue_fleet["my_total"]
    check(
        "FLEET de BLUE : total R1+R2+R3",
        my["total"],
        my["rounds"]["1"] + my["rounds"]["2"] + my["rounds"]["3"],
    )
    ok(
        "les couts prives sont reveles en fin de partie",
        blue_fleet["team"]["rounds"]["1"].get("decisions") is not None,
    )

    # --- robustesse --------------------------------------------------------

    print("\nControles de robustesse")
    res, status = post("/api/action", {"token": "faux", "action": "decide", "choice": "JOIN"})
    check("jeton inconnu rejete", status, 400)
    try:
        urllib.request.urlopen(BASE + "/api/host?cle=mauvaise", timeout=10)
        check("cle enseignant erronee rejetee", "pas d'erreur", "403")
    except urllib.error.HTTPError as e:
        check("cle enseignant erronee rejetee", e.code, 403)

    with urllib.request.urlopen(BASE + "/qr.svg?d=http://test", timeout=10) as r:
        body = r.read().decode("utf-8")
    ok("le QR est servi en SVG", body.startswith("<svg") and "path" in body)

    hact("unlock", round=3)
    st = hstate()
    check("round 3 rouvert", st["teams"]["BLUE"]["rounds"]["3"]["result"], None)
    check("architecture conservee", st["teams"]["BLUE"]["rounds"]["3"]["architecture"], "MODULAR")

    before = st["version"]
    hact("reset")
    st = hstate()
    check("nouvelle partie : plus aucun joueur", len(st["players"]), 0)
    check("nouvelle partie : retour a l'accueil", st["phase"], "LOBBY")
    ok("nouvelle partie : la version continue de croitre", st["version"] > before)
    res, status = post(
        "/api/action", {"token": players[("BLUE", "MOBI")], "action": "decide", "choice": "JOIN"}
    )
    check("les anciens jetons sont invalides", status, 400)


if __name__ == "__main__":
    main()
