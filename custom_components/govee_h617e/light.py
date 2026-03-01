"""Govee H617E Light Entity."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Any

from bleak import BleakClient, BleakError

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, GOVEE_CHAR_UUIDS

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# BLE packet helpers
# ---------------------------------------------------------------------------

def _build(cmd: int, payload: list[int]) -> bytes:
    """Build a 20-byte Govee BLE packet with XOR checksum."""
    data = [0x33, cmd] + payload
    data += [0x00] * (19 - len(data))
    cs = 0
    for b in data:
        cs ^= b
    data.append(cs)
    return bytes(data)


def _pkt_power(on: bool) -> bytes:
    return _build(0x01, [0x01 if on else 0x00])


def _pkt_brightness(pct: int) -> bytes:
    """Brightness 0-100 % → BLE value 0x00-0xFE."""
    val = round(max(0, min(100, pct)) / 100 * 0xFE)
    return _build(0x04, [val])


def _pkt_color(r: int, g: int, b: int) -> bytes:
    return _build(0x05, [0x15, 0x01, r, g, b, 0, 0, 0, 0, 0, 0xFF, 0x7F])


# ---------------------------------------------------------------------------
# Scene loader
# ---------------------------------------------------------------------------

def _load_scenes() -> list[dict]:
    """Load scenes from the bundled scenes.json."""
    path = os.path.join(os.path.dirname(__file__), "scenes.json")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data.get("scenes", [])
    except (FileNotFoundError, json.JSONDecodeError) as err:
        _LOGGER.warning("Could not load scenes.json: %s", err)
        return []


# ---------------------------------------------------------------------------
# Platform setup
# ---------------------------------------------------------------------------

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Govee H617E light platform."""
    mac: str = entry.data[CONF_MAC]
    name: str = entry.data.get(CONF_NAME, f"Govee H617E ({mac})")
    scenes = await hass.async_add_executor_job(_load_scenes)
    async_add_entities([GoveeH617ELight(mac, name, scenes)], update_before_add=False)


# ---------------------------------------------------------------------------
# Light entity
# ---------------------------------------------------------------------------

class GoveeH617ELight(LightEntity):
    """Representation of a Govee H617E LED strip."""

    _attr_should_poll = False
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(self, mac: str, name: str, scenes: list[dict]) -> None:
        self._mac = mac
        self._attr_name = name
        self._attr_unique_id = mac.replace(":", "").lower()

        # Scene list – use the raw hex packets from scenes.json
        self._scenes: list[dict] = scenes
        self._attr_effect_list = [
            s["name"] for s in scenes if s.get("name")
        ]

        # BLE state
        self._client: BleakClient | None = None
        self._char_uuid: str | None = None
        self._connect_lock = asyncio.Lock()

        # Light state (optimistic – we don't read back from the device)
        self._attr_is_on = False
        self._attr_brightness = 255
        self._attr_rgb_color: tuple[int, int, int] = (255, 255, 255)
        self._attr_effect: str | None = None
        self._attr_available = True

    # ------------------------------------------------------------------
    # HA lifecycle
    # ------------------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        """Try to connect when the entity is first registered."""
        self.hass.async_create_task(self._connect())

    async def async_will_remove_from_hass(self) -> None:
        """Disconnect cleanly when entity is removed."""
        await self._disconnect()

    # ------------------------------------------------------------------
    # BLE connection management
    # ------------------------------------------------------------------

    def _disconnected_callback(self, client: BleakClient) -> None:
        """Called by bleak when the peripheral drops the connection."""
        _LOGGER.debug("Govee H617E %s disconnected", self._mac)
        self._client = None
        self._char_uuid = None
        # Don't mark unavailable – we'll reconnect on next command

    async def _connect(self) -> bool:
        """Establish a BLE connection and discover the write characteristic."""
        async with self._connect_lock:
            if self._client and self._client.is_connected:
                return True

            _LOGGER.debug("Connecting to Govee H617E %s …", self._mac)
            try:
                client = BleakClient(
                    self._mac,
                    timeout=15.0,
                    disconnected_callback=self._disconnected_callback,
                )
                await client.connect()
                if not client.is_connected:
                    _LOGGER.warning("Could not connect to %s", self._mac)
                    return False

                self._client = client
                self._char_uuid = self._find_write_char()
                if self._char_uuid:
                    _LOGGER.debug("Connected, char UUID: %s", self._char_uuid)
                    return True
                _LOGGER.warning("No writable characteristic found on %s", self._mac)
                return False

            except (BleakError, asyncio.TimeoutError, OSError) as err:
                _LOGGER.error("BLE connect error (%s): %s", self._mac, err)
                self._client = None
                return False

    def _find_write_char(self) -> str | None:
        """Return the first matching write characteristic UUID."""
        if not self._client:
            return None
        # Prefer the known Govee UUIDs
        for service in self._client.services:
            for char in service.characteristics:
                props = char.properties
                if "write" in props or "write-without-response" in props:
                    if char.uuid.lower() in GOVEE_CHAR_UUIDS:
                        return char.uuid
        # Fallback: any writable characteristic
        for service in self._client.services:
            for char in service.characteristics:
                props = char.properties
                if "write" in props or "write-without-response" in props:
                    _LOGGER.debug("Using fallback char: %s", char.uuid)
                    return char.uuid
        return None

    async def _disconnect(self) -> None:
        """Disconnect from the BLE device."""
        if self._client:
            try:
                await self._client.disconnect()
            except Exception:  # noqa: BLE001
                pass
            self._client = None
            self._char_uuid = None

    async def _send(self, pkt: bytes) -> bool:
        """Send a raw BLE packet, reconnecting if necessary."""
        # Reconnect if needed
        if not self._client or not self._client.is_connected:
            if not await self._connect():
                _LOGGER.warning("Cannot send – not connected to %s", self._mac)
                return False

        try:
            await self._client.write_gatt_char(
                self._char_uuid, pkt, response=False
            )
            _LOGGER.debug("Sent %s → %s", pkt.hex(), self._mac)
            return True
        except (BleakError, asyncio.TimeoutError, OSError) as err:
            _LOGGER.error("BLE send error (%s): %s", self._mac, err)
            self._client = None
            self._char_uuid = None
            return False

    # ------------------------------------------------------------------
    # Light control
    # ------------------------------------------------------------------

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the strip on, optionally setting brightness, colour or effect."""
        # Power on if currently off
        if not self._attr_is_on:
            if not await self._send(_pkt_power(True)):
                return
            self._attr_is_on = True

        # --- Effect (scene) ---
        if ATTR_EFFECT in kwargs:
            effect_name: str = kwargs[ATTR_EFFECT]
            scene = next(
                (s for s in self._scenes if s.get("name") == effect_name),
                None,
            )
            if scene:
                pkt = bytes.fromhex(scene["hex"])
                if await self._send(pkt):
                    self._attr_effect = effect_name
                    self.async_write_ha_state()
                return
            _LOGGER.warning("Unknown effect: %s", effect_name)
            return

        # --- RGB colour ---
        if ATTR_RGB_COLOR in kwargs:
            r, g, b = kwargs[ATTR_RGB_COLOR]
            if await self._send(_pkt_color(r, g, b)):
                self._attr_rgb_color = (r, g, b)
                self._attr_effect = None  # colour overrides any active scene

        # --- Brightness (HA 0-255 → device 0-100 %) ---
        if ATTR_BRIGHTNESS in kwargs:
            pct = round(kwargs[ATTR_BRIGHTNESS] / 255 * 100)
            if await self._send(_pkt_brightness(pct)):
                self._attr_brightness = kwargs[ATTR_BRIGHTNESS]

        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the strip off."""
        if await self._send(_pkt_power(False)):
            self._attr_is_on = False
            self._attr_effect = None
            self.async_write_ha_state()
