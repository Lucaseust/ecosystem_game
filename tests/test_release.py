"""Verify the distributed ZIP, including startup without site-packages."""

import hashlib
import json
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.build_release import build


class ReleaseTests(unittest.TestCase):
    def test_release_excludes_local_data_and_runs_without_dependencies(self):
        with tempfile.TemporaryDirectory(prefix="ecosystem-release-") as folder:
            root = Path(folder)
            path, manifest = build(root / "release.zip")
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                self.assertIn("ecosystem/LICENSE", names)
                for name in (
                    "README.md",
                    "README.fr.md",
                    "NOTICE.md",
                    "NOTICE.fr.md",
                    "NOTICE.html",
                    "NOTICE.fr.html",
                    "NOTICE.pdf",
                    "NOTICE.fr.pdf",
                    "docs/screenshots/dashboard-en.png",
                    "docs/screenshots/dashboard-fr.png",
                ):
                    self.assertIn("ecosystem/" + name, names)
                self.assertIn("ecosystem/locales/en.json", names)
                self.assertFalse(
                    any(
                        "donnees" in name
                        or ".interface" in name
                        or name.endswith(".exe")
                        or "debrief-entrainement" in name
                        for name in names
                    )
                )
                for name, digest in manifest.items():
                    self.assertEqual(
                        hashlib.sha256(archive.read("ecosystem/" + name)).hexdigest(), digest
                    )
                archive.extractall(root / "extracted")
            extracted = root / "extracted" / "ecosystem"
            with socket.socket() as sock:
                sock.bind(("127.0.0.1", 0))
                port = sock.getsockname()[1]
            base = "http://127.0.0.1:%d" % port
            data = root / "saved"
            command = [
                sys.executable,
                "-S",
                str(extracted / "serveur.py"),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--lang",
                "en",
                "--cle",
                "release-test-only",
                "--donnees",
                str(data),
                "--desktop",
            ]

            def request(path, body=None):
                req = urllib.request.Request(
                    base + path,
                    data=json.dumps(body).encode() if body is not None else None,
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=5) as response:
                    return json.load(response)

            def ready(process):
                for _ in range(100):
                    try:
                        return request("/api/info")
                    except (OSError, urllib.error.URLError):
                        if process.poll() is not None:
                            self.fail("Packaged server exited before becoming ready")
                        time.sleep(0.05)
                self.fail("Packaged server did not become ready")

            process = subprocess.Popen(
                command, cwd=extracted, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            try:
                info = ready(process)
                self.assertEqual(info["language"], "en")
                player = request(
                    "/api/join", dict(code=info["code"], first_name="Release", last_name="Test")
                )
                request(
                    "/api/host/action",
                    dict(cle="release-test-only", action="next", expected_phase="LOBBY"),
                )
                request("/api/host/action", dict(cle="release-test-only", action="shutdown"))
                self.assertEqual(process.wait(timeout=10), 0)
                saved = json.loads(
                    (data / ("partie-%s.json" % info["code"])).read_text(encoding="utf-8")
                )
                self.assertEqual(saved["phase"], "JANUARY")
                self.assertEqual(saved["language"], "en")
                self.assertIn(player["token"], saved["players"])
                # Language and the latest economic date survive a real restart.
                resumed_command = command[:]
                index = resumed_command.index("--lang")
                del resumed_command[index : index + 2]
                process = subprocess.Popen(
                    resumed_command,
                    cwd=extracted,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                resumed = ready(process)
                self.assertEqual(resumed["language"], "en")
                self.assertEqual(resumed["code"], info["code"])
                self.assertEqual(resumed["phase"], "JANUARY")
            finally:
                if process.poll() is None:
                    try:
                        request(
                            "/api/host/action", dict(cle="release-test-only", action="shutdown")
                        )
                        process.wait(timeout=10)
                    except Exception:
                        process.terminate()
                        process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
