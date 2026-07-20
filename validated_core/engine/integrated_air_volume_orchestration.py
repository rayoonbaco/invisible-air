from __future__ import annotations
from typing import Any

PASS_ID = "SV2-45"

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))

def _neutral(label: str) -> dict[str, Any]:
    return {
        "contract_version": "integrated_air_volume_orchestration_v1",
        "pass_id": PASS_ID,
        "layer": "integrated_air_volume_orchestration",
        "evidence_state": "inferred",
        "data_state": "integrated_air_volume_unavailable_safe",
        "status": "unavailable_safe",
        "display_label": label,
        "winning_regime": "unavailable",
        "volume_authority": 0.0,
        "orchestration": {
            "width_multiplier": 1.0, "vertical_thickness_multiplier": 1.0,
            "core_opacity_multiplier": 1.0, "haze_opacity_multiplier": 1.0,
            "asymmetry_px": 0.0, "lift_px": 0.0, "settling_px": 0.0,
            "downstream_diffusion_multiplier": 1.0,
        },
        "conflict_controls": {"contradictory_shapes_allowed": False},
        "scene_directive": "Retain the neutral layered air volume until integrated response authority is available.",
        "claim_boundary": "Integrated air-volume orchestration coordinates bounded visual volume behavior only. It is not measured methane geometry, concentration, mass, plume height, CFD, transport, exposure, or proof of actual atmospheric structure.",
    }

def integrated_air_volume_orchestration_context(scene: dict) -> dict[str, Any]:
    authority = scene.get("integrated_response_authority") or {}
    motion = scene.get("integrated_motion_orchestration") or {}
    integrated = scene.get("integrated_terrain_response") or {}
    regime_conf = scene.get("terrain_regime_confidence") or {}
    if authority.get("data_state") != "integrated_response_authority_cache" or motion.get("data_state") != "integrated_motion_orchestration_ready":
        return _neutral("air-volume orchestration unavailable · integrated authority missing")

    winning = authority.get("winning_regime", "mixed-transition")
    base_authority = _clamp(float(authority.get("visual_directives", {}).get("volume_authority", authority.get("visual_directives", {}).get("motion_authority", 0.0))), 0.0, 0.40)
    agreement = _clamp(float(integrated.get("agreement_statistics", {}).get("mean", 0.0)), 0.0, 1.0)
    conflict = _clamp(float(authority.get("conflict_statistics", {}).get("mean", 1.0)), 0.0, 1.0)
    ambiguity = _clamp(float(regime_conf.get("ambiguity_statistics", {}).get("mean", conflict)), 0.0, 1.0)
    gate = _clamp(base_authority * (0.58 + 0.42*agreement) * (1.0-0.55*conflict) * (1.0-0.38*ambiguity), 0.0, 0.36)
    blend = gate / 0.36 if gate else 0.0

    profiles = {
        "confined": dict(width=.84, thick=.92, core=1.12, haze=.90, asym=-3.5, lift=.4, settle=3.5, diffusion=.88),
        "transfer": dict(width=.94, thick=1.12, core=1.04, haze=.98, asym=2.0, lift=6.0, settle=0.0, diffusion=.96),
        "dispersive": dict(width=1.18, thick=1.08, core=.90, haze=1.18, asym=4.5, lift=1.2, settle=0.0, diffusion=1.20),
        "mixed-transition": dict(width=1.06, thick=1.04, core=.96, haze=1.10, asym=1.5, lift=.8, settle=.8, diffusion=1.10),
    }
    p = profiles.get(winning, profiles["mixed-transition"])
    mix = lambda target: 1.0 + (target-1.0)*blend
    orch = {
        "width_multiplier": round(_clamp(mix(p["width"]), .84, 1.18),4),
        "vertical_thickness_multiplier": round(_clamp(mix(p["thick"]), .90, 1.12),4),
        "core_opacity_multiplier": round(_clamp(mix(p["core"]), .90, 1.12),4),
        "haze_opacity_multiplier": round(_clamp(mix(p["haze"]), .90, 1.18),4),
        "asymmetry_px": round(_clamp(p["asym"]*blend, -3.5, 4.5),3),
        "lift_px": round(_clamp(p["lift"]*blend, 0, 6.0),3),
        "settling_px": round(_clamp(p["settle"]*blend, 0, 3.5),3),
        "downstream_diffusion_multiplier": round(_clamp(mix(p["diffusion"]), .88, 1.20),4),
    }
    return {
        "contract_version": "integrated_air_volume_orchestration_v1",
        "pass_id": PASS_ID,
        "layer": "integrated_air_volume_orchestration",
        "evidence_state": "inferred",
        "data_state": "integrated_air_volume_orchestration_ready",
        "status": "ready",
        "display_label": f"air-volume orchestration {winning} · {round(gate*100)}% authority",
        "winning_regime": winning,
        "volume_authority": round(gate,4),
        "orchestration": orch,
        "conflict_controls": {
            "agreement_mean": round(agreement,4), "conflict_mean": round(conflict,4),
            "ambiguity_mean": round(ambiguity,4), "contradictory_shapes_allowed": False,
        },
        "scene_directive": "Apply one coordinated volume profile from the authorized integrated regime. Reduce width, thickness, opacity, lift, settling, and diffusion together where conflict or ambiguity is elevated.",
        "claim_boundary": "Integrated air-volume orchestration coordinates bounded visual volume behavior only. It is not measured methane geometry, concentration, mass, plume height, CFD, transport, exposure, or proof of actual atmospheric structure.",
    }
