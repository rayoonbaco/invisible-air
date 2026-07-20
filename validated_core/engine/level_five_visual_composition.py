from __future__ import annotations


def level_five_visual_composition_context(scene: dict) -> dict:
    conflict = float(((scene.get("integrated_response_authority") or {}).get("conflict_statistics") or {}).get("mean", 1.0) or 1.0)
    ambiguity = float(((scene.get("terrain_regime_confidence") or {}).get("ambiguity_statistics") or {}).get("mean", 1.0) or 1.0)
    agreement = float(((scene.get("integrated_terrain_response") or {}).get("agreement_statistics") or {}).get("mean", 0.0) or 0.0)
    authority = max(0.08, min(0.42, 0.18 + agreement * 0.22 - conflict * 0.08 - ambiguity * 0.05))
    return {
        "contract_version": "level_five_visual_composition_v1",
        "pass_id": "SV2-56",
        "layer": "level_five_visual_composition",
        "evidence_state": "visual_governance",
        "data_state": "level_five_composition_ready",
        "status": "ready",
        "display_label": f"Level Five composition ready · {round(authority*100)}% visual authority",
        "composition_authority": round(authority, 3),
        "hero_surface": "map_registered_living_scientific_scene",
        "reading_order": ["place", "reported observation", "primary response", "confidence and uncertainty", "human review action"],
        "layout": {
            "scene_priority": 0.78,
            "interpretation_priority": 0.22,
            "maximum_primary_accents": 3,
            "default_detail_level": "overview",
            "minimum_scene_height_px": 660
        },
        "performance_policy": {
            "adaptive_quality": True,
            "reduced_motion_respected": True,
            "pause_when_hidden": True,
            "quality_profiles": ["high", "balanced", "reduced"],
            "target_frame_budget_ms": 22,
            "maximum_device_pixel_ratio": 1.75
        },
        "visual_guardrails": [
            "No visual intensity may imply concentration, severity, probability, or certainty.",
            "Uncertainty remains visible at every quality profile.",
            "Reviewer interaction immediately overrides cinematic guidance.",
            "Performance reductions simplify effects, never evidence boundaries."
        ],
        "scene_directive": "Make the map-registered scientific scene the visual hero while preserving evidence state, uncertainty, and reviewer control.",
        "claim_boundary": "Level Five composition and adaptive rendering improve visual clarity and performance only. They do not add evidence, measure atmospheric behavior, or increase scientific confidence."
    }
