"""Culligan Sensor Entities."""
from __future__ import annotations

from .const import DOMAIN, LOGGER, PROPERTY_VALUE_MAP
from .entity import CulliganBaseEntity
from .update_coordinator import CulliganUpdateCoordinator

from ayla_iot_unofficial.device import Device
from collections.abc import Iterable
from culligan.culliganiot_device import CulliganIoTDevice

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    FORMAT_DATETIME,
    PERCENTAGE,
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

    # coordinator: CulliganUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: CulliganUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    devices: Iterable[Device] | Iterable[CulliganIoTDevice] = coordinator.culligan_devices.values()
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
            SensorDeviceClass.WATER,
            SensorStateClass.TOTAL_INCREASING,
        ),
        (
            # average daily usage sensor
            # doesn't match app and not sure why ... longer period?
            "average_daily_usage",
            "average daily water usage",
            UnitOfVolume.GALLONS,
            "mdi:cup-water",
            SensorDeviceClass.WATER,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # remaining capacity before regen in gallons
            "capacity_remaining_gallons",
            "capacity remaining before regeneration",
            UnitOfVolume.GALLONS,
            "mdi:water-minus",
            SensorDeviceClass.VOLUME_STORAGE,
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
            # requested by user
            "days_salt_remaining",
            "salt remaining",
            UnitOfTime.DAYS,
            "mdi:calendar-clock",
            None,
            SensorStateClass.MEASUREMENT,
        ),
        (
            # manual salt level as displayed in the app
            "manual_salt_level_rem_calc",
            "salt remaining",
            PERCENTAGE,
            "mdi:calendar-clock",
            None,
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
            SensorDeviceClass.WATER,
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

    # add daily / hourly usages
    for key in PROPERTY_VALUE_MAP.keys():
        if key[:-1] == "daily_usage_day_":
            day = key[-1]
            softener_sensors += [(
                key,
                f"daily usage today - {day}d",
                UnitOfVolume.GALLONS,
                "mdi:cup-water",
                SensorDeviceClass.WATER,
                SensorStateClass.MEASUREMENT,
            )]
        elif key[:3] == "avg" and key[-3:] in ["sun","mon","tue","wed","thr","fri","sat"]:
            day = key[-3:]
            softener_sensors += [(
                key,
                f"average usage {day}",
                UnitOfVolume.GALLONS,
                "mdi:cup-water",
                SensorDeviceClass.WATER,
                SensorStateClass.MEASUREMENT,
            )]
        elif key[:17] == "hourly_usage_hour":
            hour = key.split("_")[3]
            softener_sensors += [(
                key,
                f"hourly usage now - {hour}h",
                UnitOfVolume.GALLONS,
                "mdi:cup-water",
                SensorDeviceClass.WATER,
                SensorStateClass.MEASUREMENT,
            )]
        else:
            pass

    # Method two ... create individual sensors from a map of defined sensor attributes
    for device in devices:
        LOGGER.debug("Working on adding sensors device: %s", device._device_serial_number)
        sensors = []
        for sensor in softener_sensors:
            LOGGER.debug("sensor calling async_add: %s", sensor[0])
            sensors += [
                SoftenerSensor(
                    coordinator,
                    # config_entry,
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
class SoftenerSensor(CulliganBaseEntity, SensorEntity):
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

    # should_poll should be provided by the UpdateCoordinator

    def __init__(
        self,
        coordinator: CulliganUpdateCoordinator,
        # config_entry: ConfigEntry,
        device: Device | CulliganIoTDevice,
        sensor_id: str,
        description: str,
        unit_of_measurement: str | None,
        icon: str,
        device_class: SensorDeviceClass,
        state_class: SensorStateClass | None,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, device)

        LOGGER.debug(f"Init for {description}")

        self._attr_description                      = description
        self._attr_device_class: SensorDeviceClass  = device_class
        self._attr_icon                             = icon
        self._attr_native_unit_of_measurement       = unit_of_measurement
        self._attr_state_class:  SensorStateClass   = state_class

        self._attr_unique_id                        = device._device_serial_number + "_" + sensor_id
        self.entity_id                              = generate_entity_id("sensor.{}", self._attr_unique_id, None, coordinator.hass)

        if self.io_culligan:
            self._attr_sensor_id                    = PROPERTY_VALUE_MAP[sensor_id]   # this is the mapped Culligan sensor data value
        else:
            self._attr_sensor_id                    = sensor_id             # this is the ayla property map key to get sensor data value

    @property
    def sensor_id(self):
        """Return the property key needed to get values"""
        return self._attr_sensor_id

    @property
    def state(self) -> int | None:
        """Using devices stored property map, get the value from the dictionary"""
        SENSOR_ID             = self.sensor_id
        if self.io_culligan:
            BYPASS_PROPERTY   = PROPERTY_VALUE_MAP["actual_state_dealer_bypass"]
            VAC_MODE_PROPERTY = PROPERTY_VALUE_MAP["vacation_mode"]
            LOGGER.debug(f"self is CULLIGAN")
        else:
            BYPASS_PROPERTY   = "actual_state_dealer_bypass"
            VAC_MODE_PROPERTY = "vacation_mode"
            LOGGER.debug(f"self is AYLA")

        if SENSOR_ID in ["status","unit_status_1","unit_status_tank_1"]:
            vacation = self.device.get_property_value(VAC_MODE_PROPERTY)
            bypass = self.device.get_property_value(BYPASS_PROPERTY)
            LOGGER.debug(f"For {SENSOR_ID} got: vac: {vacation} and bypass: {bypass} else: softening")
            if vacation == 1 or vacation == 255:
                state = "Vacation"
                self._attr_icon = "mdi:airplane"
            elif bypass == 1:
                state = "Bypass"
                self._attr_icon = "mdi:water-off"
            else:
                state = "Softening"
                self._attr_icon = "mdi:water"
            return state
        elif SENSOR_ID == "current_flow_rate":
            # need to divide by 10 to get current flow rate
            LOGGER.debug(f"Attempting to get property value for: {SENSOR_ID} of len {len(SENSOR_ID)}")
            flow_rate = self.device.get_property_value(SENSOR_ID)
            LOGGER.debug(f"For {SENSOR_ID} Got {flow_rate}")
            if flow_rate:
                flow_rate = int(flow_rate)
                if flow_rate == 0:
                    return float(flow_rate)
                else:
                    return float(flow_rate / 10)
            else:
                # LOGGER.debug("UNABLE TO GET FLOW_RATE")
                return 0
        else:
            LOGGER.debug(f"For {SENSOR_ID} got: {self.device.get_property_value(SENSOR_ID)}")
            return self.device.get_property_value(SENSOR_ID)

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
    def state_class(self) -> SensorStateClass | None:
        """Define the state class"""
        return self._attr_state_class

    @property
    def name(self) -> str | None:
        """Define name as description. This shows in the Sensor Name column of entities."""
        return f"{self._attr_description}"
    
    @property
    def unique_id(self) -> str | None:
        """Suggest the unique id of the entity. User never sees these."""
        return f"{self._attr_unique_id}"