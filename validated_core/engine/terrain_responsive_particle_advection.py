from __future__ import annotations

from typing import Any

PASS_ID = "SV2-35"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def build_terrain_responsive_particle_advection(
    steering: dict,
    confidence: dict,
    volume: dict,
    living_wind: dict,
    gust_variability: dict,
) -> dict[str, Any]:
    """Build bounded particle-motion directives from steering evidence.

    The output controls a visual reconstruction only. It does not solve an
    atmospheric transport equation and does not represent material parcels.
    """
    field_ready = steering.get("data_state") == "terrain_steering_field_cache"
    confidence_ready = confidence.get("data_state") == "terrain_steering_confidence_cache"
    if not (field_ready and confidence_ready):
        return {
            "contract_version": "terrain_responsive_particle_advection_v1",
            "pass_id": PASS_ID,
            "mode": "terrain_responsive_particle_visual_reconstruction",
            "evidence_state": "visual_reconstruction",
            "data_state": "particle_advection_unavailable_safe",
            "status": "unavailable_safe",
            "display_label": "terrain-responsive particles unavailable · steering evidence incomplete",
            "dominant_driver": "unavailable",
            "advection_authority": 0.0,
            "coherence": 0.0,
            "crosswind_drift_px": 0.0,
            "channel_speed_multiplier": 1.0,
            "shelter_speed_multiplier": 1.0,
            "opposition_drag": 0.0,
            "deflection_oscillation_px": 0.0,
            "uncertainty_jitter_px": 0.0,
            "response_bands": [],
            "scene_directive": "Retain broad wind-following particle motion until the spatial steering field and confidence surface are ready.",
            "claim_boundary": "Particles are visual tracers, not measured methane parcels. Their motion does not represent concentration, mass, exposure, travel time, CFD, or verified atmospheric transport.",
        }

    field_stats = steering.get("field_statistics") or {}
    ratios = field_stats.get("response_ratios") or {}
    driver = field_stats.get("dominant_response") or max(ratios, key=ratios.get, default="alignment")
    strength = _clamp(field_stats.get("mean_strength", 0.0))
    conf = _clamp((confidence.get("confidence_statistics") or {}).get("mean", 0.0))
    uncertainty = _clamp((confidence.get("uncertainty_statistics") or {}).get("mean", 1.0 - conf))
    volume_authority = _clamp(volume.get("modulation_strength", 0.0) / 0.42 if volume else 0.0)
    gust_metrics = gust_variability.get("metrics") or {}
    gust_support = 0.0
    if gust_variability.get("data_state") == "gust_variability_window_cache":
        gust_support = _clamp(float(gust_metrics.get("selected_gust_factor") or 1.0) - 1.0, 0.0, 1.0)

    authority = _clamp(strength * (0.42 + 0.58 * conf) * (0.72 + 0.28 * volume_authority), 0.0, 0.46)
    coherence = _clamp(conf * (1.0 - 0.48 * uncertainty), 0.12, 0.92)
    crosswind = _clamp((ratios.get("lateral_deflection", 0.0) - ratios.get("alignment", 0.0)) * 34.0 * authority, -12.0, 12.0)
    channel_speed = _clamp(1.0 + ratios.get("channeling", 0.0) * authority * 0.70, 1.0, 1.26)
    shelter_speed = _clamp(1.0 - ratios.get("shelter", 0.0) * authority * 0.50, 0.82, 1.0)
    opposition_drag = _clamp(ratios.get("opposition", 0.0) * authority * 0.85, 0.0, 0.26)
    deflection_oscillation = _clamp(2.0 + ratios.get("lateral_deflection", 0.0) * authority * 34.0, 2.0, 9.0)
    uncertainty_jitter = _clamp(1.0 + uncertainty * 7.0 + gust_support * 2.0, 1.0, 10.0)

    # Three normalized along-path influence bands. These are visual timing
    # envelopes, not geophysical zones or travel-time estimates.
    response_bands = [
        {"start": 0.10, "end": 0.38, "driver": "alignment", "weight": round(_clamp(ratios.get("alignment", 0.0) + 0.20), 4)},
        {"start": 0.34, "end": 0.70, "driver": driver, "weight": round(_clamp(strength + 0.18), 4)},
        {"start": 0.66, "end": 0.96, "driver": "uncertainty", "weight": round(_clamp(uncertainty + 0.12), 4)},
    ]

    return {
        "contract_version": "terrain_responsive_particle_advection_v1",
        "pass_id": PASS_ID,
        "mode": "terrain_responsive_particle_visual_reconstruction",
        "evidence_state": "visual_reconstruction",
        "data_state": "terrain_responsive_particle_advection_ready",
        "status": "ready",
        "display_label": f"terrain-responsive particles · {driver.replace('_', ' ')} · {round(conf * 100)}% support",
        "dominant_driver": driver,
        "advection_authority": round(authority, 4),
        "coherence": round(coherence, 4),
        "crosswind_drift_px": round(crosswind, 2),
        "channel_speed_multiplier": round(channel_speed, 4),
        "shelter_speed_multiplier": round(shelter_speed, 4),
        "opposition_drag": round(opposition_drag, 4),
        "deflection_oscillation_px": round(deflection_oscillation, 2),
        "uncertainty_jitter_px": round(uncertainty_jitter, 2),
        "response_bands": response_bands,
        "inputs": {
            "steering_strength": round(strength, 4),
            "steering_confidence": round(conf, 4),
            "steering_uncertainty": round(uncertainty, 4),
            "volume_authority": round(volume_authority, 4),
            "gust_support": round(gust_support, 4),
            "response_ratios": ratios,
        },
        "scene_directive": "Let visual tracers respond gradually to confidence-gated alignment, channeling, shelter, opposition, lateral deflection, and downstream uncertainty. Keep motion smooth, bounded, reversible, and subordinate to the broad wind pathway.",
        "claim_boundary": "Particles are visual tracers, not measured methane parcels. Their motion does not represent concentration, mass, exposure, travel time, CFD, or verified atmospheric transport.",
    }
