from __future__ import annotations

import math

EARTH_RADIUS_KM = 6371.0088


def destination_point(lat: float, lon: float, bearing_deg: float, distance_km: float) -> dict:
    bearing = math.radians(bearing_deg)
    lat1 = math.radians(lat)
    lon1 = math.radians(lon)
    d = distance_km / EARTH_RADIUS_KM
    lat2 = math.asin(math.sin(lat1) * math.cos(d) + math.cos(lat1) * math.sin(d) * math.cos(bearing))
    lon2 = lon1 + math.atan2(math.sin(bearing) * math.sin(d) * math.cos(lat1), math.cos(d) - math.sin(lat1) * math.sin(lat2))
    return {"lat": math.degrees(lat2), "lon": math.degrees(lon2)}


def ellipse_polygon(center_lat: float, center_lon: float, bearing_deg: float, length_km: float, width_km: float, points: int = 96) -> list[dict]:
    coords: list[dict] = []
    major, minor = length_km / 2, width_km / 2
    theta = math.radians(bearing_deg)
    km_per_deg_lat = 110.574
    km_per_deg_lon = max(1e-9, 111.320 * math.cos(math.radians(center_lat)))
    for i in range(points):
        a = 2 * math.pi * i / points
        x, y = major * math.cos(a), minor * math.sin(a)
        xr = x * math.sin(theta) + y * math.cos(theta)
        yr = x * math.cos(theta) - y * math.sin(theta)
        coords.append({"lat": center_lat + yr / km_per_deg_lat, "lon": center_lon + xr / km_per_deg_lon})
    return coords


def _tube_polygon(path: list[dict], width_km: float) -> list[dict]:
    if len(path) < 2:
        return []
    left: list[dict] = []
    right: list[dict] = []
    for i, point in enumerate(path):
        before = path[max(0, i - 1)]
        after = path[min(len(path) - 1, i + 1)]
        lat1, lat2 = math.radians(before["lat"]), math.radians(after["lat"])
        dlon = math.radians(after["lon"] - before["lon"])
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        bearing = (math.degrees(math.atan2(y, x)) + 360.0) % 360.0
        t = i / max(1, len(path) - 1)
        half_width = width_km * (0.28 + 0.72 * math.sin(math.pi * max(0.03, t)) ** 0.7) / 2
        left.append(destination_point(point["lat"], point["lon"], bearing - 90, half_width))
        right.append(destination_point(point["lat"], point["lon"], bearing + 90, half_width))
    return left + list(reversed(right))


def build_plume_geometry(source: dict, wind_to_degrees: float, length_km: float, width_km: float, flow_path: dict | None = None) -> dict:
    start = {"lat": float(source["lat"]), "lon": float(source["lon"])}
    path = (flow_path or {}).get("points") or [start, destination_point(start["lat"], start["lon"], wind_to_degrees, length_km)]
    path[0] = start
    end = path[-1]
    if len(path) > 2:
        uncertainty = _tube_polygon(path, width_km * 1.65)
    else:
        center = destination_point(start["lat"], start["lon"], wind_to_degrees, length_km * 0.52)
        uncertainty = ellipse_polygon(center["lat"], center["lon"], wind_to_degrees, length_km * 1.08, width_km * 1.65)
    return {
        "mode": "map_registered_visual_reconstruction",
        "source": start,
        "centerline": path,
        "downwind_end": end,
        "wind_to_degrees": wind_to_degrees,
        "length_km": length_km,
        "width_km": width_km,
        "uncertainty_polygon": uncertainty,
        "flow_path": flow_path or {"mode": "neutral_wind_axis", "points": path},
        "claim_boundary": "Coordinate-registered terrain-informed visual reconstruction; not exact methane plume-product geometry.",
    }
