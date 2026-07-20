from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

from engine.full_dem import RASTER_FILE, full_dem_context

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "hillshade_cache"
HILLSHADE_FILE = CACHE_DIR / "default_scene_hillshade.png"
METADATA_FILE = CACHE_DIR / "default_scene_hillshade.json"
DEFAULT_AZIMUTH_DEG = 315.0
DEFAULT_ALTITUDE_DEG = 45.0
DEFAULT_Z_FACTOR = 1.0
MIN_VALID_RATIO = 0.90


def _relative(path: Path) -> str:
    return str(path.relative_to(path.parents[2])).replace("\\", "/")


def _base_contract(scene: dict, dem: dict) -> dict:
    return {
        "contract_version": "1.0",
        "pass_id": "SV2-35",
        "layer": "dem_derived_hillshade",
        "source_dem_sha256": dem.get("sha256"),
        "source_dem_provider": dem.get("provider"),
        "source_dem_bbox": dem.get("bbox"),
        "source_dem_grid": dem.get("requested_grid"),
        "source_dem_retrieved_at_utc": dem.get("retrieved_at_utc"),
        "illumination": {
            "azimuth_degrees": DEFAULT_AZIMUTH_DEG,
            "altitude_degrees": DEFAULT_ALTITUDE_DEG,
            "z_factor": DEFAULT_Z_FACTOR,
            "interpretation": "fixed northwest illumination for reproducible terrain reading",
        },
        "output_path": _relative(HILLSHADE_FILE),
        "metadata_path": _relative(METADATA_FILE),
        "evidence_state": "measured",
        "visual_role": "continuous terrain relief beneath the atmospheric review layer",
        "claim_boundary": "This is a reproducible hillshade derived from the cached DEM. It is not agency-certified, methane evidence, solar illumination at observation time, or atmospheric transport modeling.",
    }


def _read_dem() -> np.ndarray:
    array = np.asarray(tifffile.imread(RASTER_FILE))
    array = np.squeeze(array)
    if array.ndim != 2:
        raise ValueError(f"DEM raster must resolve to one 2D elevation band, got shape {array.shape}")
    array = array.astype(np.float64, copy=False)
    finite = np.isfinite(array)
    finite &= np.abs(array) < 1.0e20
    if finite.mean() < MIN_VALID_RATIO:
        raise ValueError(f"DEM valid-cell ratio too low ({finite.mean():.3f})")
    if not finite.all():
        fill = float(np.nanmedian(np.where(finite, array, np.nan)))
        array = np.where(finite, array, fill)
    return array


def _derive_hillshade(elevation: np.ndarray, pixel_x_m: float, pixel_y_m: float) -> tuple[np.ndarray, dict]:
    dx = max(float(pixel_x_m), 0.01)
    dy = max(float(pixel_y_m), 0.01)
    grad_y, grad_x = np.gradient(elevation, dy, dx)
    slope = np.arctan(np.hypot(grad_x, grad_y) * DEFAULT_Z_FACTOR)
    aspect = np.arctan2(-grad_x, grad_y)
    azimuth = np.deg2rad(DEFAULT_AZIMUTH_DEG)
    altitude = np.deg2rad(DEFAULT_ALTITUDE_DEG)
    illumination = (
        np.sin(altitude) * np.cos(slope)
        + np.cos(altitude) * np.sin(slope) * np.cos(azimuth - aspect)
    )
    normalized = np.clip((illumination + 1.0) * 127.5, 0, 255).astype(np.uint8)
    stats = {
        "elevation_min_m": round(float(np.min(elevation)), 3),
        "elevation_max_m": round(float(np.max(elevation)), 3),
        "elevation_range_m": round(float(np.ptp(elevation)), 3),
        "shade_min": int(normalized.min()),
        "shade_max": int(normalized.max()),
        "shade_mean": round(float(normalized.mean()), 3),
        "valid_cell_ratio": 1.0,
    }
    return normalized, stats


def refresh_hillshade(scene: dict) -> dict:
    dem = full_dem_context(scene)
    contract = _base_contract(scene, dem)
    attempted_at = datetime.now(timezone.utc).isoformat()
    if dem.get("data_state") != "continuous_dem_cache" or not RASTER_FILE.exists():
        contract.update({
            "data_state": "hillshade_unavailable_no_valid_dem",
            "cache_status": "not_generated",
            "coverage_status": "unresolved",
            "generated_at_utc": None,
            "attempted_at_utc": attempted_at,
            "display_label": "DEM-derived hillshade unavailable · valid DEM required",
            "failure_reason": "No validated continuous DEM cache is available.",
            "image_sha256": None,
            "byte_size": 0,
            "raster_stats": None,
        })
    else:
        try:
            elevation = _read_dem()
            pixel = dem.get("approx_pixel_size_m", {})
            hillshade, stats = _derive_hillshade(elevation, pixel.get("x", 1.0), pixel.get("y", 1.0))
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            image = Image.fromarray(hillshade, mode="L")
            image.save(HILLSHADE_FILE, format="PNG", optimize=True)
            image_bytes = HILLSHADE_FILE.read_bytes()
            contract.update({
                "data_state": "dem_derived_hillshade_cache",
                "cache_status": "refreshed",
                "coverage_status": "source_dem_bbox_covered",
                "generated_at_utc": attempted_at,
                "attempted_at_utc": attempted_at,
                "display_label": f"DEM-derived hillshade ready · {elevation.shape[1]} × {elevation.shape[0]}",
                "failure_reason": None,
                "image_sha256": hashlib.sha256(image_bytes).hexdigest(),
                "byte_size": len(image_bytes),
                "output_grid": {"width": int(elevation.shape[1]), "height": int(elevation.shape[0])},
                "raster_stats": stats,
                "image_url": "/hillshade-image",
            })
        except Exception as exc:
            contract.update({
                "data_state": "hillshade_generation_failed",
                "cache_status": "refresh_failed",
                "coverage_status": "unresolved",
                "generated_at_utc": None,
                "attempted_at_utc": attempted_at,
                "display_label": "DEM-derived hillshade generation failed",
                "failure_reason": str(exc)[:300],
                "image_sha256": None,
                "byte_size": 0,
                "raster_stats": None,
            })
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_FILE.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return contract


def hillshade_context(scene: dict, refresh: bool = False) -> dict:
    if refresh:
        return refresh_hillshade(scene)
    dem = full_dem_context(scene)
    contract = _base_contract(scene, dem)
    if METADATA_FILE.exists():
        try:
            cached = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
            same_dem = cached.get("source_dem_sha256") == dem.get("sha256")
            if cached.get("data_state") == "dem_derived_hillshade_cache" and same_dem and HILLSHADE_FILE.exists():
                image_bytes = HILLSHADE_FILE.read_bytes()
                if hashlib.sha256(image_bytes).hexdigest() == cached.get("image_sha256"):
                    cached["cache_status"] = "loaded"
                    cached["pass_id"] = "SV2-35"
                    return cached
            if cached.get("data_state") in {"hillshade_unavailable_no_valid_dem", "hillshade_generation_failed"} and same_dem:
                cached["pass_id"] = "SV2-35"
                return cached
        except (OSError, ValueError, TypeError):
            pass
    if dem.get("data_state") == "continuous_dem_cache":
        contract.update({
            "data_state": "hillshade_ready_to_generate",
            "cache_status": "missing",
            "coverage_status": "source_dem_available",
            "generated_at_utc": None,
            "display_label": "validated DEM ready · hillshade cache pending",
            "failure_reason": None,
            "image_sha256": None,
            "byte_size": 0,
            "raster_stats": None,
        })
    else:
        contract.update({
            "data_state": "hillshade_unavailable_no_valid_dem",
            "cache_status": "missing",
            "coverage_status": "unresolved",
            "generated_at_utc": None,
            "display_label": "DEM-derived hillshade unavailable · valid DEM required",
            "failure_reason": None,
            "image_sha256": None,
            "byte_size": 0,
            "raster_stats": None,
        })
    return contract
