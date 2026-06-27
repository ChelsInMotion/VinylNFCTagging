# Setup — direct HA access from Claude Code web sessions

This lets a cloud session reach the home HA to read live entity IDs/states so
the `# REPLACE` placeholders in `packages/household_alerts.yaml` can be filled
in automatically.

## One-time environment config (already done)

In the Claude Code web/app environment settings dialog
(cloud icon → gear, at claude.ai/code):

1. **Environment variables** (`.env` format, no quotes):
   ```
   HA_BASE=https://<your-nabu-casa-id>.ui.nabu.casa
   HA_TOKEN=<a long-lived access token>
   ```
2. **Network access → Custom → Allowed domains:**
   ```
   *.ui.nabu.casa
   ```
   with **"Also include default list of common package managers"** checked.

Notes:
- Env vars are injected at **session start**, so changes only apply to **new**
  sessions, not ones already running.
- There is no real secrets store yet — env vars are visible to anyone who can
  edit the environment. Treat `HA_TOKEN` accordingly; rotate it if it leaks.
- The HA LAN IP (`192.168.1.220`) is NOT reachable from the cloud — must use the
  public Nabu Casa URL.

## Reaching HA from a session

Outbound HTTPS goes through the agent proxy, which re-terminates TLS, so point
Python at the proxy CA bundle:

```bash
SSL_CERT_FILE=/root/.ccr/ca-bundle.crt python3 home-assistant/tools/list_entities.py
```

`list_entities.py` reads `HA_BASE` + `HA_TOKEN` from the env and is read-only.

## Kickoff prompt for a fresh session

> Connect to my Home Assistant using the `HA_BASE` and `HA_TOKEN` environment
> variables (set `SSL_CERT_FILE=/root/.ccr/ca-bundle.crt`). Run
> `home-assistant/tools/list_entities.py` to dump my real entity IDs, then fill
> in every `# REPLACE` placeholder in
> `home-assistant/packages/household_alerts.yaml` — baby gate, patio door,
> vacuum contact sensor, R2D2 status light + self-clean trigger, my
> `notify.mobile_app_*` phone service, TTS engine entity, and Google Home
> speaker(s). Show me before/after, then commit and push to this branch.

## Placeholders to resolve

| Placeholder | What it is |
|-------------|------------|
| `binary_sensor.guest_bathroom_baby_gate` | Guest-bathroom baby gate contact |
| `binary_sensor.patio_door` | Patio door contact |
| `binary_sensor.r2d2_dustbin_contact` | Vacuum contact sensor (rename suggested) |
| `notify.mobile_app_chelsea_phone` | Phone push notify service |
| `tts.google_translate_en_com` | TTS engine entity |
| `media_player.google_home` | Google Home speaker(s) to announce on |
| `vacuum.r2d2` + attribute/state (3a) | Existing self-clean-complete trigger |
| `light.r2d2_status_light` | The light that turns red |
