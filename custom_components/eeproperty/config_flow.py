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
    CONF_USER_LABEL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._client: EePropertyApiClient | None = None
        self._building_code: str | None = None
        self._personal_code: str | None = None

    # async def async_step_reauth(
    #         self, entry_data: Mapping[str, Any]
    # ) -> ConfigFlowResult:
    #     # TODO https://developers.home-assistant.io/docs/integration_setup_failures/#handling-expired-credentials
    #     _LOGGER.debug("Re-authentication with %s", entry_data)
    #     await self.async_step_user()

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        _LOGGER.debug("User input: %s", user_input)

        if user_input is not None and CONF_BUILDING_CODE in user_input and CONF_PERSONAL_CODE in user_input:
            session = async_get_clientsession(self.hass)
            self._building_code = user_input[CONF_BUILDING_CODE]
            self._personal_code = user_input[CONF_PERSONAL_CODE]

            self._client = EePropertyApiClient(self._building_code, self._personal_code, session)

            if await self._client.login():
                if await self._client.send_security_code():
                    return await self.async_step_security_code(user_input)
                else:
                    errors["base"] = "cannot_send_code"
            else:
                errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BUILDING_CODE): str,
                    vol.Required(CONF_PERSONAL_CODE): str,
                }
            ),
            errors=errors,
        )

    async def async_step_security_code(
            self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        _LOGGER.debug("User input: %s", user_input)

        if user_input is not None and CONF_2FA in user_input:
            security_code = user_input[CONF_2FA]

            if await self._client.verify_security_code(security_code):
                await self.async_set_unique_id(f"{self._building_code}_{self._client.user_id}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"{self._client.user_label or self._building_code}",
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
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_2FA): str,
                }
            ),
            errors=errors,
            last_step=True
        )
