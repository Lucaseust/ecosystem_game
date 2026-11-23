# -*- coding: utf-8 -*-
"""ECOSYSTEM - serveur de jeu.

Lancement :   python serveur.py
Puis :        les etudiants ouvrent l'adresse affichee sur leur telephone,
              l'enseignant ouvre le lien "tableau de bord".

Aucune dependance : bibliotheque standard Python uniquement.
"""

import argparse
import gzip
import json
import mimetypes
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, urlencode

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True  # pas de dossier __pycache__

from eco import engine, campaign, debrief, qr, store  # noqa: E402
from eco import i18n
from eco.http_security import ClassroomServer, MAX_BODY, RequestError, decode_body

HERE = os.path.dirname(os.path.abspath(__file__))
WEB = os.path.join(HERE, "web")
DATA = os.path.join(HERE, "donnees")

GAME = None  # instance engine.Game
DIRTY = threading.Event()
PUBLIC_URL = None  # adresse publique (tunnel), si elle existe
LANGUAGE = "fr"
STOP_REQUESTED = threading.Event()  # arret propre depuis l'interface desktop


# ---------------------------------------------------------------------------
# Reseau
# ---------------------------------------------------------------------------


def lan_ip():
    """Adresse IPv4 de la machine sur le reseau local."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def all_ipv4():
    out = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in out and not ip.startswith("127."):
                out.append(ip)
    except socket.gaierror:
        pass
    return out


# ---------------------------------------------------------------------------
# Tunnel public (cloudflared)
# ---------------------------------------------------------------------------


def find_cloudflared():
    """cloudflared dans le PATH, ou depose a cote de serveur.py."""
    found = shutil.which("cloudflared")
    if found:
        return found
    for name in ("cloudflared.exe", "cloudflared"):
        local = os.path.join(HERE, name)
        if os.path.isfile(local):
            return local
    return None


def stop_tunnel(proc):
    """Attend la fin du seul tunnel ouvert par ce serveur."""
    try:
        proc.terminate()
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)
    except OSError:
        pass


def start_tunnel(port, timeout=45):
    """Ouvre un tunnel Cloudflare et renvoie (url_publique, processus).

    Aucun compte n'est necessaire : cloudflared attribue une adresse
    https://<aleatoire>.trycloudflare.com valable le temps de la session.
    """
    exe = find_cloudflared()
    if not exe:
        print(i18n.translate("  cloudflared est introuvable.", LANGUAGE))
        print(
            i18n.translate(
                "  Installez cloudflared depuis le site officiel de Cloudflare, ou retirez --tunnel.",
                LANGUAGE,
            )
        )
        return None, None

    proc = subprocess.Popen(
        [exe, "tunnel", "--no-autoupdate", "--url", "http://127.0.0.1:%d" % port],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )

    pattern = re.compile(r"https://[a-z0-9][a-z0-9-]*\.trycloudflare\.com")
    found = {}

    def reader():
        for line in proc.stdout:
            m = pattern.search(line)
            if m and "url" not in found:
                found["url"] = m.group(0)

    threading.Thread(target=reader, daemon=True).start()

    print(i18n.translate("  Ouverture du tunnel public…", LANGUAGE), end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if STOP_REQUESTED.is_set():
            break
        if "url" in found:
            break
        if proc.poll() is not None:
            break
        time.sleep(0.4)

    if "url" not in found:
        print(i18n.translate(" échec.", LANGUAGE))
        print(
            i18n.translate(
                "  Le tunnel n'a pas répondu. Vérifiez que ce PC a bien internet.", LANGUAGE
            )
        )
        stop_tunnel(proc)
        return None, None

    url = found["url"]
    if wait_until_live(url):
        print(i18n.translate(" prêt, adresse vérifiée.", LANGUAGE))
    else:
        print(i18n.translate(" ouvert.", LANGUAGE))
        print(
            i18n.translate("  Adresse obtenue, mais connexion non vérifiée depuis ce PC.", LANGUAGE)
        )
        print(
            i18n.translate(
                "  Testez le lien sur un téléphone avant de commencer la séance.", LANGUAGE
            )
        )
    return url, proc


def wait_until_live(url, timeout=12):
    """Essaie de joindre l'adresse publique depuis ce PC. Purement indicatif."""
    import urllib.request

    deadline = time.time() + timeout
    while time.time() < deadline:
        if STOP_REQUESTED.is_set():
            return False
        try:
            with urllib.request.urlopen(url + "/api/info", timeout=5) as r:
                if r.status == 200:
                    return True
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(1.5)
    return False


# ---------------------------------------------------------------------------
# Serveur HTTP
# ---------------------------------------------------------------------------


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "ecosystem/1.0"

    def setup(self):
        super().setup()
        self.connection.settimeout(35)

    def version_string(self):
        return self.server_version

    # -- utilitaires --------------------------------------------------------

    def log_message(self, fmt, *args):
        pass  # console silencieuse

    def _send(self, code, body, ctype="application/json; charset=utf-8", cache=False):
        if isinstance(body, str):
            body = body.encode("utf-8")
        compress = (
            len(body) > 2048
            and "gzip" in self.headers.get("Accept-Encoding", "")
            and ctype.startswith(
                ("text/", "application/json", "application/javascript", "image/svg+xml")
            )
        )
        if compress:
            body = gzip.compress(body, compresslevel=5)
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.send_header("Connection", "close")
        self.send_header("Vary", "Accept-Encoding")
        if compress:
            self.send_header("Content-Encoding", "gzip")
        self.close_connection = True
        if cache:
            self.send_header("Cache-Control", "public, max-age=300")
        else:
            self.send_header("Cache-Control", "no-store")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, obj, code=200):
        self._send(code, json.dumps(i18n.view(obj, LANGUAGE), ensure_ascii=False))

    def _error(self, message, code=400):
        self._json({"error": message}, code)

    def _body(self):
        if self.headers.get("Transfer-Encoding"):
            raise RequestError("Encodage de transfert non pris en charge.")
        lengths = self.headers.get_all("Content-Length", [])
        if len(lengths) != 1:
            raise RequestError("Une taille de requête valide est nécessaire.", 411)
        try:
            n = int(lengths[0])
        except ValueError as exc:
            raise RequestError("Une taille de requête valide est nécessaire.") from exc
        if not 0 < n <= MAX_BODY:
            raise RequestError("La requête est trop volumineuse ou vide.", 413)
        if self.headers.get_content_type() != "application/json":
            raise RequestError("Le type de contenu doit être application/json.", 415)
        try:
            self.connection.settimeout(10)
            raw = self.rfile.read(n)
        except (TimeoutError, OSError) as exc:
            raise RequestError("La lecture de la requête a expiré.", 408) from exc
        finally:
            self.connection.settimeout(35)
        if len(raw) != n:
            raise RequestError("La requête est incomplète.")
        return decode_body(raw)

    def _static(self, name):
        path = (Path(WEB) / name).resolve()
        if not path.is_relative_to(Path(WEB).resolve()) or not path.is_file():
            return self._send(404, "Introuvable", "text/plain; charset=utf-8")
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if ctype.startswith(("text/", "application/javascript")):
            ctype += "; charset=utf-8"
        body = path.read_bytes()
        if path.suffix == ".html":
            body = (
                i18n.translate(body.decode("utf-8"), LANGUAGE)
                .replace('lang="fr"', 'lang="%s"' % LANGUAGE)
                .encode("utf-8")
            )
        self._send(200, body, ctype)

    def _check_host_key(self, params_or_body):
        key = self._bearer() or params_or_body.get("cle") or params_or_body.get("key")
        if isinstance(key, list):
            key = key[0] if key else None
        if not isinstance(key, str) or not secrets.compare_digest(
            key.encode(), GAME.state["host_key"].encode()
        ):
            if not self.server.limiter.allow(("host-auth", self.client_address[0]), 30):
                self._error("Trop de demandes. Patientez une minute avant de réessayer.", 429)
                return False
            self._error("Cle enseignant invalide.", 403)
            return False
        return True

    def _bearer(self):
        value = self.headers.get("Authorization", "")
        return unquote(value[7:]) if value.startswith("Bearer ") else None

    # -- routage ------------------------------------------------------------

    def do_GET(self):
        url = urlparse(self.path)
        p, q = url.path, parse_qs(url.query)

        if p == "/":
            return self._static(
                "joueur.html"
                if GAME.state.get("schema") == campaign.VERSION
                else "joueur-legacy.html"
            )
        if p in ("/hote", "/hote/"):
            return self._static(
                "hote.html" if GAME.state.get("schema") == campaign.VERSION else "hote-legacy.html"
            )
        if p.startswith("/static/"):
            return self._static(p[len("/static/") :])
        if p == "/api/language.js":
            catalogue = i18n.catalog() if LANGUAGE == "en" else {}
            return self._send(
                200,
                "EcoI18n.configure(%s);" % json.dumps(catalogue, ensure_ascii=False),
                "application/javascript; charset=utf-8",
            )
        if p == "/qr.svg":
            data = (q.get("d") or [""])[0]
            if not data:
                return self._send(400, "Parametre d manquant", "text/plain")
            try:
                svg = qr.svg(data)
            except ValueError as exc:
                return self._send(400, str(exc), "text/plain; charset=utf-8")
            return self._send(200, svg, "image/svg+xml; charset=utf-8", cache=True)

        if p == "/api/state":
            return self._api_state(q)
        if p == "/api/host":
            return self._api_host(q)
        if p == "/api/export":
            if not self._check_host_key(q):
                return
            try:
                if GAME.state.get("schema") != campaign.VERSION:
                    return self._error("Cet export concerne les campagnes narratives.")
                return self._send(200, GAME.export(), "application/zip")
            except engine.GameError as exc:
                return self._error(str(exc))
        if p == "/api/debrief":
            if not self._check_host_key(q):
                return
            with GAME.lock:
                if GAME.state.get("schema") != campaign.VERSION or GAME.state["phase"] not in (
                    "FINAL",
                    "DEBRIEF",
                ):
                    return self._error("Le rapport est disponible après la clôture de l'année.")
                data, code = debrief.build(GAME), GAME.state["code"]
            assets = {}
            for name in ("style.css", "campagne.css", "debrief.js"):
                with open(os.path.join(WEB, name), encoding="utf-8") as stream:
                    assets[name] = stream.read()
            report = debrief.html_report(
                data,
                assets["style.css"] + "\n" + assets["campagne.css"],
                assets["debrief.js"],
                code,
                language=LANGUAGE,
            )
            return self._send(200, report, "text/html; charset=utf-8")
        if p == "/api/info":
            return self._json(
                {
                    "code": GAME.state["code"],
                    "phase": GAME.state["phase"],
                    "players": len(GAME.state["players"]),
                    "language": LANGUAGE,
                }
            )
        return self._send(404, "Introuvable", "text/plain; charset=utf-8")

    def do_POST(self):
        url = urlparse(self.path)
        origin = self.headers.get("Origin")
        if (
            self.headers.get("Sec-Fetch-Site") == "cross-site"
            or origin
            and urlparse(origin).netloc != self.headers.get("Host")
        ):
            return self._error("Origine de requête refusée.", 403)
        try:
            body = self._body()
        except RequestError as exc:
            return self._error(str(exc), exc.status)
        credential = self._bearer() or body.get("token") or self.client_address[0]
        limit = 120 if url.path == "/api/join" else 180
        if not self.server.limiter.allow((url.path, credential), limit):
            return self._error("Trop de demandes. Patientez une minute avant de réessayer.", 429)

        if url.path == "/api/join":
            try:
                token = GAME.join(
                    code=body.get("code"),
                    first_name=body.get("first_name", ""),
                    last_name=body.get("last_name", ""),
                )
            except engine.GameError as exc:
                return self._error(str(exc))
            except OSError:
                return self._error(
                    "La sauvegarde n'a pas abouti. Votre décision n'a pas été confirmée ; réessayez.",
                    503,
                )
            p = GAME.state["players"][token]
            return self._json(
                {"token": token, "name": p["name"], "team": p["team"], "role": p["role"]}
            )

        if url.path == "/api/action":
            return self._api_action(body)
        if url.path == "/api/host/action":
            return self._api_host_action(body)
        return self._send(404, "Introuvable", "text/plain; charset=utf-8")

    # -- long polling -------------------------------------------------------

    def _wait(self, since):
        """Retarde la reponse jusqu'a un changement d'etat (ou 25 s)."""
        if since is None:
            return
        if GAME.state["version"] <= since:
            GAME.wait_for_change(since, timeout=25.0)

    @staticmethod
    def _since(q):
        try:
            return int((q.get("since") or [None])[0])
        except (TypeError, ValueError):
            return None

    def _api_state(self, q):
        token = self._bearer() or (q.get("token") or [""])[0]
        if token not in GAME.state["players"]:
            return self._error("Session inconnue.", 401)
        self._wait(self._since(q))
        try:
            return self._json(GAME.player_view(token))
        except engine.GameError as exc:
            return self._error(str(exc), 401)

    def _api_host(self, q):
        if not self._check_host_key(q):
            return
        self._wait(self._since(q))
        view = GAME.host_view()
        # l'adresse a projeter est celle du tunnel s'il y en a un, meme si
        # l'enseignant a ouvert le tableau de bord en local
        view["join_base"] = PUBLIC_URL
        return self._json(view)

    # -- actions joueur -----------------------------------------------------

    def _api_action(self, body):
        token = body.get("token")
        action = body.get("action")
        try:
            with GAME.lock:
                player = GAME._player(token)
                if player.get("identity_required") and action != "identity":
                    raise engine.GameError("Renseignez votre prenom et votre nom pour continuer.")
            if action == "identity":
                GAME.set_identity(token, body.get("first_name"), body.get("last_name"))
            elif GAME.state.get("schema") == campaign.VERSION:
                GAME.action(token, body)
            elif action == "decide":
                GAME.decide(token, body.get("choice"))
            elif action == "claim":
                GAME.set_claim(token, body.get("amount"), body.get("text"))
            elif action == "signal":
                GAME.signal(token, body.get("stance"), body.get("revision"))
            elif action == "contract":
                GAME.submit_contract(token, body.get("revenues"))
            elif action == "architecture":
                GAME.submit_architecture(token, body.get("architecture"), body.get("contributions"))
            elif action == "resolution":
                GAME.submit_resolution(
                    token, body.get("resolution"), body.get("revenues"), body.get("integration")
                )
            elif action == "offer":
                GAME.make_offer(token, body.get("target"), body.get("points"))
            elif action == "market":
                GAME.market_decide(token, body.get("choice"))
            elif action == "power":
                GAME.use_power(token, body.get("target"), body.get("amount"))
            elif action == "exclusivity":
                GAME.respond_exclusivity(token, bool(body.get("accept")))
            else:
                return self._error("Action inconnue.")
        except engine.GameError as exc:
            return self._error(str(exc))
        except OSError:
            return self._error(
                "La sauvegarde n'a pas abouti. Votre décision n'a pas été confirmée ; réessayez.",
                503,
            )
        return self._json({"ok": True, "version": GAME.state["version"]})

    # -- actions enseignant -------------------------------------------------

    def _api_host_action(self, body):
        if not self._check_host_key(body):
            return
        action = body.get("action")
        try:
            if GAME.state.get("schema") == campaign.VERSION and action not in (
                "next",
                "timer_start",
                "timer_pause",
                "timer_reset",
                "timer_add",
                "teams",
                "shuffle",
                "reassign",
                "remove",
                "request_identity",
                "shutdown",
            ):
                raise engine.GameError(
                    "La campagne avance par le calendrier, sans rejouer ni effacer les décisions."
                )
            if GAME.state.get("schema") == campaign.VERSION and action == "next":
                with GAME.lock:
                    if body.get("expected_phase") != GAME.state["phase"]:
                        raise engine.GameError(
                            "Le calendrier a déjà changé. Relisez la date courante avant de clore une période."
                        )
                    GAME.step(1)
                    return self._json({"ok": True, "version": GAME.state["version"]})
            if action == "phase":
                GAME.set_phase(body.get("phase"))
            elif action == "next":
                GAME.step(+1)
            elif action == "prev":
                GAME.step(-1)
            elif action == "timer_start":
                GAME.timer_start()
            elif action == "timer_pause":
                GAME.timer_pause()
            elif action == "timer_reset":
                GAME.timer_reset()
            elif action == "timer_add":
                GAME.timer_add(int(body.get("seconds") or 60))
            elif action == "teams":
                with GAME.lock:
                    GAME.set_team_count(body.get("count"))
            elif action == "shuffle":
                GAME.shuffle()
            elif action == "reassign":
                GAME.reassign(body.get("player"), body.get("team"), body.get("role"))
            elif action == "remove":
                GAME.remove_player(body.get("player"))
            elif action == "request_identity":
                GAME.request_identity()
            elif action == "shutdown":
                STOP_REQUESTED.set()
            elif action == "unlock":
                GAME.unlock_round(body.get("round"))
            elif action == "shock":
                GAME.force_shock(body.get("shock"))
            elif action == "reset":
                with GAME.lock:
                    new = engine.new_state(
                        code=GAME.state["code"], team_count=GAME.state["team_count"]
                    )
                    new["host_key"] = GAME.state["host_key"]
                    # la version continue de croitre, sinon les clients en
                    # attente ne verraient le changement qu'au bout de 25 s
                    new["version"] = GAME.state["version"]
                    GAME.state.clear()
                    GAME.state.update(new)
                    GAME.touch("Nouvelle partie")
            else:
                return self._error("Action inconnue.")
        except engine.GameError as exc:
            return self._error(str(exc))
        except (TypeError, ValueError) as exc:
            return self._error("Parametre invalide : %s" % exc)
        except OSError:
            return self._error(
                "La sauvegarde n'a pas abouti ; le calendrier n'a pas été confirmé.", 503
            )
        return self._json({"ok": True, "version": GAME.state["version"]})


# ---------------------------------------------------------------------------
# Sauvegarde differee
# ---------------------------------------------------------------------------


def saver_loop(directory):
    while not STOP_REQUESTED.is_set():
        if not DIRTY.wait(timeout=0.5):
            continue
        if STOP_REQUESTED.wait(1.5):
            break
        DIRTY.clear()
        try:
            # Keep the game lock through the write: a stale snapshot must never
            # overwrite a newer synchronous decision or the final shutdown save.
            with GAME.lock:
                store.save(directory, GAME.state)
        except Exception as exc:  # la sauvegarde ne doit jamais tuer le jeu
            print(i18n.translate("  [sauvegarde impossible] %s", LANGUAGE) % exc, file=sys.stderr)


# ---------------------------------------------------------------------------
# Demarrage
# ---------------------------------------------------------------------------

BANNER = """
  ███████ ██████ ██████ ███████ ██   ██ ███████ ████████ ███████ ███    ███ ███████
  ██     ██     ██   ██ ██       ██ ██  ██         ██    ██      ████  ████ ██
  █████  ██     ██   ██ ███████   ███   ███████    ██    █████   ██ ████ ██ █████
  ██     ██     ██   ██      ██  ██ ██       ██    ██    ██      ██  ██  ██ ██
  ███████ ██████ ██████ ███████ ██   ██ ███████    ██    ███████ ██      ██ ███████
"""


def main():
    global GAME, PUBLIC_URL, LANGUAGE

    ap = argparse.ArgumentParser(description="Serveur du serious game ECOSYSTEM")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument(
        "--lang",
        choices=i18n.LOCALES,
        default=None,
        help="langue de la séance / session language (fr, en)",
    )
    ap.add_argument(
        "--host", default="0.0.0.0", help="interface d'ecoute (0.0.0.0 = tout le reseau local)"
    )
    ap.add_argument(
        "--ip", default=None, help="adresse IP a afficher aux etudiants (detectee sinon)"
    )
    ap.add_argument(
        "--tunnel",
        action="store_true",
        help="ouvre une adresse publique via cloudflared : les "
        "etudiants se connectent en 4G, sans reseau commun",
    )
    ap.add_argument("--public", default=None, help="adresse publique deja obtenue (https://...)")
    ap.add_argument(
        "--equipes",
        type=int,
        default=None,
        help="fixe le nombre d'ecosystemes (sinon un de plus par tranche de 5 etudiants inscrits)",
    )
    ap.add_argument(
        "--nouvelle",
        action="store_true",
        help="ignore la partie sauvegardee et en cree une nouvelle",
    )
    ap.add_argument(
        "--cle", default=None, help="cle enseignant fixe (lien identique a chaque lancement)"
    )
    ap.add_argument("--donnees", default=DATA, help="dossier de sauvegarde")
    ap.add_argument("--desktop", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument(
        "--legacy", action="store_true", help="reprendre explicitement l'ancien jeu à manches"
    )
    ap.add_argument(
        "--seed", default=None, help="graine reproductible pour une nouvelle campagne de répétition"
    )
    args = ap.parse_args()
    LANGUAGE = args.lang or "fr"
    if not 1 <= args.port <= 65535:
        ap.error("--port must be between 1 and 65535")
    if args.equipes is not None and not 2 <= args.equipes <= 6:
        ap.error("--equipes must be between 2 and 6")
    if args.public and (
        urlparse(args.public).scheme not in ("http", "https")
        or not urlparse(args.public).netloc
        or urlparse(args.public).query
        or urlparse(args.public).fragment
    ):
        ap.error("--public must be an http(s) base URL without query or fragment")

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass

    state = None
    if not args.nouvelle:
        path = store.latest(args.donnees)
        if path:
            state = store.load(path)
            if not isinstance(state, dict) or not all(
                k in state for k in ("code", "host_key", "phase", "players", "teams", "version")
            ):
                raise SystemExit(
                    "Sauvegarde illisible / Invalid save: %s. Choose another save folder or use --nouvelle. The file has been preserved."
                    % path
                )
            if state and state.get("version"):
                LANGUAGE = args.lang or state.get("language", "fr")
                print(
                    i18n.translate("  Partie reprise depuis %s", LANGUAGE) % os.path.basename(path)
                )
    module = engine if args.legacy else campaign
    if state and not args.legacy and state.get("schema") != campaign.VERSION:
        print(
            i18n.translate(
                "  Ancienne sauvegarde à manches conservée. Une nouvelle campagne narrative est créée.",
                LANGUAGE,
            )
        )
        state = None
    if state and args.legacy and state.get("schema") == campaign.VERSION:
        raise SystemExit(
            "Ce dossier contient une campagne narrative ; retirez --legacy ou choisissez le dossier historique."
        )
    if state is None:
        state = module.new_state()
        while os.path.exists(store.path_for(args.donnees, state["code"])):
            state = module.new_state()
        if args.seed and not args.legacy:
            state["seed"] = args.seed
            state["seed_origin"] = "configured"
    if args.cle:
        state["host_key"] = args.cle
    LANGUAGE = args.lang or state.get("language", "fr")
    state["language"] = LANGUAGE

    # Une action de campagne est sauvegardee avant sa confirmation HTTP.
    GAME = module.Game(
        state,
        on_change=(lambda s: store.save(args.donnees, s))
        if not args.legacy
        else (lambda _s: DIRTY.set()),
    )
    try:
        httpd = ClassroomServer((args.host, args.port), Handler)
    except OSError as exc:
        raise SystemExit(
            f"Impossible d’écouter / Cannot listen on {args.host}:{args.port}: {exc}"
        ) from None

    try:
        with GAME.lock:
            if args.equipes:
                if args.legacy or GAME.state["phase"] == "LOBBY":
                    GAME.set_team_count(args.equipes)
                elif args.equipes != GAME.state["team_count"]:
                    print(
                        i18n.translate(
                            "  Campagne en cours : le nombre de territoires enregistré est conservé.",
                            LANGUAGE,
                        )
                    )
            store.save(args.donnees, GAME.state)
    except BaseException:
        httpd.server_close()
        raise
    if args.legacy:
        threading.Thread(target=saver_loop, args=(args.donnees,), daemon=True).start()

    ip = args.ip or ("127.0.0.1" if args.host in ("127.0.0.1", "localhost") else lan_ip())
    lan_base = "http://%s:%d" % (ip, args.port)
    code = GAME.state["code"]

    if not args.desktop:
        print(BANNER)
    print(i18n.translate("  Un jeu sur l'alignement, l'orchestration et l'architecture", LANGUAGE))
    print("  " + "-" * 70)
    print()

    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    tunnel_proc = None
    PUBLIC_URL = args.public
    if args.tunnel and not PUBLIC_URL:
        PUBLIC_URL, tunnel_proc = start_tunnel(args.port)
        print()

    base = PUBLIC_URL or lan_base
    join_url = "%s/?c=%s" % (base, code)
    key = GAME.state["host_key"]
    host_path = "/hote" + ("?" if args.legacy else "#") + urlencode({"cle": key})
    if args.desktop:
        print(
            "ECOSYSTEM_READY "
            + json.dumps(
                {
                    "host_url": "http://127.0.0.1:%d%s" % (args.port, host_path),
                    "join_url": join_url,
                    "code": code,
                    "public": bool(PUBLIC_URL),
                }
            ),
            flush=True,
        )

    if PUBLIC_URL:
        # le tableau de bord s'ouvre en local : c'est le lien le plus fiable
        # sur cette machine, et il affiche quand meme le QR de l'adresse
        # publique aux etudiants.
        print(
            i18n.translate(
                "  Adresse PUBLIQUE : les etudiants se connectent depuis n'importe", LANGUAGE
            )
        )
        print(i18n.translate("  quel reseau, y compris leurs donnees mobiles.", LANGUAGE))
        print()
        print(i18n.translate("  ETUDIANTS (telephone)   %s", LANGUAGE) % join_url)
        print(
            i18n.translate("  ENSEIGNANT (ce PC)      %s", LANGUAGE)
            % ("http://127.0.0.1:%d%s" % (args.port, host_path))
        )
        print()
        print(
            i18n.translate("  Depuis un autre appareil : %s", LANGUAGE) % (PUBLIC_URL + host_path)
        )
        print()
    else:
        print(i18n.translate("  ETUDIANTS (telephone)   %s", LANGUAGE) % join_url)
        print(i18n.translate("  ENSEIGNANT (projection) %s", LANGUAGE) % (lan_base + host_path))
        print()
        others = [x for x in all_ipv4() if x != ip]
        if others:
            print(
                i18n.translate("  Autres adresses de cette machine : %s", LANGUAGE)
                % ", ".join(others)
            )
            print(
                i18n.translate(
                    "  (si le QR ne fonctionne pas, relancez avec --ip <adresse>)", LANGUAGE
                )
            )
            print()
    if not args.desktop:
        try:
            print(qr.ascii_art(join_url))
        except Exception:
            pass
    print()
    print(
        i18n.translate("  Code de partie : %s     Cle enseignant : %s", LANGUAGE)
        % (code, GAME.state["host_key"])
    )
    saved = os.path.abspath(args.donnees)
    print(
        i18n.translate("  Ctrl+C pour arreter. La partie est sauvegardee dans %s", LANGUAGE) % saved
    )
    print()

    try:
        while not STOP_REQUESTED.wait(timeout=0.5):
            pass
    except KeyboardInterrupt:
        print(i18n.translate("\n  Arret du serveur.", LANGUAGE))
    finally:
        if tunnel_proc:
            stop_tunnel(tunnel_proc)
        httpd.shutdown()
        httpd.server_close()
        try:
            with GAME.lock:
                store.save(args.donnees, GAME.state)
            print(i18n.translate("  Partie sauvegardee.", LANGUAGE))
        except Exception as exc:
            print(i18n.translate("  Sauvegarde finale impossible : %s", LANGUAGE) % exc)
            raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
