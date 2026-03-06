"""The Govee H617E integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .ble.client import GoveeBleClient
from .ble.protocol import parse_hex_packet
from datetime import timedelta

from .const import (
    ATTR_PACKET_HEX,
    ATTR_PACKET_SEQUENCE,
    ATTR_RGB_COLOR,
    ATTR_SEGMENT_INDEX,
    CONF_CONNECT_TIMEOUT,
    CONF_EXPERIMENTAL_SEGMENTS,
    CONF_OPTIMISTIC_MODE,
    CONF_POLL_INTERVAL,
    CONF_RETRY_COUNT,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_OPTIMISTIC_MODE,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_RETRY_COUNT,
    DOMAIN,
    PLATFORMS,
    SERVICE_APPLY_SCENE_PAYLOAD,
    SERVICE_SET_SEGMENT_COLOR,
)
from .coordinator import GoveeH617ECoordinator

_LOGGER = logging.getLogger(__name__)

SERVICE_SET_SEGMENT_COLOR_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Required(ATTR_SEGMENT_INDEX): vol.All(vol.Coerce(int), vol.Range(min=0, max=64)),
        vol.Required(ATTR_RGB_COLOR): vol.All(cv.ensure_list, vol.Length(min=3, max=3), [vol.All(vol.Coerce(int), vol.Range(min=0, max=255))]),
    }
)

SERVICE_APPLY_SCENE_PAYLOAD_SCHEMA = vol.Schema(
    {
        vol.Required("entry_id"): cv.string,
        vol.Exclusive(ATTR_PACKET_HEX, "payload"): cv.string,
        vol.Exclusive(ATTR_PACKET_SEQUENCE, "payload"): vol.All(cv.ensure_list, [cv.string]),
    }
)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    hass.data.setdefault(DOMAIN, {})

    async def async_set_segment_color(call: ServiceCall) -> None:
        entry_id = call.data["entry_id"]
        coordinator: GoveeH617ECoordinator = hass.data[DOMAIN][entry_id]["coordinator"]
        rgb_raw = call.data[ATTR_RGB_COLOR]
        if len(rgb_raw) != 3:
            raise ValueError("rgb_color must contain exactly 3 values")
        await coordinator.async_set_segment_color(call.data[ATTR_SEGMENT_INDEX], tuple(rgb_raw))

    async def async_apply_scene_payload(call: ServiceCall) -> None:
        entry_id = call.data["entry_id"]
        coordinator: GoveeH617ECoordinator = hass.data[DOMAIN][entry_id]["coordinator"]

        if ATTR_PACKET_HEX in call.data:
            await coordinator.ble_client.async_write(parse_hex_packet(call.data[ATTR_PACKET_HEX]))
            return

        for packet_hex in call.data[ATTR_PACKET_SEQUENCE]:
            await coordinator.ble_client.async_write(parse_hex_packet(packet_hex))

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SEGMENT_COLOR,
        async_set_segment_color,
        schema=SERVICE_SET_SEGMENT_COLOR_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_APPLY_SCENE_PAYLOAD,
        async_apply_scene_payload,
        schema=SERVICE_APPLY_SCENE_PAYLOAD_SCHEMA,
    )
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    options = entry.options
    ble_client = GoveeBleClient(
        address=options.get("preferred_address", entry.data[CONF_MAC]),
        connect_timeout=options.get(CONF_CONNECT_TIMEOUT, DEFAULT_CONNECT_TIMEOUT),
        retry_count=options.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT),
    )

    coordinator = GoveeH617ECoordinator(
        hass=hass,
        ble_client=ble_client,
        polling_interval=timedelta(seconds=options.get(CONF_POLL_INTERVAL, int(DEFAULT_POLL_INTERVAL.total_seconds()))),
        optimistic_mode=options.get(CONF_OPTIMISTIC_MODE, DEFAULT_OPTIMISTIC_MODE),
        experimental_segments=options.get(CONF_EXPERIMENTAL_SEGMENTS, False),
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = {"coordinator": coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: GoveeH617ECoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        await coordinator.ble_client.async_disconnect()
        hass.data[DOMAIN].pop(entry.entry_id)

    if not hass.data[DOMAIN]:
        hass.services.async_remove(DOMAIN, SERVICE_SET_SEGMENT_COLOR)
        hass.services.async_remove(DOMAIN, SERVICE_APPLY_SCENE_PAYLOAD)
    return unload_ok
