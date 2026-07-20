from __future__ import annotations

from engine.spatial_plume import build_plume_geometry, destination_point


def basemap_context() -> dict:
    """SV2-3 basemap/terrain-prep configuration.

    The source point is intentionally on land in a U.S. terrain-capable test
    geography. Map tiles provide orientation only; they do not show methane.
    """
    source_seed = {
        "lat": 34.2256,
        "lon": -119.1189,
        "label": "generalized source-seeded reported signal area",
        "placement_note": "land-based U.S. terrain-capable test coordinate; not a facility claim",
    }
    wind_to_degrees = 68.0  # approximate WSW -> ENE travel direction
    plume = build_plume_geometry(source_seed, wind_to_degrees, length_km=23.0, width_km=5.8)
    downwind = destination_point(source_seed["lat"], source_seed["lon"], wind_to_degrees, 27.5)

    claim_boundary = (
        "Basemap is geographic context only; it is not methane evidence, "
        "source attribution, plume-product geometry, or emissions quantification."
    )
    return {
        "layer_id": "basemap",
        "pass_id": "SV2-3",
        "name": "Map-registered terrain-prep surface",
        "mode": "leaflet_coordinate_registered",
        "status": "live_optional_with_fallback",
        "claim_strength": "geographic_context_only",
        "provider": "Leaflet + OpenStreetMap standard tile endpoint",
        "source_label": "No-key Leaflet map surface with coordinate-registered overlays",
        "tile_url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attribution": "Map data © OpenStreetMap contributors",
        "center": {"lat": 34.260, "lon": -119.030},
        "zoom": 11,
        "display_place": "Ventura County, California terrain-prep test scene",
        "source_seed_point": source_seed,
        "downwind_context_point": {**downwind, "label": "downwind orientation context"},
        "plume_geometry": plume,
        "basemap_modes": [
            {
                "id": "standard",
                "label": "Standard map",
                "tile_url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
                "attribution": "Map data © OpenStreetMap contributors",
                "role": "orientation and public map context",
            },
            {
                "id": "topo",
                "label": "Terrain/topo prep",
                "tile_url": "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
                "attribution": "Map data © OpenStreetMap contributors, SRTM | OpenTopoMap",
                "role": "terrain-aware visual preparation only",
            },
            {
                "id": "dark_review",
                "label": "Dark review",
                "tile_url": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
                "attribution": "Map data © OpenStreetMap contributors, © CARTO",
                "role": "high-contrast review mode",
            },
        ],
        "default_mode": "topo",
        "terrain_prep": {
            "status": "prepared_for_dem_loader",
            "future_source": "USGS 3DEP / The National Map for U.S. scenes",
            "planned_outputs": ["DEM", "hillshade", "slope", "aspect", "contours", "local relief"],
            "site_note": "U.S. terrain-capable test geography selected so SV2-4 can connect a real DEM/hillshade lane.",
            "claim_boundary": "Terrain can explain physical context; it cannot prove a methane source.",
        },
        "orientation_note": "Real map tiles now provide coordinate space for the plume, source marker, wind path, and uncertainty field.",
        "fallback_note": "If web map tiles do not load, the app shows the local fallback surface and keeps the claim boundary visible.",
        "fallback": "If tiles fail, show the muted local fallback surface and keep the boundary visible.",
        "visual_recipe": [
            "source marker is placed from latitude/longitude",
            "plume centerline and uncertainty are rendered from coordinate geometry",
            "canvas animation converts map coordinates to screen coordinates each frame",
            "basemap mode selector prepares terrain/topo review without changing claims",
        ],
        "claim_boundary": claim_boundary,
        "boundary": claim_boundary,
        "not_claimed": [
            "not methane evidence",
            "not exact plume-product geometry",
            "not attribution",
            "not certified quantification",
            "not enforcement",
        ],
    }
