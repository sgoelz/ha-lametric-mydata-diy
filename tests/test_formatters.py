"""Unit tests for formatting helpers."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


def _load_util_module():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "custom_components" / "lametric_mydata_diy" / "util.py"
    spec = importlib.util.spec_from_file_location("lametric_util_for_tests", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load util module for tests")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


UTIL = _load_util_module()


class FormatPowerTests(unittest.TestCase):
    """Verify power formatting behaviour."""

    def test_negative_values_use_kw_threshold_by_absolute_value(self) -> None:
        self.assertEqual(UTIL.format_power(-1500), "-1.5kW")

    def test_positive_values_still_format_as_kw(self) -> None:
        self.assertEqual(UTIL.format_power(1500), "1.5kW")

    def test_small_values_stay_in_watts(self) -> None:
        self.assertEqual(UTIL.format_power(-250), "-250W")


class ParseFloatTests(unittest.TestCase):
    """Verify numeric parsing from Home Assistant states."""

    def test_parse_float_accepts_decimal_comma(self) -> None:
        self.assertEqual(UTIL.parse_float("1,5"), 1.5)

    def test_parse_float_returns_default_for_invalid_value(self) -> None:
        self.assertIsNone(UTIL.parse_float("invalid", None))


if __name__ == "__main__":
    unittest.main()
