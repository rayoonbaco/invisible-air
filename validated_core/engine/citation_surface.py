from __future__ import annotations

from datetime import datetime, timezone


def _entry(layer_id: str, title: str, source: str, source_type: str, timestamp: str | None,
           retrieval_state: str, status: str, claim_class: str, boundary: str,
           source_url: str | None = None) -> dict:
    return {
        "layer_id": layer_id,
        "title": title,
        "source": source,
        "source_type": source_type,
        "source_url": source_url,
        "timestamp_utc": timestamp,
        "retrieval_state": retrieval_state,
        "status": status,
        "claim_class": claim_class,
        "boundary": boundary,
    }


def build_citation_surface(scene: dict) -> dict:
    """Build the compact, traceable SV2-35 citation surface.

    Entries describe where each visible layer came from, when it was retrieved or
    observed, and what it cannot establish. Missing source fields remain explicit.
    """
    obs = scene.get("observation_contract", {})
    wind = scene.get("wind", {})
    terrain = scene.get("terrain", {})
    basemap = scene.get("basemap", {})
    timing = scene.get("evidence_time", {})
    hillshade = scene.get("hillshade", {})
    stability = scene.get("atmospheric_stability", {})

    entries = [
        _entry(
            "observation", "Reported observation record",
            obs.get("provider") or "provider unresolved",
            "reported observation manifest",
            obs.get("reported_time_utc"),
            "retrieved" if obs.get("retrieved_at_utc") else "retrieval time unresolved",
            obs.get("data_state", "unknown"),
            "reported_observation_record",
            obs.get("claim_boundary", "Observation provenance only."),
            obs.get("source_url"),
        ),
        _entry(
            "wind", "Current wind context",
            wind.get("provider", "Open-Meteo current wind connector"),
            "current weather context",
            wind.get("timestamp"),
            wind.get("data_state", "unknown"),
            "current_context_only",
            "current_weather_context",
            "Current wind is not observation-time wind and cannot reconstruct the reported event.",
        ),
        _entry(
            "terrain", "Measured terrain context",
            terrain.get("provider", "USGS elevation service / local cache"),
            "measured elevation samples",
            terrain.get("retrieved_at_utc") or terrain.get("cached_at_utc"),
            terrain.get("data_state", "unknown"),
            terrain.get("data_state", "unknown"),
            "measured_geographic_context",
            "Terrain supports geographic interpretation only; it does not detect methane or prove transport.",
        ),
        _entry(
            "hillshade", "DEM-derived hillshade",
            hillshade.get("source_dem_provider") or "validated DEM cache",
            "derived terrain visualization",
            hillshade.get("generated_at_utc"),
            hillshade.get("data_state", "unknown"),
            hillshade.get("data_state", "unknown"),
            "measured_terrain_derivative",
            hillshade.get("claim_boundary", "Derived terrain context only."),
        ),
        _entry(
            "basemap", "Geographic basemap",
            basemap.get("attribution", "OpenStreetMap contributors / configured tile providers"),
            "geographic orientation context",
            None,
            "live tiles with configured fallback",
            "context",
            "geographic_context",
            "Basemap tiles provide orientation only and are not emissions evidence.",
        ),
        _entry(
            "evidence_time", "Evidence-time alignment",
            "internal temporal alignment contract",
            "derived evidence boundary",
            timing.get("current_wind_time_utc"),
            timing.get("data_state", "unknown"),
            timing.get("alignment_status", "unknown"),
            "temporal_context",
            timing.get("claim_boundary", "Current conditions cannot be substituted for event-time conditions."),
        ),
        _entry(
            "atmospheric_stability", "Atmospheric stability screen",
            stability.get("provider", "provider unresolved"),
            stability.get("source_type", "meteorological screening context"),
            stability.get("selected_time_utc"),
            stability.get("data_state", "unknown"),
            stability.get("status", "unknown"),
            "inferred_meteorological_context",
            stability.get("claim_boundary", "Stability screening only."),
            stability.get("provider_url"),
        ),
        _entry(
            "plume_visualization", "Atmospheric visual reconstruction",
            "Invisible Air scene engine",
            "map-registered visual heuristic",
            wind.get("timestamp"),
            "computed from current wind, measured terrain, and bounded visual rules",
            "visual_reconstruction",
            "visual_reconstruction",
            "The animated volume is not detected methane, exact product geometry, concentration, or a dispersion-model result.",
        ),
    ]

    complete = sum(1 for e in entries if e["source"] and e["status"] not in {"unknown", "missing"})
    return {
        "contract_version": "citation_surface_v1",
        "pass_id": "SV2-35",
        "generated_at_utc": wind.get("timestamp") or obs.get("retrieved_at_utc"),
        "entry_count": len(entries),
        "traceable_entry_count": complete,
        "status": "citation_surface_active",
        "display_label": f"{complete}/{len(entries)} visible layers traceable",
        "entries": entries,
        "claim_boundary": "Citations identify source and retrieval context; they do not certify scientific conclusions, provider endorsement, attribution, or legal responsibility.",
    }
