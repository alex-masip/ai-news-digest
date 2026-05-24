"""Shared config loaded from config/*.txt files."""
from __future__ import annotations

import re
from pathlib import Path

CONFIG_DIR = Path(__file__).parent.parent / "config"


def _load_lines(name: str) -> list[str]:
    text = (CONFIG_DIR / name).read_text()
    return [
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


WHITELIST: frozenset[str] = frozenset(_load_lines("whitelist.txt"))
BLOCKLIST: frozenset[str] = frozenset(_load_lines("blocklist.txt"))
POSITIVE_PATTERNS: list[str] = _load_lines("ai_positive.txt")
NEGATIVE_PATTERNS: list[str] = _load_lines("ai_negative.txt")

_combined_positive = "|".join(f"(?:{p})" for p in POSITIVE_PATTERNS)
_combined_negative = "|".join(f"(?:{p})" for p in NEGATIVE_PATTERNS)

POSITIVE_REGEX = re.compile(_combined_positive, re.IGNORECASE)
NEGATIVE_REGEX = re.compile(_combined_negative, re.IGNORECASE)


def bq_positive_regex() -> str:
    """Pattern for BQ REGEXP_CONTAINS — apply against LOWER(title) for case-insensitivity."""
    return _combined_positive
