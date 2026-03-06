"""Data coordinator and state model for Govee H617E."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ble.client import GoveeBleClient
from .ble.protocol import brightness_packet, experimental_segment_packet, power_packet, rgb_packet
from .const import OPTIMISTIC_PARTIAL

_LOGGER = logging.getLogger(__name__)


@dataclass
class H617EState:
    """State split between confirmed and optimistic values."""

    is_on: bool = False
    brightness: int = 255
    rgb_color: tuple[int, int, int] = (255, 255, 255)
    effect: str | None = None
    available: bool = False
    confirmed_effect: str | None = None
    segment_colors: dict[int, tuple[int, int, int]] = field(default_factory=dict)


class GoveeH617ECoordinator(DataUpdateCoordinator[H617EState]):
    """Coordinator owning BLE access and runtime state."""

    def __init__(
        self,
        hass: HomeAssistant,
        ble_client: GoveeBleClient,
        polling_interval: timedelta,
        optimistic_mode: str,
        experimental_segments: bool,
    ) -> None:
        self.ble_client = ble_client
        self.optimistic_mode = optimistic_mode
        self.experimental_segments = experimental_segments
        self.state = H617EState()

        super().__init__(
            hass,
            _LOGGER,
            name="govee_h617e",
            update_interval=polling_interval,
        )

    async def _async_update_data(self) -> H617EState:
        try:
            await self.ble_client.async_ping()
            self.state.available = True
            return self.state
        except Exception as err:
            self.state.available = False
            raise UpdateFailed(str(err)) from err

    async def async_set_power(self, on: bool) -> None:
        await self.ble_client.async_write(power_packet(on))
        self.state.is_on = on
        await self.async_request_refresh()

    async def async_set_brightness(self, brightness: int) -> None:
        await self.ble_client.async_write(brightness_packet(brightness))
        self.state.brightness = brightness
        await self.async_request_refresh()

    async def async_set_rgb(self, rgb: tuple[int, int, int]) -> None:
        await self.ble_client.async_write(rgb_packet(*rgb))
        self.state.rgb_color = rgb
        self.state.effect = None
        await self.async_request_refresh()

    async def async_set_effect(self, name: str, packet: bytes) -> None:
        await self.ble_client.async_write(packet)
        if self.optimistic_mode == OPTIMISTIC_PARTIAL:
            self.state.effect = name
        self.state.confirmed_effect = name
        await self.async_request_refresh()

    async def async_set_segment_color(self, index: int, rgb: tuple[int, int, int]) -> None:
        if not self.experimental_segments:
            raise ValueError("Segment control disabled. Enable experimental segment features in options.")

        # Experimental: this packet format is not fully validated for all H617E firmware versions.
        await self.ble_client.async_write(experimental_segment_packet(index, *rgb))
        self.state.segment_colors[index] = rgb
        await self.async_request_refresh()
