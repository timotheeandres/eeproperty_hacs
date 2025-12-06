"""Config flow for eeProperty integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EePropertyApiClient
from .const import CONF_CODE, CONF_PIN, CONF_TOKEN, CONF_USER_ID, CONF_USER_LABEL, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CODE): str,
        vol.Required(CONF_PIN): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for eeProperty."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._client: EePropertyApiClient | None = None
        self._code: str | None = None
        self._pin: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - get code and PIN."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Store credentials and test login
            session = async_get_clientsession(self.hass)
            self._client = EePropertyApiClient(
                user_input[CONF_CODE],
                user_input[CONF_PIN],
                session,
            )

            # Try to login and send security code
            if await self._client.login():
                if await self._client.send_security_code():
                    # Store data for next step
                    self._code = user_input[CONF_CODE]
                    self._pin = user_input[CONF_PIN]
                    # Move to security code verification
                    return await self.async_step_security_code()
                else:
                    errors["base"] = "cannot_send_code"
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "code_info": "Your eeProperty building code (e.g., LEX8)",
                "pin_info": "Your personal PIN code",
            },
        )

    async def async_step_security_code(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the security code verification step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            security_code = user_input["security_code"]

            # Verify the security code
            if await self._client.verify_security_code(security_code):
                # Set a unique ID for this config entry
                await self.async_set_unique_id(
                    f"{self._code}_{self._client.user_id}"
                )
                self._abort_if_unique_id_configured()

                # Store credentials AND token for persistence
                return self.async_create_entry(
                    title=f"eeProperty ({self._client.user_label or self._code})",
                    data={
                        CONF_CODE: self._code,
                        CONF_PIN: self._pin,
                        CONF_TOKEN: self._client._token,
                        CONF_USER_ID: self._client.user_id,
                        CONF_USER_LABEL: self._client.user_label,
                    },
                )
            else:
                errors["base"] = "invalid_code"

        return self.async_show_form(
            step_id="security_code",
            data_schema=vol.Schema(
                {
                    vol.Required("security_code"): str,
                }
            ),
            errors=errors,
            description_placeholders={
                "info": "Enter the security code sent to your registered contact method",
            },
        )
