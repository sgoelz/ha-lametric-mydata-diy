"""Utility helpers for LaMetric My Data DIY."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


def slugify_http_value(raw: Any) -> str:
    """Convert arbitrary user input into a URL-safe HTTP slug."""
    normalized = unicodedata.normalize("NFKD", str(raw or ""))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")


def default_http_slug(raw: Any, fallback: str = "lametric-feed") -> str:
    """Return a usable default HTTP slug."""
    slug = slugify_http_value(raw)
    return slug or fallback
