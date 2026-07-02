"""Config flow for China Unicom."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries

from .const import (
    CONF_OPENID,
    CONF_PHONE_NUMBER,
    CONF_REFRESH_INTERVAL,
    DEFAULT_REFRESH_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class ChinaUnicomConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for China Unicom."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if not user_input.get(CONF_OPENID):
                errors["base"] = "openid_required"
            else:
                openid = user_input[CONF_OPENID]
                # Set unique_id so HA can distinguish multiple entries
                await self.async_set_unique_id(f"china_unicom_{openid}")
                # Check if already configured (abort if same openid)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"中国联通 {openid[:3]}****{openid[-4:]}",
                    data={
                        CONF_OPENID: openid,
                        CONF_PHONE_NUMBER: user_input.get(CONF_PHONE_NUMBER, ""),
                        CONF_REFRESH_INTERVAL: user_input.get(
                            CONF_REFRESH_INTERVAL, DEFAULT_REFRESH_INTERVAL
                        ),
                    },
                )

        data_schema = vol.Schema({
            vol.Required(CONF_OPENID): str,
            vol.Optional(CONF_PHONE_NUMBER): str,
            vol.Optional(CONF_REFRESH_INTERVAL, default=DEFAULT_REFRESH_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=60)
            ),
        })

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )