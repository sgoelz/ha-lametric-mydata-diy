# LaMetric My Data DIY for Home Assistant

Generate a LaMetric `My Data DIY` JSON feed directly from Home Assistant entities.

This custom integration lets you configure up to eight rotating LaMetric frames in the Home Assistant UI. Each frame maps one entity to:

- an icon ID
- a duration
- a display format (`power`, `percent`, `energy`, `time`, `raw`)
- an optional prefix
- an optional suffix
- output only under Home Assistant's `www/...` folder

The integration writes a JSON file into Home Assistant's `www/...` folder, so the resulting URL can be polled directly by the LaMetric app:

```text
http://<home-assistant>:8123/local/lametric/my_data_diy.json
```

## Features

- HACS-compatible custom integration
- UI-based configuration via Config Flow
- Two-step config flow with a cleaner separation between general settings and frame details
- Collapsible per-frame sections in setup and options
- Option flow for later edits
- Multiple feeds via multiple config entries
- Up to 8 frames per feed
- Built-in value formats for `power`, `percent`, `energy`, `time`, and `raw`
- Dedicated `Use current time` preset per frame
- Iconless text frames by setting icon `0`
- Optional prefixes and suffixes per frame
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
   - feed title
   - one output path inside your Home Assistant config directory (default: `www/lametric/my_data_diy.json`)
   - active frame count
2. Frame settings for the active frames only
   - current-time toggle
   - entity field
   - icon ID
   - duration
   - format
   - optional prefix/suffix

Active frames are controlled by the configured frame count. In the second step, each frame is shown
as its own collapsible section. Setting icon `0` removes the icon and keeps the text.

You can browse official LaMetric icons in the [LaMetric icon gallery](https://developer.lametric.com/icons).

Recommended defaults for a typical energy dashboard setup:

- `sensor.total_dc_power` + icon `27464` + `power`
- `sensor.battery_level` + icon `389` + `percent`
- `sensor.skoda_enyaq_batteriestand` + icon `2809` + `percent`
- `sensor.batteriestand` + icon `2818` + `percent`
- `sensor.daily_imported_energy` + icon `7959` + `energy`
- no entity + icon `0` + `time`

The `energy` formatter reads the entity unit and scales supported values automatically between
`Wh`, `kWh`, `MWh` and `GWh`.

The `time` formatter renders the current Home Assistant system time in `HH:MM`.

The `Use current time` preset is the simplest way to configure a clock frame:

- no entity is required
- the feed refreshes automatically every minute
- if the icon is set to `0`, the integration uses a built-in LaMetric-style clock icon

You can also keep using the plain `time` value format if you prefer.

## HACS notes

This repository includes the basics HACS usually expects for a custom integration repository:

- `hacs.json`
- `manifest.json`
- brand assets inside the integration directory
- validation via `hacs/action` and `hassfest`
- issue templates and installation documentation

## HACS default repository checklist

If you want to propose this repository for inclusion in the default HACS list later, make sure you have:

- a public GitHub repository with Issues enabled
- a clear repository description and relevant topics
- at least one published GitHub Release
- passing `hacs/action` and `hassfest`
- installation and usage documentation in the README

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
  {"text":"11:42","duration":3000,"icon":"data:image/png;base64,..."}
]}
```

## Roadmap

- additional formatters such as `temperature`, `voltage`, `current`, or configurable decimals
- animated LaMetric icon codes in addition to numeric icon IDs
- optional direct HTTP view instead of file output
- diagnostics and repair flow
- per-frame icon previews or curated presets
