# Citizen — Home Assistant integration

<img src="custom_components/citizen/logo.png" alt="Citizen" width="360">

Unofficial Home Assistant custom integration for [Citizen](https://citizen.com)'s **public, unauthenticated** incident feed, built on [`pycitizen`](https://github.com/BookCatKid/pycitizen).

> **Status: experimental.** Not affiliated with Citizen. Uses undocumented public endpoints that may change or become restricted at any time.

## What you get

- **`geo_location` entity per incident** — every incident inside your watched area appears on map cards with distance, severity, lifecycle state, and view/comment/share counts. Entities are added as incidents appear and removed when they expire.
- **Historical incidents** — older incidents from Citizen's separate `historical_incidents` tile layer appear as their own entities under a `citizen_historical` source (toggleable in config), so live and past incidents stay distinguishable on maps.
- **`sensor.citizen_incidents`** — count of active incidents in the area, with per-severity/per-lifecycle breakdowns and the 10 nearest incidents as attributes.
- **`sensor.citizen_nearest_incident`** — distance (km) to the nearest incident, with its title/severity as attributes. Ideal for proximity automations.

## Live vs. past incidents

The integration exposes **two separate map sources**:

| Source | What it contains |
|---|---|
| `citizen` | Whatever the live incident tiles currently return — active incidents plus recently-resolved ones still inside the server's recency window. Not strictly "live only", but not deep history either. |
| `citizen_historical` | Past incidents from the app's separate historical tile layer (past ~7 days at the time of writing — coverage and window are server-controlled and not guaranteed). |

Historical entities are named `… (time_frame)` (e.g. *"Car Accident (168)"* where `168` is the hours-old window) and use `mdi:history`, so they're easy to tell apart. An incident appearing in both layers is shown once, as live.

## Install

### HACS (custom repository)

1. HACS → ⋮ → **Custom repositories** → add `https://github.com/BookCatKid/citizen-ha` (type: *Integration*)
2. Install **Citizen** → restart Home Assistant

### Manual

Copy `custom_components/citizen` into your HA `config/custom_components/` and restart.

## Configure

**Settings → Devices & services → Add integration → Citizen**

| Field | Default | Notes |
|---|---|---|
| Latitude / Longitude | your HA home location | point to watch |
| Radius | 2 km | 0.1–50 km |
| Update interval | 60 s | Citizen tiles are cached ~60 s server-side; faster polling adds little |
| Include past incidents | on | adds the `citizen_historical` map source |

## Example automation

```yaml
alias: Alert on nearby Citizen incident
triggers:
  - trigger: numeric_state
    entity_id: sensor.citizen_nearest_incident
    below: 0.5
actions:
  - action: notify.notify
    data:
      title: "Citizen alert nearby"
      message: >-
        {{ state_attr('sensor.citizen_nearest_incident', 'title') }}
        ({{ states('sensor.citizen_nearest_incident') }} km)
mode: queued
```

Show incidents on a map card — pick either or both sources:

```yaml
type: map
geo_location_sources:
  - citizen            # live + recently resolved
  - citizen_historical # past incidents (omit for live-only)
```

## How it works

The official Citizen app renders its map from public Mapbox vector tiles at `data.sp0n.io/v1/tile/incidents/{x}/{y}/{z}.pbf` — no authentication required (verified by reverse-engineering the Android app; see `research/CITIZEN_API_REPORT.md` in the pycitizen repo). `pycitizen` decodes those tiles, deduplicates markers, and tracks lifecycle transitions; this integration polls that feed on your configured interval.

There is no public push channel — **polling the tiles is the real-time mechanism**, matching what the app itself does.

## Attribution & legal

- Incident data: Citizen App, Inc. — this project is unofficial and unaffiliated.
- Icon/logo: original artwork made for this integration.

## License

MIT — see [LICENSE](LICENSE).
