"""The eeproperty integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EePropertyApiClient
from .const import (
    CONF_CODE,
    CONF_PIN,
    CONF_TOKEN,
    CONF_USER_ID,
    CONF_USER_LABEL,
    DOMAIN as DOM,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

DOMAIN = DOM

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up eeproperty from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    code = entry.data[CONF_CODE]
    pin = entry.data[CONF_PIN]
    token = entry.data.get(CONF_TOKEN)
    user_id = entry.data.get(CONF_USER_ID)
    user_label = entry.data.get(CONF_USER_LABEL)

    session = async_get_clientsession(hass)
    client = EePropertyApiClient(code, pin, session, token, user_id, user_label)

    # Validate the stored token
    if token:
        if not await client.validate_token():
            _LOGGER.warning(
                "Stored token is invalid or expired. Attempting re-authentication..."
            )
            # Try to get a new token with the stored credentials
            if not await client.login():
                _LOGGER.error("Failed to re-authenticate with stored credentials")
                raise ConfigEntryAuthFailed(
                    "Authentication failed. Please reconfigure the integration."
                )

            # Send security code request
            if not await client.send_security_code():
                _LOGGER.error("Failed to send security code for re-authentication")
                raise ConfigEntryAuthFailed(
                    "Failed to send security code. Please reconfigure the integration."
                )

            # We can't automatically complete the 2FA without user input
            # So we need to raise an error and ask user to reconfigure
            _LOGGER.error(
                "Token expired and 2FA is required. Please reconfigure the integration."
            )
            raise ConfigEntryAuthFailed(
                "Token expired. Please reconfigure the integration to complete 2FA."
            )
        else:
            _LOGGER.info("Token validated successfully")
    else:
        # No token stored (shouldn't happen with new config flow, but handle it)
        _LOGGER.error("No token found in config entry")
        raise ConfigEntryAuthFailed(
            "No authentication token found. Please reconfigure the integration."
        )

    hass.data[DOMAIN][entry.entry_id] = client

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
