from __future__ import annotations

from engine.scene_config import default_scene_config
from engine.terrain_loader import terrain_context


def build_evidence_packet() -> dict:
    scene = default_scene_config()
    terrain = terrain_context(scene)
    scene["terrain"] = terrain
    return {
        "scene_id": scene["scene_id"],
        "summary": "A source-seeded reported methane observation now has a formal provider-neutral evidence contract. Current wind remains separate from unresolved observation-time weather, and missing source metadata stays explicit.",
        "what_is_real_now": [
            "current 10 m wind speed, direction, timestamp, and provider when Open-Meteo is available",
            "a formal observation evidence contract preserving identity, provider, source, time, coordinates, product type, and missing fields",
            "an explicit evidence-time alignment contract separating current wind from the reported observation",
            "fifteen-minute wind cache with stale-cache and default-vector fallback states",
            "visual corridor geometry rebuilt from the scene wind-to direction",
            "source marker, centerline, and uncertainty field tied to latitude/longitude",
            "terrain loader and measured-elevation cache path",
            "internal automated pass checks available from RUN_SMOKE_TESTS.bat and /self-test",
        ],
        "what_is_placeholder": [
            "observation-time wind until historical weather is connected",
            "measured terrain values until the terrain refresh succeeds",
            "exact methane product geometry until an actual source product is loaded",
            "atmospheric dispersion behavior beyond a visual directional reconstruction",
        ],
        "next_real_layers": [
            "make measured terrain visibly influence corridor width and uncertainty",
            "connect observation-time weather separately from current wind",
            "prepare an exact observation-source manifest",
        ],
        "observation_contract": scene["observation_contract"],
        "wind_lane": scene["wind"],
        "evidence_time_alignment": scene["evidence_time"],
        "map_surface": scene["basemap"],
        "plume_geometry": scene["plume_visualization"]["geometry"],
        "terrain_prep": scene["basemap"]["terrain_prep"],
        "terrain_lane": terrain,
        "boundaries": scene["boundary_pack"],
        "layers": scene["source_registry"],
    }
