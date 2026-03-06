"""Config flow for Govee H617E."""
from __future__ import annotations

import re
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_MAC, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_CONNECT_TIMEOUT,
    CONF_DEBUG_LOGGING,
    CONF_EXPERIMENTAL_SEGMENTS,
    CONF_OPTIMISTIC_MODE,
    CONF_POLL_INTERVAL,
    CONF_PREFERRED_ADDRESS,
    CONF_RETRY_COUNT,
    CONF_SEGMENT_COUNT_OVERRIDE,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_NAME,
    DEFAULT_OPTIMISTIC_MODE,
    DEFAULT_RETRY_COUNT,
    DOMAIN,
    OPTIMISTIC_AUTO,
    OPTIMISTIC_PARTIAL,
    OPTIMISTIC_STRICT,
)

MAC_RE = re.compile(r"^([0-9A-F]{2}:){5}[0-9A-F]{2}$")


class GoveeH617EConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle setup via bluetooth discovery and manual path."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_address: str | None = None
        self._discovered_name: str | None = None

    async def async_step_bluetooth(self, discovery_info: bluetooth.BluetoothServiceInfoBleak) -> FlowResult:
        name = discovery_info.name or ""
        if "H617E" not in name.upper() and not name.upper().startswith("GOVEE"):
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovered_address = discovery_info.address
        self._discovered_name = discovery_info.name or DEFAULT_NAME
        self.context["title_placeholders"] = {"name": self._discovered_name}
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovered_name or DEFAULT_NAME,
                data={CONF_MAC: self._discovered_address, CONF_NAME: self._discovered_name or DEFAULT_NAME},
            )
        return self.async_show_form(step_id="confirm")

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            mac = user_input[CONF_MAC].strip().upper()
            if not MAC_RE.match(mac):
                errors["base"] = "invalid_mac"
            else:
                await self.async_set_unique_id(mac)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data={CONF_MAC: mac, CONF_NAME: user_input.get(CONF_NAME, DEFAULT_NAME)},
                )

        schema = vol.Schema({vol.Required(CONF_MAC): str, vol.Optional(CONF_NAME, default=DEFAULT_NAME): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return GoveeH617EOptionsFlow(config_entry)


class GoveeH617EOptionsFlow(config_entries.OptionsFlow):
    """Options for reliability and experimental controls."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self._entry.options
        schema = vol.Schema(
            {
                vol.Optional(CONF_PREFERRED_ADDRESS, default=options.get(CONF_PREFERRED_ADDRESS, self._entry.data[CONF_MAC])): str,
                vol.Optional(CONF_POLL_INTERVAL, default=options.get(CONF_POLL_INTERVAL, 30)): vol.All(vol.Coerce(int), vol.Range(min=5, max=300)),
                vol.Optional(CONF_CONNECT_TIMEOUT, default=options.get(CONF_CONNECT_TIMEOUT, DEFAULT_CONNECT_TIMEOUT)): vol.All(vol.Coerce(float), vol.Range(min=3, max=30)),
                vol.Optional(CONF_RETRY_COUNT, default=options.get(CONF_RETRY_COUNT, DEFAULT_RETRY_COUNT)): vol.All(vol.Coerce(int), vol.Range(min=0, max=6)),
                vol.Optional(CONF_EXPERIMENTAL_SEGMENTS, default=options.get(CONF_EXPERIMENTAL_SEGMENTS, False)): bool,
                vol.Optional(CONF_SEGMENT_COUNT_OVERRIDE, default=options.get(CONF_SEGMENT_COUNT_OVERRIDE, 0)): vol.All(vol.Coerce(int), vol.Range(min=0, max=32)),
                vol.Optional(CONF_DEBUG_LOGGING, default=options.get(CONF_DEBUG_LOGGING, False)): bool,
                vol.Optional(CONF_OPTIMISTIC_MODE, default=options.get(CONF_OPTIMISTIC_MODE, DEFAULT_OPTIMISTIC_MODE)): vol.In(
                    [OPTIMISTIC_AUTO, OPTIMISTIC_STRICT, OPTIMISTIC_PARTIAL]
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
