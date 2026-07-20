from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
import tifffile

from engine.full_dem import RASTER_FILE, full_dem_context

PASS_ID = "SV2-38"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"
CONVERGENCE_FILE = CACHE_DIR / "terrain_convergence_potential.png"
ACCUMULATION_FILE = CACHE_DIR / "terrain_focused_accumulation_potential.png"
META_FILE = CACHE_DIR / "terrain_convergence_accumulation.json"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _band(value: float) -> str:
    if value >= 0.72: return "high"
    if value >= 0.48: return "moderate-high"
    if value >= 0.28: return "moderate"
    if value >= 0.12: return "low-moderate"
    return "low"


def _box_mean(arr: np.ndarray, radius: int) -> np.ndarray:
    pad=np.pad(arr,radius,mode="edge")
    cs=np.pad(pad,((1,0),(1,0)),mode="constant").cumsum(0).cumsum(1)
    k=2*radius+1
    return (cs[k:,k:]-cs[:-k,k:]-cs[k:,:-k]+cs[:-k,:-k])/(k*k)


def _unavailable(label: str, state: str="terrain_convergence_unavailable_safe") -> dict[str,Any]:
    return {
      "contract_version":"terrain_convergence_accumulation_v1","pass_id":PASS_ID,
      "layer":"terrain_convergence_and_focused_accumulation","evidence_state":"inferred",
      "data_state":state,"status":"unavailable_safe","display_label":label,
      "convergence_statistics":{},"accumulation_statistics":{},"confidence_support":0.0,
      "convergence_image_url":None,"accumulation_image_url":None,
      "particle_directives":{"convergence_pull_px":0.0,"focus_slowdown":1.0,"focus_broadening":1.0,"focus_band":[0.48,0.90]},
      "atmospheric_basis":"terrain_and_current_context_only",
      "scene_directive":"Hide convergence and focused-accumulation effects until validated terrain and steering confidence are available.",
      "claim_boundary":"Terrain convergence and focused accumulation are DEM-derived visual potentials. They are not measured airflow convergence, methane concentration, pollutant trapping, exposure, CFD, or proof that emissions accumulated at a location."
    }


def terrain_convergence_context(scene: dict, refresh: bool=False) -> dict[str,Any]:
    dem=scene.get("full_dem") or full_dem_context(scene)
    conf=scene.get("terrain_steering_confidence") or {}
    basin=scene.get("basin_retention_cold_air_pooling") or {}
    steering=scene.get("terrain_steering_field") or {}
    if dem.get("data_state")!="continuous_dem_cache" or not RASTER_FILE.exists(): return _unavailable("terrain convergence unavailable · validated DEM missing")
    if conf.get("data_state")!="terrain_steering_confidence_cache": return _unavailable("terrain convergence unavailable · steering confidence missing")
    source_hash=dem.get("raster_sha256") or dem.get("sha256") or "unknown"
    conf_mean=_clamp((conf.get("confidence_statistics") or {}).get("mean",0.0))
    steering_mean=_clamp((steering.get("field_statistics") or {}).get("mean_strength",0.0))
    basin_mean=_clamp((basin.get("basin_statistics") or {}).get("mean_potential",0.0))
    cache_key=hashlib.sha256(f"{source_hash}|{conf_mean:.4f}|{steering_mean:.4f}|{basin_mean:.4f}|v1".encode()).hexdigest()
    if not refresh and META_FILE.exists() and CONVERGENCE_FILE.exists() and ACCUMULATION_FILE.exists():
      try:
        cached=json.loads(META_FILE.read_text(encoding="utf-8"))
        if cached.get("cache_key")==cache_key:return cached
      except Exception: pass
    try:
      elev=np.asarray(tifffile.imread(RASTER_FILE),dtype=np.float64)
      if elev.ndim>2:elev=elev[0]
      valid=np.isfinite(elev)
      if valid.mean()<0.90:return _unavailable("terrain convergence unavailable · DEM coverage insufficient")
      z=np.where(valid,elev,float(np.nanmedian(elev[valid])))
      approx=dem.get("approx_pixel_size_m") or {}
      px=float(approx.get("x") if isinstance(approx,dict) else approx or 30.0)
      py=float(approx.get("y") if isinstance(approx,dict) else approx or 30.0)
      gy,gx=np.gradient(z,py,px)
      mag=np.hypot(gx,gy)+1e-9
      ux=-gx/mag; uy=-gy/mag
      dux_dx=np.gradient(ux,px,axis=1); duy_dy=np.gradient(uy,py,axis=0)
      convergence_raw=np.maximum(-(dux_dx+duy_dy),0)
      scale=max(1e-8,float(np.nanpercentile(convergence_raw[valid],96)))
      convergence=np.clip(convergence_raw/scale,0,1)
      broad=_box_mean(z,10)
      low_position=np.clip((broad-z)/max(20.0,float(np.nanpercentile(np.maximum(broad-z,0),94))),0,1)
      flatness=np.clip(1-np.degrees(np.arctan(mag))/18.0,0,1)
      convergence=np.clip(_box_mean(convergence,2)*(0.45+0.55*conf_mean)*(0.70+0.30*steering_mean),0,1)
      # Accumulation is intentionally conditional: convergence + lower terrain + basin support.
      accumulation=np.clip((0.48*convergence+0.30*low_position+0.22*flatness)*(0.45+0.35*conf_mean+0.20*basin_mean),0,1)
      convergence=np.nan_to_num(np.where(valid,convergence,0.0)); accumulation=np.nan_to_num(np.where(valid,accumulation,0.0))
      co=np.zeros((*convergence.shape,4),dtype=np.uint8); co[...,0]=88; co[...,1]=225; co[...,2]=204; co[...,3]=np.clip((convergence-.04)/.96*176,0,176).astype(np.uint8)
      ac=np.zeros((*accumulation.shape,4),dtype=np.uint8); ac[...,0]=171; ac[...,1]=126; ac[...,2]=242; ac[...,3]=np.clip((accumulation-.04)/.96*166,0,166).astype(np.uint8)
      CACHE_DIR.mkdir(parents=True,exist_ok=True)
      Image.fromarray(co,"RGBA").save(CONVERGENCE_FILE); Image.fromarray(ac,"RGBA").save(ACCUMULATION_FILE)
      cm=float(np.mean(convergence[valid])); am=float(np.mean(accumulation[valid]))
      pull=_clamp(cm*conf_mean*11.0,0,7.5)
      slowdown=_clamp(1-am*conf_mean*.20,.86,1.0)
      broadening=_clamp(1+am*conf_mean*.20,1.0,1.14)
      out={
        "contract_version":"terrain_convergence_accumulation_v1","pass_id":PASS_ID,"layer":"terrain_convergence_and_focused_accumulation","evidence_state":"inferred",
        "data_state":"terrain_convergence_accumulation_cache","status":"ready","cache_key":cache_key,"source_dem_sha256":source_hash,"source_bbox":dem.get("bbox") or dem.get("requested_bbox"),
        "confidence_support":round(conf_mean,4),"atmospheric_basis":"terrain_and_current_context_only",
        "convergence_statistics":{"mean_potential":round(cm,4),"potential_band":_band(cm),"elevated_cell_ratio":round(float(np.mean(convergence[valid]>=.45)),4)},
        "accumulation_statistics":{"mean_potential":round(am,4),"potential_band":_band(am),"elevated_cell_ratio":round(float(np.mean(accumulation[valid]>=.45)),4)},
        "convergence_image_url":"/terrain-convergence-image","convergence_image_sha256":hashlib.sha256(CONVERGENCE_FILE.read_bytes()).hexdigest(),
        "accumulation_image_url":"/terrain-focused-accumulation-image","accumulation_image_sha256":hashlib.sha256(ACCUMULATION_FILE.read_bytes()).hexdigest(),
        "particle_directives":{"convergence_pull_px":round(pull,2),"focus_slowdown":round(slowdown,4),"focus_broadening":round(broadening,4),"focus_band":[0.48,0.90]},
        "display_label":f"terrain convergence {_band(cm)} · focused accumulation {_band(am)} · {round(conf_mean*100)}% support",
        "scene_directive":"Show restrained teal convergence illumination and a quiet violet focused-accumulation veil. Apply only small confidence-gated visual focusing, slowdown, and broadening.",
        "claim_boundary":"Terrain convergence and focused accumulation are DEM-derived visual potentials. They are not measured airflow convergence, methane concentration, pollutant trapping, exposure, CFD, or proof that emissions accumulated at a location."
      }
      META_FILE.write_text(json.dumps(out,indent=2),encoding="utf-8")
      return out
    except Exception as exc:
      out=_unavailable(f"terrain convergence generation failed · {type(exc).__name__}","terrain_convergence_generation_failed"); out["error_type"]=type(exc).__name__; return out
