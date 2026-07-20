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
CHANNEL_FILE = CACHE_DIR / "canyon_channeling_potential.png"
DRAINAGE_FILE = CACHE_DIR / "drainage_alignment_potential.png"
META_FILE = CACHE_DIR / "canyon_channeling_drainage_alignment.json"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _band(value: float) -> str:
    if value >= 0.72: return "high"
    if value >= 0.48: return "moderate-high"
    if value >= 0.28: return "moderate"
    if value >= 0.12: return "low-moderate"
    return "low"


def _box_mean(arr: np.ndarray, radius: int) -> np.ndarray:
    pad=np.pad(arr, radius, mode="edge")
    cs=np.pad(pad, ((1,0),(1,0)), mode="constant").cumsum(0).cumsum(1)
    k=2*radius+1
    return (cs[k:,k:]-cs[:-k,k:]-cs[k:,:-k]+cs[:-k,:-k])/(k*k)


def _unavailable(label: str, state: str="canyon_channeling_unavailable_safe") -> dict[str,Any]:
    return {
      "contract_version":"canyon_channeling_drainage_alignment_v1","pass_id":PASS_ID,
      "layer":"canyon_channeling_and_drainage_alignment","evidence_state":"inferred",
      "data_state":state,"status":"unavailable_safe","display_label":label,
      "channeling_statistics":{},"drainage_statistics":{},"confidence_support":0.0,
      "channel_image_url":None,"drainage_image_url":None,
      "particle_directives":{"channel_pull_px":0.0,"channel_speed_multiplier":1.0,"drainage_coherence":0.0,"channel_band":[0.18,0.78]},
      "scene_directive":"Hide canyon-channeling and drainage-alignment effects until validated terrain, wind, and steering confidence are available.",
      "claim_boundary":"Canyon channeling and drainage alignment are DEM-derived visual potentials. They are not measured airflow, verified drainage wind, CFD, plume routing, methane concentration, travel time, exposure, or proof of actual atmospheric behavior."
    }


def canyon_channeling_context(scene: dict, refresh: bool=False) -> dict[str,Any]:
    dem=scene.get("full_dem") or full_dem_context(scene)
    wind=scene.get("wind") or {}
    conf=scene.get("terrain_steering_confidence") or {}
    if dem.get("data_state")!="continuous_dem_cache" or not RASTER_FILE.exists(): return _unavailable("canyon channeling unavailable · validated DEM missing")
    if wind.get("data_state") not in {"live_current_conditions","stale_cached_current_conditions","default_vector_fallback"}: return _unavailable("canyon channeling unavailable · wind context missing")
    if conf.get("data_state")!="terrain_steering_confidence_cache": return _unavailable("canyon channeling unavailable · steering confidence missing")
    wind_to=float(wind.get("to_degrees") or 0)%360
    speed=max(0.0,float(wind.get("speed_mph") or 0))
    source_hash=dem.get("raster_sha256") or dem.get("sha256") or "unknown"
    conf_mean=_clamp((conf.get("confidence_statistics") or {}).get("mean",0.0))
    cache_key=hashlib.sha256(f"{source_hash}|{wind_to:.2f}|{speed:.2f}|{conf_mean:.4f}|v1".encode()).hexdigest()
    if not refresh and META_FILE.exists() and CHANNEL_FILE.exists() and DRAINAGE_FILE.exists():
      try:
        c=json.loads(META_FILE.read_text(encoding="utf-8"))
        if c.get("cache_key")==cache_key:return c
      except Exception: pass
    try:
      elev=np.asarray(tifffile.imread(RASTER_FILE),dtype=np.float64)
      if elev.ndim>2:elev=elev[0]
      valid=np.isfinite(elev)
      if valid.mean()<0.90:return _unavailable("canyon channeling unavailable · DEM coverage insufficient")
      z=np.where(valid,elev,float(np.nanmedian(elev[valid])))
      approx=dem.get("approx_pixel_size_m") or {}
      px=float(approx.get("x") if isinstance(approx,dict) else approx or 30.0)
      py=float(approx.get("y") if isinstance(approx,dict) else approx or 30.0)
      gy,gx=np.gradient(z,py,px)
      slope=np.degrees(np.arctan(np.hypot(gx,gy)))
      broad=_box_mean(z,7); local=_box_mean(z,2)
      tpi=broad-z
      concavity=np.clip(tpi/max(20.0,float(np.nanpercentile(np.abs(tpi),85))),0,1)
      local_relief=np.sqrt(np.maximum(0.0,_box_mean((z-broad)**2,5)))
      enclosure=np.clip(local_relief/max(25.0,float(np.nanpercentile(local_relief,85))),0,1)
      # downslope direction in map-bearing convention
      downslope=(np.degrees(np.arctan2(-gx,gy))+360)%360
      delta=np.abs(((downslope-wind_to+180)%360)-180)
      alignment=np.abs(np.cos(np.radians(delta)))
      slope_support=np.clip(slope/24.0,0,1)
      speed_support=_clamp(speed/14.0,0.08,1.0)
      gate=0.35+0.65*conf_mean
      drainage=np.clip(concavity*(0.48+0.52*slope_support)*alignment*gate,0,1)
      channel=np.clip((0.58*concavity+0.42*enclosure)*(0.35+0.65*alignment)*(0.40+0.60*speed_support)*gate,0,1)
      support=valid
      drainage=np.nan_to_num(np.where(support,drainage,0.0))
      channel=np.nan_to_num(np.where(support,channel,0.0))
      ch=np.zeros((*channel.shape,4),dtype=np.uint8); ch[...,0]=70; ch[...,1]=232; ch[...,2]=205; ch[...,3]=np.clip((channel-.05)/.95*180,0,180).astype(np.uint8)
      dr=np.zeros((*drainage.shape,4),dtype=np.uint8); dr[...,0]=74; dr[...,1]=154; dr[...,2]=255; dr[...,3]=np.clip((drainage-.05)/.95*165,0,165).astype(np.uint8)
      CACHE_DIR.mkdir(parents=True,exist_ok=True)
      Image.fromarray(ch,"RGBA").save(CHANNEL_FILE); Image.fromarray(dr,"RGBA").save(DRAINAGE_FILE)
      ch_mean=float(np.mean(channel[support])); dr_mean=float(np.mean(drainage[support]))
      pull=_clamp(ch_mean*conf_mean*24,0,9)
      accel=_clamp(1+ch_mean*conf_mean*.28,1,1.16)
      coherence=_clamp((dr_mean*.55+ch_mean*.45)*conf_mean,0,.85)
      out={
        "contract_version":"canyon_channeling_drainage_alignment_v1","pass_id":PASS_ID,"layer":"canyon_channeling_and_drainage_alignment","evidence_state":"inferred",
        "data_state":"canyon_channeling_drainage_cache","status":"ready","cache_key":cache_key,"source_dem_sha256":source_hash,"source_bbox":dem.get("bbox") or dem.get("requested_bbox"),
        "wind_to_degrees":round(wind_to,1),"wind_speed_mph":round(speed,1),"temporal_basis":"current_atmospheric_context_only","confidence_support":round(conf_mean,4),
        "channeling_statistics":{"mean_potential":round(ch_mean,4),"potential_band":_band(ch_mean),"elevated_cell_ratio":round(float(np.mean(channel[support]>=.45)),4)},
        "drainage_statistics":{"mean_alignment":round(dr_mean,4),"alignment_band":_band(dr_mean),"elevated_cell_ratio":round(float(np.mean(drainage[support]>=.45)),4)},
        "channel_image_url":"/canyon-channeling-image","channel_image_sha256":hashlib.sha256(CHANNEL_FILE.read_bytes()).hexdigest(),
        "drainage_image_url":"/drainage-alignment-image","drainage_image_sha256":hashlib.sha256(DRAINAGE_FILE.read_bytes()).hexdigest(),
        "particle_directives":{"channel_pull_px":round(pull,2),"channel_speed_multiplier":round(accel,4),"drainage_coherence":round(coherence,4),"channel_band":[0.18,0.78]},
        "display_label":f"canyon channeling {_band(ch_mean)} · drainage alignment {_band(dr_mean)} · {round(conf_mean*100)}% support",
        "scene_directive":"Show restrained cyan channel corridors and blue drainage alignment. Pull visual tracers modestly toward supported corridors and slightly increase coherence and speed only where confidence allows.",
        "claim_boundary":"Canyon channeling and drainage alignment are DEM-derived visual potentials. They are not measured airflow, verified drainage wind, CFD, plume routing, methane concentration, travel time, exposure, or proof of actual atmospheric behavior."
      }
      META_FILE.write_text(json.dumps(out,indent=2),encoding="utf-8")
      return out
    except Exception as exc:
      out=_unavailable(f"canyon channeling generation failed · {type(exc).__name__}","canyon_channeling_generation_failed"); out["error_type"]=type(exc).__name__; return out
