from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image
from engine.full_dem import RASTER_FILE, full_dem_context
from engine.canyon_channeling import CHANNEL_FILE, DRAINAGE_FILE
from engine.ridge_spillover_shelter import SPILLOVER_FILE, SHELTER_FILE
from engine.saddle_gap_acceleration import SADDLE_FILE, GAP_FILE
from engine.basin_retention_cold_air_pooling import BASIN_FILE, COLD_POOL_FILE
from engine.terrain_convergence_accumulation import CONVERGENCE_FILE, ACCUMULATION_FILE
from engine.terrain_divergence_dispersion import DIVERGENCE_FILE, DISPERSION_FILE
from engine.terrain_transition_regimes import TRANSITION_FILE, BOUNDARY_FILE
from engine.terrain_regime_confidence import CONFIDENCE_FILE, AMBIGUITY_FILE

PASS_ID="SV2-42"
CACHE_DIR=Path(__file__).resolve().parents[1]/"data"/"cache"
FIELD_FILE=CACHE_DIR/"integrated_terrain_response.png"
AGREEMENT_FILE=CACHE_DIR/"integrated_terrain_agreement.png"
META_FILE=CACHE_DIR/"integrated_terrain_response.json"

def _clamp(v,lo=0.0,hi=1.0): return max(lo,min(hi,float(v)))
def _band(v): return "high" if v>=.68 else "moderate" if v>=.42 else "low" if v>=.2 else "evidence-limited"
def _alpha(path:Path, shape):
    if not path.exists(): return np.zeros(shape,dtype=float)
    a=np.asarray(Image.open(path).convert("RGBA"),dtype=float)
    if a.shape[:2]!=shape: a=np.asarray(Image.fromarray(a.astype(np.uint8)).resize((shape[1],shape[0])),dtype=float)
    return np.clip(a[...,3]/255.0,0,1)
def _unavailable(label,state="integrated_terrain_response_unavailable_safe"):
    return {"contract_version":"integrated_terrain_response_v1","pass_id":PASS_ID,"layer":"integrated_terrain_response_field","evidence_state":"inferred","data_state":state,"status":"unavailable_safe","display_label":label,"response_statistics":{},"agreement_statistics":{},"component_support":{},"dominant_regime":"unavailable","field_image_url":None,"agreement_image_url":None,"visual_directives":{"field_opacity":0.0,"agreement_glow":0.0,"conflict_veil":0.0},"scene_directive":"Hide the integrated response field until validated component surfaces are available.","claim_boundary":"The integrated terrain-response field synthesizes DEM-derived visual potentials. It is not measured airflow, CFD, plume transport, methane concentration, exposure, or proof of actual atmospheric behavior."}

def integrated_terrain_response_context(scene:dict,refresh:bool=False)->dict[str,Any]:
    dem=scene.get("full_dem") or full_dem_context(scene)
    required_states={
      "terrain_regime_confidence":"terrain_regime_confidence_cache",
      "terrain_transition_regimes":"terrain_transition_regimes_cache",
      "terrain_convergence_accumulation":"terrain_convergence_accumulation_cache",
      "terrain_divergence_dispersion":"terrain_divergence_dispersion_cache",
    }
    if dem.get("data_state")!="continuous_dem_cache" or not RASTER_FILE.exists(): return _unavailable("integrated response unavailable · validated DEM missing")
    missing=[k for k,v in required_states.items() if (scene.get(k) or {}).get("data_state")!=v]
    if missing:return _unavailable("integrated response unavailable · component evidence missing: "+", ".join(missing))
    source_hash=dem.get("raster_sha256") or dem.get("sha256") or "unknown"
    key=hashlib.sha256((source_hash+"|"+"|".join(str((scene.get(k)or{}).get("cache_key","")) for k in required_states)+"|v1").encode()).hexdigest()
    if not refresh and META_FILE.exists() and FIELD_FILE.exists() and AGREEMENT_FILE.exists():
        try:
            c=json.loads(META_FILE.read_text())
            if c.get("cache_key")==key:return c
        except Exception:pass
    try:
        base=np.asarray(Image.open(CONFIDENCE_FILE).convert("RGBA")); shape=base.shape[:2]
        confidence=_alpha(CONFIDENCE_FILE,shape); ambiguity=_alpha(AMBIGUITY_FILE,shape)
        channel=np.maximum(_alpha(CHANNEL_FILE,shape),_alpha(DRAINAGE_FILE,shape))
        shelter=np.maximum(_alpha(SHELTER_FILE,shape),_alpha(BASIN_FILE,shape))
        retain=np.maximum.reduce([_alpha(COLD_POOL_FILE,shape),_alpha(ACCUMULATION_FILE,shape),_alpha(CONVERGENCE_FILE,shape)])
        transfer=np.maximum.reduce([_alpha(SPILLOVER_FILE,shape),_alpha(SADDLE_FILE,shape),_alpha(GAP_FILE,shape)])
        spread=np.maximum.reduce([_alpha(DIVERGENCE_FILE,shape),_alpha(DISPERSION_FILE,shape)])
        transition=np.maximum(_alpha(TRANSITION_FILE,shape),_alpha(BOUNDARY_FILE,shape))
        confined=np.clip(.42*channel+.28*shelter+.30*retain,0,1)
        transfer=np.clip(.72*transfer+.28*channel,0,1)
        dispersive=np.clip(.78*spread+.22*(1-shelter),0,1)
        mixed=np.clip(.64*transition+.36*ambiguity,0,1)
        stack=np.stack([confined,transfer,dispersive,mixed],axis=-1)
        order=np.sort(stack,axis=-1)
        top=order[...,-1]; second=order[...,-2]
        separation=np.clip(top-second,0,1)
        agreement=np.clip((.55*separation+.45*confidence)*(1-.45*ambiguity),0,1)
        authority=np.clip(top*(.45+.55*confidence)*(1-.35*ambiguity),0,1)
        dominant=np.argmax(stack,axis=-1)
        palette=np.array([[66,205,190],[242,184,92],[104,171,239],[190,132,222]],dtype=np.uint8)
        rgba=np.zeros((*shape,4),dtype=np.uint8); rgba[...,:3]=palette[dominant]; rgba[...,3]=np.clip(authority*142,0,142).astype(np.uint8)
        agree=np.zeros((*shape,4),dtype=np.uint8); agree[...,0]=125; agree[...,1]=225; agree[...,2]=210; agree[...,3]=np.clip(agreement*150,0,150).astype(np.uint8)
        CACHE_DIR.mkdir(parents=True,exist_ok=True); Image.fromarray(rgba,"RGBA").save(FIELD_FILE); Image.fromarray(agree,"RGBA").save(AGREEMENT_FILE)
        ratios={name:round(float(np.mean(dominant==i)),4) for i,name in enumerate(["confined","transfer","dispersive","mixed-transition"])}
        dom=max(ratios,key=ratios.get); mean_auth=float(np.mean(authority)); mean_agree=float(np.mean(agreement)); conflict=float(np.mean((separation<.12)|(ambiguity>.52)))
        support={"channeling_mean":round(float(np.mean(channel)),4),"shelter_mean":round(float(np.mean(shelter)),4),"retention_convergence_mean":round(float(np.mean(retain)),4),"ridge_gap_transfer_mean":round(float(np.mean(transfer)),4),"divergence_dispersion_mean":round(float(np.mean(spread)),4),"transition_ambiguity_mean":round(float(np.mean(mixed)),4),"regime_confidence_mean":round(float(np.mean(confidence)),4)}
        out={"contract_version":"integrated_terrain_response_v1","pass_id":PASS_ID,"layer":"integrated_terrain_response_field","evidence_state":"inferred","data_state":"integrated_terrain_response_cache","status":"ready","cache_key":key,"source_dem_sha256":source_hash,"source_bbox":dem.get("bbox") or dem.get("requested_bbox"),"dominant_regime":dom,"response_statistics":{"mean_authority":round(mean_auth,4),"authority_band":_band(mean_auth),"regime_ratios":ratios},"agreement_statistics":{"mean":round(mean_agree,4),"band":_band(mean_agree),"conflict_cell_ratio":round(conflict,4)},"component_support":support,"field_image_url":"/integrated-terrain-response-image","field_image_sha256":hashlib.sha256(FIELD_FILE.read_bytes()).hexdigest(),"agreement_image_url":"/integrated-terrain-agreement-image","agreement_image_sha256":hashlib.sha256(AGREEMENT_FILE.read_bytes()).hexdigest(),"visual_directives":{"field_opacity":round(_clamp(mean_auth*.46,.10,.38),4),"agreement_glow":round(_clamp(mean_agree*.42,0,.34),4),"conflict_veil":round(_clamp(conflict*.32,0,.28),4)},"display_label":f"integrated response {dom} · {_band(mean_auth)} authority · {round(mean_agree*100)}% agreement","scene_directive":"Use one restrained integrated field to summarize confined, transfer, dispersive, and mixed terrain responses. Preserve access to every component and soften areas of disagreement.","claim_boundary":"The integrated terrain-response field synthesizes DEM-derived visual potentials. It is not measured airflow, CFD, plume transport, methane concentration, exposure, or proof of actual atmospheric behavior."}
        META_FILE.write_text(json.dumps(out,indent=2)); return out
    except Exception as exc:
        o=_unavailable(f"integrated response generation failed · {type(exc).__name__}","integrated_terrain_response_generation_failed");o["error_type"]=type(exc).__name__;return o
