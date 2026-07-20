from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any
import numpy as np
from PIL import Image
from engine.integrated_terrain_response import FIELD_FILE, AGREEMENT_FILE

PASS_ID='SV2-43'
CACHE_DIR=Path(__file__).resolve().parents[1]/'data'/'cache'
AUTHORITY_FILE=CACHE_DIR/'integrated_response_authority.png'
CONFLICT_FILE=CACHE_DIR/'integrated_response_conflict.png'
META_FILE=CACHE_DIR/'integrated_response_authority.json'

def _clamp(v,lo=0.0,hi=1.0): return max(lo,min(hi,float(v)))
def _band(v): return 'high' if v>=.68 else 'moderate' if v>=.42 else 'low' if v>=.2 else 'evidence-limited'
def _unavailable(label,state='integrated_response_authority_unavailable_safe'):
    return {'contract_version':'integrated_response_authority_v1','pass_id':PASS_ID,'layer':'integrated_response_authority_conflict_resolution','evidence_state':'inferred','data_state':state,'status':'unavailable_safe','display_label':label,'authority_statistics':{},'conflict_statistics':{},'resolution_policy':{},'winning_regime':'unavailable','suppressed_regimes':[],'authority_image_url':None,'conflict_image_url':None,'visual_directives':{'authority_opacity':0.0,'conflict_veil':0.0,'motion_authority':0.0},'scene_directive':'Do not apply integrated visual authority until the integrated response and agreement surfaces are available.','claim_boundary':'Integrated response authority governs only the visual influence of DEM-derived terrain heuristics. It is not confidence in methane presence, measured airflow, plume transport, concentration, exposure, or source responsibility.'}

def integrated_response_authority_context(scene:dict,refresh:bool=False)->dict[str,Any]:
    integrated=scene.get('integrated_terrain_response') or {}
    if integrated.get('data_state')!='integrated_terrain_response_cache' or not FIELD_FILE.exists() or not AGREEMENT_FILE.exists():
        return _unavailable('response authority unavailable · integrated terrain response missing')
    key=hashlib.sha256((str(integrated.get('cache_key',''))+'|authority-v1').encode()).hexdigest()
    if not refresh and META_FILE.exists() and AUTHORITY_FILE.exists() and CONFLICT_FILE.exists():
        try:
            c=json.loads(META_FILE.read_text())
            if c.get('cache_key')==key:return c
        except Exception: pass
    try:
        field=np.asarray(Image.open(FIELD_FILE).convert('RGBA'),dtype=float)
        agree=np.asarray(Image.open(AGREEMENT_FILE).convert('RGBA'),dtype=float)
        field_strength=np.clip(field[...,3]/255.0,0,1)
        agreement=np.clip(agree[...,3]/150.0,0,1)
        conflict_ratio=float((integrated.get('agreement_statistics') or {}).get('conflict_cell_ratio',0.0))
        conflict=np.clip((1-agreement)*(.55+.45*field_strength),0,1)
        authority=np.clip(field_strength*(.30+.70*agreement)*(1-.55*conflict),0,1)
        # categorical winner from integrated palette
        rgb=field[...,:3]
        palette=np.array([[66,205,190],[242,184,92],[104,171,239],[190,132,222]],dtype=float)
        dist=np.sum((rgb[...,None,:]-palette[None,None,:,:])**2,axis=-1)
        dom=np.argmin(dist,axis=-1)
        names=['confined','transfer','dispersive','mixed-transition']
        weighted={name:float(np.sum(authority*(dom==i))) for i,name in enumerate(names)}
        winning=max(weighted,key=weighted.get)
        suppressed=[n for n in names if n!=winning and weighted[n] < weighted[winning]*.55]
        rgba=np.zeros_like(field,dtype=np.uint8); rgba[...,:3]=np.array([118,226,207],dtype=np.uint8); rgba[...,3]=np.clip(authority*165,0,165).astype(np.uint8)
        crgba=np.zeros_like(field,dtype=np.uint8); crgba[...,:3]=np.array([226,116,170],dtype=np.uint8); crgba[...,3]=np.clip(conflict*145,0,145).astype(np.uint8)
        CACHE_DIR.mkdir(parents=True,exist_ok=True)
        Image.fromarray(rgba,'RGBA').save(AUTHORITY_FILE); Image.fromarray(crgba,'RGBA').save(CONFLICT_FILE)
        mean_auth=float(np.mean(authority)); mean_conf=float(np.mean(conflict)); max_auth=float(np.max(authority))
        resolution='agreement-weighted winner' if mean_conf<.45 else 'conflict-preserving blend'
        out={'contract_version':'integrated_response_authority_v1','pass_id':PASS_ID,'layer':'integrated_response_authority_conflict_resolution','evidence_state':'inferred','data_state':'integrated_response_authority_cache','status':'ready','cache_key':key,'source_integrated_cache_key':integrated.get('cache_key'),'winning_regime':winning,'suppressed_regimes':suppressed,'authority_statistics':{'mean':round(mean_auth,4),'maximum':round(max_auth,4),'band':_band(mean_auth),'authorized_cell_ratio':round(float(np.mean(authority>.18)),4)},'conflict_statistics':{'mean':round(mean_conf,4),'band':_band(mean_conf),'high_conflict_cell_ratio':round(float(np.mean(conflict>.58)),4),'source_conflict_cell_ratio':round(conflict_ratio,4)},'resolution_policy':{'mode':resolution,'winner_requires_agreement':True,'conflict_is_preserved':True,'suppression_threshold':'below 55% of winning weighted support','hard_override_allowed':False},'authority_image_url':'/integrated-response-authority-image','authority_image_sha256':hashlib.sha256(AUTHORITY_FILE.read_bytes()).hexdigest(),'conflict_image_url':'/integrated-response-conflict-image','conflict_image_sha256':hashlib.sha256(CONFLICT_FILE.read_bytes()).hexdigest(),'visual_directives':{'authority_opacity':round(_clamp(mean_auth*.52,0,.40),4),'conflict_veil':round(_clamp(mean_conf*.38,0,.32),4),'motion_authority':round(_clamp(mean_auth*(1-mean_conf)*.48,0,.34),4)},'display_label':f"response authority {_band(mean_auth)} · {round(mean_auth*100)}% · conflict {_band(mean_conf)}",'scene_directive':'Let the integrated response influence visuals only in proportion to agreement-weighted authority. Preserve conflict as a visible veil and never force a winner where support is weak.','claim_boundary':'Integrated response authority governs only the visual influence of DEM-derived terrain heuristics. It is not confidence in methane presence, measured airflow, plume transport, concentration, exposure, or source responsibility.'}
        META_FILE.write_text(json.dumps(out,indent=2)); return out
    except Exception as exc:
        o=_unavailable(f'response authority generation failed · {type(exc).__name__}','integrated_response_authority_generation_failed');o['error_type']=type(exc).__name__;return o
