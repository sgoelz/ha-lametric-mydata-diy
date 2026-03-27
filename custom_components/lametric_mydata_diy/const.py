"""Constants for the LaMetric My Data DIY integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "lametric_mydata_diy"
NAME: Final = "LaMetric My Data DIY"
SERVICE_REFRESH: Final = "refresh"

CONF_TITLE: Final = "title"
CONF_OUTPUT_PATH: Final = "output_path"
CONF_ENTITY_ID: Final = "entity_id"
CONF_ICON: Final = "icon"
CONF_DURATION: Final = "duration"
CONF_FORMAT: Final = "format"
CONF_ENABLED: Final = "enabled"
CONF_PREFIX: Final = "prefix"
CONF_SUFFIX: Final = "suffix"
CONF_FRAME_COUNT: Final = "frame_count"

FORMAT_POWER: Final = "power"
FORMAT_PERCENT: Final = "percent"
FORMAT_RAW: Final = "raw"
FORMAT_OPTIONS: Final = [FORMAT_POWER, FORMAT_PERCENT, FORMAT_RAW]

DEFAULT_OUTPUT_PATH: Final = "www/lametric/my_data_diy.json"
DEFAULT_FRAME_COUNT: Final = 4
MAX_FRAME_COUNT: Final = 8
DEFAULT_TITLE: Final = "LaMetric Feed"

DEFAULT_FRAMES: Final = (
    {
        CONF_ENABLED: True,
        CONF_ENTITY_ID: "sensor.total_dc_power",
        CONF_ICON: 27464,
        CONF_DURATION: 4000,
        CONF_FORMAT: FORMAT_POWER,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: True,
        CONF_ENTITY_ID: "sensor.battery_level",
        CONF_ICON: 389,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_PERCENT,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: True,
        CONF_ENTITY_ID: "sensor.skoda_enyaq_batteriestand",
        CONF_ICON: 2809,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_PERCENT,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: True,
        CONF_ENTITY_ID: "sensor.batteriestand",
        CONF_ICON: 2818,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_PERCENT,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: False,
        CONF_ENTITY_ID: "",
        CONF_ICON: 0,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_RAW,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: False,
        CONF_ENTITY_ID: "",
        CONF_ICON: 0,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_RAW,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: False,
        CONF_ENTITY_ID: "",
        CONF_ICON: 0,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_RAW,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: False,
        CONF_ENTITY_ID: "",
        CONF_ICON: 0,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_RAW,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
)


def frame_key(index: int, key: str) -> str:
    """Build a flattened frame key for config-entry data."""
    return f"frame_{index}_{key}"
