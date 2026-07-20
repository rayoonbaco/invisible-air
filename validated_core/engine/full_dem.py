from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "dem_cache"
RASTER_FILE = CACHE_DIR / "default_scene_3dep_dem.tif"
METADATA_FILE = CACHE_DIR / "default_scene_3dep_dem.json"
EXPORT_URL = os.environ.get(
    "AW_USGS_3DEP_EXPORT_URL",
    "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage",
)
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 512
MIN_RASTER_BYTES = 4096


def _relative(path: Path) -> str:
    return str(path.relative_to(path.parents[2])).replace("\\", "/")


def _base_contract(scene: dict) -> dict:
    bbox = [float(value) for value in scene["location"]["bbox"]]
    west, south, east, north = bbox
    approx_width_m = max(1.0, (east - west) * 111_320.0 * max(0.2, __import__('math').cos(__import__('math').radians((south+north)/2))))
    approx_height_m = max(1.0, (north - south) * 110_540.0)
    return {
        "contract_version": "1.0",
        "pass_id": "SV2-35",
        "layer": "full_dem",
        "provider": "USGS 3DEP Elevation ImageServer",
        "source_type": "continuous_elevation_raster",
        "bbox": bbox,
        "spatial_reference": "EPSG:4326 request; provider-returned TIFF raster",
        "requested_grid": {"width": DEFAULT_WIDTH, "height": DEFAULT_HEIGHT},
        "approx_pixel_size_m": {
            "x": round(approx_width_m / DEFAULT_WIDTH, 2),
            "y": round(approx_height_m / DEFAULT_HEIGHT, 2),
        },
        "raster_path": _relative(RASTER_FILE),
        "metadata_path": _relative(METADATA_FILE),
        "source_endpoint": EXPORT_URL,
        "evidence_state": "measured",
        "visual_role": "continuous terrain foundation for later hillshade, slope, aspect, curvature, and 3D terrain",
        "claim_boundary": "The cached raster is terrain elevation context. It is not methane evidence, atmospheric transport, source attribution, or a certified derived hillshade product.",
    }


def _request_url(contract: dict) -> str:
    west, south, east, north = contract["bbox"]
    width = contract["requested_grid"]["width"]
    height = contract["requested_grid"]["height"]
    query = urlencode({
        "bbox": f"{west},{south},{east},{north}",
        "bboxSR": 4326,
        "imageSR": 4326,
        "size": f"{width},{height}",
        "format": "tiff",
        "pixelType": "F32",
        "interpolation": "RSP_BilinearInterpolation",
        "f": "image",
    })
    return f"{EXPORT_URL}?{query}"


def _valid_tiff(data: bytes) -> bool:
    return len(data) >= MIN_RASTER_BYTES and data[:4] in {b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"}


def refresh_full_dem(scene: dict, timeout: float = 45.0) -> dict:
    contract = _base_contract(scene)
    request_url = _request_url(contract)
    attempted_at = datetime.now(timezone.utc).isoformat()
    try:
        request = Request(request_url, headers={"User-Agent": "InvisibleAir-SV2-35/1.0"})
        with urlopen(request, timeout=timeout) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type", "")
        if not _valid_tiff(data):
            raise ValueError(f"provider response was not a valid TIFF raster ({len(data)} bytes; {content_type})")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        RASTER_FILE.write_bytes(data)
        contract.update({
            "data_state": "continuous_dem_cache",
            "cache_status": "refreshed",
            "coverage_status": "requested_bbox_covered",
            "coverage_ratio": 1.0,
            "retrieved_at_utc": attempted_at,
            "byte_size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "content_type": content_type or "image/tiff",
            "request_url": request_url,
            "display_label": f"continuous 3DEP DEM cached · {DEFAULT_WIDTH} × {DEFAULT_HEIGHT}",
            "failure_reason": None,
        })
    except Exception as exc:
        contract.update({
            "data_state": "provider_unavailable_no_dem_cache",
            "cache_status": "refresh_failed",
            "coverage_status": "unresolved",
            "coverage_ratio": 0.0,
            "retrieved_at_utc": None,
            "attempted_at_utc": attempted_at,
            "byte_size": 0,
            "sha256": None,
            "content_type": None,
            "request_url": request_url,
            "display_label": "continuous DEM request failed · sparse terrain remains active",
            "failure_reason": str(exc)[:240],
        })
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_FILE.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return contract


def full_dem_context(scene: dict, refresh: bool = False) -> dict:
    if refresh:
        return refresh_full_dem(scene)
    contract = _base_contract(scene)
    if METADATA_FILE.exists():
        try:
            cached = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
            if cached.get("bbox") == contract["bbox"]:
                if cached.get("data_state") == "continuous_dem_cache" and RASTER_FILE.exists():
                    data = RASTER_FILE.read_bytes()
                    if _valid_tiff(data) and hashlib.sha256(data).hexdigest() == cached.get("sha256"):
                        cached["cache_status"] = "loaded"
                        cached["pass_id"] = "SV2-35"
                        return cached
                if cached.get("cache_status") == "refresh_failed":
                    cached["pass_id"] = "SV2-35"
                    return cached
        except (OSError, ValueError, TypeError):
            pass
    contract.update({
        "data_state": "dem_loader_ready_cache_pending",
        "cache_status": "missing",
        "coverage_status": "unresolved",
        "coverage_ratio": 0.0,
        "retrieved_at_utc": None,
        "byte_size": 0,
        "sha256": None,
        "content_type": None,
        "request_url": _request_url(contract),
        "display_label": "continuous DEM lane ready · raster cache pending",
        "failure_reason": None,
    })
    return contract
