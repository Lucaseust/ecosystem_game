"""Real two-player negotiation, consent, cents and disagreement over HTTP."""

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
    base = f"http://127.0.0.1:{port}"

    def request(path, body=None):
        req = urllib.request.Request(
            base + path,
            data=json.dumps(body).encode() if body else None,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.load(response)

    def act(token, action, **kw):
        return request(
            "/api/action", dict(token=token, action=action, request_id=uuid.uuid4().hex, **kw)
        )

    def advance():
        phase = request("/api/host?cle=credits-test")["phase"]
        request("/api/host/action", dict(cle="credits-test", action="next", expected_phase=phase))

    with tempfile.TemporaryDirectory(prefix="eco-credits-") as folder:
        process = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "serveur.py"),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--cle",
                "credits-test",
                "--lang",
                "fr",
                "--nouvelle",
                "--seed",
                "credits-ui",
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
                raise RuntimeError("Server did not start")
            for i in range(10):
                request("/api/join", dict(code=info["code"], first_name="Test", last_name=str(i)))
            players = request("/api/host?cle=credits-test")["players"]
            tokens = {p["role"]: p["id"] for p in players if p["team"] == "BLUE"}
            advance()
            for role, choice in dict(
                MOBI="LOCAL", AUTO="DEDICATED", BRAIN="MOBILE", GRID="BASE", FLEET="LEAN"
            ).items():
                act(tokens[role], "profile", choice=choice)
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                pages = {}
                errors = []
                for role in ["MOBI", "AUTO"]:
                    context = browser.new_context(
                        viewport={"width": 390, "height": 844}, reduced_motion="reduce"
                    )
                    context.add_init_script(
                        "localStorage.setItem('eco_token',%s);localStorage.setItem('eco_briefing_seen_v3',%s)"
                        % (json.dumps(tokens[role]), json.dumps(tokens[role]))
                    )
                    page = context.new_page()
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    page.goto(base)
                    expect(page.get_by_role("heading", name="Négocier ensemble")).to_be_visible()
                    pages[role] = page
                mobi, auto = pages["MOBI"], pages["AUTO"]
                auto.get_by_text("Publier mes conditions en crédits", exact=True).click()
                auto.locator("#minimum").fill("8.01")
                auto.locator("#maximum").fill("2.99")
                auto.locator("#positionText").fill(
                    "Je propose de financer une partie des interfaces."
                )
                auto.get_by_role("button", name="Soumettre mes conditions à la table").click()
                expect(mobi.locator(".negotiation")).to_contain_text("8,01")
                mobi.locator("#discussionTarget").select_option("AUTO")
                mobi.locator("#discussionText").fill("D’accord pour cette contribution.")
                mobi.get_by_role("button", name="Envoyer à la table", exact=True).click()
                expect(auto.locator(".negotiation")).to_contain_text("MOBI → AUTO")
                mobi.locator("#arch-MODULAR").click()
                mobi.locator("#launch-EARLY").click()
                for role, amount in dict(
                    MOBI="7.6", AUTO="8.01", BRAIN="7.6", GRID="7.6", FLEET="7.19"
                ).items():
                    mobi.locator("#share_" + role).fill(amount)
                mobi.locator("#fund_MOBI").fill("3.01")
                mobi.locator("#fund_AUTO").fill("2.99")
                expect(mobi.locator("#publishProposal")).to_be_enabled()
                mobi.locator("#publishProposal").click()
                expect(auto.locator("#acceptProposal")).to_be_visible()
                auto.locator("#decisionReason").fill("Le financement me convient.")
                auto.locator("#acceptProposal").click()
                expect(mobi.locator(".negotiation")).to_contain_text("Le financement me convient.")
                for role in ROLES:
                    if role != "AUTO":
                        act(tokens[role], "consent", choice="ACCEPT", revision=1)
                mobi.wait_for_function("C.st.team.installed")
                expect(mobi.locator(".allocation").first).to_contain_text("8,01")
                assert "%" not in mobi.locator(".allocation").first.inner_text()
                for width in [320, 390, 768]:
                    mobi.set_viewport_size({"width": width, "height": 844})
                    assert mobi.evaluate("document.documentElement.scrollWidth <= innerWidth")
                advance()
                state = request("/api/state?token=" + tokens["MOBI"])
                # The preceding signed contract must never earn anything in April.
                before = {r: request("/api/state?token=" + tokens[r])["me"]["cash"] for r in ROLES}
                assert not state["team"]["agreement_current"]
                advance()
                for role in ROLES:
                    current = request("/api/state?token=" + tokens[role])
                    assert current["me"]["cash"] == before[role]
                    assert current["team"]["settlements"][-1]["revenue"] == 0
                assert not errors, errors
                browser.close()
            print(
                "Credits verified: two-player conditions, targeted discussion, explained consent, cents, mobile layout and zero earnings without a fresh agreement."
            )
        finally:
            process.terminate()
            process.wait(timeout=10)


if __name__ == "__main__":
    verify()
