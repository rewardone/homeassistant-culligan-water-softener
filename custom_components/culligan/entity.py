"""CulliganEntity class"""
from .const import DOMAIN
from .update_coordinator import CulliganUpdateCoordinator
from ayla_iot_unofficial.device import Device
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class CulliganBaseEntity(Entity):
    """Base methods for Culligan entities."""

    def __init__(self, device: Device) -> None:
        """Init base methods."""
        self.device = device
        self.base_unique_id = device._name + "_" + device._device_serial_number
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.device._device_serial_number)},
            manufacturer="Culligan",
            model=f"{self.device._name + ' ' + self.device._device_model_number}",
            name=self.device._name
        )

class CulliganWaterSoftenerEntity(CoordinatorEntity):
    """
    First attempt. Deprecated for BaseEntity.
    """

    def __init__(
        self,
        coordinator: CulliganUpdateCoordinator,
        config_entry: ConfigEntry,
        device: Device,
    ) -> None:
        """Create a new SensorEntity"""

        super().__init__(coordinator)

        self._config_entry = config_entry

        self._coordinator = coordinator

        # assume that the device is a softener
        self.device = device

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
    def available(self):
        """Return state"""
        online = self.coordinator.device_is_online(self.device._device_serial_number)
        if online:
            return True
        else:
            return False
