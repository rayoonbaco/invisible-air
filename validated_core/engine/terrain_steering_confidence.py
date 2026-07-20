from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from engine.terrain_steering_field import terrain_steering_field_context, FIELD_FILE
from engine.terrain_confidence import terrain_confidence_context, CONFIDENCE_RASTER_FILE

PASS_ID = "SV2-35"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"
CONFIDENCE_FILE = CACHE_DIR / "terrain_steering_confidence.png"
UNCERTAINTY_FILE = CACHE_DIR / "terrain_steering_uncertainty.png"
META_FILE = CACHE_DIR / "terrain_steering_confidence.json"


def _band(v: float) -> str:
    if v >= .82: return "very_high"
    if v >= .68: return "high"
    if v >= .50: return "moderate"
    if v >= .32: return "low"
    if v >= .15: return "review_carefully"
    return "insufficient_evidence"


def _uband(v: float) -> str:
    if v < .22: return "low_uncertainty"
    if v < .42: return "moderate_uncertainty"
    if v < .62: return "elevated_uncertainty"
    if v < .80: return "evidence_limited"
    return "insufficient_evidence"


def _unavailable(label: str, state: str="steering_confidence_unavailable_safe") -> dict[str, Any]:
    return {
        "contract_version":"terrain_steering_confidence_v1", "pass_id":PASS_ID,
        "layer":"terrain_steering_confidence", "evidence_state":"inferred",
        "data_state":state, "status":"unavailable_safe", "display_label":label,
        "confidence_statistics":{}, "uncertainty_statistics":{}, "contributors":[],
        "downgrade_reasons":[], "confidence_image_url":None, "uncertainty_image_url":None,
        "source_bbox":None, "scene_directive":"Keep confidence and uncertainty hidden until the steering field and terrain-quality evidence are ready.",
        "claim_boundary":"This field expresses confidence in the terrain-steering heuristic only. It is not confidence in methane presence, plume location, atmospheric transport, emissions magnitude, or source responsibility.",
    }


def terrain_steering_confidence_context(scene: dict, refresh: bool=False) -> dict[str, Any]:
    steering=scene.get("terrain_steering_field") or terrain_steering_field_context(scene)
    terrain_conf=scene.get("terrain_confidence") or terrain_confidence_context(scene)
    if steering.get("data_state") != "terrain_steering_field_cache" or not FIELD_FILE.exists():
        return _unavailable("steering confidence unavailable · steering field missing")
    if terrain_conf.get("data_state") != "terrain_confidence_ready" or not CONFIDENCE_RASTER_FILE.exists():
        return _unavailable("steering confidence unavailable · terrain confidence missing")
    source_key=f"{steering.get('image_sha256')}|{terrain_conf.get('composite_score')}|v1"
    cache_key=hashlib.sha256(source_key.encode()).hexdigest()
    if not refresh and META_FILE.exists() and CONFIDENCE_FILE.exists() and UNCERTAINTY_FILE.exists():
        try:
            cached=json.loads(META_FILE.read_text(encoding='utf-8'))
            if cached.get('cache_key')==cache_key: return cached
        except Exception: pass
    try:
        sf=np.asarray(Image.open(FIELD_FILE).convert('RGBA'),dtype=np.float32)
        tc=np.asarray(Image.open(CONFIDENCE_RASTER_FILE).convert('L'),dtype=np.float32)/255.0
        if tc.shape != sf.shape[:2]:
            tc=np.asarray(Image.fromarray((tc*255).astype(np.uint8)).resize((sf.shape[1],sf.shape[0]),Image.Resampling.BILINEAR),dtype=np.float32)/255.0
        strength=np.clip(sf[...,3]/150.0,0,1)
        # Spatial agreement proxy: coherent local strength raises confidence; abrupt disagreement raises uncertainty.
        local=(np.roll(strength,1,0)+np.roll(strength,-1,0)+np.roll(strength,1,1)+np.roll(strength,-1,1))/4.0
        coherence=1.0-np.clip(np.abs(strength-local)*2.2,0,1)
        wind=scene.get('wind') or {}
        wind_state=wind.get('data_state')
        atmospheric_support=0.72 if wind_state=='live_current_conditions' else 0.58 if wind_state=='stale_cached_current_conditions' else 0.38
        temporal_penalty=0.16 if (scene.get('observation_contract') or {}).get('reported_time_utc') is None else 0.0
        extra_support=0.0
        if (scene.get('gust_variability') or {}).get('data_state')=='gust_variability_window_cache': extra_support += .05
        if (scene.get('atmospheric_stability') or {}).get('data_state')=='atmospheric_stability_screen': extra_support += .04
        confidence=np.clip(0.34*tc + 0.30*strength + 0.22*coherence + 0.14*atmospheric_support + extra_support - temporal_penalty,0,1)
        valid=sf[...,3]>0
        confidence=np.where(valid,confidence,0)
        uncertainty=np.where(valid,1.0-confidence,0)
        # Calm cinematic confidence illumination: cool white/cyan; uncertainty: amber-violet veil.
        cr=np.clip(80+165*confidence,0,255); cg=np.clip(130+125*confidence,0,255); cb=np.clip(145+110*confidence,0,255)
        ca=np.where(valid,np.clip((confidence-.18)/.82*150,0,150),0)
        confidence_rgba=np.dstack([cr,cg,cb,ca]).astype(np.uint8)
        ur=np.clip(150+95*uncertainty,0,255); ug=np.clip(70+85*(1-uncertainty),0,255); ub=np.clip(110+95*uncertainty,0,255)
        ua=np.where(valid,np.clip((uncertainty-.25)/.75*145,0,145),0)
        uncertainty_rgba=np.dstack([ur,ug,ub,ua]).astype(np.uint8)
        CACHE_DIR.mkdir(parents=True,exist_ok=True)
        Image.fromarray(confidence_rgba,'RGBA').save(CONFIDENCE_FILE)
        Image.fromarray(uncertainty_rgba,'RGBA').save(UNCERTAINTY_FILE)
        vals=confidence[valid]
        uvals=uncertainty[valid]
        mean=float(vals.mean()) if vals.size else 0
        mean_u=float(uvals.mean()) if uvals.size else 1
        hist={}
        bands=[('very_high',.82,1.01),('high',.68,.82),('moderate',.50,.68),('low',.32,.50),('review_carefully',.15,.32),('insufficient_evidence',0,.15)]
        for name,lo,hi in bands: hist[name]=round(float(((vals>=lo)&(vals<hi)).mean()),4) if vals.size else 0
        downgrade=[]
        if temporal_penalty: downgrade.append('observation-time atmosphere unresolved')
        if wind_state!='live_current_conditions': downgrade.append('live wind unavailable or degraded')
        if (scene.get('gust_variability') or {}).get('data_state')!='gust_variability_window_cache': downgrade.append('gust variability unavailable')
        if (scene.get('atmospheric_stability') or {}).get('data_state')!='atmospheric_stability_screen': downgrade.append('atmospheric stability unavailable')
        chash=hashlib.sha256(CONFIDENCE_FILE.read_bytes()).hexdigest(); uhash=hashlib.sha256(UNCERTAINTY_FILE.read_bytes()).hexdigest()
        contract={
            "contract_version":"terrain_steering_confidence_v1","pass_id":PASS_ID,"layer":"terrain_steering_confidence",
            "evidence_state":"inferred","data_state":"terrain_steering_confidence_cache","status":"ready","cache_key":cache_key,
            "source_steering_sha256":steering.get('image_sha256'),"source_bbox":steering.get('source_dem_bbox'),
            "confidence_statistics":{"mean":round(mean,4),"band":_band(mean),"histogram":hist,"valid_cell_ratio":round(float(valid.mean()),4)},
            "uncertainty_statistics":{"mean":round(mean_u,4),"band":_uband(mean_u)},
            "contributors":[
                {"name":"terrain evidence quality","weight":.34,"state":terrain_conf.get('grade','available')},
                {"name":"steering signal strength","weight":.30,"state":steering.get('field_statistics',{}).get('strength_band','available')},
                {"name":"spatial coherence","weight":.22,"state":"cell-neighborhood agreement"},
                {"name":"atmospheric support","weight":.14,"state":wind_state or 'unavailable'},
            ],
            "downgrade_reasons":downgrade,
            "confidence_image_url":"/terrain-steering-confidence-image","uncertainty_image_url":"/terrain-steering-uncertainty-image",
            "confidence_image_sha256":chash,"uncertainty_image_sha256":uhash,
            "display_label":f"{_band(mean).replace('_',' ')} confidence · {round(mean*100)}% · {_uband(mean_u).replace('_',' ')}",
            "scene_directive":"Use soft confidence illumination and an optional uncertainty veil. Never use confidence brightness as methane concentration or plume certainty.",
            "claim_boundary":"This field expresses confidence in the terrain-steering heuristic only. It is not confidence in methane presence, plume location, atmospheric transport, emissions magnitude, or source responsibility.",
        }
        META_FILE.write_text(json.dumps(contract,indent=2),encoding='utf-8')
        return contract
    except Exception as exc:
        out=_unavailable(f"steering confidence generation failed · {type(exc).__name__}","steering_confidence_generation_failed")
        out['error_type']=type(exc).__name__
        return out
