from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
import tifffile

from engine.full_dem import RASTER_FILE, full_dem_context

PASS_ID = "SV2-36"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"
SADDLE_FILE = CACHE_DIR / "saddle_transfer_potential.png"
GAP_FILE = CACHE_DIR / "gap_acceleration_potential.png"
META_FILE = CACHE_DIR / "saddle_transfer_gap_acceleration.json"


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


def _box_max(arr: np.ndarray, radius: int) -> np.ndarray:
    from numpy.lib.stride_tricks import sliding_window_view
    p=np.pad(arr,radius,mode="edge")
    return sliding_window_view(p,(2*radius+1,2*radius+1)).max(axis=(-2,-1))


def _unavailable(label: str, state: str="saddle_gap_unavailable_safe") -> dict[str,Any]:
    return {
      "contract_version":"saddle_transfer_gap_acceleration_v1","pass_id":PASS_ID,
      "layer":"saddle_transfer_and_gap_acceleration","evidence_state":"inferred",
      "data_state":state,"status":"unavailable_safe","display_label":label,
      "saddle_statistics":{},"gap_statistics":{},"confidence_support":0.0,
      "saddle_image_url":None,"gap_image_url":None,
      "particle_directives":{"saddle_transfer_px":0.0,"gap_speed_multiplier":1.0,"gap_coherence":0.0,"saddle_band":[0.24,0.62],"gap_band":[0.34,0.76]},
      "scene_directive":"Hide saddle-transfer and gap-acceleration effects until validated terrain, wind, and steering confidence are available.",
      "claim_boundary":"Saddle transfer and gap acceleration are DEM-derived visual potentials. They are not measured airflow, verified Venturi acceleration, CFD, plume routing, methane concentration, travel time, exposure, or proof of actual atmospheric behavior."
    }


def saddle_gap_context(scene: dict, refresh: bool=False) -> dict[str,Any]:
    dem=scene.get("full_dem") or full_dem_context(scene)
    wind=scene.get("wind") or {}
    conf=scene.get("terrain_steering_confidence") or {}
    if dem.get("data_state")!="continuous_dem_cache" or not RASTER_FILE.exists(): return _unavailable("saddle transfer unavailable · validated DEM missing")
    if wind.get("data_state") not in {"live_current_conditions","stale_cached_current_conditions","default_vector_fallback"}: return _unavailable("saddle transfer unavailable · wind context missing")
    if conf.get("data_state")!="terrain_steering_confidence_cache": return _unavailable("saddle transfer unavailable · steering confidence missing")
    wind_to=float(wind.get("to_degrees") or 0)%360
    speed=max(0.0,float(wind.get("speed_mph") or 0))
    source_hash=dem.get("raster_sha256") or dem.get("sha256") or "unknown"
    conf_mean=_clamp((conf.get("confidence_statistics") or {}).get("mean",0.0))
    cache_key=hashlib.sha256(f"{source_hash}|{wind_to:.2f}|{speed:.2f}|{conf_mean:.4f}|v1".encode()).hexdigest()
    if not refresh and META_FILE.exists() and SADDLE_FILE.exists() and GAP_FILE.exists():
      try:
        cached=json.loads(META_FILE.read_text(encoding="utf-8"))
        if cached.get("cache_key")==cache_key:return cached
      except Exception: pass
    try:
      elev=np.asarray(tifffile.imread(RASTER_FILE),dtype=np.float64)
      if elev.ndim>2:elev=elev[0]
      valid=np.isfinite(elev)
      if valid.mean()<0.90:return _unavailable("saddle transfer unavailable · DEM coverage insufficient")
      z=np.where(valid,elev,float(np.nanmedian(elev[valid])))
      approx=dem.get("approx_pixel_size_m") or {}
      px=float(approx.get("x") if isinstance(approx,dict) else approx or 30.0)
      py=float(approx.get("y") if isinstance(approx,dict) else approx or 30.0)
      gy,gx=np.gradient(z,py,px)
      slope=np.degrees(np.arctan(np.hypot(gx,gy)))
      broad=_box_mean(z,8)
      ridge=np.clip((z-broad)/max(25.0,float(np.nanpercentile(np.abs(z-broad),90))),0,1)
      nearby_high=_box_max(z,5)
      notch=np.clip((nearby_high-z)/max(20.0,float(np.nanpercentile(nearby_high-z,90))),0,1)
      # A saddle is elevated relative to broad terrain but locally lower than adjacent crest terrain.
      saddle=np.clip(ridge*notch*np.clip(slope/18.0,0,1),0,1)
      aspect_to=(np.degrees(np.arctan2(-gx,gy))+360)%360
      delta=np.abs(((aspect_to-wind_to+180)%360)-180)
      wind_alignment=np.abs(np.cos(np.radians(delta)))
      constriction=np.clip((_box_mean(slope,3)-slope+12)/28.0,0,1)
      speed_support=_clamp(speed/14.0,0.08,1.0)
      gate=0.35+0.65*conf_mean
      gap=np.clip((0.58*saddle+0.42*constriction)*(0.35+0.65*wind_alignment)*(0.35+0.65*speed_support)*gate,0,1)
      saddle=np.nan_to_num(np.where(valid,saddle*gate,0.0)); gap=np.nan_to_num(np.where(valid,gap,0.0))
      sa=np.zeros((*saddle.shape,4),dtype=np.uint8); sa[...,0]=255; sa[...,1]=205; sa[...,2]=112; sa[...,3]=np.clip((saddle-.04)/.96*175,0,175).astype(np.uint8)
      ga=np.zeros((*gap.shape,4),dtype=np.uint8); ga[...,0]=126; ga[...,1]=244; ga[...,2]=255; ga[...,3]=np.clip((gap-.04)/.96*185,0,185).astype(np.uint8)
      CACHE_DIR.mkdir(parents=True,exist_ok=True)
      Image.fromarray(sa,"RGBA").save(SADDLE_FILE); Image.fromarray(ga,"RGBA").save(GAP_FILE)
      sm=float(np.mean(saddle[valid])); gm=float(np.mean(gap[valid]))
      transfer=_clamp(sm*conf_mean*18,0,6.5)
      accel=_clamp(1+gm*conf_mean*.34,1,1.18)
      coherence=_clamp((gm*.60+sm*.40)*conf_mean,0,.88)
      out={
        "contract_version":"saddle_transfer_gap_acceleration_v1","pass_id":PASS_ID,"layer":"saddle_transfer_and_gap_acceleration","evidence_state":"inferred",
        "data_state":"saddle_transfer_gap_cache","status":"ready","cache_key":cache_key,"source_dem_sha256":source_hash,"source_bbox":dem.get("bbox") or dem.get("requested_bbox"),
        "wind_to_degrees":round(wind_to,1),"wind_speed_mph":round(speed,1),"temporal_basis":"current_atmospheric_context_only","confidence_support":round(conf_mean,4),
        "saddle_statistics":{"mean_potential":round(sm,4),"potential_band":_band(sm),"elevated_cell_ratio":round(float(np.mean(saddle[valid]>=.45)),4)},
        "gap_statistics":{"mean_potential":round(gm,4),"potential_band":_band(gm),"elevated_cell_ratio":round(float(np.mean(gap[valid]>=.45)),4)},
        "saddle_image_url":"/saddle-transfer-image","saddle_image_sha256":hashlib.sha256(SADDLE_FILE.read_bytes()).hexdigest(),
        "gap_image_url":"/gap-acceleration-image","gap_image_sha256":hashlib.sha256(GAP_FILE.read_bytes()).hexdigest(),
        "particle_directives":{"saddle_transfer_px":round(transfer,2),"gap_speed_multiplier":round(accel,4),"gap_coherence":round(coherence,4),"saddle_band":[0.24,0.62],"gap_band":[0.34,0.76]},
        "display_label":f"saddle transfer {_band(sm)} · gap acceleration {_band(gm)} · {round(conf_mean*100)}% support",
        "scene_directive":"Show restrained amber saddle openings and cool gap corridors. Apply only a small confidence-gated transfer lift and speed concentration to visual tracers.",
        "claim_boundary":"Saddle transfer and gap acceleration are DEM-derived visual potentials. They are not measured airflow, verified Venturi acceleration, CFD, plume routing, methane concentration, travel time, exposure, or proof of actual atmospheric behavior."
      }
      META_FILE.write_text(json.dumps(out,indent=2),encoding="utf-8")
      return out
    except Exception as exc:
      out=_unavailable(f"saddle transfer generation failed · {type(exc).__name__}","saddle_gap_generation_failed"); out["error_type"]=type(exc).__name__; return out
