from __future__ import annotations

import math


def _angular_difference(a: float, b: float) -> float:
    diff = abs((a - b + 180.0) % 360.0 - 180.0)
    return min(diff, 180.0 - diff)


def terrain_affected_behavior(terrain: dict, wind_to_degrees: float) -> dict:
    """Return a restrained visual-behavior contract from measured terrain context.

    This is a review heuristic for visualization. It is not a fluid-dynamics,
    methane-dispersion, or source-attribution model.
    """
    measured = terrain.get("data_state") == "measured_sample_cache"
    relief = terrain.get("local_relief_m")
    slope_hint = str(terrain.get("slope_hint", ""))

    base = {
        "mode": "terrain_affected_visual_heuristic",
        "data_state": "measured_terrain_applied" if measured else "neutral_pending_measured_terrain",
        "measured_terrain_used": measured,
        "width_multiplier": 1.0,
        "length_multiplier": 1.0,
        "bend_degrees": 0.0,
        "turbulence": 0.18,
        "channeling": "unresolved",
        "display_label": "neutral pathway · measured terrain pending",
        "explanation": "The reconstruction remains wind-oriented until measured elevation context is available.",
        "claim_boundary": "Terrain affects only this visual review heuristic; it is not atmospheric dispersion modeling or exact plume geometry.",
    }
    if not measured or not isinstance(relief, (int, float)):
        return base

    relief = float(relief)
    if relief < 20:
        width_multiplier = 1.18
        length_multiplier = 1.04
        turbulence = 0.14
        channeling = "open-spread tendency"
    elif relief < 80:
        width_multiplier = 1.04
        length_multiplier = 1.0
        turbulence = 0.22
        channeling = "gentle redirection review"
    elif relief < 220:
        width_multiplier = 0.86
        length_multiplier = 1.05
        turbulence = 0.31
        channeling = "possible terrain channeling"
    else:
        width_multiplier = 0.74
        length_multiplier = 0.93
        turbulence = 0.42
        channeling = "complex-terrain disruption"

    axis_bearing = None
    if "north-south" in slope_hint:
        axis_bearing = 0.0
    elif "west-east" in slope_hint:
        axis_bearing = 90.0

    bend = 0.0
    alignment_note = "sample-grid landform axis unresolved"
    if axis_bearing is not None:
        difference = _angular_difference(float(wind_to_degrees), axis_bearing)
        alignment = max(0.0, 1.0 - difference / 90.0)
        if relief >= 80:
            # Small, capped visual bend toward the sampled elevation axis.
            signed = ((axis_bearing - float(wind_to_degrees) + 540.0) % 360.0) - 180.0
            bend = max(-12.0, min(12.0, signed * 0.12 * alignment))
        alignment_note = f"wind/landform-axis alignment factor {alignment:.2f}"

    return {
        **base,
        "data_state": "measured_terrain_applied",
        "measured_terrain_used": True,
        "width_multiplier": round(width_multiplier, 3),
        "length_multiplier": round(length_multiplier, 3),
        "bend_degrees": round(bend, 2),
        "turbulence": round(turbulence, 3),
        "channeling": channeling,
        "display_label": f"{channeling} · {relief:.1f} m sampled relief",
        "explanation": f"Measured sample-grid relief changes visual width, continuity, and turbulence; {alignment_note}.",
    }
