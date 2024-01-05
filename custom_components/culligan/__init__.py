"""Culligan Integration."""
from .const import (
    API_TIMEOUT,
    CLIENT,
    CULLIGAN_APP_ID,
    DOMAIN,
    LOGGER,
    PLATFORMS,
    STARTUP_MESSAGE,
)
from .update_coordinator import CulliganUpdateCoordinator

import asyncio
import async_timeout

from ayla_iot_unofficial.device import Softener
from culligan.culliganiot_device import CulliganIoTSoftener

from contextlib import suppress

from culligan import (
    CulliganApi,
    CulliganAuthError,
    CulliganAuthExpiringError,
    CulliganNotAuthedError,
)

from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Initialize via UI --- IF --- async_setup is not defined"""
    LOGGER.debug("__init__ async_setup_entry from")

    # config entry object contains: data, options, unique_id, source, state, update_listeners, and more
    # data contains the data property from the config_flow
    #    UI is configured to return:
    #       data.user_info (UI entry data just in case re-auth is needed)
    #       data.instance (title, devices, dsn[0], culligan_api)
    LOGGER.debug("title %s", config_entry.title)
    LOGGER.debug("data %s", config_entry.data)
    LOGGER.debug("options %s", config_entry.options)
    LOGGER.debug("unique_id %s", config_entry.unique_id) # set to DSN
    LOGGER.debug("source %s", config_entry.source)

    # raise ConfigEntryNotReady

    # check existing DOMAIN for data
    if hass.data.get(DOMAIN) is None:
        LOGGER.debug("No DOMAIN ... setting %s", DOMAIN)
        hass.data.setdefault(DOMAIN, {})
        LOGGER.info(STARTUP_MESSAGE)
    LOGGER.debug(f"Domain is now: {hass.data[DOMAIN]}")

    # if we entered from UI ... a connection check was made and an object exists already
    # don't recreate ... but also can't serialize culligan_api objects in the config_entry
    if "culligan_api" in config_entry.data["instance"].keys():
        culligan_api = config_entry.data["instance"]["culligan_api"]
    #except KeyError:
    else:
        LOGGER.debug("CulliganApi instance was not passed from config_entry ... creating one")
        try:
            culligan_api = CulliganApi(
                username=config_entry.data["user_input"][CONF_USERNAME],
                password=config_entry.data["user_input"][CONF_PASSWORD],
                app_id=CULLIGAN_APP_ID,
                websession=async_get_clientsession(hass),
            )
        except CannotConnect as exc:
            raise ConfigEntryNotReady from exc

    # connect_or_timeout will set API token and CulliganAPI.Ayla
    try:
        LOGGER.debug("Calling connect_or_timeout to sign in and ensure API tokens")
        # if successful, culligan_api.Ayla will be initialized
        if not await async_connect_or_timeout(culligan_api):
            return False
    except CannotConnect as exc:
        raise ConfigEntryNotReady from exc
    
    # get device registry from Culligan
    LOGGER.debug("Asking for devices from Culligan")
    culliganiot_devices = await culligan_api.async_get_devices()
    device_names = ", ".join(d.name for d in culliganiot_devices)
    LOGGER.debug("Found %d Culligan device(s): %s", len(culliganiot_devices), device_names)
    if len(culliganiot_devices) > 0:
        for d in culliganiot_devices:
            LOGGER.debug(f"    of type: {type(d)}")

    # get device registry from ayla
    LOGGER.debug("Asking for devices from Ayla")
    culligan_devices = await culligan_api.Ayla.async_get_devices()
    device_names = ", ".join(d.name for d in culligan_devices)
    LOGGER.debug("Found %d Ayla-connected Culligan device(s): %s", len(culligan_devices), device_names)
    if len(culligan_devices) > 0:
        for d in culligan_devices:
            LOGGER.debug(f"    of type: {type(d)}")

    # combine the list of devices from both to all_devices
    if len(culliganiot_devices) > 0 and len(culligan_devices) > 0:
        LOGGER.debug("Adding CulliganIoT and Ayla devices together")
        all_devices = culliganiot_devices + culligan_devices
    elif len(culliganiot_devices) > 0 and len(culligan_devices) < 1:
        LOGGER.debug("Only found CulliganIoT devices")
        all_devices = culliganiot_devices
    elif len(culliganiot_devices) < 1 and len(culligan_devices) > 0:
        LOGGER.debug("Only found Ayla-connected devices")
        all_devices = culligan_devices

    # separate devices from supported devices since processing unsupported devices results in too many errors
    SUPPORTED_DEVICE_CLASSES = [Softener, CulliganIoTSoftener]
    supported_devices = []
    for device in all_devices:
        if type(device) in SUPPORTED_DEVICE_CLASSES:
            LOGGER.debug(f"Adding supported device {device.name} of {type(device)}")
            supported_devices += [device]
    
    # instance the data update coordinator with only supported_devices instead of all_devices
    LOGGER.debug(f"Setting coordinator with supported_devices: {supported_devices}")
    coordinator = CulliganUpdateCoordinator(
        hass, config_entry, culligan_api, supported_devices
    )

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    LOGGER.debug("refreshing coordinator")
    # await coordinator.async_refresh()
    await coordinator.async_config_entry_first_refresh()

    if not coordinator.last_update_success:
        LOGGER.debug("refresh was not successful")
        raise ConfigEntryNotReady

    LOGGER.debug("calling add_update_listener(s)")

    # don't overwrite the entry_id itself ... add a properpty
    #     coordinator has an instance of api coordinator.culligan_api
    # hass.data[DOMAIN][config_entry.entry_id] = coordinator
    LOGGER.debug(f"entry_id was: {config_entry.entry_id}")
    hass.data[DOMAIN][config_entry.entry_id] = {}
    hass.data[DOMAIN][config_entry.entry_id]["coordinator"] = coordinator

    LOGGER.debug("Calling forward_entry_setup")
    for platform in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, platform)
        )

    # HA docs signal updates
    config_entry.async_on_unload(config_entry.add_update_listener(async_update_options))
    # config_entry.add_update_listener(async_update_options)
    # config_entry.add_update_listener(async_reload_entry)

    LOGGER.debug("If we made it this far ... TRUE that setup is complete")
    return True


async def async_connect_or_timeout(culligan: CulliganApi) -> bool:
    """Connect to Ayla."""
    LOGGER.debug("async_connect_or_timeout")
    try:
        async with async_timeout.timeout(API_TIMEOUT):
            LOGGER.debug("Signing into Culligan")
            await culligan.async_sign_in()

            LOGGER.debug("Passed sign in ... parsing access_tokens for Ayla")
            culligan.Ayla = culligan.get_ayla_api()

            return True
    except CulliganAuthError:
        LOGGER.error("Authentication error connecting to Culligan api")
        return False
    except asyncio.TimeoutError as exc:
        LOGGER.error("Timeout expired")
        raise CannotConnect from exc


async def async_disconnect_or_timeout(coordinator: CulliganUpdateCoordinator):
    """Disconnect - Invalidate Access Token"""
    LOGGER.debug("Disconnecting from Ayla Api")
    async with async_timeout.timeout(API_TIMEOUT):
        with suppress(
            CulliganAuthError, CulliganAuthExpiringError, CulliganNotAuthedError
        ):
            await coordinator.culligan_api.async_sign_out()
            return True


async def async_update_options(hass: HomeAssistant, config_entry: ConfigEntry):
    """Update options function for options flow events"""
    LOGGER.debug("async_update_options")
    # Reload the integration to re-instance the coordinator with a new update_interval / options
    # hass.config_entries.async_update_entry(
    #     config_entry, options=dict(config_entry.options)
    # )
    # await async_reload_entry(hass, config_entry)
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    LOGGER.debug("async_unload_entry")

    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, platform)
                for platform in PLATFORMS
            ]
        )
    )

    # coordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]

    await async_disconnect_or_timeout(coordinator)

    if unloaded:
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Reload config entry."""
    LOGGER.debug("async_reload_entry")

    await hass.config_entries.async_reload(config_entry.entry_id)
