from unittest.mock import AsyncMock

import pytest

from custom_components.govee_h617e.const import DOMAIN, SERVICE_SET_SEGMENT_COLOR


@pytest.mark.asyncio
async def test_segment_service_invalid_rgb(hass) -> None:
    coordinator = AsyncMock()
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["entry"] = {"coordinator": coordinator}

    from custom_components.govee_h617e import async_setup

    await async_setup(hass, {})

    with pytest.raises(Exception):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_SEGMENT_COLOR,
            {"entry_id": "entry", "segment_index": 0, "rgb_color": [1, 2]},
            blocking=True,
        )
