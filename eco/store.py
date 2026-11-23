# -*- coding: utf-8 -*-
"""Persistance de la partie sur disque (un fichier JSON, ecriture atomique)."""

import json
import os
import tempfile
import threading

_lock = threading.Lock()


def path_for(directory, code):
    return os.path.join(directory, "partie-%s.json" % code)


def latest(directory):
    """Chemin du fichier de partie le plus recent, ou None."""
    if not os.path.isdir(directory):
        return None
    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.startswith("partie-")
        and f.endswith(".json")
        and os.path.isfile(os.path.join(directory, f))
    ]
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def load(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def save(directory, state):
    """Ecrit l'etat sans risque de fichier tronque en cas d'interruption."""
    with _lock:
        os.makedirs(directory, exist_ok=True)
        target = path_for(directory, state["code"])
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(state, fh, ensure_ascii=False)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, target)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
