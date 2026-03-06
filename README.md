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

### Via HACS (empfohlen / recommended)

1. [HACS](https://hacs.xyz) in Home Assistant installiert haben.
2. HACS öffnen → **„Custom repositories"** → URL `https://github.com/N30Z/Govee-H617E-Home-Assistant-` eingeben → Typ **„Integration"** wählen → **Hinzufügen**.
3. In HACS nach **„Govee H617E"** suchen und **Installieren** klicken.
4. Home Assistant neu starten.

> **English:** Open HACS → *Custom repositories* → add `https://github.com/N30Z/Govee-H617E-Home-Assistant-` as type *Integration* → search for **Govee H617E** and install → restart Home Assistant.

---

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
service: govee_h617e.set_segment_color
data:
  entry_id: "<config_entry_id>"
  segment_index: 2
  rgb_color: [255, 50, 0]
```

Raw-Beispiel:
```yaml
service: govee_h617e.apply_scene_payload
data:
  entry_id: "<config_entry_id>"
  packet_hex: "3305040100000000000000000000000000000033"
```

## 8) Debugging
### Logger
```yaml
logger:
  default: info
  logs:
    custom_components.govee_h617e: debug
    custom_components.govee_h617e.ble: debug
```

### Wichtige Analysepunkte
- Discovery ok, aber Connect fail → meist Host/Container/DBus-Problem.
- Connect ok, aber keine Reaktion → Reichweite/Interferenz/firmwareabhängige Kommandos prüfen.
- Instabilität unter Last → Polling erhöhen, Retry/Timeout leicht anheben.

Checkliste „Gerät wird nicht gefunden“:
- Adapter vorhanden?
- DBus gemountet?
- host networking aktiv?
- aktives Scannen getestet?
- Strip in Reichweite?

Checkliste „verbindet sich, reagiert aber falsch“:
- Modell wirklich H617E?
- Experimentelle Features deaktivieren.
- Nur stabile Kernfunktionen testen (Power/Brightness/RGB).

## 9) Technische Grenzen
- Confirmed vs. Optimistic State werden getrennt geführt.
- Segmentbefehle sind explizit experimentell (firmwareabhängig).
- BLE-Protokoll ist nicht vollständig offiziell dokumentiert.

## 10) Entwicklung
- Struktur folgt HA-Patterns (config flow, options, diagnostics, coordinator).
- Tests unter `tests/components/govee_h617e/`.
- Für weitere Govee-Modelle: neues Modellmodul + capability mapping ergänzen, BLE-Transport wiederverwenden.

## 11) Roadmap
- Mehr Govee-BLE-Modelle
- Bessere Segment-Rücklesbarkeit
- Zusätzliche valide Szenenprofile
- Feinere Retry-/Reconnect-Telemetrie

## 12) Haftungshinweis / Transparenz
Diese Integration nutzt lokal validierte BLE-Kommandos und enthält experimentelle Bereiche für noch nicht vollständig belastbar dokumentierte Protokollteile. Experimentelle Features sind entsprechend gekennzeichnet und standardmäßig defensiv ausgelegt.

---

## Projektstruktur
```text
custom_components/govee_h617e/
  __init__.py
  manifest.json
  const.py
  config_flow.py
  coordinator.py
  diagnostics.py
  light.py
  select.py
  number.py
  switch.py
  services.yaml
  strings.json
  ble/
    __init__.py
    client.py
    protocol.py
  translations/
    en.json
    de.json

tests/components/govee_h617e/
  test_config_flow.py
  test_options_flow.py
  test_init.py
  test_coordinator.py
  test_protocol.py
  test_services.py
```
