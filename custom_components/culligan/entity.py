"""CulliganEntity class"""
from .const import DOMAIN
from .update_coordinator import CulliganUpdateCoordinator
from ayla_iot_unofficial.device import Device
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class CulliganBaseEntity(CoordinatorEntity, Entity):
    """Base methods for Culligan entities."""

    def __init__(self, coordinator: CulliganUpdateCoordinator, device: Device) -> None:
        """Init base methods."""
        super().__init__(coordinator, device)
        
        self.device = device
        self.base_unique_id = device.name + "_" + device.device_serial_number
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.device.device_serial_number)},
            manufacturer="Culligan",
            model=f"{self.device.name + ' ' + self.device.device_model_number}",
            name=self.device.name
        )