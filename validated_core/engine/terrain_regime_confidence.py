from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image
import tifffile
from engine.full_dem import RASTER_FILE, full_dem_context

PASS_ID = "SV2-41"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"
CONFIDENCE_FILE = CACHE_DIR / "terrain_regime_confidence.png"
AMBIGUITY_FILE = CACHE_DIR / "terrain_boundary_ambiguity.png"
META_FILE = CACHE_DIR / "terrain_regime_confidence.json"

def _clamp(v, lo=0.0, hi=1.0): return max(lo, min(hi, float(v)))
def _band(v): return "very high" if v>=.82 else "high" if v>=.68 else "moderate" if v>=.46 else "low" if v>=.24 else "evidence-limited"
def _ambiguity_band(v): return "low" if v<.22 else "moderate" if v<.45 else "elevated" if v<.68 else "high"
def _box_mean(a, r):
    q=np.pad(a,r,mode="edge"); cs=np.pad(q,((1,0),(1,0)),mode="constant").cumsum(0).cumsum(1); k=2*r+1
    return (cs[k:,k:]-cs[:-k,k:]-cs[k:,:-k]+cs[:-k,:-k])/(k*k)
def _unavailable(label, state="terrain_regime_confidence_unavailable_safe"):
    return {"contract_version":"terrain_regime_confidence_v1","pass_id":PASS_ID,"layer":"terrain_regime_confidence_and_boundary_ambiguity","evidence_state":"inferred","data_state":state,"status":"unavailable_safe","display_label":label,"confidence_statistics":{},"ambiguity_statistics":{},"regime_support":{},"downgrade_reasons":["Validated transition-regime evidence is unavailable."],"confidence_image_url":None,"ambiguity_image_url":None,"visual_directives":{"confidence_glow":0.0,"ambiguity_veil":0.0,"boundary_fade":1.0},"scene_directive":"Hide regime-confidence and boundary-ambiguity effects until validated terrain transition evidence is available.","claim_boundary":"Terrain-regime confidence expresses support for a DEM-derived interpretive regime map. Boundary ambiguity marks weak separation among terrain-response classes. Neither layer is confidence in methane presence, plume location, atmospheric transport, concentration, exposure, or a measured atmospheric boundary."}

def terrain_regime_confidence_context(scene:dict, refresh:bool=False)->dict[str,Any]:
    dem=scene.get("full_dem") or full_dem_context(scene)
    transitions=scene.get("terrain_transition_regimes") or {}
    steering_conf=scene.get("terrain_steering_confidence") or {}
    if dem.get("data_state")!="continuous_dem_cache" or not RASTER_FILE.exists(): return _unavailable("regime confidence unavailable · validated DEM missing")
    if transitions.get("data_state")!="terrain_transition_regimes_cache": return _unavailable("regime confidence unavailable · transition regimes missing")
    if steering_conf.get("data_state")!="terrain_steering_confidence_cache": return _unavailable("regime confidence unavailable · steering confidence missing")
    source_hash=dem.get("raster_sha256") or dem.get("sha256") or "unknown"
    base_conf=_clamp((steering_conf.get("confidence_statistics") or {}).get("mean",0))
    transition_mean=_clamp((transitions.get("transition_statistics") or {}).get("mean_potential",0))
    boundary_mean=_clamp((transitions.get("boundary_statistics") or {}).get("mean_potential",0))
    key=hashlib.sha256(f"{source_hash}|{base_conf:.5f}|{transition_mean:.5f}|{boundary_mean:.5f}|v1".encode()).hexdigest()
    if not refresh and META_FILE.exists() and CONFIDENCE_FILE.exists() and AMBIGUITY_FILE.exists():
        try:
            c=json.loads(META_FILE.read_text())
            if c.get("cache_key")==key:return c
        except Exception: pass
    try:
        e=np.asarray(tifffile.imread(RASTER_FILE),dtype=float); e=e[0] if e.ndim>2 else e; valid=np.isfinite(e)
        if valid.mean()<.90:return _unavailable("regime confidence unavailable · DEM coverage insufficient")
        z=np.where(valid,e,float(np.nanmedian(e[valid])))
        ap=dem.get("approx_pixel_size_m") or {}; px=float(ap.get("x") if isinstance(ap,dict) else ap or 30); py=float(ap.get("y") if isinstance(ap,dict) else ap or 30)
        gy,gx=np.gradient(z,py,px); slope=np.degrees(np.arctan(np.hypot(gx,gy))); broad=_box_mean(z,10); local=z-broad
        relief_scale=max(20,float(np.nanpercentile(np.abs(local[valid]),94)))
        slope_n=np.clip(slope/28,0,1); low=np.clip((-local)/relief_scale+.32,0,1); high=np.clip(local/relief_scale+.32,0,1)
        confined=np.clip((1-slope_n)*low,0,1); exposed=np.clip(.58*slope_n+.42*high,0,1)
        separation=np.clip(np.abs(confined-exposed),0,1)
        rg=np.hypot(*np.gradient(confined-exposed)); rg_scale=max(1e-8,float(np.nanpercentile(rg[valid],96))); edge=np.clip(_box_mean(rg/rg_scale,1),0,1)
        local_consistency=np.clip(1-np.abs(separation-_box_mean(separation,3)),0,1)
        terrain_support=np.clip(.46*separation+.30*local_consistency+.24*(1-edge),0,1)
        confidence=np.clip(terrain_support*(.48+.52*base_conf),0,1)
        ambiguity=np.clip((1-separation)*(.55+.45*edge)*(1-.35*base_conf),0,1)
        confidence=np.nan_to_num(np.where(valid,_box_mean(confidence,2),0)); ambiguity=np.nan_to_num(np.where(valid,_box_mean(ambiguity,2),0))
        ci=np.zeros((*confidence.shape,4),dtype=np.uint8); ci[...,0]=115; ci[...,1]=220; ci[...,2]=228; ci[...,3]=np.clip((confidence-.08)/.92*150,0,150).astype(np.uint8)
        ai=np.zeros((*ambiguity.shape,4),dtype=np.uint8); ai[...,0]=224; ai[...,1]=152; ai[...,2]=238; ai[...,3]=np.clip((ambiguity-.08)/.92*160,0,160).astype(np.uint8)
        CACHE_DIR.mkdir(parents=True,exist_ok=True); Image.fromarray(ci,"RGBA").save(CONFIDENCE_FILE); Image.fromarray(ai,"RGBA").save(AMBIGUITY_FILE)
        cm=float(np.mean(confidence[valid])); am=float(np.mean(ambiguity[valid]))
        downgrade=[]
        if base_conf<.68:downgrade.append("Steering-field confidence is below high support.")
        if transition_mean>.45:downgrade.append("Broad transition coverage reduces regime separation.")
        if boundary_mean>.45:downgrade.append("Boundary density increases local ambiguity.")
        if not downgrade:downgrade.append("No major terrain-evidence downgrade triggered.")
        out={"contract_version":"terrain_regime_confidence_v1","pass_id":PASS_ID,"layer":"terrain_regime_confidence_and_boundary_ambiguity","evidence_state":"inferred","data_state":"terrain_regime_confidence_cache","status":"ready","cache_key":key,"source_dem_sha256":source_hash,"source_bbox":dem.get("bbox") or dem.get("requested_bbox"),"confidence_statistics":{"mean":round(cm,4),"band":_band(cm),"high_support_cell_ratio":round(float(np.mean(confidence[valid]>=.68)),4)},"ambiguity_statistics":{"mean":round(am,4),"band":_ambiguity_band(am),"elevated_ambiguity_cell_ratio":round(float(np.mean(ambiguity[valid]>=.52)),4)},"regime_support":{"steering_confidence_mean":round(base_conf,4),"transition_mean":round(transition_mean,4),"boundary_mean":round(boundary_mean,4),"terrain_signal_separation_mean":round(float(np.mean(separation[valid])),4)},"downgrade_reasons":downgrade,"confidence_image_url":"/terrain-regime-confidence-image","confidence_image_sha256":hashlib.sha256(CONFIDENCE_FILE.read_bytes()).hexdigest(),"ambiguity_image_url":"/terrain-boundary-ambiguity-image","ambiguity_image_sha256":hashlib.sha256(AMBIGUITY_FILE.read_bytes()).hexdigest(),"visual_directives":{"confidence_glow":round(_clamp(cm*.62,0,.55),4),"ambiguity_veil":round(_clamp(am*.58,0,.52),4),"boundary_fade":round(_clamp(1-am*.18,.84,1),4)},"display_label":f"regime confidence {_band(cm)} · boundary ambiguity {_ambiguity_band(am)} · {round(cm*100)}% support","scene_directive":"Show a restrained cool confidence illumination and a soft violet ambiguity veil. Fade regime boundaries where separation is weak; never sharpen them into hard fronts.","claim_boundary":"Terrain-regime confidence expresses support for a DEM-derived interpretive regime map. Boundary ambiguity marks weak separation among terrain-response classes. Neither layer is confidence in methane presence, plume location, atmospheric transport, concentration, exposure, or a measured atmospheric boundary."}
        META_FILE.write_text(json.dumps(out,indent=2)); return out
    except Exception as exc:
        o=_unavailable(f"regime confidence generation failed · {type(exc).__name__}","terrain_regime_confidence_generation_failed"); o["error_type"]=type(exc).__name__; return o
