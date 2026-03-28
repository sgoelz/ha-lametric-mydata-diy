"""LaMetric My Data DIY integration."""

from __future__ import annotations

from collections.abc import Callable
import json
import logging
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import Event, HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .const import (
    CONF_DURATION,
    CONF_ENABLED,
    CONF_ENTITY_ID,
    CONF_FRAME_COUNT,
    CONF_FORMAT,
    CONF_ICON,
    CONF_OUTPUT_PATH,
    CONF_PREFIX,
    CONF_SUFFIX,
    DEFAULT_FRAME_COUNT,
    DEFAULT_FRAMES,
    DEFAULT_OUTPUT_PATH,
    DOMAIN,
    FORMAT_PERCENT,
    FORMAT_POWER,
    MAX_FRAME_COUNT,
    SERVICE_REFRESH,
    frame_key,
)

_LOGGER = logging.getLogger(__name__)
Unsub = Callable[[], None]


def _parse_float(raw: str | None, default: float = 0.0) -> float:
    try:
        return float(str(raw).replace(",", "."))
    except (TypeError, ValueError):
        return default


def _format_value(raw: str | None, value_format: str) -> str:
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

    if raw in (None, "", "unknown", "unavailable"):
        return "--"

    return str(raw)


def _apply_affixes(value: str, prefix: str, suffix: str) -> str:
    """Apply optional prefix and suffix to a formatted value."""
    return f"{prefix}{value}{suffix}"


def _entry_config(entry: ConfigEntry) -> dict[str, Any]:
    """Return merged entry config from data and options."""
    config = dict(entry.data)
    config.update(entry.options)
    return config


def _frame_config(config: dict[str, Any], index: int) -> dict[str, Any]:
    """Extract one frame config from flattened config-entry data."""
    defaults = DEFAULT_FRAMES[index - 1]
    return {
        CONF_ENABLED: bool(config.get(frame_key(index, CONF_ENABLED), defaults[CONF_ENABLED])),
        CONF_ENTITY_ID: config.get(frame_key(index, CONF_ENTITY_ID), defaults[CONF_ENTITY_ID]),
        CONF_ICON: int(config.get(frame_key(index, CONF_ICON), defaults[CONF_ICON])),
        CONF_DURATION: int(config.get(frame_key(index, CONF_DURATION), defaults[CONF_DURATION])),
        CONF_FORMAT: config.get(frame_key(index, CONF_FORMAT), defaults[CONF_FORMAT]),
        CONF_PREFIX: str(config.get(frame_key(index, CONF_PREFIX), defaults[CONF_PREFIX])),
        CONF_SUFFIX: str(config.get(frame_key(index, CONF_SUFFIX), defaults[CONF_SUFFIX])),
    }


def _write_payload(target: Path, payload: dict[str, Any]) -> None:
    """Write payload atomically."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path = target.with_suffix(f"{target.suffix}.tmp")
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
            entity_id = frame[CONF_ENTITY_ID]
            if entity_id and entity_id not in entities:
                entities.append(entity_id)
        return entities

    async def async_start(self) -> None:
        """Start tracking entity changes."""
        self._unsubs.append(
            async_track_state_change_event(
                self.hass,
                self.tracked_entities,
                self._handle_state_change,
            )
        )
        self._unsubs.append(
            self.hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STARTED,
                self._handle_started,
            )
        )
        await self.async_write_payload()

    async def async_stop(self) -> None:
        """Stop listeners."""
        if self._delayed_unsub:
            self._delayed_unsub()
            self._delayed_unsub = None
        while self._unsubs:
            self._unsubs.pop()()

    async def async_write_payload(self) -> None:
        """Render and write the current payload."""
        try:
            output_path = self.output_path
        except ValueError as err:
            _LOGGER.error("Invalid output path for %s: %s", self.entry.entry_id, err)
            return

        payload = {"frames": []}
        for idx in range(1, self.frame_count + 1):
            frame = _frame_config(self.config, idx)
            if not frame[CONF_ENABLED] or not frame[CONF_ENTITY_ID]:
                continue
            state = self.hass.states.get(frame[CONF_ENTITY_ID])
            value = _format_value(state.state if state else None, frame[CONF_FORMAT])
            payload_frame = {
                "text": _apply_affixes(value, frame[CONF_PREFIX], frame[CONF_SUFFIX]),
                "duration": frame[CONF_DURATION],
            }
            if frame[CONF_ICON] > 0:
                payload_frame["icon"] = frame[CONF_ICON]
            payload["frames"].append(payload_frame)

        await self.hass.async_add_executor_job(_write_payload, output_path, payload)
        _LOGGER.debug("Updated LaMetric feed for %s at %s", self.entry.entry_id, output_path)

    async def _handle_state_change(self, event: Event) -> None:
        """Update feed when a tracked entity changes."""
        await self.async_write_payload()

    async def _handle_started(self, event: Event) -> None:
        """Delay first write slightly after startup."""
        del event

        async def _delayed_write(_now: Any) -> None:
            self._delayed_unsub = None
            await self.async_write_payload()

        self._delayed_unsub = async_call_later(self.hass, 15, _delayed_write)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up LaMetric My Data DIY from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    writer = LaMetricFeedWriter(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = writer
    await writer.async_start()

    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        async def _handle_refresh(call: ServiceCall) -> None:
            entry_id = call.data.get("entry_id")
            writers: dict[str, LaMetricFeedWriter] = hass.data[DOMAIN]
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
    writer: LaMetricFeedWriter = hass.data[DOMAIN].pop(entry.entry_id)
    await writer.async_stop()

    if not hass.data[DOMAIN] and hass.services.has_service(DOMAIN, SERVICE_REFRESH):
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
            minor_version=2,
        )

    return True
