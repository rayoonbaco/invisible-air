from __future__ import annotations

from typing import Any

PASS_ID = "SV2-35"

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))

def build_steering_aware_air_volume(base_volume: dict, steering: dict, confidence: dict, interaction: dict, wind: dict) -> dict[str, Any]:
    """Bound the visual air volume with spatial steering evidence.

    This is a rendering contract, not a transport or concentration model.
    """
    base = dict(base_volume or {})
    field_ready = steering.get("data_state") == "terrain_steering_field_cache"
    conf_ready = confidence.get("data_state") == "terrain_steering_confidence_cache"
    if not (field_ready and conf_ready):
        return {
            **base,
            "contract_version": "steering_aware_air_volume_v1",
            "pass_id": PASS_ID,
            "mode": "steering_aware_air_volume_visual_reconstruction",
            "data_state": "steering_aware_volume_unavailable_safe",
            "status": "unavailable_safe",
            "display_label": "steering-aware air volume unavailable · steering evidence incomplete",
            "steering_driver": "unavailable",
            "modulation_strength": 0.0,
            "confidence_support": 0.0,
            "lateral_bias_px": 0.0,
            "curve_strength": 0.0,
            "channel_compression": 1.0,
            "uncertainty_expansion": 1.0,
            "layer_asymmetry": 0.0,
            "inputs": {},
            "scene_directive": "Retain the neutral layered air volume until the steering field and its confidence surface are ready.",
            "claim_boundary": "Visual modulation and opacity do not represent measured methane concentration, plume height, mass, exact geometry, CFD, or proof of actual airflow.",
        }
    stats = steering.get("field_statistics") or {}
    ratios = stats.get("response_ratios") or {}
    driver = stats.get("dominant_response") or max(ratios, key=ratios.get, default="alignment")
    mean_strength = _clamp(stats.get("mean_strength", 0), 0, 1)
    mean_conf = _clamp((confidence.get("confidence_statistics") or {}).get("mean", 0), 0, 1)
    uncertainty = _clamp((confidence.get("uncertainty_statistics") or {}).get("mean", 1-mean_conf), 0, 1)
    interaction_score = _clamp((interaction.get("interaction_index") or interaction.get("score") or 0) / 100.0, 0, 1)
    modulation = _clamp(mean_strength * (0.45 + 0.55*mean_conf) * (0.75 + 0.25*interaction_score), 0, 0.42)
    sign = -1 if driver in {"opposition","shelter"} else 1
    lateral = sign * _clamp(4 + 26*modulation, 0, 15)
    curve = _clamp(0.08 + 0.82*modulation, 0.08, 0.42)
    compression = {"channeling":0.78,"alignment":0.90,"lateral_deflection":1.02,"opposition":1.10,"shelter":1.14}.get(driver,1.0)
    compression = _clamp(compression + (0.5-mean_conf)*0.08, 0.74, 1.18)
    expansion = _clamp(1.0 + uncertainty*0.32, 1.0, 1.32)
    asym = _clamp((ratios.get("lateral_deflection",0)-ratios.get("alignment",0))*0.7, -0.22, 0.22)
    return {
        **base,
        "contract_version": "steering_aware_air_volume_v1",
        "pass_id": PASS_ID,
        "mode": "steering_aware_air_volume_visual_reconstruction",
        "data_state": "steering_aware_air_volume_ready",
        "status": "ready",
        "display_label": f"steering-aware air volume · {driver.replace('_',' ')} · {round(mean_conf*100)}% support",
        "steering_driver": driver,
        "modulation_strength": round(modulation,4),
        "confidence_support": round(mean_conf,4),
        "uncertainty_support": round(uncertainty,4),
        "lateral_bias_px": round(lateral,2),
        "curve_strength": round(curve,4),
        "channel_compression": round(compression,4),
        "uncertainty_expansion": round(expansion,4),
        "layer_asymmetry": round(asym,4),
        "wind_basis": wind.get("data_state","unavailable"),
        "temporal_basis": interaction.get("temporal_basis","current atmospheric context only"),
        "inputs": {
            "steering_mean_strength": round(mean_strength,4),
            "steering_confidence": round(mean_conf,4),
            "steering_uncertainty": round(uncertainty,4),
            "terrain_air_interaction": round(interaction_score,4),
        },
        "scene_directive": "Use confidence-gated curvature, compression, asymmetry, and uncertainty expansion to shape the visual air volume. Keep all modulation bounded and reversible.",
        "claim_boundary": "This steering-aware air volume is a confidence-gated visual heuristic. Its shape and opacity do not represent measured methane concentration, plume height, mass, exact geometry, CFD, or proof of actual airflow.",
    }
