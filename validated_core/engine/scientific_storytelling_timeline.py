from __future__ import annotations
from typing import Any

PASS_ID="SV2-52"

def _clamp(v: Any, lo: float, hi: float) -> float:
    try: v=float(v)
    except (TypeError, ValueError): v=lo
    return max(lo,min(hi,v))

def scientific_storytelling_timeline_context(scene: dict) -> dict[str, Any]:
    annotations=scene.get("scientific_annotation_choreography") or {}
    coherence=scene.get("integrated_scene_coherence") or {}
    hierarchy=scene.get("evidence_visual_hierarchy") or {}
    ready=annotations.get("data_state")=="scientific_annotation_choreography_ready"
    authority=_clamp(annotations.get("annotation_authority",0),0,.28)
    cadence=_clamp(coherence.get("cadence_authority",0),0,.35)
    hierarchy_auth=_clamp(hierarchy.get("hierarchy_authority",0),0,.30)
    phases=[
      {"id":"terrain","label":"Measured terrain establishes place","start_ms":0,"duration_ms":1800,"evidence_state":"measured"},
      {"id":"wind","label":"Available wind context appears","start_ms":1800,"duration_ms":1800,"evidence_state":"current_context"},
      {"id":"steering","label":"Terrain-response interpretation develops","start_ms":3600,"duration_ms":2200,"evidence_state":"inferred"},
      {"id":"confidence","label":"Confidence and conflict become visible","start_ms":5800,"duration_ms":2000,"evidence_state":"inferred"},
      {"id":"sources","label":"Evidence provenance and citations surface","start_ms":7800,"duration_ms":1800,"evidence_state":"observed"},
      {"id":"uncertainty","label":"Unknowns and missing evidence remain explicit","start_ms":9600,"duration_ms":2200,"evidence_state":"unknown"},
      {"id":"synthesis","label":"Stable review frame","start_ms":11800,"duration_ms":2600,"evidence_state":"mixed"},
    ]
    if not ready:
        return {"contract_version":"scientific_storytelling_timeline_v1","pass_id":PASS_ID,"layer":"scientific_storytelling_timeline","evidence_state":"inferred","data_state":"scientific_storytelling_timeline_unavailable_safe","status":"unavailable_safe","display_label":"scientific timeline unavailable · annotation choreography missing","timeline_authority":0.0,"timeline_mode":"static_review","total_duration_ms":0,"phases":phases,"interaction_guardrails":{"reviewer_override":True,"reduced_motion_respected":True,"autoplay_once":False},"scene_directive":"Show the complete stable review frame without staged reveals.","claim_boundary":"The timeline sequences explanation only. It does not reconstruct observation time, plume travel time, atmospheric evolution, or physical causality."}
    timeline=_clamp(.36*authority+.34*cadence+.22*hierarchy_auth+.06,.10,.30)
    return {"contract_version":"scientific_storytelling_timeline_v1","pass_id":PASS_ID,"layer":"scientific_storytelling_timeline","evidence_state":"inferred","data_state":"scientific_storytelling_timeline_ready","status":"ready","display_label":f"scientific storytelling timeline · 7 phases · {round(timeline*100)}% authority","timeline_authority":round(timeline,4),"timeline_mode":"evidence_first_single_reveal","total_duration_ms":14400,"phases":phases,"interaction_guardrails":{"reviewer_override":True,"reduced_motion_respected":True,"autoplay_once":True,"no_loop":True,"skip_control_required":True,"uncertainty_cannot_be_skipped":True},"scene_directive":"Reveal place, context, interpretation, confidence, provenance, uncertainty, and synthesis once in that order, then remain in a stable review frame.","claim_boundary":"The timeline sequences explanation only. It does not reconstruct observation time, plume travel time, atmospheric evolution, or physical causality."}
