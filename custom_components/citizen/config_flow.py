"""Config flow for the Citizen integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
)

from .const import (
    CONF_INCLUDE_HISTORICAL,
    DEFAULT_INCLUDE_HISTORICAL,
    DEFAULT_RADIUS_KM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


class CitizenConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a Citizen config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            latitude = user_input[CONF_LATITUDE]
            longitude = user_input[CONF_LONGITUDE]
            await self.async_set_unique_id(f"{latitude:.4f}_{longitude:.4f}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Citizen ({latitude:.4f}, {longitude:.4f})",
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LATITUDE, default=self.hass.config.latitude
                    ): vol.Coerce(float),
                    vol.Required(
                        CONF_LONGITUDE, default=self.hass.config.longitude
                    ): vol.Coerce(float),
                    vol.Required(CONF_RADIUS, default=DEFAULT_RADIUS_KM): vol.All(
                        vol.Coerce(float), vol.Range(min=0.1, max=50.0)
                    ),
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=int(DEFAULT_SCAN_INTERVAL.total_seconds()),
                    ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
                    vol.Required(
                        CONF_INCLUDE_HISTORICAL,
                        default=DEFAULT_INCLUDE_HISTORICAL,
                    ): bool,
                }
            ),
            errors=errors,
        )
