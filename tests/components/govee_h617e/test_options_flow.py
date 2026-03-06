from homeassistant.data_entry_flow import FlowResultType

from custom_components.govee_h617e.config_flow import GoveeH617EOptionsFlow


async def test_options_flow_create_entry(hass, MockConfigEntry) -> None:
    entry = MockConfigEntry(domain="govee_h617e", data={"mac": "AA:BB:CC:DD:EE:FF"})
    flow = GoveeH617EOptionsFlow(entry)
    result = await flow.async_step_init(None)
    assert result["type"] == FlowResultType.FORM
