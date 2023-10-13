"""Data update coordinator for Culligan devices."""
from __future__ import annotations
from .const import API_TIMEOUT, DOMAIN, LOGGER, PLATFORMS

import asyncio
from async_timeout import timeout

from ayla_iot_unofficial.device import Device, Softener
from ayla_iot_unofficial import AylaAuthError, AylaNotAuthedError, AylaAuthExpiringError
from culligan.exc import CulliganApi, CulliganAuthError, CulliganNotAuthedError, CulliganAuthExpiringError
from culligan.culliganiot_device import CulliganIoTDevice, CulliganIoTSoftener

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
        culligan_devices: list[Softener] | list[Device] | list[CulliganIoTDevice] | list[CulliganIoTSoftener],
    ) -> None:
        """Set up the CulliganUpdateCoordinator class."""
        LOGGER.debug("coordinator init")

        self.culligan_api = culligan_api

        LOGGER.debug(f"Culligan_devices: {culligan_devices}")
        # make a dict of serials with their device objects
        self.culligan_devices = {
            softener.device_serial_number: softener for softener in culligan_devices
        }
        LOGGER.debug(f"self culligan_devices map: {self.culligan_devices}")

        self._config_entry = config_entry
        self._hass = hass
        self._online_dsns: set[str] = set()
        self.platforms = PLATFORMS

        update_interval = config_entry.data["user_input"]["update_interval"]

        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        LOGGER.debug("coordinator setup complete")

    @property
    def online_dsns(self) -> set[str]:
        """Get the set of all online DSNs."""
        # LOGGER.debug("property set: online_dsns")
        return self._online_dsns

    def device_is_online(self, dsn: str) -> bool:
        """Return the online state of a given device dsn."""
        LOGGER.debug("check: device_is_online")
        return dsn in self._online_dsns

    @staticmethod
    async def _async_update_softener(softener: Softener | CulliganIoTSoftener) -> None:
        """Asynchronously update the data for a single device."""
        dsn = softener.device_serial_number
        LOGGER.debug(
            "async_update_softener: Updating Culligan data for device DSN %s", dsn
        )

        # Ayla connected Softeners need to send a wifi_report to trigger up-to-date information
        if isinstance(softener, Softener):
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

        if isinstance(softener, CulliganIoTSoftener):
            LOGGER.debug("updating culliganiot softener")
            async with timeout(API_TIMEOUT):
                try:
                    LOGGER.debug("starting async_update")
                    return await softener.async_update()
                except Exception as err:
                    LOGGER.exception(
                        "Unexpected error updating Culligan devices.  Attempting re-auth"
                    )
                    raise UpdateFailed(err) from err

    async def _async_update_data(self) -> bool:
        """Loop through online DSNs and call update_softener. CulliganApi has an instance of AylaApi, which is what we really care about updating until Culligan takes ownership."""
        LOGGER.debug("_async_update_data")

        # If configuration options have changed ... update them now:
        config_entry = self.hass.config_entries.async_get_entry(
            self._config_entry.entry_id
        )
        # LOGGER.debug("Config entry data: %s", config_entry.data)
        # LOGGER.debug("Config entry options: %s", config_entry.options)
        if "update_interval" in config_entry.options.keys():
            if self.update_interval != timedelta(
                seconds=config_entry.options["update_interval"]
            ):
                LOGGER.debug(
                    "Updating update-interval to: %i",
                    config_entry.options["update_interval"],
                )
                self.update_interval = timedelta(
                    seconds=config_entry.options["update_interval"]
                )

        # Check auth and refresh if needed of Culligan IoT
        try:
            LOGGER.debug("checking CulliganIoT auth token expiry")
            if self.culligan_api.token_expiring_soon:
                await self.culligan_api.async_refresh_auth()
            elif datetime.now() > self.culligan_api.auth_expiration - timedelta(
                seconds=600
            ):
                await self.culligan_api.async_refresh_auth()
        except (
            CulliganAuthError,
            CulliganNotAuthedError,
            CulliganAuthExpiringError,
        ) as err:
            LOGGER.debug("CulliganIoT Bad auth state.  Attempting re-auth", exc_info=err)
            raise ConfigEntryAuthFailed from err
        except Exception as err:
            LOGGER.exception(
                "Unexpected error updating Culligan devices.  Attempting re-auth"
            )
            raise UpdateFailed(err) from err
        
        # Check auth and refresh if needed of Ayla
        try:
            LOGGER.debug("checking Ayla auth token expiry")
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
            LOGGER.debug("Bad Ayla auth state.  Attempting re-auth", exc_info=err)
            raise ConfigEntryAuthFailed from err
        except Exception as err:
            LOGGER.exception(
                "Unexpected error updating Culligan devices.  Attempting re-auth"
            )
            raise UpdateFailed(err) from err

        # Check online devices
        all_online_devices = []
        all_online_devices += await self.culligan_api.Ayla.async_list_devices()
        all_online_devices += (await self.culligan_api.async_get_device_registry())["data"]["devices"]

        temp = {}
        for device in all_online_devices:
            dsn = ""
            if "dsn" in device.keys():
                dsn = device["dsn"]
            elif "serialNumber" in device.keys():
                dsn = device["serialNumber"]
            else:
                LOGGER.debug(f"all_online_devices has no dsn or serialNumber property! {device}")

            temp[dsn] = "online"
        LOGGER.debug(f"Added online DSNs to temp dict {temp}")
        self._online_dsns = temp.keys()
        LOGGER.debug(f"online_dsns is keys() {self.online_dsns}")

        # self._online_dsns = all_online_devices

        if len(self.online_dsns) > 0:
            # Update all online devices
            # get the objects by dsn from the culligan_devices dict
            LOGGER.debug(f"async_update_data: Updating Culligan device data for {len(all_online_devices)} devices")
            online_devices = (self.culligan_devices[dsn] for dsn in self._online_dsns)

            try:
                return await asyncio.gather(
                    *(self._async_update_softener(v) for v in online_devices)
                )
            except Exception as err:
                LOGGER.exception("Unexpected error updating Culligan devices")
                raise UpdateFailed(err) from err
        else:
            LOGGER.debug("No online devices were parsed, no updates to make.")