# Home Assistant automations

Drop-in automations for the house. Everything lives in
[`packages/household_alerts.yaml`](packages/household_alerts.yaml) as a single
Home Assistant **package** (helpers + automations in one file).

## What's in here

| # | Automation | Trigger | Result |
|---|------------|---------|--------|
| 1 | Baby gate alert | Guest-bathroom baby gate open **> 30 s** | Phone push + Google Home says *"Bagel is about to eat cat poop"* |
| 2a | AC off reminder | Patio door open **5 min** | Phone push + TTS: *turn off the AC* |
| 2b | AC on reminder | Patio door **closes** after a 5-min-open event | Phone push + TTS: *turn the AC back on* |
| 3a | R2D2 red light *(reconstructed wrapper)* | Self-clean complete | Snapshots lights, sets red status light |
| 3b | R2D2 light reset **(new)** | Vacuum contact sensor **opened then closed** | Restores lights to normal |

## Install

1. Enable packages in `configuration.yaml` (once):

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

2. Copy `packages/household_alerts.yaml` to your HA `<config>/packages/` folder.
3. Fill in the placeholders below.
4. **Developer Tools → YAML → Check Configuration**, then **Reload Automations**
   (and **Reload Input Booleans** / restart so the helpers register).

## Placeholders to replace

Every line tagged `# REPLACE` in the YAML:

| Placeholder | What it is | How to find it |
|-------------|------------|----------------|
| `binary_sensor.guest_bathroom_baby_gate` | Baby gate contact sensor | Settings → Devices & Services → Entities |
| `binary_sensor.patio_door` | Patio door contact sensor | same |
| `binary_sensor.r2d2_dustbin_contact` | Vacuum contact sensor | same — **rename suggested, see below** |
| `notify.mobile_app_chelsea_phone` | Your phone's notify service | Developer Tools → Actions → search `notify.mobile_app_` |
| `tts.google_translate_en_com` | Your TTS engine entity | Settings → Voice assistants, or Developer Tools → States → filter `tts.` |
| `media_player.google_home` | The Google Home(s) to speak on | Developer Tools → States → filter `media_player.` (you can list several) |
| `vacuum.r2d2` / `attribute`/`to` (3a) | Your existing self-clean trigger | Replace with whatever your real routine uses |
| `light.r2d2_status_light` | The light that goes red | Developer Tools → States → filter `light.` |

> **Multiple speakers:** `media_player_entity_id:` accepts a list, e.g.
> `[media_player.kitchen_home, media_player.living_room_home]`.

## About the vacuum routine (#3)

You said the existing routine is "R2D2 done red light status" and to edit it
directly — that automation isn't in this repo, so **3a is a reconstructed
wrapper** that mimics it (snapshot lights → go red → flag
`input_boolean.r2d2_self_clean_done`). The piece you actually asked for is
**3b**, the reset.

Two ways to wire it up:

- **Keep your existing automation:** delete 3a, and in your real routine add one
  line at the end so the reset knows red is active:
  `service: input_boolean.turn_on` → `entity_id: input_boolean.r2d2_self_clean_done`.
  Also snapshot the light first (`scene.create` with `scene_id: r2d2_pre_clean_lights`)
  if you want an exact restore.
- **Use 3a as-is:** just swap its trigger + light target for your real ones.

Paste your current "R2D2 done red light status" YAML and I'll merge it precisely
instead of leaving the wrapper.

### Renaming the vacuum contact sensor

A bare contact entity named after the vacuum (e.g. `binary_sensor.r2d2` or
`binary_sensor.vacuum_sensor`) is ambiguous — "contact" could mean the dustbin
lid, a door it lives behind, etc., and it's easy to grab the wrong one later. I'd
rename it to something that says *what it senses*:

- `binary_sensor.r2d2_dustbin_contact` — if it's the dust bin lid
- `binary_sensor.r2d2_lid_contact` — if it's the top lid

To rename: **Settings → Devices & Services → Entities → (the sensor) → ⚙ →
Entity ID**. Update the `# REPLACE` line in the YAML to match.
