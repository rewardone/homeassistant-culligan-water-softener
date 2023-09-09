"""Culligan Integration."""
import asyncio
from contextlib import suppress

import async_timeout
from culligan import (
    CulliganApi,
    CulliganAuthError,
    CulliganAuthExpiringError,
    CulliganNotAuthedError,
)

from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PASSWORD, CONF_REGION, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import selector

from .const import (
    API_TIMEOUT,
    AYLA_REGION_EU,
    AYLA_REGION_DEFAULT,
    AYLA_REGION_OPTIONS,
    CULLIGAN_APP_ID,
    DOMAIN,
    NAME,
    LOGGER,
    PLATFORMS,
    STARTUP_MESSAGE,
    UPDATE_INTERVAL,
)
from .update_coordinator import CulliganUpdateCoordinator

SCAN_INTERVAL = UPDATE_INTERVAL

# CONFIG_SCHEMA = vol.Schema(
#     {
#         vol.Required(CONF_USERNAME): cv.matches_regex(
#             "\A[\w!#$%&'*+\/=?`{|}~^-]+(?:\.[\w!#$%&'*+\/=?`{|}~^-]+)*@(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}\Z"
#         ),
#         vol.Required(CONF_PASSWORD): cv.string,
#         vol.Required(CONF_REGION, default=AYLA_REGION_DEFAULT): selector.SelectSelector(
#             selector.SelectSelectorConfig(
#                 options=AYLA_REGION_OPTIONS, translation_key="region"
#             ),
#         ),
#     }
# )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


async def async_connect_or_timeout(culligan: CulliganApi) -> bool:
    """Connect to Ayla."""
    try:
        async with async_timeout.timeout(API_TIMEOUT):
            LOGGER.debug("Initialize connection to Ayla networks API")
            await culligan.async_sign_in()
            culligan.Ayla = culligan.get_ayla_api()
    except CulliganAuthError:
        LOGGER.error("Authentication error connecting to Culligan api")
        return False
    except asyncio.TimeoutError as exc:
        LOGGER.error("Timeout expired")
        raise CannotConnect from exc

    return True


# async def async_setup(hass: HomeAssistant, config_entry: ConfigType) -> bool:
#     """Initialize the Culligan platform via manual configuration.yml entry."""
#     LOGGER.debug("async_setup")

#     if CONF_REGION not in config_entry["culligan"]:
#         LOGGER.error(
#             "Culligan required value: 'region' not specified. Try one of: %s",
#             AYLA_REGION_OPTIONS,
#         )
#         raise ConfigEntryNotReady

#     LOGGER.debug("instantiating CulliganAPI")
#     culligan = CulliganApi(
#         username=config_entry["culligan"][CONF_USERNAME],
#         password=config_entry["culligan"][CONF_PASSWORD],
#         app_id=CULLIGAN_APP_ID,
#         websession=async_get_clientsession(hass),
#     )

#     try:
#         if not await async_connect_or_timeout(culligan):
#             return False
#     except CannotConnect as exc:
#         raise ConfigEntryNotReady from exc

#     LOGGER.debug("Obtaining device list")
#     culligan_devices = await culligan.Ayla.async_get_devices()

#     device_names = ", ".join(d.name for d in culligan_devices)
#     LOGGER.debug("Found %d Culligan device(s): %s", len(culligan_devices), device_names)

#     coordinator = CulliganUpdateCoordinator(
#         hass, config_entry, culligan, culligan_devices
#     )

#     # let the coordinator update the data
#     LOGGER.debug("Calling coordinator to update")
#     await coordinator.async_config_entry_first_refresh()

#     if not coordinator.last_update_success:
#         raise ConfigEntryNotReady

#     for platform in PLATFORMS:
#         if config_entry.options.get(platform, True):
#             coordinator.platforms.append(platform)
#             hass.async_add_job(
#                 hass.config_entries.async_forward_entry_setup(config_entry, platform)
#             )
#         else:
#             hass.data.setdefault(DOMAIN, {})
#             hass.data[DOMAIN][config_entry.entry_id] = coordinator

#             await hass.config_entries.async_forward_entry_setups(
#                 config_entry, PLATFORMS
#             )

#     config_entry.add_update_listener(async_reload_entry)

#     return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Initialize via UI"""
    LOGGER.debug("async_setup_entry")
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        LOGGER.info(STARTUP_MESSAGE)

    culligan = CulliganApi(
        username=config_entry.data[CONF_USERNAME],
        password=config_entry.data[CONF_PASSWORD],
        app_id=CULLIGAN_APP_ID,
        websession=async_get_clientsession(hass),
    )

    try:
        if not await async_connect_or_timeout(culligan):
            return False
    except CannotConnect as exc:
        raise ConfigEntryNotReady from exc

    culligan_devices = await culligan.Ayla.async_get_devices()
    device_names = ", ".join(d.name for d in culligan_devices)
    LOGGER.debug("Found %d Culligan device(s): %s", len(culligan_devices), device_names)

    coordinator = CulliganUpdateCoordinator(
        hass, config_entry, culligan, culligan_devices
    )

    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    for platform in PLATFORMS:
        if config_entry.options.get(platform, True):
            coordinator.platforms.append(platform)
            hass.async_add_job(
                hass.config_entries.async_forward_entry_setup(config_entry, platform)
            )
        else:
            hass.data.setdefault(DOMAIN, {})
            hass.data[DOMAIN][config_entry.entry_id] = coordinator

            await hass.config_entries.async_forward_entry_setups(
                config_entry, PLATFORMS
            )

    config_entry.add_update_listener(async_reload_entry)
    return True


async def async_disconnect_or_timeout(coordinator: CulliganUpdateCoordinator):
    """Disconnect - Invalidate Access Token"""
    LOGGER.debug("Disconnecting from Ayla Api")
    async with async_timeout.timeout(API_TIMEOUT):
        with suppress(
            CulliganAuthError, CulliganAuthExpiringError, CulliganNotAuthedError
        ):
            await coordinator.culligan.async_sign_out()


async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    """Update options."""
    LOGGER.debug("async_update_options")
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    LOGGER.debug("async_unload_entry")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        domain_data = hass.data[DOMAIN][config_entry.entry_id]
        with suppress(CulliganAuthError):
            await async_disconnect_or_timeout(coordinator=domain_data)
        hass.data[DOMAIN].pop(config_entry.entry_id)

    # unload_ok = await hass.config_entries.async_unload_platforms(
    #     config_entry, PLATFORMS
    # )
    # if unload_ok:
    #     domain_data = hass.data[DOMAIN][config_entry.entry_id]
    #     with suppress(CulliganAuthError):
    #         await async_disconnect_or_timeout(coordinator=domain_data)
    #     hass.data[DOMAIN].pop(config_entry.entry_id)

    # return unload_ok
    return unloaded


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload config entry."""
    LOGGER.debug("async_reload_entry")
    await async_unload_entry(hass, config_entry)
    await async_setup_entry(hass, config_entry)
