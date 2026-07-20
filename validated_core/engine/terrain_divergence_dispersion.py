from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image
import tifffile
from engine.full_dem import RASTER_FILE, full_dem_context
PASS_ID="SV2-39"
CACHE_DIR=Path(__file__).resolve().parents[1]/"data"/"cache"
DIVERGENCE_FILE=CACHE_DIR/"terrain_divergence_potential.png"
DISPERSION_FILE=CACHE_DIR/"terrain_dispersion_potential.png"
META_FILE=CACHE_DIR/"terrain_divergence_dispersion.json"
def _clamp(v,lo=0.0,hi=1.0): return max(lo,min(hi,float(v)))
def _band(v):
    return "high" if v>=.72 else "moderate-high" if v>=.48 else "moderate" if v>=.28 else "low-moderate" if v>=.12 else "low"
def _box_mean(a,r):
    p=np.pad(a,r,mode='edge'); cs=np.pad(p,((1,0),(1,0)),mode='constant').cumsum(0).cumsum(1); k=2*r+1
    return (cs[k:,k:]-cs[:-k,k:]-cs[k:,:-k]+cs[:-k,:-k])/(k*k)
def _unavailable(label,state='terrain_divergence_unavailable_safe'):
    return {"contract_version":"terrain_divergence_dispersion_v1","pass_id":PASS_ID,"layer":"terrain_induced_divergence_and_dispersion_potential","evidence_state":"inferred","data_state":state,"status":"unavailable_safe","display_label":label,"divergence_statistics":{},"dispersion_statistics":{},"confidence_support":0.0,"divergence_image_url":None,"dispersion_image_url":None,"particle_directives":{"divergence_spread_px":0.0,"dispersion_broadening":1.0,"dispersion_speed_multiplier":1.0,"dispersion_band":[0.56,0.96]},"atmospheric_basis":"terrain_and_current_context_only","scene_directive":"Hide divergence and dispersion effects until validated terrain and steering confidence are available.","claim_boundary":"Terrain-induced divergence and dispersion are DEM-derived visual potentials. They are not measured airflow divergence, concentration decay, dilution, CFD, travel time, exposure, or proof that emissions dispersed."}
def terrain_divergence_context(scene:dict,refresh:bool=False)->dict[str,Any]:
    dem=scene.get('full_dem') or full_dem_context(scene); conf=scene.get('terrain_steering_confidence') or {}; steering=scene.get('terrain_steering_field') or {}; conv=scene.get('terrain_convergence_accumulation') or {}
    if dem.get('data_state')!='continuous_dem_cache' or not RASTER_FILE.exists(): return _unavailable('terrain divergence unavailable · validated DEM missing')
    if conf.get('data_state')!='terrain_steering_confidence_cache': return _unavailable('terrain divergence unavailable · steering confidence missing')
    source_hash=dem.get('raster_sha256') or dem.get('sha256') or 'unknown'; conf_mean=_clamp((conf.get('confidence_statistics') or {}).get('mean',0)); steering_mean=_clamp((steering.get('field_statistics') or {}).get('mean_strength',0)); conv_mean=_clamp((conv.get('convergence_statistics') or {}).get('mean_potential',0))
    key=hashlib.sha256(f'{source_hash}|{conf_mean:.4f}|{steering_mean:.4f}|{conv_mean:.4f}|v1'.encode()).hexdigest()
    if not refresh and META_FILE.exists() and DIVERGENCE_FILE.exists() and DISPERSION_FILE.exists():
        try:
            c=json.loads(META_FILE.read_text());
            if c.get('cache_key')==key:return c
        except Exception: pass
    try:
        e=np.asarray(tifffile.imread(RASTER_FILE),dtype=float); e=e[0] if e.ndim>2 else e; valid=np.isfinite(e)
        if valid.mean()<.90:return _unavailable('terrain divergence unavailable · DEM coverage insufficient')
        z=np.where(valid,e,float(np.nanmedian(e[valid]))); ap=dem.get('approx_pixel_size_m') or {}; px=float(ap.get('x') if isinstance(ap,dict) else ap or 30); py=float(ap.get('y') if isinstance(ap,dict) else ap or 30)
        gy,gx=np.gradient(z,py,px); mag=np.hypot(gx,gy)+1e-9; ux=-gx/mag; uy=-gy/mag
        raw=np.maximum(np.gradient(ux,px,axis=1)+np.gradient(uy,py,axis=0),0); scale=max(1e-8,float(np.nanpercentile(raw[valid],96))); divergence=np.clip(raw/scale,0,1)
        slope=np.degrees(np.arctan(mag)); exposure=np.clip(slope/24,0,1); broad=_box_mean(z,10); high=np.clip((z-broad)/max(20,float(np.nanpercentile(np.maximum(z-broad,0),94))),0,1)
        divergence=np.clip(_box_mean(divergence,2)*(0.45+0.55*conf_mean)*(0.72+0.28*steering_mean),0,1)
        dispersion=np.clip((.52*divergence+.28*exposure+.20*high)*(0.44+.36*conf_mean+.20*(1-conv_mean)),0,1)
        divergence=np.nan_to_num(np.where(valid,divergence,0)); dispersion=np.nan_to_num(np.where(valid,dispersion,0))
        di=np.zeros((*divergence.shape,4),dtype=np.uint8); di[...,0]=246; di[...,1]=183; di[...,2]=91; di[...,3]=np.clip((divergence-.04)/.96*170,0,170).astype(np.uint8)
        sp=np.zeros((*dispersion.shape,4),dtype=np.uint8); sp[...,0]=118; sp[...,1]=184; sp[...,2]=255; sp[...,3]=np.clip((dispersion-.04)/.96*158,0,158).astype(np.uint8)
        CACHE_DIR.mkdir(parents=True,exist_ok=True); Image.fromarray(di,'RGBA').save(DIVERGENCE_FILE); Image.fromarray(sp,'RGBA').save(DISPERSION_FILE)
        dm=float(np.mean(divergence[valid])); sm=float(np.mean(dispersion[valid])); spread=_clamp(dm*conf_mean*12,0,8); broadening=_clamp(1+sm*conf_mean*.22,1,1.16); speed=_clamp(1+sm*conf_mean*.10,1,1.08)
        out={"contract_version":"terrain_divergence_dispersion_v1","pass_id":PASS_ID,"layer":"terrain_induced_divergence_and_dispersion_potential","evidence_state":"inferred","data_state":"terrain_divergence_dispersion_cache","status":"ready","cache_key":key,"source_dem_sha256":source_hash,"source_bbox":dem.get('bbox') or dem.get('requested_bbox'),"confidence_support":round(conf_mean,4),"atmospheric_basis":"terrain_and_current_context_only","divergence_statistics":{"mean_potential":round(dm,4),"potential_band":_band(dm),"elevated_cell_ratio":round(float(np.mean(divergence[valid]>=.45)),4)},"dispersion_statistics":{"mean_potential":round(sm,4),"potential_band":_band(sm),"elevated_cell_ratio":round(float(np.mean(dispersion[valid]>=.45)),4)},"divergence_image_url":"/terrain-divergence-image","divergence_image_sha256":hashlib.sha256(DIVERGENCE_FILE.read_bytes()).hexdigest(),"dispersion_image_url":"/terrain-dispersion-image","dispersion_image_sha256":hashlib.sha256(DISPERSION_FILE.read_bytes()).hexdigest(),"particle_directives":{"divergence_spread_px":round(spread,2),"dispersion_broadening":round(broadening,4),"dispersion_speed_multiplier":round(speed,4),"dispersion_band":[.56,.96]},"display_label":f'terrain divergence {_band(dm)} · dispersion {_band(sm)} · {round(conf_mean*100)}% support',"scene_directive":"Show restrained amber divergence illumination and a quiet blue dispersion veil. Apply only small confidence-gated visual spreading, broadening, and speed variation.","claim_boundary":"Terrain-induced divergence and dispersion are DEM-derived visual potentials. They are not measured airflow divergence, concentration decay, dilution, CFD, travel time, exposure, or proof that emissions dispersed."}
        META_FILE.write_text(json.dumps(out,indent=2)); return out
    except Exception as exc:
        o=_unavailable(f'terrain divergence generation failed · {type(exc).__name__}','terrain_divergence_generation_failed'); o['error_type']=type(exc).__name__; return o
