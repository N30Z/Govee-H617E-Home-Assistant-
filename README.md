# Govee H617E – Home Assistant Integration

Direkte Bluetooth-Low-Energy (BLE) Steuerung des **Govee H617E** LED-Strips in Home Assistant – ohne Cloud, ohne Bridge, ohne Govee-App.

---

## Features

| Funktion | Unterstützt |
|---|---|
| Ein / Aus | ✅ |
| Helligkeit (0–100 %) | ✅ |
| RGB-Farbe | ✅ |
| Szenen / Effekte (228 Stück) | ✅ |
| Eigene Custom Effekte (custom_effects.json) | ✅ |
| Automatische Wiederverbindung | ✅ |
| Konfiguration über die HA-UI | ✅ |
| Kein Cloud-Zugriff nötig | ✅ |

---

## Voraussetzungen

- Home Assistant **2023.1** oder neuer
- Bluetooth-Adapter, der vom HA-Host erreichbar ist (integriert oder USB-Dongle)
- Govee **H617E** LED-Strip (anderer Modelle werden nicht unterstützt)
- Python-Bibliothek [`bleak`](https://github.com/hbldh/bleak) ≥ 0.21 (wird automatisch installiert)

---

## Installation

### Manuell (ohne HACS)

1. Den Ordner `custom_components/govee_h617e/` aus diesem Repository in dein Home-Assistant-Konfigurationsverzeichnis kopieren:

   ```
   <config>/
   └── custom_components/
       └── govee_h617e/
           ├── __init__.py
           ├── config_flow.py
           ├── const.py
           ├── custom_effects.json   ← eigene Effekte hier eintragen
           ├── light.py
           ├── manifest.json
           ├── scenes.json
           ├── strings.json
           └── translations/
               ├── de.json
               └── en.json
   ```

2. Home Assistant neu starten.

---

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen**
2. Nach **„Govee H617E"** suchen und auswählen.
3. Die **Bluetooth-MAC-Adresse** des Strips eingeben (Format: `AA:BB:CC:DD:EE:FF`).

   Die MAC-Adresse kannst du mit dem mitgelieferten Standalone-Skript ermitteln:
   ```bash
   pip install bleak
   python3 govee_h617e.py --scan
   ```
   Govee-Geräte erscheinen dort mit `← GOVEE!` markiert.

4. Optional einen benutzerdefinierten Namen vergeben und auf **Fertig** klicken.

---

## Verwendung

Nach der Einrichtung erscheint eine neue **Licht-Entität** in Home Assistant.

### Steuerung über die UI

- **Ein / Aus** – Power-Button
- **Helligkeit** – Schieberegler (0–100 %)
- **Farbe** – RGB-Farbe wählen
- **Effekte** – 228 vorgespeicherte Szenen aus dem Dropdown

### Beispiel: Automatisierung (YAML)

```yaml
# Szene "Aurora-A" aktivieren
service: light.turn_on
target:
  entity_id: light.govee_h617e
data:
  effect: "Aurora-A"

# Helligkeit auf 60 % setzen
service: light.turn_on
target:
  entity_id: light.govee_h617e
data:
  brightness_pct: 60

# RGB-Farbe Orange
service: light.turn_on
target:
  entity_id: light.govee_h617e
data:
  rgb_color: [255, 128, 0]
```

---

## Szenen

Die Integration enthält **228 vorgespeicherte Effekte**, die direkt per Raw-BLE-Paket (aus `scenes.json`) gesendet werden – inklusive der korrekten Parameterwerte, die mit `btsnoop_hci.log` verifiziert wurden.

Beispiele:

| Name | Beschreibung |
|---|---|
| Sonnenaufgang | Sanfter Farbverlauf von Rot nach Gelb |
| Sonnenuntergang | Warm-orange Töne |
| Aurora-A / Aurora-B | Nordlicht-Effekte |
| Meteor / Meteorregen | Meteoriteneffekte |
| Wald | Natürliches Grün |
| Universum-A / Universum-B | Kosmische Effekte |
| … | 222 weitere |

---

## Eigene Effekte (Custom Effects)

Neben den 228 vorgespeicherten Szenen können eigene Effekte als **rohe BLE-Pakete** definiert werden.
Custom Effekte unterstützen auch **Mehrfach-Pakete** (Sequenzen), die der Reihe nach gesendet werden.

### Datei: `custom_effects.json`

Die Datei liegt neben `scenes.json` im Integrationsordner:

```
custom_components/govee_h617e/custom_effects.json
```

### Format

```json
{
  "custom_effects": [
    {
      "name": "Mein Effekt",
      "description": "Optionale Beschreibung",
      "packets": [
        "33051501ffffff000000000024490000000000b0",
        "330515016c00a5000000000049120000000000b0",
        "330515010000ff0000000000922400000000006b"
      ]
    },
    {
      "name": "Einfacher Effekt",
      "packets": [
        "3305040d700000000000000000000000000000e5"
      ]
    }
  ]
}
```

**Felder:**

| Feld | Typ | Pflicht | Beschreibung |
|---|---|---|---|
| `name` | string | ✅ | Anzeigename im HA-Effekt-Dropdown |
| `description` | string | ❌ | Freitext-Beschreibung (wird nicht von HA genutzt) |
| `packets` | array of strings | ✅ | Liste von Raw-BLE-Paketen als Hex-Strings (je 20 Byte = 40 Zeichen) |

### Paketformat

Jedes Paket ist ein 20-Byte-Hex-String mit XOR-Checksum:

```
Byte 0   : 0x33          – Govee-Prefix
Byte 1   : 0x05          – Kommandofamilie (Farbe/Effekt)
Byte 2   : Subkommando   – z. B. 0x15 = Custom/DIY, 0x04 = eingebaute Szene
Byte 3   : Parameter     – z. B. Segment-Index oder Szenen-ID
Byte 4-18: Nutzdaten     – z. B. RGB-Werte, Effektparameter, Padding
Byte 19  : XOR-Checksum  – XOR über alle vorherigen 19 Bytes
```

### Eigene Raw-Pakete aufzeichnen

Mit dem beiliegenden Standalone-Skript können eigene Pakete aufzeichnet werden:

```bash
python3 govee_h617e.py --mac AA:BB:CC:DD:EE:FF

# Im interaktiven Modus:
> raw 33051501ffffff000000000024490000000000b0   # Paket direkt senden
> rawsave                                        # Letztes Paket speichern
> rec start                                      # Aufzeichnung starten
> rec stop                                       # Aufzeichnung stoppen
> list packets                                   # Alle gespeicherten Pakete anzeigen
```

### Effekt in Home Assistant verwenden

Nach dem Hinzufügen eines Eintrags in `custom_effects.json` und einem **Neustart von Home Assistant** erscheint der Effekt automatisch im Effekt-Dropdown und kann per Automatisierung verwendet werden:

```yaml
service: light.turn_on
target:
  entity_id: light.govee_h617e
data:
  effect: "Mein Effekt"
```

> **Hinweis:** Custom Effekte erscheinen **hinter** den 228 eingebauten Szenen in der Liste.

---

## BLE-Protokoll

Das Protokoll wurde per `btsnoop_hci.log` reverse-engineered und verifiziert.

```
Paketformat: 20 Byte, XOR-Checksum über alle Bytes

Power:      33 01 [01=an / 00=aus] 00×16 CS
Helligkeit: 33 04 [00-FE]          00×16 CS
Farbe:      33 05 15 01 RR GG BB 00×05 FF 7F 00×05 CS
Szene:      33 05 04 [ID] [PARAM] 00×14 CS
```

Write-Characteristic UUIDs:
- `00010203-0405-0607-0809-0a0b0c0d2b11` (bevorzugt)
- `00010203-0405-0607-0809-0a0b0c0d1910` (Fallback)

---

## Standalone-Skript

Das Skript `govee_h617e.py` im Root-Verzeichnis ermöglicht die direkte Steuerung ohne Home Assistant – ideal zum Testen und Debuggen:

```bash
pip install bleak

# Geräte scannen
python3 govee_h617e.py --scan

# Verbinden und interaktive Shell starten
python3 govee_h617e.py --mac AA:BB:CC:DD:EE:FF

# Szenen offline verwalten (ohne BLE-Verbindung)
python3 govee_h617e.py --offline
```

Verfügbare Shell-Befehle: `on`, `off`, `brightness N`, `color R G B`, `scene ID/NAME`, `scenes [FILTER]`, `red`, `green`, `blue`, `white`, `orange`, `purple`, `yellow`, `cyan`, `pink`, `raw HEX`, `rawsave`, `rawplay`, `rec start/stop`, `play NAME`, `list packets`, `list seq`

---

## Bekannte Einschränkungen

- Der H617E meldet seinen Zustand **nicht zurück** über BLE – die Integration arbeitet optimistisch (der zuletzt gesendete Zustand wird als aktuell angenommen).
- Nur ein BLE-Client kann gleichzeitig verbunden sein. Die Govee-App und die HA-Integration sollten nicht gleichzeitig verwendet werden.
- Bluetooth-Reichweite ist geräteabhängig. Bei Verbindungsabbrüchen verbindet sich die Integration beim nächsten Befehl automatisch neu.

---

## Lizenz

MIT License – Copyright 2026 N30Z

---

## Credits

- Protokoll-Analyse: Eigene Reverse-Engineering-Arbeit via `btsnoop_hci.log`
- Inspiration: [Beshelmek/govee_ble_lights](https://github.com/Beshelmek/govee_ble_lights)
- BLE-Bibliothek: [bleak](https://github.com/hbldh/bleak)
