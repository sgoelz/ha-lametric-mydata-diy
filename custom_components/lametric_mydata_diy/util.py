"""Utility helpers for LaMetric My Data DIY."""

from __future__ import annotations

import re
import unicodedata
from typing import Any


def parse_float(raw: str | None, default: float | None = 0.0) -> float | None:
    """Parse a float from a Home Assistant state string."""
    try:
        return float(str(raw).replace(",", "."))
    except (TypeError, ValueError):
        return default


def normalize_energy_to_wh(raw: str | None, unit: Any) -> float | None:
    """Convert a supported energy value to Wh."""
    factors = {
        "wh": 1,
        "kwh": 1_000,
        "mwh": 1_000_000,
        "gwh": 1_000_000_000,
    }
    normalized_unit = str(unit or "").strip().lower().replace(" ", "")
    factor = factors.get(normalized_unit)
    if factor is None:
        return None

    value = parse_float(raw, None)
    if value is None:
        return None

    return value * factor


def normalize_temperature(raw: str | None, unit: Any) -> tuple[float, str] | None:
    """Convert a supported temperature value to a display tuple."""
    normalized_unit = str(unit or "").strip().lower().replace(" ", "")
    display_unit = {
        "°c": "°C",
        "c": "°C",
        "°f": "°F",
        "f": "°F",
    }.get(normalized_unit)
    if display_unit is None:
        return None

    value = parse_float(raw, None)
    if value is None:
        return None

    return value, display_unit


def normalize_voltage(raw: str | None, unit: Any) -> tuple[float, str] | None:
    """Convert a supported voltage value to volts."""
    normalized_unit = str(unit or "").strip().lower().replace(" ", "")
    factor = {
        "v": 1,
        "mv": 0.001,
    }.get(normalized_unit)
    if factor is None:
        return None

    value = parse_float(raw, None)
    if value is None:
        return None

    return value * factor, "V"


def normalize_current(raw: str | None, unit: Any) -> tuple[float, str] | None:
    """Convert a supported current value to amps."""
    normalized_unit = str(unit or "").strip().lower().replace(" ", "")
    factor = {
        "a": 1,
        "ma": 0.001,
    }.get(normalized_unit)
    if factor is None:
        return None

    value = parse_float(raw, None)
    if value is None:
        return None

    return value * factor, "A"


def format_energy(energy_wh: float) -> str:
    """Format an energy value using compact units."""
    magnitude = abs(energy_wh)
    if magnitude >= 1_000_000_000:
        return f"{energy_wh / 1_000_000_000:.1f}GWh"
    if magnitude >= 1_000_000:
        return f"{energy_wh / 1_000_000:.1f}MWh"
    if magnitude >= 1_000:
        return f"{energy_wh / 1_000:.1f}kWh"
    return f"{round(energy_wh):.0f}Wh"


def format_compact_number(value: float, unit: str) -> str:
    """Format a unit-bearing value with at most one decimal place."""
    rounded = round(value, 1)
    if rounded.is_integer():
        return f"{int(rounded)}{unit}"
    return f"{rounded:.1f}{unit}"


def format_power(watts: float) -> str:
    """Format a power value using W or kW while preserving the sign."""
    if abs(watts) >= 1000:
        return f"{watts / 1000:.1f}kW"
    return f"{round(watts):.0f}W"


def slugify_http_value(raw: Any) -> str:
    """Convert arbitrary user input into a URL-safe HTTP slug."""
    normalized = unicodedata.normalize("NFKD", str(raw or ""))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")


def default_http_slug(raw: Any, fallback: str = "lametric-feed") -> str:
    """Return a usable default HTTP slug."""
    slug = slugify_http_value(raw)
    return slug or fallback
