from __future__ import annotations
from typing import Any

PASS_ID = "SV2-50"


def _clamp(value: Any, low: float, high: float) -> float:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = low
    return max(low, min(high, value))


def evidence_visual_hierarchy_context(scene: dict) -> dict[str, Any]:
    lighting = scene.get("atmospheric_light_legibility") or {}
    focus = scene.get("evidence_guided_focus_depth") or {}
    vocabulary = scene.get("evidence_vocabulary") or {}
    missing = scene.get("missing_evidence") or {}
    authority = scene.get("integrated_response_authority") or {}

    ready = lighting.get("data_state") == "atmospheric_light_legibility_ready"
    if not ready:
        return {
            "contract_version": "evidence_visual_hierarchy_v1",
            "pass_id": PASS_ID,
            "layer": "evidence_visual_hierarchy",
            "evidence_state": "inferred",
            "data_state": "evidence_visual_hierarchy_unavailable_safe",
            "status": "unavailable_safe",
            "display_label": "visual hierarchy unavailable · lighting context missing",
            "hierarchy_authority": 0.0,
            "hierarchy_mode": "neutral_evidence_review",
            "priority_order": ["uncertainty", "observed", "measured", "modeled", "inferred", "not_claimed"],
            "palette": {
                "observed": "#72f0a3", "measured": "#73bfff", "modeled": "#bf94ff",
                "current_context": "#ffbf59", "inferred": "#ff9866", "uncertainty": "#d8ccff",
                "unavailable": "#8d999d", "not_claimed": "#f3f6f6",
            },
            "contrast_rules": {
                "text_contrast_floor": 0.82, "uncertainty_prominence_floor": 0.90,
                "simultaneous_accent_limit": 3, "color_as_measurement": False,
                "color_as_concentration": False, "hidden_evidence_allowed": False,
            },
            "interaction_guardrails": {"reviewer_override": True, "reduced_motion_respected": True},
            "scene_directive": "Use the neutral evidence palette until the lighting and focus systems are available.",
            "claim_boundary": "Color, contrast, saturation, and visual hierarchy communicate evidence state and reading order only. They do not measure concentration, severity, probability, distance, plume thickness, or atmospheric structure.",
        }

    light_authority = _clamp(lighting.get("lighting_authority", 0), 0, .28)
    focus_authority = _clamp(focus.get("focus_authority", 0), 0, .24)
    conflict = _clamp((authority.get("conflict_statistics") or {}).get("mean", 0), 0, 1)
    unresolved = int((missing.get("summary") or {}).get("missing_count", 0) or 0)
    vocabulary_active = vocabulary.get("status") == "ready" or bool(vocabulary.get("layers"))

    authority_score = _clamp((.52 * light_authority + .30 * focus_authority + (.18 if vocabulary_active else .08)) * (1 - .34 * conflict), .08, .30)
    uncertainty_floor = _clamp(.90 + min(.08, unresolved * .008) + .04 * conflict, .90, 1.0)
    mode = {
        "corridor_separation": "confined_evidence_hierarchy",
        "ridge_relief_reveal": "transfer_evidence_hierarchy",
        "volume_edge_separation": "dispersive_evidence_hierarchy",
        "uncertainty_first_balance": "uncertainty_first_hierarchy",
    }.get(lighting.get("lighting_mode"), "balanced_evidence_hierarchy")

    return {
        "contract_version": "evidence_visual_hierarchy_v1",
        "pass_id": PASS_ID,
        "layer": "evidence_visual_hierarchy",
        "evidence_state": "inferred",
        "data_state": "evidence_visual_hierarchy_ready",
        "status": "ready",
        "display_label": f"evidence hierarchy · {mode.replace('_', ' ')} · {round(authority_score*100)}% authority",
        "hierarchy_authority": round(authority_score, 4),
        "hierarchy_mode": mode,
        "priority_order": ["uncertainty", "observed", "measured", "modeled", "current_context", "inferred", "unavailable", "not_claimed"],
        "palette": {
            "observed": "#72f0a3", "measured": "#73bfff", "modeled": "#bf94ff",
            "current_context": "#ffbf59", "inferred": "#ff9866", "uncertainty": "#d8ccff",
            "unavailable": "#8d999d", "not_claimed": "#f3f6f6",
        },
        "contrast_rules": {
            "text_contrast_floor": round(_clamp(.84 + .22 * authority_score, .84, .91), 3),
            "uncertainty_prominence_floor": round(uncertainty_floor, 3),
            "simultaneous_accent_limit": 3,
            "accent_saturation_cap": round(_clamp(.72 - .38 * conflict, .48, .72), 3),
            "secondary_layer_opacity_cap": round(_clamp(.52 - .24 * conflict, .30, .52), 3),
            "color_as_measurement": False,
            "color_as_concentration": False,
            "color_as_probability": False,
            "hidden_evidence_allowed": False,
        },
        "interaction_guardrails": {
            "reviewer_override": True, "reduced_motion_respected": True,
            "uncertainty_always_visible": True, "not_claimed_remains_neutral": True,
        },
        "scene_directive": "Govern color, contrast, saturation, and reading order so uncertainty remains most visible, direct evidence remains distinct, and inferred layers cannot visually overpower their support.",
        "claim_boundary": "Color, contrast, saturation, and visual hierarchy communicate evidence state and reading order only. They do not measure concentration, severity, probability, distance, plume thickness, or atmospheric structure.",
    }
