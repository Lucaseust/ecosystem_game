"""Real HTTP regressions: malformed requests, access checks and static isolation."""

import gzip
import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serveur
from eco import campaign
from eco.http_security import ClassroomServer, MAX_BODY


class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ClassroomServer(("127.0.0.1", 0), serveur.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        serveur.GAME = campaign.Game(campaign.new_state(code="TEST"))
        serveur.GAME.state["host_key"] = "private-instructor-key"
        serveur.LANGUAGE = "fr"
        self.server.limiter.entries.clear()

    def request(self, method, path, data=None, headers=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.request(method, path, data, headers or {})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def post(self, body, **headers):
        return self.request(
            "POST", "/api/join", body, {"Content-Type": "application/json", **headers}
        )

    def test_invalid_json_shapes_and_field_types_are_rejected_without_mutation(self):
        for body in (
            b"[]",
            b"null",
            b"false",
            b"1",
            b"{",
            b"\xff",
            b'{"code":[]}',
            b'{"first_name":{}}',
            b'{"first_name":"\\ud800"}',
            b'{"text":"\\udfff"}',
            b'{"cle":"\\ud800"}',
            b'{"seconds":-1}',
            b'{"seconds":true}',
            b'{"shares":[]}',
            b'{"funding":{"MOBI":null}}',
            b'{"count":NaN}',
        ):
            with self.subTest(body=body):
                status, _, raw = self.post(body)
                self.assertEqual(status, 400)
                self.assertIn("error", json.loads(raw))
        self.assertEqual(serveur.GAME.state["players"], {})
        self.assertEqual(self.request("GET", "/api/info")[0], 200)

    def test_body_limit_content_type_and_cross_origin(self):
        self.assertEqual(self.post(b"x" * (MAX_BODY + 1))[0], 413)
        self.assertEqual(self.post(b"{}", **{"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.post(b"{}", Origin="https://untrusted.invalid")[0], 403)
        self.assertEqual(self.post(b"{}", **{"Sec-Fetch-Site": "cross-site"})[0], 403)

    def test_authorisation_headers_and_export_gates(self):
        self.assertEqual(self.request("GET", "/api/host")[0], 403)
        self.assertEqual(self.request("GET", "/api/state")[0], 401)
        headers = {"Authorization": "Bearer private-instructor-key"}
        self.assertEqual(self.request("GET", "/api/host", headers=headers)[0], 200)
        self.assertEqual(self.request("GET", "/api/export", headers=headers)[0], 400)
        self.assertEqual(self.request("GET", "/api/debrief", headers=headers)[0], 400)

    def test_security_headers_gzip_and_english_error(self):
        status, headers, raw = self.request("GET", "/", headers={"Accept-Encoding": "gzip"})
        self.assertEqual(status, 200)
        self.assertIn(b"ECOSYSTEM", gzip.decompress(raw))
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        self.assertNotIn("unsafe-eval", headers["Content-Security-Policy"])
        serveur.LANGUAGE = "en"
        self.assertEqual(
            json.loads(self.post(b"[]")[2])["error"],
            "The request body must be a valid JSON object.",
        )

    def test_sibling_directory_with_the_same_prefix_is_not_served(self):
        previous = serveur.WEB
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "web").mkdir()
            (root / "web-secret").mkdir()
            (root / "web-secret" / "key.txt").write_text("private", encoding="utf-8")
            try:
                serveur.WEB = str(root / "web")
                status, _, raw = self.request("GET", "/static/../web-secret/key.txt")
                self.assertEqual(status, 404)
                self.assertNotIn(b"private", raw)
            finally:
                serveur.WEB = previous

    def test_failed_host_authentication_is_rate_limited(self):
        for _ in range(30):
            self.assertEqual(self.request("GET", "/api/host?cle=wrong")[0], 403)
        self.assertEqual(self.request("GET", "/api/host?cle=wrong")[0], 429)
        self.assertEqual(self.request("GET", "/api/host?cle=private-instructor-key")[0], 200)


if __name__ == "__main__":
    unittest.main()
