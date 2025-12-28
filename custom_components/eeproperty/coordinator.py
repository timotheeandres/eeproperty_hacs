import logging
from datetime import timedelta
from typing import List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.eeproperty import EePropertyApiClient
from custom_components.eeproperty.const import DEFAULT_SCAN_INTERVAL, DOMAIN
from custom_components.eeproperty.models import EePropertyData, Machine, User

_LOGGER = logging.getLogger(__name__)


class EePropertyDataUpdateCoordinator(DataUpdateCoordinator[EePropertyData]):
    """Class to manage fetching eeproperty data."""

    def __init__(
            self,
            hass: HomeAssistant,
            config_entry,
            client: EePropertyApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            always_update=False
        )
        self._client = client

    async def _async_update_data(self) -> EePropertyData:
        try:
            machines = await self._client.get_machines()
            user_data = await self._client.get_user_data()

            return EePropertyData(machines=machines, user=user_data)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with eeproperty API") from err

    def get_machines_data(self) -> List[Machine] | None:
        if not self.data:
            return None
        return self.data.machines

    def get_user_data(self) -> User | None:
        if not self.data:
            return None
        return self.data.user
