"""Regression tests for integration defaults."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest


def _load_const_module():
    root = Path(__file__).resolve().parents[1]
    module_path = root / "custom_components" / "lametric_mydata_diy" / "const.py"
    spec = importlib.util.spec_from_file_location("lametric_const_for_tests", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Failed to load const module for tests")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CONST = _load_const_module()


class DefaultFrameTests(unittest.TestCase):
    """Ensure shipped defaults stay neutral for new users."""

    def test_active_default_frames_start_blank(self) -> None:
        active_defaults = CONST.DEFAULT_FRAMES[: CONST.DEFAULT_FRAME_COUNT]

        for frame in active_defaults:
            self.assertEqual(frame[CONST.CONF_ENTITY_ID], "")
            self.assertEqual(frame[CONST.CONF_ICON], 0)
            self.assertEqual(frame[CONST.CONF_FORMAT], CONST.FORMAT_RAW)
            self.assertEqual(frame[CONST.CONF_DURATION], 3000)

    def test_default_frames_do_not_reference_personal_sensor_ids(self) -> None:
        for frame in CONST.DEFAULT_FRAMES:
            self.assertFalse(str(frame[CONST.CONF_ENTITY_ID]).startswith("sensor."))


if __name__ == "__main__":
    unittest.main()
