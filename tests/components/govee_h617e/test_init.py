from unittest.mock import AsyncMock, patch

from homeassistant.const import CONF_MAC, CONF_NAME

from custom_components.govee_h617e.const import DOMAIN


async def test_setup_unload_entry(hass, MockConfigEntry) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_MAC: "AA:BB:CC:DD:EE:FF", CONF_NAME: "Strip"})
    entry.add_to_hass(hass)

    with patch("custom_components.govee_h617e.GoveeBleClient.async_connect", new=AsyncMock(return_value=None)):
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.entry_id in hass.data[DOMAIN]
    assert await hass.config_entries.async_unload(entry.entry_id)
