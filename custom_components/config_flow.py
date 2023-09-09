"""Config Flow for Culligan integration"""

import aiohttp
import asyncio
import async_timeout
from collections.abc import Mapping
from culligan import CulliganApi, CulliganAuthError

from homeassistant import config_entries, core, exceptions
from homeassistant.core import callback
from homeassistant.const import CONF_PASSWORD, CONF_REGION, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from typing import Any, Dict, Optional

import voluptuous as vol

from .const import (
    API_TIMEOUT,
    AYLA_REGION_EU,
    AYLA_REGION_DEFAULT,
    AYLA_REGION_OPTIONS,
    CULLIGAN_APP_ID,
    DOMAIN,
    LOGGER,
    PLATFORMS,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): selector.TextSelector(
            selector.TextSelectorConfig(
                type=selector.TextSelectorType.EMAIL, autocomplete="username"
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
    }
)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""


class UnknownAuth(exceptions.HomeAssistantError):
    """Error to indicate there is an uncaught auth error."""


async def _validate_input(
    hass: core.HomeAssistant, data: Mapping[str, Any]
) -> dict[str, str]:
    """Actually test the user input allows us to connect."""

    LOGGER.debug("_validate_input")
    culligan = CulliganApi(
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        app_id=CULLIGAN_APP_ID,
        websession=async_get_clientsession(hass),
    )

    # Keep this section of error handling even though culligan v1.0.0 signs in SYNCHRONOUSLY upon __init__
    # Culligan should change ... OPTIONAL sign in on __init__ to play nice with async libraries

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

    devices = await culligan.Ayla.async_get_devices()
    # Return info that you want to store in the config entry.
    return {"title": data[CONF_USERNAME], "dsn": devices[0]._dsn}


class CulliganFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    # @config_entries.HANDLERS.register(DOMAIN)
    # class CulliganWaterSoftenerConfigFlow(data_entry_flow.FlowHandler):
    """Handle config flow(s) for Culligan"""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    LOGGER.debug("In data entry flow")

    def __init__(self):
        """Initialize"""
        self._errors = {}

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=self._errors,
        )

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] | None = None
    ):  # -> FlowResult:
        """
        Step: User
        User initiates flow via user interface or when discovered and the discovery step is not defined
        """
        LOGGER.debug("async step user")
        errors: Dict[str, str] = {}
        if user_input is not None:
            LOGGER.debug("Got user input")
            info, errors = await self._async_validate_input(user_input)
            if info:
                await self.async_set_unique_id(info["dsn"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Culligan - {info['dsn']}", data=self
                )
            else:
                return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

        # return self.async_show_form(
        #     step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        # )

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

    async def _async_validate_input(
        self, user_input: Mapping[str, Any]
    ) -> tuple[dict[str, str] | None, dict[str, str]]:
        """Validate form input."""
        LOGGER.debug("_async_validate_input")
        errors = {}
        info = None

        # noinspection PyBroadException
        try:
            info = await _validate_input(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except UnknownAuth:
            errors["base"] = "unknown"
        return info, errors

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return CulliganOptionsFlowHandler(config_entry)


class CulliganOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for Culligan."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_USERNAME), data=self.options
        )
