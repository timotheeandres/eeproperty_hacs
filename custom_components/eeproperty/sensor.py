"""Sensor platform for eeproperty."""
import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

from .const import (ATTR_COST_PER_CYCLE, ATTR_MACHINE_NUMBER, ATTR_MACHINE_TYPE, ATTR_PRICING, ATTR_ROOM, CURRENCY,
                    DOMAIN)
from .models import Machine, MachineType

if TYPE_CHECKING:
    from .coordinator import EePropertyDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    pass


class EePropertyMachineSensor(CoordinatorEntity['EePropertyDataUpdateCoordinator'], SensorEntity):
    """Representation of an eeproperty washing machine sensor."""

    def __init__(
            self,
            coordinator: 'EePropertyDataUpdateCoordinator',
            machine_number: int,
            machine_type: MachineType,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._machine_number = machine_number
        self._machine_type = machine_type
        self._attr_unique_id = f"{DOMAIN}_machine_{machine_number}"

        # Set name based on type
        type_name = "Washing Machine" if machine_type == "WASHER" else "Dryer"
        self._attr_name = f"{type_name} {machine_number}"

    def _get_machine_data(self) -> Machine | None:
        """Get this machine's data from coordinator."""
        if not self.coordinator.data or not self.coordinator.data.machines:
            return None

        for machine in self.coordinator.data.machines:
            if machine.number == self._machine_number:
                return machine
        return None

    @property
    def device_info(self) -> DeviceInfo | None:
        return DeviceInfo(identifiers={(DOMAIN, self.unique_id)}, name=self.name)

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        machine = self._get_machine_data()
        if not machine:
            return None

        return machine.friendly_state

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        """Return the state attributes."""
        machine = self._get_machine_data()
        if not machine:
            return {}

        return {
            ATTR_MACHINE_TYPE: machine.type,
            ATTR_MACHINE_NUMBER: machine.number,
            ATTR_ROOM: machine.room,
            ATTR_PRICING: machine.pricing,
            ATTR_COST_PER_CYCLE: machine.cost_per_cycle,
        }

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        machine = self._get_machine_data()
        if not machine:
            return "mdi:washing-machine-off"

        # Choose icon based on type and state
        if machine.type == "DRYER":
            if machine.state == "DEACTIVATED":
                return "mdi:tumble-dryer"
            elif machine.state == "ACTIVATED":
                return "mdi:tumble-dryer-off"
            else:
                return "mdi:tumble-dryer-alert"
        else:  # WASHER
            if machine.state == "DEACTIVATED":
                return "mdi:washing-machine"
            elif machine.state == "ACTIVATED":
                return "mdi:washing-machine-off"
            else:
                return "mdi:washing-machine-alert"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._get_machine_data() is not None


class EePropertyBalanceSensor(CoordinatorEntity['EePropertyDataUpdateCoordinator'], SensorEntity):
    """Sensor for user account balance."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_native_unit_of_measurement = CURRENCY

    def __init__(self, coordinator: 'EePropertyDataUpdateCoordinator') -> None:
        """Initialize the balance sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_balance"
        self._attr_name = "Balance"

    @property
    def device_info(self) -> DeviceInfo | None:
        return DeviceInfo(identifiers={(DOMAIN, self.unique_id)}, name=self.name)

    @property
    def native_value(self) -> int | None:
        """Return the balance."""
        if not self.coordinator.data or not self.coordinator.data.user:
            return None

        return self.coordinator.data.user.balance

    @property
    def extra_state_attributes(self) -> dict[str, str | bool]:
        """Return the state attributes."""
        if not self.coordinator.data or not self.coordinator.data.user:
            return {}

        user = self.coordinator.data.user

        return {
            "user_number": user.number,
            "user_name": user.full_name,
            "unlimited_balance": user.unlimited_balance,
        }

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:wallet"
