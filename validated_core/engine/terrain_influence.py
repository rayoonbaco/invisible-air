from __future__ import annotations

import math
from statistics import mean


def classify_terrain(samples: list[dict]) -> dict:
    """Derive restrained terrain context from sampled elevations.

    This is contextual interpretation, not atmospheric dispersion modeling.
    """
    valid = [s for s in samples if isinstance(s.get("elevation_m"), (int, float))]
    if len(valid) < 4:
        return {
            "terrain_class": "unknown",
            "local_relief_m": None,
            "mean_elevation_m": None,
            "slope_hint": "insufficient DEM samples",
            "influence": "terrain influence unresolved",
            "confidence": "not_scored",
        }

    elevations = [float(s["elevation_m"]) for s in valid]
    relief = max(elevations) - min(elevations)
    avg = mean(elevations)

    rows: dict[int, list[dict]] = {}
    for sample in valid:
        rows.setdefault(int(sample.get("row", 0)), []).append(sample)
    row_means = [mean(float(x["elevation_m"]) for x in row) for _, row in sorted(rows.items()) if row]
    north_south_change = row_means[-1] - row_means[0] if len(row_means) >= 2 else 0.0

    cols: dict[int, list[dict]] = {}
    for sample in valid:
        cols.setdefault(int(sample.get("col", 0)), []).append(sample)
    col_means = [mean(float(x["elevation_m"]) for x in col) for _, col in sorted(cols.items()) if col]
    west_east_change = col_means[-1] - col_means[0] if len(col_means) >= 2 else 0.0

    if relief < 20:
        terrain_class = "low relief"
        influence = "open-terrain pathway candidate"
    elif relief < 80:
        terrain_class = "rolling terrain"
        influence = "terrain may widen or gently redirect pathways"
    elif relief < 220:
        terrain_class = "pronounced relief"
        influence = "channeling or blocking deserves human review"
    else:
        terrain_class = "complex terrain"
        influence = "terrain-pathway interaction is likely important but unresolved"

    dominant = "north-south" if abs(north_south_change) >= abs(west_east_change) else "west-east"
    change = north_south_change if dominant == "north-south" else west_east_change
    slope_hint = f"strongest sampled elevation change runs {dominant} ({change:+.1f} m across sample grid)"

    return {
        "terrain_class": terrain_class,
        "local_relief_m": round(relief, 1),
        "mean_elevation_m": round(avg, 1),
        "slope_hint": slope_hint,
        "influence": influence,
        "confidence": "sample_grid_context_only",
    }
