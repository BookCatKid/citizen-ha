# Citizen — Home Assistant integration

<img src="custom_components/citizen/logo.png" alt="Citizen" width="360">

Unofficial Home Assistant custom integration for [Citizen](https://citizen.com)'s **public, unauthenticated** incident feed, built on [`pycitizen`](https://github.com/BookCatKid/pycitizen).

> **Status: experimental.** Not affiliated with Citizen. Uses undocumented public endpoints that may change or become restricted at any time.

## What you get

- **`geo_location` entity per incident** — every incident inside your watched area appears on map cards with distance, severity, lifecycle state, and view/comment/share counts. Entities are added as incidents appear and removed when they expire.
- **`sensor.citizen_incidents`** — count of active incidents in the area, with per-severity/per-lifecycle breakdowns and the 10 nearest incidents as attributes.
- **`sensor.citizen_nearest_incident`** — distance (km) to the nearest incident, with its title/severity as attributes. Ideal for proximity automations.

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

Or show live incidents on a map card:

```yaml
type: map
entities:
  - entity: sensor.citizen_incidents  # shows all geo_location entities under the device
geo_location_sources:
  - citizen
```

## How it works

The official Citizen app renders its map from public Mapbox vector tiles at `data.sp0n.io/v1/tile/incidents/{x}/{y}/{z}.pbf` — no authentication required (verified by reverse-engineering the Android app; see `research/CITIZEN_API_REPORT.md` in the pycitizen repo). `pycitizen` decodes those tiles, deduplicates markers, and tracks lifecycle transitions; this integration polls that feed on your configured interval.

There is no public push channel — **polling the tiles is the real-time mechanism**, matching what the app itself does.

## Attribution & legal

- Incident data: Citizen App, Inc. — this project is unofficial and unaffiliated.
- Icon/logo: original artwork made for this integration.

## License

MIT — see [LICENSE](LICENSE).
