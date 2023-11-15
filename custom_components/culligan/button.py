"""Switch representing the shutoff valve for the Flo by Moen integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.button import ButtonEntity
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
    """Set up the Culligan buttons from config entry."""
    LOGGER.debug("Switch async_setup_entry")
    # coordinator: CulliganUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator: CulliganUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    devices: Iterable[Device] | Iterable[CulliganIoTDevice] = coordinator.culligan_devices.values()

    # name/description to be displayed in UI
    # icon
    # supported devices
    softener_buttons = [
        (
            "clear bypass",
            "mdi:valve-open",
            ALL_DEVICES,
        )
    ]

    for device in devices:
        LOGGER.debug("Working on adding buttons to device: %s", device._device_serial_number)
        buttons = []
        for button in softener_buttons:
            if type(device) in button[2]:
                LOGGER.debug("button calling async_add: %s", button[0])
                buttons += [
                    SoftenerButton(
                        coordinator,
                        # config_entry,
                        device,
                        button[0],  # id (property map key)
                        button[1],  # icon on
                    )
                ]
            else:
                LOGGER.debug(f"{button[0]} not supported for {type(device)}")
    
    if len(buttons) > 0:
        async_add_devices(buttons)

    LOGGER.debug("Finished button async_add_devices")


class SoftenerButton(CulliganBaseEntity, ButtonEntity):
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
            icon: str
        ) -> None:
        """Initialize the Softener switch."""
        super().__init__(coordinator, device)

        # # if CulliganIoT device
        # if self.io_culligan: # isinstance(device, CulliganIoTDevice):
        #     self._attr_sensor_id                = PROPERTY_VALUE_MAP[sensor_id]   # this is the mapped Culligan sensor data value
        # else:
        self._attr_sensor_id                    = sensor_id             # this is the ayla property map key to get sensor data value
        
        # self._attr_description                  = description
        self._attr_icon                         = icon

        self._attr_unique_id                    = device._device_serial_number + "_" + self._attr_sensor_id
        self.entity_id                          = generate_entity_id("button.{}", self._attr_unique_id, None, coordinator.hass)

    @property
    def sensor_id(self):
        """Return the property key needed to get values"""
        return self._attr_sensor_id

    @property
    def icon(self):
        """Define the icon"""
        return self._attr_icon

    @property
    def name(self) -> str | None:
        """Define name as sensor ID. This shows in the Sensor Name column of entities."""
        return f"{self._attr_sensor_id}"
    
    @property
    def unique_id(self) -> str | None:
        """Suggest the unique id of the entity. User never sees these."""
        return f"{self._attr_unique_id}"

    async def async_press(self, **kwargs: Any) -> None:
        """Close the thing / turn off the thing."""
        LOGGER.debug(f"Pressed: {self.sensor_id}")
        if self.sensor_id in ["clear bypass"]:
            LOGGER.debug("Pressing clear bypass")
            await self.device.async_stop_bypass_mode() # device should be a property and set with BaseEntity
