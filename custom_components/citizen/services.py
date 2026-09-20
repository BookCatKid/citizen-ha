"""Service actions for ad-hoc Citizen queries from automations.

Both actions return response data (``response_variable``) so automations
and scripts can consume results directly.
"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util.location import distance as location_distance
from pycitizen import CitizenError, Incident, IncidentMarker

from .const import DOMAIN
from .coordinator import CitizenCoordinator, bbox_for_radius

SERVICE_GET_INCIDENT = "get_incident"
SERVICE_GET_INCIDENTS = "get_incidents"

SCHEMA_GET_INCIDENT = vol.Schema({vol.Required("incident_id"): cv.string})

SCHEMA_GET_INCIDENTS = vol.Schema(
    {
        vol.Optional("latitude"): cv.latitude,
        vol.Optional("longitude"): cv.longitude,
        vol.Optional("radius_km", default=2.0): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=50.0)
        ),
        vol.Optional("include_historical", default=False): cv.boolean,
    }
)


def _coordinator(hass: HomeAssistant) -> CitizenCoordinator:
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.state is ConfigEntryState.LOADED and entry.runtime_data:
            return entry.runtime_data
    raise ServiceValidationError("No loaded Citizen config entries")


def _incident_to_dict(i: Incident) -> dict:
    loc = i.location_details or {}
    return {
        "incident_id": i.incident_id,
        "title": i.title,
        "latitude": i.position.latitude if i.position else None,
        "longitude": i.position.longitude if i.position else None,
        "location": i.location,
        "address": loc.get("formattedAddress") or i.address,
        "neighborhood": i.neighborhood,
        "city_code": i.city_code,
        "category": i.category,
        "severity": i.severity.value,
        "lifecycle_state": i.lifecycle_state.value,
        "lifecycle_subtitle": i.raw.get("lifecycleStateSubtitle"),
        "responding_agency": loc.get("police"),
        "timestamp": i.timestamp.isoformat() if i.timestamp else None,
        "created": i.created.isoformat() if i.created else None,
        "closed": i.closed,
        "confirmed": i.confirmed,
        "users_notified": i.stats.users_notified if i.stats else None,
        "stats": {
            "views": i.stats.views,
            "shares": i.stats.shares,
            "comments": i.stats.comments,
        }
        if i.stats
        else None,
        "updates": [
            {
                "text": u.text,
                "timestamp": u.timestamp.isoformat() if u.timestamp else None,
                "author": (u.author or {}).get("displayName"),
                "pinned": u.pinned,
            }
            for u in i.updates
        ],
        "thumbnail": i.map_thumbnail,
    }


def _marker_to_dict(
    m: IncidentMarker, origin_lat: float, origin_lon: float
) -> dict:
    pos = m.position
    return {
        "incident_id": m.incident_id,
        "title": m.title,
        "latitude": pos.latitude if pos else None,
        "longitude": pos.longitude if pos else None,
        "distance_km": (
            round(
                location_distance(
                    origin_lat, origin_lon, pos.latitude, pos.longitude
                )
                / 1000,
                3,
            )
            if pos
            else None
        ),
        "category": m.category,
        "subcategory": m.subcategory,
        "severity": m.severity.value,
        "lifecycle_state": m.lifecycle_state.value,
        "timestamp": m.timestamp.isoformat() if m.timestamp else None,
        "view_count": m.view_count,
        "comment_count": m.comment_count,
        "share_count": m.share_count,
        "has_vod": m.has_vod,
    }


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register Citizen service actions (idempotent)."""
    if hass.services.has_service(DOMAIN, SERVICE_GET_INCIDENT):
        return

    async def _get_incident(call: ServiceCall) -> ServiceResponse:
        coordinator = _coordinator(hass)
        incident_id = call.data["incident_id"]
        try:
            incident = await coordinator.client.get_incident(incident_id)
        except CitizenError as err:
            raise HomeAssistantError(
                f"Citizen request failed for {incident_id}: {err}"
            ) from err
        return {"incident": _incident_to_dict(incident)}

    async def _get_incidents(call: ServiceCall) -> ServiceResponse:
        coordinator = _coordinator(hass)
        lat = call.data.get("latitude", coordinator.latitude)
        lon = call.data.get("longitude", coordinator.longitude)
        radius_km = call.data["radius_km"]
        bbox = bbox_for_radius(lat, lon, radius_km)
        try:
            markers = await coordinator.client.get_incident_markers(bbox)
            historical = (
                await coordinator.client.get_historical_incidents(bbox)
                if call.data["include_historical"]
                else []
            )
        except CitizenError as err:
            raise HomeAssistantError(f"Citizen request failed: {err}") from err
        incidents = [_marker_to_dict(m, lat, lon) for m in markers]
        live_ids = {i["incident_id"] for i in incidents}
        incidents += [
            {
                "incident_id": h.incident_id,
                "title": h.title,
                "latitude": h.position.latitude if h.position else None,
                "longitude": h.position.longitude if h.position else None,
                "distance_km": (
                    round(
                        location_distance(
                            lat,
                            lon,
                            h.position.latitude,
                            h.position.longitude,
                        )
                        / 1000,
                        3,
                    )
                    if h.position
                    else None
                ),
                "historical": True,
                "time_frame": h.time_frame,
            }
            for h in historical
            if h.incident_id not in live_ids
        ]
        incidents.sort(
            key=lambda i: i["distance_km"] if i["distance_km"] is not None else 9e9
        )
        return {"incidents": incidents, "count": len(incidents)}

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_INCIDENT,
        _get_incident,
        SCHEMA_GET_INCIDENT,
        supports_response=SupportsResponse.ONLY,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_INCIDENTS,
        _get_incidents,
        SCHEMA_GET_INCIDENTS,
        supports_response=SupportsResponse.ONLY,
    )


@callback
def async_remove_services(hass: HomeAssistant, unloading_entry_id: str) -> None:
    """Remove service actions once no other entries remain loaded."""
    if any(
        e.state is ConfigEntryState.LOADED and e.entry_id != unloading_entry_id
        for e in hass.config_entries.async_entries(DOMAIN)
    ):
        return
    hass.services.async_remove(DOMAIN, SERVICE_GET_INCIDENT)
    hass.services.async_remove(DOMAIN, SERVICE_GET_INCIDENTS)
