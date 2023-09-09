"""Culligan Wrapper."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any
import voluptuous as vol

from ayla_iot_unofficial.device import Device, Softener

from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfVolume,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER, AYLA_REGION_DEFAULT, AYLA_REGION_OPTIONS
from .update_coordinator import CulliganUpdateCoordinator

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_REGION,
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Culligan coordinator."""
    coordinator: CulliganUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    devices: Iterable[Softener] = coordinator.culligan_devices.values()
    device_names = [d.name for d in devices]
    LOGGER.debug(
        "Found %d Culligan device(s): %s",
        len(device_names),
        ", ".join([d.name for d in devices]),
    )
    async_add_entities([CulliganWaterSoftenerEntity(d, coordinator) for d in devices])


class CulliganWaterSoftenerEntity(
    CoordinatorEntity[CulliganUpdateCoordinator], SensorEntity
):
    """
    Softener Entity
    """

    def __init__(
        self, softener: Softener, coordinator: CulliganUpdateCoordinator
    ) -> None:
        """Create a new SensorEntity"""
        super().__init__(coordinator)
        self.softener = softener
        self._attr_name = softener.name
        self._attr_unique_id = softener.serial_number
        self._serial_number = softener.serial_number

    def not_a_function(self, **kwargs: Any) -> None:
        """Placeholder. Not yet implemented."""
        raise NotImplementedError()

    def send_command(
        self,
        command: str,
        params: dict[str, Any] | list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Send a command to the softener. Not yet implemented."""
        raise NotImplementedError()

    @property
    def is_online(self) -> bool:
        """Tell us if the device is online."""
        return self.coordinator.device_is_online(self._serial_number)

    @property
    def model(self) -> str:
        """Vacuum model number."""
        if self.softener.model_number:
            return self.softener.model_number
        return self.softener.oem_model_number

    @property
    def device_info(self) -> DeviceInfo:
        """Device info dictionary."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._serial_number)},
            manufacturer="Culligan",
            model=self.model,
            name=self.name,
            sw_version=self.softener.get_property_value(
                "wifi_mcu_version"
            ),  # should be device SW Version not wifi_mcu_version
        )

    @property
    def error_code(self) -> int | None:
        """Return the last observed error code (or None)."""
        return self.softener.get_property_value("error_flags")

    @property
    def error_message(self) -> str | None:
        """Return the last observed error message (or None)."""
        if not self.error_code:
            return None
        return self.softener.error_text

    @property
    def operating_mode(self) -> str | None:
        """Operating mode."""
        vacation = self.softener.get_property_value("vacation_mode")
        if vacation == 255:
            return "Vacation"
        else:
            bypass = self.softener.get_property_value("actual_state_dealer_bypass")
            if bypass == 255:
                return "Bypass"
            else:
                return "Softening"

    @property
    def state(self) -> str | None:
        """
        Get the current softener state.
        """
        return self.operating_mode

    @property
    def available(self) -> bool:
        """Determine if the sensor is available based on API results."""
        # If the last update was successful...
        return self.coordinator.last_update_success and self.is_online

    @property
    def avg_daily_usage(self) -> int | None:
        """Return the avg_daily_usage or None"""
        return self.softener.get_property_value("avg_daily_usage")

    @property
    def current_flow_rate(self) -> int | None:
        """Return the current flow rate (or None)."""
        return self.softener.get_property_value("current_flow_rate")

    @property
    def water_hardness(self) -> int | None:
        """Return the water hardness in grain per gallon (typically set by the installer) (or None)."""
        return self.softener.get_property_value("hardness_in_grans_per_gal")

    @property
    def days_since_last_regen(self) -> int | None:
        """Return the days since last regen (or None)."""
        return self.softener.get_property_value("days_since_last_regen")

    @property
    def days_salt_remaining(self) -> int | None:
        """Return the estimated number of days of salt remaining (or None)."""
        return self.softener.get_property_value("days_salt_remaining")

    @property
    def manual_salt_level_rem_calc(self) -> int | None:
        """Return the salt level based on manual additions (or None)."""
        return self.softener.get_property_value("manual_salt_level_rem_calc")

    @property
    def last_regen_date(self) -> None:
        """Return the last regen date (or None)."""
        return self.softener.get_property_value("last_regen_date_time")

    @property
    def next_regen_on_date(self) -> None:
        """Return the last regen date (or None)."""
        return self.softener.get_property_value("next_regen_on_date")

    @property
    def regen_interval_days(self) -> int | None:
        """Return the regen interval days (or None). Maybe this doesn't count for smart softeners"""
        return self.softener.get_property_value("regen_interval_days_setting")

    @property
    def regen_tonight_pending(self) -> None:
        """Return if there is a regen pending tonight (or None)."""
        return self.softener.get_property_value("regen_tonight_pending")

    @property
    def salt_level_low(self) -> None:
        """Return the if the salt level is low warning (or None)."""
        return self.softener.get_property_value("sbt_salt_level_low")

    @property
    def time_rem_in_position(self) -> None:
        """Return the time remaining on a timed bypass (or None)."""
        return self.softener.get_property_value("time_rem_in_position")

    @property
    def valve_position(self) -> str | None:
        """Return the valve position (or None)."""
        if self.softener.get_property_value("valve_position") == 255:
            return "Closed"
        else:
            return "Open"

    @property
    def total_gallons_today(self) -> int | None:
        """Return the total softened gallons today (or None)."""
        return self.softener.get_property_value("total_gallons_today")

    @property
    def total_gallons_since_install(self) -> int | None:
        """Return the total gallons since install (or None)."""
        return self.softener.get_property_value("total_gallons_since_install")

    @property
    def total_regens_since_install(self) -> int | None:
        """Return the total regens since install (or None)."""
        return self.softener.get_property_value("total_regens_since_install")

    @property
    def capacity_remaining_gallons(self) -> int | None:
        """Return the remaining gallon capacity before regen (or None)."""
        return self.softener.get_property_value("capacity_remaining_gallons")

    async def async_start_vacation_mode(self, **kwargs: Any) -> None:
        """Set the softener to turn on vacation mode"""
        await self.softener.async_start_vacation_mode()
        await self.coordinator.async_refresh()

    async def async_stop_vacation_mode(self, **kwargs: Any) -> None:
        """Set the softener to turn off vacation mode"""
        await self.softener.async_stop_vacation_mode()
        await self.coordinator.async_refresh()

    @property
    def rssi(self) -> int | None:
        """Get the WiFi RSSI."""
        return self.softener.get_property_value("rssi")
