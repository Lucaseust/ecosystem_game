"""Capture real, bilingual documentation screenshots using isolated demo games.

Requires the optional Playwright development package and Chromium. Never reads
classroom saves or launcher preferences, and never opens a public tunnel.
"""

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
OUTPUT = ROOT / "docs" / "screenshots"
ROLES = ("MOBI", "AUTO", "BRAIN", "GRID", "FLEET")
PROFILES = dict(MOBI="LOCAL", AUTO="DEDICATED", BRAIN="MOBILE", GRID="BASE", FLEET="LEAN")


def capture(language):
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = "http://127.0.0.1:%d" % port
    key = uuid.uuid4().hex

    def request(path, body=None, credential=None):
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + (credential or key),
        }
        req = urllib.request.Request(
            base + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.load(response)

    def host(action):
        state = request("/api/host")
        return request("/api/host/action", dict(action=action, expected_phase=state["phase"]))

    def act(token, action, **extra):
        return request(
            "/api/action", dict(token=token, action=action, request_id=uuid.uuid4().hex, **extra)
        )

    def screenshot(page, name):
        page.screenshot(
            path=str(OUTPUT / (name + "-" + language + ".png")),
            animations="disabled",
            full_page=name in ("dashboard", "debrief"),
        )

    with tempfile.TemporaryDirectory(prefix="ecosystem-readme-") as data:
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
                "--lang",
                language,
                "--cle",
                key,
                "--seed",
                "documentation-demo-2032",
                "--donnees",
                data,
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
                    if process.poll() is not None:
                        raise RuntimeError("The demo server exited before becoming ready") from None
                    time.sleep(0.1)
            else:
                raise RuntimeError("The demo server did not become ready")
            for number in range(10):
                request(
                    "/api/join",
                    dict(code=info["code"], first_name="Demo", last_name="%02d" % (number + 1)),
                )
            state = request("/api/host")
            tokens = {(p["team"], p["role"]): p["id"] for p in state["players"]}
            errors = []
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 390, "height": 844},
                    reduced_motion="reduce",
                    device_scale_factor=1,
                )
                context.add_init_script(
                    "localStorage.setItem('eco_token',%s)" % json.dumps(tokens["BLUE", "FLEET"])
                )
                mobile = context.new_page()
                mobile.on("pageerror", lambda error: errors.append(str(error)))
                mobile.goto(base)
                expect(mobile.locator("#intro")).to_be_visible()
                screenshot(mobile, "briefing")
                mobile.locator("#introSkip").click()
                teacher = browser.new_page(
                    viewport={"width": 1440, "height": 1000},
                    reduced_motion="reduce",
                    device_scale_factor=1,
                )
                teacher.on("pageerror", lambda error: errors.append(str(error)))
                teacher.goto(base + "/hote#cle=" + key)
                teacher.wait_for_function("() => H.st?.phase === 'LOBBY'")
                teacher.locator("#enlargeQr").click()
                expect(teacher.locator("#joinDialog")).to_be_visible()
                screenshot(teacher, "join")
                teacher.locator("#closeJoinDialog").click()
                host("next")
                teacher.wait_for_function("() => H.st?.phase === 'JANUARY'")
                screenshot(teacher, "dashboard")
                for (_team, role), token in tokens.items():
                    act(token, "profile", choice=PROFILES[role])
                mobile.wait_for_function("() => C.st?.me.profile === 'LEAN'")
                mobile.locator("#nav-entreprise").click()
                expect(mobile.locator(".private-ledger")).to_be_visible()
                screenshot(mobile, "company")
                mobile.locator("#nav-table").click()
                expect(mobile.locator(".ecosystem-node")).to_have_count(5)
                screenshot(mobile, "table")
                # Play actual contracts and settlements, solely to demonstrate
                # the debrief. Public mobile captures contain no proposed split.
                for team in ("BLUE", "GREEN"):
                    act(
                        tokens[team, "MOBI"],
                        "propose",
                        kind="INSTALL",
                        architecture="INTEGRATED" if team == "BLUE" else "MODULAR",
                        launch="EARLY",
                        allocations={r: (800 if team == "BLUE" else 760) for r in ROLES},
                        funding={"MOBI": 600} if team == "GREEN" else {},
                    )
                    for role in ROLES:
                        act(tokens[team, role], "consent", choice="ACCEPT", revision=1)
                for _ in range(4):
                    state = request("/api/host")
                    for team, data in state["teams"].items():
                        if data["incident"] or not data["agreement_current"]:
                            action = "REPAIR" if data["incident"] else "REVISE"
                            quote = next(o["cost"] for o in data["options"] if o["key"] == action)
                            own = request("/api/state", credential=tokens[team, "MOBI"])
                            if own["me"]["cash"] >= quote:
                                act(
                                    tokens[team, "MOBI"],
                                    "propose",
                                    kind=action,
                                    allocations={
                                        r: data["full_capacity_revenue"] // 5 for r in ROLES
                                    },
                                    funding={"MOBI": quote},
                                )
                                revision = request("/api/host")["teams"][team]["proposal"][
                                    "revision"
                                ]
                                for role in ROLES:
                                    act(
                                        tokens[team, role],
                                        "consent",
                                        choice="ACCEPT",
                                        revision=revision,
                                    )
                    host("next")
                teacher.wait_for_function("() => H.st?.phase === 'FINAL'")
                teacher.locator("#tab-brief").click()
                expect(teacher.locator("#debriefChart svg")).to_be_visible()
                teacher.locator("#debriefProjection").click()
                teacher.locator(".debrief").scroll_into_view_if_needed()
                teacher.evaluate("window.scrollTo(0, 0)")
                screenshot(teacher, "debrief")
                assert not errors, errors
                browser.close()
            print("Captured six real demo screenshots:", language)
        finally:
            if process.poll() is None:
                try:
                    host("shutdown")
                    process.wait(timeout=10)
                except Exception:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for language in ("en", "fr"):
        capture(language)
