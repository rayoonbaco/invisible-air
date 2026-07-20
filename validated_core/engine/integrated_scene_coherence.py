from __future__ import annotations
from typing import Any
PASS_ID="SV2-46"

def _clamp(v,lo,hi): return max(lo,min(hi,float(v)))

def integrated_scene_coherence_context(scene:dict)->dict[str,Any]:
    motion=scene.get("integrated_motion_orchestration") or {}
    volume=scene.get("integrated_air_volume_orchestration") or {}
    authority=scene.get("integrated_response_authority") or {}
    ready=motion.get("data_state")=="integrated_motion_orchestration_ready" and volume.get("data_state")=="integrated_air_volume_orchestration_ready"
    if not ready:
        return {"contract_version":"integrated_scene_coherence_v1","pass_id":PASS_ID,"layer":"integrated_scene_coherence","evidence_state":"inferred","data_state":"integrated_scene_coherence_unavailable_safe","status":"unavailable_safe","display_label":"scene cadence unavailable · integrated orchestration missing","cadence_authority":0.0,"phases":[],"timing":{"transition_seconds":1.4,"uncertainty_fade_seconds":1.2,"regime_overlap_seconds":0.0},"scene_directive":"Retain neutral timing until integrated orchestration is available.","claim_boundary":"Scene cadence coordinates visual timing only. It is not measured atmospheric evolution, plume dynamics, transport timing, concentration change, or observed physical motion."}
    base=_clamp(float(authority.get("visual_directives",{}).get("motion_authority",0)),0,.34)
    conflict=_clamp(float(authority.get("conflict_statistics",{}).get("mean",0)),0,1)
    cadence=_clamp(base*(1-.45*conflict),.08,.35)
    return {"contract_version":"integrated_scene_coherence_v1","pass_id":PASS_ID,"layer":"integrated_scene_coherence","evidence_state":"inferred","data_state":"integrated_scene_coherence_ready","status":"ready","display_label":f"integrated scene cadence · {round(cadence*100)}% authority","cadence_authority":round(cadence,4),"phases":[{"id":"observation","share":.18},{"id":"interpretation","share":.27},{"id":"integration","share":.35},{"id":"persistence","share":.20}],"timing":{"transition_seconds":round(1.1+1.3*(1-cadence/.35),2),"uncertainty_fade_seconds":round(.8+1.2*conflict,2),"regime_overlap_seconds":round(min(1.5,.4+conflict),2)},"scene_directive":"Synchronize terrain response, particles, air volume, confidence, and uncertainty on one restrained cadence. Never use abrupt scene-wide changes.","claim_boundary":"Scene cadence coordinates visual timing only. It is not measured atmospheric evolution, plume dynamics, transport timing, concentration change, or observed physical motion."}
