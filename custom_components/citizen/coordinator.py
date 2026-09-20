"""Data update coordinator wrapping pycitizen's IncidentFeed."""

from __future__ import annotations

import asyncio
import logging
import math
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pycitizen import (
    CitizenClient,
    CitizenError,
    FeedUpdate,
    HistoricalIncident,
    IncidentFeed,
)

from .const import DEFAULT_EXPIRE_AFTER, DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


def bbox_for_radius(latitude: float, longitude: float, radius_km: float) -> tuple[float, float, float, float]:
    """Return a (west, south, east, north) bbox covering a radius in km."""
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / max(1e-6, 111.0 * math.cos(math.radians(latitude)))
    return (
        longitude - lon_delta,
        latitude - lat_delta,
        longitude + lon_delta,
        latitude + lat_delta,
    )


class CitizenCoordinator(DataUpdateCoordinator[FeedUpdate]):
    """Polls Citizen incident tiles via pycitizen's IncidentFeed."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: CitizenClient,
        latitude: float,
        longitude: float,
        radius_km: float,
        scan_interval: timedelta,
        include_historical: bool = True,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=scan_interval,
        )
        self.client = client
        self.latitude = latitude
        self.longitude = longitude
        self.radius_km = radius_km
        self.include_historical = include_historical
        self.bbox = bbox_for_radius(latitude, longitude, radius_km)
        self.feed = IncidentFeed(
            client,
            self.bbox,
            expire_after=DEFAULT_EXPIRE_AFTER,
        )
        #: Past incidents from the historical_incidents tile layer.
        self.historical: dict[str, HistoricalIncident] = {}

    async def _async_update_data(self) -> FeedUpdate:
        try:
            if self.include_historical:
                update, historical = await asyncio.gather(
                    self.feed.update(),
                    self.client.get_historical_incidents(self.bbox),
                )
                self.historical = {h.incident_id: h for h in historical}
                return update
            return await self.feed.update()
        except CitizenError as err:
            raise UpdateFailed(f"Error fetching Citizen incidents: {err}") from err
