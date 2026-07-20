from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from engine.terrain_influence import classify_terrain

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "terrain_cache"
CACHE_FILE = CACHE_DIR / "default_scene_terrain.json"
EPQS_URL = os.environ.get("AW_USGS_EPQS_URL", "https://epqs.nationalmap.gov/v1/json")
MIN_USABLE_SAMPLES = 4


def _base_contract(scene: dict) -> dict:
    location = scene["location"]
    return {
        "layer": "terrain",
        "status": "terrain_loader_sv2_12",
        "source_mode": "usgs_epqs_sample_grid_with_local_cache",
        "provider": "USGS Elevation Point Query Service / 3DEP-backed elevation context",
        "bbox": location["bbox"],
        "center": {"lat": location["lat"], "lon": location["lon"]},
        "sample_grid": {"rows": 5, "cols": 5, "requested_points": 25},
        "cache_path": str(CACHE_FILE.relative_to(CACHE_FILE.parents[2])).replace("\\", "/"),
        "visual_role": "terrain changes pathway interpretation",
        "what_it_can_help_see": "sampled landform relief and possible terrain influence on pathway review",
        "what_it_cannot_prove": "terrain does not prove methane detection, source responsibility, exact plume geometry, or atmospheric dispersion",
        "claim_strength": "measured_elevation_context_when_cached",
    }


def _grid_points(bbox: list[float], rows: int = 5, cols: int = 5) -> list[dict]:
    west, south, east, north = bbox
    points = []
    for row in range(rows):
        lat = south + (north - south) * row / max(rows - 1, 1)
        for col in range(cols):
            lon = west + (east - west) * col / max(cols - 1, 1)
            points.append({"row": row, "col": col, "lat": round(lat, 6), "lon": round(lon, 6)})
    return points


def _fetch_point(lat: float, lon: float, timeout: float = 6.0) -> float:
    query = urlencode({"x": lon, "y": lat, "units": "Meters", "wkid": 4326, "includeDate": "false"})
    request = Request(f"{EPQS_URL}?{query}", headers={"User-Agent": "InvisibleAir-SV2-10/1.0"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    value = payload.get("value")
    if value is None:
        value = payload.get("USGS_Elevation_Point_Query_Service", {}).get("Elevation_Query", {}).get("Elevation")
    if value is None:
        raise ValueError("USGS elevation response did not contain an elevation value")
    return float(value)


def _sample_point(point: dict) -> dict:
    elevation = _fetch_point(point["lat"], point["lon"])
    return {**point, "elevation_m": round(elevation, 2)}


def refresh_terrain_cache(scene: dict) -> dict:
    contract = _base_contract(scene)
    points = _grid_points(contract["bbox"])
    samples: list[dict] = []
    errors: list[dict] = []

    # Parallel sampling keeps startup bounded while preserving point-level failure reporting.
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_sample_point, point): point for point in points}
        for future in as_completed(futures):
            point = futures[future]
            try:
                samples.append(future.result())
            except Exception as exc:  # external service failures must not break the app
                errors.append({**point, "error": str(exc)[:180]})

    samples.sort(key=lambda item: (item["row"], item["col"]))
    errors.sort(key=lambda item: (item["row"], item["col"]))
    contract.update({
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "samples": samples,
        "failed_samples": errors,
        "sample_count": len(samples),
        "refresh_attempted": True,
    })
    contract.update(classify_terrain(samples))
    contract["data_state"] = "measured_sample_cache" if len(samples) >= MIN_USABLE_SAMPLES else "provider_unavailable_no_measured_cache"
    contract["cache_status"] = "refreshed" if len(samples) >= MIN_USABLE_SAMPLES else "refresh_failed"
    contract["display_label"] = (
        f"{contract['terrain_class']} · {contract['local_relief_m']} m sampled relief"
        if contract["local_relief_m"] is not None
        else "terrain refresh attempted · measured cache unavailable"
    )

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return contract


def terrain_context(scene: dict, refresh: bool = False) -> dict:
    if refresh:
        return refresh_terrain_cache(scene)

    contract = _base_contract(scene)
    if CACHE_FILE.exists():
        try:
            cached = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            if cached.get("bbox") == contract["bbox"]:
                if cached.get("sample_count", 0) >= MIN_USABLE_SAMPLES:
                    cached["cache_status"] = "loaded"
                    cached["status"] = "terrain_loader_sv2_12"
                    return cached
                # Preserve an honest failed-attempt state instead of pretending no attempt occurred.
                if cached.get("refresh_attempted"):
                    cached["cache_status"] = "refresh_failed"
                    cached["status"] = "terrain_loader_sv2_12"
                    return cached
        except (OSError, ValueError, TypeError):
            pass

    contract.update({
        "data_state": "loader_ready_cache_pending",
        "cache_status": "missing",
        "sample_count": 0,
        "samples": [],
        "failed_samples": [],
        "refresh_attempted": False,
        "terrain_class": "pending measured sample",
        "local_relief_m": None,
        "mean_elevation_m": None,
        "slope_hint": "automatic startup refresh has not completed",
        "influence": "terrain influence unresolved until measured elevations are cached",
        "confidence": "not_scored",
        "display_label": "terrain lane ready · automatic measured sample pending",
    })
    return contract
