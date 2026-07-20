from __future__ import annotations
from typing import Any
PASS_ID = "SV2-48"

def _clamp(v, lo, hi):
    return max(lo, min(hi, float(v)))

def evidence_guided_focus_depth_context(scene: dict) -> dict[str, Any]:
    camera = scene.get("scientific_cinematic_camera") or {}
    authority = scene.get("integrated_response_authority") or {}
    response = scene.get("integrated_terrain_response") or {}
    regime_conf = scene.get("terrain_regime_confidence") or {}
    ready = camera.get("data_state") == "scientific_cinematic_camera_ready"
    if not ready:
        return {
            "contract_version":"evidence_guided_focus_depth_v1","pass_id":PASS_ID,
            "layer":"evidence_guided_focus_depth","evidence_state":"inferred",
            "data_state":"focus_depth_unavailable_safe","status":"unavailable_safe",
            "display_label":"focus and depth unavailable · scientific camera missing",
            "focus_authority":0.0,"focus_target":"stable_review_frame","depth_planes":[],
            "visual_directives":{"vignette_opacity":0.0,"terrain_contrast":1.0,"air_volume_emphasis":1.0,"uncertainty_softening":0.0,"max_blur_px":0.0},
            "interaction_guardrails":{"reviewer_override":True,"reduced_motion_respected":True,"no_hidden_evidence":True},
            "scene_directive":"Keep all evidence planes equally legible until an evidence-guided camera state exists.",
            "claim_boundary":"Focus, blur, glow, contrast, and depth cues guide attention only. They do not measure distance, concentration, plume thickness, hidden geometry, or atmospheric structure."
        }
    cam=_clamp(camera.get("camera_authority",0),0,.26)
    conflict=_clamp((authority.get("conflict_statistics") or {}).get("mean",0),0,1)
    ambiguity=_clamp((regime_conf.get("ambiguity_statistics") or {}).get("mean",0),0,1)
    focus=_clamp(cam*(1-.42*conflict)*(1-.30*ambiguity),.05,.24)
    regime=response.get("dominant_regime") or authority.get("winning_regime") or "mixed-transition"
    target={"confined":"terrain_corridor","transfer":"ridge_and_gap","dispersive":"downwind_expansion","mixed-transition":"uncertainty_boundary"}.get(regime,"stable_review_frame")
    blur=round(_clamp(.35+1.4*ambiguity,0,1.8),2)
    vignette=round(_clamp(.08+focus*.48,0,.20),3)
    return {
        "contract_version":"evidence_guided_focus_depth_v1","pass_id":PASS_ID,
        "layer":"evidence_guided_focus_depth","evidence_state":"inferred",
        "data_state":"evidence_guided_focus_depth_ready","status":"ready",
        "display_label":f"evidence-guided focus · {regime} · {round(focus*100)}% authority",
        "focus_authority":round(focus,4),"focus_target":target,"focus_regime":regime,
        "depth_planes":[
            {"id":"terrain_evidence","order":1,"role":"measured foundation","emphasis":round(1+.12*focus,3)},
            {"id":"atmospheric_volume","order":2,"role":"visual reconstruction","emphasis":round(1+.16*focus,3)},
            {"id":"confidence","order":3,"role":"interpretive support","emphasis":round(1+.10*focus,3)},
            {"id":"uncertainty","order":4,"role":"visible limitation","emphasis":round(1+.18*ambiguity,3)},
        ],
        "visual_directives":{
            "vignette_opacity":vignette,"terrain_contrast":round(1+.10*focus,3),
            "air_volume_emphasis":round(1+.14*focus,3),"uncertainty_softening":round(.15+.35*ambiguity,3),
            "max_blur_px":blur,"edge_fade":round(_clamp(.10+.28*conflict,0,.34),3),
            "focus_pulse":False,"depth_of_field_simulation":False
        },
        "interaction_guardrails":{"reviewer_override":True,"reduced_motion_respected":True,"no_hidden_evidence":True,"no_focus_lock":True,"no_looping":True},
        "scene_directive":"Use restrained contrast, edge fade, and depth separation to guide attention while keeping terrain, atmospheric reconstruction, confidence, and uncertainty simultaneously legible.",
        "claim_boundary":"Focus, blur, glow, contrast, and depth cues guide attention only. They do not measure distance, concentration, plume thickness, hidden geometry, or atmospheric structure."
    }
