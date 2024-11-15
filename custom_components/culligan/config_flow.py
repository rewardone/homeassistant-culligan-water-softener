"""Config Flow for Culligan integration"""

import aiohttp
import asyncio
import async_timeout
from collections.abc import Mapping
from culligan import CulliganApi, CulliganAuthError

from homeassistant import config_entries, core, exceptions
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.core import callback
from homeassistant.const import CONF_PASSWORD, CONF_REGION, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from typing import Any, Optional

from re import compile as recompile

import voluptuous as vol

from .const import (
    API_TIMEOUT,
    AYLA_REGION_DEFAULT,
    AYLA_REGION_OPTIONS,
    CULLIGAN_APP_ID,
    DOMAIN,
    LOGGER,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.EMAIL, autocomplete="email"
            )
        ),
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
        vol.Required(CONF_REGION, default=AYLA_REGION_DEFAULT): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=AYLA_REGION_OPTIONS, translation_key="region"
            ),
        ),
        vol.Optional("update_interval", default=30): cv.positive_int,
    }
)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class UnknownAuth(exceptions.HomeAssistantError):
    """Error to indicate there is an uncaught auth error."""


async def validate_email(hass: core.HomeAssistant, data: Mapping[str, Any]) -> bool:
    """Validate the username is an email address"""

    LOGGER.debug("_validate_email")
    email_regex = "(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21\\x23-\\x5b\\x5d-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21-\\x5a\\x53-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])+)\\])"
    compiled = recompile(email_regex)
    matches = compiled.findall(data[CONF_USERNAME])
    if not matches:
        return False
    else:
        return True


async def validate_input(
    hass: core.HomeAssistant, data: Mapping[str, Any]
) -> None:  # dict[str, str]:
    """Actually test the user input allows us to connect."""

    LOGGER.debug("_validate_input")
    culligan = CulliganApi(
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        app_id=CULLIGAN_APP_ID,
        websession=async_get_clientsession(hass),
    )

    try:
        async with async_timeout.timeout(API_TIMEOUT):
            LOGGER.debug("Initialize connection to Ayla networks API")
            await culligan.async_sign_in()
            culligan.Ayla = culligan.get_ayla_api()
    except (asyncio.TimeoutError, aiohttp.ClientError, TypeError) as error:
        LOGGER.error(error)
        raise CannotConnect(
            "Unable to connect to Culligan services.  Check your region settings."
        ) from error
    except CulliganAuthError as error:
        LOGGER.error(error)
        raise InvalidAuth(
            "Username or password incorrect.  Please check your credentials."
        ) from error
    except Exception as error:
        LOGGER.exception("Unexpected exception")
        LOGGER.error(error)
        raise UnknownAuth(
            "An unknown error occurred. Check your region settings and open an issue on Github if the issue persists."
        ) from error

    if culligan.Ayla:
        LOGGER.debug("Got Ayla instance, obtaining devices")
        devices = await culligan.Ayla.async_get_devices()

        # Return info that you want to store in the config entry.
        info = {
            "title": "Culligan - %s" % data[CONF_USERNAME],
            "dsn": ", ".join(d._dsn for d in devices),
        }
        LOGGER.debug(info)
        return info
    elif culligan.Ayla in (None,False):
        LOGGER.debug("No Ayla instances, obtaining devices directly from Culligan only")
        devices = await culligan.async_get_devices()

        # Return info that you want to store in the config entry.
        info = {
            "title": "Culligan - %s" % data[CONF_USERNAME],
            "dsn": ", ".join(d._dsn for d in devices),
        }
        LOGGER.debug(info)
        return info
    else:
        raise UnknownAuth(
            "An unknown error occurred. Check your region settings and open an issue on Github if the issue persists."
        )


async def async_validate_input(
    hass: core.HomeAssistant, user_input: Mapping[str, Any]
) -> tuple[dict[str, str] | None, dict[str, str]]:
    """Validate form input using email andd input validator functions."""
    LOGGER.debug("_async_validate_input")
    errors = {}
    info = None

    # _validate_email will return false if issues and nothing if OK
    email = await validate_email(hass, user_input)
    LOGGER.debug(email)
    if not email:
        errors["base"] = "must_be_email"
        return info, errors

    # noinspection PyBroadException
    try:
        info = await validate_input(hass, user_input)
    except CannotConnect:
        errors["base"] = "cannot_connect"
    except InvalidAuth:
        errors["base"] = "invalid_auth"
    except UnknownAuth:
        errors["base"] = "unknown"
    return info, errors


class CulliganFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow(s) for Culligan"""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    LOGGER.debug("In data entry flow")

    def __init__(self) -> None:
        """Initialize"""
        self._errors = {}

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=self._errors,
        )

    async def async_step_user(
        self, user_input: Optional[dict[str, Any]] | None = None
    ) -> FlowResult:
        """
        Step: User
        User initiates flow via user interface or when discovered and the discovery step is not defined
        """

        LOGGER.debug("async step user")
        self._errors = {}

        if user_input is not None:
            LOGGER.debug("Got user input")
            # info contains: title, dsn, CulliganAPI
            info, self._errors = await async_validate_input(self.hass, user_input)
            if info:
                LOGGER.debug("Got info ... checking unique_id")
                await self.async_set_unique_id(info["dsn"])
                self._abort_if_unique_id_configured()

                LOGGER.debug("DSN is unique, creating entry")
                return self.async_create_entry(
                    title="Culligan - %s" % info["dsn"],
                    data={
                        "user_input": user_input,
                        "instance": info,
                    },
                )

            LOGGER.debug("user input, but failed validation ... showing config form")
            return await self._show_config_form(user_input)

        LOGGER.debug("no user input ... showing config form")
        return await self._show_config_form(user_input)

    # async def async_step_reauth(self, user_input: Mapping[str, Any]) -> FlowResult:
    #     """Handle re-auth if login is invalid."""
    #     errors: dict[str, str] = {}
    #     LOGGER.debug("async_step_reauth")

    #     if user_input is not None:
    #         _, errors = await self._async_validate_input(user_input)

    #         if not errors:
    #             errors = {"base": "unknown"}
    #             if entry := await self.async_set_unique_id(self.unique_id):
    #                 self.hass.config_entries.async_update_entry(entry, data=user_input)
    #                 return self.async_abort(reason="reauth_successful")

    #         if errors["base"] != "invalid_auth":
    #             return self.async_abort(reason=errors["base"])

    #     return self.async_show_form(
    #         step_id="reauth",
    #         data_schema=STEP_USER_DATA_SCHEMA,
    #         errors=errors,
    #     )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get/Enable options flow for this handler"""
        return CulliganOptionsFlowHandler(config_entry)


class CulliganOptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow handler for Culligan."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry
        self._errors = None

    async def _show_options_form(self, user_input):  # pylint: disable=unused-argument
        """Show the options form to edit location and update interval. Step is always 'init'"""

        STEP_OPTION_DATA_SCHEMA = vol.Schema(
            {
                vol.Optional(
                    "update_interval",
                    default=self.config_entry.data["user_input"]["update_interval"],
                ): cv.positive_int
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=STEP_OPTION_DATA_SCHEMA,
            errors=self._errors,
        )

    async def async_step_init(
        self, user_input: Optional[dict[str, Any]] | None = None
    ) -> FlowResult:  # pylint: disable=unused-argument
        """Manage the options. First step is always init: https://developers.home-assistant.io/docs/config_entries_options_flow_handler#flow-handler."""

        LOGGER.debug("async set (options) init")
        self._errors = {}

        if user_input is not None:
            LOGGER.debug("Options flow user_input: %s", user_input)
            # value of data will be set on the options property of our config_entry

            # thanks to: https://community.home-assistant.io/t/config-flow-how-to-update-an-existing-entity/522442/7

            # We technically don't want to re-create the entity, just update the entity
            # return self.async_create_entry(
            #     title="Some options",
            #     data={
            #         "user_input": user_input,
            #     },
            # )

            # update the config entry instead of re-creating
            self.hass.config_entries.async_update_entry(
                self.config_entry, options=user_input
            )

            # return a blank config entry so the listener in __init__ can reload the integration
            return self.async_create_entry(title=None, data=None)

        return await self._show_options_form(user_input)
