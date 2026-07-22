from __future__ import annotations

from copy import deepcopy

DEFAULT_MATERIAL_PROFILE_ID = "methane-gas"

MATERIAL_PROFILES = {
    "methane-gas": {
        "behavior": {
            "plume_rise_m": 0.0,
            "crosswind_spread_factor": 1.0,
            "persistence_factor": 1.0,
            "settling_velocity_mps": 0.0,
            "dry_deposition_velocity_mps": 0.0,
            "wet_scavenging_factor": 0.0,
            "support_uncertainty_penalty": 0.0,
        },
        "id": "methane-gas",
        "visual_identity": {"family": "methane", "accent": "#42c7d2", "core_rgb": [182, 246, 241], "mid_rgb": [65, 190, 204], "outer_rgb": [37, 103, 126], "marker_rgb": [184, 243, 239], "texture": "clean-gas"},
        "name": "Methane gas",
        "short_label": "Methane",
        "category": "gas",
        "pollutant_phase": "gas",
        "release_height_m": 10.0,
        "release_duration_minutes": 60.0,
        "relative_strength": 1.0,
        "buoyancy_behavior": "near_neutral",
        "deposition_behavior": "none",
        "settling_behavior": "none",
        "wet_removal_behavior": "not_applied",
        "atmospheric_lifetime": "long_relative_to_local_scene",
        "renderer_mode": "existing_governing_field",
        "physics_status": "material_behavior_active_baseline_preserved",
        "assumption_summary": "A near-surface methane release represented by the existing governing transport field. Pass 1 does not change established plume physics.",
        "claim_boundary": "This profile organizes model assumptions. It does not identify, measure, or verify a real methane release.",
    },
    "fine-smoke-aerosol": {
        "behavior": {
            "plume_rise_m": 30.0,
            "crosswind_spread_factor": 1.18,
            "persistence_factor": 1.22,
            "settling_velocity_mps": 0.002,
            "dry_deposition_velocity_mps": 0.0015,
            "wet_scavenging_factor": 0.18,
            "support_uncertainty_penalty": 0.05,
        },
        "id": "fine-smoke-aerosol",
        "visual_identity": {"family": "smoke", "accent": "#d6a45d", "core_rgb": [255, 239, 174], "mid_rgb": [220, 166, 78], "outer_rgb": [83, 147, 155], "marker_rgb": [255, 226, 154], "texture": "fine-aerosol"},
        "name": "Fine smoke aerosol",
        "short_label": "Smoke",
        "category": "aerosol",
        "pollutant_phase": "particle",
        "release_height_m": 40.0,
        "release_duration_minutes": 180.0,
        "relative_strength": 1.0,
        "buoyancy_behavior": "moderately_buoyant",
        "deposition_behavior": "bounded_dry_and_wet_removal",
        "settling_behavior": "slow",
        "wet_removal_behavior": "future_precipitation_sensitive",
        "atmospheric_lifetime": "hours_to_days_context_dependent",
        "renderer_mode": "material_aware_governing_field",
        "physics_status": "bounded_material_behavior_active",
        "assumption_summary": "A fine-particle smoke profile reserved for a later physics pass with buoyancy, settling, and removal behavior.",
        "claim_boundary": "This profile is not a wildfire forecast, air-quality measurement, or public-health advisory.",
    },
    "radioactive-mixed-release": {
        "behavior": {
            "plume_rise_m": 12.0,
            "crosswind_spread_factor": 1.08,
            "persistence_factor": 0.96,
            "settling_velocity_mps": 0.006,
            "dry_deposition_velocity_mps": 0.004,
            "wet_scavenging_factor": 0.24,
            "support_uncertainty_penalty": 0.12,
        },
        "id": "radioactive-mixed-release",
        "visual_identity": {"family": "radioactive", "accent": "#a8cc67", "core_rgb": [231, 249, 174], "mid_rgb": [155, 202, 89], "outer_rgb": [72, 124, 100], "marker_rgb": [211, 239, 143], "texture": "mixed-deposition"},
        "name": "Radioactive mixed release",
        "short_label": "Radioactive release",
        "category": "mixed",
        "pollutant_phase": "mixed",
        "release_height_m": 25.0,
        "release_duration_minutes": 90.0,
        "relative_strength": 1.0,
        "buoyancy_behavior": "source_dependent",
        "deposition_behavior": "bounded_mixed_deposition_screening",
        "settling_behavior": "mixed",
        "wet_removal_behavior": "future_precipitation_sensitive",
        "atmospheric_lifetime": "material_specific",
        "renderer_mode": "material_aware_governing_field",
        "physics_status": "bounded_material_behavior_active",
        "assumption_summary": "A mixed airborne-material contract reserved for later component-specific transport and deposition treatment.",
        "claim_boundary": "This profile does not estimate radiation dose, contamination, emergency zones, or public safety actions.",
    },
    "hot-industrial-plume": {
        "behavior": {
            "plume_rise_m": 95.0,
            "crosswind_spread_factor": 1.12,
            "persistence_factor": 1.08,
            "settling_velocity_mps": 0.003,
            "dry_deposition_velocity_mps": 0.002,
            "wet_scavenging_factor": 0.10,
            "support_uncertainty_penalty": 0.08,
        },
        "id": "hot-industrial-plume",
        "visual_identity": {"family": "industrial", "accent": "#a98ad8", "core_rgb": [238, 218, 255], "mid_rgb": [164, 121, 214], "outer_rgb": [83, 111, 154], "marker_rgb": [222, 198, 255], "texture": "elevated-mixed"},
        "name": "Hot elevated industrial plume",
        "short_label": "Industrial plume",
        "category": "gas_and_aerosol",
        "pollutant_phase": "mixed",
        "release_height_m": 80.0,
        "release_duration_minutes": 120.0,
        "relative_strength": 1.0,
        "buoyancy_behavior": "strongly_buoyant",
        "deposition_behavior": "bounded_material_specific_screening",
        "settling_behavior": "material_dependent",
        "wet_removal_behavior": "bounded_material_specific_screening",
        "atmospheric_lifetime": "material_specific",
        "renderer_mode": "material_aware_governing_field",
        "physics_status": "bounded_material_behavior_active",
        "assumption_summary": "An elevated buoyant industrial-release contract reserved for a later plume-rise and material-behavior pass.",
        "claim_boundary": "This profile is not a regulatory dispersion result, emissions inventory, permit analysis, or compliance determination.",
    },
}


def list_material_profiles():
    return [deepcopy(profile) for profile in MATERIAL_PROFILES.values()]


def get_material_profile(profile_id=None):
    selected = profile_id or DEFAULT_MATERIAL_PROFILE_ID
    return deepcopy(MATERIAL_PROFILES.get(selected, MATERIAL_PROFILES[DEFAULT_MATERIAL_PROFILE_ID]))


MATERIAL_BEHAVIOR_VERSION = "ia_material_behavior_v1.0.0"


def build_material_behavior(profile, precipitation_rate_mm_hr=0.0):
    behavior = deepcopy(profile.get("behavior") or {})
    precipitation = max(0.0, float(precipitation_rate_mm_hr or 0.0))
    wet_base = max(0.0, float(behavior.get("wet_scavenging_factor", 0.0)))
    wet_effective = min(0.75, wet_base * min(1.0, precipitation / 8.0))

    release_height = max(0.0, float(profile.get("release_height_m", 10.0)))
    plume_rise = max(0.0, float(behavior.get("plume_rise_m", 0.0)))
    behavior.update({
        "material_profile_id": profile.get("id", DEFAULT_MATERIAL_PROFILE_ID),
        "material_name": profile.get("name", "Material"),
        "pollutant_phase": profile.get("pollutant_phase", "gas"),
        "base_release_height_m": release_height,
        "effective_release_height_m": release_height + plume_rise,
        "precipitation_rate_mm_hr": precipitation,
        "effective_wet_removal_factor": wet_effective,
        "material_behavior_version": MATERIAL_BEHAVIOR_VERSION,
        "behavior_scope": "bounded_screening_scale_relative_influence",
        "not_claimed": [
            "regulatory concentration",
            "exposure",
            "dose",
            "health risk",
            "emergency zone",
            "source attribution",
        ],
    })
    return behavior


def apply_material_profile(scene, profile):
    contract = deepcopy(profile)
    contract["data_state"] = "material_profile_contract_ready"
    contract["pass_id"] = "MATERIAL-BEHAVIOR-PASS-2"
    contract["material_behavior_version"] = MATERIAL_BEHAVIOR_VERSION
    contract["governing_physics_changed"] = contract.get("id") != DEFAULT_MATERIAL_PROFILE_ID
    scene["material_profile"] = contract
    scene["active_material_profile"] = contract
    scene.setdefault("material_contract", {}).update({
        "profile_id": contract["id"],
        "profile_name": contract["name"],
        "data_state": contract["data_state"],
        "physics_status": contract["physics_status"],
        "governing_physics_changed": contract["governing_physics_changed"],
        "material_behavior_version": MATERIAL_BEHAVIOR_VERSION,
    })
    return scene
