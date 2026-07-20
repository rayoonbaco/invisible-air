from __future__ import annotations

import math

from engine.spatial_plume import destination_point


def _bearing_between(a: dict, b: dict) -> float:
    lat1 = math.radians(float(a["lat"]))
    lat2 = math.radians(float(b["lat"]))
    dlon = math.radians(float(b["lon"]) - float(a["lon"]))
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360.0) % 360.0


def _distance_km(a: dict, b: dict) -> float:
    lat1, lon1 = math.radians(float(a["lat"])), math.radians(float(a["lon"]))
    lat2, lon2 = math.radians(float(b["lat"])), math.radians(float(b["lon"]))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(min(1.0, math.sqrt(h)))


def _idw_elevation(samples: list[dict], point: dict) -> float | None:
    valid = [s for s in samples if isinstance(s.get("elevation_m"), (int, float))]
    if not valid:
        return None
    weighted = 0.0
    weight_sum = 0.0
    for sample in valid:
        distance = max(0.08, _distance_km(point, sample))
        weight = 1.0 / (distance * distance)
        weighted += float(sample["elevation_m"]) * weight
        weight_sum += weight
    return weighted / weight_sum if weight_sum else None


def build_terrain_flow_path(
    source: dict,
    wind_to_degrees: float,
    length_km: float,
    terrain: dict,
    nodes: int = 11,
) -> dict:
    """Build a restrained terrain-informed visual pathway.

    Sparse measured elevations are sampled on both sides of the wind axis. The
    pathway may shift gently toward relatively lower sampled ground and show
    extra disruption where cross-path elevation contrast is large. This is a
    visual review heuristic, not fluid dynamics or a dispersion model.
    """
    measured = terrain.get("data_state") == "measured_sample_cache"
    samples = terrain.get("samples") or []
    relief = float(terrain.get("local_relief_m") or 0.0)
    if not measured or len(samples) < 4:
        points = [destination_point(source["lat"], source["lon"], wind_to_degrees, length_km * i / (nodes - 1)) for i in range(nodes)]
        return {
            "mode": "neutral_wind_axis",
            "data_state": "neutral_pending_measured_terrain",
            "points": points,
            "node_diagnostics": [],
            "max_lateral_shift_km": 0.0,
            "terrain_response": "neutral",
            "claim_boundary": "Wind-axis visual pathway only; measured terrain was unavailable. This is not atmospheric dispersion modeling or exact plume geometry.",
        }

    raw_offsets: list[float] = []
    diagnostics: list[dict] = []
    contrast_scale = max(35.0, min(260.0, relief * 0.32))
    for i in range(nodes):
        t = i / (nodes - 1)
        baseline = destination_point(source["lat"], source["lon"], wind_to_degrees, length_km * t)
        probe_km = 1.15 + 1.35 * math.sin(math.pi * t)
        left = destination_point(baseline["lat"], baseline["lon"], wind_to_degrees - 90.0, probe_km)
        right = destination_point(baseline["lat"], baseline["lon"], wind_to_degrees + 90.0, probe_km)
        left_elev = _idw_elevation(samples, left)
        right_elev = _idw_elevation(samples, right)
        if left_elev is None or right_elev is None or i in {0, nodes - 1}:
            offset = 0.0
            contrast = 0.0
        else:
            contrast = right_elev - left_elev
            # Positive contrast means the left probe is lower. Shift is capped,
            # tapered at both ends, and deliberately conservative.
            normalized = max(-1.0, min(1.0, contrast / contrast_scale))
            taper = math.sin(math.pi * t) ** 1.25
            offset = -normalized * min(1.35, 0.34 + relief / 650.0) * taper
        raw_offsets.append(offset)
        diagnostics.append({
            "index": i,
            "fraction": round(t, 3),
            "left_elevation_m": None if left_elev is None else round(left_elev, 1),
            "right_elevation_m": None if right_elev is None else round(right_elev, 1),
            "cross_path_contrast_m": round(contrast, 1),
            "raw_lateral_shift_km": round(offset, 3),
        })

    # Two light smoothing passes prevent a jagged path from sparse samples.
    offsets = raw_offsets[:]
    for _ in range(2):
        offsets = [
            offsets[i] if i in {0, len(offsets) - 1}
            else offsets[i - 1] * 0.25 + offsets[i] * 0.5 + offsets[i + 1] * 0.25
            for i in range(len(offsets))
        ]

    points: list[dict] = []
    for i, offset in enumerate(offsets):
        t = i / (nodes - 1)
        baseline = destination_point(source["lat"], source["lon"], wind_to_degrees, length_km * t)
        bearing = wind_to_degrees - 90.0 if offset < 0 else wind_to_degrees + 90.0
        shifted = destination_point(baseline["lat"], baseline["lon"], bearing, abs(offset))
        points.append(shifted)
        diagnostics[i]["smoothed_lateral_shift_km"] = round(offset, 3)

    max_shift = max(abs(x) for x in offsets)
    max_contrast = max(abs(float(d["cross_path_contrast_m"])) for d in diagnostics)
    if max_shift < 0.18:
        response = "wind-dominant pathway"
    elif max_contrast >= 120:
        response = "ridge-crossing disruption"
    else:
        response = "terrain-guided redirection"

    return {
        "mode": "measured_terrain_informed_visual_path",
        "data_state": "measured_terrain_applied",
        "points": points,
        "node_diagnostics": diagnostics,
        "max_lateral_shift_km": round(max_shift, 3),
        "max_cross_path_contrast_m": round(max_contrast, 1),
        "terrain_response": response,
        "end_bearing_degrees": round(_bearing_between(points[-2], points[-1]), 2),
        "claim_boundary": "Sparse measured elevation gently shapes this visual review pathway; it is not atmospheric dispersion modeling or exact plume geometry.",
    }
