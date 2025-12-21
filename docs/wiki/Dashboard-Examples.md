# Dashboard Examples

Lovelace card configurations for controlling Sonorium from your Home Assistant dashboard.

## Basic Session Control Card

A simple card to control a single session. Replace `bedroom` with your session name.

```yaml
type: entities
title: Bedroom Ambiance
show_header_toggle: false
entities:
  - entity: select.sonorium_bedroom_theme
    name: Theme
  - entity: select.sonorium_bedroom_preset
    name: Preset
  - entity: number.sonorium_bedroom_volume
    name: Volume
  - entity: switch.sonorium_bedroom_play
    name: Play
  - entity: sensor.sonorium_bedroom_status
    name: Status
```

---

## Global Control Card

Control any session from a single card using the global entities.

```yaml
type: entities
title: Sonorium
show_header_toggle: false
entities:
  - entity: select.sonorium_session
    name: Session
  - entity: switch.sonorium_global_play
    name: Play
  - entity: select.sonorium_global_theme
    name: Theme
  - entity: select.sonorium_preset
    name: Preset
  - entity: number.sonorium_volume
    name: Volume
  - entity: sensor.sonorium_global_active_sessions
    name: Active Sessions
  - entity: switch.sonorium_stop_all
    name: Stop All
```

---

## Compact Button Card

A minimal card with just play/stop and theme selection.

```yaml
type: horizontal-stack
cards:
  - type: button
    entity: switch.sonorium_bedroom_play
    name: Bedroom
    icon: mdi:music
    tap_action:
      action: toggle
  - type: button
    entity: switch.sonorium_office_play
    name: Office
    icon: mdi:music
    tap_action:
      action: toggle
```

---

## Multi-Room Overview

See all sessions at a glance with a glance card.

```yaml
type: glance
title: Ambient Sound
entities:
  - entity: switch.sonorium_bedroom_play
    name: Bedroom
  - entity: switch.sonorium_office_play
    name: Office
  - entity: switch.sonorium_living_room_play
    name: Living Room
  - entity: sensor.sonorium_global_active_sessions
    name: Active
```

---

## Vertical Stack Layout

A comprehensive control panel using vertical stacks.

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: "## Sonorium Ambient Sound"

  - type: horizontal-stack
    cards:
      - type: button
        entity: switch.sonorium_global_play
        name: Play
        icon: mdi:play
        tap_action:
          action: toggle
      - type: button
        entity: switch.sonorium_stop_all
        name: Stop All
        icon: mdi:stop
        tap_action:
          action: toggle

  - type: entities
    entities:
      - entity: select.sonorium_session
        name: Session
      - entity: select.sonorium_global_theme
        name: Theme
      - entity: select.sonorium_preset
        name: Preset

  - type: entities
    entities:
      - entity: number.sonorium_volume
        name: Volume
```

---

## Conditional Card

Show controls only when a session is playing.

```yaml
type: conditional
conditions:
  - entity: switch.sonorium_bedroom_play
    state: "on"
card:
  type: entities
  title: Now Playing - Bedroom
  entities:
    - entity: select.sonorium_bedroom_theme
      name: Theme
    - entity: select.sonorium_bedroom_preset
      name: Preset
    - entity: number.sonorium_bedroom_volume
      name: Volume
    - entity: switch.sonorium_bedroom_play
      name: Stop
```

---

## Mushroom Cards (if installed)

If you have the Mushroom cards integration, here's a modern-looking layout.

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-title-card
    title: Ambient Sound
    subtitle: Sonorium

  - type: horizontal-stack
    cards:
      - type: custom:mushroom-entity-card
        entity: switch.sonorium_bedroom_play
        name: Bedroom
        icon_color: blue
        tap_action:
          action: toggle
      - type: custom:mushroom-entity-card
        entity: switch.sonorium_office_play
        name: Office
        icon_color: green
        tap_action:
          action: toggle

  - type: custom:mushroom-select-card
    entity: select.sonorium_bedroom_theme
    name: Theme

  - type: custom:mushroom-number-card
    entity: number.sonorium_bedroom_volume
    name: Volume
    display_mode: slider
```

---

## Grid Layout for Multiple Sessions

A grid layout showing all sessions with play buttons and volume.

```yaml
type: grid
columns: 2
square: false
cards:
  - type: entities
    title: Bedroom
    entities:
      - entity: switch.sonorium_bedroom_play
        name: Play
      - entity: select.sonorium_bedroom_theme
        name: Theme
      - entity: number.sonorium_bedroom_volume
        name: Volume

  - type: entities
    title: Office
    entities:
      - entity: switch.sonorium_office_play
        name: Play
      - entity: select.sonorium_office_theme
        name: Theme
      - entity: number.sonorium_office_volume
        name: Volume

  - type: entities
    title: Living Room
    entities:
      - entity: switch.sonorium_living_room_play
        name: Play
      - entity: select.sonorium_living_room_theme
        name: Theme
      - entity: number.sonorium_living_room_volume
        name: Volume
```

---

## Tips

### Finding Your Entity Names

1. Go to **Developer Tools > States** in Home Assistant
2. Filter by "sonorium" to see all entities
3. Note the exact entity IDs for your sessions

### Entity ID Format

Session names are converted to entity IDs:
- Spaces become underscores
- Names are lowercased
- Special characters are removed

| Session Name | Entity Prefix |
|--------------|---------------|
| Bedroom | `sonorium_bedroom` |
| Master Bedroom | `sonorium_master_bedroom` |
| Kids Room | `sonorium_kids_room` |
| Office 2 | `sonorium_office_2` |

### Updating Entity Names

If you rename a session in Sonorium, the old entities will become unavailable and new ones will be created. You may need to update your dashboard cards with the new entity IDs.
