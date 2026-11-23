"""Small, bounded HTTP safeguards for supervised classroom sessions."""

import json
import threading
import time
from collections import OrderedDict
from http.server import ThreadingHTTPServer

MAX_BODY = 16_384


class RequestError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def decode_body(raw):
    def invalid_constant(value):
        raise ValueError(value)

    try:
        body = json.loads(raw.decode("utf-8"), parse_constant=invalid_constant)
    except (ValueError, UnicodeDecodeError, RecursionError) as exc:
        raise RequestError("Le corps de la requête doit être un objet JSON valide.") from exc
    if not isinstance(body, dict):
        raise RequestError("Le corps de la requête doit être un objet JSON valide.")
    strings = {
        "token",
        "cle",
        "key",
        "action",
        "code",
        "first_name",
        "last_name",
        "text",
        "reason",
        "request_id",
        "kind",
        "architecture",
        "launch",
        "choice",
        "player",
        "team",
        "role",
        "phase",
        "expected_phase",
        "target",
        "stance",
        "resolution",
        "shock",
    }
    mappings = {"shares", "allocations", "funding", "revenues", "contributions", "integration"}
    for key, value in body.items():
        if key in strings and (not isinstance(value, str) or len(value) > 512):
            raise RequestError("Un champ de texte est invalide.")
        if key in strings:
            try:
                value.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise RequestError("Un champ de texte est invalide.") from exc
        if key in mappings:
            if (
                not isinstance(value, dict)
                or len(value) > 6
                or any(
                    not isinstance(v, (int, str)) or isinstance(v, bool) or len(str(v)) > 10
                    for v in value.values()
                )
            ):
                raise RequestError("Les montants doivent être des nombres entiers.")
        if key in {
            "minimum",
            "maximum",
            "revision",
            "seconds",
            "count",
            "round",
            "amount",
            "points",
        }:
            if isinstance(value, bool) or not isinstance(value, (str, int)) or len(str(value)) > 10:
                raise RequestError("Les montants doivent être des nombres entiers.")
            try:
                int(value)
            except ValueError as exc:
                raise RequestError("Les montants doivent être des nombres entiers.") from exc
        if key == "accept" and not isinstance(value, bool):
            raise RequestError("La réponse doit être vraie ou fausse.")
    if "seconds" in body and not 1 <= int(body["seconds"]) <= 3600:
        raise RequestError("L'ajout au chronomètre doit être compris entre 1 et 3600 secondes.")
    return body


class RateLimiter:
    """Fixed windows, bounded memory; no third-party service or participant data."""

    def __init__(self, capacity=2048):
        self.capacity = capacity
        self.entries = OrderedDict()
        self.lock = threading.Lock()

    def allow(self, key, limit, window=60):
        now = time.monotonic()
        with self.lock:
            started, count = self.entries.pop(key, (now, 0))
            if now - started >= window:
                started, count = now, 0
            self.entries[key] = (started, count + 1)
            if len(self.entries) > self.capacity:
                self.entries.popitem(last=False)
            return count < limit


class ClassroomServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 64

    def __init__(self, *args, **kwargs):
        self.slots = threading.BoundedSemaphore(128)
        self.limiter = RateLimiter()
        super().__init__(*args, **kwargs)

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()
