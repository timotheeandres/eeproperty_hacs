import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.eeproperty import EePropertyApiClient
from custom_components.eeproperty.const import DEFAULT_SCAN_INTERVAL, DOMAIN
from custom_components.eeproperty.models import EePropertyData
from custom_components.eeproperty.sensor import EePropertyBalanceSensor, EePropertyMachineSensor

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Config entry example."""
    client = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = EePropertyDataUpdateCoordinator(hass, config_entry, client)

    await coordinator.async_config_entry_first_refresh()

    entities: list[SensorEntity] = []

    # Create sensor for each machine
    if coordinator.data and coordinator.data.machines:
        for machine in coordinator.data.machines:
            entities.append(
                EePropertyMachineSensor(coordinator, machine.number, machine.type)
            )

    # Create balance sensor
    entities.append(EePropertyBalanceSensor(coordinator))

    async_add_entities(entities)


class EePropertyDataUpdateCoordinator(DataUpdateCoordinator[EePropertyData]):
    """Class to manage fetching eeproperty data."""

    def __init__(
            self,
            hass: HomeAssistant,
            config_entry,
            client: EePropertyApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=config_entry,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            always_update=False
        )
        self.client = client

    async def _async_update_data(self) -> EePropertyData:
        """Update data via library."""
        try:
            machines = await self.client.get_machines()
            user_data = await self.client.get_user_data()

            return EePropertyData(machines=machines, user=user_data)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
