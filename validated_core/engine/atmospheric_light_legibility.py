from __future__ import annotations
from typing import Any

PASS_ID = "SV2-49"


def _clamp(value: Any, low: float, high: float) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = low
    return max(low, min(high, value))


def atmospheric_light_legibility_context(scene: dict) -> dict[str, Any]:
    focus = scene.get("evidence_guided_focus_depth") or {}
    camera = scene.get("scientific_cinematic_camera") or {}
    authority = scene.get("integrated_response_authority") or {}
    regime_conf = scene.get("terrain_regime_confidence") or {}
    terrain_conf = scene.get("terrain_confidence") or {}

    ready = focus.get("data_state") == "evidence_guided_focus_depth_ready"
    if not ready:
        return {
            "contract_version": "atmospheric_light_legibility_v1",
            "pass_id": PASS_ID,
            "layer": "atmospheric_light_legibility",
            "evidence_state": "inferred",
            "data_state": "atmospheric_light_legibility_unavailable_safe",
            "status": "unavailable_safe",
            "display_label": "atmospheric lighting unavailable · focus composition missing",
            "lighting_authority": 0.0,
            "lighting_mode": "neutral_review_light",
            "legibility_scores": {"terrain": 1.0, "air_volume": 1.0, "confidence": 1.0, "uncertainty": 1.0},
            "visual_directives": {
                "terrain_shadow": 0.0, "terrain_highlight": 0.0, "air_glow": 0.0,
                "edge_separation": 0.0, "confidence_illumination": 0.0,
                "uncertainty_luminance": 1.0, "max_shadow_opacity": 0.0,
                "optical_density_simulation": False, "concentration_shading": False,
            },
            "interaction_guardrails": {
                "reviewer_override": True, "uncertainty_must_remain_visible": True,
                "no_hidden_evidence": True, "no_light_as_measurement": True,
            },
            "scene_directive": "Use neutral review lighting until the evidence-guided depth composition is available.",
            "claim_boundary": "Light, shadow, glow, and edge contrast improve evidence legibility only. They do not measure concentration, optical density, plume thickness, distance, temperature, or atmospheric structure.",
        }

    focus_authority = _clamp(focus.get("focus_authority", 0), 0, .24)
    camera_authority = _clamp(camera.get("camera_authority", 0), 0, .26)
    conflict = _clamp((authority.get("conflict_statistics") or {}).get("mean", 0), 0, 1)
    ambiguity = _clamp((regime_conf.get("ambiguity_statistics") or {}).get("mean", 0), 0, 1)
    terrain_quality = _clamp((terrain_conf.get("summary") or {}).get("composite_score", .75), 0, 1)
    lighting_authority = _clamp((.58 * focus_authority + .24 * camera_authority + .18 * terrain_quality) * (1 - .42 * conflict) * (1 - .30 * ambiguity), .06, .28)

    regime = focus.get("focus_regime") or authority.get("winning_regime") or "mixed-transition"
    mode = {
        "confined": "corridor_separation",
        "transfer": "ridge_relief_reveal",
        "dispersive": "volume_edge_separation",
        "mixed-transition": "uncertainty_first_balance",
    }.get(regime, "balanced_review_light")

    uncertainty_floor = _clamp(.82 + .18 * ambiguity, .82, 1.0)
    terrain_shadow = _clamp(.08 + .30 * lighting_authority, 0, .17)
    terrain_highlight = _clamp(.06 + .24 * lighting_authority, 0, .14)
    air_glow = _clamp(.05 + .27 * lighting_authority, 0, .14)
    edge_separation = _clamp(.07 + .34 * lighting_authority, 0, .17)
    confidence_illumination = _clamp(.04 + .22 * lighting_authority, 0, .11)

    return {
        "contract_version": "atmospheric_light_legibility_v1",
        "pass_id": PASS_ID,
        "layer": "atmospheric_light_legibility",
        "evidence_state": "inferred",
        "data_state": "atmospheric_light_legibility_ready",
        "status": "ready",
        "display_label": f"atmospheric light · {regime} · {round(lighting_authority * 100)}% authority",
        "lighting_authority": round(lighting_authority, 4),
        "lighting_mode": mode,
        "focus_regime": regime,
        "legibility_scores": {
            "terrain": round(_clamp(.76 + .54 * lighting_authority, 0, 1), 3),
            "air_volume": round(_clamp(.74 + .58 * lighting_authority, 0, 1), 3),
            "confidence": round(_clamp(.70 + .48 * lighting_authority, 0, 1), 3),
            "uncertainty": round(_clamp(uncertainty_floor, 0, 1), 3),
        },
        "visual_directives": {
            "terrain_shadow": round(terrain_shadow, 3),
            "terrain_highlight": round(terrain_highlight, 3),
            "air_glow": round(air_glow, 3),
            "edge_separation": round(edge_separation, 3),
            "confidence_illumination": round(confidence_illumination, 3),
            "uncertainty_luminance": round(uncertainty_floor, 3),
            "max_shadow_opacity": round(min(.18, terrain_shadow), 3),
            "max_glow_radius_px": round(_clamp(5 + 30 * lighting_authority, 5, 13), 2),
            "optical_density_simulation": False,
            "concentration_shading": False,
            "plume_thickness_inference": False,
        },
        "interaction_guardrails": {
            "reviewer_override": True,
            "uncertainty_must_remain_visible": True,
            "no_hidden_evidence": True,
            "no_light_as_measurement": True,
            "reduced_motion_respected": True,
        },
        "scene_directive": "Coordinate restrained terrain shadow, air-volume glow, edge contrast, confidence illumination, and uncertainty luminance so every evidence plane remains readable at the same time.",
        "claim_boundary": "Light, shadow, glow, and edge contrast improve evidence legibility only. They do not measure concentration, optical density, plume thickness, distance, temperature, or atmospheric structure.",
    }
