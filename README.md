# LaMetric My Data DIY for Home Assistant

Generate a LaMetric `My Data DIY` JSON feed directly from Home Assistant entities.

This custom integration lets you configure up to eight rotating LaMetric frames in the Home Assistant UI. Each frame maps one entity to:

- an icon ID
- a duration
- a display format (`power`, `percent`, `energy`, `temperature`, `voltage`, `current`, `time`, `raw`)
- an optional preset for common frame types
- an optional prefix
- an optional suffix
- delivery either as a static file or as a direct HTTP endpoint

The default file mode writes a JSON file into Home Assistant's `www/...` folder, so the resulting URL can be polled directly by the LaMetric app:

```text
http://<home-assistant>:8123/local/lametric/my_data_diy.json
```

Milestone 1 of the HTTP mode also supports a direct endpoint per config entry:

```text
http://<home-assistant>:8123/api/lametric_mydata_diy/<entry_id>
```

## Features

- HACS-compatible custom integration
- UI-based configuration via Config Flow
- Two-step config flow with a cleaner separation between general settings and frame details
- Collapsible per-frame sections in setup and options
- Delivery mode selector for static file or direct HTTP endpoint
- One-click frame presets for common LaMetric use cases
- Option flow for later edits
- Multiple feeds via multiple config entries
- Up to 8 frames per feed
- Built-in value formats for `power`, `percent`, `energy`, `temperature`, `voltage`, `current`, `time`, and `raw`
- Dedicated `Use current time` preset per frame
- Iconless text frames by setting icon `0`
- Optional prefixes and suffixes per frame
- Optional per-frame hiding for `0`, empty, or unavailable values
- Automatic refresh on entity state changes
- Automatic minute-based refresh for time frames
- Human-friendly German and English labels in setup and options
- Manual refresh service: `lametric_mydata_diy.refresh`
- Writes a static JSON feed for LaMetric `My Data DIY`

## Installation

[![Open your Home Assistant instance and add this repository inside HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=sgoelz&repository=ha-lametric-mydata-diy&category=integration)

### HACS

1. Add this repository as a custom repository in HACS.
2. Select type `Integration`.
3. Install `LaMetric My Data DIY`.
4. Restart Home Assistant.
5. Go to `Settings -> Devices & Services -> Add Integration`.

### Manual

Copy `custom_components/lametric_mydata_diy` into your Home Assistant `custom_components` folder and restart Home Assistant.

## Configuration

The setup runs in two steps:

1. General settings
   - delivery mode
   - feed title
   - one output path inside your Home Assistant config directory for file mode (default: `www/lametric/my_data_diy.json`)
   - active frame count
2. Frame settings for the active frames only
   - optional preset
   - current-time toggle
   - entity field
   - icon ID
   - duration
   - format
   - optional hide rule for zero or empty values
   - optional prefix/suffix

Active frames are controlled by the configured frame count. In the second step, each frame is shown
as its own collapsible section. Setting icon `0` removes the icon and keeps the text for regular
value frames.

Frame presets help fill common combinations quickly. They can prefill icon and format suggestions
for common use cases such as power, battery percentage, energy, temperature, voltage, current, and
clock frames. Presets are apply-on-save helpers: they set the actual frame fields when you save, but
the preset selector itself is not stored and will show `No preset` / `Keine Vorlage` when you reopen
the options. The applied values remain editable afterwards.

You can browse official LaMetric icons in the [LaMetric icon gallery](https://developer.lametric.com/icons).

Example frame combinations:

- a power sensor + icon `27464` + `power`
- a battery percentage sensor + icon `389` + `percent`
- an energy sensor + icon `7959` + `energy`
- a temperature sensor + icon `2056` + `temperature`
- a voltage sensor + icon `603` + `voltage`
- no entity + icon `7645` + `time`

The `energy` formatter reads the entity unit and scales supported values automatically between
`Wh`, `kWh`, `MWh` and `GWh`.

The `temperature`, `voltage`, and `current` formatters read the entity unit automatically and
render compact values such as `35.1°C`, `422.1V`, or `0.2A`.

- `temperature` supports `°C` and `°F`
- `voltage` supports `V` and `mV`
- `current` supports `A` and `mA`

Each frame can also be hidden automatically when the source value is `0`, empty, or unavailable.
This is useful for values that should disappear entirely from the rotation instead of showing
`0W` or `--`.

The `time` formatter renders the current Home Assistant system time in `HH:MM`.

The `Use current time` preset is the simplest way to configure a clock frame:

- no entity is required
- the feed refreshes automatically every minute
- the default clock icon is `7645`
- if a time frame is saved with icon `0`, the integration falls back to the default clock icon

You can also keep using the plain `time` value format if you prefer.

## Delivery modes

### File mode

This is the default mode.

- writes the rendered payload into `www/...`
- feed is reachable through `/local/...`
- easiest option for typical LaMetric `My Data DIY` setups

### HTTP mode

This mode serves the payload directly from the integration without writing a file.

- feed is reachable under `/api/lametric_mydata_diy/<entry_id>`
- designed for local-network usage in Milestone 1
- the endpoint path currently uses the Home Assistant config entry ID
- no token-based public sharing is included yet

The rendering logic is the same in both modes, including current-time frames and hide rules.

## Service

You can force a refresh manually:

```yaml
service: lametric_mydata_diy.refresh
data: {}
```

Optional:

```yaml
service: lametric_mydata_diy.refresh
data:
  entry_id: YOUR_CONFIG_ENTRY_ID
```

## Output example

```json
{"frames":[
  {"icon":27464,"text":"1.2kW","duration":4000},
  {"icon":389,"text":"59%","duration":3000},
  {"icon":7959,"text":"6.4kWh","duration":3000},
  {"icon":2818,"text":"76%","duration":3000}
]}
```

Clock-frame example:

```json
{"frames":[
  {"text":"11:42","duration":3000,"icon":7645}
]}
```

## Roadmap

- configurable decimal precision for generic numeric values
- optional direct HTTP view instead of file output
- diagnostics and repair flow
- richer icon guidance or a lightweight icon picker
