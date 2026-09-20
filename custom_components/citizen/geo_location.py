"""Geo-location entities for tracked Citizen incidents.

Each tracked incident becomes a ``geo_location`` entity so it appears on
map cards and can drive proximity/distance automations. Entities are
added when incidents enter the feed and removed when they expire out.
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.location import distance as location_distance
from pycitizen import TrackedIncident

from . import CitizenConfigEntry
from .const import (
    ATTR_CATEGORY,
    ATTR_COMMENT_COUNT,
    ATTR_FIRST_SEEN,
    ATTR_HAS_VOD,
    ATTR_INCIDENT_ID,
    ATTR_LAST_SEEN,
    ATTR_LIFECYCLE_STATE,
    ATTR_SEVERITY,
    ATTR_SHARE_COUNT,
    ATTR_SUBCATEGORY,
    ATTR_VIEW_COUNT,
    DOMAIN,
)
from .coordinator import CitizenCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CitizenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up geo_location entities from the coordinator's tracked set."""
    coordinator = entry.runtime_data
    known_ids: set[str] = set()

    @callback
    def _check_for_new_incidents() -> None:
        feed_ids = set(coordinator.feed.incidents)
        # Forget ids that left the feed so a reappearing incident re-adds.
        known_ids.intersection_update(feed_ids)
        new_entities = [
            CitizenIncidentGeoLocation(coordinator, tracked)
            for incident_id, tracked in coordinator.feed.incidents.items()
            if incident_id not in known_ids and not known_ids.add(incident_id)
        ]
        if new_entities:
            async_add_entities(new_entities)

    entry.async_on_unload(coordinator.async_add_listener(_check_for_new_incidents))
    _check_for_new_incidents()


class CitizenIncidentGeoLocation(CoordinatorEntity[CitizenCoordinator], GeolocationEvent):
    """A geo_location entity tracking one Citizen incident."""

    _attr_icon = "mdi:alarm-light"
    _attr_source = "citizen"

    def __init__(self, coordinator: CitizenCoordinator, tracked: TrackedIncident) -> None:
        super().__init__(coordinator)
        self._incident_id = tracked.incident_id
        self._attr_unique_id = f"{DOMAIN}_{tracked.incident_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{coordinator.latitude}_{coordinator.longitude}")},
            "name": f"Citizen ({coordinator.latitude:.4f}, {coordinator.longitude:.4f})",
            "manufacturer": "Citizen",
        }
        self._update(tracked)

    @property
    def _tracked(self) -> TrackedIncident | None:
        return self.coordinator.feed.incidents.get(self._incident_id)

    @callback
    def _handle_coordinator_update(self) -> None:
        tracked = self._tracked
        if tracked is None:
            self.hass.async_create_task(self.async_remove(force_remove=True))
            return
        self._update(tracked)
        super()._handle_coordinator_update()

    def _update(self, tracked: TrackedIncident) -> None:
        marker = tracked.marker
        position = marker.position
        self._attr_name = marker.title or f"Incident {tracked.incident_id}"
        self._attr_latitude = position.latitude if position else None
        self._attr_longitude = position.longitude if position else None
        if position:
            self._attr_distance = location_distance(
                self.coordinator.latitude, self.coordinator.longitude,
                position.latitude, position.longitude,
            )
        else:
            self._attr_distance = None
        self._attr_extra_state_attributes = {
            ATTR_INCIDENT_ID: tracked.incident_id,
            ATTR_CATEGORY: marker.category,
            ATTR_SUBCATEGORY: marker.subcategory,
            ATTR_SEVERITY: marker.severity.value,
            ATTR_LIFECYCLE_STATE: marker.lifecycle_state.value,
            ATTR_FIRST_SEEN: tracked.first_seen.isoformat(),
            ATTR_LAST_SEEN: tracked.last_seen.isoformat(),
            ATTR_COMMENT_COUNT: marker.comment_count,
            ATTR_SHARE_COUNT: marker.share_count,
            ATTR_VIEW_COUNT: marker.view_count,
            ATTR_HAS_VOD: marker.has_vod,
            "feed_state": tracked.state.value,
        }
