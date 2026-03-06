"""Scene select entity for separating device scenes from light effects."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import GoveeH617ECoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: GoveeH617ECoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([GoveeSceneModeSelect(coordinator, entry.entry_id)])


class GoveeSceneModeSelect(CoordinatorEntity[GoveeH617ECoordinator], SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Scene mode"
    _attr_options = ["light_effects", "device_scenes"]

    def __init__(self, coordinator: GoveeH617ECoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_scene_mode"
        self._attr_current_option = "light_effects"

    async def async_select_option(self, option: str) -> None:
        self._attr_current_option = option
        self.async_write_ha_state()
