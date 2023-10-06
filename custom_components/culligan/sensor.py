"""Culligan Sensor Entities."""
from __future__ import annotations

from .const import DOMAIN, LOGGER
from .entity import CulliganWaterSoftenerEntity
from .update_coordinator import CulliganUpdateCoordinator

from ayla_iot_unofficial.device import Device
from collections.abc import Iterable

from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    FORMAT_DATETIME,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfMass,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
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

    softener_sensors = [
        (
            # total gallons today
            "total_gallons_today",
            "total gallons today",
            "total_gallons_today",
            UnitOfVolume.GALLONS,
            "mdi:water-circle",
            SensorDeviceClass.VOLUME_STORAGE,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # average daily usage sensor
            # doesn't match app and not sure why ... longer period?
            "average_daily_usage",
            "average daily water usage",
            "average_daily_usage",
            UnitOfVolume.GALLONS,
            "mdi:cup-water",
            SensorDeviceClass.VOLUME,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # remaining capacity before regen in gallons
            "capacity_remaining_gallons",
            "capacity remaining before regeneration",
            "capacity_remaining_gallons",
            UnitOfVolume.GALLONS,
            "mdi:water-minus",
            SensorDeviceClass.VOLUME,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # current flow rate
            "current_flow_rate",
            "current flow rate",
            "current_flow_rate",
            "gpm",
            "mdi:waves",
            SensorDeviceClass.WATER,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # manual salt level as displayed in the app
            "manual_salt_level_rem_calc",
            "manual days of salt remaining",
            "manual_salt_level_rem_calc",
            UnitOfTime.DAYS,
            "mdi:calendar-clock",
            SensorDeviceClass.DATE,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # Salt dosage in lbs (storage size)
            "salt_dosage_in_lbs",
            "total salt capacity",
            "salt_dosage_in_lbs",
            UnitOfMass.POUNDS,
            "mdi:shaker-outline",
            SensorDeviceClass.WEIGHT,
            SensorStateClass.TOTAL,
        ),
        (
            # days since last regeneration
            "days_since_last_regen",
            "days since last regeneration",
            "days_since_last_regen",
            UnitOfTime.DAYS,
            "mdi:calendar-refresh",
            SensorDeviceClass.DATE,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # exact date of last regeneration
            "last_regen_date_time",
            "last regeneration date",
            "last_regen_date_time",
            FORMAT_DATETIME,
            "mdi:calendar-check",
            SensorDeviceClass.TIMESTAMP,
            None,
        ),
        (
            # date of next regen
            "next_regen_on_date",
            "next regeneration date",
            "next_regen_on_date",
            None,  # FORMAT_DATETIME,
            "mdi:calendar-arrow-right",
            SensorDeviceClass.DATE,
            None,
        ),
        (
            # days between regenerations
            # not applicable if smart sensing
            "regen_interval_days_setting",
            "programmed days between regenerations",
            "regen_interval_days_setting",
            UnitOfTime.DAYS,
            "mdi:calendar-refresh",
            None,  # SensorDeviceClass.TIMESTAMP,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # smart 'aqua sensor' Zmin
            "aqua_sensor_Zmin",
            "Aqua Sensor Threshold",
            "aqua_sensor_Zmin",
            "μS/cm",  # micro? Siemens per meter (conductivity)
            "mdi:water-alert",
            None,
            SensorStateClass.TOTAL,
        ),
        (
            # smart 'aqua sensor' Zcurrent
            "aqua_sensor_Zratio_current",
            "Aqua Sensor",
            "aqua_sensor_Zratio_current",
            "μS/cm",  # micro? Siemens per meter (conductivity)
            "mdi:water-opacity",
            None,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # average number of days between regens
            "avg_no_of_days_btwn_reg",
            "average days between regenerations",
            "avg_no_of_days_btwn_reg",
            UnitOfTime.DAYS,
            "mdi:calendar",
            None,  # SensorDeviceClass.TIMESTAMP,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # hardness programmed in grains
            "hardness_in_grains_per_gal",
            "programmed water hardness",
            "hardness_in_grains_per_gal",
            "gpg",
            "mdi:water-percent",
            None,
            SensorStateClass.TOTAL,
        ),
        (
            # Wifi strength
            "rssi",
            "WiFi strength",
            "rssi",
            SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            "mdi:wifi-arrow-up-down",
            SensorDeviceClass.SIGNAL_STRENGTH,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # time remaining in valve position
            "time_rem_in_position",
            "valve position time remaining",
            "time_rem_in_position",
            None,  # FORMAT_DATETIME,
            "mdi:clock-end",
            None,  # SensorDeviceClass.TIMESTAMP,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # Total gallons softened since install
            "total_gallons_since_install",
            "total gallons softened since install",
            "total_gallons_since_install",
            UnitOfVolume.GALLONS,
            "mdi:cup-water",
            SensorDeviceClass.VOLUME_STORAGE,
            SensorStateClass.TOTAL_INCREASING,
        ),
        (
            # Total regenerations since install
            "total_regens_since_install",
            "total regenerations since install",
            "total_regens_since_install",
            None,
            "mdi:refresh-circle",
            None,
            SensorStateClass.TOTAL_INCREASING,
        ),
        (
            # Error codes
            "error_flags",
            "Error codes",
            "error_flags",
            None,
            "mdi:alert-circle",
            None,
            None,
        )
        # (
        #     # id
        #     # description
        #     # key
        #     # unit (of measurement)
        #     # icon
        #     # device_class
        #     # state_class
        # ),
    ]

    # Method two ... create individual sensors from a map of defined sensor attributes
    for device in devices:
        LOGGER.debug("Working on device: %s", device._device_serial_number)
        sensors = []
        for sensor in softener_sensors:
            LOGGER.debug("sensor calling async_add: %s", sensor[0])
            sensors += [
                SoftenerSensor(
                    coordinator,
                    config_entry,
                    device,
                    sensor[0],
                    sensor[1],
                    sensor[2],
                    sensor[3],
                    sensor[4],
                    sensor[5],
                    sensor[6],
                )
            ]

        # add devices will add a new device (with area selection)
        async_add_devices(sensors)

        # add entities also did the same, but the entity names were correct
        # async_add_entities(sensors)
        LOGGER.debug("Finished sensor async_add_devices")


class SoftenerSensor(CulliganWaterSoftenerEntity):
    """Generic sensor template for water softener"""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: CulliganUpdateCoordinator,
        config_entry: ConfigEntry,
        device: Device,
        sensor_id: str,
        description: str,
        key: str,
        unit_of_measurement: str | None,
        icon: str,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass | None,
    ) -> None:
        """Initialize the sensor."""
        # Entity defines properties: info, name, state
        super().__init__(coordinator, config_entry, device)

        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit_of_measurement
        self._attr_state_class = state_class
        self._attr_sensor_id = sensor_id
        self._attr_unique_id = device._device_serial_number + "_" + sensor_id

        self._attr_description = description
        self._attr_sensor_key = key
        self._attr_icon = icon

    @property
    def state(self) -> int | None:
        """Using devices stored property map, get the value from the dictionary"""
        return self.device.get_property_value(self._attr_sensor_key)

    @property
    def unit_of_measurement(self) -> str | None:
        """Define unit of measurement"""
        return self._attr_native_unit_of_measurement

    @property
    def icon(self) -> str | None:
        """Define the icon"""
        return self._attr_icon

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Define the device class"""
        return self._attr_device_class

    @property
    def name(self) -> str | None:
        """Define name as description"""
        return f"{self._attr_description}"

    @property
    def id(self) -> str | None:
        """Define name as the sensors ID"""
        return f"{self._attr_sensor_id}"

    @property
    def unique_id(self) -> str | None:
        """Define unique ID as DSN + ID"""
        return f"{self._attr_unique_id}"
