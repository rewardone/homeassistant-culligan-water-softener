"""Switch representing the shutoff valve for the Flo by Moen integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
# from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import generate_entity_id

from .const import DOMAIN, LOGGER, PROPERTY_VALUE_MAP
from .entity import CulliganBaseEntity
from .update_coordinator import CulliganUpdateCoordinator

from ayla_iot_unofficial.device import Device, Softener
from collections.abc import Iterable
from culligan.culliganiot_device import CulliganIoTDevice, CulliganIoTSoftener

AYLA_DEVICES = [Device, Softener]
CULLIGAN_IOT_DEVICES = [CulliganIoTDevice, CulliganIoTSoftener]
ALL_DEVICES = AYLA_DEVICES + CULLIGAN_IOT_DEVICES

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up the Culligan switches from config entry."""
    LOGGER.debug("Switch async_setup_entry")
    # coordinator: CulliganUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: CulliganUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    devices: Iterable[Device] | Iterable[CulliganIoTDevice] = coordinator.culligan_devices.values()

    # id/key as in property map
    # name/description to be displayed in UI
    # icon_on
    # icon_off
    # supported devices
    softener_switches = [
        (
            # Vacation mode ('Gotcha', property name is 'set_vacation_mode', but ayla-iot-unofficial will 'clean' property name)
            "vacation_mode",
            "vacation mode",
            "mdi:airplane",
            "mdi:airplane-off",
            ALL_DEVICES,
        ),
        (
            # Permanent bypass mode ('Gotcha', property name is 'set_standard_bypass', but ayla-iot-unofficial will 'clean' property name)
            "standard_bypass",
            "permanent bypass",
            "mdi:valve-closed",
            "mdi:valve-open",
            ALL_DEVICES,
        )
    ]

    for device in devices:
        LOGGER.debug("Working on adding switches to device: %s", device._device_serial_number)
        switches = []
        for switch in softener_switches:
            if type(device) in switch[4]:
                LOGGER.debug("switch calling async_add: %s", switch[0])
                switches += [
                    SoftenerSwitch(
                        coordinator,
                        # config_entry,
                        device,
                        switch[0],  # id (property map key)
                        switch[1],  # description (name)
                        switch[2],  # icon on
                        switch[3],  # icon off
                    )
                ]
            else:
                LOGGER.debug(f"{switch[0]} not supported for {type(device)}")
    
    if len(switches) > 0:
        async_add_devices(switches)

    LOGGER.debug("Finished switch async_add_devices")

    # platform = entity_platform.async_get_current_platform()

    # platform.async_register_entity_service(
    #     SERVICE_SET_AWAY_MODE, {}, "async_set_mode_away"
    # )
    # platform.async_register_entity_service(
    #     SERVICE_SET_HOME_MODE, {}, "async_set_mode_home"
    # )
    # platform.async_register_entity_service(
    #     SERVICE_RUN_HEALTH_TEST, {}, "async_run_health_test"
    # )
    # platform.async_register_entity_service(
    #     SERVICE_SET_SLEEP_MODE,
    #     {
    #         vol.Required(ATTR_SLEEP_MINUTES, default=120): vol.All(
    #             vol.Coerce(int),
    #             vol.In(SLEEP_MINUTE_OPTIONS),
    #         ),
    #         vol.Required(ATTR_REVERT_TO_MODE, default=SYSTEM_MODE_HOME): vol.In(
    #             SYSTEM_REVERT_MODES
    #         ),
    #     },
    #     "async_set_mode_sleep",
    # )


class SoftenerSwitch(CulliganBaseEntity, SwitchEntity):
    """Switch class for the Flo by Moen valve."""

    # default ... sensor name is the property name alone (similar to specifying has_entity_name = True and use_device_name = False)
    has_entity_name = True  # sensor name is Softener property name ... because device exists by default
    use_device_name = False # sensor name is property name ... because device name is turned off by this flag

    def __init__(
            self, 
            coordinator: CulliganUpdateCoordinator, 
            #config_entry: ConfigEntry, 
            device: Device | CulliganIoTDevice, 
            sensor_id: str, 
            description: str, 
            icon_on: str, 
            icon_off: str
        ) -> None:
        """Initialize the Softener switch."""
        super().__init__(coordinator, device)

        # if CulliganIoT device
        if self.io_culligan: # isinstance(device, CulliganIoTDevice):
            self._attr_sensor_id                = PROPERTY_VALUE_MAP[sensor_id]   # this is the mapped Culligan sensor data value
        else:
            self._attr_sensor_id                = sensor_id             # this is the ayla property map key to get sensor data value
        
        self._attr_description                  = description
        self._attr_icon_on                      = icon_on
        self._attr_icon_off                     = icon_off

        self._attr_unique_id                    = device._device_serial_number + "_" + self._attr_sensor_id
        self.entity_id                          = generate_entity_id("switch.{}", self._attr_unique_id, None, coordinator.hass)

        # init is_on
        # Vac mode is 0 (off) or 1 (on)
        # Bypass is 255 (off) or 1-6 (on) or false/true
        self.on_values  = (True, 1, 2, 3, 4, 5, 6)
        self.off_values = (False, 0, 255)
        init_is_on      = device.get_property_value(self._attr_sensor_id)
        bypass_time     = device.get_property_value("time_rem_in_position")
        LOGGER.debug(f"Got: {init_is_on} for switch: {self.sensor_id}")
        self._attr_is_on= None
        if init_is_on in self.on_values or bypass_time > 0:
            if self._attr_description == "permanent bypass":
                if init_is_on == 6 or bypass_time == 255:
                    self._attr_is_on = True
                else:
                    self._attr_is_on = False
            elif self.sensor_id == "timed bypass":
                if init_is_on in (1,2,3,4,5) or (bypass_time > 0 and bypass_time < 255):
                    self._attr_is_on = True
                else:
                    self._attr_is_on = False
            elif self.sensor_id in ("vacation_mode","away_mode"):
                if init_is_on in self.on_values:
                    self._attr_is_on = True
                else:
                    self._attr_is_on = False
        else:
            LOGGER.debug("Setting switch to FALSE")
            self._attr_is_on = False
        #self._attr_is_on                        = bool(device.get_property_value(self._attr_sensor_id))

    @property
    def sensor_id(self):
        """Return the property key needed to get values"""
        return self._attr_sensor_id

    @property
    def icon(self):
        """Return the icon to use for the valve."""
        if self.is_on:
            return self._attr_icon_on
        return self._attr_icon_off

    @property
    def name(self) -> str | None:
        """Define name as description. This shows in the Sensor Name column of entities."""
        return f"{self._attr_description}"
    
    @property
    def unique_id(self) -> str | None:
        """Suggest the unique id of the entity. User never sees these."""
        return f"{self._attr_unique_id}"

    # @property
    # def is_on(self) -> bool | None:
    #     """Return the bool of on"""
    #     return f"{self._attr_is_on}"

    def set_is_on(self) -> None:
        """Set is_on based upon needed logic"""
        init_is_on      = self.device.get_property_value(self.sensor_id)
        bypass_time     = self.device.get_property_value("time_rem_in_position")
        LOGGER.debug(f"Got: {init_is_on} for switch: {self.sensor_id} with desc: {self._attr_description}. bypass_time is: {bypass_time}")
        if init_is_on in self.on_values or bypass_time > 0:
            if self._attr_description == "permanent bypass":
                if init_is_on == 6 or bypass_time == 255:
                    self._attr_is_on = True
                else:
                    self._attr_is_on = False
            elif self.sensor_id == "timed bypass":
                if init_is_on in (1,2,3,4,5) or (bypass_time > 0 and bypass_time < 255):
                    self._attr_is_on = True
                else:
                    self._attr_is_on = False
            elif self.sensor_id in ("vacation_mode","away_mode"):
                if init_is_on in self.on_values:
                    self._attr_is_on = True
                else:
                    self._attr_is_on = False
        else:
            self._attr_is_on = False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Open the thing / turn on the thing"""
        LOGGER.debug(f"turning on: {self.sensor_id}")
        if self.sensor_id in ["vacation_mode","away_mode"]:
            LOGGER.debug("Calling vacation/away")
            await self.device.async_start_vacation_mode() # device should be a property and set with BaseEntity
        elif self.sensor_id in ["standard_bypass"]:
            LOGGER.debug("Calling bypass")
            await self.device.async_start_bypass_mode() # device should be a property and set with BaseEntity
        self.set_is_on()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Close the thing / turn off the thing."""
        LOGGER.debug(f"turning off: {self.sensor_id}")
        if self.sensor_id in ["vacation_mode","away_mode"]:
            LOGGER.debug("Calling vacation/away")
            await self.device.async_stop_vacation_mode() # device should be a property and set with BaseEntity
        elif self.sensor_id in ["standard_bypass"]:
            LOGGER.debug("Calling bypass")
            await self.device.async_stop_bypass_mode() # device should be a property and set with BaseEntity
        self.set_is_on()
        self.async_write_ha_state()

    @callback
    def async_update_state(self) -> None:
        """Retrieve the latest valve state and update the state machine."""
        #self._attr_is_on = bool(self.device.get_property_value(self.sensor_id))
        self.set_is_on()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        #self.async_on_remove(self.device.async_add_listener(self.async_update_state))
        self.async_on_remove(self.coordinator.async_add_listener(self.async_update_state))

    # async def async_set_mode_home(self):
    #     """Set the Flo location to home mode."""
    #     await self._device.async_set_mode_home()

    # async def async_set_mode_away(self):
    #     """Set the Flo location to away mode."""
    #     await self._device.async_set_mode_away()

    # async def async_set_mode_sleep(self, sleep_minutes, revert_to_mode):
    #     """Set the Flo location to sleep mode."""
    #     await self._device.async_set_mode_sleep(sleep_minutes, revert_to_mode)

    # async def async_run_health_test(self):
    #     """Run a Flo device health test."""
    #     await self._device.async_run_health_test()