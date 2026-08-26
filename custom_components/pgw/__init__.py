"""The Philadelphia Gas Works (PGW) integration."""

from __future__ import annotations

from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import PLATFORMS
from .coordinator import PGWConfigEntry, PGWCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: PGWConfigEntry) -> bool:
    """Set up PGW from a config entry."""
    coordinator = PGWCoordinator(
        hass,
        entry,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PGWConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
