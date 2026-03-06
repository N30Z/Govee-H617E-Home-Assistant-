# Govee H617E BLE – Home Assistant Custom Integration

## 1) Projektziel
Diese Integration bringt den **Bluetooth-only LED-Strip Govee H617E** lokal in Home Assistant, ohne Cloud-Pfad. Schwerpunkt ist ein alltagstauglicher, erweiterbarer Aufbau für den Betrieb auf **Home Assistant Container auf Raspberry Pi**.

Warum `govee_h617e` als Domain?
- Modellklare Zuordnung (wichtig, weil Govee BLE model-spezifisch ist).
- Keine impliziten Versprechen für andere Modelle.
- Saubere Basis, um später optional ein Multi-Model-Projekt aufzubauen.

## 2) Unterstützter Umfang
### Stabil
- Power On/Off
- Brightness
- RGB-Farbe
- Effekt-Auswahl aus lokal hinterlegten, verifizierten Szenenpaketen (`scenes.json`)
- Robuster BLE-Write-Pfad mit Locking + Retry + Reconnect

### Experimentell
- Segmentsteuerung (`set_segment_color`) hinter Feature-Flag im Options Flow
- Raw-Scene-Payloads via Service (`apply_scene_payload`) als Advanced/Debug-Werkzeug

### Bewusst nicht vollständig
- Keine behauptete vollständige Rücklesbarkeit aller H617E-States
- Keine als "voll sicher" deklarierten Segment-/Szenen-Protokolldetails, wenn sie firmwareabhängig sind

## 3) Architekturüberblick
Struktur:
- `ble/`: Transport + Protokoll-Helfer
- `coordinator.py`: State-Modell, Reconnect, zentrale Schreiblogik
- Entity-Schicht (`light.py`, `select.py`, `number.py`, `switch.py`)
- Config/Options/Diagnostics/Services HA-konform

Designentscheidungen:
- **Strikte Trennung** zwischen BLE-Transport, Modelllogik und HA-Entities.
- **Serielle BLE-Kommandos** über Lock im Client, damit parallele Service-Calls keine Race Conditions erzeugen.
- **Optimistic State** nur dort, wo Rücklesbarkeit technisch unsicher ist.

## 4) Voraussetzungen (Raspberry Pi + HA Container)
Pflichtpunkte für stabile BLE-Nutzung im Container:
1. BlueZ läuft auf dem Host.
2. DBus ist in den Container gemountet (`/run/dbus`).
3. Host-Networking empfohlen (`--network host`).
4. Container privilegiert oder passende Capabilities / Devices.
5. Bluetooth-Adapter im Host sichtbar (`bluetoothctl list`).

Typische Stolperfallen auf Raspberry Pi:
- 2,4-GHz Interferenzen (WLAN/BLE gleichzeitig).
- Zu große Distanz / Abschattung.
- Instabile Dongles oder aggressive USB-Energiesparmodi.
- Container ohne DBus-Mount → Discovery/Connect schlägt fehl.
- Falscher Scanmodus (aktiv/passiv je nach Gerät relevant).

## 5) Installation
### HACS (vorbereitet)
1. Repository als Custom Repository in HACS hinzufügen.
2. Integration installieren.
3. Home Assistant neu starten.
4. Integration in UI hinzufügen.

### Manuell
1. `custom_components/govee_h617e` nach `<config>/custom_components/` kopieren.
2. Home Assistant neu starten.
3. Integration über UI hinzufügen.

## 6) Konfiguration
### Config Flow
- Bluetooth Discovery (wenn Name/Muster passt)
- Manueller Pfad mit MAC-Adresse
- Duplicate Prevention via Unique ID

### Options Flow
- Preferred BLE Address
- Polling-Intervall
- Connect Timeout
- Retry Count
- Experimental Segments (Flag)
- Segment Count Override
- Debug Logging
- State-Modus (`strict`, `auto`, `partial`)

Empfohlene Defaults:
- Polling: 30s
- Timeout: 12s
- Retry: 2
- Segments: aus (nur bei validiertem Gerät aktivieren)
- Optimistic: `auto`

## 7) Nutzung im Alltag
### Light Entity
- `light.<name>` mit on/off, brightness, rgb, effect

### Szenen/Effekte
- Klassische Effekte über `effect` in der Light-Entity.
- Erweiterte/rohe Payloads über Service `apply_scene_payload`.

### Segmentsteuerung
- Service: `govee_h617e.set_segment_color`
- Nur aktiv, wenn experimentelles Flag gesetzt ist.

Service-Beispiel:
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
