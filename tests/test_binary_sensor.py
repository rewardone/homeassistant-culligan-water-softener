"""Regression tests for Culligan binary sensor entity semantics."""
from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from types import SimpleNamespace


REPO_ROOT = Path(__file__).resolve().parents[1]
INTEGRATION_PATH = REPO_ROOT / "custom_components" / "culligan"


def _module(name: str, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


def _install_homeassistant_stubs():
    class Platform:
        BINARY_SENSOR = "binary_sensor"
        BUTTON = "button"
        NUMBER = "number"
        SENSOR = "sensor"
        SWITCH = "switch"

    class BinarySensorDeviceClass:
        OPENING = "opening"
        PRESENCE = "presence"

    class BinarySensorEntity:
        @property
        def state(self):
            is_on = getattr(self, "is_on")
            if is_on is None:
                return None
            return "on" if is_on else "off"

    class CoordinatorEntity:
        def __init__(self, coordinator, device=None):
            self.coordinator = coordinator

    class Entity:
        pass

    class DeviceInfo(dict):
        pass

    def generate_entity_id(fmt, name, hass=None, current_ids=None):
        return fmt.format(name)

    _module("homeassistant")
    _module("homeassistant.const", Platform=Platform)
    _module("homeassistant.components")
    _module("homeassistant.components.binary_sensor", BinarySensorDeviceClass=BinarySensorDeviceClass, BinarySensorEntity=BinarySensorEntity)
    _module("homeassistant.config_entries", ConfigEntry=object)
    _module("homeassistant.core", HomeAssistant=object)
    _module("homeassistant.helpers")
    _module("homeassistant.helpers.entity_platform", AddEntitiesCallback=object)
    _module("homeassistant.helpers.entity", DeviceInfo=DeviceInfo, Entity=Entity, generate_entity_id=generate_entity_id)
    _module("homeassistant.helpers.update_coordinator", CoordinatorEntity=CoordinatorEntity)


class _FakeAylaDevice:
    name = "Softener"
    _model = "FakeModel"

    def __init__(self, values):
        self._values = values
        self._device_serial_number = "ayla-serial"
        self.device_serial_number = "ayla-serial"
        self.seen_keys = []

    def get_property_value(self, key):
        self.seen_keys.append(key)
        return self._values.get(key)


class _FakeAylaSoftener(_FakeAylaDevice):
    pass


class _FakeCulliganIoTDevice(_FakeAylaDevice):
    def __init__(self, values):
        super().__init__(values)
        self._device_serial_number = "iot-serial"
        self.device_serial_number = "iot-serial"


class _FakeCulliganIoTSoftener(_FakeCulliganIoTDevice):
    pass


class _FakeCulliganIoTRO(_FakeCulliganIoTDevice):
    pass


def _install_vendor_stubs():
    _module("ayla_iot_unofficial")
    _module("ayla_iot_unofficial.device", Device=_FakeAylaDevice, Softener=_FakeAylaSoftener)
    _module("culligan")
    _module("culligan.culliganiot_device", CulliganIoTDevice=_FakeCulliganIoTDevice, CulliganIoTRO=_FakeCulliganIoTRO, CulliganIoTSoftener=_FakeCulliganIoTSoftener)


def _load_binary_sensor_module():
    for name in list(sys.modules):
        if name == "custom_components.culligan" or name.startswith("custom_components.culligan."):
            del sys.modules[name]

    _install_homeassistant_stubs()
    _install_vendor_stubs()
    _module("custom_components", __path__=[str(REPO_ROOT / "custom_components")])
    _module("custom_components.culligan", __path__=[str(INTEGRATION_PATH)])
    _module("custom_components.culligan.update_coordinator", CulliganUpdateCoordinator=object)
    return importlib.import_module("custom_components.culligan.binary_sensor")


def _make_sensor(module, device, sensor_id="valve_position"):
    return module.SoftenerBinarySensor(
        SimpleNamespace(hass=object()),
        object(),
        device,
        sensor_id,
        "bypass",
        "mdi:valve",
        None,
    )


def test_binary_sensor_uses_homeassistant_state_contract():
    module = _load_binary_sensor_module()
    entity = _make_sensor(module, _FakeCulliganIoTSoftener({"valve_position_1": True}))

    assert "state" not in module.SoftenerBinarySensor.__dict__
    assert entity.is_on is True
    assert entity.state == "on"


def test_culligan_iot_binary_sensor_uses_property_value_map():
    module = _load_binary_sensor_module()
    device = _FakeCulliganIoTSoftener({"valve_position_1": 1})
    entity = _make_sensor(module, device)

    assert entity.is_on is True
    assert device.seen_keys == ["valve_position_1"]


def test_ayla_binary_sensor_uses_raw_sensor_id():
    module = _load_binary_sensor_module()
    device = _FakeAylaSoftener({"valve_position": 0})
    entity = _make_sensor(module, device)

    assert entity.is_on is False
    assert device.seen_keys == ["valve_position"]


def test_binary_sensor_reports_unknown_for_missing_property():
    module = _load_binary_sensor_module()
    entity = _make_sensor(module, _FakeCulliganIoTSoftener({"valve_position_1": None}))

    assert entity.is_on is None
    assert entity.state is None
