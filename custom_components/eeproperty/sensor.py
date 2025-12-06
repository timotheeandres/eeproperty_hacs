"""Sensor platform for eeProperty."""
from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import EePropertyApiClient
from .const import (
    ATTR_BALANCE,
    ATTR_COST_PER_CYCLE,
    ATTR_MACHINE_NUMBER,
    ATTR_MACHINE_TYPE,
    ATTR_PRICING,
    ATTR_ROOM,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    STATE_ACTIVATED,
    STATE_DEACTIVATED,
    STATE_ERROR,
    TYPE_DRYER,
    TYPE_WASHER,
    CURRENCY,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up eeProperty sensor based on a config entry."""
    client: EePropertyApiClient = hass.data[DOMAIN][entry.entry_id]

    # Create coordinator for all machines
    coordinator = EePropertyDataUpdateCoordinator(hass, client)

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    entities = []

    # Create sensor for each machine
    if coordinator.data and "machines" in coordinator.data:
        for machine in coordinator.data["machines"]:
            machine_number = machine.get("number")
            machine_type = machine.get("type")
            entities.append(
                EePropertyMachineSensor(coordinator, machine_number, machine_type)
            )

    # Create balance sensor
    entities.append(EePropertyBalanceSensor(coordinator))

    async_add_entities(entities)


class EePropertyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching eeProperty data."""

    def __init__(
            self,
            hass: HomeAssistant,
            client: EePropertyApiClient,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            machines = await self.client.get_machines()
            user_data = await self.client.get_user_data()

            return {
                "machines": machines,
                "user": user_data,
            }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err


class EePropertyMachineSensor(CoordinatorEntity, SensorEntity):
    """Representation of an eeProperty washing machine sensor."""

    def __init__(
            self,
            coordinator: EePropertyDataUpdateCoordinator,
            machine_number: int,
            machine_type: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._machine_number = machine_number
        self._machine_type = machine_type
        self._attr_unique_id = f"{DOMAIN}_machine_{machine_number}"

        # Set name based on type
        type_name = "Washing Machine" if machine_type == TYPE_WASHER else "Dryer" if machine_type == TYPE_DRYER else "Unknown"
        self._attr_name = f"{type_name} {machine_number}"

    def _get_machine_data(self) -> dict[str, Any] | None:
        """Get this machine's data from coordinator."""
        if not self.coordinator.data or "machines" not in self.coordinator.data:
            return None

        for machine in self.coordinator.data["machines"]:
            if machine.get("number") == self._machine_number:
                return machine
        return None

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        machine = self._get_machine_data()
        if not machine:
            return None

        state = machine.get("state")
        # Map states to friendly names
        if state == STATE_DEACTIVATED:
            return "Available"
        elif state == STATE_ACTIVATED:
            return "Occupied"
        elif state == STATE_ERROR:
            return "Unavailable"
        return state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        machine = self._get_machine_data()
        if not machine:
            return {}

        return {
            ATTR_MACHINE_TYPE: machine.get("type"),
            ATTR_MACHINE_NUMBER: machine.get("number"),
            ATTR_ROOM: machine.get("room"),
            ATTR_PRICING: machine.get("pricing"),
            ATTR_COST_PER_CYCLE: machine.get("costPerCycle"),
        }

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        machine = self._get_machine_data()
        if not machine:
            return "mdi:washing-machine-off"

        state = machine.get("state")
        machine_type = machine.get("type")

        # Choose icon based on type and state
        if machine_type == TYPE_DRYER:
            if state == STATE_ACTIVATED:
                return "mdi:tumble-dryer"
            elif state == STATE_DEACTIVATED:
                return "mdi:tumble-dryer-off"
            else:
                return "mdi:tumble-dryer-alert"
        elif machine_type == TYPE_WASHER:  # WASHER
            if state == STATE_ACTIVATED:
                return "mdi:washing-machine"
            elif state == STATE_DEACTIVATED:
                return "mdi:washing-machine-off"
            else:
                return "mdi:washing-machine-alert"
        else:
            return "mdi:help-circle"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._get_machine_data() is not None


class EePropertyBalanceSensor(CoordinatorEntity, SensorEntity):
    """Sensor for user account balance."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = CURRENCY

    def __init__(self, coordinator: EePropertyDataUpdateCoordinator) -> None:
        """Initialize the balance sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_balance"
        self._attr_name = "eeProperty Balance"

    @property
    def native_value(self) -> int | None:
        """Return the balance."""
        if not self.coordinator.data or "user" not in self.coordinator.data:
            return None

        user = self.coordinator.data["user"]
        if user:
            return user.get("balance")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if not self.coordinator.data or "user" not in self.coordinator.data:
            return {}

        user = self.coordinator.data["user"]
        if not user:
            return {}

        return {
            "user_number": user.get("number"),
            "user_name": f"{user.get('firstName')} {user.get('lastName')}",
            "unlimited_balance": user.get("unlimitedBalance"),
        }

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:wallet"
