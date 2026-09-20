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
