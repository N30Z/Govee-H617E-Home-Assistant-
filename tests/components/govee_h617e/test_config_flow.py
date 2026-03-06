from homeassistant import config_entries
from homeassistant.const import CONF_MAC
from homeassistant.data_entry_flow import FlowResultType

from custom_components.govee_h617e.const import DOMAIN


async def test_user_flow_success(hass) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_MAC: "AA:BB:CC:DD:EE:FF", "name": "Strip"},
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY


async def test_user_flow_invalid_mac(hass) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {CONF_MAC: "invalid"})
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"]["base"] == "invalid_mac"
