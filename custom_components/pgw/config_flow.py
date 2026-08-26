"""Config flow for PGW integration."""

from __future__ import annotations

from typing import Any

import aiohttp
import voluptuous as vol
from pgw_api import PGWApiClient, PGWAuthError, PGWConnectionError

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class PGWConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PGW."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors: dict[str, str] = {}

        await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
        self._abort_if_unique_id_configured()

        client = PGWApiClient(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
        session = async_get_clientsession(self.hass)

        jar = aiohttp.CookieJar()
        timeout = aiohttp.ClientTimeout(total=60)

        try:
            async with aiohttp.ClientSession(
                connector=session.connector,
                connector_owner=False,
                cookie_jar=jar,
                timeout=timeout,
            ) as pgw_session:
                await client.async_validate_credentials(pgw_session)
        except PGWAuthError:
            errors["base"] = "invalid_auth"
        except (PGWConnectionError, aiohttp.ClientError):
            errors["base"] = "cannot_connect"
        except Exception:  # noqa: BLE001
            errors["base"] = "unknown"

        if errors:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
            )

        return self.async_create_entry(
            title="PGW Gas",
            data=user_input,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauth when credentials expire."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reauth confirmation."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors: dict[str, str] = {}

        client = PGWApiClient(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
        session = async_get_clientsession(self.hass)

        jar = aiohttp.CookieJar()
        timeout = aiohttp.ClientTimeout(total=60)

        try:
            async with aiohttp.ClientSession(
                connector=session.connector,
                connector_owner=False,
                cookie_jar=jar,
                timeout=timeout,
            ) as pgw_session:
                await client.async_validate_credentials(pgw_session)
        except PGWAuthError:
            errors["base"] = "invalid_auth"
        except (PGWConnectionError, aiohttp.ClientError):
            errors["base"] = "cannot_connect"
        except Exception:  # noqa: BLE001
            errors["base"] = "unknown"

        if errors:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=STEP_USER_DATA_SCHEMA,
                errors=errors,
            )

        reauth_entry = self._get_reauth_entry()
        return self.async_update_reload_and_abort(
            reauth_entry, data=user_input
        )
