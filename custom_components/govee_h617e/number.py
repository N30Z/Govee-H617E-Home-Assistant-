"""Number entities for advanced tuning."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_SEGMENT_COUNT_OVERRIDE, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    async_add_entities([GoveeSegmentCountNumber(entry.entry_id, entry.options.get(CONF_SEGMENT_COUNT_OVERRIDE, 0))])


class GoveeSegmentCountNumber(NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Segment count override"
    _attr_native_min_value = 0
    _attr_native_max_value = 32
    _attr_native_step = 1

    def __init__(self, entry_id: str, initial: int) -> None:
        self._attr_unique_id = f"{entry_id}_segment_count"
        self._attr_native_value = initial

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
