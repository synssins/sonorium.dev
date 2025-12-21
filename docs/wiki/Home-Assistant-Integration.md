# Home Assistant Integration

Sonorium integrates with Home Assistant through MQTT Discovery, automatically creating entities that you can use in dashboards, automations, and scripts.

## Overview

When running as a Home Assistant addon, Sonorium publishes MQTT entities for each session (channel) you create. These entities allow you to:

- Control playback from HA dashboards
- Create automations (morning alarms, scheduled soundscapes)
- Include Sonorium in scenes
- Build custom Lovelace cards

## Requirements

- Home Assistant with MQTT integration configured
- Sonorium addon installed and running
- At least one session/channel created in Sonorium

## How It Works

1. **Create Sessions in Sonorium** - Use the Sonorium web UI to create sessions (channels) with names like "Bedroom", "Office", or "Living Room"
2. **Entities Auto-Created** - Sonorium publishes MQTT discovery configs, and HA automatically creates entities
3. **Control from HA** - Use the entities in dashboards and automations

## Entity Naming

Entity IDs are based on your session names:

| Session Name | Entity Pattern |
|--------------|----------------|
| Bedroom | `*.sonorium_bedroom_*` |
| Living Room | `*.sonorium_living_room_*` |
| Office Music | `*.sonorium_office_music_*` |

Spaces and special characters are converted to underscores, and names are lowercased.

## Next Steps

- [MQTT Entities Reference](MQTT-Entities) - Complete list of all entities
- [Dashboard Examples](Dashboard-Examples) - Lovelace card configurations
- [Automation Examples](Automation-Examples) - Wake-up alarms and schedules
