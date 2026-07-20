from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
import tifffile

from engine.full_dem import RASTER_FILE, full_dem_context

PASS_ID = "SV2-35"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"
FIELD_FILE = CACHE_DIR / "terrain_steering_field.png"
META_FILE = CACHE_DIR / "terrain_steering_field.json"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _angle_delta(a: np.ndarray, b: float) -> np.ndarray:
    return np.abs((a - b + 180.0) % 360.0 - 180.0)


def _band(value: float) -> str:
    if value >= 0.78: return "high"
    if value >= 0.58: return "moderate-high"
    if value >= 0.38: return "moderate"
    if value >= 0.18: return "low-moderate"
    return "low"


def _unavailable(label: str, state: str = "steering_field_unavailable_safe") -> dict[str, Any]:
    return {
        "contract_version": "terrain_steering_field_v1",
        "pass_id": PASS_ID,
        "layer": "terrain_steering_field",
        "evidence_state": "inferred",
        "data_state": state,
        "status": "unavailable_safe",
        "display_label": label,
        "source_dem_bbox": None,
        "wind_to_degrees": None,
        "wind_speed_mph": None,
        "field_statistics": {},
        "image_url": None,
        "image_sha256": None,
        "scene_directive": "Keep the steering field hidden until a validated DEM and usable wind context are available.",
        "claim_boundary": "The Terrain Steering Field is a DEM-derived visual heuristic showing where terrain may align, oppose, shelter, channel, or laterally deflect available wind context. It is not CFD, measured airflow, plume transport, methane concentration, or proof of actual atmospheric behavior.",
    }


def terrain_steering_field_context(scene: dict, refresh: bool = False) -> dict[str, Any]:
    dem = scene.get("full_dem") or full_dem_context(scene)
    wind = scene.get("wind") or {}
    if dem.get("data_state") != "continuous_dem_cache" or not RASTER_FILE.exists():
        return _unavailable("terrain steering field unavailable · validated DEM missing")
    if wind.get("data_state") not in {"live_current_conditions", "stale_cached_current_conditions", "default_vector_fallback"}:
        return _unavailable("terrain steering field unavailable · wind context missing")

    wind_to = float(wind.get("to_degrees") or 0.0) % 360.0
    wind_speed = float(wind.get("speed_mph") or 0.0)
    source_hash = dem.get("raster_sha256") or dem.get("sha256") or "unknown"
    cache_key = hashlib.sha256(f"{source_hash}|{wind_to:.2f}|{wind_speed:.2f}|v1".encode()).hexdigest()
    if not refresh and META_FILE.exists() and FIELD_FILE.exists():
        try:
            cached=json.loads(META_FILE.read_text(encoding="utf-8"))
            if cached.get("cache_key")==cache_key:
                return cached
        except Exception:
            pass

    try:
        elev=np.asarray(tifffile.imread(RASTER_FILE),dtype=np.float64)
        if elev.ndim>2: elev=elev[0]
        valid=np.isfinite(elev)
        if valid.mean()<0.90:
            return _unavailable("terrain steering field unavailable · DEM coverage insufficient")
        fill=float(np.nanmedian(elev[valid]))
        z=np.where(valid,elev,fill)
        # Pixel spacing metadata is approximate but consistent with the DEM acquisition contract.
        approx = dem.get("approx_pixel_size_m") or {}
        px=float(approx.get("x") if isinstance(approx, dict) else approx or 30.0)
        py=float(approx.get("y") if isinstance(approx, dict) else approx or 30.0)
        gy,gx=np.gradient(z,py,px)
        slope=np.degrees(np.arctan(np.hypot(gx,gy)))
        # Downslope aspect clockwise from north.
        aspect=(np.degrees(np.arctan2(-gx,gy))+360.0)%360.0
        delta=_angle_delta(aspect,wind_to)
        slope_signal=np.clip(slope/35.0,0,1)
        alignment=np.clip(1.0-delta/90.0,0,1)
        opposition=np.clip((delta-90.0)/90.0,0,1)
        cross=np.sin(np.radians(delta))
        cross=np.clip(np.abs(cross),0,1)
        # Local concavity proxy: positive values suggest relative shelter/channel form.
        broad=(np.roll(z,1,0)+np.roll(z,-1,0)+np.roll(z,1,1)+np.roll(z,-1,1))/4.0
        concavity=np.clip((broad-z)/35.0,0,1)
        exposure=np.clip((z-np.nanpercentile(z,35))/(max(1.0,np.nanpercentile(z,90)-np.nanpercentile(z,35))),0,1)
        speed_signal=_clamp(wind_speed/22.0)
        align_score=np.clip(slope_signal*alignment*(0.55+0.45*speed_signal),0,1)
        oppose_score=np.clip(slope_signal*opposition*(0.55+0.45*speed_signal),0,1)
        shelter_score=np.clip(concavity*(1.0-0.45*speed_signal)+slope_signal*opposition*0.25,0,1)
        channel_score=np.clip(concavity*alignment*0.75+slope_signal*alignment*0.25,0,1)
        deflect_score=np.clip(slope_signal*cross*(0.50+0.50*speed_signal),0,1)
        stack=np.stack([align_score,oppose_score,shelter_score,channel_score,deflect_score],axis=-1)
        category=np.argmax(stack,axis=-1)
        strength=np.max(stack,axis=-1)
        strength=np.where(valid,strength,0)
        # Transparent, restrained categorical field.
        palette=np.array([
            [82,238,220],   # align cyan
            [245,159,92],   # oppose amber
            [76,116,150],   # shelter slate
            [119,220,176],  # channel green
            [184,142,238],  # deflect violet
        ],dtype=np.uint8)
        rgb=palette[category]
        alpha=np.clip((strength-0.12)/0.88*150,0,150).astype(np.uint8)
        alpha=np.where(valid,alpha,0).astype(np.uint8)
        rgba=np.dstack([rgb,alpha])
        CACHE_DIR.mkdir(parents=True,exist_ok=True)
        Image.fromarray(rgba,"RGBA").save(FIELD_FILE)
        image_sha=hashlib.sha256(FIELD_FILE.read_bytes()).hexdigest()
        names=["alignment","opposition","shelter","channeling","lateral_deflection"]
        ratios={name:round(float(((category==i)&(strength>=0.18)&valid).sum()/valid.sum()),4) for i,name in enumerate(names)}
        means={name:round(float(np.nanmean(arr[valid])),4) for name,arr in zip(names,[align_score,oppose_score,shelter_score,channel_score,deflect_score])}
        dominant=max(ratios,key=ratios.get)
        overall=float(np.nanmean(strength[valid]))
        contract={
            "contract_version":"terrain_steering_field_v1","pass_id":PASS_ID,"layer":"terrain_steering_field",
            "evidence_state":"inferred","data_state":"terrain_steering_field_cache","status":"ready",
            "cache_key":cache_key,"source_dem_sha256":source_hash,"source_dem_bbox":dem.get("bbox") or dem.get("requested_bbox"),
            "wind_to_degrees":round(wind_to,1),"wind_speed_mph":round(wind_speed,1),"temporal_basis":"current_atmospheric_context_only",
            "field_statistics":{"mean_strength":round(overall,4),"strength_band":_band(overall),"dominant_response":dominant,"response_ratios":ratios,"component_means":means,"valid_cell_ratio":round(float(valid.mean()),4)},
            "image_url":"/terrain-steering-field-image","image_sha256":image_sha,
            "display_label":f"{_band(overall)} spatial steering · dominant {dominant.replace('_',' ')} · current context only",
            "scene_directive":"Show the field as a restrained spatial review layer beneath the atmospheric reconstruction. Treat categories as terrain-conditioned possibilities, not actual airflow measurements.",
            "claim_boundary":"The Terrain Steering Field is a DEM-derived visual heuristic showing where terrain may align, oppose, shelter, channel, or laterally deflect available wind context. It is not CFD, measured airflow, plume transport, methane concentration, or proof of actual atmospheric behavior.",
        }
        META_FILE.write_text(json.dumps(contract,indent=2),encoding="utf-8")
        return contract
    except Exception as exc:
        out=_unavailable(f"terrain steering field generation failed · {type(exc).__name__}","steering_field_generation_failed")
        out["error_type"]=type(exc).__name__
        return out
