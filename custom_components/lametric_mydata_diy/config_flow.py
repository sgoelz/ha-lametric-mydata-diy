"""Config flow for LaMetric My Data DIY."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

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
    CONF_TITLE,
    DEFAULT_FRAME_COUNT,
    DEFAULT_FRAMES,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TITLE,
    DOMAIN,
    FORMAT_OPTIONS,
    MAX_FRAME_COUNT,
    frame_key,
)


def _normalize_title(raw: Any, fallback: str = DEFAULT_TITLE) -> str:
    """Normalize a feed title."""
    title = str(raw or "").strip()
    return title or fallback


def _normalize_output_path(raw: Any) -> str:
    """Normalize and validate the output path inside /config."""
    value = str(raw or "").strip().lstrip("/")
    if not value:
        raise vol.Invalid("output_path_required")
    normalized = PurePosixPath(value)
    if not normalized.parts or normalized.parts[0] != "www":
        raise vol.Invalid("output_path_must_be_inside_www")
    if ".." in normalized.parts:
        raise vol.Invalid("output_path_must_be_inside_www")
    if normalized.suffix != ".json":
        raise vol.Invalid("output_path_must_end_with_json")
    return normalized.as_posix()


def _coerce_frame_count(raw: Any) -> int:
    """Coerce the configured frame count into the supported range."""
    try:
        value = int(raw)
    except (TypeError, ValueError) as err:
        raise vol.Invalid("frame_count_invalid") from err
    return max(1, min(MAX_FRAME_COUNT, value))


def _defaults_from_mapping(mapping: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return defaults merged with hardcoded fallbacks."""
    defaults: dict[str, Any] = {
        CONF_TITLE: DEFAULT_TITLE,
        CONF_OUTPUT_PATH: DEFAULT_OUTPUT_PATH,
        CONF_FRAME_COUNT: DEFAULT_FRAME_COUNT,
    }
    if mapping:
        defaults.update(mapping)

    for idx, frame in enumerate(DEFAULT_FRAMES, start=1):
        for key, value in frame.items():
            defaults.setdefault(frame_key(idx, key), value)

    return defaults


def _general_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    """Build the first-step schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_TITLE,
                default=defaults.get(CONF_TITLE, DEFAULT_TITLE),
            ): TextSelector(),
            vol.Required(
                CONF_OUTPUT_PATH,
                default=defaults.get(CONF_OUTPUT_PATH, DEFAULT_OUTPUT_PATH),
            ): TextSelector(),
            vol.Required(
                CONF_FRAME_COUNT,
                default=defaults.get(CONF_FRAME_COUNT, DEFAULT_FRAME_COUNT),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=MAX_FRAME_COUNT,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                )
            ),
        }
    )


def _frames_schema(defaults: Mapping[str, Any], frame_count: int) -> vol.Schema:
    """Build the frame-detail schema for the active frames only."""
    schema: dict[Any, Any] = {}

    for idx in range(1, frame_count + 1):
        schema[
            vol.Required(
                frame_key(idx, CONF_ENTITY_ID),
                default=defaults[frame_key(idx, CONF_ENTITY_ID)],
            )
        ] = EntitySelector(EntitySelectorConfig())
        schema[
            vol.Required(
                frame_key(idx, CONF_ICON),
                default=defaults[frame_key(idx, CONF_ICON)],
            )
        ] = NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=999999,
                step=1,
                mode=NumberSelectorMode.BOX,
            )
        )
        schema[
            vol.Required(
                frame_key(idx, CONF_DURATION),
                default=defaults[frame_key(idx, CONF_DURATION)],
            )
        ] = NumberSelector(
            NumberSelectorConfig(
                min=1000,
                max=10000,
                step=500,
                mode=NumberSelectorMode.BOX,
                unit_of_measurement="ms",
            )
        )
        schema[
            vol.Required(
                frame_key(idx, CONF_FORMAT),
                default=defaults[frame_key(idx, CONF_FORMAT)],
            )
        ] = SelectSelector(
            SelectSelectorConfig(
                options=FORMAT_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
            )
        )
        schema[
            vol.Optional(
                frame_key(idx, CONF_PREFIX),
                default=defaults[frame_key(idx, CONF_PREFIX)],
            )
        ] = TextSelector()
        schema[
            vol.Optional(
                frame_key(idx, CONF_SUFFIX),
                default=defaults[frame_key(idx, CONF_SUFFIX)],
            )
        ] = TextSelector()

    return vol.Schema(schema)


def _merge_frame_settings(
    defaults: Mapping[str, Any],
    frame_input: Mapping[str, Any],
    frame_count: int,
) -> dict[str, Any]:
    """Merge frame settings back into a full flattened config map."""
    merged = dict(defaults)
    merged[CONF_FRAME_COUNT] = frame_count

    for idx in range(1, MAX_FRAME_COUNT + 1):
        enabled = idx <= frame_count
        merged[frame_key(idx, CONF_ENABLED)] = enabled
        if idx > frame_count:
            continue

        merged[frame_key(idx, CONF_ENTITY_ID)] = str(
            frame_input.get(frame_key(idx, CONF_ENTITY_ID), defaults[frame_key(idx, CONF_ENTITY_ID)])
        ).strip()
        merged[frame_key(idx, CONF_ICON)] = int(
            frame_input.get(frame_key(idx, CONF_ICON), defaults[frame_key(idx, CONF_ICON)])
        )
        merged[frame_key(idx, CONF_DURATION)] = int(
            frame_input.get(frame_key(idx, CONF_DURATION), defaults[frame_key(idx, CONF_DURATION)])
        )
        merged[frame_key(idx, CONF_FORMAT)] = str(
            frame_input.get(frame_key(idx, CONF_FORMAT), defaults[frame_key(idx, CONF_FORMAT)])
        )
        merged[frame_key(idx, CONF_PREFIX)] = str(
            frame_input.get(frame_key(idx, CONF_PREFIX), defaults[frame_key(idx, CONF_PREFIX)])
        )
        merged[frame_key(idx, CONF_SUFFIX)] = str(
            frame_input.get(frame_key(idx, CONF_SUFFIX), defaults[frame_key(idx, CONF_SUFFIX)])
        )

    return merged


class LaMetricMyDataDIYConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LaMetric My Data DIY."""

    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._pending_data: dict[str, Any] | None = None

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "LaMetricMyDataDIYOptionsFlow":
        """Create the options flow."""
        return LaMetricMyDataDIYOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Collect general feed settings."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                self._pending_data = {
                    CONF_TITLE: _normalize_title(user_input.get(CONF_TITLE)),
                    CONF_OUTPUT_PATH: _normalize_output_path(user_input.get(CONF_OUTPUT_PATH)),
                    CONF_FRAME_COUNT: _coerce_frame_count(user_input.get(CONF_FRAME_COUNT)),
                }
                return await self.async_step_frames()
            except vol.Invalid as err:
                errors["base"] = str(err)

        return self.async_show_form(
            step_id="user",
            data_schema=_general_schema(_defaults_from_mapping(self._pending_data)),
            errors=errors,
        )

    async def async_step_frames(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Collect frame details."""
        if self._pending_data is None:
            return await self.async_step_user()

        frame_count = _coerce_frame_count(self._pending_data[CONF_FRAME_COUNT])
        defaults = _defaults_from_mapping(self._pending_data)

        if user_input is not None:
            merged = _merge_frame_settings(defaults, user_input, frame_count)
            title = _normalize_title(merged.get(CONF_TITLE))
            return self.async_create_entry(title=title, data=merged)

        return self.async_show_form(
            step_id="frames",
            data_schema=_frames_schema(defaults, frame_count),
        )


class LaMetricMyDataDIYOptionsFlow(config_entries.OptionsFlow):
    """Handle options for LaMetric My Data DIY."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry
        self._pending_options: dict[str, Any] | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage general options."""
        errors: dict[str, str] = {}

        defaults = _defaults_from_mapping(self._config_entry.options or self._config_entry.data)

        if user_input is not None:
            try:
                self._pending_options = dict(defaults)
                self._pending_options[CONF_TITLE] = _normalize_title(
                    user_input.get(CONF_TITLE),
                    self._config_entry.title,
                )
                self._pending_options[CONF_OUTPUT_PATH] = _normalize_output_path(
                    user_input.get(CONF_OUTPUT_PATH)
                )
                self._pending_options[CONF_FRAME_COUNT] = _coerce_frame_count(
                    user_input.get(CONF_FRAME_COUNT)
                )
                return await self.async_step_frames()
            except vol.Invalid as err:
                errors["base"] = str(err)

        view_defaults = dict(defaults)
        if self._pending_options is not None:
            view_defaults.update(self._pending_options)

        return self.async_show_form(
            step_id="init",
            data_schema=_general_schema(view_defaults),
            errors=errors,
        )

    async def async_step_frames(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage frame options."""
        defaults = _defaults_from_mapping(self._config_entry.options or self._config_entry.data)
        if self._pending_options is None:
            self._pending_options = dict(defaults)

        working_defaults = dict(defaults)
        working_defaults.update(self._pending_options)
        frame_count = _coerce_frame_count(working_defaults[CONF_FRAME_COUNT])

        if user_input is not None:
            merged = _merge_frame_settings(working_defaults, user_input, frame_count)
            title = _normalize_title(merged.get(CONF_TITLE), self._config_entry.title)
            self.hass.config_entries.async_update_entry(self._config_entry, title=title)
            return self.async_create_entry(data=merged)

        return self.async_show_form(
            step_id="frames",
            data_schema=_frames_schema(working_defaults, frame_count),
        )
