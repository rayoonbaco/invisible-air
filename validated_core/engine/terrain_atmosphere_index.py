from __future__ import annotations

from typing import Any

PASS_ID = "SV2-35"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _band(score: float) -> str:
    if score >= 0.80:
        return "high"
    if score >= 0.62:
        return "moderate-high"
    if score >= 0.42:
        return "moderate"
    if score >= 0.22:
        return "low-moderate"
    return "low"


def _ratio(distribution: dict[str, Any], *labels: str) -> float:
    return sum(float((distribution.get(label) or {}).get("ratio", 0.0)) for label in labels)


def _vertical_mixing(stability: dict, boundary: dict) -> dict:
    if stability.get("data_state") != "atmospheric_stability_screen":
        return {"status": "unavailable_safe", "score": None, "band": "unavailable", "reason": "Observation-time atmospheric stability is unavailable."}
    if boundary.get("data_state") != "boundary_layer_depth_cache":
        return {"status": "unavailable_safe", "score": None, "band": "unavailable", "reason": "Observation-time boundary-layer depth is unavailable."}
    stability_class = stability.get("stability_class", "unknown")
    depth = float(boundary.get("boundary_layer_height_m") or 0.0)
    stability_score = {"unstable": 0.82, "neutral": 0.54, "stable": 0.24}.get(stability_class, 0.0)
    depth_score = _clamp(depth / 1800.0)
    score = _clamp(0.60 * stability_score + 0.40 * depth_score)
    return {
        "status": "available", "score": round(score, 4), "band": _band(score),
        "reason": f"{stability_class} stability screen with {depth:.0f} m model-derived boundary-layer depth.",
    }


def terrain_atmosphere_index_context(terrain: dict, landforms: dict, terrain_confidence: dict, wind: dict, stability: dict, boundary: dict, variability: dict) -> dict:
    base = {
        "contract_version": "terrain_atmosphere_interaction_index_v1",
        "pass_id": PASS_ID,
        "layer": "terrain_atmosphere_interaction_index",
        "evidence_state": "inferred",
        "method": "bounded weighted synthesis of DEM-derived landform proportions, terrain confidence, and available atmospheric context",
        "claim_boundary": "The Terrain-Atmosphere Interaction Index is a reproducible evidence synthesis describing how measured terrain may interact with available atmospheric context. It is not a plume-dispersion model, methane transport simulation, concentration estimate, source attribution, emissions quantification, or proof of actual airflow behavior.",
    }
    stats = landforms.get("statistics") or {}
    distribution = stats.get("classification_distribution") or {}
    terrain_ready = landforms.get("data_state") == "dem_derived_landform_cache" and terrain_confidence.get("data_state") == "terrain_confidence_ready"
    wind_ready = wind.get("data_state") in {"live_current_conditions", "stale_cached_current_conditions", "default_vector_fallback"}
    if not terrain_ready or not wind_ready or not distribution:
        base.update({
            "data_state": "interaction_index_unavailable_safe", "status": "unavailable_safe",
            "interaction_index": None, "interaction_band": "unavailable", "confidence_score": 0.0,
            "confidence_band": "unresolved", "components": {},
            "temporal_basis": "unresolved",
            "display_label": "terrain-atmosphere interaction unavailable · required terrain or wind context missing",
            "scene_directive": "Keep terrain-atmosphere synthesis visually neutral until measured terrain and atmospheric context are available.",
        })
        return base

    ridge = _ratio(distribution, "ridge", "spur", "shoulder", "upper slope")
    channel = _ratio(distribution, "valley", "drainage", "saddle")
    shelter_forms = _ratio(distribution, "valley", "drainage", "basin", "lower slope")
    exposed_forms = _ratio(distribution, "ridge", "spur", "shoulder", "upper slope")
    relief = float(terrain.get("relief_m") or terrain.get("sampled_relief_m") or 0.0)
    relief_signal = _clamp(relief / 1000.0)
    wind_speed = float(wind.get("speed_mph") or 0.0)
    wind_signal = _clamp(wind_speed / 25.0)
    terrain_quality = _clamp(float(terrain_confidence.get("overall_score") or 0.0))

    steering = _clamp(0.42 * relief_signal + 0.30 * channel + 0.18 * ridge + 0.10 * wind_signal)
    shelter = _clamp(0.62 * shelter_forms + 0.25 * relief_signal + 0.13 * (1.0 - wind_signal))
    channeling = _clamp(0.72 * channel + 0.18 * relief_signal + 0.10 * wind_signal)
    exposure = _clamp(0.72 * exposed_forms + 0.18 * wind_signal + 0.10 * relief_signal)
    mixing = _vertical_mixing(stability, boundary)

    components = {
        "terrain_steering": {"score": round(steering,4), "band": _band(steering), "basis": "relief, channel landforms, exposed landforms, and current wind speed"},
        "terrain_shelter": {"score": round(shelter,4), "band": _band(shelter), "basis": "valley, drainage, basin, lower-slope prevalence and relief"},
        "channeling_potential": {"score": round(channeling,4), "band": _band(channeling), "basis": "valley, drainage, saddle prevalence and relief"},
        "ridge_exposure": {"score": round(exposure,4), "band": _band(exposure), "basis": "ridge, spur, shoulder, upper-slope prevalence and wind context"},
        "vertical_mixing_opportunity": mixing,
    }
    weighted = [(steering,0.30),(shelter,0.20),(channeling,0.20),(exposure,0.15)]
    if mixing.get("score") is not None:
        weighted.append((float(mixing["score"]),0.15))
    total_weight=sum(w for _,w in weighted)
    composite=sum(v*w for v,w in weighted)/total_weight
    temporal_complete = mixing.get("score") is not None and variability.get("data_state") == "gust_variability_window_cache"
    confidence = _clamp(0.70 * terrain_quality + 0.20 * (1.0 if wind.get("data_state")=="live_current_conditions" else 0.65) + 0.10 * (1.0 if temporal_complete else 0.35), 0.0, 0.90)
    temporal_basis = "observation_time_atmospheric_context" if temporal_complete else "current_atmospheric_context_only"
    base.update({
        "data_state": "terrain_atmosphere_interaction_index", "status": "ready",
        "interaction_index": round(composite*100,1), "interaction_band": _band(composite),
        "confidence_score": round(confidence,2), "confidence_band": "strong" if confidence>=0.8 else "moderate" if confidence>=0.62 else "limited",
        "components": components, "temporal_basis": temporal_basis,
        "input_summary": {"terrain_confidence": round(terrain_quality,4), "sampled_relief_m": round(relief,1), "wind_speed_mph": round(wind_speed,1), "wind_state": wind.get("data_state"), "landform_mean_confidence": stats.get("mean_confidence")},
        "display_label": f"{_band(composite)} interaction · {composite*100:.0f}/100 · {temporal_basis.replace('_',' ')}",
        "scene_directive": "Use the index as a transparent review synthesis. Keep actual plume transport, concentration, and source responsibility unclaimed.",
    })
    return base
