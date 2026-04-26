"""Config flow for LaMetric My Data DIY."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import section
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
)

from .const import (
    CONF_CURRENT_TIME,
    CONF_DELIVERY_MODE,
    CONF_DURATION,
    CONF_ENABLED,
    CONF_ENTITY_ID,
    CONF_FRAME_COUNT,
    CONF_FORMAT,
    CONF_HTTP_SLUG,
    CONF_PRESET,
    CONF_HIDE_WHEN,
    CONF_ICON,
    CONF_OUTPUT_PATH,
    CONF_PREFIX,
    CONF_SUFFIX,
    CONF_TITLE,
    DEFAULT_FRAME_COUNT,
    DEFAULT_DELIVERY_MODE,
    DEFAULT_FRAMES,
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TITLE,
    DELIVERY_MODE_FILE,
    DELIVERY_MODE_HTTP,
    DELIVERY_MODE_OPTIONS,
    DOMAIN,
    FRAME_PRESET_VALUES,
    FORMAT_OPTIONS,
    HIDE_WHEN_OPTIONS,
    MAX_FRAME_COUNT,
    PRESET_NONE,
    PRESET_OPTIONS,
    frame_key,
)
from .util import default_http_slug, slugify_http_value


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
        CONF_DELIVERY_MODE: DEFAULT_DELIVERY_MODE,
        CONF_TITLE: DEFAULT_TITLE,
        CONF_OUTPUT_PATH: DEFAULT_OUTPUT_PATH,
        CONF_FRAME_COUNT: DEFAULT_FRAME_COUNT,
    }
    if mapping:
        defaults.update(mapping)
    defaults.setdefault(
        CONF_HTTP_SLUG,
        default_http_slug(defaults.get(CONF_TITLE), "lametric-feed"),
    )

    for idx, frame in enumerate(DEFAULT_FRAMES, start=1):
        for key, value in frame.items():
            defaults.setdefault(frame_key(idx, key), value)

    return defaults


def _general_schema(defaults: Mapping[str, Any]) -> vol.Schema:
    """Build the first-step schema."""
    selected_mode = str(defaults.get(CONF_DELIVERY_MODE, DEFAULT_DELIVERY_MODE))
    schema: dict[Any, Any] = {
        vol.Required(
            CONF_DELIVERY_MODE,
            default=selected_mode,
        ): SelectSelector(
            SelectSelectorConfig(
                options=DELIVERY_MODE_OPTIONS,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key="delivery_mode",
            )
        ),
        vol.Required(
            CONF_TITLE,
            default=defaults.get(CONF_TITLE, DEFAULT_TITLE),
        ): TextSelector(),
    }
    if selected_mode == DELIVERY_MODE_HTTP:
        schema[
            vol.Required(
                CONF_HTTP_SLUG,
                default=defaults.get(
                    CONF_HTTP_SLUG,
                    default_http_slug(defaults.get(CONF_TITLE), "lametric-feed"),
                ),
            )
        ] = TextSelector()
    else:
        schema[
            vol.Required(
                CONF_OUTPUT_PATH,
                default=defaults.get(CONF_OUTPUT_PATH, DEFAULT_OUTPUT_PATH),
            )
        ] = TextSelector()

    schema[
        vol.Required(
            CONF_FRAME_COUNT,
            default=defaults.get(CONF_FRAME_COUNT, DEFAULT_FRAME_COUNT),
        )
    ] = NumberSelector(
        NumberSelectorConfig(
            min=1,
            max=MAX_FRAME_COUNT,
            step=1,
            mode=NumberSelectorMode.BOX,
        )
    )
    return vol.Schema(schema)


def _normalize_http_slug(raw: Any) -> str:
    """Normalize and validate an HTTP endpoint slug."""
    value = str(raw or "").strip()
    if not value:
        raise vol.Invalid("http_slug_required")
    slug = slugify_http_value(value)
    if not slug:
        raise vol.Invalid("http_slug_invalid")
    return slug


def _frames_schema(defaults: Mapping[str, Any], frame_count: int) -> vol.Schema:
    """Build the frame-detail schema for the active frames only."""
    schema: dict[Any, Any] = {}
    section_entity_key = "entity"

    for idx in range(1, frame_count + 1):
        schema[vol.Required(f"frame_{idx}")] = section(
            vol.Schema(
                {
                    vol.Optional(
                        CONF_PRESET,
                        default=PRESET_NONE,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=PRESET_OPTIONS,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="frame_preset",
                        )
                    ),
                    vol.Optional(
                        CONF_CURRENT_TIME,
                        default=defaults[frame_key(idx, CONF_CURRENT_TIME)],
                    ): BooleanSelector(),
                    vol.Optional(
                        section_entity_key,
                        default=defaults[frame_key(idx, CONF_ENTITY_ID)],
                    ): TextSelector(),
                    vol.Optional(
                        CONF_ICON,
                        default=defaults[frame_key(idx, CONF_ICON)],
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=0,
                            max=999999,
                            step=1,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_DURATION,
                        default=defaults[frame_key(idx, CONF_DURATION)],
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1000,
                            max=10000,
                            step=500,
                            mode=NumberSelectorMode.BOX,
                            unit_of_measurement="ms",
                        )
                    ),
                    vol.Optional(
                        CONF_FORMAT,
                        default=defaults[frame_key(idx, CONF_FORMAT)],
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=FORMAT_OPTIONS,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="value_format",
                        )
                    ),
                    vol.Optional(
                        CONF_HIDE_WHEN,
                        default=defaults[frame_key(idx, CONF_HIDE_WHEN)],
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=HIDE_WHEN_OPTIONS,
                            mode=SelectSelectorMode.DROPDOWN,
                            translation_key="hide_when",
                        )
                    ),
                    vol.Optional(
                        CONF_PREFIX,
                        default=defaults[frame_key(idx, CONF_PREFIX)],
                    ): TextSelector(),
                    vol.Optional(
                        CONF_SUFFIX,
                        default=defaults[frame_key(idx, CONF_SUFFIX)],
                    ): TextSelector(),
                }
            ),
            {"collapsed": idx > 1},
        )

    return vol.Schema(schema)


def _apply_frame_preset(
    defaults: Mapping[str, Any],
    section_input: Mapping[str, Any],
    idx: int,
) -> dict[str, Any]:
    """Apply a selected frame preset without clobbering explicit overrides."""
    preset = str(section_input.get(CONF_PRESET, PRESET_NONE))
    if preset == PRESET_NONE:
        return dict(section_input)

    preset_values = FRAME_PRESET_VALUES.get(preset)
    if preset_values is None:
        return dict(section_input)

    applied = dict(section_input)
    field_aliases = {CONF_ENTITY_ID: "entity"}

    for key, preset_value in preset_values.items():
        form_key = field_aliases.get(key, key)
        default_value = defaults[frame_key(idx, key)]
        current_value = section_input.get(form_key, default_value)

        # The clock preset should always clear the entity to avoid stale values.
        if key == CONF_ENTITY_ID:
            applied[form_key] = preset_value
            continue

        if current_value == default_value:
            applied[form_key] = preset_value

    return applied


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

        section_input = _apply_frame_preset(
            defaults,
            frame_input.get(f"frame_{idx}", {}),
            idx,
        )
        merged[frame_key(idx, CONF_CURRENT_TIME)] = bool(
            section_input.get(
                CONF_CURRENT_TIME,
                defaults[frame_key(idx, CONF_CURRENT_TIME)],
            )
        )
        merged[frame_key(idx, CONF_ENTITY_ID)] = str(
            section_input.get("entity", defaults[frame_key(idx, CONF_ENTITY_ID)])
        ).strip()
        merged[frame_key(idx, CONF_ICON)] = int(
            section_input.get(CONF_ICON, defaults[frame_key(idx, CONF_ICON)])
        )
        merged[frame_key(idx, CONF_DURATION)] = int(
            section_input.get(CONF_DURATION, defaults[frame_key(idx, CONF_DURATION)])
        )
        merged[frame_key(idx, CONF_FORMAT)] = str(
            section_input.get(CONF_FORMAT, defaults[frame_key(idx, CONF_FORMAT)])
        )
        merged[frame_key(idx, CONF_HIDE_WHEN)] = str(
            section_input.get(CONF_HIDE_WHEN, defaults[frame_key(idx, CONF_HIDE_WHEN)])
        )
        merged[frame_key(idx, CONF_PREFIX)] = str(
            section_input.get(CONF_PREFIX, defaults[frame_key(idx, CONF_PREFIX)])
        )
        merged[frame_key(idx, CONF_SUFFIX)] = str(
            section_input.get(CONF_SUFFIX, defaults[frame_key(idx, CONF_SUFFIX)])
        )

    return merged


def _entry_slug(mapping: Mapping[str, Any] | None) -> str:
    """Return the stored HTTP slug for one config mapping."""
    defaults = _defaults_from_mapping(mapping)
    return str(defaults.get(CONF_HTTP_SLUG, "")).strip()


class LaMetricMyDataDIYConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for LaMetric My Data DIY."""

    VERSION = 1
    MINOR_VERSION = 4

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._pending_data: dict[str, Any] | None = None

    def _slug_in_use(self, slug: str) -> bool:
        """Return whether the HTTP slug is already used by another entry."""
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            entry_data = dict(entry.data)
            entry_data.update(entry.options)
            if str(entry_data.get(CONF_DELIVERY_MODE, DEFAULT_DELIVERY_MODE)) != DELIVERY_MODE_HTTP:
                continue
            if _entry_slug(entry_data) == slug:
                return True
        return False

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
                defaults = _defaults_from_mapping(self._pending_data)
                selected_mode = str(
                    user_input.get(CONF_DELIVERY_MODE, defaults.get(CONF_DELIVERY_MODE, DEFAULT_DELIVERY_MODE))
                )
                title = _normalize_title(user_input.get(CONF_TITLE))
                pending_data = dict(defaults)
                pending_data[CONF_DELIVERY_MODE] = selected_mode
                pending_data[CONF_TITLE] = title
                pending_data[CONF_FRAME_COUNT] = _coerce_frame_count(user_input.get(CONF_FRAME_COUNT))

                if selected_mode == DELIVERY_MODE_HTTP:
                    if selected_mode != defaults.get(CONF_DELIVERY_MODE):
                        pending_data[CONF_HTTP_SLUG] = default_http_slug(title, "lametric-feed")
                        self._pending_data = pending_data
                        return self.async_show_form(
                            step_id="user",
                            data_schema=_general_schema(_defaults_from_mapping(self._pending_data)),
                        )
                    pending_data[CONF_HTTP_SLUG] = _normalize_http_slug(user_input.get(CONF_HTTP_SLUG))
                    if self._slug_in_use(pending_data[CONF_HTTP_SLUG]):
                        raise vol.Invalid("http_slug_not_unique")
                else:
                    if selected_mode != defaults.get(CONF_DELIVERY_MODE):
                        self._pending_data = pending_data
                        return self.async_show_form(
                            step_id="user",
                            data_schema=_general_schema(_defaults_from_mapping(self._pending_data)),
                        )
                    pending_data[CONF_OUTPUT_PATH] = _normalize_output_path(user_input.get(CONF_OUTPUT_PATH))

                self._pending_data = pending_data
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

    def _slug_in_use(self, slug: str) -> bool:
        """Return whether the HTTP slug is already used by another entry."""
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if entry.entry_id == self._config_entry.entry_id:
                continue
            entry_data = dict(entry.data)
            entry_data.update(entry.options)
            if str(entry_data.get(CONF_DELIVERY_MODE, DEFAULT_DELIVERY_MODE)) != DELIVERY_MODE_HTTP:
                continue
            if _entry_slug(entry_data) == slug:
                return True
        return False

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage general options."""
        errors: dict[str, str] = {}

        defaults = _defaults_from_mapping(self._config_entry.options or self._config_entry.data)

        if user_input is not None:
            try:
                selected_mode = str(
                    user_input.get(CONF_DELIVERY_MODE, defaults.get(CONF_DELIVERY_MODE, DEFAULT_DELIVERY_MODE))
                )
                title = _normalize_title(
                    user_input.get(CONF_TITLE),
                    self._config_entry.title,
                )
                self._pending_options = dict(defaults)
                self._pending_options[CONF_DELIVERY_MODE] = selected_mode
                self._pending_options[CONF_TITLE] = title
                self._pending_options[CONF_FRAME_COUNT] = _coerce_frame_count(
                    user_input.get(CONF_FRAME_COUNT)
                )

                if selected_mode == DELIVERY_MODE_HTTP:
                    if selected_mode != defaults.get(CONF_DELIVERY_MODE):
                        self._pending_options[CONF_HTTP_SLUG] = default_http_slug(title, "lametric-feed")
                        view_defaults = dict(defaults)
                        view_defaults.update(self._pending_options)
                        return self.async_show_form(
                            step_id="init",
                            data_schema=_general_schema(view_defaults),
                        )
                    self._pending_options[CONF_HTTP_SLUG] = _normalize_http_slug(
                        user_input.get(CONF_HTTP_SLUG)
                    )
                    if self._slug_in_use(self._pending_options[CONF_HTTP_SLUG]):
                        raise vol.Invalid("http_slug_not_unique")
                else:
                    if selected_mode != defaults.get(CONF_DELIVERY_MODE):
                        view_defaults = dict(defaults)
                        view_defaults.update(self._pending_options)
                        return self.async_show_form(
                            step_id="init",
                            data_schema=_general_schema(view_defaults),
                        )
                    self._pending_options[CONF_OUTPUT_PATH] = _normalize_output_path(
                        user_input.get(CONF_OUTPUT_PATH)
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
