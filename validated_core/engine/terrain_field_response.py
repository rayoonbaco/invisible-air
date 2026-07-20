from __future__ import annotations

"""Bounded, deterministic local-terrain response for Invisible Air Pass 50.

This is a screening-scale terrain transform, not CFD. It creates cell-level
steering, compression, barrier attenuation, divergence, and support arrays from
an explicit terrain profile. Profiles are deterministic benchmark abstractions;
the observatory may later replace them with resampled DEM derivatives.
"""

import math
from typing import Any
import numpy as np

TERRAIN_RESPONSE_VERSION = "ia_terrain_response_v1.0.0"


def _sigmoid(z: np.ndarray, scale: float = 1.0) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(z / max(scale, 1e-6), -30.0, 30.0)))


def build_terrain_response(xx: np.ndarray, yy: np.ndarray, profile: str, strength: float = 1.0,
                           evidence_support: float = 0.85) -> dict[str, Any]:
    """Return cell-level terrain modifiers in model coordinates (km).

    center_shift_km: lateral displacement of the preferred corridor
    width_factor: local crosswind width multiplier
    transmission: local influence attenuation [0,1]
    support_factor: local model-support multiplier [0,1]
    """
    xp = np.maximum(xx, 0.0)
    strength = float(np.clip(strength, 0.0, 1.5))
    evidence = float(np.clip(evidence_support, 0.0, 1.0))
    shape = xx.shape
    center_shift = np.zeros(shape, dtype=float)
    width_factor = np.ones(shape, dtype=float)
    transmission = np.ones(shape, dtype=float)
    support_factor = np.full(shape, evidence, dtype=float)
    diagnostics: dict[str, Any] = {"profile": profile, "response_version": TERRAIN_RESPONSE_VERSION}

    if profile in {"open", "none", "off"} or strength <= 0:
        diagnostics.update({"max_center_shift_km": 0.0, "min_transmission": 1.0, "mean_width_factor": 1.0})
        return {"center_shift_km": center_shift, "width_factor": width_factor,
                "transmission": transmission, "support_factor": support_factor,
                "diagnostics": diagnostics}

    if profile == "valley_aligned":
        # A gently curving valley axis attracts and compresses the field.
        valley_axis = 2.2 * np.sin(xp / 13.0) * (1.0 - np.exp(-xp / 8.0))
        attraction = np.exp(-0.5 * ((yy - valley_axis) / 8.5) ** 2)
        center_shift = valley_axis * strength
        width_factor = 1.0 - 0.34 * strength * attraction
        # Sheltered channel supports persistence; valley shoulders reduce support.
        transmission = 0.90 + 0.10 * attraction
        support_factor *= np.clip(0.72 + 0.28 * attraction, 0.35, 1.0)
        diagnostics["mechanism"] = "valley-axis attraction and channel compression"

    elif profile == "cross_ridge":
        # A ridge crosses the mean transport near x=25 km. The field divides around
        # a central high barrier and partially recovers in the lee.
        ridge = np.exp(-0.5 * ((xp - 25.0) / 4.0) ** 2)
        central_barrier = np.exp(-0.5 * (yy / 7.0) ** 2)
        barrier = ridge * central_barrier
        branch_sign = np.tanh(yy / 3.0)
        downstream = _sigmoid(xp - 21.0, 3.5)
        branch_magnitude = 7.0 * strength * downstream * np.exp(-xp / 95.0)
        center_shift = branch_sign * branch_magnitude
        width_factor = 1.0 + 0.42 * strength * ridge + 0.20 * strength * downstream
        transmission = np.clip(1.0 - 0.58 * strength * barrier, 0.30, 1.0)
        lee = np.exp(-0.5 * ((xp - 34.0) / 9.0) ** 2) * central_barrier
        support_factor *= np.clip(1.0 - 0.38 * strength * barrier - 0.20 * strength * lee, 0.30, 1.0)
        diagnostics["mechanism"] = "cross-ridge resistance, lee weakening, and deterministic divergence"

    elif profile == "complex":
        # Multiple bounded terrain influences create modest, explainable meander
        # and localized support loss without overwhelming the wind field.
        shift = (2.4 * np.sin(xp / 9.0) + 1.3 * np.sin(xp / 4.7)) * (1.0 - np.exp(-xp / 9.0))
        center_shift = shift * strength
        rough = 0.5 + 0.5 * np.sin(xp / 5.5 + yy / 8.0)
        width_factor = 1.0 + 0.22 * strength * rough
        transmission = np.clip(0.86 + 0.14 * (1.0 - rough), 0.60, 1.0)
        support_factor *= np.clip(0.62 + 0.30 * (1.0 - rough), 0.30, 1.0)
        diagnostics["mechanism"] = "bounded multi-landform steering and roughness dispersion"

    else:
        diagnostics["mechanism"] = "unknown profile; neutral terrain response"

    diagnostics.update({
        "max_center_shift_km": round(float(np.max(np.abs(center_shift))), 4),
        "min_transmission": round(float(np.min(transmission)), 4),
        "mean_width_factor": round(float(np.mean(width_factor)), 4),
        "mean_support_factor": round(float(np.mean(support_factor)), 4),
    })
    return {"center_shift_km": center_shift, "width_factor": np.clip(width_factor, 0.55, 1.65),
            "transmission": np.clip(transmission, 0.20, 1.0),
            "support_factor": np.clip(support_factor, 0.0, 1.0), "diagnostics": diagnostics}
