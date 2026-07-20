from __future__ import annotations

from engine.provenance import Provenance


def get_source_registry() -> list[dict]:
    """Registry of evidence and context layers for the SV2-15 scene engine."""
    layers = [
        Provenance(
            layer_id="citation_surface", status="active", source_label="layer-level citation and retrieval registry",
            claim_strength="software_quality_control",
            what_is_real="Each visible scientific layer carries a source label, source type, timestamp state, retrieval state, claim class, and boundary.",
            what_is_reconstruction="The compact citation surface organizes provenance already available to the app; it does not independently validate providers.",
            what_is_missing="Complete source URLs and observation timestamps remain explicit when unavailable.",
            boundary="Citations support traceability; they do not certify scientific conclusions or provider endorsement.",
        ),
        Provenance(
            layer_id="observation", status="contract_active_manifest_incomplete", source_label="provider-neutral observation evidence contract",
            claim_strength="reported_observation_record",
            what_is_real="The app preserves an observation ID, provider field, source URL field, reported time, coordinates, product type, retrieval time, geometry state, quantification state, confidence state, and missing-field list.",
            what_is_reconstruction="The scene remains source-seeded until a complete provider manifest and exact product geometry are loaded.",
            what_is_missing="Verified provider metadata, source URL, retrieval timestamp, exact product geometry, and any defensible quantification fields not explicitly supplied.",
            boundary="The observation contract is a provenance record, not a methane detection, attribution, quantification, or enforcement finding.",
        ),
        Provenance(
            layer_id="basemap", status="live_optional_with_fallback", source_label="Leaflet + OpenStreetMap / topo / dark review tile endpoints",
            claim_strength="geographic_context",
            what_is_real="The source marker, visual corridor, and uncertainty field are registered to map coordinates.",
            what_is_reconstruction="The map is visual orientation only and does not represent methane or responsibility.",
            what_is_missing="Dedicated imagery/terrain provider metadata and offline cached tiles.",
            boundary="A basemap is geographic context only; it is not methane evidence.",
        ),
        Provenance(
            layer_id="terrain", status="loader_ready_cache_pending", source_label="USGS EPQS / 3DEP-backed sample grid with local cache",
            claim_strength="context",
            what_is_real="A measured elevation sampling connector, cache contract, and terrain influence classifier are present.",
            what_is_reconstruction="Until a measured cache is loaded, no relief value is invented.",
            what_is_missing="Clipped DEM, hillshade, slope, aspect, and contours.",
            boundary="Terrain explains physical context; it does not prove methane detection or responsibility.",
        ),
        Provenance(
            layer_id="wind", status="live_current_with_cache_and_fallback", source_label="Open-Meteo current 10 m wind",
            claim_strength="current_weather_context",
            what_is_real="Current wind speed, direction, provider, retrieval state, and timestamp are connected when the provider is available.",
            what_is_reconstruction="The visual corridor is oriented by current wind but remains a map-registered reconstruction.",
            what_is_missing="Observation-time wind and a gridded atmospheric wind field.",
            boundary="Current wind is not necessarily observation-time wind and cannot identify responsibility.",
        ),
        Provenance(
            layer_id="evidence_time", status="active_boundary", source_label="observation-time versus current-weather alignment contract",
            claim_strength="temporal_context",
            what_is_real="The app separately records the reported observation-time state and the timestamp attached to current wind context.",
            what_is_reconstruction="Current wind drives only a present-day visual context layer unless event-time wind is connected.",
            what_is_missing="A verified observation timestamp and historical/event-time weather matched to that observation.",
            boundary="Current wind must not be presented as observation-time transport.",
        ),
        Provenance(
            layer_id="plume_visualization", status="animated_reconstruction", source_label="current-wind-oriented canvas reconstruction over map context",
            claim_strength="visual_reconstruction",
            what_is_real="Particles begin at the source coordinate and follow the current-wind map direction when available.",
            what_is_reconstruction="The moving corridor is not a dispersion model or product retrieval.",
            what_is_missing="Exact product geometry and time-sequenced enhancement data.",
            boundary="Animated motion is not live methane movement.",
        ),
        Provenance(
            layer_id="internal_smoke_test", status="active", source_label="offline route, contract, file, and guardrail checks",
            claim_strength="software_quality_control",
            what_is_real="Each pass now includes executable automated checks and an in-app status report.",
            what_is_reconstruction="A passing smoke test does not validate scientific accuracy or replace human visual inspection.",
            what_is_missing="Browser screenshot regression and provider integration monitoring.",
            boundary="Software checks verify expected behavior; they do not certify scientific conclusions.",
        ),
    ]
    return [layer.to_dict() for layer in layers]


def get_layer(layer_id: str) -> dict | None:
    for layer in get_source_registry():
        if layer["layer_id"] == layer_id:
            return layer
    return None
