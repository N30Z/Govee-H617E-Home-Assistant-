from datetime import timedelta

import pytest

from custom_components.govee_h617e.const import OPTIMISTIC_PARTIAL
from custom_components.govee_h617e.coordinator import GoveeH617ECoordinator


class FakeBleClient:
    def __init__(self) -> None:
        self.available = True
        self.payloads: list[bytes] = []
        self.fail = False

    async def async_write(self, payload: bytes) -> None:
        if self.fail:
            raise RuntimeError("write failed")
        self.payloads.append(payload)

    async def async_ping(self) -> None:
        if self.fail:
            raise RuntimeError("unreachable")


@pytest.mark.asyncio
async def test_set_segment_disabled_raises(hass) -> None:
    coordinator = GoveeH617ECoordinator(
        hass,
        FakeBleClient(),
        timedelta(seconds=30),
        optimistic_mode=OPTIMISTIC_PARTIAL,
        experimental_segments=False,
    )
    with pytest.raises(ValueError):
        await coordinator.async_set_segment_color(1, (255, 0, 0))


@pytest.mark.asyncio
async def test_reconnect_error_propagates(hass) -> None:
    client = FakeBleClient()
    client.fail = True
    coordinator = GoveeH617ECoordinator(hass, client, timedelta(seconds=30), OPTIMISTIC_PARTIAL, False)
    with pytest.raises(Exception):
        await coordinator._async_update_data()
