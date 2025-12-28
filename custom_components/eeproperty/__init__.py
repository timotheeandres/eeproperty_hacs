"""The eeproperty integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EePropertyApiClient
from .const import (CONF_BUILDING_CODE, CONF_PERSONAL_CODE, CONF_TOKEN_DATE, CONF_TOKEN_EXPIRY, CONF_USER_ID,
                    CONF_USER_LABEL, DOMAIN as DOM)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

DOMAIN = DOM


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up eeproperty from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    building_code = entry.data[CONF_BUILDING_CODE]
    personal_code = entry.data[CONF_PERSONAL_CODE]
    token = entry.data.get(CONF_TOKEN)
    token_date = entry.data.get(CONF_TOKEN_DATE)
    token_expiry = entry.data.get(CONF_TOKEN_EXPIRY)
    user_id = entry.data.get(CONF_USER_ID)
    user_label = entry.data.get(CONF_USER_LABEL)

    session = async_get_clientsession(hass)
    client = EePropertyApiClient(building_code, personal_code, session, user_id, user_label, token, token_date,
                                 token_expiry)

    if token:
        if not await client.validate_token():
            _LOGGER.warning(
                "Stored token is invalid or expired. Attempting re-authentication..."
            )
            if not await client.login():
                _LOGGER.error("Failed to re-authenticate with stored credentials")
                raise ConfigEntryAuthFailed(
                    "Authentication failed. Please reconfigure the integration."
                )

            if not await client.send_security_code():
                _LOGGER.error("Failed to send security code for re-authentication")
                raise ConfigEntryAuthFailed(
                    "Failed to send security code. Please reconfigure the integration."
                )

            _LOGGER.error(
                "Token expired and 2FA is required. Please reconfigure the integration."
            )
            raise ConfigEntryAuthFailed(
                "Token expired. Please reconfigure the integration to complete 2FA."
            )
        else:
            _LOGGER.debug("Token validated successfully")
    else:
        raise ConfigEntryAuthFailed("No authentication token found.")

    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
