from __future__ import annotations
from typing import Any
PASS_ID="SV2-47"

def _clamp(v,lo,hi): return max(lo,min(hi,float(v)))

def scientific_cinematic_camera_context(scene:dict)->dict[str,Any]:
    cadence=scene.get("integrated_scene_coherence") or {}
    authority=scene.get("integrated_response_authority") or {}
    response=scene.get("integrated_terrain_response") or {}
    location=scene.get("location") or {}
    center={"lat":float(location.get("lat",34.26)),"lon":float(location.get("lon",-119.03))}
    if cadence.get("data_state")!="integrated_scene_coherence_ready":
        return {"contract_version":"scientific_cinematic_camera_v1","pass_id":PASS_ID,"layer":"scientific_cinematic_camera","evidence_state":"inferred","data_state":"scientific_camera_unavailable_safe","status":"unavailable_safe","display_label":"scientific camera unavailable · scene cadence missing","camera_authority":0.0,"mode":"static_evidence_view","keyframes":[],"interaction_guardrails":{"pause_on_user_input":True,"reduced_motion_respected":True,"auto_resume":False},"scene_directive":"Keep the camera static until a coherent integrated scene exists.","claim_boundary":"Camera motion guides visual attention only. It does not reveal hidden plume geometry, prove airflow, reconstruct transport, or add scientific evidence."}
    c=_clamp(float(cadence.get("cadence_authority",0)),0,.35)
    conflict=_clamp(float(authority.get("conflict_statistics",{}).get("mean",0)),0,1)
    cam=_clamp(c*(1-.5*conflict),.06,.26)
    regime=response.get("dominant_regime") or authority.get("winning_regime") or "mixed-transition"
    offset={"confined":(-.018,.010),"transfer":(.012,.014),"dispersive":(.020,-.008),"mixed-transition":(.008,.006)}.get(regime,(.008,.006))
    dlat,dlon=offset
    return {"contract_version":"scientific_cinematic_camera_v1","pass_id":PASS_ID,"layer":"scientific_cinematic_camera","evidence_state":"inferred","data_state":"scientific_cinematic_camera_ready","status":"ready","display_label":f"scientific camera · {regime} framing · {round(cam*100)}% authority","camera_authority":round(cam,4),"mode":"evidence_guided_cinematic_observer","focus_regime":regime,"keyframes":[{"id":"establish","lat":center["lat"],"lon":center["lon"],"zoom_delta":0,"duration_ms":1400},{"id":"terrain_reveal","lat":center["lat"]+dlat,"lon":center["lon"]+dlon,"zoom_delta":1,"duration_ms":2200},{"id":"evidence_return","lat":center["lat"],"lon":center["lon"],"zoom_delta":0,"duration_ms":1800}],"interaction_guardrails":{"pause_on_user_input":True,"reduced_motion_respected":True,"auto_resume":False,"max_zoom_delta":1,"max_center_shift_degrees":.03,"looping":False},"scene_directive":"Use one restrained evidence-guided camera reveal, then return to the stable review frame. Stop permanently when the reviewer interacts.","claim_boundary":"Camera motion guides visual attention only. It does not reveal hidden plume geometry, prove airflow, reconstruct transport, or add scientific evidence."}
