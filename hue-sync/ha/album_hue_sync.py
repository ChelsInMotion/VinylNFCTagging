"""Album-art Hue sync — Home Assistant pyscript version (always-on, no PC needed).

Drop this at /config/pyscript/album_hue_sync.py (pyscript installed via HACS,
with "Allow all imports" enabled). It reuses the Pillow that HA core already
ships (camera/image integrations), so nothing extra needs installing.

While media_player.denon_avr_x4800h_3 is playing, it extracts a colour palette
from the album art and slowly animates it across the three TV lights, restoring
them to their pre-sync state (an HA scene snapshot) when playback stops.

Reload after editing:  Developer Tools → Actions → pyscript.reload
"""
import urllib.request, colorsys
from io import BytesIO
from PIL import Image

PLAYER   = "media_player.denon_avr_x4800h_3"
LIGHTS   = ["light.tv_wall_left", "light.tv_wall_right", "light.77_inch_tv"]
SCENE_ID = "album_hue_prev"

STEP_SEC     = 6      # palette rotation interval, seconds
TRANSITION   = 4      # light fade time, seconds
BRIGHTNESS   = 191    # 0-255  (191 ≈ 75%)
SAT_BOOST    = 1.25
MONO_SAT_MIN = 0.18   # below this max-saturation -> warm white fallback
WARM_WHITE_K = 2700


@pyscript_compile
def _extract_palette(url, n=5):
    """Blocking: download art, return (list of RGB tuples, is_monochrome).
    Runs in an executor thread so it never blocks HA's event loop.

    @pyscript_compile makes this a plain Python function (not a pyscript
    function), which is required to hand it to task.executor."""
    raw = urllib.request.urlopen(url, timeout=15).read()
    img = Image.open(BytesIO(raw)).convert("RGB").resize((120, 120))
    q = img.quantize(colors=12, method=Image.MEDIANCUT)
    pal, counts = q.getpalette(), q.getcolors()
    total = sum(c for c, _ in counts) or 1
    cols = []
    for cnt, idx in counts:
        r, g, b = pal[idx * 3:idx * 3 + 3]
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        cols.append((cnt, h, s, v))
    cols.sort(key=lambda c: (c[0] / total) * (0.3 + c[2]) * (0.25 + c[3]), reverse=True)
    mono = max((c[2] for c in cols[:6]), default=0) < MONO_SAT_MIN
    picks = []
    for cnt, h, s, v in cols:
        s2 = min(1.0, s * SAT_BOOST)
        v2 = max(0.35, v)
        rr, gg, bb = colorsys.hsv_to_rgb(h, s2, v2)
        c = (int(rr * 255), int(gg * 255), int(bb * 255))
        if any((c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2 + (c[2] - p[2]) ** 2 < 1600 for p in picks):
            continue
        picks.append(c)
        if len(picks) >= n:
            break
    if not picks:
        picks = [(255, 180, 120)]
    return picks, mono


@time_trigger("startup")
def album_hue_loop():
    """Runs at HA start and on every pyscript.reload. One persistent loop."""
    task.unique("album_hue_sync")          # only ever one instance
    syncing = False
    cur_art = None
    palette, mono, step = [], False, 0
    log.info("album_hue_sync: loop started")

    while True:
        try:
            cur_state = state.get(PLAYER)
            attrs = state.getattr(PLAYER) or {}
            art = attrs.get("entity_picture")
            playing = (cur_state == "playing" and bool(art))

            if playing:
                if not syncing:
                    scene.create(scene_id=SCENE_ID, snapshot_entities=LIGHTS)
                    syncing, cur_art = True, None
                    log.info("album_hue_sync: snapshotted TV lights, syncing")
                if art != cur_art:
                    cur_art = art
                    palette, mono = task.executor(_extract_palette, art)
                    log.info(f"album_hue_sync: {attrs.get('media_artist')} - "
                             f"{attrs.get('media_title')} | "
                             f"{'mono->warm' if mono else [('#%02x%02x%02x' % c) for c in palette]}")
                if mono or not palette:
                    for e in LIGHTS:
                        light.turn_on(entity_id=e, color_temp_kelvin=WARM_WHITE_K,
                                      brightness=BRIGHTNESS, transition=TRANSITION)
                else:
                    for i, e in enumerate(LIGHTS):
                        rgb = palette[(i + step) % len(palette)]
                        light.turn_on(entity_id=e, rgb_color=list(rgb),
                                      brightness=BRIGHTNESS, transition=TRANSITION)
                    step += 1
                task.sleep(STEP_SEC)
            else:
                if syncing:
                    scene.turn_on(entity_id="scene." + SCENE_ID, transition=TRANSITION)
                    syncing = False
                    log.info("album_hue_sync: playback stopped, restored TV lights")
                task.sleep(4)
        except Exception as e:
            log.error(f"album_hue_sync loop error: {e}")
            task.sleep(4)
