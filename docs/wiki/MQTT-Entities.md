# MQTT Entities Reference

Sonorium publishes the following entities for each session/channel via MQTT Discovery.

## Entity Naming Convention

All entities follow this pattern:
```
{domain}.sonorium_{session_name}_{entity_type}
```

Where `{session_name}` is your session name with spaces converted to underscores and lowercased.

**Example:** A session named "Master Bedroom" creates entities like:
- `switch.sonorium_master_bedroom_play`
- `select.sonorium_master_bedroom_theme`
- `number.sonorium_master_bedroom_volume`

---

## Per-Session Entities

These entities are created for each session/channel you create in Sonorium.

### Play Switch
**Entity:** `switch.sonorium_{session}_play`

Controls playback for this session.

| State | Description |
|-------|-------------|
| `on` | Session is playing |
| `off` | Session is stopped |

**Services:**
- `switch.turn_on` - Start playback
- `switch.turn_off` - Stop playback
- `switch.toggle` - Toggle playback

---

### Theme Select
**Entity:** `select.sonorium_{session}_theme`

Select which theme to play on this session.

| Attribute | Description |
|-----------|-------------|
| `options` | List of available theme names |
| `state` | Currently selected theme name (or empty) |

**Services:**
```yaml
service: select.select_option
target:
  entity_id: select.sonorium_bedroom_theme
data:
  option: "Primeval Forest"
```

---

### Preset Select
**Entity:** `select.sonorium_{session}_preset`

Select a preset for the current theme. Options update automatically when you change themes.

| Attribute | Description |
|-----------|-------------|
| `options` | List of preset names for current theme |
| `state` | Currently selected preset name (or empty) |

**Services:**
```yaml
service: select.select_option
target:
  entity_id: select.sonorium_bedroom_preset
data:
  option: "Thunderstorm Heavy"
```

---

### Volume Number
**Entity:** `number.sonorium_{session}_volume`

Adjust session volume.

| Attribute | Value |
|-----------|-------|
| `min` | 0 |
| `max` | 100 |
| `step` | 1 |
| `unit_of_measurement` | % |

**Services:**
```yaml
service: number.set_value
target:
  entity_id: number.sonorium_bedroom_volume
data:
  value: 50
```

---

### Status Sensor
**Entity:** `sensor.sonorium_{session}_status`

Shows the current playback status.

| State | Description |
|-------|-------------|
| `playing` | Session is actively playing |
| `stopped` | Session is stopped |
| `loading` | Theme is loading |

---

### Speakers Sensor
**Entity:** `sensor.sonorium_{session}_speakers`

Shows which speakers are assigned to this session.

| State | Description |
|-------|-------------|
| `Speaker 1, Speaker 2` | Comma-separated list of speaker names |
| `No speakers` | No speakers assigned |

---

## Global Entities

These entities provide system-wide control.

### Session Select
**Entity:** `select.sonorium_session`

Switch between sessions. Useful for controlling which session receives global commands.

| Attribute | Description |
|-----------|-------------|
| `options` | List of all session names |
| `state` | Currently selected session |

---

### Global Play Switch
**Entity:** `switch.sonorium_global_play`

Start/stop playback on the currently selected session.

---

### Global Theme Select
**Entity:** `select.sonorium_global_theme`

Select theme for the currently selected session.

---

### Global Preset Select
**Entity:** `select.sonorium_preset`

Select preset for the currently selected session.

---

### Global Volume
**Entity:** `number.sonorium_volume`

Adjust volume for the currently selected session.

---

### Active Sessions Sensor
**Entity:** `sensor.sonorium_global_active_sessions`

Shows the number of sessions currently playing.

| State | Description |
|-------|-------------|
| `0` | No sessions playing |
| `3` | Three sessions playing |

---

### Stop All Switch
**Entity:** `switch.sonorium_stop_all`

Stops all playing sessions when turned on. Automatically turns off after stopping.

---

## Device Information

All entities are grouped under a single device in Home Assistant:

- **Name:** Sonorium
- **Manufacturer:** Sonorium
- **Model:** Ambient Mixer

This allows you to see all Sonorium entities together in the device view.

---

## Troubleshooting

### Entities Show "Unavailable"
1. Check that the Sonorium addon is running
2. Verify MQTT is connected (check addon logs)
3. Try restarting the addon

### Theme/Preset Shows UUID Instead of Name
Update to addon version 1.2.40 or later, which displays human-readable names.

### Entities Not Appearing
1. Ensure MQTT integration is configured in HA
2. Check that you've created at least one session in Sonorium
3. Look for errors in the addon logs

### Old/Stale Entities
Sonorium v1.2.40+ automatically cleans up stale entities. If you have old entities from previous versions, you may need to manually remove them from the HA entity registry.
