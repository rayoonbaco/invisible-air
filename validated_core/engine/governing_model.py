from __future__ import annotations

"""Invisible Air governing model.

This module is deliberately independent from the legacy visual orchestration.
It produces two deterministic, dimensionless grids:

* relative_influence: run-normalized atmospheric influence [0, 1]
* model_support: spatial support for that influence [0, 1]

It does not calculate regulatory concentration, exposure, danger, or probability.
"""

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import math
from typing import Any

import numpy as np

from engine.terrain_field_response import build_terrain_response, TERRAIN_RESPONSE_VERSION

MODEL_VERSION = "ia_governing_model_v1.0.0"
COEFFICIENT_VERSION = "ia_coefficients_2026-07-20-pass50"
MATERIAL_BEHAVIOR_VERSION = "ia_material_behavior_v1.0.0"

STABILITY = {
    "very_unstable": {"crosswind_growth": 0.22, "vertical_growth": 0.19, "decay_scale": 0.78},
    "unstable":      {"crosswind_growth": 0.18, "vertical_growth": 0.15, "decay_scale": 0.88},
    "neutral":       {"crosswind_growth": 0.12, "vertical_growth": 0.10, "decay_scale": 1.00},
    "stable":        {"crosswind_growth": 0.075,"vertical_growth": 0.055,"decay_scale": 1.12},
    "very_stable":   {"crosswind_growth": 0.050,"vertical_growth": 0.038,"decay_scale": 1.20},
}

TERRAIN_REGIMES = {
    "open": {"alignment_deg": None, "steering_strength": 0.0, "crosswind_spread_factor": 1.0, "support_penalty": 0.0},
    "valley": {"alignment_deg": 0.0, "steering_strength": 0.28, "crosswind_spread_factor": 0.72, "support_penalty": 0.08},
    "cross_ridge": {"alignment_deg": 90.0, "steering_strength": 0.12, "crosswind_spread_factor": 1.18, "support_penalty": 0.18},
    "complex": {"alignment_deg": None, "steering_strength": 0.08, "crosswind_spread_factor": 1.28, "support_penalty": 0.24},
}

@dataclass(frozen=True)
class SourceInput:
    latitude: float = 34.22560
    longitude: float = -119.11890
    relative_strength: float = 1.0
    release_height_m: float = 10.0
    release_duration_minutes: float = 60.0
    pollutant_phase: str = "gas"

@dataclass(frozen=True)
class MeteorologyInput:
    wind_from_deg: float = 112.0
    wind_speed_mps: float = 0.9
    stability_class: str = "neutral"
    boundary_layer_depth_m: float = 650.0
    direction_variability_deg: float = 12.0
    gust_factor: float = 1.25

@dataclass(frozen=True)
class TerrainInput:
    regime: str = "open"
    alignment_deg: float | None = None
    response_strength: float = 1.0
    evidence_support: float = 0.85
    local_profile: str | None = None
    local_response_enabled: bool = True

@dataclass(frozen=True)
class MaterialBehaviorInput:
    material_profile_id: str = "methane-gas"
    material_name: str = "Methane gas"
    pollutant_phase: str = "gas"
    base_release_height_m: float = 10.0
    effective_release_height_m: float = 10.0
    plume_rise_m: float = 0.0
    crosswind_spread_factor: float = 1.0
    persistence_factor: float = 1.0
    settling_velocity_mps: float = 0.0
    dry_deposition_velocity_mps: float = 0.0
    wet_scavenging_factor: float = 0.0
    effective_wet_removal_factor: float = 0.0
    support_uncertainty_penalty: float = 0.0
    precipitation_rate_mm_hr: float = 0.0
    material_behavior_version: str = MATERIAL_BEHAVIOR_VERSION
    behavior_scope: str = "bounded_screening_scale_relative_influence"


@dataclass(frozen=True)
class GridInput:
    domain_downwind_km: float = 80.0
    domain_crosswind_km: float = 40.0
    nx: int = 241
    ny: int = 161

@dataclass(frozen=True)
class GoverningModelInput:
    source: SourceInput = field(default_factory=SourceInput)
    meteorology: MeteorologyInput = field(default_factory=MeteorologyInput)
    terrain: TerrainInput = field(default_factory=TerrainInput)
    material: MaterialBehaviorInput = field(default_factory=MaterialBehaviorInput)
    grid: GridInput = field(default_factory=GridInput)


def _angle_delta(a: float, b: float) -> float:
    return ((b - a + 180.0) % 360.0) - 180.0


def _effective_transport_direction(m: MeteorologyInput, t: TerrainInput) -> tuple[float, dict[str, float]]:
    wind_to = (m.wind_from_deg + 180.0) % 360.0
    regime = TERRAIN_REGIMES.get(t.regime, TERRAIN_REGIMES["complex"])
    alignment = t.alignment_deg if t.alignment_deg is not None else regime["alignment_deg"]
    steering = float(regime["steering_strength"]) * float(np.clip(t.response_strength, 0.0, 1.5))
    applied_turn = 0.0
    if alignment is not None and steering > 0:
        # Valleys/ridges have bidirectional axes; use the axis direction closest to transport.
        candidates = [alignment % 360.0, (alignment + 180.0) % 360.0]
        target = min(candidates, key=lambda v: abs(_angle_delta(wind_to, v)))
        applied_turn = np.clip(_angle_delta(wind_to, target), -38.0, 38.0) * steering
    effective = (wind_to + applied_turn) % 360.0
    return effective, {"wind_to_deg": round(wind_to, 3), "terrain_turn_deg": round(float(applied_turn), 3), "effective_transport_deg": round(effective, 3)}


def run_governing_model(inputs: GoverningModelInput) -> dict[str, Any]:
    m, s, t, material, g = inputs.meteorology, inputs.source, inputs.terrain, inputs.material, inputs.grid
    if m.stability_class not in STABILITY:
        raise ValueError(f"Unsupported stability_class: {m.stability_class}")
    if m.wind_speed_mps <= 0:
        raise ValueError("wind_speed_mps must be positive")
    if g.nx < 31 or g.ny < 31:
        raise ValueError("grid resolution must be at least 31 x 31")

    coeff = STABILITY[m.stability_class]
    regime = TERRAIN_REGIMES.get(t.regime, TERRAIN_REGIMES["complex"])
    direction, direction_diag = _effective_transport_direction(m, t)

    x = np.linspace(-0.08 * g.domain_downwind_km, g.domain_downwind_km, g.nx)
    y = np.linspace(-g.domain_crosswind_km, g.domain_crosswind_km, g.ny)
    xx, yy = np.meshgrid(x, y)
    xp = np.maximum(xx, 0.0)

    variability_rad = math.radians(max(0.0, m.direction_variability_deg))
    gust_excess = max(0.0, m.gust_factor - 1.0)
    terrain_spread = float(regime["crosswind_spread_factor"])
    material_spread = float(np.clip(material.crosswind_spread_factor, 0.65, 1.65))
    effective_release_height_m = max(0.0, float(material.effective_release_height_m))

    initial_sigma_km = 0.35 + 0.025 * effective_release_height_m
    growth = coeff["crosswind_growth"] * terrain_spread * material_spread
    turbulent_growth = 0.035 * gust_excess + 0.30 * math.tan(min(variability_rad, math.radians(35.0)))
    base_sigma_y = np.maximum(0.25, initial_sigma_km + xp * (growth + turbulent_growth))

    profile = t.local_profile or ({"valley": "valley_aligned", "cross_ridge": "cross_ridge", "complex": "complex"}.get(t.regime, "open"))
    terrain_local = build_terrain_response(xx, yy, profile if t.local_response_enabled else "off", t.response_strength, t.evidence_support)
    terrain_center = terrain_local["center_shift_km"]
    sigma_y = np.maximum(0.25, base_sigma_y * terrain_local["width_factor"])

    mixing_factor = np.clip(700.0 / max(120.0, m.boundary_layer_depth_m), 0.45, 1.8)
    speed_reach = np.clip(0.58 + 0.24 * m.wind_speed_mps, 0.65, 2.4)
    release_factor = np.clip(s.relative_strength, 0.05, 20.0)
    persistence_factor = float(np.clip(material.persistence_factor, 0.55, 1.65))
    decay_length = g.domain_downwind_km * 0.42 * coeff["decay_scale"] * speed_reach * persistence_factor
    settling_loss_per_km = max(0.0, float(material.settling_velocity_mps)) * 0.024
    dry_loss_per_km = max(0.0, float(material.dry_deposition_velocity_mps)) * 0.018
    wet_loss_per_km = max(0.0, float(material.effective_wet_removal_factor)) * 0.012
    material_loss = np.exp(-xp * (settling_loss_per_km + dry_loss_per_km + wet_loss_per_km))

    crosswind = np.exp(-0.5 * ((yy - terrain_center) / sigma_y) ** 2)
    downwind = np.exp(-xp / max(2.0, decay_length))
    source_transition = 1.0 - np.exp(-xp / max(0.7, 1.2 + effective_release_height_m / 35.0))
    upstream_guard = np.where(xx >= 0.0, 1.0, np.exp(xx / 0.7) * 0.08)

    raw = release_factor * mixing_factor * crosswind * downwind * material_loss * source_transition * upstream_guard * terrain_local["transmission"]
    raw += release_factor * mixing_factor * np.exp(-((xx / 0.8) ** 2 + (yy / 0.8) ** 2)) * 0.72
    max_raw = float(raw.max()) or 1.0
    influence = np.clip(raw / max_raw, 0.0, 1.0)

    distance_support = np.exp(-xp / max(5.0, g.domain_downwind_km * 0.70))
    lateral_support = np.exp(-0.5 * (np.abs(yy) / np.maximum(0.7, sigma_y * 2.15)) ** 2)
    variability_penalty = np.clip(1.0 - m.direction_variability_deg / 95.0 - gust_excess * 0.08, 0.35, 1.0)
    terrain_penalty = np.clip(1.0 - float(regime["support_penalty"]) * t.response_strength, 0.35, 1.0)
    material_support = np.clip(1.0 - float(material.support_uncertainty_penalty), 0.55, 1.0)
    evidence = np.clip(t.evidence_support, 0.0, 1.0)
    support = np.clip(distance_support * lateral_support * variability_penalty * terrain_penalty * material_support * evidence * terrain_local["support_factor"], 0.0, 1.0)
    support *= (influence > 0.004)

    cell_area = (g.domain_downwind_km * 1.08 / (g.nx - 1)) * (2 * g.domain_crosswind_km / (g.ny - 1))
    weighted_x = float((influence * xx).sum() / max(influence.sum(), 1e-9))
    spread = float(np.sqrt((influence * yy**2).sum() / max(influence.sum(), 1e-9)))
    active = influence >= 0.10
    supported = support >= 0.50

    manifest = {
        "model_version": MODEL_VERSION,
        "coefficient_version": COEFFICIENT_VERSION,
        "output_definition": "Run-normalized relative modeled atmospheric influence and model-support fields; dimensionless values in [0,1].",
        "not_claimed": ["regulatory concentration", "exposure", "danger", "health risk", "probability", "source attribution"],
        "inputs": asdict(inputs),
        "governing_method": {
            "transport": "Wind-to direction with bounded terrain-axis steering.",
            "spread": "Gaussian crosswind kernel with stability, directional variability, gust, release-height, and terrain-regime terms.",
            "decay": "Exponential downwind attenuation with wind-speed and stability reach factors.",
            "mixing": "Boundary-layer-depth scaling of relative raw influence before within-run normalization.",
            "support": "Independent distance, lateral, variability, terrain-evidence, terrain-conflict, and cell-level support field.",
            "local_terrain": "Bounded deterministic cell-level steering, compression, barrier transmission, divergence, and support response; screening-scale, not CFD.",
            "material_behavior": "Bounded release-height, spread, persistence, settling, deposition, wet-removal, and support modifiers; relative screening behavior, not regulatory dispersion.",
        },
    }
    fingerprint_payload = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode() + influence.tobytes() + support.tobytes()
    fingerprint = sha256(fingerprint_payload).hexdigest()[:24]

    return {
        "contract_version": "invisible_air_governing_field_contract_v1",
        "model_version": MODEL_VERSION,
        "coefficient_version": COEFFICIENT_VERSION,
        "fingerprint": fingerprint,
        "output_definition": manifest["output_definition"],
        "grid": {
            "nx": g.nx, "ny": g.ny,
            "x_downwind_km": np.round(x, 5).tolist(),
            "y_crosswind_km": np.round(y, 5).tolist(),
            "relative_influence": np.round(influence, 6).tolist(),
            "model_support": np.round(support, 6).tolist(),
            "transport_bearing_deg": direction,
            "source": asdict(s),
        },
        "diagnostics": {
            **direction_diag,
            "peak_raw_relative_units": round(max_raw, 8),
            "mixing_factor": round(float(mixing_factor), 5),
            "decay_length_km": round(float(decay_length), 5),
            "influence_centroid_downwind_km": round(weighted_x, 5),
            "rms_crosswind_spread_km": round(spread, 5),
            "active_area_km2_at_0_10": round(float(active.sum() * cell_area), 4),
            "supported_area_km2_at_0_50": round(float((active & supported).sum() * cell_area), 4),
            "mean_support_in_active_field": round(float(support[active].mean()) if active.any() else 0.0, 5),
            "terrain_response_version": TERRAIN_RESPONSE_VERSION,
            "material_behavior_version": MATERIAL_BEHAVIOR_VERSION,
            "material_profile_id": material.material_profile_id,
            "material_name": material.material_name,
            "effective_release_height_m": round(float(effective_release_height_m), 5),
            "effective_buoyancy_factor": round(float(1.0 + material.plume_rise_m / max(10.0, material.base_release_height_m)), 5),
            "effective_settling_rate_mps": round(float(material.settling_velocity_mps), 6),
            "effective_persistence_factor": round(float(persistence_factor), 5),
            "effective_deposition_factor": round(float(dry_loss_per_km), 8),
            "effective_wet_removal_factor": round(float(material.effective_wet_removal_factor), 5),
            "material_crosswind_spread_factor": round(float(material_spread), 5),
            "material_support_factor": round(float(material_support), 5),
            "terrain_local": terrain_local["diagnostics"],
        },
        "manifest": manifest,
    }


def input_from_dict(payload: dict[str, Any]) -> GoverningModelInput:
    # Material profiles also carry explanatory contract metadata such as
    # ``not_claimed``. The numerical governing model intentionally accepts only
    # fields declared by MaterialBehaviorInput and safely ignores presentation
    # or claim-boundary metadata.
    material_payload = payload.get("material", {}) or {}
    allowed_material_fields = MaterialBehaviorInput.__dataclass_fields__
    material_values = {
        key: value
        for key, value in material_payload.items()
        if key in allowed_material_fields
    }

    return GoverningModelInput(
        source=SourceInput(**payload.get("source", {})),
        meteorology=MeteorologyInput(**payload.get("meteorology", {})),
        terrain=TerrainInput(**payload.get("terrain", {})),
        material=MaterialBehaviorInput(**material_values),
        grid=GridInput(**payload.get("grid", {})),
    )
