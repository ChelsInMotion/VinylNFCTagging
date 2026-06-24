#!/usr/bin/env python3
"""Album-art Hue sync for the Denon / Music Assistant player.

Polls media_player.denon_avr_x4800h_3. While it's playing, it pulls the album
art, extracts a colour palette, and slowly animates that palette across the
three TV lights. When playback stops it restores the lights to exactly how
they were before the sync started (captured as an HA scene snapshot).

The HA token is read from the HA_TOKEN environment variable and is NEVER
hardcoded here, so this file is safe to commit.

Run:  HA_TOKEN='...' python -u hue-sync/album_hue_sync.py
Stop: Ctrl-C  (restores the lights on the way out)
"""
import os, sys, json, time, colorsys, urllib.request, urllib.error
from io import BytesIO
from PIL import Image

# Windows consoles default to cp1252 and choke on non-ASCII; force UTF-8.
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# ---- config (env-overridable) ----------------------------------------------
HA       = os.environ.get('HA_BASE', 'http://192.168.1.220:8123')
TOK      = os.environ.get('HA_TOKEN')
PLAYER   = os.environ.get('HUE_PLAYER', 'media_player.denon_avr_x4800h_3')
LIGHTS   = os.environ.get('HUE_LIGHTS',
            'light.tv_wall_left,light.tv_wall_right,light.77_inch_tv').split(',')
SCENE_ID = 'album_hue_prev'

POLL_SEC     = 4      # how often to check the player while idle
STEP_SEC     = int(os.environ.get('HUE_STEP_SEC', 6))    # palette rotation interval
TRANSITION   = int(os.environ.get('HUE_TRANSITION', 4))  # light fade time, seconds
BRIGHTNESS   = int(os.environ.get('HUE_BRIGHTNESS', 191))# 0-255 (191 ≈ 75%)
SAT_BOOST    = float(os.environ.get('HUE_SAT_BOOST', 1.25))  # colour punch
MONO_SAT_MIN = 0.18   # if the cover's most saturated colour is below this,
                      # treat it as monochrome and use warm white instead
WARM_WHITE_K = 2700

if not TOK:
    sys.exit("Set the HA_TOKEN environment variable first.")

# ---- tiny HA REST helpers ----------------------------------------------------
def api_get(path):
    r = urllib.request.Request(HA + path, headers={'Authorization': 'Bearer ' + TOK})
    return json.load(urllib.request.urlopen(r, timeout=15))

def api_post(path, payload):
    data = json.dumps(payload).encode()
    r = urllib.request.Request(HA + path, data=data, method='POST',
        headers={'Authorization': 'Bearer ' + TOK, 'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(r, timeout=15).read()
        return True
    except urllib.error.URLError as e:
        print("  ! POST", path, "failed:", e)
        return False

# ---- palette extraction ------------------------------------------------------
def extract_palette(url, n=5):
    """Return (list of RGB tuples, is_monochrome) from an album-art URL."""
    raw = urllib.request.urlopen(url, timeout=15).read()
    img = Image.open(BytesIO(raw)).convert('RGB').resize((120, 120))
    q = img.quantize(colors=12, method=Image.MEDIANCUT)
    pal, counts = q.getpalette(), q.getcolors()
    total = sum(c for c, _ in counts) or 1
    cols = []
    for cnt, idx in counts:
        r, g, b = pal[idx*3:idx*3+3]
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
        cols.append((cnt, h, s, v))
    # rank by colourfulness, weighted by how much of the cover it covers
    cols.sort(key=lambda c: (c[0]/total) * (0.3 + c[2]) * (0.25 + c[3]), reverse=True)
    mono = max((c[2] for c in cols[:6]), default=0) < MONO_SAT_MIN

    picks = []
    for cnt, h, s, v in cols:
        s2 = min(1.0, s * SAT_BOOST)
        v2 = max(0.35, v)                       # floor so lights aren't near-black
        rr, gg, bb = colorsys.hsv_to_rgb(h, s2, v2)
        c = (int(rr*255), int(gg*255), int(bb*255))
        # skip near-duplicates so the three lights stay visually distinct
        if any((c[0]-p[0])**2 + (c[1]-p[1])**2 + (c[2]-p[2])**2 < 1600 for p in picks):
            continue
        picks.append(c)
        if len(picks) >= n:
            break
    if not picks:
        picks = [(255, 180, 120)]               # safety fallback
    return picks, mono

# ---- light control -----------------------------------------------------------
def set_rgb(entity, rgb):
    api_post('/api/services/light/turn_on', {
        'entity_id': entity, 'rgb_color': list(rgb),
        'brightness': BRIGHTNESS, 'transition': TRANSITION})

def set_warm(entity):
    api_post('/api/services/light/turn_on', {
        'entity_id': entity, 'color_temp_kelvin': WARM_WHITE_K,
        'brightness': BRIGHTNESS, 'transition': TRANSITION})

def snapshot():
    api_post('/api/services/scene/create', {'scene_id': SCENE_ID, 'snapshot_entities': LIGHTS})

def restore():
    api_post('/api/services/scene/turn_on', {'entity_id': 'scene.' + SCENE_ID, 'transition': TRANSITION})

# ---- main loop ---------------------------------------------------------------
def main():
    syncing = False
    cur_art = None
    palette, mono, step = [], False, 0
    print(f"album_hue_sync: watching {PLAYER}; lights = {LIGHTS}")
    while True:
        try:
            st = api_get('/api/states/' + PLAYER)
            attrs = st.get('attributes', {})
            art = attrs.get('entity_picture')
            playing = (st['state'] == 'playing' and bool(art))

            if playing:
                if not syncing:
                    print("-> playback started; snapshotting TV lights")
                    snapshot()
                    syncing, cur_art = True, None
                if art != cur_art:
                    cur_art = art
                    try:
                        palette, mono = extract_palette(art)
                        tag = 'monochrome → warm white' if mono else \
                              ' '.join('#%02x%02x%02x' % c for c in palette)
                        print(f"  cover: {attrs.get('media_artist')} - {attrs.get('media_title')}")
                        print(f"  palette: {tag}")
                    except Exception as e:
                        print("  ! palette error:", e); palette = []
                if mono or not palette:
                    for e in LIGHTS:
                        set_warm(e)
                else:
                    for i, e in enumerate(LIGHTS):
                        set_rgb(e, palette[(i + step) % len(palette)])
                    step += 1
                time.sleep(STEP_SEC)
            else:
                if syncing:
                    print("-> playback stopped; restoring TV lights")
                    restore()
                    syncing = False
                time.sleep(POLL_SEC)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("loop error:", e); time.sleep(POLL_SEC)

    if syncing:
        print("exiting; restoring TV lights")
        restore()

if __name__ == '__main__':
    main()
