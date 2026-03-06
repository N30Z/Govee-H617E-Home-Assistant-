"""Switch entities for optional operating modes."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_EXPERIMENTAL_SEGMENTS, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([GoveeExperimentalSegmentsSwitch(entry.entry_id, entry.options.get(CONF_EXPERIMENTAL_SEGMENTS, False))])


class GoveeExperimentalSegmentsSwitch(SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Experimental segments enabled"

    def __init__(self, entry_id: str, is_on: bool) -> None:
        self._attr_unique_id = f"{entry_id}_experimental_segments"
        self._attr_is_on = is_on

    async def async_turn_on(self, **kwargs) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()
