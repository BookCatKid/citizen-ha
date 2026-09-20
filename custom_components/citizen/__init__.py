"""The Citizen integration — public incident feed via pycitizen."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_RADIUS,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pycitizen import CitizenClient

from .const import DEFAULT_RADIUS_KM, DEFAULT_SCAN_INTERVAL
from .coordinator import CitizenCoordinator

PLATFORMS: list[Platform] = [Platform.GEO_LOCATION, Platform.SENSOR]

type CitizenConfigEntry = ConfigEntry[CitizenCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: CitizenConfigEntry) -> bool:
    """Set up Citizen from a config entry."""
    client = CitizenClient(session=async_get_clientsession(hass))
    scan_seconds = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL.total_seconds())
    coordinator = CitizenCoordinator(
        hass,
        entry,
        client,
        latitude=entry.data[CONF_LATITUDE],
        longitude=entry.data[CONF_LONGITUDE],
        radius_km=entry.data.get(CONF_RADIUS, DEFAULT_RADIUS_KM),
        scan_interval=timedelta(seconds=scan_seconds),
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: CitizenConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
