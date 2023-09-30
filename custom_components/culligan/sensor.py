"""Culligan Wrapper."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, final

from ayla_iot_unofficial.device import Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .update_coordinator import CulliganUpdateCoordinator
from .entity import CulliganWaterSoftenerEntity

from .const import ATTRIBUTES, DOMAIN, ICON, LOGGER


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    # async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up the Culligan sensor."""
    LOGGER.debug("Sensor async_setup_entry")

    coordinator: CulliganUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    devices: Iterable[Device] = coordinator.culligan_devices.values()
    device_names = [d.name for d in devices]
    LOGGER.debug(
        "Found %d Culligan device(s): %s",
        len(device_names),
        ", ".join([d.name for d in devices]),
    )

    # Two primary functions ... async_add_devices OR async_add_entities
    LOGGER.debug("sensor calling async_add_entities:")
    sensors = [
        CulliganWaterSoftenerSensor(coordinator, config_entry, device)
        for device in devices
    ]
    async_add_entities(sensors)
    LOGGER.debug("Finished sensor async_add_entities")


class CulliganWaterSoftenerSensor(CulliganWaterSoftenerEntity):
    """Culligan Water Softener Sensor Class"""

    # Sensor should have name, state, icon, device class
    # Sensor is a subclass of softener entity, who's init should have a device)

    @final
    @property
    def state_attributes(self) -> dict[str, Any]:
        """Return state attributes."""
        data: dict[str, Any] = {}

        for prop, attr in ATTRIBUTES.items():
            if (value := getattr(self, prop)) is not None:
                LOGGER.debug("Attributes: setting %s to %s", attr, value)
                data[attr] = value
            else:
                LOGGER.debug("Attributes: %s is None", attr)

        return data

    @property
    def available(self) -> bool:
        """Determine if the sensor is available based on API results."""
        # If the last update was successful...
        return self.coordinator.last_update_success and self.is_online

    @property
    def average_daily_usage(self) -> int | None:
        """Return the avgerage_daily_usage or None"""
        return self.device.get_property_value("average_daily_usage")

    @property
    def capacity_remaining_gal(self) -> int | None:
        """Return the remaining gallon capacity before regen (or None)."""
        return self.device.get_property_value("capacity_remaining_gallons")

    @property
    def current_flow_rate(self) -> int | None:
        """Return the current flow rate (or None)."""
        return self.device.get_property_value("current_flow_rate")

    @property
    def days_salt_remaining(self) -> int | None:
        """Return the estimated number of days of salt remaining (or None)."""
        return self.device.get_property_value("days_salt_remaining")

    @property
    def days_since_last_regen(self) -> int | None:
        """Return the days since last regen (or None)."""
        return self.device.get_property_value("days_since_last_regen")

    @property
    def device_class(self) -> str | None:
        """Return the device class of the sensor"""
        return "water_softener"

    @property
    def error_code(self) -> int | None:
        """Return the last observed error code (or None)."""
        return self.device.get_property_value("error_flags")

    @property
    def error_message(self) -> str | None:
        """Return the last observed error message (or None)."""
        if not self.error_code:
            return None
        return self.device.error_text

    @property
    def icon(self) -> str | None:
        """Return the icon of the sensor."""
        return ICON

    @property
    def is_online(self) -> bool | None:
        """Tell us if the device is online."""
        online = self.coordinator.device_is_online(self.device._device_serial_number)
        return online

    @property
    def last_regen_date(self) -> str | None:
        """Return the last regen date (or None)."""
        return self.device.get_property_value("last_regen_date_time")

    @property
    def manual_salt_level_rem_calc(self) -> int | None:
        """Return the salt level based on manual additions (or None)."""
        return self.device.get_property_value("manual_salt_level_rem_calc")

    @property
    def model(self) -> str | None:
        """Softener model number."""
        if self.device._device_model_number:
            return self.device._device_model_number
        return self.device._oem_model_number

    @property
    def next_regen_on_date(self) -> str | None:
        """Return the last regen date (or None)."""
        return self.device.get_property_value("next_regen_on_date")

    @property
    def operating_mode(self) -> str | None:
        """Operating mode."""
        vacation = self.device.get_property_value("vacation_mode")
        state = ""
        if vacation == 1 or vacation == 255:
            state = "Vacation"
        else:
            bypass = self.device.get_property_value("actual_state_dealer_bypass")
            if bypass == 1 or vacation == 255:
                state = "Bypass"
            else:
                state = "Softening"
        return state

    @property
    def regen_interval_days(self) -> int | None:
        """Return the regen interval days (or None). Maybe this doesn't count for smart softeners"""
        return self.device.get_property_value("regen_interval_days_setting")

    @property
    def regen_tonight_pending(self) -> str | None:
        """Return if there is a regen pending tonight (or None)."""
        return self.device.get_property_value("regen_tonight_pending")

    @property
    def rssi(self) -> int | None:
        """Get the WiFi RSSI."""
        return self.device.get_property_value("rssi")

    @property
    def salt_level_low(self) -> str | None:
        """Return the if the salt level is low warning (or None)."""
        return self.device.get_property_value("sbt_salt_level_low")

    @property
    def state(self) -> str | None:
        """Get the current softener state."""
        # alternative to look into? self.coordinator.data.get("body")
        return self.operating_mode

    @property
    def time_rem_in_position(self) -> str | None:
        """Return the time remaining on a timed bypass (or None)."""
        return self.device.get_property_value("time_rem_in_position")

    @property
    def total_gallons_today(self) -> int | None:
        """Return the total softened gallons today (or None)."""
        return self.device.get_property_value("total_gallons_today")

    @property
    def total_gallons_since_install(self) -> int | None:
        """Return the total gallons since install (or None)."""
        return self.device.get_property_value("total_gallons_since_install")

    @property
    def total_regens_since_install(self) -> int | None:
        """Return the total regens since install (or None)."""
        return self.device.get_property_value("total_regens_since_install")

    @property
    def valve_position(self) -> str | None:
        """Return the valve position (or None)."""
        if self.device.get_property_value("valve_position") == 0:
            return "Open"
        else:
            return "Closed"

    @property
    def water_hardness(self) -> int | None:
        """Return the water hardness in grain per gallon (typically set by the installer) (or None)."""
        return self.device.get_property_value("hardness_in_grains_per_gal")

    async def async_start_vacation_mode(self, **kwargs: Any) -> None:
        """Set the softener to turn on vacation mode"""
        await self.device.async_start_vacation_mode()
        await self.coordinator.async_refresh()

    async def async_stop_vacation_mode(self, **kwargs: Any) -> None:
        """Set the softener to turn off vacation mode"""
        await self.device.async_stop_vacation_mode()
        await self.coordinator.async_refresh()

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
