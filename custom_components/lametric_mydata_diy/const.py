"""Constants for the LaMetric My Data DIY integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "lametric_mydata_diy"
NAME: Final = "LaMetric My Data DIY"
SERVICE_REFRESH: Final = "refresh"

CONF_DELIVERY_MODE: Final = "delivery_mode"
CONF_HTTP_SLUG: Final = "http_slug"
CONF_PRESET: Final = "preset"
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
CONF_CURRENT_TIME: Final = "current_time"
CONF_HIDE_WHEN: Final = "hide_when"

FORMAT_POWER: Final = "power"
FORMAT_PERCENT: Final = "percent"
FORMAT_ENERGY: Final = "energy"
FORMAT_TEMPERATURE: Final = "temperature"
FORMAT_VOLTAGE: Final = "voltage"
FORMAT_CURRENT: Final = "current"
FORMAT_TIME: Final = "time"
FORMAT_RAW: Final = "raw"
FORMAT_OPTIONS: Final = [
    FORMAT_POWER,
    FORMAT_PERCENT,
    FORMAT_ENERGY,
    FORMAT_TEMPERATURE,
    FORMAT_VOLTAGE,
    FORMAT_CURRENT,
    FORMAT_TIME,
    FORMAT_RAW,
]

HIDE_WHEN_NEVER: Final = "never"
HIDE_WHEN_ZERO: Final = "zero"
HIDE_WHEN_EMPTY: Final = "empty"
HIDE_WHEN_ZERO_OR_EMPTY: Final = "zero_or_empty"
HIDE_WHEN_OPTIONS: Final = [
    HIDE_WHEN_NEVER,
    HIDE_WHEN_ZERO,
    HIDE_WHEN_EMPTY,
    HIDE_WHEN_ZERO_OR_EMPTY,
]

PRESET_NONE: Final = "none"
PRESET_POWER: Final = "power"
PRESET_BATTERY_PERCENT: Final = "battery_percent"
PRESET_ENERGY: Final = "energy"
PRESET_TEMPERATURE: Final = "temperature"
PRESET_VOLTAGE: Final = "voltage"
PRESET_CURRENT: Final = "current"
PRESET_CLOCK: Final = "clock"
PRESET_OPTIONS: Final = [
    PRESET_NONE,
    PRESET_POWER,
    PRESET_BATTERY_PERCENT,
    PRESET_ENERGY,
    PRESET_TEMPERATURE,
    PRESET_VOLTAGE,
    PRESET_CURRENT,
    PRESET_CLOCK,
]

DEFAULT_TIME_ICON: Final = 7645

DELIVERY_MODE_FILE: Final = "file"
DELIVERY_MODE_HTTP: Final = "http"
DELIVERY_MODE_OPTIONS: Final = [
    DELIVERY_MODE_FILE,
    DELIVERY_MODE_HTTP,
]
DEFAULT_DELIVERY_MODE: Final = DELIVERY_MODE_FILE
HTTP_VIEW_BASE: Final = "/api/lametric_mydata_diy"

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
        CONF_CURRENT_TIME: False,
        CONF_HIDE_WHEN: HIDE_WHEN_NEVER,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: True,
        CONF_ENTITY_ID: "sensor.battery_level",
        CONF_ICON: 389,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_PERCENT,
        CONF_CURRENT_TIME: False,
        CONF_HIDE_WHEN: HIDE_WHEN_NEVER,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: True,
        CONF_ENTITY_ID: "sensor.skoda_enyaq_batteriestand",
        CONF_ICON: 2809,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_PERCENT,
        CONF_CURRENT_TIME: False,
        CONF_HIDE_WHEN: HIDE_WHEN_NEVER,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: True,
        CONF_ENTITY_ID: "sensor.batteriestand",
        CONF_ICON: 2818,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_PERCENT,
        CONF_CURRENT_TIME: False,
        CONF_HIDE_WHEN: HIDE_WHEN_NEVER,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: False,
        CONF_ENTITY_ID: "",
        CONF_ICON: 0,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_RAW,
        CONF_CURRENT_TIME: False,
        CONF_HIDE_WHEN: HIDE_WHEN_NEVER,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: False,
        CONF_ENTITY_ID: "",
        CONF_ICON: 0,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_RAW,
        CONF_CURRENT_TIME: False,
        CONF_HIDE_WHEN: HIDE_WHEN_NEVER,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: False,
        CONF_ENTITY_ID: "",
        CONF_ICON: 0,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_RAW,
        CONF_CURRENT_TIME: False,
        CONF_HIDE_WHEN: HIDE_WHEN_NEVER,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    {
        CONF_ENABLED: False,
        CONF_ENTITY_ID: "",
        CONF_ICON: 0,
        CONF_DURATION: 3000,
        CONF_FORMAT: FORMAT_RAW,
        CONF_CURRENT_TIME: False,
        CONF_HIDE_WHEN: HIDE_WHEN_NEVER,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
)

FRAME_PRESET_VALUES: Final = {
    PRESET_POWER: {
        CONF_CURRENT_TIME: False,
        CONF_ICON: 27464,
        CONF_FORMAT: FORMAT_POWER,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    PRESET_BATTERY_PERCENT: {
        CONF_CURRENT_TIME: False,
        CONF_ICON: 389,
        CONF_FORMAT: FORMAT_PERCENT,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    PRESET_ENERGY: {
        CONF_CURRENT_TIME: False,
        CONF_ICON: 7959,
        CONF_FORMAT: FORMAT_ENERGY,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    PRESET_TEMPERATURE: {
        CONF_CURRENT_TIME: False,
        CONF_ICON: 2056,
        CONF_FORMAT: FORMAT_TEMPERATURE,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    PRESET_VOLTAGE: {
        CONF_CURRENT_TIME: False,
        CONF_ICON: 603,
        CONF_FORMAT: FORMAT_VOLTAGE,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    PRESET_CURRENT: {
        CONF_CURRENT_TIME: False,
        CONF_ICON: 604,
        CONF_FORMAT: FORMAT_CURRENT,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
    PRESET_CLOCK: {
        CONF_CURRENT_TIME: True,
        CONF_ENTITY_ID: "",
        CONF_ICON: DEFAULT_TIME_ICON,
        CONF_FORMAT: FORMAT_TIME,
        CONF_PREFIX: "",
        CONF_SUFFIX: "",
    },
}


def frame_key(index: int, key: str) -> str:
    """Build a flattened frame key for config-entry data."""
    return f"frame_{index}_{key}"
