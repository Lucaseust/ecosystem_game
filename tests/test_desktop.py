"""Lancement et arrêt réels de l’interface desktop, sans paquet externe."""

import json
import os
from pathlib import Path
import queue
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.dont_write_bytecode = True
from eco.desktop import MODES, ServerController, Settings, load_settings, save_settings


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def post(base, path, body):
    req = urllib.request.Request(
        base + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="eco-desktop-test-")
        self.controller = ServerController()
        self.settings = Settings(
            mode=MODES[2],
            port=str(free_port()),
            data=self.tmp.name,
            key="clé avec espaces & symbole",
        )

    def tearDown(self):
        if self.controller.running:
            self.controller.stop()
        self.tmp.cleanup()

    def ready(self):
        deadline = time.monotonic() + 10
        log = []
        while time.monotonic() < deadline:
            try:
                kind, value = self.controller.events.get(timeout=0.3)
            except queue.Empty:
                continue
            if kind == "ready":
                return value
            if kind == "log":
                log.append(value)
            if kind == "exit":
                self.fail("Le serveur s’est arrêté : " + "".join(log))
        self.fail("Le serveur ne s’est pas annoncé : " + "".join(log))

    def test_settings_validate_and_roundtrip_without_launching(self):
        preferences = Path(self.tmp.name) / "interface.json"
        self.assertEqual(load_settings(preferences).port, "8000")
        save_settings(self.settings, preferences)
        expected = Settings(**vars(self.settings))
        expected.key = ""
        self.assertEqual(load_settings(preferences), expected)
        self.assertNotIn(self.settings.key, preferences.read_text(encoding="utf-8"))
        preferences.write_text("fichier incomplet", encoding="utf-8")
        self.assertEqual(load_settings(preferences), Settings())
        for field, value in (
            ("port", "0"),
            ("port", "65536"),
            ("port", "abc"),
            ("teams", "7"),
            ("data", " "),
            ("ip", "not-an-ip"),
        ):
            settings = Settings(**vars(self.settings))
            setattr(settings, field, value)
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                settings.validate()

    def test_occupied_port_does_not_launch_or_write_game(self):
        with socket.socket() as other:
            other.bind(("127.0.0.1", int(self.settings.port)))
            other.listen()
            with self.assertRaises(ValueError):
                self.controller.start(self.settings, new=True)
        self.assertFalse(self.controller.running)
        self.assertEqual(list(Path(self.tmp.name).glob("partie-*.json")), [])

    def test_console_occupied_port_does_not_save_a_new_game(self):
        self.settings.teams = "3"
        with socket.socket() as other:
            other.bind(("127.0.0.1", 0))
            other.listen()
            self.settings.port = str(other.getsockname()[1])
            command = self.settings.command(self.settings.key, new=True)
            command.remove("--desktop")
            result = subprocess.run(command, capture_output=True, timeout=10, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(b"Cannot listen on", result.stderr)
        self.assertEqual(list(Path(self.tmp.name).glob("partie-*.json")), [])

    def test_invalid_save_is_reported_and_preserved(self):
        path = Path(self.tmp.name) / "partie-TEST.json"
        original = b"[1]"
        path.write_bytes(original)
        self.settings.key = ""
        self.controller.start(self.settings)
        log = []
        while True:
            kind, value = self.controller.events.get(timeout=10)
            if kind == "log":
                log.append(value)
            elif kind == "exit":
                self.assertNotEqual(value, 0)
                break
            else:
                self.fail(f"Unexpected event while reading an invalid save: {kind}")
        self.assertIn("Invalid save", "".join(log))
        self.assertEqual(path.read_bytes(), original)

    def test_graceful_stop_saves_latest_action_and_resume(self):
        self.controller.start(self.settings, new=True)
        ready = self.ready()
        base = "http://127.0.0.1:%s" % self.settings.port
        self.assertEqual(ready["join_url"], base + "/?c=" + ready["code"])
        with self.assertRaises(urllib.error.HTTPError) as rejected:
            post(base, "/api/host/action", {"action": "shutdown", "cle": "incorrecte"})
        self.assertEqual(rejected.exception.code, 403)
        rejected.exception.close()
        self.assertTrue(self.controller.running)
        with urllib.request.urlopen(ready["host_url"], timeout=10) as response:
            self.assertEqual(response.status, 200)
        player = post(
            base,
            "/api/join",
            {"code": ready["code"], "first_name": "Élise", "last_name": "Le Gall"},
        )
        # Arrêt immédiat, avant le délai de sauvegarde automatique de 1,5 s.
        self.controller.stop()
        self.assertFalse(self.controller.running)
        saved = json.loads(
            (Path(self.tmp.name) / ("partie-%s.json" % ready["code"])).read_text(encoding="utf-8")
        )
        self.assertEqual(saved["players"][player["token"]]["name"], "Élise Le Gall")
        self.assertEqual(self.controller.process.returncode, 0)
        self.controller = ServerController()
        self.settings.key = ""
        self.controller.start(self.settings)
        resumed = self.ready()
        self.assertEqual(resumed["code"], ready["code"])
        self.assertEqual(self.controller.key, saved["host_key"])
        with urllib.request.urlopen(
            base + "/api/state?token=" + player["token"], timeout=10
        ) as response:
            self.assertEqual(json.load(response)["me"]["name"], "Élise Le Gall")

    def test_new_game_keeps_previous_save(self):
        self.controller.start(self.settings, new=True)
        first = self.ready()
        self.controller.stop()
        self.controller = ServerController()
        self.controller.start(self.settings, new=True)
        second = self.ready()
        self.controller.stop()
        self.assertNotEqual(first["code"], second["code"])
        self.assertEqual(len(list(Path(self.tmp.name).glob("partie-*.json"))), 2)

    def test_old_round_save_is_preserved_and_default_launch_uses_campaign(self):
        from eco.engine import new_state

        old = new_state(code="OLDX")
        path = Path(self.tmp.name) / "partie-OLDX.json"
        path.write_text(json.dumps(old), encoding="utf-8")
        original = path.read_bytes()
        self.controller.start(self.settings)
        ready = self.ready()
        self.assertNotEqual(ready["code"], "OLDX")
        self.controller.stop()
        self.assertEqual(path.read_bytes(), original)
        campaign = json.loads(
            (Path(self.tmp.name) / ("partie-%s.json" % ready["code"])).read_text(encoding="utf-8")
        )
        self.assertEqual(campaign["schema"], "campaign-2.0")

    def test_stop_during_startup_and_duplicate_launch(self):
        self.controller.start(self.settings, new=True)
        with self.assertRaises(ValueError):
            self.controller.start(self.settings, new=True)
        self.controller.stop()
        self.assertFalse(self.controller.running)
        self.assertEqual(self.controller.process.returncode, 0)
        self.assertEqual(len(list(Path(self.tmp.name).glob("partie-*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
