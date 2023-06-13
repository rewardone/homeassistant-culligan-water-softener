"""Culligan Integration."""
import asyncio
from contextlib import suppress

import async_timeout
from culligan import (
    CulliganApi,
    CulliganAuthError,
    CulliganAuthExpiringError,
    CulliganNotAuthedError
)

from homeassistant import exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_REGION, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    API_TIMEOUT,
    DOMAIN,
    LOGGER,
    AYLA_REGION_EU,
    AYLA_REGION_DEFAULT,
    AYLA_REGION_OPTIONS,
    PLATFORMS,
)
from .update_coordinator import CulliganUpdateCoordinator


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


async def async_connect_or_timeout(culligan: CulliganApi) -> bool:
    """Connect to vacuum."""
    try:
        async with async_timeout.timeout(API_TIMEOUT):
            LOGGER.debug("Initialize connection to Ayla networks API")
            await culligan.async_sign_in()
    except CulliganAuthError:
        LOGGER.error("Authentication error connecting to Culligan api")
        return False
    except asyncio.TimeoutError as exc:
        LOGGER.error("Timeout expired")
        raise CannotConnect from exc

    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Initialize the Culligan platform via config entry."""
    if CONF_REGION not in config_entry.data:
        hass.config_entries.async_update_entry(
            config_entry,
            data={**config_entry.data, CONF_REGION: AYLA_REGION_DEFAULT},
        )

    culligan = CulliganApi(
        username=config_entry.data[CONF_USERNAME],
        password=config_entry.data[CONF_PASSWORD],
        websession=async_get_clientsession(hass)
    )

    try:
        if not await async_connect_or_timeout(culligan):
            return False
    except CannotConnect as exc:
        raise exceptions.ConfigEntryNotReady from exc

    culligan_devices = await culligan.Ayla.async_get_devices()
    device_names = ", ".join(d.name for d in culligan_devices)
    LOGGER.debug("Found %d Culligan device(s): %s", len(culligan_devices), device_names)
    coordinator = CulliganUpdateCoordinator(hass, config_entry, culligan, culligan_devices)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_disconnect_or_timeout(coordinator: CulliganUpdateCoordinator):
    """Disconnect to vacuum."""
    LOGGER.debug("Disconnecting from Ayla Api")
    async with async_timeout.timeout(5):
        with suppress(
            CulliganAuthError, CulliganAuthExpiringError, CulliganNotAuthedError
        ):
            await coordinator.culligan.async_sign_out()


async def async_update_options(hass, config_entry):
    """Update options."""
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        domain_data = hass.data[DOMAIN][config_entry.entry_id]
        with suppress(CulliganAuthError):
            await async_disconnect_or_timeout(coordinator=domain_data)
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok