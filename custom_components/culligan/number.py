"""Number entities for Culligan."""
from __future__ import annotations

from collections.abc import Iterable

from culligan.culliganiot_device import CulliganIoTDevice, CulliganIoTSoftener
from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import generate_entity_id
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEFAULT_TIMED_BYPASS_MINUTES,
    DOMAIN,
    LOGGER,
    MAX_TIMED_BYPASS_MINUTES,
    MIN_TIMED_BYPASS_MINUTES,
    STEP_TIMED_BYPASS_MINUTES,
)
from .entity import CulliganBaseEntity
from .update_coordinator import CulliganUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    """Set up Culligan number entities from config entry."""
    LOGGER.debug("Number async_setup_entry")
    coordinator: CulliganUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    devices: Iterable[CulliganIoTDevice] = coordinator.culligan_devices.values()

    if not hasattr(coordinator, "timed_bypass_minutes"):
        coordinator.timed_bypass_minutes = {}
    if not isinstance(coordinator.timed_bypass_minutes, dict):
        coordinator.timed_bypass_minutes = {}

    numbers = []
    for device in devices:
        if isinstance(device, CulliganIoTSoftener):
            numbers.append(TimedBypassMinutesNumber(coordinator, device))

    if numbers:
        async_add_devices(numbers)

    LOGGER.debug("Finished number async_add_devices")


class TimedBypassMinutesNumber(CulliganBaseEntity, NumberEntity):
    """Dashboard-selectable timed bypass duration for CulliganIoT softeners."""

    has_entity_name = True
    use_device_name = False

    _attr_mode = NumberMode.SLIDER
    _attr_native_min_value = MIN_TIMED_BYPASS_MINUTES
    _attr_native_max_value = MAX_TIMED_BYPASS_MINUTES
    _attr_native_step = STEP_TIMED_BYPASS_MINUTES
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES
    _attr_icon = "mdi:timer-cog-outline"

    def __init__(self, coordinator: CulliganUpdateCoordinator, device: CulliganIoTSoftener) -> None:
        """Initialize the timed bypass duration number."""
        super().__init__(coordinator, device)
        self._attr_description = "timed bypass duration"
        self._attr_unique_id = f"{device.device_serial_number}_timed_bypass_minutes"
        self.entity_id = generate_entity_id("number.{}", self._attr_unique_id, None, coordinator.hass)
        self._attr_native_value = int(
            coordinator.timed_bypass_minutes.get(
                device.device_serial_number,
                DEFAULT_TIMED_BYPASS_MINUTES,
            )
        )
        self.coordinator.timed_bypass_minutes[device.device_serial_number] = self._attr_native_value

    @property
    def name(self) -> str | None:
        """Define name as description."""
        return self._attr_description

    @property
    def unique_id(self) -> str | None:
        """Return the unique ID."""
        return self._attr_unique_id

    @property
    def native_value(self) -> int:
        """Return the currently selected bypass duration."""
        duration_map = getattr(self.coordinator, "timed_bypass_minutes", {})
        if not isinstance(duration_map, dict):
            return self._attr_native_value
        return int(duration_map.get(self.device.device_serial_number, self._attr_native_value))

    async def async_set_native_value(self, value: float) -> None:
        """Set the timed bypass duration in minutes."""
        minutes = round(value)
        minutes = max(MIN_TIMED_BYPASS_MINUTES, min(MAX_TIMED_BYPASS_MINUTES, minutes))
        self.coordinator.timed_bypass_minutes[self.device.device_serial_number] = minutes
        self._attr_native_value = minutes
        self.async_write_ha_state()
