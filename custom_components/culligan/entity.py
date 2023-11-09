"""CulliganEntity class"""
from .const import DOMAIN, LOGGER
from .update_coordinator import CulliganUpdateCoordinator
from ayla_iot_unofficial.device import Device, Softener
from culligan.culliganiot_device import CulliganIoTDevice, CulliganIoTSoftener
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

class CulliganBaseEntity(CoordinatorEntity, Entity):
    """Base methods for Culligan entities."""

    has_entity_name = True  # sensor name is Softener property name ... because device exists by default
    use_device_name = False # sensor name is property name ... because device name is turned off by this flag

    def __init__(self, coordinator: CulliganUpdateCoordinator, device: Device) -> None:
        """Init base methods."""
        super().__init__(coordinator, device)
        
        self.device         = device
        self.coordinator    = coordinator

        # at a high level, we want to know if it's a culligan 'thing' or an ayla 'thing'
        self._io_culligan    = isinstance(device, CulliganIoTDevice)

        # if culligan iot, but not classified as 'softener' ... expect things to break
        if self._io_culligan and not isinstance(device, CulliganIoTSoftener):
            LOGGER.warning(f"Device {device.device_serial_number} is a CulliganIoT device, but was not cast as a CulliganIoTSoftener. Expect things to break!")
        
        # Similar, if Ayla, but not classified as 'softener' ... expect things to break
        if not self._io_culligan and not isinstance(device, Softener):
            LOGGER.warning(f"Device {device.device_serial_number} is an Ayla device, but was not cast as a Softener. Expect things to break!")

        # self.base_unique_id = device.name + "_" + device.device_serial_number
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.device.device_serial_number)},
            manufacturer="Culligan",
            model=f"{self.device.name + ' ' + self.device.device_model_number}",
            name=self.device.name
        )

    @property
    def io_culligan(self) -> bool:
        """Return whether is instance of Culligan"""
        return self._io_culligan