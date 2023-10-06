"""Data update coordinator for Culligan devices."""
from __future__ import annotations
from .const import API_TIMEOUT, DOMAIN, LOGGER, PLATFORMS, UPDATE_INTERVAL

import asyncio
from async_timeout import timeout

from culligan import CulliganApi
from ayla_iot_unofficial.device import Device, Softener
from ayla_iot_unofficial import AylaAuthError, AylaNotAuthedError, AylaAuthExpiringError

from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed


class CulliganUpdateCoordinator(DataUpdateCoordinator[bool]):
    """Define a wrapper class to update Culligan data."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        culligan_api: CulliganApi,
        culligan_devices: list[Softener] | list[Device],
    ) -> None:
        """Set up the CulliganUpdateCoordinator class."""
        LOGGER.debug("coordinator init")

        self.culligan_api = culligan_api
        self.culligan_devices: dict[str, Softener] | dict[str, Device] = {
            softener.serial_number: softener for softener in culligan_devices
        }
        self._config_entry = config_entry
        self._online_dsns: set[str] = set()
        self.platforms = PLATFORMS

        super().__init__(hass, LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)
        LOGGER.debug("coordinator setup complete")

    @property
    def online_dsns(self) -> set[str]:
        """Get the set of all online DSNs."""
        LOGGER.debug("property set: online_dsns")
        return self._online_dsns

    def device_is_online(self, dsn: str) -> bool:
        """Return the online state of a given device dsn."""
        LOGGER.debug("check: device_is_online")
        return dsn in self._online_dsns

    @staticmethod
    async def _async_update_softener(softener: Softener) -> None:
        """Asynchronously update the data for a single device."""
        dsn = softener.serial_number
        LOGGER.debug(
            "async_update_softener: Updating Culligan data for device DSN %s", dsn
        )

        # Softeners need to send a wifi_report to trigger up-to-date information
        async with timeout(API_TIMEOUT):
            try:
                LOGGER.debug("sending batch_datapoints")
                poll = await softener.async_send_poll()
            except Exception as err:
                LOGGER.exception(
                    "Unexpected error updating Culligan devices.  Attempting re-auth"
                )
                raise UpdateFailed(err) from err

        # if the poll was successful, update internal property state
        if poll:
            async with timeout(API_TIMEOUT):
                try:
                    LOGGER.debug("starting async_update")
                    return await softener.async_update()
                except Exception as err:
                    LOGGER.exception(
                        "Unexpected error updating Culligan devices.  Attempting re-auth"
                    )
                    raise UpdateFailed(err) from err
        else:
            LOGGER.debug(
                "batch_datapoint send failure, properties will not be accurate"
            )

    async def _async_update_data(self) -> bool:
        """Loop through online DSNs and call update_softener. CulliganApi has an instance of AylaApi, which is what we really care about updating until Culligan takes ownership."""
        LOGGER.debug("_async_update_data")
        # Check auth and refresh if needed
        try:
            LOGGER.debug("checking auth token expiry")
            if self.culligan_api.Ayla.token_expiring_soon:
                await self.culligan_api.Ayla.async_refresh_auth()
            elif datetime.now() > self.culligan_api.Ayla.auth_expiration - timedelta(
                seconds=600
            ):
                await self.culligan_api.Ayla.async_refresh_auth()
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

        # Check online devices
        all_devices = await self.culligan_api.Ayla.async_list_devices()
        self._online_dsns = {
            v["dsn"]
            for v in all_devices
            if v["connection_status"] == "Online" and v["dsn"] in self.culligan_devices
        }
        LOGGER.debug("Online devices: %d", len(self._online_dsns))

        LOGGER.debug("async_update_data: Updating Culligan device data")
        online_devices = (self.culligan_devices[dsn] for dsn in self._online_dsns)
        try:
            return await asyncio.gather(
                *(self._async_update_softener(v) for v in online_devices)
            )
        except Exception as err:
            LOGGER.exception("Unexpected error updating Culligan devices")
            raise UpdateFailed(err) from err
