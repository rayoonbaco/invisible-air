from __future__ import annotations


def build_living_wind(wind: dict, terrain_behavior: dict, flow_path: dict) -> dict:
    """Return bounded motion cues derived from current wind and terrain context.

    These values control visual cadence and sway only. They are not a turbulence
    measurement or atmospheric simulation.
    """
    speed = max(0.0, float(wind.get("speed_mph", 0.0)))
    turbulence = max(0.0, min(1.0, float(terrain_behavior.get("turbulence", 0.18))))
    measured = flow_path.get("data_state") == "measured_terrain_applied"
    speed_factor = max(0.55, min(1.75, 0.72 + speed / 18.0))
    gust_strength = max(0.04, min(0.22, 0.055 + speed / 140.0 + turbulence * 0.055))
    sway = max(2.5, min(13.0, 3.0 + turbulence * 6.5 + speed * 0.22))
    wake = max(0.0, min(0.28, turbulence * 0.24 + (0.05 if measured else 0.0)))
    return {
        "mode": "live_wind_responsive_visual_motion",
        "data_state": wind.get("data_state", "default_vector_fallback"),
        "speed_factor": round(speed_factor, 3),
        "cadence_multiplier": round(speed_factor, 3),
        "spacing_multiplier": round(max(0.72, min(1.28, 1.10 - speed / 90.0)), 3),
        "sway_amplitude_px": round(sway, 2),
        "gust_cycle_seconds": round(max(4.5, min(9.0, 8.2 - speed * 0.16)), 2),
        "gust_strength": round(gust_strength, 3),
        "turbulence_pockets": 3 if measured else 2,
        "terrain_wake_strength": round(wake, 3),
        "display_label": "live-wind-responsive visual motion",
        "claim_boundary": "Cadence, spacing, sway, gust pulses, and wake cues are visual responses to current wind and terrain context; they are not a measured turbulence field, observation-time wind reconstruction, or atmospheric simulation.",
    }
