"""Config flow for the Govee H617E integration."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_MAC, CONF_NAME

from .const import DEFAULT_NAME, DOMAIN

MAC_PATTERN = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_MAC): str,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
    }
)


class GoveeH617EConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Govee H617E."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            mac = user_input[CONF_MAC].upper().strip()

            if not MAC_PATTERN.match(mac):
                errors["base"] = "invalid_mac"
            else:
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_configured()

                name = user_input.get(CONF_NAME) or f"Govee H617E ({mac})"

                return self.async_create_entry(
                    title=name,
                    data={CONF_MAC: mac, CONF_NAME: name},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
        )
