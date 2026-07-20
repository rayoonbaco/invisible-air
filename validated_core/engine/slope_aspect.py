from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

from engine.full_dem import RASTER_FILE, full_dem_context

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "terrain_derivatives_cache"
SLOPE_FILE = CACHE_DIR / "default_scene_slope.png"
ASPECT_FILE = CACHE_DIR / "default_scene_aspect.png"
METADATA_FILE = CACHE_DIR / "default_scene_slope_aspect.json"
MIN_VALID_RATIO = 0.90


def _relative(path: Path) -> str:
    return str(path.relative_to(path.parents[2])).replace("\\", "/")


def _read_dem() -> np.ndarray:
    array = np.squeeze(np.asarray(tifffile.imread(RASTER_FILE))).astype(np.float64, copy=False)
    if array.ndim != 2:
        raise ValueError(f"DEM raster must be 2D, got {array.shape}")
    finite = np.isfinite(array) & (np.abs(array) < 1.0e20)
    if float(finite.mean()) < MIN_VALID_RATIO:
        raise ValueError(f"DEM valid-cell ratio too low ({finite.mean():.3f})")
    if not finite.all():
        fill = float(np.nanmedian(np.where(finite, array, np.nan)))
        array = np.where(finite, array, fill)
    return array


def _derive(elevation: np.ndarray, pixel_x_m: float, pixel_y_m: float):
    dy=max(float(pixel_y_m),0.01); dx=max(float(pixel_x_m),0.01)
    grad_y, grad_x = np.gradient(elevation, dy, dx)
    slope_deg = np.degrees(np.arctan(np.hypot(grad_x, grad_y)))
    aspect_deg = (np.degrees(np.arctan2(grad_x, -grad_y)) + 360.0) % 360.0
    flat = slope_deg < 0.5
    # slope visualization: 0-60 degrees mapped to grayscale
    slope_img = np.clip((slope_deg / 60.0) * 255.0, 0, 255).astype(np.uint8)
    # aspect visualization: HSV hue follows compass direction; low saturation for flats
    h = np.clip(aspect_deg / 360.0 * 255.0, 0, 255).astype(np.uint8)
    sat = np.where(flat, 0, 150).astype(np.uint8)
    val = np.where(flat, 160, 225).astype(np.uint8)
    hsv = np.dstack([h, sat, val])
    aspect_img = np.asarray(Image.fromarray(hsv, mode="HSV").convert("RGB"))
    stats = {
        "slope_min_degrees": round(float(slope_deg.min()),3),
        "slope_max_degrees": round(float(slope_deg.max()),3),
        "slope_mean_degrees": round(float(slope_deg.mean()),3),
        "slope_p95_degrees": round(float(np.percentile(slope_deg,95)),3),
        "flat_cell_ratio": round(float(flat.mean()),4),
        "aspect_convention": "clockwise degrees from north; flat cells visually neutral",
        "valid_cell_ratio": 1.0,
    }
    return slope_img, aspect_img, stats


def _base(scene: dict, dem: dict) -> dict:
    return {
        "contract_version":"1.0","pass_id":"SV2-35","layer":"dem_derived_slope_aspect",
        "source_dem_sha256":dem.get("sha256"),"source_dem_provider":dem.get("provider"),
        "source_dem_bbox":dem.get("bbox"),"source_dem_grid":dem.get("requested_grid"),
        "slope_output_path":_relative(SLOPE_FILE),"aspect_output_path":_relative(ASPECT_FILE),
        "metadata_path":_relative(METADATA_FILE),"evidence_state":"measured",
        "derivation": {"slope":"arctangent of horizontal elevation-gradient magnitude","aspect":"clockwise downslope orientation from north","units":"degrees"},
        "visual_role":"continuous terrain steepness and orientation context for later landform classification",
        "claim_boundary":"Slope and aspect are DEM-derived terrain context. They are not atmospheric transport, methane evidence, event-time conditions, or proof of source responsibility.",
    }


def refresh_slope_aspect(scene: dict) -> dict:
    dem=full_dem_context(scene); c=_base(scene,dem); now=datetime.now(timezone.utc).isoformat()
    if dem.get("data_state")!="continuous_dem_cache" or not RASTER_FILE.exists():
        c.update({"data_state":"slope_aspect_unavailable_no_valid_dem","cache_status":"not_generated","coverage_status":"unresolved","generated_at_utc":None,"display_label":"slope and aspect unavailable · valid DEM required","failure_reason":"No validated continuous DEM cache is available.","statistics":None})
    else:
        try:
            elev=_read_dem(); pix=dem.get("approx_pixel_size_m",{})
            slope,aspect,stats=_derive(elev,pix.get("x",1),pix.get("y",1))
            CACHE_DIR.mkdir(parents=True,exist_ok=True)
            Image.fromarray(slope,mode="L").save(SLOPE_FILE,format="PNG",optimize=True)
            Image.fromarray(aspect,mode="RGB").save(ASPECT_FILE,format="PNG",optimize=True)
            sb=SLOPE_FILE.read_bytes(); ab=ASPECT_FILE.read_bytes()
            c.update({"data_state":"dem_derived_slope_aspect_cache","cache_status":"refreshed","coverage_status":"source_dem_bbox_covered","generated_at_utc":now,"display_label":f"DEM-derived slope + aspect ready · {elev.shape[1]} × {elev.shape[0]}","failure_reason":None,"output_grid":{"width":int(elev.shape[1]),"height":int(elev.shape[0])},"slope_sha256":hashlib.sha256(sb).hexdigest(),"aspect_sha256":hashlib.sha256(ab).hexdigest(),"slope_byte_size":len(sb),"aspect_byte_size":len(ab),"statistics":stats,"slope_image_url":"/slope-image","aspect_image_url":"/aspect-image"})
        except Exception as exc:
            c.update({"data_state":"slope_aspect_generation_failed","cache_status":"refresh_failed","coverage_status":"unresolved","generated_at_utc":None,"display_label":"slope and aspect generation failed","failure_reason":str(exc)[:300],"statistics":None})
    CACHE_DIR.mkdir(parents=True,exist_ok=True); METADATA_FILE.write_text(json.dumps(c,indent=2),encoding="utf-8")
    return c


def slope_aspect_context(scene: dict, refresh: bool=False) -> dict:
    if refresh: return refresh_slope_aspect(scene)
    dem=full_dem_context(scene); c=_base(scene,dem)
    if METADATA_FILE.exists():
        try:
            cached=json.loads(METADATA_FILE.read_text(encoding="utf-8")); same=cached.get("source_dem_sha256")==dem.get("sha256")
            if cached.get("data_state")=="dem_derived_slope_aspect_cache" and same and SLOPE_FILE.exists() and ASPECT_FILE.exists():
                if hashlib.sha256(SLOPE_FILE.read_bytes()).hexdigest()==cached.get("slope_sha256") and hashlib.sha256(ASPECT_FILE.read_bytes()).hexdigest()==cached.get("aspect_sha256"):
                    cached["cache_status"]="loaded"; cached["pass_id"]="SV2-35"; return cached
        except (OSError,ValueError,TypeError): pass
    if dem.get("data_state")=="continuous_dem_cache":
        c.update({"data_state":"slope_aspect_ready_to_generate","cache_status":"missing","coverage_status":"source_dem_available","generated_at_utc":None,"display_label":"validated DEM ready · slope/aspect cache pending","failure_reason":None,"statistics":None})
    else:
        c.update({"data_state":"slope_aspect_unavailable_no_valid_dem","cache_status":"missing","coverage_status":"unresolved","generated_at_utc":None,"display_label":"slope and aspect unavailable · valid DEM required","failure_reason":None,"statistics":None})
    return c
