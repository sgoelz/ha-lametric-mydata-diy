# LaMetric My Data DIY for Home Assistant

Generate a LaMetric `My Data DIY` JSON feed directly from Home Assistant entities.

This custom integration lets you configure up to eight rotating LaMetric frames in the Home Assistant UI. Each frame maps one entity to:

- an icon ID
- a duration
- a display format (`power`, `percent`, `raw`)
- an optional prefix
- an optional suffix
- an enabled/disabled state

The integration writes a JSON file into `/config/www/...`, so the resulting URL can be polled directly by the LaMetric app:

```text
http://<home-assistant>:8123/local/lametric/my_data_diy.json
```

## Features

- HACS-compatible custom integration
- UI-based configuration via Config Flow
- Two-step config flow with a cleaner separation between general settings and frame details
- Option flow for later edits
- Multiple feeds via multiple config entries
- Up to 8 frames per feed
- Text-only frames by setting icon `0`
- Optional prefixes and suffixes per frame
- Automatic refresh on entity state changes
- Manual refresh service: `lametric_mydata_diy.refresh`
- Writes a static JSON feed for LaMetric `My Data DIY`

## Installation

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
   - one output path inside `/config` (default: `www/lametric/my_data_diy.json`)
   - active frame count
2. Frame settings for the active frames only
   - entity picker
   - icon ID
   - duration
   - format
   - optional prefix/suffix

You can browse official LaMetric icons in the [LaMetric icon gallery](https://developer.lametric.com/icons).

Recommended defaults for a typical energy dashboard setup:

- `sensor.total_dc_power` + icon `27464` + `power`
- `sensor.battery_level` + icon `389` + `percent`
- `sensor.skoda_enyaq_batteriestand` + icon `2809` + `percent`
- `sensor.batteriestand` + icon `2818` + `percent`

## HACS notes

This repository includes the basics HACS usually expects for a custom integration repository:

- `hacs.json`
- `manifest.json`
- brand assets inside the integration directory
- validation via `hacs/action` and `hassfest`
- issue templates and installation documentation

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
  {"icon":2809,"text":"43%","duration":3000},
  {"icon":2818,"text":"76%","duration":3000}
]}
```

## Roadmap

- additional formatters
- optional direct HTTP view instead of file output
- diagnostics and repair flow
- per-frame icon previews or curated presets
