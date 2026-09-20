"""Summary sensors for the Citizen incident feed."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.location import distance as location_distance

from . import CitizenConfigEntry
from .const import DOMAIN
from .coordinator import CitizenCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: CitizenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Citizen summary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            CitizenIncidentCountSensor(coordinator),
            CitizenNearestIncidentSensor(coordinator),
        ]
    )


class _CitizenBaseSensor(CoordinatorEntity[CitizenCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: CitizenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{coordinator.latitude}_{coordinator.longitude}")},
            "name": f"Citizen ({coordinator.latitude:.4f}, {coordinator.longitude:.4f})",
            "manufacturer": "Citizen",
        }

    def _distance_km(self, tracked) -> float | None:
        position = tracked.marker.position
        if position is None:
            return None
        return location_distance(
            self.coordinator.latitude, self.coordinator.longitude,
            position.latitude, position.longitude,
        )


class CitizenIncidentCountSensor(_CitizenBaseSensor):
    """Number of incidents currently reported inside the watched area."""

    _attr_name = "Incidents"
    _attr_icon = "mdi:alarm-light"
    _attr_native_unit_of_measurement = "incidents"
    _attr_state_class = "measurement"

    def __init__(self, coordinator: CitizenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.latitude}_{coordinator.longitude}_incidents"

    @property
    def native_value(self) -> int:
        return len(self.coordinator.feed.active_incidents())

    @property
    def extra_state_attributes(self) -> dict:
        feed = self.coordinator.feed
        active = feed.active_incidents()
        by_severity: dict[str, int] = {}
        by_lifecycle: dict[str, int] = {}
        for tracked in active:
            sev = tracked.marker.severity.value
            life = tracked.marker.lifecycle_state.value
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_lifecycle[life] = by_lifecycle.get(life, 0) + 1
        incidents = [
            {
                "incident_id": t.incident_id,
                "title": t.marker.title,
                "severity": t.marker.severity.value,
                "lifecycle_state": t.marker.lifecycle_state.value,
                "distance_km": round(d, 3) if (d := self._distance_km(t)) is not None else None,
            }
            for t in active[:10]
        ]
        return {
            "radius_km": self.coordinator.radius_km,
            "by_severity": by_severity,
            "by_lifecycle": by_lifecycle,
            "incidents": incidents,
            "last_update": feed.last_update.isoformat() if feed.last_update else None,
        }


class CitizenNearestIncidentSensor(_CitizenBaseSensor):
    """Distance (km) to the nearest reported incident."""

    _attr_name = "Nearest incident"
    _attr_icon = "mdi:map-marker-distance"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = "measurement"

    def __init__(self, coordinator: CitizenCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_{coordinator.latitude}_{coordinator.longitude}_nearest"

    @property
    def _nearest(self):
        best = None
        best_distance = None
        for tracked in self.coordinator.feed.active_incidents():
            d = self._distance_km(tracked)
            if d is not None and (best_distance is None or d < best_distance):
                best, best_distance = tracked, d
        return best, best_distance

    @property
    def native_value(self) -> float | None:
        _, best_distance = self._nearest
        return round(best_distance, 3) if best_distance is not None else None

    @property
    def extra_state_attributes(self) -> dict:
        nearest, _ = self._nearest
        if nearest is None:
            return {}
        marker = nearest.marker
        return {
            "incident_id": nearest.incident_id,
            "title": marker.title,
            "severity": marker.severity.value,
            "lifecycle_state": marker.lifecycle_state.value,
        }
