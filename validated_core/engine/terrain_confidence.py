from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import tifffile
from PIL import Image

from engine.full_dem import RASTER_FILE, full_dem_context
from engine.hillshade import HILLSHADE_FILE, hillshade_context
from engine.slope_aspect import SLOPE_FILE, ASPECT_FILE, slope_aspect_context
from engine.landform_classification import LANDFORM_FILE, CONFIDENCE_FILE, landform_context

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "terrain_derivatives_cache"
CONFIDENCE_RASTER_FILE = CACHE_DIR / "default_scene_terrain_confidence.png"
METADATA_FILE = CACHE_DIR / "default_scene_terrain_confidence.json"


def _relative(path: Path) -> str:
    return str(path.relative_to(path.parents[2])).replace("\\", "/")


def _sha(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _base(scene: dict, dem: dict) -> dict:
    return {
        "contract_version": "1.0",
        "pass_id": "SV2-35",
        "layer": "terrain_confidence",
        "source_dem_sha256": dem.get("sha256"),
        "source_dem_provider": dem.get("provider"),
        "source_dem_bbox": dem.get("bbox"),
        "source_dem_grid": dem.get("requested_grid"),
        "source_resolution_m": dem.get("approx_pixel_size_m"),
        "confidence_output_path": _relative(CONFIDENCE_RASTER_FILE),
        "metadata_path": _relative(METADATA_FILE),
        "evidence_state": "measured",
        "confidence_dimensions": [
            "dem_coverage", "dem_valid_cells", "source_resolution", "cache_integrity",
            "hillshade_completeness", "slope_aspect_completeness", "landform_completeness",
            "landform_classification_confidence",
        ],
        "visual_role": "show how much trust the measured terrain stack earns without increasing scientific certainty",
        "claim_boundary": "Terrain confidence scores the completeness and integrity of the terrain evidence stack. It does not validate methane observations, atmospheric transport, event reconstruction, geology, or source responsibility.",
    }


def _grade(score: float) -> str:
    if score >= 0.90: return "high"
    if score >= 0.75: return "strong"
    if score >= 0.55: return "moderate"
    if score >= 0.35: return "limited"
    return "unresolved"


def _read_validity() -> tuple[np.ndarray, float, float]:
    a=np.squeeze(np.asarray(tifffile.imread(RASTER_FILE))).astype(np.float64,copy=False)
    if a.ndim != 2: raise ValueError(f"DEM raster must be 2D, got {a.shape}")
    finite=np.isfinite(a) & (np.abs(a)<1e20)
    valid_ratio=float(finite.mean())
    nodata_ratio=1.0-valid_ratio
    return finite,valid_ratio,nodata_ratio


def refresh_terrain_confidence(scene: dict) -> dict:
    dem=full_dem_context(scene)
    hill=hillshade_context(scene)
    deriv=slope_aspect_context(scene)
    land=landform_context(scene)
    c=_base(scene,dem)
    now=datetime.now(timezone.utc).isoformat()
    if dem.get("data_state") != "continuous_dem_cache" or not RASTER_FILE.exists():
        c.update({
            "data_state":"terrain_confidence_unavailable_no_valid_dem",
            "cache_status":"not_generated","coverage_status":"unresolved",
            "generated_at_utc":None,"overall_score":0.0,"quality_grade":"unresolved",
            "display_label":"terrain confidence unavailable · valid DEM required",
            "failure_reason":"No validated continuous DEM cache is available.",
            "dimensions":{},"statistics":None,
        })
    else:
        try:
            finite,valid_ratio,nodata_ratio=_read_validity()
            coverage=float(dem.get("coverage_ratio",0.0) or 0.0)
            px=dem.get("approx_pixel_size_m",{}) or {}
            resolution=max(float(px.get("x",9999)),float(px.get("y",9999)))
            resolution_score=float(np.clip(1.0-(resolution-10.0)/250.0,0.35,1.0))
            integrity_checks={
                "dem": _sha(RASTER_FILE)==dem.get("sha256"),
                "hillshade": hill.get("data_state")=="dem_derived_hillshade_cache" and HILLSHADE_FILE.exists(),
                "slope": deriv.get("data_state")=="dem_derived_slope_aspect_cache" and SLOPE_FILE.exists(),
                "aspect": deriv.get("data_state")=="dem_derived_slope_aspect_cache" and ASPECT_FILE.exists(),
                "landforms": land.get("data_state")=="dem_derived_landform_cache" and LANDFORM_FILE.exists(),
                "landform_confidence": land.get("data_state")=="dem_derived_landform_cache" and CONFIDENCE_FILE.exists(),
            }
            cache_integrity=sum(integrity_checks.values())/len(integrity_checks)
            hill_score=1.0 if integrity_checks["hillshade"] else 0.0
            deriv_score=(float(integrity_checks["slope"])+float(integrity_checks["aspect"]))/2
            land_score=(float(integrity_checks["landforms"])+float(integrity_checks["landform_confidence"]))/2
            land_mean=float((land.get("statistics") or {}).get("mean_confidence",0.0) or 0.0)
            dimensions={
                "dem_coverage":{"score":round(coverage,4),"state":_grade(coverage)},
                "dem_valid_cells":{"score":round(valid_ratio,4),"state":_grade(valid_ratio),"nodata_ratio":round(nodata_ratio,6)},
                "source_resolution":{"score":round(resolution_score,4),"state":_grade(resolution_score),"approx_max_pixel_m":round(resolution,2)},
                "cache_integrity":{"score":round(cache_integrity,4),"state":_grade(cache_integrity),"checks":integrity_checks},
                "hillshade_completeness":{"score":hill_score,"state":_grade(hill_score)},
                "slope_aspect_completeness":{"score":round(deriv_score,4),"state":_grade(deriv_score)},
                "landform_completeness":{"score":round(land_score,4),"state":_grade(land_score)},
                "landform_classification_confidence":{"score":round(land_mean,4),"state":_grade(land_mean)},
            }
            weights={"dem_coverage":0.18,"dem_valid_cells":0.18,"source_resolution":0.10,"cache_integrity":0.16,
                     "hillshade_completeness":0.08,"slope_aspect_completeness":0.10,"landform_completeness":0.10,
                     "landform_classification_confidence":0.10}
            overall=sum(dimensions[k]["score"]*w for k,w in weights.items())
            # Spatial confidence: valid DEM cells modulated by landform confidence where present.
            spatial=np.where(finite,0.72,0.0).astype(np.float64)
            if CONFIDENCE_FILE.exists() and integrity_checks["landform_confidence"]:
                lc=np.asarray(Image.open(CONFIDENCE_FILE).convert("L"),dtype=np.float64)/255.0
                if lc.shape==spatial.shape: spatial=np.where(finite,0.60+0.40*lc,0.0)
            img=np.clip(spatial*255,0,255).astype(np.uint8)
            CACHE_DIR.mkdir(parents=True,exist_ok=True)
            Image.fromarray(img,"L").save(CONFIDENCE_RASTER_FILE,"PNG",optimize=True)
            b=CONFIDENCE_RASTER_FILE.read_bytes()
            c.update({
                "data_state":"terrain_confidence_ready","cache_status":"refreshed",
                "coverage_status":"source_dem_bbox_scored","generated_at_utc":now,
                "overall_score":round(float(overall),4),"quality_grade":_grade(overall),
                "display_label":f"terrain evidence quality {_grade(overall)} · {overall*100:.0f}% composite",
                "failure_reason":None,"dimensions":dimensions,
                "output_grid":{"width":int(img.shape[1]),"height":int(img.shape[0])},
                "confidence_sha256":hashlib.sha256(b).hexdigest(),"confidence_byte_size":len(b),
                "confidence_image_url":"/terrain-confidence-image",
                "statistics":{"valid_cell_ratio":round(valid_ratio,6),"nodata_ratio":round(nodata_ratio,6),
                              "mean_spatial_confidence":round(float(spatial.mean()),4),
                              "p10_spatial_confidence":round(float(np.percentile(spatial,10)),4),
                              "p90_spatial_confidence":round(float(np.percentile(spatial,90)),4)},
            })
        except Exception as exc:
            c.update({"data_state":"terrain_confidence_generation_failed","cache_status":"refresh_failed",
                      "coverage_status":"unresolved","generated_at_utc":None,"overall_score":0.0,
                      "quality_grade":"unresolved","display_label":"terrain confidence generation failed",
                      "failure_reason":str(exc)[:300],"dimensions":{},"statistics":None})
    CACHE_DIR.mkdir(parents=True,exist_ok=True)
    METADATA_FILE.write_text(json.dumps(c,indent=2),encoding="utf-8")
    return c


def terrain_confidence_context(scene: dict, refresh: bool=False) -> dict:
    if refresh: return refresh_terrain_confidence(scene)
    dem=full_dem_context(scene); c=_base(scene,dem)
    if METADATA_FILE.exists():
        try:
            cached=json.loads(METADATA_FILE.read_text(encoding="utf-8"))
            same=cached.get("source_dem_sha256")==dem.get("sha256")
            if cached.get("data_state")=="terrain_confidence_ready" and same and CONFIDENCE_RASTER_FILE.exists():
                if _sha(CONFIDENCE_RASTER_FILE)==cached.get("confidence_sha256"):
                    cached["cache_status"]="loaded"; cached["pass_id"]="SV2-35"; return cached
        except (OSError,ValueError,TypeError): pass
    if dem.get("data_state")=="continuous_dem_cache":
        c.update({"data_state":"terrain_confidence_ready_to_generate","cache_status":"missing",
                  "coverage_status":"source_dem_available","generated_at_utc":None,"overall_score":0.0,
                  "quality_grade":"unresolved","display_label":"validated terrain stack ready · confidence cache pending",
                  "failure_reason":None,"dimensions":{},"statistics":None})
    else:
        c.update({"data_state":"terrain_confidence_unavailable_no_valid_dem","cache_status":"missing",
                  "coverage_status":"unresolved","generated_at_utc":None,"overall_score":0.0,
                  "quality_grade":"unresolved","display_label":"terrain confidence unavailable · valid DEM required",
                  "failure_reason":None,"dimensions":{},"statistics":None})
    return c
