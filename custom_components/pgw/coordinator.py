"""DataUpdateCoordinator for the PGW integration."""

from __future__ import annotations

from datetime import timedelta

import aiohttp
from pgw_api import GasUsage, PGWApiClient, PGWAuthError, PGWConnectionError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import LOGGER, SCAN_INTERVAL_HOURS

type PGWConfigEntry = ConfigEntry["PGWCoordinator"]


class PGWCoordinator(DataUpdateCoordinator[list[GasUsage]]):
    """Coordinator for PGW usage data."""

    config_entry: PGWConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: PGWConfigEntry,
        username: str,
        password: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name="PGW Gas Usage",
            update_interval=timedelta(hours=SCAN_INTERVAL_HOURS),
        )
        self._client = PGWApiClient(username, password)

    async def _async_update_data(self) -> list[GasUsage]:
        """Fetch data from PGW."""
        session = async_get_clientsession(self.hass)

        # Use a separate cookie jar so PGW cookies don't leak into other integrations
        jar = aiohttp.CookieJar()
        connector = session.connector
        timeout = aiohttp.ClientTimeout(total=60)

        async with aiohttp.ClientSession(
            connector=connector, connector_owner=False, cookie_jar=jar, timeout=timeout
        ) as pgw_session:
            try:
                return await self._client.async_get_usage(pgw_session)
            except PGWAuthError as err:
                raise ConfigEntryAuthFailed(str(err)) from err
            except PGWConnectionError as err:
                raise UpdateFailed(f"Error communicating with PGW: {err}") from err
