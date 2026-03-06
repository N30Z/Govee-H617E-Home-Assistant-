"""Diagnostics for Govee H617E."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MAC
from homeassistant.core import HomeAssistant

from .const import DOMAIN

TO_REDACT = {CONF_MAC, "preferred_address"}


async def async_get_config_entry_diagnostics(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    payload: dict[str, Any] = {
        "entry": dict(entry.data),
        "options": dict(entry.options),
        "model": "H617E",
        "features": {
            "power": True,
            "brightness": True,
            "rgb": True,
            "effects": True,
            "segments": coordinator.experimental_segments,
        },
        "connection": {
            "available": coordinator.state.available,
            "last_effect": coordinator.state.effect,
        },
    }
    return async_redact_data(payload, TO_REDACT)
