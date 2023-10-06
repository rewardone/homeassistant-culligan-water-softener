"""CulliganEntity class"""
from .const import DOMAIN, LOGGER
from .update_coordinator import CulliganUpdateCoordinator
from ayla_iot_unofficial.device import Device
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity


class CulliganWaterSoftenerEntity(CoordinatorEntity):
    """
    Softener Entity
    """

    def __init__(
        self,
        coordinator: CulliganUpdateCoordinator,
        config_entry: ConfigEntry,
        device: Device,
    ) -> None:
        """Create a new SensorEntity"""
        LOGGER.debug("Class SoftenerEntity init")

        super().__init__(coordinator)
        self._config_entry = config_entry

        # assume that the device is a softener
        self.device = device

        LOGGER.debug(
            "Entity init: %s - %s", self.device._name, self.device._device_serial_number
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Device info dictionary."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.device._device_serial_number)},
            name=self.device._name,
            manufacturer="Culligan",
            model=self.device._device_model_number,
        )

    @property
    def name(self) -> str | None:
        """Return the name of the sensor."""
        return self.device._name

    @property
    def state(self):
        """Return state"""
        online = self.coordinator.device_is_online(self.device._device_serial_number)
        if online:
            return True
        else:
            return False
