from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
import tifffile

from engine.full_dem import RASTER_FILE, full_dem_context

PASS_ID = "SV2-37"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"
BASIN_FILE = CACHE_DIR / "basin_retention_potential.png"
COLD_POOL_FILE = CACHE_DIR / "cold_air_pooling_potential.png"
META_FILE = CACHE_DIR / "basin_retention_cold_air_pooling.json"


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


def _box_min(arr: np.ndarray, radius: int) -> np.ndarray:
    from numpy.lib.stride_tricks import sliding_window_view
    p=np.pad(arr,radius,mode="edge")
    return sliding_window_view(p,(2*radius+1,2*radius+1)).min(axis=(-2,-1))


def _unavailable(label: str, state: str="basin_retention_unavailable_safe") -> dict[str,Any]:
    return {
      "contract_version":"basin_retention_cold_air_pooling_v1","pass_id":PASS_ID,
      "layer":"basin_retention_and_cold_air_pooling","evidence_state":"inferred",
      "data_state":state,"status":"unavailable_safe","display_label":label,
      "basin_statistics":{},"cold_pooling_statistics":{},"confidence_support":0.0,
      "basin_image_url":None,"cold_pooling_image_url":None,
      "particle_directives":{"retention_slowdown":1.0,"pooling_broadening":1.0,"settling_px":0.0,"retention_band":[0.50,0.88]},
      "atmospheric_basis":"terrain_only_until_observation_time_stability_is_available",
      "scene_directive":"Hide basin-retention and cold-air-pooling effects until validated terrain and steering confidence are available.",
      "claim_boundary":"Basin retention and cold-air pooling are DEM-derived visual potentials. They are not measured temperature inversions, verified pollutant trapping, observed cold-air drainage, CFD, methane concentration, exposure, or proof that emissions accumulated in a basin."
    }


def basin_retention_context(scene: dict, refresh: bool=False) -> dict[str,Any]:
    dem=scene.get("full_dem") or full_dem_context(scene)
    conf=scene.get("terrain_steering_confidence") or {}
    stability=scene.get("atmospheric_stability") or {}
    if dem.get("data_state")!="continuous_dem_cache" or not RASTER_FILE.exists(): return _unavailable("basin retention unavailable · validated DEM missing")
    if conf.get("data_state")!="terrain_steering_confidence_cache": return _unavailable("basin retention unavailable · steering confidence missing")
    source_hash=dem.get("raster_sha256") or dem.get("sha256") or "unknown"
    conf_mean=_clamp((conf.get("confidence_statistics") or {}).get("mean",0.0))
    stability_state=str(stability.get("classification") or stability.get("stability_class") or "unknown").lower()
    stability_support={"stable":1.0,"neutral":0.62,"unstable":0.22}.get(stability_state,0.42)
    cache_key=hashlib.sha256(f"{source_hash}|{conf_mean:.4f}|{stability_state}|v1".encode()).hexdigest()
    if not refresh and META_FILE.exists() and BASIN_FILE.exists() and COLD_POOL_FILE.exists():
      try:
        cached=json.loads(META_FILE.read_text(encoding="utf-8"))
        if cached.get("cache_key")==cache_key:return cached
      except Exception: pass
    try:
      elev=np.asarray(tifffile.imread(RASTER_FILE),dtype=np.float64)
      if elev.ndim>2:elev=elev[0]
      valid=np.isfinite(elev)
      if valid.mean()<0.90:return _unavailable("basin retention unavailable · DEM coverage insufficient")
      z=np.where(valid,elev,float(np.nanmedian(elev[valid])))
      approx=dem.get("approx_pixel_size_m") or {}
      px=float(approx.get("x") if isinstance(approx,dict) else approx or 30.0)
      py=float(approx.get("y") if isinstance(approx,dict) else approx or 30.0)
      gy,gx=np.gradient(z,py,px)
      slope=np.degrees(np.arctan(np.hypot(gx,gy)))
      broad=_box_mean(z,10)
      local=_box_mean(z,4)
      depression=np.clip((broad-z)/max(20.0,float(np.nanpercentile(np.maximum(broad-z,0),92))),0,1)
      enclosed=np.clip((_box_mean(np.maximum(z-_box_min(z,7),0),4))/max(15.0,float(np.nanpercentile(np.maximum(z-_box_min(z,7),0),90))),0,1)
      flatness=np.clip(1.0-slope/14.0,0,1)
      basin=np.clip((0.52*depression+0.28*enclosed+0.20*flatness)*(0.35+0.65*conf_mean),0,1)
      # Cold-air pooling receives only conditional atmospheric support; unresolved time never becomes a positive claim.
      pooling=np.clip(basin*(0.55+0.45*flatness)*(0.35+0.65*stability_support),0,1)
      basin=np.nan_to_num(np.where(valid,basin,0.0)); pooling=np.nan_to_num(np.where(valid,pooling,0.0))
      ba=np.zeros((*basin.shape,4),dtype=np.uint8); ba[...,0]=93; ba[...,1]=146; ba[...,2]=196; ba[...,3]=np.clip((basin-.05)/.95*170,0,170).astype(np.uint8)
      ca=np.zeros((*pooling.shape,4),dtype=np.uint8); ca[...,0]=164; ca[...,1]=216; ca[...,2]=255; ca[...,3]=np.clip((pooling-.05)/.95*178,0,178).astype(np.uint8)
      CACHE_DIR.mkdir(parents=True,exist_ok=True)
      Image.fromarray(ba,"RGBA").save(BASIN_FILE); Image.fromarray(ca,"RGBA").save(COLD_POOL_FILE)
      bm=float(np.mean(basin[valid])); pm=float(np.mean(pooling[valid]))
      slowdown=_clamp(1-bm*conf_mean*.24,.84,1.0)
      broadening=_clamp(1+pm*conf_mean*.24,1.0,1.16)
      settling=_clamp(pm*conf_mean*6.0,0,5.0)
      atmospheric_basis = "observation_time_stability_context" if stability_state in {"stable","neutral","unstable"} else "terrain_only_current_context_stability_unresolved"
      out={
        "contract_version":"basin_retention_cold_air_pooling_v1","pass_id":PASS_ID,"layer":"basin_retention_and_cold_air_pooling","evidence_state":"inferred",
        "data_state":"basin_retention_cold_air_pooling_cache","status":"ready","cache_key":cache_key,"source_dem_sha256":source_hash,"source_bbox":dem.get("bbox") or dem.get("requested_bbox"),
        "confidence_support":round(conf_mean,4),"atmospheric_basis":atmospheric_basis,"stability_state":stability_state,
        "basin_statistics":{"mean_potential":round(bm,4),"potential_band":_band(bm),"elevated_cell_ratio":round(float(np.mean(basin[valid]>=.45)),4)},
        "cold_pooling_statistics":{"mean_potential":round(pm,4),"potential_band":_band(pm),"elevated_cell_ratio":round(float(np.mean(pooling[valid]>=.45)),4)},
        "basin_image_url":"/basin-retention-image","basin_image_sha256":hashlib.sha256(BASIN_FILE.read_bytes()).hexdigest(),
        "cold_pooling_image_url":"/cold-air-pooling-image","cold_pooling_image_sha256":hashlib.sha256(COLD_POOL_FILE.read_bytes()).hexdigest(),
        "particle_directives":{"retention_slowdown":round(slowdown,4),"pooling_broadening":round(broadening,4),"settling_px":round(settling,2),"retention_band":[0.50,0.88]},
        "display_label":f"basin retention {_band(bm)} · cold-air pooling {_band(pm)} · {round(conf_mean*100)}% support",
        "scene_directive":"Show a restrained blue basin-retention veil and pale cold-air-pooling illumination. Apply only small confidence-gated visual slowdown, broadening, and settling.",
        "claim_boundary":"Basin retention and cold-air pooling are DEM-derived visual potentials. They are not measured temperature inversions, verified pollutant trapping, observed cold-air drainage, CFD, methane concentration, exposure, or proof that emissions accumulated in a basin."
      }
      META_FILE.write_text(json.dumps(out,indent=2),encoding="utf-8")
      return out
    except Exception as exc:
      out=_unavailable(f"basin retention generation failed · {type(exc).__name__}","basin_retention_generation_failed"); out["error_type"]=type(exc).__name__; return out
