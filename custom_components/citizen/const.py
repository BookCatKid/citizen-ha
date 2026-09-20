"""Constants for the Citizen integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "citizen"

#: Default radius (km) around the configured point.
DEFAULT_RADIUS_KM: Final = 2.0
#: Default poll interval. Citizen tiles carry Cache-Control: max-age=60,
#: so polling faster than ~60s adds no freshness.
DEFAULT_SCAN_INTERVAL: Final = timedelta(seconds=60)
#: Keep an incident entity this long after it leaves the tiles.
DEFAULT_EXPIRE_AFTER: Final = 900.0

CONF_INCLUDE_HISTORICAL: Final = "include_historical"
DEFAULT_INCLUDE_HISTORICAL: Final = True

#: How many of the nearest live incidents to fetch full v3 details for
#: (address, responding agency, update narrative). 0 disables detail fetches.
CONF_DETAIL_COUNT: Final = "detail_count"
DEFAULT_DETAIL_COUNT: Final = 5

#: MDI icon per Citizen tile category (snake_case keys from the tile layer).
CATEGORY_ICONS: Final[dict[str, str]] = {
    "fire": "mdi:fire",
    "fire_ems_activity": "mdi:fire",
    "wildfire": "mdi:fire",
    "traffic_related": "mdi:car-emergency",
    "police_related": "mdi:police-badge",
    "pursuit_search": "mdi:police-badge",
    "auto_igl_incident": "mdi:police-badge",
    "medical": "mdi:medical-bag",
    "rescue": "mdi:lifebuoy",
    "helicopter": "mdi:helicopter",
    "gun_related": "mdi:alert-octagon",
    "weapon": "mdi:alert-octagon",
    "assault_fight": "mdi:alert-octagon",
    "robbery_theft": "mdi:shield-alert",
    "harassment": "mdi:account-alert",
    "barricade": "mdi:barrier",
    "earthquake": "mdi:vibrate",
    "hurricane": "mdi:weather-hurricane",
    "weather": "mdi:weather-lightning",
    "air_quality": "mdi:smog",
    "transit": "mdi:train",
    "protest": "mdi:bullhorn",
    "community": "mdi:account-group",
    "animal_related": "mdi:paw",
    "shelter": "mdi:home-alert",
    "covid": "mdi:virus",
    "election": "mdi:vote",
    "santa": "mdi:pine-tree",
}
DEFAULT_ICON: Final = "mdi:alert-circle"

ATTR_INCIDENT_ID: Final = "incident_id"
ATTR_CATEGORY: Final = "category"
ATTR_SUBCATEGORY: Final = "subcategory"
ATTR_SEVERITY: Final = "severity"
ATTR_LIFECYCLE_STATE: Final = "lifecycle_state"
ATTR_FIRST_SEEN: Final = "first_seen"
ATTR_LAST_SEEN: Final = "last_seen"
ATTR_COMMENT_COUNT: Final = "comment_count"
ATTR_SHARE_COUNT: Final = "share_count"
ATTR_VIEW_COUNT: Final = "view_count"
ATTR_HAS_VOD: Final = "has_vod"
