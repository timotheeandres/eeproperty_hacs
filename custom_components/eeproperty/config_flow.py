"""Config flow for eeproperty integration."""
import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EePropertyApiClient
from .const import CONF_2FA, CONF_BUILDING_CODE, CONF_PERSONAL_CODE, CONF_TOKEN_DATE, CONF_TOKEN_EXPIRY, CONF_USER_ID, \
    CONF_USER_LABEL, \
    DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BUILDING_CODE): str,
        vol.Required(CONF_PERSONAL_CODE): str,
    }
)

STEP_SECURITY_CODE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_2FA): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._client: EePropertyApiClient | None = None
        self._building_code: str | None = None
        self._personal_code: str | None = None

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step: get code and PIN."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            self._building_code = user_input[CONF_BUILDING_CODE]
            self._personal_code = user_input[CONF_PERSONAL_CODE]

            await self.async_set_unique_id(f"{self._building_code}_{self._client.user_id}")
            self._abort_if_unique_id_configured()

            self._client = EePropertyApiClient(self._building_code, self._personal_code, session)

            if await self._client.login():
                if await self._client.send_security_code():
                    self._building_code = user_input[CONF_BUILDING_CODE]
                    self._personal_code = user_input[CONF_PERSONAL_CODE]
                    return await self.async_step_security_code()
                else:
                    errors["base"] = "cannot_send_code"
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors
        )

    async def async_step_security_code(
            self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the security code verification step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            security_code = user_input[CONF_2FA]

            if await self._client.verify_security_code(security_code):
                return self.async_create_entry(
                    title=f"eeproperty ({self._client.user_label or self._building_code})",
                    data={
                        CONF_BUILDING_CODE: self._building_code,
                        CONF_PERSONAL_CODE: self._personal_code,
                        CONF_TOKEN: self._client._token,
                        CONF_TOKEN_DATE: self._client._token_date,
                        CONF_TOKEN_EXPIRY: self._client._token_expiry,
                        CONF_USER_ID: self._client.user_id,
                        CONF_USER_LABEL: self._client.user_label,
                    },
                )
            else:
                errors["base"] = "invalid_code"

        return self.async_show_form(
            step_id="security_code",
            data_schema=STEP_SECURITY_CODE_SCHEMA,
            errors=errors,
            last_step=True
        )
