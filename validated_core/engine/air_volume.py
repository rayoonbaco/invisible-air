from __future__ import annotations


def build_air_volume(terrain_behavior: dict, flow_path: dict) -> dict:
    """Return bounded visual-volume parameters for a non-quantitative air reconstruction."""
    turbulence = max(0.0, min(1.0, float(terrain_behavior.get("turbulence", 0.18))))
    measured = flow_path.get("data_state") == "measured_terrain_applied"
    return {
        "mode": "layered_air_volume_visual_reconstruction",
        "data_state": "terrain_informed_visual_volume" if measured else "neutral_visual_volume",
        "core_opacity": round(0.20 + turbulence * 0.05, 3),
        "mid_opacity": round(0.105 + turbulence * 0.035, 3),
        "haze_opacity": round(0.055 + turbulence * 0.02, 3),
        "edge_falloff": 0.82,
        "vertical_layer_count": 3,
        "vertical_offset_px": round(5.0 + turbulence * 5.0, 2),
        "particle_scale_growth": 4.2,
        "continuity": "layered core, middle body, and diffuse outer haze",
        "display_label": "layered air volume · visual reconstruction",
        "claim_boundary": "Opacity, density, and layering are visual devices for human review; they do not represent measured methane concentration, vertical plume height, mass, or exact plume geometry.",
    }
