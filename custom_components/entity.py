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

        LOGGER.debug("Entity init: %s - %s", self.device, self.device._name)

    # Entity to contain at minimum: unique_id, device_info, state_attributes
    @property
    def unique_id(self):
        """Return a unique ID to use for this entity"""
        return self._config_entry.entry_id

    @property
    def device_info(self) -> DeviceInfo:
        """Device info dictionary."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
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
