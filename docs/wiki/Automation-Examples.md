# Automation Examples

Home Assistant automations for Sonorium. All examples can be created via the UI or pasted into your `automations.yaml` file.

## Creating Automations via UI

1. Go to **Settings > Automations & Scenes**
2. Click **+ Create Automation**
3. Click **Create new automation**
4. Click the three-dot menu (top right) > **Edit in YAML**
5. Delete everything and paste the example (without the `- id:` line)
6. Click **Save**

---

## Morning Wake-Up Alarm

Wake up to ambient sounds at a specific time.

```yaml
alias: "Morning Wake-Up - Forest Sounds"
description: "Wake up to ambient forest sounds at 7am"
trigger:
  - platform: time
    at: "07:00:00"
condition: []
action:
  - service: select.select_option
    target:
      entity_id: select.sonorium_bedroom_theme
    data:
      option: "Primeval Forest"
  - delay:
      seconds: 1
  - service: number.set_value
    target:
      entity_id: number.sonorium_bedroom_volume
    data:
      value: 30
  - service: switch.turn_on
    target:
      entity_id: switch.sonorium_bedroom_play
mode: single
```

---

## Gradual Volume Wake-Up

Start quiet and gradually increase volume over 10 minutes for a gentle wake-up.

```yaml
alias: "Gentle Wake-Up with Volume Fade"
description: "Wake up gently with volume increasing over 10 minutes"
trigger:
  - platform: time
    at: "07:00:00"
condition: []
action:
  - service: select.select_option
    target:
      entity_id: select.sonorium_bedroom_theme
    data:
      option: "Primeval Forest"
  - delay:
      seconds: 1
  - service: number.set_value
    target:
      entity_id: number.sonorium_bedroom_volume
    data:
      value: 10
  - service: switch.turn_on
    target:
      entity_id: switch.sonorium_bedroom_play
  - delay:
      minutes: 2
  - service: number.set_value
    target:
      entity_id: number.sonorium_bedroom_volume
    data:
      value: 25
  - delay:
      minutes: 2
  - service: number.set_value
    target:
      entity_id: number.sonorium_bedroom_volume
    data:
      value: 40
  - delay:
      minutes: 2
  - service: number.set_value
    target:
      entity_id: number.sonorium_bedroom_volume
    data:
      value: 55
  - delay:
      minutes: 2
  - service: number.set_value
    target:
      entity_id: number.sonorium_bedroom_volume
    data:
      value: 70
  - delay:
      minutes: 2
  - service: number.set_value
    target:
      entity_id: number.sonorium_bedroom_volume
    data:
      value: 80
mode: single
```

---

## Weekday-Only Wake-Up

Only trigger on weekdays (Monday through Friday).

```yaml
alias: "Weekday Morning Wake-Up"
description: "Wake up to ambient sounds on weekdays only"
trigger:
  - platform: time
    at: "06:30:00"
condition:
  - condition: time
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: select.select_option
    target:
      entity_id: select.sonorium_bedroom_theme
    data:
      option: "A Rainy Day"
  - delay:
      seconds: 1
  - service: number.set_value
    target:
      entity_id: number.sonorium_bedroom_volume
    data:
      value: 40
  - service: switch.turn_on
    target:
      entity_id: switch.sonorium_bedroom_play
mode: single
```

---

## Auto-Stop After Duration

Stop playback automatically after a set time.

```yaml
alias: "Auto-Stop Morning Alarm"
description: "Stop Sonorium 30 minutes after morning playback starts"
trigger:
  - platform: state
    entity_id: switch.sonorium_bedroom_play
    to: "on"
condition:
  - condition: time
    after: "06:00:00"
    before: "08:00:00"
action:
  - delay:
      minutes: 30
  - service: switch.turn_off
    target:
      entity_id: switch.sonorium_bedroom_play
mode: single
```

---

## Bedtime Routine

Start relaxing sounds when you're ready for bed.

```yaml
alias: "Bedtime Ambiance"
description: "Start sleep sounds when bedtime scene activates"
trigger:
  - platform: state
    entity_id: scene.bedtime
    to: "scening"
action:
  - service: select.select_option
    target:
      entity_id: select.sonorium_bedroom_theme
    data:
      option: "A Rainy Day"
  - delay:
      seconds: 1
  - service: number.set_value
    target:
      entity_id: number.sonorium_bedroom_volume
    data:
      value: 25
  - service: switch.turn_on
    target:
      entity_id: switch.sonorium_bedroom_play
mode: single
```

---

## Sleep Timer

Turn off all ambient sound after falling asleep.

```yaml
alias: "Sleep Timer - 1 Hour"
description: "Stop all Sonorium playback after 1 hour"
trigger:
  - platform: state
    entity_id: input_boolean.sleep_timer
    to: "on"
action:
  - delay:
      hours: 1
  - service: switch.turn_on
    target:
      entity_id: switch.sonorium_stop_all
  - service: input_boolean.turn_off
    target:
      entity_id: input_boolean.sleep_timer
mode: single
```

**Note:** Create an `input_boolean.sleep_timer` helper first:
1. Go to **Settings > Devices & Services > Helpers**
2. Click **+ Create Helper**
3. Choose **Toggle**
4. Name it "Sleep Timer"

---

## Work Focus Hours

Play focus-enhancing ambient sound during work hours.

```yaml
alias: "Work Focus Ambiance"
description: "Start ambient sound during work hours on weekdays"
trigger:
  - platform: time
    at: "09:00:00"
condition:
  - condition: time
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: select.select_option
    target:
      entity_id: select.sonorium_office_theme
    data:
      option: "Tavern"
  - delay:
      seconds: 1
  - service: number.set_value
    target:
      entity_id: number.sonorium_office_volume
    data:
      value: 20
  - service: switch.turn_on
    target:
      entity_id: switch.sonorium_office_play
mode: single
```

---

## End of Work Day

Stop office sounds at end of work day.

```yaml
alias: "End of Work Day"
description: "Stop office ambient sound at 6pm"
trigger:
  - platform: time
    at: "18:00:00"
condition:
  - condition: time
    weekday:
      - mon
      - tue
      - wed
      - thu
      - fri
action:
  - service: switch.turn_off
    target:
      entity_id: switch.sonorium_office_play
mode: single
```

---

## Holiday Theme Automation

Play seasonal themes on specific dates.

```yaml
alias: "Christmas Morning Ambiance"
description: "Play sleigh ride sounds on Christmas morning"
trigger:
  - platform: time
    at: "08:00:00"
condition:
  - condition: template
    value_template: "{{ now().month == 12 and now().day == 25 }}"
action:
  - service: select.select_option
    target:
      entity_id: select.sonorium_living_room_theme
    data:
      option: "Sleigh Ride"
  - delay:
      seconds: 1
  - service: number.set_value
    target:
      entity_id: number.sonorium_living_room_volume
    data:
      value: 50
  - service: switch.turn_on
    target:
      entity_id: switch.sonorium_living_room_play
mode: single
```

---

## Motion-Triggered Ambiance

Start sounds when motion is detected in a room.

```yaml
alias: "Living Room Motion Ambiance"
description: "Play ambient sounds when someone enters the living room"
trigger:
  - platform: state
    entity_id: binary_sensor.living_room_motion
    to: "on"
condition:
  - condition: state
    entity_id: switch.sonorium_living_room_play
    state: "off"
action:
  - service: select.select_option
    target:
      entity_id: select.sonorium_living_room_theme
    data:
      option: "Tavern"
  - delay:
      seconds: 1
  - service: number.set_value
    target:
      entity_id: number.sonorium_living_room_volume
    data:
      value: 30
  - service: switch.turn_on
    target:
      entity_id: switch.sonorium_living_room_play
mode: single
```

---

## Multi-Room Sync

Start the same theme in multiple rooms simultaneously.

```yaml
alias: "Whole House Ambiance"
description: "Start ambient sound in all rooms"
trigger:
  - platform: state
    entity_id: input_boolean.whole_house_ambiance
    to: "on"
action:
  - service: select.select_option
    target:
      entity_id:
        - select.sonorium_bedroom_theme
        - select.sonorium_living_room_theme
        - select.sonorium_office_theme
    data:
      option: "A Rainy Day"
  - delay:
      seconds: 2
  - service: switch.turn_on
    target:
      entity_id:
        - switch.sonorium_bedroom_play
        - switch.sonorium_living_room_play
        - switch.sonorium_office_play
mode: single
```

---

## Voice Assistant Integration

If you use a voice assistant, you can create scripts to call from voice commands.

### Script: Play Rain Sounds
```yaml
alias: Play Rain Sounds
sequence:
  - service: select.select_option
    target:
      entity_id: select.sonorium_bedroom_theme
    data:
      option: "A Rainy Day"
  - delay:
      seconds: 1
  - service: switch.turn_on
    target:
      entity_id: switch.sonorium_bedroom_play
mode: single
```

Then configure your voice assistant to trigger this script with phrases like "Play rain sounds" or "Start ambient sound."

---

## Tips

### Theme Names Are Case-Sensitive

Always use the exact theme name as it appears in Sonorium:
- "Primeval Forest" (correct)
- "primeval forest" (incorrect)
- "PRIMEVAL FOREST" (incorrect)

### Add Delays After Theme Selection

Always include a 1-second delay after selecting a theme before starting playback:
```yaml
- service: select.select_option
  target:
    entity_id: select.sonorium_bedroom_theme
  data:
    option: "Primeval Forest"
- delay:
    seconds: 1
- service: switch.turn_on
  target:
    entity_id: switch.sonorium_bedroom_play
```

### Finding Your Entity IDs

1. Go to **Developer Tools > States**
2. Filter by "sonorium"
3. Note your exact entity IDs

### Testing Automations

Use the **Run** button in the automation editor to test without waiting for the trigger.
