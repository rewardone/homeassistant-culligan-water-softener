from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text()


def test_setup_supports_explicit_culligan_iot_ro_not_generic_device():
    init_py = _read("custom_components/culligan/__init__.py")

    assert "CulliganIoTRO" in init_py
    assert "SUPPORTED_DEVICE_CLASSES = [Softener, CulliganIoTSoftener, CulliganIoTRO]" in init_py
    assert "SUPPORTED_DEVICE_CLASSES = [Softener, CulliganIoTSoftener, CulliganIoTDevice]" not in init_py


def test_ro_datapoint_sensors_are_bound_to_explicit_ro_class():
    sensor_py = _read("custom_components/culligan/sensor.py")

    assert "CulliganIoTRO" in sensor_py
    assert "class CulliganIoTROSensor" in sensor_py
    assert "if isinstance(device, CulliganIoTRO):" in sensor_py
    assert "GenericCulliganIoTSensor" not in sensor_py
    assert "isinstance(device, CulliganIoTDevice) and not isinstance(device, CulliganIoTSoftener)" not in sensor_py


def test_update_coordinator_tracks_ro_as_supported_without_generic_iot_support():
    coordinator_py = _read("custom_components/culligan/update_coordinator.py")

    assert "CulliganIoTRO" in coordinator_py
    assert "SUPPORTED_DEVICE_CLASSES = [Softener, CulliganIoTSoftener, CulliganIoTRO]" in coordinator_py
    assert "SUPPORTED_DEVICE_CLASSES = [Softener, CulliganIoTSoftener, CulliganIoTDevice]" not in coordinator_py


def test_manifest_pins_culligan_library_version_with_ro_class():
    manifest_json = _read("custom_components/culligan/manifest.json")

    assert '"culligan==1.1.6"' in manifest_json
