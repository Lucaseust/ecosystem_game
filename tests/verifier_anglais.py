"""English campaign in a real browser, including all roles and offline charts."""

import json
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

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
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.load(response)

    def host(action):
        phase = request("/api/host?cle=english-test")["phase"]
        return request(
            "/api/host/action", {"cle": "english-test", "action": action, "expected_phase": phase}
        )

    def act(token, action, **extra):
        return request(
            "/api/action", dict(token=token, action=action, request_id=uuid.uuid4().hex, **extra)
        )

    with tempfile.TemporaryDirectory(prefix="ecosystem-english-") as folder:
        process = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "serveur.py"),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--equipes",
                "2",
                "--cle",
                "english-test",
                "--lang",
                "en",
                "--seed",
                "english-browser",
                "--donnees",
                folder,
            ],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(100):
                try:
                    info = request("/api/info")
                    break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("English server failed to start")
            assert info["language"] == "en"
            tokens = []
            for i in range(10):
                tokens.append(
                    request(
                        "/api/join", dict(code=info["code"], first_name="Nom", last_name=str(i))
                    )["token"]
                )
            players = request("/api/host?cle=english-test")["players"]
            people = {p["role"]: p for p in players if p["team"] == "BLUE"}
            errors = []
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                teacher = browser.new_page(viewport={"width": 1440, "height": 1000})
                teacher.on("pageerror", lambda e: errors.append(str(e)))
                teacher.goto(base + "/hote#cle=english-test")
                expect(teacher.locator("#advanceDate")).to_have_text("Open January →")
                assert "cle=" not in teacher.url
                teacher.locator("#enlargeQr").click()
                expect(teacher.locator("#joinDialog")).to_be_visible()
                expect(teacher.locator("#joinDialogTitle")).to_have_text("Join the game")
                expect(teacher.locator("#joinCode")).to_have_text(info["code"])
                join_url = base + "/?c=" + info["code"]
                expect(teacher.locator("#joinLink")).to_have_attribute("href", join_url)
                assert (
                    teacher.locator("#joinQr").evaluate(
                        "img => new URL(img.src).searchParams.get('d')"
                    )
                    == join_url
                )
                assert (
                    teacher.locator("#joinQr").bounding_box()["width"]
                    > 3 * teacher.locator("#qr").bounding_box()["width"]
                )
                # State polling must not close the QR or send keyboard shortcuts
                # to controls behind the modal.
                version = teacher.evaluate("H.st.version")
                host("timer_reset")
                teacher.wait_for_function("v => H.st.version > v", arg=version)
                expect(teacher.locator("#joinDialog")).to_be_visible()
                teacher.locator("#joinLink").focus()
                teacher.keyboard.press("Space")
                assert request("/api/host?cle=english-test")["timer"]["running"] is False
                teacher.keyboard.press("Escape")
                expect(teacher.locator("#joinDialog")).not_to_be_visible()
                expect(teacher.locator("#enlargeQr")).to_be_focused()
                teacher.keyboard.press("Enter")
                expect(teacher.locator("#joinDialog")).to_be_visible()
                teacher.locator("#closeJoinDialog").click()
                expect(teacher.locator("#joinDialog")).not_to_be_visible()
                for width, height in ((320, 740), (844, 390), (1440, 1000)):
                    teacher.set_viewport_size({"width": width, "height": height})
                    teacher.locator("#enlargeQr").click()
                    assert teacher.locator("#joinDialog").evaluate(
                        "d => d.scrollWidth <= d.clientWidth"
                    )
                    assert teacher.locator("#joinQr").bounding_box()["width"] <= width
                    teacher.keyboard.press("Escape")
                teacher.locator("#enlargeQr").click()
                teacher.mouse.click(4, 4)
                expect(teacher.locator("#joinDialog")).not_to_be_visible()
                pages = {}
                for role in ROLES:
                    context = browser.new_context(
                        viewport={"width": 390, "height": 844}, reduced_motion="reduce"
                    )
                    context.add_init_script(
                        "localStorage.setItem('eco_token',%s)" % json.dumps(people[role]["id"])
                    )
                    page = context.new_page()
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.goto(base)
                    expect(page.locator("html")).to_have_attribute("lang", "en")
                    expect(page.locator("#introTitle")).to_contain_text("Your mission")
                    for width in (320, 390, 768):
                        page.set_viewport_size({"width": width, "height": 844})
                        assert page.locator("#intro").evaluate("d => d.scrollWidth <= innerWidth")
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.locator("#introSkip").click()
                    expect(page.locator("#tName")).to_have_text(people[role]["name"])
                    expect(page.locator("#tTeamName")).to_have_text("BLUE")
                    expect(page.locator(".player-team-label")).to_have_text("Your team")
                    for width in (320, 390, 768):
                        page.set_viewport_size({"width": width, "height": 844})
                        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                        expect(page.locator("#tTeamName")).to_be_in_viewport()
                        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                        assert page.locator("#tTeamName").evaluate(
                            "n => n.scrollWidth <= n.clientWidth"
                        )
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.evaluate("window.scrollTo(0, 0)")
                    pages[role] = page
                green_player = next(p for p in players if p["team"] == "GREEN")
                green_context = browser.new_context(reduced_motion="reduce")
                green_context.add_init_script(
                    "localStorage.setItem('eco_token',%s)" % json.dumps(green_player["id"])
                )
                green_page = green_context.new_page()
                green_page.on("pageerror", lambda e: errors.append(str(e)))
                green_page.goto(base)
                green_page.locator("#introSkip").click()
                expect(green_page.locator("#tTeamName")).to_have_text("GREEN")
                assert (
                    green_page.locator("#tTeamName").evaluate(
                        "n => getComputedStyle(n).backgroundColor"
                    )
                    == "rgb(133, 224, 178)"
                )
                for team in ("BLUE", "GREEN"):
                    request(
                        "/api/host/action",
                        dict(
                            cle="english-test",
                            action="reassign",
                            player=green_player["id"],
                            team=team,
                            role=green_player["role"],
                        ),
                    )
                    expect(green_page.locator("#tTeamName")).to_have_text(team)
                green_context.close()
                teacher.locator("#advanceDate").click()
                for role, page in pages.items():
                    expect(page.locator(".profile-question")).to_be_visible()
                    expect(page.locator("#app")).not_to_contain_text("Votre entreprise")
                    page.locator(
                        "#profile-"
                        + {
                            "MOBI": "LOCAL",
                            "AUTO": "DEDICATED",
                            "BRAIN": "MOBILE",
                            "GRID": "BASE",
                            "FLEET": "LEAN",
                        }[role]
                    ).click()
                mobi = pages["MOBI"]
                mobi.wait_for_function("() => Object.keys(C.st.team.profiles).length === 5")
                mobi.locator("#arch-MODULAR").click()
                mobi.locator("#launch-PILOT").click()
                for role in ROLES:
                    mobi.locator("#share_" + role).fill("7.6")
                mobi.locator("#fund_MOBI").fill("9")
                expect(mobi.locator("#publishProposal")).to_have_text("Publish this proposal")
                mobi.locator("#publishProposal").click()
                for page in pages.values():
                    expect(page.locator("#acceptProposal")).to_have_text("I accept")
                    page.locator("#acceptProposal").click()
                mobi.wait_for_function("() => C.st.team.installed")
                fleet = pages["FLEET"]
                fleet.locator("#nav-table").click()
                message = "Votre entreprise, crédits, Nom <img src=x onerror=alert(1)>"
                fleet.locator("#claimText").fill(message)
                fleet.get_by_role("button", name="Post a message").click()
                expect(fleet.locator(".message-entry")).to_contain_text(message)
                assert fleet.locator(".message-entry img").count() == 0
                fleet.locator("#nav-entreprise").click()
                expect(fleet.locator("#app")).to_contain_text("Available cash")
                fleet.screenshot(
                    path=str(ROOT / "docs" / "english-company-mobile.png"), full_page=True
                )
                for next_phase in ("APRIL", "JULY", "OCTOBER", "FINAL"):
                    host("next")
                    mobi.wait_for_function("phase => C.st.phase === phase", arg=next_phase)
                    mobi.locator("#nav-situation").click()
                    receipt = mobi.locator(".quarter-receipt")
                    expect(receipt.locator("summary")).to_contain_text("credits for your company")
                    receipt.locator("summary").click()
                    amounts = mobi.evaluate("""() => {
                        const date = C.st.team.settlements.at(-1).date;
                        const rows = C.st.me.transactions.filter(r => r.economic_date === date);
                        const sum = kind => rows.filter(r => r.kind === kind).reduce((n, r) => n + r.amount, 0);
                        return [sum('REVENUE'), sum('OUTSIDE'),
                            rows.filter(r => r.amount < 0).reduce((n, r) => n + r.amount, 0),
                            rows.reduce((n, r) => n + r.amount, 0)].map(money);
                    }""")
                    for cell, amount in zip(receipt.locator("dd").all(), amounts, strict=True):
                        expect(cell).to_have_text(amount + " credits")
                    expect(receipt).not_to_contain_text("%")
                    assert receipt.evaluate("r => r.scrollWidth <= r.clientWidth")
                teacher.wait_for_function("() => H.st.phase === 'FINAL'")
                teacher.locator("#tab-brief").click()
                expect(teacher.locator(".db-views button")).to_have_count(5)
                for view in ("trajectory", "value", "actors", "contracts", "events"):
                    teacher.locator("#db-view-" + view).click()
                    expect(teacher.locator("#debriefChart svg")).to_be_visible()
                    expect(teacher.locator("#view")).not_to_contain_text("crédits")
                teacher.screenshot(path=str(ROOT / "docs" / "english-debrief.png"), full_page=True)
                with teacher.expect_download() as report:
                    teacher.locator("#exportReport").click()
                report_path = Path(folder) / "report.html"
                report.value.save_as(report_path)
                offline = browser.new_context(offline=True)
                page = offline.new_page()
                page.on("pageerror", lambda e: errors.append(str(e)))
                page.goto(report_path.as_uri())
                expect(page.locator("html")).to_have_attribute("lang", "en")
                expect(page.locator("#dbChartTitle")).to_have_text("Cumulative collective value")
                for view in ("value", "actors", "contracts", "events"):
                    page.locator("#db-view-" + view).click()
                    expect(page.locator("#debriefChart svg")).to_be_visible()
                offline.close()
                assert not errors, errors
                browser.close()
            print(
                "English verified: persistent BLUE/GREEN team badges, accessible enlarged QR, five roles, contract, literal user content, year-end and all five offline charts."
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
