"""QA navigateur facultative (Playwright), serveur et donnees temporaires.

Lancement : python tests/verifier_parcours.py
Le serveur du cours n'est pas utilise. Captures dans docs/.
"""

import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    PORT = sock.getsockname()[1]
BASE = "http://127.0.0.1:%d" % PORT


def request(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def host(action, **extra):
    return request("/api/host/action", dict(cle="preview", action=action, **extra))


def verify():
    with tempfile.TemporaryDirectory(prefix="eco-browser-") as data:
        server = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "serveur.py"),
                "--host",
                "127.0.0.1",
                "--port",
                str(PORT),
                "--equipes",
                "2",
                "--cle",
                "preview",
                "--nouvelle",
                "--legacy",
                "--donnees",
                data,
            ],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(60):
                try:
                    info = request("/api/info")
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Le serveur temporaire n'a pas demarre")
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                errors = []
                gate = browser.new_page(
                    viewport={"width": 390, "height": 844}, device_scale_factor=1
                )
                gate.on("pageerror", lambda exc: errors.append(str(exc)))
                gate.goto(BASE)
                gate.screenshot(path=str(ROOT / "docs/accueil-mobile.png"), full_page=True)
                gate.locator("#pname").fill("Camille")
                gate.locator("#plastname").fill("Martin")
                gate.locator("#pcode").fill(info["code"])
                gate.locator("#gojoin").click()
                expect(gate.locator("#game")).to_be_visible()
                expect(gate.locator("#intro")).to_be_visible()
                gate.locator("#introPause").click()
                expect(gate.locator("#introTitle")).to_have_text(
                    "La ville attendsa première navette."
                )
                gate.screenshot(
                    path=str(ROOT / "docs/intro-contexte-mobile.png"), animations="disabled"
                )
                gate.locator("#introNext").click()
                expect(gate.locator(".intro-partners li")).to_have_count(5)
                expect(gate.locator(".intro-partners .is-you")).to_have_count(1)
                expect(gate.locator(".intro-partners li").last).to_be_visible()
                gate.screenshot(
                    path=str(ROOT / "docs/intro-roles-mobile.png"), animations="disabled"
                )
                gate.locator("#introNext").click()
                expect(gate.locator("#introText")).to_contain_text(
                    "le plus de points pour votre entreprise"
                )
                assert not any(
                    word in gate.locator("#introStage").inner_text().lower()
                    for word in ("choc", "marché", "manche 2", "manche 3")
                )
                gate.screenshot(
                    path=str(ROOT / "docs/intro-objectif-mobile.png"), animations="disabled"
                )
                gate.locator("#introNext").click()
                expect(gate.locator("#intro")).not_to_be_visible()
                gate.reload()
                expect(gate.locator("#playerNav")).to_be_visible()
                expect(gate.locator("#intro")).not_to_be_visible()
                # La relecture et le pilotage manuel n'envoient aucune action de jeu.
                gate.locator("#replayIntro").click()
                gate.clock.install()
                gate.locator("#introPause").click()
                gate.clock.fast_forward(35000)
                expect(gate.locator("#intro")).to_have_attribute("data-step", "0")
                gate.locator("#introNext").click()
                expect(gate.locator(".intro-partners li").last).to_be_visible()
                gate.locator("#introBack").click()
                gate.locator("#introPause").click()
                for duration, step in [(7000, "1"), (12500, "2")]:
                    gate.clock.fast_forward(duration)
                    expect(gate.locator("#intro")).to_have_attribute("data-step", step)
                gate.clock.fast_forward(9000)
                expect(gate.locator("#intro")).not_to_be_visible()
                people = request("/api/host?cle=preview")["players"]
                first_id = people[0]["id"]
                for i in range(9):
                    request(
                        "/api/join",
                        dict(code=info["code"], first_name="Alex", last_name="Joueur%d" % i),
                    )
                people = request("/api/host?cle=preview")["players"]
                pages = {}
                tokens = {}
                for person in people:
                    if person["team"] != "BLUE":
                        continue
                    role, token = person["role"], person["id"]
                    tokens[role] = token
                    if token == first_id:
                        page = gate
                    else:
                        context = browser.new_context(
                            viewport={"width": 390, "height": 844}, device_scale_factor=1
                        )
                        context.add_init_script(
                            "localStorage.setItem('eco_token', %s)" % json.dumps(token)
                        )
                        page = context.new_page()
                        page.on("pageerror", lambda exc: errors.append(str(exc)))
                        page.goto(BASE)
                        expect(page.locator("#intro")).to_be_visible()
                        page.locator("#introSkip").click()
                    expect(page.locator("#playerNav")).to_be_visible()
                    pages[role] = page

                mobi, fleet = pages["MOBI"], pages["FLEET"]
                # Avec la reduction des animations, la lecture est manuelle par defaut.
                quiet = browser.new_context(
                    viewport={"width": 320, "height": 640}, reduced_motion="reduce"
                )
                quiet.add_init_script(
                    "localStorage.setItem('eco_token', %s)" % json.dumps(tokens["FLEET"])
                )
                quiet_page = quiet.new_page()
                quiet_page.on("pageerror", lambda exc: errors.append(str(exc)))
                quiet_page.goto(BASE)
                expect(quiet_page.locator("#intro")).to_be_visible()
                expect(quiet_page.locator("#introPause")).to_have_attribute("aria-pressed", "true")
                for _ in range(3):
                    assert quiet_page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                    expect(quiet_page.locator("#introNext")).to_be_in_viewport()
                    quiet_page.locator("#introNext").click()
                expect(quiet_page.locator("#intro")).not_to_be_visible()
                quiet_page.locator("#replayIntro").click()
                quiet_page.keyboard.press("Escape")
                expect(quiet_page.locator("#intro")).not_to_be_visible()
                quiet.close()
                phases = [
                    "LOBBY",
                    "R1_NEGO",
                    "R1_DECIDE",
                    "R1_RESULTS",
                    "R2_NEGO",
                    "R2_DECIDE",
                    "R2_RESULTS",
                    "MARKET",
                    "R3_ARCH",
                    "R3_SHOCK",
                    "R3_NEGO",
                    "R3_DECIDE",
                    "R3_RESULTS",
                    "FINAL",
                    "DEBRIEF",
                ]
                for phase in phases:
                    host("phase", phase=phase)
                    for role, page in pages.items():
                        page.wait_for_function("phase => S.st?.phase === phase", arg=phase)
                        for tab in ("entreprise", "table", "situation"):
                            page.locator("#nav-" + tab).click()
                            expect(page.locator("#nav-" + tab)).to_have_attribute(
                                "aria-current", "page"
                            )
                            assert page.locator("#app").inner_text().strip(), (phase, role, tab)
                            assert page.evaluate(
                                "document.documentElement.scrollWidth <= innerWidth"
                            ), (phase, role, tab, "debordement")
                        assert not page.locator(".session-rail").count()
                        if phase == "LOBBY":
                            assert not any(
                                word in page.locator("#app").inner_text().lower()
                                for word in ("choc", "architecture", "marché", "round 2", "round 3")
                            )
                    if phase == "R1_NEGO":
                        fleet.locator("#nav-table").click()
                        expect(fleet.locator("#claimAmt")).to_have_count(0)
                        fleet.locator("#claimTxt").fill("Cette offre ne me convainc pas")
                        # Une saisie survit aux notifications de l'equipe et aux changements d'onglet.
                        host("timer_add", seconds=60)
                        fleet.locator("#nav-entreprise").click()
                        fleet.locator("#nav-table").click()
                        expect(fleet.locator("#claimTxt")).to_have_value(
                            "Cette offre ne me convainc pas"
                        )
                        fleet.get_by_role("button", name="Prendre la parole").click()
                        fleet.locator("#nav-situation").click()
                        expect(
                            fleet.get_by_role("button", name="À renégocier", exact=True)
                        ).to_have_count(0)
                        fleet.get_by_role("button", name="Réservé", exact=True).click()
                        fleet.wait_for_function(
                            "() => S.st.team.rounds['1'].signals.FLEET === 'DISCUSS'"
                        )
                    if phase == "R1_DECIDE":
                        fleet.get_by_role("button", name="Je me retire").click()
                        fleet.wait_for_function("() => S.st.me.decision === 'OUT'")
                        fleet.get_by_role("button", name="Je participe").click()
                        fleet.wait_for_function("() => S.st.me.decision === 'JOIN'")
                    if phase == "R2_NEGO":
                        for role, value in dict(MOBI=6, AUTO=9, BRAIN=9, GRID=6, FLEET=10).items():
                            mobi.locator("#c_" + role).fill(str(value))
                        mobi.get_by_role("button", name="Publier le contrat").click()
                        fleet.wait_for_function(
                            "() => S.st.team.rounds['2'].contract?.FLEET === 10"
                        )
                        fleet.screenshot(
                            path=str(ROOT / "docs/negociation-mobile.png"),
                            full_page=True,
                            style=".toast { visibility: hidden; }",
                        )
                        fleet.locator("#nav-entreprise").click()
                        fleet.screenshot(
                            path=str(ROOT / "docs/dossier-mobile.png"),
                            full_page=True,
                            style=".toast { visibility: hidden; }",
                        )
                        assert "Revenu minimum" not in fleet.locator("#app").inner_text()
                        fleet.locator("#nav-table").click()
                        fleet.screenshot(
                            path=str(ROOT / "docs/table-mobile.png"),
                            full_page=True,
                            style=".toast { visibility: hidden; }",
                        )
                    if phase == "R3_ARCH":
                        assert not any(
                            word in mobi.locator("#app").inner_text()
                            for word in ("ALT-AI", "AI FAILURE", "−12")
                        )
                        fleet.locator("#nav-entreprise").click()
                        fleet.once("dialog", lambda dialog: dialog.accept())
                        fleet.get_by_role("button", name="UTILISER MON POUVOIR").click()
                        mobi.wait_for_function("() => S.st.team.veto")
                        expect(
                            mobi.get_by_role("button", name="INTÉGRÉE", exact=True)
                        ).to_be_disabled()
                        mobi.get_by_role("button", name="MODULAIRE", exact=True).click()
                        mobi.locator("#s_MOBI").fill("6")
                        mobi.get_by_role("button", name="Publier l’architecture").click()
                        mobi.wait_for_function(
                            "() => S.st.team.rounds['3'].architecture === 'MODULAR'"
                        )
                    if phase == "R3_SHOCK":
                        host("shock", shock="AI_FAILURE")
                    if phase == "R3_NEGO":
                        mobi.wait_for_function("() => S.st.shock === 'AI_FAILURE'")
                        mobi.get_by_role("button", name="Garder BRAIN", exact=True).click()
                        for role, value in dict(MOBI=6, AUTO=9, BRAIN=9, GRID=6, FLEET=10).items():
                            mobi.locator("#r_" + role).fill(str(value))
                        mobi.get_by_role("button", name="Publier la solution").click()
                        mobi.wait_for_function("() => S.st.team.rounds['3'].resolution === 'KEEP'")
                    print("OK", phase, "5 roles / 3 rubriques", flush=True)
                # Ecrans etroits et larges, dont les classements de fin de partie.
                for width in (320, 768, 1280):
                    mobi.set_viewport_size({"width": width, "height": 844})
                    for tab in ("situation", "entreprise", "table"):
                        mobi.locator("#nav-" + tab).click()
                        assert mobi.evaluate(
                            "document.documentElement.scrollWidth <= innerWidth"
                        ), (width, tab)
                # Les branches ou les partenaires necessaires changent ont leur propre ecran.
                for shock, resolution, target, integration in [
                    ("AI_FAILURE", "REPLACE", "BRAIN", 2),
                    ("INFRA_FAILURE", "REPLACE", "GRID", 4),
                    ("REGULATION", "KEEP", None, 3),
                    ("AI_FAILURE", "ABANDON", None, 0),
                ]:
                    host("phase", phase="R3_SHOCK")
                    host("shock", shock=shock)
                    host("unlock", round=3)
                    host("phase", phase="R3_NEGO")
                    mobi.reload()
                    mobi.wait_for_function("() => S.st?.phase === 'R3_NEGO'")
                    mobi.evaluate("choice => pickRes(choice)", resolution)
                    if resolution != "ABANDON":
                        roles = [r for r in pages if r != target] + (["ALT_AI"] if target else [])
                        for role in roles:
                            mobi.locator("#r_" + role).fill("8")
                        mobi.locator("#i_MOBI").fill(str(integration))
                    mobi.get_by_role("button", name="Publier la solution").click()
                    mobi.wait_for_function(
                        "choice => S.st.team.rounds['3'].resolution === choice", arg=resolution
                    )
                    for phase in ("R3_DECIDE", "R3_RESULTS"):
                        host("phase", phase=phase)
                        for role, page in pages.items():
                            page.wait_for_function("phase => S.st?.phase === phase", arg=phase)
                            expect(page.locator("#app")).not_to_be_empty()
                            if phase == "R3_DECIDE":
                                assert page.locator(".choice-pair").count() == (
                                    0 if role == target or resolution == "ABANDON" else 1
                                )
                    print("OK", shock, resolution, "votes et resultats des 5 roles", flush=True)
                assert not errors, errors
                browser.close()
                print(
                    "Parcours mobile verifie, 225 ecrans, saisies, annonces, intentions, votes et publications."
                )
        finally:
            server.terminate()
            server.wait(timeout=10)


if __name__ == "__main__":
    verify()
