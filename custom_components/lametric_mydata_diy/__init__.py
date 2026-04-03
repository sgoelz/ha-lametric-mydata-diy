"""LaMetric My Data DIY integration."""

from __future__ import annotations

from collections.abc import Callable
import json
import logging
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any
from uuid import uuid4

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Event, HomeAssistant, ServiceCall, State
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_CURRENT_TIME,
    CONF_DELIVERY_MODE,
    CONF_DURATION,
    CONF_ENABLED,
    CONF_ENTITY_ID,
    CONF_FRAME_COUNT,
    CONF_FORMAT,
    CONF_HIDE_WHEN,
    CONF_ICON,
    CONF_OUTPUT_PATH,
    CONF_PREFIX,
    CONF_SUFFIX,
    DEFAULT_FRAME_COUNT,
    DEFAULT_FRAMES,
    DEFAULT_DELIVERY_MODE,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TIME_ICON,
    DELIVERY_MODE_FILE,
    DELIVERY_MODE_HTTP,
    DOMAIN,
    FORMAT_CURRENT,
    FORMAT_ENERGY,
    FORMAT_PERCENT,
    FORMAT_POWER,
    FORMAT_TEMPERATURE,
    FORMAT_TIME,
    FORMAT_VOLTAGE,
    HIDE_WHEN_EMPTY,
    HIDE_WHEN_NEVER,
    HIDE_WHEN_ZERO,
    HIDE_WHEN_ZERO_OR_EMPTY,
    MAX_FRAME_COUNT,
    SERVICE_REFRESH,
    HTTP_VIEW_BASE,
    frame_key,
)

_LOGGER = logging.getLogger(__name__)
Unsub = Callable[[], None]
DATA_WRITERS = "writers"
DATA_HTTP_VIEW_REGISTERED = "http_view_registered"


def _parse_float(raw: str | None, default: float | None = 0.0) -> float | None:
    try:
        return float(str(raw).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _normalize_energy_to_wh(raw: str | None, unit: Any) -> float | None:
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

    value = _parse_float(raw, None)
    if value is None:
        return None

    return value * factor


def _normalize_temperature(raw: str | None, unit: Any) -> tuple[float, str] | None:
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

    value = _parse_float(raw, None)
    if value is None:
        return None

    return value, display_unit


def _normalize_voltage(raw: str | None, unit: Any) -> tuple[float, str] | None:
    """Convert a supported voltage value to volts."""
    normalized_unit = str(unit or "").strip().lower().replace(" ", "")
    factor = {
        "v": 1,
        "mv": 0.001,
    }.get(normalized_unit)
    if factor is None:
        return None

    value = _parse_float(raw, None)
    if value is None:
        return None

    return value * factor, "V"


def _normalize_current(raw: str | None, unit: Any) -> tuple[float, str] | None:
    """Convert a supported current value to amps."""
    normalized_unit = str(unit or "").strip().lower().replace(" ", "")
    factor = {
        "a": 1,
        "ma": 0.001,
    }.get(normalized_unit)
    if factor is None:
        return None

    value = _parse_float(raw, None)
    if value is None:
        return None

    return value * factor, "A"


def _format_energy(energy_wh: float) -> str:
    """Format an energy value using compact units."""
    magnitude = abs(energy_wh)
    if magnitude >= 1_000_000_000:
        return f"{energy_wh / 1_000_000_000:.1f}GWh"
    if magnitude >= 1_000_000:
        return f"{energy_wh / 1_000_000:.1f}MWh"
    if magnitude >= 1_000:
        return f"{energy_wh / 1_000:.1f}kWh"
    return f"{round(energy_wh):.0f}Wh"


def _format_compact_number(value: float, unit: str) -> str:
    """Format a unit-bearing value with at most one decimal place."""
    rounded = round(value, 1)
    if rounded.is_integer():
        return f"{int(rounded)}{unit}"
    return f"{rounded:.1f}{unit}"


def _is_empty_state(raw: str | None) -> bool:
    """Return whether the raw state should be treated as empty."""
    normalized = str(raw or "").strip().lower()
    return normalized in {"", "unknown", "unavailable", "none", "null"}


def _is_zero_state(raw: str | None) -> bool:
    """Return whether the raw state is a numeric zero."""
    value = _parse_float(raw, None)
    return value is not None and abs(value) < 1e-9


def _format_value(state: State | None, value_format: str) -> str:
    raw = state.state if state else None

    if value_format == FORMAT_TIME:
        return dt_util.now().strftime("%H:%M")

    if value_format == FORMAT_POWER:
        watts = _parse_float(raw, 0.0)
        if watts >= 1000:
            return f"{watts / 1000:.1f}kW"
        return f"{round(watts):.0f}W"

    if value_format == FORMAT_PERCENT:
        percent = _parse_float(raw, -1.0)
        if percent < 0:
            return "--%"
        return f"{round(percent):.0f}%"

    if value_format == FORMAT_ENERGY:
        if raw in (None, "", "unknown", "unavailable"):
            return "--"
        energy_wh = _normalize_energy_to_wh(
            raw,
            state.attributes.get("unit_of_measurement") if state else None,
        )
        if energy_wh is None:
            return str(raw)
        return _format_energy(energy_wh)

    if value_format == FORMAT_TEMPERATURE:
        if raw in (None, "", "unknown", "unavailable"):
            return "--"
        normalized = _normalize_temperature(
            raw,
            state.attributes.get("unit_of_measurement") if state else None,
        )
        if normalized is None:
            return str(raw)
        value, unit = normalized
        return _format_compact_number(value, unit)

    if value_format == FORMAT_VOLTAGE:
        if raw in (None, "", "unknown", "unavailable"):
            return "--"
        normalized = _normalize_voltage(
            raw,
            state.attributes.get("unit_of_measurement") if state else None,
        )
        if normalized is None:
            return str(raw)
        value, unit = normalized
        return _format_compact_number(value, unit)

    if value_format == FORMAT_CURRENT:
        if raw in (None, "", "unknown", "unavailable"):
            return "--"
        normalized = _normalize_current(
            raw,
            state.attributes.get("unit_of_measurement") if state else None,
        )
        if normalized is None:
            return str(raw)
        value, unit = normalized
        return _format_compact_number(value, unit)

    if raw in (None, "", "unknown", "unavailable"):
        return "--"

    return str(raw)


def _apply_affixes(value: str, prefix: str, suffix: str) -> str:
    """Apply optional prefix and suffix to a formatted value."""
    return f"{prefix}{value}{suffix}"


def _should_hide_frame(state: State | None, frame: dict[str, Any]) -> bool:
    """Return whether a frame should be omitted from the payload."""
    if _frame_uses_current_time(frame):
        return False

    hide_when = frame[CONF_HIDE_WHEN]
    if hide_when == HIDE_WHEN_NEVER:
        return False

    raw = state.state if state else None
    is_empty = _is_empty_state(raw)
    is_zero = _is_zero_state(raw)

    if hide_when == HIDE_WHEN_ZERO:
        return is_zero
    if hide_when == HIDE_WHEN_EMPTY:
        return is_empty
    if hide_when == HIDE_WHEN_ZERO_OR_EMPTY:
        return is_zero or is_empty

    return False


def _entry_config(entry: ConfigEntry) -> dict[str, Any]:
    """Return merged entry config from data and options."""
    config = dict(entry.data)
    config.update(entry.options)
    return config


def _domain_data(hass: HomeAssistant) -> dict[str, Any]:
    """Return integration runtime storage."""
    return hass.data.setdefault(
        DOMAIN,
        {
            DATA_WRITERS: {},
            DATA_HTTP_VIEW_REGISTERED: False,
        },
    )


def _writers(hass: HomeAssistant) -> dict[str, "LaMetricFeedWriter"]:
    """Return all active writers."""
    return _domain_data(hass)[DATA_WRITERS]


def _frame_config(config: dict[str, Any], index: int) -> dict[str, Any]:
    """Extract one frame config from flattened config-entry data."""
    defaults = DEFAULT_FRAMES[index - 1]
    return {
        CONF_ENABLED: bool(config.get(frame_key(index, CONF_ENABLED), defaults[CONF_ENABLED])),
        CONF_CURRENT_TIME: bool(
            config.get(frame_key(index, CONF_CURRENT_TIME), defaults[CONF_CURRENT_TIME])
        ),
        CONF_ENTITY_ID: config.get(frame_key(index, CONF_ENTITY_ID), defaults[CONF_ENTITY_ID]),
        CONF_ICON: int(config.get(frame_key(index, CONF_ICON), defaults[CONF_ICON])),
        CONF_DURATION: int(config.get(frame_key(index, CONF_DURATION), defaults[CONF_DURATION])),
        CONF_FORMAT: config.get(frame_key(index, CONF_FORMAT), defaults[CONF_FORMAT]),
        CONF_HIDE_WHEN: config.get(frame_key(index, CONF_HIDE_WHEN), defaults[CONF_HIDE_WHEN]),
        CONF_PREFIX: str(config.get(frame_key(index, CONF_PREFIX), defaults[CONF_PREFIX])),
        CONF_SUFFIX: str(config.get(frame_key(index, CONF_SUFFIX), defaults[CONF_SUFFIX])),
    }


def _frame_uses_current_time(frame: dict[str, Any]) -> bool:
    """Return whether a frame should render the current time."""
    return bool(frame[CONF_CURRENT_TIME] or frame[CONF_FORMAT] == FORMAT_TIME)


def _write_payload(target: Path, payload: dict[str, Any]) -> None:
    """Write payload atomically."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target.with_name(f"{target.name}.{uuid4().hex}.tmp")
    temp_path.write_text(json.dumps(payload, separators=(",", ":")) + "\n", encoding="utf-8")
    temp_path.replace(target)


def _resolve_output_path(hass: HomeAssistant, raw_path: Any) -> Path:
    """Resolve an output path and keep writes confined to /config/www."""
    relative = str(raw_path or DEFAULT_OUTPUT_PATH).strip().lstrip("/")
    normalized = PurePosixPath(relative)
    if not normalized.parts or normalized.parts[0] != "www":
        raise ValueError("output path must stay inside /config/www")
    if ".." in normalized.parts:
        raise ValueError("output path must stay inside /config/www")
    if normalized.suffix != ".json":
        raise ValueError("output path must end with .json")

    base_path = Path(hass.config.path("www")).resolve()
    target_path = Path(hass.config.path(normalized.as_posix())).resolve(strict=False)
    if target_path != base_path and base_path not in target_path.parents:
        raise ValueError("output path resolved outside /config/www")

    return target_path


class LaMetricFeedWriter:
    """Manage feed generation for one config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the writer."""
        self.hass = hass
        self.entry = entry
        self._unsubs: list[Unsub] = []
        self._delayed_unsub: Unsub | None = None
        self._started_unsub: Unsub | None = None
        self._last_payload: dict[str, Any] | None = None

    @property
    def config(self) -> dict[str, Any]:
        """Return merged config."""
        return _entry_config(self.entry)

    @property
    def output_path(self) -> Path:
        """Return the absolute target path for the JSON payload."""
        return _resolve_output_path(
            self.hass,
            self.config.get(CONF_OUTPUT_PATH, DEFAULT_OUTPUT_PATH),
        )

    @property
    def delivery_mode(self) -> str:
        """Return the configured payload delivery mode."""
        return str(self.config.get(CONF_DELIVERY_MODE, DEFAULT_DELIVERY_MODE))

    @property
    def http_path(self) -> str:
        """Return the direct HTTP endpoint path for this feed."""
        return f"{HTTP_VIEW_BASE}/{self.entry.entry_id}"

    @property
    def frame_count(self) -> int:
        """Return the number of configured frames to render."""
        return max(1, min(MAX_FRAME_COUNT, int(self.config.get(CONF_FRAME_COUNT, DEFAULT_FRAME_COUNT))))

    @property
    def tracked_entities(self) -> list[str]:
        """Return all entity IDs used by the feed."""
        entities: list[str] = []
        for idx in range(1, self.frame_count + 1):
            frame = _frame_config(self.config, idx)
            if not frame[CONF_ENABLED]:
                continue
            if _frame_uses_current_time(frame):
                continue
            entity_id = frame[CONF_ENTITY_ID]
            if entity_id and entity_id not in entities:
                entities.append(entity_id)
        return entities

    @property
    def has_time_frames(self) -> bool:
        """Return whether any active frame renders the current time."""
        for idx in range(1, self.frame_count + 1):
            frame = _frame_config(self.config, idx)
            if frame[CONF_ENABLED] and _frame_uses_current_time(frame):
                return True
        return False

    async def async_start(self) -> None:
        """Start tracking entity changes."""
        if self.tracked_entities:
            self._unsubs.append(
                async_track_state_change_event(
                    self.hass,
                    self.tracked_entities,
                    self._handle_state_change,
                )
            )
        if self.has_time_frames:
            self._unsubs.append(
                async_track_time_change(
                    self.hass,
                    self._handle_time_tick,
                    second=0,
                )
            )
        self._started_unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED,
            self._handle_started,
        )
        await self.async_write_payload()

    async def async_stop(self) -> None:
        """Stop listeners."""
        if self._delayed_unsub:
            self._delayed_unsub()
            self._delayed_unsub = None
        if self._started_unsub:
            self._started_unsub()
            self._started_unsub = None
        while self._unsubs:
            self._unsubs.pop()()

    def _render_payload(self) -> dict[str, Any]:
        """Render the current payload for this config entry."""
        payload = {"frames": []}
        for idx in range(1, self.frame_count + 1):
            frame = _frame_config(self.config, idx)
            if not frame[CONF_ENABLED]:
                continue
            if not _frame_uses_current_time(frame) and not frame[CONF_ENTITY_ID]:
                continue
            state = None
            value_format = frame[CONF_FORMAT]
            if not _frame_uses_current_time(frame):
                state = self.hass.states.get(frame[CONF_ENTITY_ID])
                if _should_hide_frame(state, frame):
                    continue
            else:
                value_format = FORMAT_TIME

            value = _format_value(state, value_format)
            payload_frame = {
                "text": _apply_affixes(value, frame[CONF_PREFIX], frame[CONF_SUFFIX]),
                "duration": frame[CONF_DURATION],
            }
            if _frame_uses_current_time(frame) and frame[CONF_ICON] == 0:
                payload_frame["icon"] = DEFAULT_TIME_ICON
            elif frame[CONF_ICON] > 0:
                payload_frame["icon"] = frame[CONF_ICON]
            payload["frames"].append(payload_frame)

        return payload

    async def async_write_payload(self) -> None:
        """Render and publish the current payload."""
        payload = self._render_payload()
        self._last_payload = payload

        if self.delivery_mode == DELIVERY_MODE_HTTP:
            _LOGGER.debug("Updated LaMetric HTTP feed for %s at %s", self.entry.entry_id, self.http_path)
            return

        try:
            output_path = self.output_path
        except ValueError as err:
            _LOGGER.error("Invalid output path for %s: %s", self.entry.entry_id, err)
            return

        await self.hass.async_add_executor_job(_write_payload, output_path, payload)
        _LOGGER.debug("Updated LaMetric feed for %s at %s", self.entry.entry_id, output_path)

    async def async_get_payload(self) -> dict[str, Any]:
        """Return the latest payload, rendering it on demand if needed."""
        if self._last_payload is None:
            await self.async_write_payload()
        if self._last_payload is None:
            raise RuntimeError("payload not available")
        return self._last_payload

    async def _handle_state_change(self, event: Event) -> None:
        """Update feed when a tracked entity changes."""
        await self.async_write_payload()

    async def _handle_time_tick(self, now: Any) -> None:
        """Refresh time-based frames once per minute."""
        del now
        await self.async_write_payload()

    async def _handle_started(self, event: Event) -> None:
        """Delay first write slightly after startup."""
        del event
        self._started_unsub = None

        async def _delayed_write(_now: Any) -> None:
            self._delayed_unsub = None
            await self.async_write_payload()

        self._delayed_unsub = async_call_later(self.hass, 15, _delayed_write)


class LaMetricMyDataDIYFeedView(HomeAssistantView):
    """Serve a LaMetric feed directly over HTTP."""

    url = f"{HTTP_VIEW_BASE}/{{entry_id}}"
    name = f"api:{DOMAIN}:feed"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the HTTP view."""
        self.hass = hass

    async def get(self, request: web.Request, entry_id: str | None = None) -> web.Response:
        """Return the current payload for one HTTP-mode feed."""
        del request
        entry_id = entry_id or ""
        writer = _writers(self.hass).get(entry_id)
        if writer is None or writer.delivery_mode != DELIVERY_MODE_HTTP:
            raise web.HTTPNotFound()

        try:
            payload = await writer.async_get_payload()
        except RuntimeError as err:
            raise web.HTTPServiceUnavailable(text=str(err)) from err

        return web.json_response(payload)


def _ensure_http_view_registered(hass: HomeAssistant) -> None:
    """Register the direct feed HTTP view once per runtime."""
    data = _domain_data(hass)
    if data[DATA_HTTP_VIEW_REGISTERED]:
        return
    hass.http.register_view(LaMetricMyDataDIYFeedView(hass))
    data[DATA_HTTP_VIEW_REGISTERED] = True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LaMetric My Data DIY from a config entry."""
    _ensure_http_view_registered(hass)
    writer = LaMetricFeedWriter(hass, entry)
    _writers(hass)[entry.entry_id] = writer
    await writer.async_start()

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        async def _handle_refresh(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            writers = _writers(hass)
            if entry_id:
                writer = writers.get(entry_id)
                if writer is not None:
                    await writer.async_write_payload()
                return
            for item in writers.values():
                await item.async_write_payload()

        hass.services.async_register(DOMAIN, SERVICE_REFRESH, _handle_refresh)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    writer = _writers(hass).pop(entry.entry_id)
    await writer.async_stop()

    if not _writers(hass) and hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to the current data shape."""
    if entry.version > 1:
        return False

    data = dict(entry.data)
    options = dict(entry.options)
    updated = False

    if CONF_DELIVERY_MODE not in data:
        data[CONF_DELIVERY_MODE] = DEFAULT_DELIVERY_MODE
        updated = True

    if CONF_FRAME_COUNT not in data:
        data[CONF_FRAME_COUNT] = DEFAULT_FRAME_COUNT
        updated = True

    for idx, defaults in enumerate(DEFAULT_FRAMES, start=1):
        for key, default in defaults.items():
            flat_key = frame_key(idx, key)
            if flat_key not in data:
                data[flat_key] = default
                updated = True

    if updated:
        hass.config_entries.async_update_entry(
            entry,
            data=data,
            options=options,
            version=1,
            minor_version=3,
        )

    return True
