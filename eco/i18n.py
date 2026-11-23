"""Presentation translations. Protocol keys, saves and user content stay untouched."""

import json
import re
from functools import lru_cache
from pathlib import Path

LOCALES = ("fr", "en")
CATALOG = Path(__file__).resolve().parent.parent / "locales" / "en.json"


@lru_cache(maxsize=1)
def catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def phrase_pattern():
    return re.compile("|".join(re.escape(k) for k in sorted(catalog(), key=len, reverse=True)))


def translate(text, language="fr"):
    if language != "en" or not isinstance(text, str):
        return text
    return phrase_pattern().sub(lambda match: catalog()[match[0]], text)


def view(value, language="fr", key=None):
    """Translate copies at the HTTP boundary, never persisted game state."""
    if language != "en" or key in {
        "name",
        "names",
        "first_name",
        "last_name",
        "claims",
        "discussion",
        "positions",
        "players",
        "token",
        "id",
        "org_id",
        "code",
        "join_base",
    }:
        return value
    if isinstance(value, dict):
        return {k: view(v, language, k) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [view(v, language, key) for v in value]
    return translate(value, language)
