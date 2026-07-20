from __future__ import annotations
from typing import Any

PASS_ID = "SV2-51"

def _clamp(v: Any, lo: float, hi: float) -> float:
    try: v=float(v)
    except (TypeError, ValueError): v=lo
    return max(lo,min(hi,v))

def scientific_annotation_choreography_context(scene: dict) -> dict[str, Any]:
    hierarchy=scene.get("evidence_visual_hierarchy") or {}
    coherence=scene.get("integrated_scene_coherence") or {}
    missing=scene.get("missing_evidence") or {}
    ready=hierarchy.get("data_state")=="evidence_visual_hierarchy_ready"
    unresolved=int((missing.get("summary") or {}).get("missing_count",0) or 0)
    authority=_clamp(hierarchy.get("hierarchy_authority",0),0,.30)
    cadence=_clamp(coherence.get("cadence_authority",0),0,.35)
    if not ready:
        return {"contract_version":"scientific_annotation_choreography_v1","pass_id":PASS_ID,"layer":"scientific_annotation_choreography","evidence_state":"inferred","data_state":"scientific_annotation_choreography_unavailable_safe","status":"unavailable_safe","display_label":"annotation choreography unavailable · hierarchy context missing","annotation_authority":0.0,"annotation_mode":"static_review_labels","label_budget":4,"priority_labels":["uncertainty","observed evidence","measured terrain","not claimed"],"timing":{"entry_ms":0,"hold_ms":0,"exit_ms":0},"collision_policy":{"avoid_map_controls":True,"avoid_source_marker":True,"max_simultaneous_labels":4},"interaction_guardrails":{"reviewer_override":True,"reduced_motion_respected":True,"labels_never_hide_uncertainty":True},"scene_directive":"Use static evidence labels until governed hierarchy is available.","claim_boundary":"Annotations organize evidence and guide reading order only. They do not add observations, certainty, concentration, distance, transport, or source attribution."}
    ann=_clamp(.44*authority+.26*cadence+.12, .10,.28)
    return {"contract_version":"scientific_annotation_choreography_v1","pass_id":PASS_ID,"layer":"scientific_annotation_choreography","evidence_state":"inferred","data_state":"scientific_annotation_choreography_ready","status":"ready","display_label":f"annotation choreography · {round(ann*100)}% authority · {unresolved} unresolved inputs visible","annotation_authority":round(ann,4),"annotation_mode":"evidence_first_contextual_labels","label_budget":6,"priority_labels":["uncertainty","observation record","measured terrain","current wind context","inferred terrain response","not claimed"],"timing":{"entry_ms":700,"stagger_ms":420,"hold_ms":3200,"exit_ms":650,"uncertainty_entry_first":True},"collision_policy":{"avoid_map_controls":True,"avoid_source_marker":True,"avoid_high_information_terrain":True,"max_simultaneous_labels":6,"minimum_spacing_px":18},"label_states":{"observed":"direct record","measured":"measured terrain","modeled":"modeled context","inferred":"interpretive terrain response","unknown":"unresolved","not_claimed":"explicit boundary"},"interaction_guardrails":{"reviewer_override":True,"reduced_motion_respected":True,"labels_never_hide_uncertainty":True,"no_looping_callouts":True},"scene_directive":"Introduce evidence labels in controlled order, preserve uncertainty, avoid collisions, and yield immediately to reviewer interaction.","claim_boundary":"Annotations organize evidence and guide reading order only. They do not add observations, certainty, concentration, distance, transport, or source attribution."}
