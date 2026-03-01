#!/usr/bin/env python3
"""
Govee H617E – BLE Controller
=============================
Protokoll verifiziert via btsnoop_hci.log.

Paketformat (20 Bytes, XOR-Checksum):
  Power:      33 01 [01/00] 00*16 CS
  Brightness: 33 04 [00-FE] 00*16 CS
  Color:      33 05 15 01 RR GG BB 00*5 FF 7F 00*5 CS
  Scene:      33 05 04 [ID] 00*15 CS

Setup:
    pip install bleak

Nutzung:
    python3 govee_h617e.py --mac AA:BB:CC:DD:EE:FF
    python3 govee_h617e.py --scan
    python3 govee_h617e.py --offline
"""

import asyncio, json, os, argparse
from datetime import datetime
from bleak import BleakClient, BleakScanner

# ── Dateipfade ────────────────────────────────────────────
SCENES_FILE    = "scenes.json"
CAPTURES_FILE  = "captures.json"
SEQUENCES_FILE = "sequences.json"

GOVEE_CHAR_UUIDS = [
    "00010203-0405-0607-0809-0a0b0c0d2b11",
    "00010203-0405-0607-0809-0a0b0c0d1910",
]

# ── Paket-Bau ─────────────────────────────────────────────

def build(cmd: int, payload: list) -> bytes:
    data = [0x33, cmd] + payload
    data += [0x00] * (19 - len(data))
    cs = 0
    for b in data: cs ^= b
    data.append(cs)
    assert len(data) == 20
    return bytes(data)

def pkt_power(on: bool)       -> bytes: return build(0x01, [0x01 if on else 0x00])
def pkt_brightness(pct: int)  -> bytes: return build(0x04, [round(max(0,min(100,pct))/100*0xFE)])
def pkt_color(r,g,b)          -> bytes: return build(0x05, [0x15,0x01,r,g,b,0,0,0,0,0,0xFF,0x7F])
def pkt_scene(sid: int)       -> bytes: return build(0x05, [0x04, sid & 0xFF])

PRESETS = {
    "red":    (0xFF,0x00,0x00), "green":  (0x00,0xFF,0x00),
    "blue":   (0x00,0x00,0xFF), "white":  (0xFF,0xFF,0xFF),
    "orange": (0xFF,0x80,0x00), "purple": (0x80,0x00,0xFF),
    "yellow": (0xFF,0xFF,0x00), "cyan":   (0x00,0xFF,0xFF),
    "pink":   (0xFF,0x20,0x60),
}

# ── JSON Store ────────────────────────────────────────────

def load_json(path):
    if os.path.exists(path):
        with open(path) as f: return json.load(f)
    return {}

def save_json(path, data):
    with open(path, "w") as f: json.dump(data, f, indent=2)
    print(f"  💾 {path}")

def store_packet(name, hex_str, note=""):
    c = load_json(CAPTURES_FILE)
    c[name] = {"hex": hex_str.lower().replace(" ",""), "note": note,
               "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    save_json(CAPTURES_FILE, c)
    print(f"  ✅ '{name}' gespeichert.")

def save_sequence(name, steps, note=""):
    s = load_json(SEQUENCES_FILE)
    s[name] = {"steps": steps, "note": note,
               "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    save_json(SEQUENCES_FILE, s)
    print(f"  ✅ Sequenz '{name}' mit {len(steps)} Schritten gespeichert.")

# ── Szenen-Verwaltung ─────────────────────────────────────

def load_scenes() -> list:
    data = load_json(SCENES_FILE)
    return data.get("scenes", [])

def save_scenes(scenes: list):
    save_json(SCENES_FILE, {"scenes": scenes})

def find_scene(query: str) -> list:
    """Suche nach ID (dezimal/hex) oder Name."""
    scenes = load_scenes()
    results = []
    q = query.lower().strip()
    for s in scenes:
        # Match by ID
        try:
            if int(q, 0) == s["id"]:
                results.append(s); continue
        except ValueError:
            pass
        # Match by name
        if q in s.get("name","").lower():
            results.append(s)
    return results

def list_scenes(filter_str=""):
    scenes = load_scenes()
    if not scenes:
        print("  (keine Szenen – scenes.json fehlt)")
        return
    print(f"\n  {'Nr':<4} {'ID':<6} {'Hex':<6} {'Name'}")
    print("  " + "─"*50)
    for i, s in enumerate(scenes, 1):
        name = s.get("name","")
        if filter_str and filter_str.lower() not in name.lower():
            continue
        marker = "  ← (kein Name)" if not name else ""
        print(f"  {i:<4} {s['id']:<6} {s['hex_id']:<6} {name}{marker}")

def name_scene(query: str, new_name: str):
    scenes = load_scenes()
    count = 0
    for s in scenes:
        try:
            if int(query, 0) == s["id"]:
                s["name"] = new_name
                count += 1
        except ValueError:
            pass
    if count:
        save_scenes(scenes)
        print(f"  ✅ Szene {query} → '{new_name}'")
    else:
        print(f"  ❌ Szene '{query}' nicht gefunden.")

# ── BLE Controller ────────────────────────────────────────

class GoveeController:
    def __init__(self, mac):
        self.mac = mac
        self.client = None
        self.char_uuid = None
        self._rec_buffer = None

    async def connect(self):
        print(f"\n🔗 Verbinde mit {self.mac} ...")
        self.client = BleakClient(self.mac, timeout=15.0)
        await self.client.connect()
        if not self.client.is_connected:
            raise ConnectionError("Verbindung fehlgeschlagen")
        print("✅ Verbunden!")
        for service in self.client.services:
            for char in service.characteristics:
                if "write" in char.properties or "write-without-response" in char.properties:
                    for uuid in GOVEE_CHAR_UUIDS:
                        if char.uuid.lower() == uuid.lower():
                            self.char_uuid = char.uuid
                            print(f"  📡 {self.char_uuid}")
                            return
        # Fallback
        for service in self.client.services:
            for char in service.characteristics:
                if "write" in char.properties or "write-without-response" in char.properties:
                    self.char_uuid = char.uuid
                    print(f"  ⚠️  Fallback: {self.char_uuid}")
                    return

    async def disconnect(self):
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            print("🔌 Getrennt.")

    async def send(self, pkt: bytes, delay=0.0, label=""):
        await self.client.write_gatt_char(self.char_uuid, pkt, response=False)
        rec = " [●REC]" if self._rec_buffer is not None else ""
        print(f"  📤 {pkt.hex()}  {('← '+label) if label else ''}{rec}")
        if self._rec_buffer is not None:
            self._rec_buffer.append({"hex": pkt.hex(), "delay": delay, "label": label})
        if delay > 0:
            await asyncio.sleep(delay)

    async def play_sequence(self, name):
        seqs = load_json(SEQUENCES_FILE)
        if name not in seqs:
            print(f"  ❌ '{name}' nicht gefunden.")
            return
        steps = seqs[name]["steps"]
        print(f"\n  ▶️  '{name}' – {len(steps)} Schritte ...")
        for i, step in enumerate(steps):
            print(f"  [{i+1}/{len(steps)}]", end=" ")
            await self.send(bytes.fromhex(step["hex"]), step.get("delay",0.15), step.get("label",""))
        print("  ✅ Fertig.")

    async def send_named(self, name):
        c = load_json(CAPTURES_FILE)
        if name not in c:
            print(f"  ❌ '{name}' nicht gefunden.")
            return
        await self.send(bytes.fromhex(c[name]["hex"]), label=name)

    async def scan_scenes(self, start=0, end=255, delay=2.0):
        """Alle Scene-IDs im Bereich abspielen zum Durchschauen."""
        scenes = load_scenes()
        scene_ids = {s["id"] for s in scenes}
        print(f"\n  🔍 Scanne Szenen {start}–{end} (je {delay}s) ...")
        print(f"  Ctrl+C zum Stoppen\n")
        for sid in range(start, end+1):
            if sid not in scene_ids:
                continue
            name = next((s.get("name","") for s in scenes if s["id"]==sid), "")
            print(f"  ID {sid:3d} (0x{sid:02x}) {name}", end="\r")
            await self.send(pkt_scene(sid), delay=delay, label=f"Scene {sid}")

    def rec_start(self):
        self._rec_buffer = []
        print("  🔴 Aufnahme gestartet.")

    def rec_stop(self):
        if self._rec_buffer is None:
            print("  ⚠️  Keine Aufnahme aktiv.")
            return None
        buf = self._rec_buffer
        self._rec_buffer = None
        return buf

# ── Controller Shell ──────────────────────────────────────

HELP = """
┌─────────────────────────────────────────────────────────────────┐
│  GOVEE H617E CONTROLLER                                         │
├─────────────────────────────────────────────────────────────────┤
│  POWER & LICHT                                                  │
│    on / off                                                     │
│    brightness N          Helligkeit % (0-100)                   │
│                                                                 │
│  FARBE                                                          │
│    color R G B           Farbe (0-255 je Kanal)                 │
│    red/green/blue/white/orange/purple/yellow/cyan/pink          │
│                                                                 │
│  SZENEN                                                         │
│    scene ID              Szene per ID (dezimal oder 0xNN)       │
│    scene NAME            Szene per Name (Teilstring)            │
│    scenes                Alle Szenen auflisten                  │
│    scenes FILTER         Szenen filtern nach Name               │
│    scanscenes            Alle Szenen durchlaufen (2s je)        │
│    scanscenes N          Mit N Sekunden Pause                   │
│    name ID NEUERNAME     Szene benennen                         │
│                                                                 │
│  RAW / PAKETE                                                   │
│    raw HEX               Rohes Paket senden                     │
│    rawsave NAME HEX      Paket benennen & in captures.json      │
│    rawplay NAME          Gespeichertes Paket senden             │
│    list packets          captures.json anzeigen                 │
│                                                                 │
│  SEQUENZEN                                                      │
│    rec start / rec stop  Sequenz aufnehmen                      │
│    play NAME             Sequenz abspielen                      │
│    list seq              sequences.json anzeigen                │
│                                                                 │
│  quit                                                           │
└─────────────────────────────────────────────────────────────────┘
"""

async def controller_shell(ctrl: GoveeController):
    print(HELP)
    loop = asyncio.get_event_loop()

    while True:
        rec = " [●REC]" if ctrl._rec_buffer is not None else ""
        try:
            line = await loop.run_in_executor(None, input, f"govee{rec}> ")
        except (EOFError, KeyboardInterrupt):
            print(); break

        parts = line.strip().split()
        if not parts: continue
        cmd = parts[0].lower()

        try:
            # Power
            if cmd == "on":
                await ctrl.send(pkt_power(True), label="Power ON")
            elif cmd == "off":
                await ctrl.send(pkt_power(False), label="Power OFF")

            # Helligkeit
            elif cmd == "brightness":
                await ctrl.send(pkt_brightness(int(parts[1])), label=f"Brightness {parts[1]}%")

            # Farb-Presets
            elif cmd in PRESETS:
                r,g,b = PRESETS[cmd]
                await ctrl.send(pkt_color(r,g,b), label=cmd)

            # Farbe RGB
            elif cmd == "color":
                r,g,b = int(parts[1]),int(parts[2]),int(parts[3])
                await ctrl.send(pkt_color(r,g,b), label=f"RGB({r},{g},{b})")

            # Szenen
            elif cmd == "scene":
                if not parts[1:]:
                    print("  Verwendung: scene ID | scene NAME")
                else:
                    query = " ".join(parts[1:])
                    results = find_scene(query)
                    if not results:
                        print(f"  ❌ Keine Szene gefunden für '{query}'")
                    elif len(results) == 1:
                        s = results[0]
                        await ctrl.send(pkt_scene(s["id"]), label=f"Scene {s['id']} {s.get('name','')}")
                    else:
                        print(f"  Mehrere Treffer:")
                        for s in results:
                            print(f"    {s['id']:3d} (0x{s['id']:02x}) {s.get('name','')}")

            elif cmd == "scenes":
                filter_str = " ".join(parts[1:]) if parts[1:] else ""
                list_scenes(filter_str)

            elif cmd == "scanscenes":
                delay = float(parts[1]) if parts[1:] else 2.0
                try:
                    await ctrl.scan_scenes(delay=delay)
                except KeyboardInterrupt:
                    print("\n  ⏹  Scan gestoppt.")

            elif cmd == "name":
                # name 0xd4 Sonnenuntergang
                sid_str = parts[1]
                new_name = " ".join(parts[2:])
                if not new_name:
                    print("  Verwendung: name ID NEUERNAME")
                else:
                    name_scene(sid_str, new_name)

            # Raw
            elif cmd == "raw":
                await ctrl.send(bytes.fromhex("".join(parts[1:])), label="RAW")

            elif cmd == "rawsave":
                name = parts[1]
                hex_str = "".join(parts[2:])
                note = (await loop.run_in_executor(None, input, "  Notiz: ")).strip()
                store_packet(name, hex_str, note)

            elif cmd == "rawplay":
                await ctrl.send_named(parts[1])

            # Sequenzen
            elif cmd == "rec":
                sub = parts[1].lower() if len(parts) > 1 else ""
                if sub == "start":
                    ctrl.rec_start()
                elif sub == "stop":
                    buf = ctrl.rec_stop()
                    if buf:
                        name = (await loop.run_in_executor(None, input, "  Sequenzname: ")).strip()
                        if name:
                            note = (await loop.run_in_executor(None, input, "  Notiz: ")).strip()
                            save_sequence(name, buf, note)
                else:
                    print("  rec start | rec stop")

            elif cmd == "play":
                await ctrl.play_sequence(parts[1])

            elif cmd == "list":
                sub = parts[1].lower() if len(parts) > 1 else ""
                if sub == "packets":
                    c = load_json(CAPTURES_FILE)
                    if not c:
                        print("  (leer)")
                    else:
                        print(f"\n  {'Name':<20} {'Hex':<42} Note")
                        print("  " + "─"*75)
                        for n,v in c.items():
                            print(f"  {n:<20} {v['hex']:<42} {v.get('note','')}")
                elif sub == "seq":
                    s = load_json(SEQUENCES_FILE)
                    if not s:
                        print("  (leer)")
                    else:
                        for n,v in s.items():
                            print(f"  [{n}]  {len(v['steps'])} Schritte  {v.get('note','')}")
                else:
                    print("  list packets | list seq")

            elif cmd in ("help","?"): print(HELP)
            elif cmd in ("quit","exit"): break
            else: print(f"  ❓ '{cmd}'  –  'help' für alle Befehle")

        except (IndexError, ValueError) as e:
            print(f"  ⚠️  Eingabefehler: {e}")
        except Exception as e:
            print(f"  ❌ {e}")

# ── Offline Shell ─────────────────────────────────────────

def offline_shell():
    print("\n  📂 Offline-Modus")
    print("  Befehle: scenes [FILTER] | name ID NAME | list packets | list seq | quit\n")
    while True:
        try:
            line = input("offline> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        parts = line.split(maxsplit=1)
        if not parts: continue
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "scenes":
            list_scenes(arg)
        elif cmd == "name":
            p2 = arg.split(maxsplit=1)
            if len(p2) < 2:
                print("  Verwendung: name ID NEUERNAME")
            else:
                name_scene(p2[0], p2[1])
        elif cmd == "list":
            if "packet" in arg:
                c = load_json(CAPTURES_FILE)
                for n,v in c.items():
                    print(f"  {n:<20} {v['hex']}  {v.get('note','')}")
            elif "seq" in arg:
                s = load_json(SEQUENCES_FILE)
                for n,v in s.items():
                    print(f"  [{n}]  {len(v['steps'])} Schritte")
        elif cmd in ("quit","exit"):
            break
        else:
            print("  scenes | name ID NAME | list packets | list seq | quit")

# ── Main ──────────────────────────────────────────────────

async def do_scan():
    print("🔍 Scanne BLE (10s) ...")
    devices = await BleakScanner.discover(timeout=10.0)
    for d in sorted(devices, key=lambda x: x.rssi, reverse=True):
        name = d.name or "?"
        tag = "  ← GOVEE!" if "govee" in name.lower() or "ihoment" in name.lower() else ""
        print(f"  {d.address}  RSSI:{d.rssi:4d}  {name}{tag}")

async def async_main(mac):
    ctrl = GoveeController(mac)
    try:
        await ctrl.connect()
        await controller_shell(ctrl)
    finally:
        await ctrl.disconnect()

def main():
    parser = argparse.ArgumentParser(description="Govee H617E BLE Controller")
    parser.add_argument("--mac",     type=str)
    parser.add_argument("--scan",    action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    if args.scan:       asyncio.run(do_scan())
    elif args.offline:  offline_shell()
    elif args.mac:      asyncio.run(async_main(args.mac))
    else:
        parser.print_help()
        print("\n  Beispiele:")
        print("    python3 govee_h617e.py --scan")
        print("    python3 govee_h617e.py --mac AA:BB:CC:DD:EE:FF")
        print("    python3 govee_h617e.py --offline")

if __name__ == "__main__":
    main()
