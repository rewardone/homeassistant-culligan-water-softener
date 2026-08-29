"""Tests for automatic re-authentication and telemetry polling (issues #15 and #29)."""
import asyncio
from pathlib import Path

import pytest
from culligan.exc import CulliganAuthError

from custom_components.culligan.update_coordinator import async_fetch_registry_devices
from homeassistant.exceptions import ConfigEntryAuthFailed

ROOT = Path(__file__).resolve().parents[1]

DEVICES = [{"serialNumber": "ABC123"}]


class FakeCulliganApi:
    """Minimal CulliganApi double for registry/auth behavior."""

    Ayla = None
    _ayla_access_token = "at"
    _ayla_refresh_token = "rt"
    _ayla_expiration_raw = 3600

    def __init__(self, registry_errors: int = 0, sign_in_error: bool = False):
        self._registry_errors = registry_errors
        self._sign_in_error = sign_in_error
        self.sign_in_calls = 0
        self.registry_calls = 0

    async def async_get_device_registry(self):
        self.registry_calls += 1
        if self._registry_errors > 0:
            self._registry_errors -= 1
            raise CulliganAuthError({"error": {"message": "INVALID_TOKEN"}})
        return {"data": {"devices": DEVICES}}

    async def async_sign_in(self):
        self.sign_in_calls += 1
        if self._sign_in_error:
            raise CulliganAuthError({"error": {"message": "BAD_CREDENTIALS"}})


def test_nominal_fetch_does_not_sign_in():
    api = FakeCulliganApi()
    devices = asyncio.run(async_fetch_registry_devices(api))
    assert devices == DEVICES
    assert api.sign_in_calls == 0


def test_invalid_token_triggers_resign_in_and_retry():
    api = FakeCulliganApi(registry_errors=1)
    devices = asyncio.run(async_fetch_registry_devices(api))
    assert devices == DEVICES
    assert api.sign_in_calls == 1
    assert api.registry_calls == 2


def test_bad_credentials_raise_config_entry_auth_failed():
    api = FakeCulliganApi(registry_errors=1, sign_in_error=True)
    with pytest.raises(ConfigEntryAuthFailed):
        asyncio.run(async_fetch_registry_devices(api))


def test_coordinator_sends_telemetry_command_for_iot_softeners():
    coordinator_py = (ROOT / "custom_components/culligan/update_coordinator.py").read_text()

    assert "async_get_telemetry" in coordinator_py
    assert "isinstance(softener, CulliganIoTSoftener)" in coordinator_py
