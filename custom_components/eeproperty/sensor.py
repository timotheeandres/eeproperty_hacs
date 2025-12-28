"""Sensor platform for eeproperty."""
import logging
import typing
from typing import Literal

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EePropertyApiClient
from .const import (ATTR_COST_PER_CYCLE, ATTR_MACHINE_NUMBER, ATTR_MACHINE_TYPE, ATTR_PRICING, ATTR_ROOM,
                    ATTR_UNLIMITED_BALANCE, CURRENCY, DOMAIN)
from .coordinator import EePropertyDataUpdateCoordinator
from .models import Machine, MachineType, User

_LOGGER = logging.getLogger(__name__)

MachineOption = Literal["available", "occupied", "unavailable", "used"]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    client: EePropertyApiClient = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = EePropertyDataUpdateCoordinator(hass, config_entry, client)

    await coordinator.async_config_entry_first_refresh()

    entities: list[SensorEntity] = [EePropertyBalanceSensor(coordinator, client.user_label)]

    for machine in coordinator.data.machines:
        entities.append(
            EePropertyMachineSensor(coordinator, client.user_label, machine.number, machine.type)
        )

    async_add_entities(entities)


class EePropertyMachineSensor(CoordinatorEntity[EePropertyDataUpdateCoordinator], SensorEntity):
    """Representation of an eeproperty washing machine sensor."""

    def __init__(
            self,
            coordinator: 'EePropertyDataUpdateCoordinator',
            user_label: str,
            machine_number: int,
            machine_type: MachineType,
    ) -> None:
        super().__init__(coordinator)
        self._machine_number = machine_number
        self._machine_type = machine_type
        self._user_label = user_label

        sensor_id = user_label.replace(" ", "_")
        self._attr_unique_id = f"{DOMAIN}_{sensor_id}_machine_{machine_number}"

        self._attr_translation_key = "washer_n" if self._machine_type == "WASHER" else "dryer_n"
        self._attr_translation_placeholders = {"machine_number": str(self._machine_number)}

    @property
    def options(self) -> list[str] | None:
        return list(typing.get_args(MachineOption))

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.ENUM

    @property
    def native_value(self) -> MachineOption | None:
        if (machine := self._machine_data) is not None:
            match machine.state:
                case "DEACTIVATED":
                    return "available"
                case "ACTIVATED" if machine.user_label == self._user_label:
                    return "used"
                case "ACTIVATED":
                    return "occupied"
                case "ERROR":
                    return "unavailable"

        return None

    @property
    def extra_state_attributes(self) -> dict[str, str | int | None]:
        if (machine := self._machine_data) is not None:
            return {
                ATTR_MACHINE_TYPE: machine.type,
                ATTR_MACHINE_NUMBER: machine.number,
                ATTR_ROOM: machine.room,
                ATTR_PRICING: machine.pricing,
                ATTR_COST_PER_CYCLE: machine.cost_per_cycle,
            }

        return {}

    @property
    def available(self) -> bool:
        return self._machine_data is not None

    @property
    def _machine_data(self) -> Machine | None:
        for machine in self.coordinator.get_machines_data():
            if machine.type == self._machine_type and machine.number == self._machine_number:
                return machine

        return None


class EePropertyBalanceSensor(CoordinatorEntity[EePropertyDataUpdateCoordinator], SensorEntity):
    """Sensor for user account balance."""

    def __init__(self, coordinator: EePropertyDataUpdateCoordinator, user_label: str) -> None:
        super().__init__(coordinator)
        sensor_id = user_label.replace(" ", "_")
        self._attr_unique_id = f"{DOMAIN}_{sensor_id}_balance"
        self._attr_has_entity_name = True

        self._attr_translation_key = "balance"

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.MONETARY

    @property
    def native_value(self) -> int | None:
        """Return the balance."""
        if (user := self._user_data) is not None:
            return user.balance

        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        return CURRENCY

    @property
    def extra_state_attributes(self) -> dict[str, str | bool]:
        if (user := self._user_data) is not None:
            return {
                ATTR_UNLIMITED_BALANCE: user.unlimited_balance,
            }

        return {}

    @property
    def _user_data(self) -> User | None:
        if self.coordinator.data and self.coordinator.data.user:
            return self.coordinator.data.user

        return None
