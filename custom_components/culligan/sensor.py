"""Culligan Sensor Entities."""
from __future__ import annotations

from .const import DOMAIN, LOGGER
from .entity import CulliganBaseEntity
from .update_coordinator import CulliganUpdateCoordinator

from ayla_iot_unofficial.device import Device
from collections.abc import Iterable

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    FORMAT_DATETIME,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfMass,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import generate_entity_id


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
            # generic softener status
            "status",
            "status",
            None,
            "mdi:water",
            None,
            None,
        ),
        (
            # total gallons today
            "total_gallons_today",
            "total gallons today",
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
            UnitOfVolume.GALLONS,
            "mdi:cup-water",
            SensorDeviceClass.VOLUME,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # remaining capacity before regen in gallons
            "capacity_remaining_gallons",
            "capacity remaining before regeneration",
            UnitOfVolume.GALLONS,
            "mdi:water-minus",
            SensorDeviceClass.VOLUME,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # current flow rate
            "current_flow_rate",
            "current flow rate",
            "gpm",
            "mdi:waves",
            SensorDeviceClass.WATER,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # manual salt level as displayed in the app
            "manual_salt_level_rem_calc",
            "manual days of salt remaining",
            UnitOfTime.DAYS,
            "mdi:calendar-clock",
            SensorDeviceClass.DATE,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # Salt dosage in lbs (storage size)
            "salt_dosage_in_lbs",
            "total salt capacity",
            UnitOfMass.POUNDS,
            "mdi:shaker-outline",
            SensorDeviceClass.WEIGHT,
            SensorStateClass.TOTAL,
        ),
        (
            # days since last regeneration
            "days_since_last_regen",
            "days since last regeneration",
            UnitOfTime.DAYS,
            "mdi:calendar-refresh",
            SensorDeviceClass.DATE,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # exact date of last regeneration
            "last_regen_date_time",
            "last regeneration date",
            FORMAT_DATETIME,
            "mdi:calendar-check",
            SensorDeviceClass.TIMESTAMP,
            None,
        ),
        (
            # date of next regen
            "next_regen_on_date",
            "next regeneration date",
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
            UnitOfTime.DAYS,
            "mdi:calendar-refresh",
            None,  # SensorDeviceClass.TIMESTAMP,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # smart 'aqua sensor' Zmin
            "aqua_sensor_Zmin",
            "aqua sensor threshold",
            "μS/cm",  # micro? Siemens per meter (conductivity)
            "mdi:water-alert",
            None,
            SensorStateClass.TOTAL,
        ),
        (
            # smart 'aqua sensor' Zcurrent
            "aqua_sensor_Zratio_current",
            "aqua sensor",
            "μS/cm",  # micro? Siemens per meter (conductivity)
            "mdi:water-opacity",
            None,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # average number of days between regens
            "avg_no_of_days_btwn_reg",
            "average days between regenerations",
            UnitOfTime.DAYS,
            "mdi:calendar",
            None,  # SensorDeviceClass.TIMESTAMP,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # hardness programmed in grains
            "hardness_in_grains_per_gal",
            "programmed water hardness",
            "gpg",
            "mdi:water-percent",
            None,
            SensorStateClass.TOTAL,
        ),
        (
            # Wifi strength
            "rssi",
            "WiFi strength",
            SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
            "mdi:wifi-arrow-up-down",
            SensorDeviceClass.SIGNAL_STRENGTH,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # time remaining in valve position
            "time_rem_in_position",
            "valve position time remaining",
            None,  # FORMAT_DATETIME,
            "mdi:clock-end",
            None,  # SensorDeviceClass.TIMESTAMP,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # Total gallons softened since install
            "total_gallons_since_install",
            "total gallons softened since install",
            UnitOfVolume.GALLONS,
            "mdi:cup-water",
            SensorDeviceClass.VOLUME_STORAGE,
            SensorStateClass.TOTAL_INCREASING,
        ),
        (
            # Total regenerations since install
            "total_regens_since_install",
            "total regenerations since install",
            None,
            "mdi:refresh-circle",
            None,
            SensorStateClass.TOTAL_INCREASING,
        ),
        (
            # Error codes
            "error_flags",
            "error codes",
            None,
            "mdi:alert-circle",
            None,
            None,
        )
        # (
        #     # id
        #     # description
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
                    sensor[0],  # id
                    sensor[1],  # description
                    sensor[2],  # unit of measurement
                    sensor[3],  # icon
                    sensor[4],  # device class
                    sensor[5],  # state class
                )
            ]

        # add devices will add a new device (with area selection)
        if len(sensors) > 0:
            async_add_devices(sensors)

        LOGGER.debug("Finished sensor async_add_devices")

#class SoftenerSensor(CulliganWaterSoftenerEntity):
class SoftenerSensor(CulliganBaseEntity):
    """Generic sensor template for water softener"""

    # in entity_platform, deciding entity_id:
    #   if entity_id is defined, make that the suggested_entity_id
    #   else if device and has_entity_name
    #       if use_device_name, then just use the devices name (e.g. all sensors named Softener)
    #       else, use device name + suggested_object_id
    #   else use suggested_object_id
    #   suggested_object_id is config_entry id or device default name ... generates numbers if name is the same

    # default ... sensor name is the property name alone (similar to specifying has_entity_name = True and use_device_name = False)
    has_entity_name = True  # sensor name is Softener property name ... because device exists by default
    use_device_name = False # sensor name is property name ... because device name is turned off by this flag
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: CulliganUpdateCoordinator,
        config_entry: ConfigEntry,
        device: Device,
        sensor_id: str,
        description: str,
        unit_of_measurement: str | None,
        icon: str,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(device)

        self._attr_description                  = description
        self._attr_device_class                 = device_class
        self._attr_icon                         = icon
        self._attr_native_unit_of_measurement   = unit_of_measurement
        self._attr_sensor_id                    = sensor_id             # this is the ayla property map key to get sensor data value
        self._attr_state_class                  = state_class

        self._attr_unique_id                    = device._device_serial_number + "_" + sensor_id
        self.entity_id                          = generate_entity_id("sensor.{}", self._attr_unique_id, None, coordinator.hass)

    @property
    def state(self) -> int | None:
        """Using devices stored property map, get the value from the dictionary"""

        if self._attr_sensor_id == "status":
            vacation = self.device.get_property_value("vacation_mode")
            bypass = self.device.get_property_value("actual_state_dealer_bypass")
            if vacation == 1 or vacation == 255:
                state = "Vacation"
                self._attr_icon = "mdi:plain"
            elif bypass == 1:
                state = "Bypass"
                self._attr_icon = "mdi:water-off"
            else:
                state = "Softening"
                self._attr_icon = "mdi:water"
            return state
        else:
            return self.device.get_property_value(self._attr_sensor_id)

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
        """Define name as description. This shows in the Sensor Name column of entities."""
        return f"{self._attr_description}"
    
    @property
    def unique_id(self) -> str | None:
        """Suggest the unique id of the entity. User never sees these."""
        return f"{self._attr_unique_id}"
