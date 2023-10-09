"""Binary Sensor Entities"""
from .const import DOMAIN, LOGGER
from .entity import CulliganBaseEntity, CulliganWaterSoftenerEntity
from .update_coordinator import CulliganUpdateCoordinator
from ayla_iot_unofficial.device import Device
from collections.abc import Iterable
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import generate_entity_id


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up Culligan binary sensors"""
    LOGGER.debug("Binary sensor async_setup_entry")

    coordinator: CulliganUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    devices: Iterable[Device] = coordinator.culligan_devices.values()
    device_names = [d.name for d in devices]
    LOGGER.debug(
        "Found %d Culligan device(s): %s",
        len(device_names),
        ", ".join([d.name for d in devices]),
    )

    # id (property map key)
    # description (name)
    # icon
    # device_class
    binary_sensor_config = [
        (
            # Regen pending tonight
            "regen_tonight_pending",
            "regenerate tonight",
            "mdi:refresh-circle",
            None,
        ),
        (
            # Away mode water use (alerts)
            "away_mode_water_use",
            "away mode",
            "mdi:airplane",
            BinarySensorDeviceClass.PRESENCE,
        ),
        (
            # Salt level low
            "sbt_salt_level_low",
            "salt level low",
            "mdi:shaker-outline",
            None,
        ),
        (
            # Valve position
            "valve_position",
            "bypass",
            "mdi:valve",
            BinarySensorDeviceClass.OPENING,
        ),
    ]

    # Method two ... create individual sensors from a map of defined sensor attributes
    for device in devices:
        LOGGER.debug("Working on device: %s", device._device_serial_number)
        binary_sensors = []
        for sensor in binary_sensor_config:
            LOGGER.debug("binary sensor calling async_add: %s", sensor[0])
            binary_sensors += [
                SoftenerBinarySensor(
                    coordinator,
                    config_entry,
                    device,
                    sensor[0],  # id (property map key)
                    sensor[1],  # description (name)
                    sensor[2],  # icon
                    sensor[3],  # device class
                )
            ]

        # add devices will add a new device (with area selection)
        if len(binary_sensors) > 0:
            async_add_devices(binary_sensors)

        LOGGER.debug("Finished binary_sensor async_add_devices")


#class SoftenerBinarySensor(CulliganWaterSoftenerEntity):
class SoftenerBinarySensor(CulliganBaseEntity):
    """Generic binary sensor template for water softener"""

    has_entity_name = True
    use_device_name = False
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: CulliganUpdateCoordinator,
        config_entry: ConfigEntry,
        device: Device,
        sensor_id: str,
        description: str,
        icon: str,
        device_class: BinarySensorDeviceClass,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(device)

        self._attr_description  = description
        self._attr_device_class = device_class
        self._attr_icon         = icon
        self._attr_sensor_id    = sensor_id

        self._attr_unique_id    = device._device_serial_number + "_" + sensor_id
        self.entity_id          = generate_entity_id("binary_sensor.{}", self._attr_unique_id, None, coordinator.hass)


    @property
    def state(self) -> bool:
        """Overwrite state instead of creating new entity class"""
        return bool(self.device.get_property_value(self._attr_sensor_id))

    @property
    def is_on(self) -> bool:
        """On based on state"""
        return self.state

    @property
    def icon(self) -> str | None:
        """Define the icon"""
        return self._attr_icon

    @property
    def name(self) -> str | None:
        """Define name as description"""
        return f"{self._attr_description}"
