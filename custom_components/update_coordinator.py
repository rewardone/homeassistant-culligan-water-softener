"""Data update coordinator for shark iq vacuums."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from async_timeout import timeout
from culligan import CulliganApi

from ayla_iot_unofficial.device import Device, Softener

from ayla_iot_unofficial import AylaAuthError, AylaNotAuthedError, AylaAuthExpiringError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_TIMEOUT, DOMAIN, LOGGER, UPDATE_INTERVAL


class CulliganUpdateCoordinator(DataUpdateCoordinator[bool]):
    """Define a wrapper class to update Culligan data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        culligan: CulliganApi,
        culligan_devices: list[Softener] | list[Device],
    ) -> None:
        self.platforms = []

        """Set up the CulliganUpdateCoordinator class."""
        self.culligan = culligan
        self.culligan_devices: dict[str, Softener] | dict[str, Device] = {
            softener.serial_number: softener for softener in culligan_devices
        }
        self._config_entry = config_entry
        self._online_dsns: set[str] = set()

        super().__init__(hass, LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)

    @property
    def online_dsns(self) -> set[str]:
        """Get the set of all online DSNs."""
        return self._online_dsns

    def device_is_online(self, dsn: str) -> bool:
        """Return the online state of a given vacuum dsn."""
        return dsn in self._online_dsns

    @staticmethod
    async def _async_update_softener(softener: Softener) -> None:
        """Asynchronously update the data for a single vacuum."""
        dsn = softener.serial_number
        LOGGER.debug("Updating Culligan data for device DSN %s", dsn)
        async with timeout(API_TIMEOUT):
            await softener.async_update()

    async def _async_update_data(self) -> bool:
        """Update data device by device."""
        """CulliganApi has an instance of AylaApi, which is what we really care about updating until Culligan takes ownership"""

        # Check auth and refresh if needed
        try:
            if self.culligan.Ayla.token_expiring_soon:
                await self.culligan.Ayla.async_refresh_auth()
            elif datetime.now() > self.culligan.Ayla.auth_expiration - timedelta(
                seconds=600
            ):
                await self.culligan.Ayla.async_refresh_auth()

            # Check online devices
            all_devices = await self.culligan.Ayla.async_list_devices()
            self._online_dsns = {
                v["dsn"]
                for v in all_devices
                if v["connection_status"] == "Online"
                and v["dsn"] in self.culligan_devices
            }

            LOGGER.debug("Updating Culligan device data")
            online_devices = (self.culligan_devices[dsn] for dsn in self.online_dsns)
            await asyncio.gather(
                *(self._async_update_softener(v) for v in online_devices)
            )
        except (
            AylaAuthError,
            AylaNotAuthedError,
            AylaAuthExpiringError,
        ) as err:
            LOGGER.debug("Bad auth state.  Attempting re-auth", exc_info=err)
            raise ConfigEntryAuthFailed from err
        except Exception as err:
            LOGGER.exception(
                "Unexpected error updating Culligan devices.  Attempting re-auth"
            )
            raise UpdateFailed(err) from err

        return True
