from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image
import tifffile
from engine.full_dem import RASTER_FILE, full_dem_context
PASS_ID="SV2-40"
CACHE_DIR=Path(__file__).resolve().parents[1]/"data"/"cache"
TRANSITION_FILE=CACHE_DIR/"terrain_transition_zones.png"
BOUNDARY_FILE=CACHE_DIR/"flow_regime_boundaries.png"
META_FILE=CACHE_DIR/"terrain_transition_regimes.json"
def _clamp(v,lo=0.0,hi=1.0): return max(lo,min(hi,float(v)))
def _band(v): return "high" if v>=.72 else "moderate-high" if v>=.48 else "moderate" if v>=.28 else "low-moderate" if v>=.12 else "low"
def _box_mean(a,r):
    p=np.pad(a,r,mode='edge'); cs=np.pad(p,((1,0),(1,0)),mode='constant').cumsum(0).cumsum(1); k=2*r+1
    return (cs[k:,k:]-cs[:-k,k:]-cs[k:,:-k]+cs[:-k,:-k])/(k*k)
def _unavailable(label,state='terrain_transition_unavailable_safe'):
    return {"contract_version":"terrain_transition_regimes_v1","pass_id":PASS_ID,"layer":"terrain_transition_zones_and_flow_regime_boundaries","evidence_state":"inferred","data_state":state,"status":"unavailable_safe","display_label":label,"transition_statistics":{},"boundary_statistics":{},"regime_mix":{},"confidence_support":0.0,"transition_image_url":None,"boundary_image_url":None,"particle_directives":{"transition_jitter_px":0.0,"boundary_softening":1.0,"regime_blend":0.0,"transition_band":[0.38,0.78]},"atmospheric_basis":"terrain_and_current_context_only","scene_directive":"Hide transition-zone and regime-boundary effects until validated terrain-response layers are available.","claim_boundary":"Terrain transition zones and flow-regime boundaries are DEM-derived interpretive boundaries. They are not measured atmospheric fronts, CFD regime changes, plume edges, concentration gradients, travel-time boundaries, or proof of actual airflow behavior."}
def terrain_transition_context(scene:dict,refresh:bool=False)->dict[str,Any]:
    dem=scene.get('full_dem') or full_dem_context(scene); conf=scene.get('terrain_steering_confidence') or {}; conv=scene.get('terrain_convergence_accumulation') or {}; div=scene.get('terrain_divergence_dispersion') or {}; canyon=scene.get('canyon_channeling') or {}; ridge=scene.get('ridge_spillover_shelter') or {}; basin=scene.get('basin_retention_cold_air_pooling') or {}
    if dem.get('data_state')!='continuous_dem_cache' or not RASTER_FILE.exists(): return _unavailable('terrain transitions unavailable · validated DEM missing')
    if conf.get('data_state')!='terrain_steering_confidence_cache': return _unavailable('terrain transitions unavailable · steering confidence missing')
    source_hash=dem.get('raster_sha256') or dem.get('sha256') or 'unknown'; conf_mean=_clamp((conf.get('confidence_statistics') or {}).get('mean',0));
    support=[_clamp((conv.get('convergence_statistics') or {}).get('mean_potential',0)),_clamp((div.get('divergence_statistics') or {}).get('mean_potential',0)),_clamp((canyon.get('channel_statistics') or {}).get('mean_potential',0)),_clamp((ridge.get('shelter_statistics') or {}).get('mean_potential',0)),_clamp((basin.get('basin_statistics') or {}).get('mean_potential',0))]
    key=hashlib.sha256((source_hash+'|'+'|'.join(f'{x:.4f}' for x in [conf_mean,*support])+'|v1').encode()).hexdigest()
    if not refresh and META_FILE.exists() and TRANSITION_FILE.exists() and BOUNDARY_FILE.exists():
        try:
            c=json.loads(META_FILE.read_text())
            if c.get('cache_key')==key:return c
        except Exception: pass
    try:
        e=np.asarray(tifffile.imread(RASTER_FILE),dtype=float); e=e[0] if e.ndim>2 else e; valid=np.isfinite(e)
        if valid.mean()<.90:return _unavailable('terrain transitions unavailable · DEM coverage insufficient')
        z=np.where(valid,e,float(np.nanmedian(e[valid]))); ap=dem.get('approx_pixel_size_m') or {}; px=float(ap.get('x') if isinstance(ap,dict) else ap or 30); py=float(ap.get('y') if isinstance(ap,dict) else ap or 30)
        gy,gx=np.gradient(z,py,px); slope=np.degrees(np.arctan(np.hypot(gx,gy))); broad=_box_mean(z,10); local=z-broad
        relief_scale=max(20,float(np.nanpercentile(np.abs(local[valid]),94))); relief=np.clip(np.abs(local)/relief_scale,0,1)
        slope_n=np.clip(slope/28,0,1)
        # response proxies: confinement vs exposure and convergence vs divergence
        confinement=np.clip((1-slope_n)*np.clip((-local)/relief_scale+.35,0,1),0,1)
        exposure=np.clip(.58*slope_n+.42*np.clip(local/relief_scale,0,1),0,1)
        response_balance=np.abs(confinement-exposure)
        transition=np.clip((1-response_balance)*(.42+.58*relief)*(0.45+0.55*conf_mean),0,1)
        # boundaries emphasize rapid spatial changes in regime membership
        rg=np.hypot(*np.gradient(confinement-exposure)); scale=max(1e-8,float(np.nanpercentile(rg[valid],96))); boundary=np.clip(_box_mean(rg/scale,1)*(0.50+0.50*conf_mean),0,1)
        transition=np.nan_to_num(np.where(valid,_box_mean(transition,2),0)); boundary=np.nan_to_num(np.where(valid,boundary,0))
        ti=np.zeros((*transition.shape,4),dtype=np.uint8); ti[...,0]=235; ti[...,1]=221; ti[...,2]=142; ti[...,3]=np.clip((transition-.05)/.95*160,0,160).astype(np.uint8)
        bi=np.zeros((*boundary.shape,4),dtype=np.uint8); bi[...,0]=255; bi[...,1]=255; bi[...,2]=255; bi[...,3]=np.clip((boundary-.08)/.92*190,0,190).astype(np.uint8)
        CACHE_DIR.mkdir(parents=True,exist_ok=True); Image.fromarray(ti,'RGBA').save(TRANSITION_FILE); Image.fromarray(bi,'RGBA').save(BOUNDARY_FILE)
        tm=float(np.mean(transition[valid])); bm=float(np.mean(boundary[valid])); jitter=_clamp(tm*conf_mean*7,0,5.5); soften=_clamp(1+bm*conf_mean*.12,1,1.10); blend=_clamp((tm+bm)*.5*conf_mean,0,.72)
        mix={"confined_ratio":round(float(np.mean(confinement[valid]>=.52)),4),"exposed_ratio":round(float(np.mean(exposure[valid]>=.52)),4),"mixed_transition_ratio":round(float(np.mean(transition[valid]>=.42)),4)}
        out={"contract_version":"terrain_transition_regimes_v1","pass_id":PASS_ID,"layer":"terrain_transition_zones_and_flow_regime_boundaries","evidence_state":"inferred","data_state":"terrain_transition_regimes_cache","status":"ready","cache_key":key,"source_dem_sha256":source_hash,"source_bbox":dem.get('bbox') or dem.get('requested_bbox'),"confidence_support":round(conf_mean,4),"atmospheric_basis":"terrain_and_current_context_only","transition_statistics":{"mean_potential":round(tm,4),"potential_band":_band(tm),"elevated_cell_ratio":round(float(np.mean(transition[valid]>=.45)),4)},"boundary_statistics":{"mean_potential":round(bm,4),"potential_band":_band(bm),"elevated_cell_ratio":round(float(np.mean(boundary[valid]>=.45)),4)},"regime_mix":mix,"transition_image_url":"/terrain-transition-image","transition_image_sha256":hashlib.sha256(TRANSITION_FILE.read_bytes()).hexdigest(),"boundary_image_url":"/flow-regime-boundary-image","boundary_image_sha256":hashlib.sha256(BOUNDARY_FILE.read_bytes()).hexdigest(),"particle_directives":{"transition_jitter_px":round(jitter,2),"boundary_softening":round(soften,4),"regime_blend":round(blend,4),"transition_band":[.38,.78]},"display_label":f'terrain transitions {_band(tm)} · regime boundaries {_band(bm)} · {round(conf_mean*100)}% support',"scene_directive":"Show restrained gold transition illumination and thin pale regime-boundary traces. Blend visual motion gently across these zones rather than creating hard edges.","claim_boundary":"Terrain transition zones and flow-regime boundaries are DEM-derived interpretive boundaries. They are not measured atmospheric fronts, CFD regime changes, plume edges, concentration gradients, travel-time boundaries, or proof of actual airflow behavior."}
        META_FILE.write_text(json.dumps(out,indent=2)); return out
    except Exception as exc:
        o=_unavailable(f'terrain transition generation failed · {type(exc).__name__}','terrain_transition_generation_failed'); o['error_type']=type(exc).__name__; return o
