from __future__ import annotations

ALLOWED_STATES = (
    "observed",
    "measured",
    "modeled",
    "current_context",
    "visual_reconstruction",
    "contextual",
    "inferred",
    "unavailable",
    "unknown",
    "not_modeled",
    "not_claimed",
)

STATE_DEFINITIONS = {
    "observed": {"label": "Observed", "meaning": "Directly reported by an external observation source.", "color_role": "green"},
    "measured": {"label": "Measured", "meaning": "Derived from a measured physical or geospatial dataset.", "color_role": "blue"},
    "modeled": {"label": "Modeled", "meaning": "Produced by an explicit scientific or numerical model.", "color_role": "violet"},
    "current_context": {"label": "Current context", "meaning": "Describes present conditions, not the reported event time.", "color_role": "amber"},
    "visual_reconstruction": {"label": "Visual reconstruction", "meaning": "A bounded human-review visualization, not measured geometry or concentration.", "color_role": "cyan"},
    "contextual": {"label": "Context", "meaning": "Supports orientation or interpretation without being emissions evidence.", "color_role": "slate"},
    "inferred": {"label": "Inferred", "meaning": "A reasoned interpretation derived from other evidence and clearly labeled as such.", "color_role": "orange"},
    "unavailable": {"label": "Unavailable", "meaning": "The data may exist but was not retrieved or supplied.", "color_role": "gray"},
    "unknown": {"label": "Unknown", "meaning": "The value is not known and is not estimated.", "color_role": "black"},
    "not_modeled": {"label": "Not modeled", "meaning": "No scientific model has produced this layer or conclusion.", "color_role": "rose"},
    "not_claimed": {"label": "Not claimed", "meaning": "The system explicitly does not assert this conclusion.", "color_role": "white"},
}


def state(state_id: str) -> dict:
    if state_id not in STATE_DEFINITIONS:
        raise ValueError(f"Unsupported evidence state: {state_id}")
    return {"id": state_id, **STATE_DEFINITIONS[state_id]}


def layer_state(layer_id: str, primary_state: str, purpose: str, represents: str, does_not_represent: list[str]) -> dict:
    return {
        "layer_id": layer_id,
        "primary_state": primary_state,
        "state": state(primary_state),
        "purpose": purpose,
        "represents": represents,
        "does_not_represent": does_not_represent,
    }


def build_evidence_vocabulary(scene: dict) -> dict:
    observation = scene.get("observation_contract", {})
    observation_state = "observed" if observation.get("data_state") == "manifest_loaded" else "unavailable"
    terrain_state = "measured" if scene.get("terrain", {}).get("data_state") == "measured_sample_cache" else "unavailable"
    hillshade_state = "measured" if scene.get("hillshade", {}).get("data_state") == "dem_derived_hillshade_cache" else "unavailable"
    layers = [
        layer_state("observation", observation_state, "Preserve the reported observation record and provenance.", "A source-seeded observation record when its manifest is available.", ["app-detected methane", "source attribution", "certified quantification"]),
        layer_state("current_wind", "current_context", "Orient the scene using present-day wind.", "Current measured or provider-reported wind context.", ["observation-time wind", "historical transport", "measured turbulence"]),
        layer_state("terrain", terrain_state, "Describe the measured land beneath the scene.", "Measured elevation context when retrieval succeeds.", ["methane evidence", "transport proof", "continuous certified DEM unless explicitly loaded"]),
        layer_state("hillshade", hillshade_state, "Reveal continuous terrain relief from the validated DEM.", "A reproducible DEM-derived hillshade with recorded illumination parameters.", ["methane evidence", "event-time sunlight", "agency certification"]),
        layer_state("basemap", "contextual", "Provide geographic orientation.", "Roads, place labels, coastlines, and map context.", ["emissions evidence", "facility responsibility"]),
        layer_state("plume_visualization", "visual_reconstruction", "Make invisible-air context reviewable.", "A map-registered visual pathway tied to current context and measured terrain.", ["detected methane geometry", "measured concentration", "dispersion-model output"]),
        layer_state("air_volume", "visual_reconstruction", "Create visual continuity and depth.", "A layered atmospheric visual form.", ["plume height", "mass", "emissions rate"]),
        layer_state("living_wind", "visual_reconstruction", "Express live-wind-responsive motion.", "Bounded visual motion driven by current wind inputs.", ["measured turbulence field", "event-time transport"]),
        layer_state("atmospheric_stability", "inferred" if scene.get("atmospheric_stability", {}).get("data_state") == "atmospheric_stability_screen" else "unavailable", "Screen likely near-surface mixing tendency from archived weather inputs.", "A bounded stable, neutral, unstable, or unknown screening class.", ["measured turbulence", "formal Pasquill-Gifford class", "dispersion-model output"]),
        layer_state("evidence_time", "current_context", "Keep present conditions separate from observation time.", "A temporal alignment and gap contract.", ["event-time weather confirmation", "historical reconstruction"]),
        layer_state("dispersion_model", "not_modeled", "State the modeling boundary.", "No atmospheric dispersion model is active in this pass.", ["HYSPLIT output", "AERMOD output", "certified forecast"]),
        layer_state("attribution", "not_claimed", "State the responsibility boundary.", "No responsibility or illegality conclusion.", ["facility blame", "operator culpability", "enforcement readiness"]),
    ]
    return {
        "contract_version": "evidence_state_vocabulary_v1",
        "pass_id": "SV2-35",
        "status": "controlled_vocabulary_active",
        "allowed_states": list(ALLOWED_STATES),
        "definitions": STATE_DEFINITIONS,
        "layer_count": len(layers),
        "layers": layers,
        "display_label": f"{len(layers)} layers · controlled evidence language",
        "claim_boundary": "Evidence-state labels classify how information enters the scene; they do not increase the underlying certainty or validate a provider claim.",
    }
