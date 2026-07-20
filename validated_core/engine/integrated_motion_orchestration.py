from __future__ import annotations
from typing import Any

PASS_ID = "SV2-44"

def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(v)))

def _unavailable(label: str, state: str = "integrated_motion_orchestration_unavailable_safe") -> dict[str, Any]:
    return {
        "contract_version": "integrated_motion_orchestration_v1",
        "pass_id": PASS_ID,
        "layer": "integrated_response_driven_motion_orchestration",
        "evidence_state": "inferred",
        "data_state": state,
        "status": "unavailable_safe",
        "display_label": label,
        "winning_regime": "unavailable",
        "motion_authority": 0.0,
        "orchestration": {
            "speed_multiplier": 1.0,
            "coherence": 0.0,
            "compression": 1.0,
            "lateral_spread": 1.0,
            "lift_px": 0.0,
            "settling_px": 0.0,
            "uncertainty_jitter_px": 0.0,
        },
        "conflict_controls": {"conflict_reduction": 1.0, "ambiguity_reduction": 1.0},
        "scene_directive": "Retain neutral particle motion until integrated response authority is available.",
        "claim_boundary": "Integrated motion orchestration coordinates bounded visual tracer behavior only. It is not measured airflow, CFD, plume transport, concentration, travel time, exposure, or proof of actual atmospheric motion.",
    }

def integrated_motion_orchestration_context(scene: dict) -> dict[str, Any]:
    authority = scene.get("integrated_response_authority") or {}
    integrated = scene.get("integrated_terrain_response") or {}
    regime_conf = scene.get("terrain_regime_confidence") or {}
    if authority.get("data_state") != "integrated_response_authority_cache":
        return _unavailable("motion orchestration unavailable · response authority missing")

    winning = authority.get("winning_regime", "mixed-transition")
    a = _clamp((authority.get("visual_directives") or {}).get("motion_authority", 0.0), 0.0, 0.34)
    conflict = _clamp((authority.get("conflict_statistics") or {}).get("mean", 1.0), 0.0, 1.0)
    ambiguity = _clamp((regime_conf.get("ambiguity_statistics") or {}).get("mean", conflict), 0.0, 1.0)
    agreement = _clamp((integrated.get("agreement_statistics") or {}).get("mean", 0.0), 0.0, 1.0)
    gate = _clamp(a * (0.55 + 0.45 * agreement) * (1.0 - 0.52 * conflict) * (1.0 - 0.35 * ambiguity), 0.0, 0.30)

    profiles = {
        "confined": {"speed": 0.94, "coherence": 0.86, "compression": 0.88, "spread": 0.92, "lift": 0.5, "settle": 2.8},
        "transfer": {"speed": 1.08, "coherence": 0.78, "compression": 0.94, "spread": 1.00, "lift": 5.5, "settle": 0.0},
        "dispersive": {"speed": 1.04, "coherence": 0.58, "compression": 1.04, "spread": 1.14, "lift": 1.2, "settle": 0.0},
        "mixed-transition": {"speed": 1.00, "coherence": 0.52, "compression": 1.00, "spread": 1.06, "lift": 0.8, "settle": 0.8},
    }
    prof = profiles.get(winning, profiles["mixed-transition"])
    blend = gate / 0.30 if gate > 0 else 0.0
    speed = 1.0 + (prof["speed"] - 1.0) * blend
    compression = 1.0 + (prof["compression"] - 1.0) * blend
    spread = 1.0 + (prof["spread"] - 1.0) * blend
    coherence = prof["coherence"] * blend
    lift = prof["lift"] * blend
    settling = prof["settle"] * blend
    jitter = _clamp((conflict * 3.2 + ambiguity * 2.4) * blend, 0.0, 4.5)

    return {
        "contract_version": "integrated_motion_orchestration_v1",
        "pass_id": PASS_ID,
        "layer": "integrated_response_driven_motion_orchestration",
        "evidence_state": "inferred",
        "data_state": "integrated_motion_orchestration_ready",
        "status": "ready",
        "winning_regime": winning,
        "motion_authority": round(gate, 4),
        "orchestration": {
            "speed_multiplier": round(_clamp(speed, 0.92, 1.10), 4),
            "coherence": round(_clamp(coherence, 0.0, 0.82), 4),
            "compression": round(_clamp(compression, 0.90, 1.06), 4),
            "lateral_spread": round(_clamp(spread, 0.94, 1.14), 4),
            "lift_px": round(_clamp(lift, 0.0, 5.5), 3),
            "settling_px": round(_clamp(settling, 0.0, 3.0), 3),
            "uncertainty_jitter_px": round(jitter, 3),
        },
        "conflict_controls": {
            "conflict_mean": round(conflict, 4),
            "ambiguity_mean": round(ambiguity, 4),
            "agreement_mean": round(agreement, 4),
            "conflict_reduction": round(1.0 - 0.52 * conflict, 4),
            "ambiguity_reduction": round(1.0 - 0.35 * ambiguity, 4),
            "contradictory_effects_allowed": False,
        },
        "display_label": f"motion orchestration {winning} · {round(gate*100)}% authority",
        "scene_directive": "Apply one coordinated motion profile from the authorized integrated regime. Reduce all motion effects together where conflict or ambiguity is elevated.",
        "claim_boundary": "Integrated motion orchestration coordinates bounded visual tracer behavior only. It is not measured airflow, CFD, plume transport, concentration, travel time, exposure, or proof of actual atmospheric motion.",
    }
