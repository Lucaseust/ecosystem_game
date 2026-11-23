"""Verification HTTP et navigateur de la campagne, donnees et serveur temporaires."""

import hashlib
import io
import csv
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import urllib.error
import uuid
import zipfile
import xml.etree.ElementTree as ET

from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ROLES = ["MOBI", "AUTO", "BRAIN", "GRID", "FLEET"]


def verify():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = "http://127.0.0.1:%d" % port

    def request(path, body=None):
        req = urllib.request.Request(
            base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.load(response)

    def host(action, **kw):
        if action == "next":
            kw["expected_phase"] = request("/api/host?cle=preview")["phase"]
        return request("/api/host/action", dict(cle="preview", action=action, **kw))

    def act(token, action, **kw):
        return request(
            "/api/action", dict(token=token, action=action, request_id=uuid.uuid4().hex, **kw)
        )

    def draw(seed, team, date, channel):
        return (
            int.from_bytes(
                hashlib.sha256("|".join([seed, team, date, channel]).encode()).digest()[:8], "big"
            )
            / 2**64
        )

    seed = next(
        "browser-%d" % i
        for i in range(1000000)
        if 0.8 <= draw("browser-%d" % i, "BLUE", "APRIL", "external_event") < 0.9
        and 0.15 <= draw("browser-%d" % i, "GREEN", "APRIL", "external_event") < 0.30
        and 0.30 <= draw("browser-%d" % i, "BLUE", "JULY", "external_event") < 0.45
        and draw("browser-%d" % i, "BLUE", "JANUARY", "commissioning") >= 0.25
        and 0.45 <= draw("browser-%d" % i, "GREEN", "JULY", "external_event") < 0.65
        and draw("browser-%d" % i, "GREEN", "JULY", "event_target") >= 2 / 3
        and 0.65 <= draw("browser-%d" % i, "GREEN", "OCTOBER", "external_event") < 0.8
    )
    with tempfile.TemporaryDirectory(prefix="eco-campaign-browser-") as folder:
        process = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "serveur.py"),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--equipes",
                "4",
                "--cle",
                "preview",
                "--nouvelle",
                "--seed",
                seed,
                "--donnees",
                folder,
            ],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(70):
                try:
                    info = request("/api/info")
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Le serveur de campagne n'a pas demarre")
            assert request("/api/host?cle=preview")["schema"] == "campaign-2.0"
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                errors = []
                gate = browser.new_page(viewport={"width": 390, "height": 844})
                gate.on("pageerror", lambda e: errors.append(str(e)))
                gate.goto(base)
                gate.screenshot(path=str(ROOT / "docs/accueil-mobile.png"), full_page=True)
                gate.locator("#pname").fill("Camille")
                gate.locator("#plastname").fill("Martin")
                gate.locator("#pcode").fill(info["code"])
                gate.locator("#gojoin").click()
                expect(gate.locator("#intro")).to_be_visible()
                gate.locator("#introPause").click()
                expect(gate.locator("#introText")).to_contain_text("navettes sans chauffeur")
                gate.screenshot(
                    path=str(ROOT / "docs/intro-contexte-mobile.png"), animations="disabled"
                )
                gate.locator("#introNext").click()
                expect(gate.locator(".intro-partners li")).to_have_count(5)
                gate.screenshot(
                    path=str(ROOT / "docs/intro-roles-mobile.png"), animations="disabled"
                )
                gate.locator("#introNext").click()
                expect(gate.locator("#introText")).to_contain_text("résultat financier annuel")
                expect(gate.locator(".intro-capital")).to_contain_text("20")
                gate.screenshot(
                    path=str(ROOT / "docs/intro-objectif-mobile.png"), animations="disabled"
                )
                gate.locator("#introNext").click()
                expect(gate.locator("#introStage")).to_contain_text(
                    "toutes les entreprises concernées acceptent"
                )
                expect(gate.locator(".intro-signals > span")).to_have_count(5)
                expect(gate.locator("#introReadHint")).to_be_visible()
                gate.locator("#introStage").evaluate("s=>s.scrollTop=s.scrollHeight")
                expect(gate.locator("#introReadHint")).not_to_be_visible()
                expect(gate.locator(".intro-emphasis")).to_be_in_viewport()
                gate.locator("#introStage").evaluate("s=>s.scrollTop=0")
                gate.screenshot(
                    path=str(ROOT / "docs/intro-accords-mobile.png"), animations="disabled"
                )
                gate.locator("#introNext").click()
                expect(gate.locator("#introStage")).to_contain_text(
                    "Un groupe sans accord ne bloque pas les autres"
                )
                expect(gate.locator("#introText")).to_contain_text("L’enseignant clôt le trimestre")
                gate.screenshot(
                    path=str(ROOT / "docs/intro-calendrier-mobile.png"), animations="disabled"
                )
                gate.locator("#introNext").click()
                expect(gate.locator("#introStage")).to_contain_text(
                    "les frais d’exploitation engagée restent dus"
                )
                expect(gate.locator(".intro-progress > span")).to_have_count(6)
                gate.screenshot(
                    path=str(ROOT / "docs/intro-consequences-mobile.png"), animations="disabled"
                )
                for width in [320, 390, 768]:
                    gate.set_viewport_size({"width": width, "height": 844})
                    for step in range(5, -1, -1):
                        assert gate.locator("#intro").evaluate("d=>d.scrollWidth <= innerWidth"), (
                            width,
                            step,
                        )
                        assert gate.locator("#introStage").evaluate(
                            "s=>s.scrollWidth <= s.clientWidth"
                        ), (width, step, "contenu")
                        if step:
                            gate.locator("#introBack").click()
                    for _ in range(5):
                        gate.locator("#introNext").click()
                gate.set_viewport_size({"width": 390, "height": 844})
                gate.locator("#introNext").click()
                gate.reload()
                expect(gate.locator("#playerNav")).to_be_visible()
                expect(gate.locator("#intro")).not_to_be_visible()
                expect(gate.locator(".fleet-map")).to_be_visible()
                expect(gate.locator(".fleet-map figcaption")).to_contain_text("Flotte à constituer")
                gate.screenshot(path=str(ROOT / "docs/flotte-mobile.png"), full_page=True)
                for i in range(19):
                    request(
                        "/api/join",
                        dict(code=info["code"], first_name="Alex", last_name="Joueur%d" % i),
                    )
                people = request("/api/host?cle=preview")["players"]
                tokens = {(p["team"], p["role"]): p["id"] for p in people}
                assert len(tokens) == 20
                pages = {}
                for role in ROLES:
                    token = tokens["BLUE", role]
                    if role == "MOBI":
                        page = gate
                    else:
                        context = browser.new_context(viewport={"width": 390, "height": 844})
                        context.add_init_script(
                            "localStorage.setItem('eco_token',%s)" % json.dumps(token)
                        )
                        page = context.new_page()
                        page.on("pageerror", lambda e: errors.append(str(e)))
                        page.goto(base)
                        expect(page.locator("#intro")).to_be_visible()
                        page.locator("#introSkip").click()
                    pages[role] = page
                teacher = browser.new_page(viewport={"width": 1440, "height": 1000})
                teacher.on("pageerror", lambda e: errors.append(str(e)))
                teacher.goto(base + "/hote?cle=preview")
                teacher.wait_for_function("() => H.st && H.st.schema === 'campaign-2.0'")
                teacher.locator("#enlargeQr").click()
                expect(teacher.locator("#joinDialogTitle")).to_have_text("Rejoindre la partie")
                expect(teacher.locator("#joinCode")).to_have_text(info["code"])
                teacher.locator("#closeJoinDialog").click()
                expect(teacher.locator("#joinDialog")).not_to_be_visible()
                expect(gate.locator("#tTeamName")).to_have_text("BLUE")
                expect(gate.locator(".player-team-label")).to_have_text("Votre équipe")
                teacher.locator("#advanceDate").click()
                try:
                    request(
                        "/api/host/action",
                        dict(cle="preview", action="next", expected_phase="LOBBY"),
                    )
                    raise AssertionError("Une clôture périmée a été acceptée")
                except urllib.error.HTTPError as error:
                    assert error.code == 400
                    error.close()
                assert request("/api/host?cle=preview")["phase"] == "JANUARY"
                assert request("/api/host?cle=preview")["debrief"] is None
                for url, code in [
                    ("/api/debrief?cle=preview", 400),
                    ("/api/debrief?cle=invalide", 403),
                ]:
                    try:
                        request(url)
                        raise AssertionError("Rapport accessible avant autorisation/clôture")
                    except urllib.error.HTTPError as error:
                        assert error.code == code
                        error.close()
                expect(teacher.locator("#advanceHint")).to_contain_text(
                    "sans accord dans tous les groupes"
                )
                expect(teacher.locator(".date-overview")).to_contain_text(
                    "La date peut avancer pour tous"
                )
                for role, page in pages.items():
                    page.wait_for_function("() => C.st && C.st.phase === 'JANUARY'")
                    expect(page.locator(".profile-question")).to_be_visible()
                    expect(page.locator(".option-effects")).to_have_count(2)
                    if role == "MOBI":
                        expect(page.locator("#app")).to_contain_text(
                            "2 crédits s’ajoutent aux recettes trimestrielles"
                        )
                        expect(page.locator("#app")).to_contain_text(
                            "reçoit sa part des recettes ajoutées"
                        )
                        page.screenshot(
                            path=str(ROOT / "docs/choix-engagement-mobile.png"), full_page=True
                        )
                    choice = {
                        "MOBI": "LOCAL",
                        "AUTO": "DEDICATED",
                        "BRAIN": "MOBILE",
                        "GRID": "RESERVE",
                        "FLEET": "PREPARED",
                    }[role]
                    page.locator("#profile-" + choice).click()
                mobi = pages["MOBI"]
                mobi.wait_for_function("() => Object.keys(C.st.team.profiles).length === 5")
                mobi.locator("#arch-MODULAR").click()
                mobi.locator("#launch-EARLY").click()
                for role in ROLES:
                    mobi.locator("#share_" + role).fill("7.6")
                mobi.locator("#fund_MOBI").fill("6")
                expect(mobi.locator("#publishProposal")).to_be_enabled()
                mobi.locator("#publishProposal").click()
                for page in pages.values():
                    page.wait_for_function("() => C.st.team.proposal?.status === 'OPEN'")
                pages["FLEET"].screenshot(
                    path=str(ROOT / "docs/negociation-mobile.png"),
                    full_page=True,
                    style=".toast{visibility:hidden}",
                )
                for page in pages.values():
                    page.locator("#acceptProposal").click()
                for page in pages.values():
                    page.wait_for_function("() => C.st.team.installed")
                expect(mobi.locator("#requestRenegotiation")).to_be_visible()
                pages["FLEET"].locator("#nav-entreprise").click()
                pages["FLEET"].screenshot(
                    path=str(ROOT / "docs/dossier-mobile.png"),
                    full_page=True,
                    style=".toast{visibility:hidden}",
                )
                pages["FLEET"].locator("#nav-table").click()
                pages["FLEET"].locator("#claimText").fill(
                    "Nous souhaitons discuter des capacités supplémentaires."
                )
                expect(pages["FLEET"].locator(".ecosystem-node")).to_have_count(5)
                pages["FLEET"].locator("#role-map-BRAIN").click()
                expect(pages["FLEET"].locator("#role-map-BRAIN")).to_have_attribute(
                    "aria-pressed", "true"
                )
                expect(pages["FLEET"].locator("#role-insight")).to_contain_text(
                    "intelligence artificielle"
                )
                expect(pages["FLEET"].locator("#claimText")).to_have_value(
                    "Nous souhaitons discuter des capacités supplémentaires."
                )
                pages["FLEET"].screenshot(
                    path=str(ROOT / "docs/carte-ecosysteme-mobile.png"),
                    full_page=True,
                    style=".toast{visibility:hidden}",
                )
                pages["FLEET"].get_by_role("button", name="Prendre la parole").click()
                pages["FLEET"].screenshot(
                    path=str(ROOT / "docs/table-mobile.png"),
                    full_page=True,
                    style=".toast{visibility:hidden}",
                )
                # Une seconde trajectoire reelle, avec un autre choix d'interfaces.
                for role in ROLES:
                    act(
                        tokens["GREEN", role],
                        "profile",
                        choice={
                            "MOBI": "LOCAL",
                            "AUTO": "DEDICATED",
                            "BRAIN": "MOBILE",
                            "GRID": "BASE",
                            "FLEET": "LEAN",
                        }[role],
                    )
                act(
                    tokens["GREEN", "MOBI"],
                    "propose",
                    kind="INSTALL",
                    architecture="INTEGRATED",
                    launch="EARLY",
                    allocations={r: 800 for r in ROLES},
                    funding={},
                )
                for role in ROLES:
                    act(tokens["GREEN", role], "consent", choice="ACCEPT", revision=1)
                teacher.once("dialog", lambda d: d.accept())
                teacher.locator("#advanceDate").click()
                for page in pages.values():
                    page.wait_for_function("() => C.st.phase === 'APRIL'")
                mobi.locator("#nav-situation").click()
                mobi.wait_for_function("() => C.st.team.node === 'INCIDENT'")
                state = request("/api/host?cle=preview")
                assert state["teams"]["GREEN"]["node"] == "DEMAND"
                assert state["teams"]["RED"]["node"] == "FOUNDING"
                assert state["teams"]["BLUE"]["settlements"][-1]["revenue"] > 0
                assert state["teams"]["RED"]["settlements"][-1]["revenue"] == 0
                red_context = browser.new_context(
                    viewport={"width": 390, "height": 844}, reduced_motion="reduce"
                )
                red_context.add_init_script(
                    "localStorage.setItem('eco_token',%s)" % json.dumps(tokens["RED", "MOBI"])
                )
                red_page = red_context.new_page()
                red_page.on("pageerror", lambda e: errors.append(str(e)))
                red_page.goto(base)
                expect(red_page.locator("#introPause")).to_have_attribute("aria-pressed", "true")
                red_page.locator("#introSkip").click()
                expect(red_page.locator(".quarter-status")).to_contain_text("Il reste 3 trimestres")
                red_page.locator(".quarter-receipt summary").click()
                expect(red_page.locator(".quarter-receipt")).to_contain_text(
                    "Sans accord unanime pour ce tour"
                )
                red_page.screenshot(
                    path=str(ROOT / "docs/territoire-sans-accord-mobile.png"),
                    full_page=True,
                    animations="disabled",
                )
                expect(mobi.locator(".quarter-status")).to_contain_text("Trimestre 2 / 4")
                # Le remplacement ne facture pas GRID et lui laisse un parcours de retour.
                if not mobi.locator(".proposal-editor").evaluate("el=>el.open"):
                    mobi.get_by_text("Préparer une proposition · MOBI", exact=True).click()
                mobi.locator("#plan-REPLACE").click()
                mobi.locator("#share_ALT").fill("7.6")
                mobi.locator("#fund_MOBI").fill("1")
                mobi.locator("#publishProposal").click()
                mobi.wait_for_function(
                    "() => C.st.team.proposal.status === 'OPEN' && C.st.team.proposal.kind === 'REPLACE'"
                )
                for role, page in pages.items():
                    page.locator("#nav-situation").click()
                    if role != "GRID":
                        page.locator("#acceptProposal").click()
                grid = pages["GRID"]
                grid.wait_for_function("() => C.st.me.outside_position")
                expect(grid.locator("#acceptProposal")).to_have_count(0)
                grid.locator("#nav-table").click()
                expect(grid.locator("#role-map-GRID")).to_have_attribute(
                    "data-status", "substitute"
                )
                grid.locator("#role-map-GRID").click()
                expect(grid.locator("#role-insight")).to_contain_text("fournisseur extérieur")
                grid.locator("#nav-situation").click()
                grid.locator("#requestReturn").click()
                mobi.wait_for_function("() => C.st.team.return_request === 'GRID'")
                mobi.locator("#plan-RETURN").click()
                mobi.locator("#publishProposal").click()
                for page in pages.values():
                    page.wait_for_function(
                        "() => C.st.team.proposal.status === 'OPEN' && C.st.team.proposal.kind === 'RETURN'"
                    )
                    page.locator("#acceptProposal").click()
                grid.wait_for_function("() => !C.st.me.outside_position")
                teacher.screenshot(path=str(ROOT / "docs/tableau-enseignant.png"), full_page=True)
                host("next")
                # La hausse privée de FLEET ouvre une vraie négociation, sans révéler son montant.
                green_context = browser.new_context(viewport={"width": 390, "height": 844})
                green_context.add_init_script(
                    "localStorage.setItem('eco_token',%s);localStorage.setItem('eco_briefing_seen_v3',%s)"
                    % (json.dumps(tokens["GREEN", "FLEET"]), json.dumps(tokens["GREEN", "FLEET"]))
                )
                green_fleet = green_context.new_page()
                green_fleet.on("pageerror", lambda e: errors.append(str(e)))
                green_fleet.goto(base)
                green_fleet.wait_for_function(
                    "() => C.st?.phase === 'JULY' && C.st.me.private_shock"
                )
                expect(green_fleet.locator(".cost-change")).to_be_visible()
                expect(green_fleet.locator("#app h1")).to_contain_text(
                    "Votre activité coûte plus cher"
                )
                expect(green_fleet.locator("#app > .fleet-map")).to_have_count(0)
                for width in [320, 390, 768]:
                    green_fleet.set_viewport_size({"width": width, "height": 844})
                    assert green_fleet.evaluate(
                        "document.documentElement.scrollWidth <= innerWidth"
                    )
                green_fleet.set_viewport_size({"width": 390, "height": 844})
                green_fleet.screenshot(
                    path=str(ROOT / "docs/choc-prive-mobile.png"),
                    full_page=True,
                    animations="disabled",
                    style=".toast{visibility:hidden}",
                )
                green_fleet.locator("#requestRenegotiation").click()
                green_fleet.wait_for_function("() => C.st.team.renegotiation_requests.FLEET")
                green_other = request("/api/state?token=" + tokens["GREEN", "MOBI"])
                assert green_other["me"]["private_shock"] is None
                assert "cost_shocks" not in green_other["team"]
                assert "FLEET" in green_other["team"]["renegotiation_requests"]
                green_fleet.once("dialog", lambda d: d.accept())
                green_fleet.locator("#withdrawCapacity").click()
                green_fleet.wait_for_function("() => C.st.team.missing === 'FLEET'")
                green_fleet.locator("#requestReturn").click()
                green_fleet.wait_for_function("() => C.st.team.return_request === 'FLEET'")
                act(
                    tokens["GREEN", "MOBI"],
                    "propose",
                    kind="RETURN",
                    allocations=dict(MOBI=600, AUTO=800, BRAIN=800, GRID=800, FLEET=1000),
                    funding={},
                )
                for role in ROLES:
                    act(tokens["GREEN", role], "consent", choice="ACCEPT", revision=2)
                green_fleet.wait_for_function(
                    "() => C.st.team.operating && C.st.team.contract.revision === 2"
                )
                assert (
                    request("/api/host?cle=preview")["teams"]["GREEN"]["contract"]["allocations"][
                        "FLEET"
                    ]
                    == 1000
                )
                brain = pages["BRAIN"]
                brain.wait_for_function("() => C.st.phase === 'JULY' && C.st.me.can_leave")
                brain.once("dialog", lambda d: d.accept())
                brain.locator("#leaveCompany").click()
                brain.wait_for_function("() => C.st.me.outside_position")
                brain.locator("#nav-table").click()
                expect(brain.locator("#role-map-BRAIN")).to_have_attribute("data-status", "missing")
                brain.locator("#nav-situation").click()
                mobi.wait_for_function("() => C.st.team.missing === 'BRAIN'")
                mobi.locator("#plan-REPLACE").click()
                # L'ancien brouillon avait GRID ; la nouvelle position a sa propre repartition.
                for role in ["MOBI", "AUTO", "GRID", "FLEET", "ALT"]:
                    mobi.locator("#share_" + role).fill("7.6")
                mobi.locator("#fund_MOBI").fill("1")
                mobi.locator("#publishProposal").click()
                for role, page in pages.items():
                    page.locator("#nav-situation").click()
                    if role != "BRAIN":
                        page.wait_for_function("() => C.st.team.proposal.status === 'OPEN'")
                        page.locator("#acceptProposal").click()
                mobi.wait_for_function("() => C.st.team.replaced === 'BRAIN'")
                host("next")
                green_fleet.wait_for_function(
                    "() => C.st.phase === 'OCTOBER' && C.st.team.node === 'REVENUE_PRESSURE'"
                )
                expect(green_fleet.locator("#app")).to_contain_text("Moins de crédits à répartir")
                expect(green_fleet.locator("#app")).to_contain_text(
                    "Accord précédent · à renégocier pour ce tour"
                )
                expect(green_fleet.locator("#app")).to_contain_text("La baisse de contribution")
                green_fleet.screenshot(
                    path=str(ROOT / "docs/choc-territoire-mobile.png"),
                    full_page=True,
                    animations="disabled",
                    style=".toast{visibility:hidden}",
                )
                host("next")
                for role, page in pages.items():
                    page.wait_for_function("() => C.st.phase === 'FINAL'")
                    for width in [320, 390, 768]:
                        page.set_viewport_size({"width": width, "height": 844})
                        for tab in ["situation", "entreprise", "table"]:
                            page.locator("#nav-" + tab).click()
                            assert page.evaluate(
                                "document.documentElement.scrollWidth <= innerWidth"
                            ), (role, width, tab)
                            assert page.locator("#app").inner_text().strip()
                    assert "round" not in page.locator("#app").inner_text().lower()
                end = request("/api/host?cle=preview")
                assert len(end["teams"]["RED"]["settlements"]) == 4
                assert len(end["teams"]["BLUE"]["settlements"]) == 4
                assert all(s["revenue"] == 0 for s in end["teams"]["RED"]["settlements"])
                assert end["teams"]["BLUE"]["revenue"] > 0
                teacher.locator("#tab-brief").click()
                teacher.wait_for_function("() => H.st.can_export")
                expect(teacher.locator(".db-views button")).to_have_count(5)
                expect(teacher.locator("#debriefMetric")).to_be_visible()
                for metric in ["revenue", "company_result", "created"]:
                    teacher.locator("#debriefMetric").select_option(metric)
                    expect(teacher.locator("#debriefChart svg")).to_be_visible()
                teacher.locator("#debriefTeam").select_option("GREEN")
                teacher.locator("#debriefProjection").click()
                expect(teacher.locator(".host-head")).not_to_be_visible()
                for view in ["trajectory", "value", "actors", "contracts", "events"]:
                    teacher.locator("#db-view-" + view).click()
                    expect(teacher.locator("#debriefChart svg")).to_be_visible()
                    assert teacher.locator("#debriefChart svg").get_attribute("viewBox")
                    with teacher.expect_download() as graphic:
                        teacher.locator("#downloadChart").click()
                    xml = ET.parse(graphic.value.path())
                    assert xml.getroot().tag.endswith("svg")
                    assert xml.getroot().find("{http://www.w3.org/2000/svg}style") is not None
                    with teacher.expect_download() as chart_data:
                        teacher.locator("#downloadChartCSV").click()
                    with open(chart_data.value.path(), encoding="utf-8-sig", newline="") as stream:
                        assert len(list(csv.reader(stream, delimiter=";"))) > 1
                    teacher.screenshot(
                        path=str(ROOT / ("docs/debrief-" + view + ".png")),
                        full_page=True,
                        animations="disabled",
                    )
                teacher.locator("#db-view-trajectory").click()
                teacher.locator(".db-point").first.focus()
                teacher.keyboard.press("Enter")
                expect(teacher.locator("#db-view-events")).to_have_attribute("aria-pressed", "true")
                expect(teacher.locator("#dbEventsDetails")).to_be_visible()
                teacher.locator("#debriefTeam").select_option("RED")
                teacher.locator("#db-view-contracts").click()
                expect(teacher.locator("#debriefChart")).to_contain_text("Aucun accord")
                for width in [390, 768, 1440]:
                    teacher.set_viewport_size({"width": width, "height": 1000})
                    for view in ["trajectory", "value", "actors", "contracts", "events"]:
                        teacher.locator("#db-view-" + view).click()
                        assert teacher.locator(".debrief").evaluate(
                            "n=>n.scrollWidth<=n.clientWidth"
                        ), (width, view)
                teacher.locator("#debriefTeam").select_option("GREEN")
                teacher.locator("#db-view-events").click()
                teacher.locator("#debriefProjection").click()
                expect(teacher.locator(".host-head")).to_be_visible()
                with teacher.expect_download() as report_download:
                    teacher.locator("#exportReport").click()
                report_path = Path(folder) / "rapport-debrief.html"
                report_download.value.save_as(report_path)
                report_text = report_path.read_text(encoding="utf-8")
                for token in tokens.values():
                    assert token not in report_text
                offline_context = browser.new_context(
                    offline=True, viewport={"width": 1280, "height": 900}
                )
                offline_page = offline_context.new_page()
                offline_page.on("pageerror", lambda e: errors.append(str(e)))
                offline_page.goto(report_path.as_uri())
                expect(offline_page.locator(".db-views button")).to_have_count(5)
                assert (
                    offline_page.evaluate("getComputedStyle(document.body).backgroundColor")
                    == "rgb(16, 25, 32)"
                )
                offline_page.locator("#debriefTeam").select_option("GREEN")
                offline_page.locator("#db-view-actors").click()
                expect(offline_page.locator("#dbChartTitle")).to_contain_text("GREEN")
                offline_context.close()
                with teacher.expect_download() as download:
                    teacher.locator("#exportData").click()
                with zipfile.ZipFile(download.value.path()) as archive:
                    assert len(archive.namelist()) == 8
                    data = archive.read("journal.jsonl").decode()
                    assert "partner_left" in data and "contract_committed" in data
                    assert (
                        "capacity_withdrawn" in data
                        and "renegotiation_requested" in data
                        and "shock_applied" in data
                    )
                    metadata = json.loads(archive.read("metadata.json"))
                    assert metadata["rules_version"] == "campaign-3.0"
                    draws = list(
                        csv.DictReader(io.StringIO(archive.read("tirages.csv").decode("utf-8-sig")))
                    )
                    assert any(d["selected"] == "PRIVATE_COST" for d in draws)
                    assert any(d["selected"] == "PRICE_DROP" for d in draws)
                    for token in tokens.values():
                        assert token not in data
                    states = list(
                        csv.DictReader(io.StringIO(archive.read("etats.csv").decode("utf-8-sig")))
                    )
                    assert "cash_MOBI" in states[0]
                    contracts = list(
                        csv.DictReader(
                            io.StringIO(archive.read("contrats.csv").decode("utf-8-sig"))
                        )
                    )
                    assert "revenue_credits" in contracts[0] and "funding" in contracts[0]
                teacher.screenshot(
                    path=str(ROOT / "docs/trajectoires-enseignant.png"), full_page=True
                )
                assert not errors, errors
                browser.close()
            # Verifie la reprise exacte du bilan et des acteurs par un nouveau processus.
            before = request("/api/host?cle=preview")
            host("shutdown")
            process.wait(timeout=10)
            process = subprocess.Popen(
                [
                    sys.executable,
                    str(ROOT / "serveur.py"),
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--equipes",
                    "4",
                    "--cle",
                    "preview",
                    "--donnees",
                    folder,
                ],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            for _ in range(70):
                try:
                    after = request("/api/host?cle=preview")
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("La reprise n'a pas demarre")
            assert after["phase"] == "FINAL" and after["code"] == before["code"]
            assert after["teams"]["BLUE"]["cash"] == before["teams"]["BLUE"]["cash"]
            print(
                "Campagne verifiee : 20 joueurs, 4 territoires, 5 interfaces mobiles, incidents, hausse privée, renégociation, retrait, retour, baisse collective des recettes, bilan, export et reprise."
            )
        finally:
            if process.poll() is None:
                try:
                    host("shutdown")
                    process.wait(timeout=10)
                except Exception:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    verify()
