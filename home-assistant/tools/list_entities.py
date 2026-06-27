#!/usr/bin/env python3
"""Dump the HA entities/services relevant to the household_alerts package.

Run it on a machine that can reach your HA and has the token (e.g. the same
box that runs album_hue_sync.py):

    HA_TOKEN='...' python3 home-assistant/tools/list_entities.py

It prints candidate entity ids for the baby gate, patio door, vacuum,
status lights, Google Home speakers, your TTS engine, and notify services.
Paste the output back and the # REPLACE placeholders get filled in.
Read-only: it only does GET requests, changes nothing.
"""
import os, sys, json, urllib.request

HA  = os.environ.get('HA_BASE', 'http://192.168.1.220:8123')
TOK = os.environ.get('HA_TOKEN')
if not TOK:
    sys.exit("Set HA_TOKEN first (same token album_hue_sync.py uses).")

def get(path):
    r = urllib.request.Request(HA + path,
        headers={'Authorization': 'Bearer ' + TOK})
    return json.load(urllib.request.urlopen(r, timeout=15))

states = get('/api/states')

def show(title, predicate):
    print(f"\n== {title} ==")
    hits = [s for s in states if predicate(s)]
    for s in sorted(hits, key=lambda s: s['entity_id']):
        name = s['attributes'].get('friendly_name', '')
        dc   = s['attributes'].get('device_class', '')
        print(f"  {s['entity_id']:50}  state={s['state']:>10}  {dc:10} {name}")
    if not hits:
        print("  (none found)")

def dom(s, d):   return s['entity_id'].startswith(d + '.')

# Contact/opening sensors -> baby gate, patio door, vacuum contact sensor
show("binary_sensor (baby gate / patio door / vacuum contact)",
     lambda s: dom(s, 'binary_sensor'))
show("vacuum (R2D2)",        lambda s: dom(s, 'vacuum'))
show("light (status light + others)", lambda s: dom(s, 'light'))
show("media_player (Google Home speakers)", lambda s: dom(s, 'media_player'))
show("tts (your TTS engine entity)", lambda s: dom(s, 'tts'))

# notify services aren't entities; they live under the notify domain.
print("\n== notify services (your phone) ==")
try:
    svc = get('/api/services')
    notify = next((d for d in svc if d['domain'] == 'notify'), None)
    for name in sorted((notify or {}).get('services', {})):
        print(f"  notify.{name}")
except Exception as e:
    print("  (couldn't list services:", e, ")")
