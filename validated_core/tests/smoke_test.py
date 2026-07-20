from __future__ import annotations

import os
import tempfile
import json
import sys
from pathlib import Path

os.environ["AW_DISABLE_LIVE_FETCH"] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402

ROUTES = [
    "/", "/scene", "/shot", "/scene.json", "/evidence", "/evidence.json",
    "/data-status", "/data-status.json", "/map-surface", "/map-surface.json",
    "/terrain", "/terrain.json", "/dem", "/dem.json", "/hillshade", "/hillshade.json", "/wind", "/wind.json", "/observation", "/observation.json", "/citations", "/citations.json", "/evidence-states", "/evidence-states.json", "/missing-evidence", "/missing-evidence.json", "/time-alignment", "/time-alignment.json", "/self-test",
    "/terrain-confidence", "/terrain-confidence.json", "/historical-weather", "/historical-weather.json", "/multi-level-wind", "/multi-level-wind.json", "/atmospheric-stability", "/atmospheric-stability.json", "/boundary-layer-depth", "/boundary-layer-depth.json", "/gust-variability", "/gust-variability.json", "/terrain-steering-field", "/terrain-steering-field.json", "/terrain-steering-confidence", "/terrain-steering-confidence.json", "/terrain-transition-regimes", "/terrain-transition-regimes.json", "/terrain-regime-confidence", "/terrain-regime-confidence.json", "/integrated-terrain-response", "/integrated-terrain-response.json", "/integrated-response-authority", "/integrated-response-authority.json", "/evidence-guided-focus-depth", "/evidence-guided-focus-depth.json", "/atmospheric-light-legibility", "/atmospheric-light-legibility.json", "/reviewer-guided-evidence-exploration", "/reviewer-guided-evidence-exploration.json", "/progressive-disclosure", "/progressive-disclosure.json", "/scientific-synthesis", "/scientific-synthesis.json", "/level-five-visual-composition", "/level-five-visual-composition.json", "/self-test.json", "/health", "/audit", "/audit.json", "/hunter", "/hunter.json",
]

REQUIRED_FILES = [
    "engine/integrated_scene_coherence.py",
    "engine/scientific_cinematic_camera.py",
    "engine/evidence_guided_focus_depth.py",
    "engine/atmospheric_light_legibility.py",
    "engine/evidence_visual_hierarchy.py",
    "engine/reviewer_guided_exploration.py",
    "engine/level_five_visual_composition.py",
    "templates/integrated_scene_coherence.html",
    "templates/scientific_cinematic_camera.html",
    "templates/evidence_guided_focus_depth.html",
    "templates/atmospheric_light_legibility.html",
    "templates/evidence_visual_hierarchy.html",
    "templates/reviewer_guided_exploration.html",
    "templates/level_five_visual_composition.html",
    "docs/INTEGRATED_SCENE_COHERENCE_SV2_46.md",
    "docs/SCIENTIFIC_CINEMATIC_CAMERA_SV2_47.md",
    "docs/EVIDENCE_GUIDED_FOCUS_DEPTH_SV2_48.md",
    "docs/ATMOSPHERIC_LIGHT_LEGIBILITY_SV2_49.md",
    "docs/REVIEWER_GUIDED_EVIDENCE_EXPLORATION_SV2_53.md",
    "docs/LEVEL_FIVE_VISUAL_COMPOSITION_SV2_56.md",
    "RUN_VERIFY_SV2_56.bat",
    "RUN_VERIFY_SV2_53.bat",
    "app.py", "engine/scene_config.py", "engine/source_registry.py", "engine/provenance.py",
    "engine/plume_model.py", "engine/basemap_surface.py", "engine/spatial_plume.py",
    "engine/evidence_packet.py", "engine/terrain_loader.py", "engine/full_dem.py", "engine/hillshade.py", "engine/slope_aspect.py", "engine/terrain_influence.py",
    "engine/wind_loader.py", "engine/terrain_plume_behavior.py", "engine/terrain_flow_path.py", "engine/terrain_lighting.py", "engine/air_volume.py", "engine/living_wind.py", "engine/evidence_time.py", "engine/observation_contract.py", "engine/citation_surface.py", "engine/evidence_vocabulary.py", "engine/missing_evidence.py",
    "engine/historical_weather.py", "engine/multi_level_wind.py", "engine/atmospheric_stability.py", "engine/boundary_layer_depth.py", "engine/gust_variability.py", "engine/terrain_atmosphere_index.py", "engine/terrain_steering_field.py", "engine/terrain_steering_confidence.py", "engine/terrain_responsive_particle_advection.py", "engine/ridge_spillover_shelter.py", "engine/canyon_channeling.py", "engine/saddle_gap_acceleration.py", "engine/basin_retention_cold_air_pooling.py", "engine/terrain_convergence_accumulation.py", "engine/terrain_divergence_dispersion.py", "engine/terrain_transition_regimes.py", "engine/terrain_regime_confidence.py", "engine/integrated_terrain_response.py", "engine/integrated_response_authority.py", "engine/integrated_motion_orchestration.py", "engine/integrated_air_volume_orchestration.py", "engine/pass_checks.py", "templates/terrain.html", "templates/wind.html", "templates/time_alignment.html", "templates/observation.html", "templates/citations.html", "templates/evidence_states.html", "templates/missing_evidence.html",
    "templates/historical_weather.html", "templates/multi_level_wind.html", "templates/atmospheric_stability.html", "templates/boundary_layer_depth.html", "templates/gust_variability.html", "templates/terrain_atmosphere_index.html", "templates/terrain_steering_field.html", "templates/terrain_steering_confidence.html", "templates/terrain_responsive_particle_advection.html", "templates/ridge_spillover_shelter.html", "templates/canyon_channeling.html", "templates/saddle_gap_acceleration.html", "templates/basin_retention_cold_air_pooling.html", "templates/terrain_convergence_accumulation.html", "templates/terrain_divergence_dispersion.html", "templates/terrain_transition_regimes.html", "templates/terrain_regime_confidence.html", "templates/integrated_terrain_response.html", "templates/integrated_response_authority.html", "templates/integrated_motion_orchestration.html", "templates/integrated_air_volume_orchestration.html", "templates/self_test.html", "templates/scene.html", "templates/dem.html", "templates/hillshade.html", "templates/slope_aspect.html", "static/js/plume_canvas.js",
    "static/js/map_scene.js", "static/css/styles.css", "docs/TERRAIN_LOADER_SV2_4.md",
    "docs/LIVE_WIND_CONNECTOR_SV2_5.md", "docs/HISTORICAL_WEATHER_RETRIEVAL_SV2_24.md", "docs/GUST_VARIABILITY_WINDOW_SV2_28.md", "RUN_VERIFY_SV2_28.bat",
    "tools/launch_review.py", "docs/TERRAIN_AFFECTED_PLUME_SV2_6.md",
    "docs/RELIABLE_LAUNCH_SV2_7.md", "docs/AUTOMATIC_TERRAIN_READINESS_SV2_8.md",
    "docs/TERRAIN_DRIVEN_FLOW_SV2_9.md", "docs/ELEVATION_LIGHTING_LOCAL_RELIEF_SV2_10.md", "docs/AIR_VOLUME_SV2_11.md", "docs/LIVING_WIND_SV2_12.md", "docs/EVIDENCE_TIME_ALIGNMENT_SV2_13.md", "docs/OBSERVATION_EVIDENCE_CONTRACT_SV2_14.md", "docs/CERTIFIED_HILLSHADE_LANE_SV2_20.md",
]

REQUIRED_TEXT = [
    ("/scene", "Look into the hidden air"),
    ("/scene", "living wind"),
    ("/scene", "current"),
    ("/scene", "visual reconstruction"),
    ("/scene", "Smoke test"),
    ("/wind", "current wind lane"),
    ("/wind", "Current, not observation-time"),
    ("/terrain", "Terrain evidence lane"),
    ("/evidence", "What is real"),
    ("/data-status", "Layer status"),
    ("/landforms", "Landform"),
    ("/terrain-confidence", "How much trust has the terrain stack earned"),
    ("/historical-weather", "Reconnect the weather clock"),
    ("/atmospheric-stability", "How readily might the near-surface air mix"),
    ("/gust-variability", "See how the wind changed around the evidence hour"),
    ("/terrain-steering-field", "Terrain Steering Field"),("/terrain-steering-confidence", "See where the steering field earns trust"),
    ("/steering-aware-air-volume", "Steering-Aware Air Volume"),
    ("/terrain-responsive-particle-advection", "Terrain-Responsive Particle Advection"),
    ("/terrain-responsive-particle-advection.json", "terrain_responsive_particle_advection_v1"),
    ("/ridge-spillover-lee-shelter", "Ridge Spillover"),
    ("/ridge-spillover-lee-shelter.json", "ridge_spillover_shelter_v1"),
    ("/canyon-channeling-drainage-alignment.json", "canyon_channeling_drainage_alignment_v1"),
    ("/saddle-transfer-gap-acceleration", "Saddle Transfer"),
    ("/saddle-transfer-gap-acceleration.json", "saddle_transfer_gap_acceleration_v1"),
    ("/terrain-transition-regimes", "Terrain transition zones"),
    ("/terrain-transition-regimes.json", "terrain_transition_regimes_v1"),
    ("/terrain-regime-confidence", "See where the terrain regime is clear"),
    ("/terrain-regime-confidence.json", "terrain_regime_confidence_v1"),
    ("/integrated-terrain-response", "See the terrain response as one auditable field"),
    ("/integrated-terrain-response.json", "integrated_terrain_response_v1"),
    ("/integrated-response-authority.json", "integrated_response_authority_v1"),
    ("/integrated-motion-orchestration.json", "integrated_motion_orchestration_v1"),
    ("/integrated-air-volume-orchestration.json", "integrated_air_volume_orchestration_v1"),
    ("/integrated-scene-coherence.json", "integrated_scene_coherence_v1"),
    ("/scientific-cinematic-camera", "Scientific Cinematic Camera Intelligence"),
    ("/scientific-cinematic-camera.json", "scientific_cinematic_camera_v1"),
    ("/evidence-guided-focus-depth", "Evidence-Guided Focus and Depth Composition"),
    ("/evidence-guided-focus-depth.json", "evidence_guided_focus_depth_v1"),
    ("/atmospheric-light-legibility", "Atmospheric Light, Shadow, and Evidence Legibility"),
    ("/atmospheric-light-legibility.json", "atmospheric_light_legibility_v1"),
    ("/evidence-visual-hierarchy.json", "evidence_visual_hierarchy_v1"),
    ("/reviewer-guided-evidence-exploration", "Reviewer-Guided Evidence Exploration"),
    ("/reviewer-guided-evidence-exploration.json", "reviewer_guided_evidence_exploration_v1"),
    ("/progressive-disclosure", "Progressive Disclosure and Scene Simplification"),
    ("/progressive-disclosure.json", "progressive_disclosure_v1"),
    ("/scientific-synthesis.json", "scientific_synthesis_decision_surface_v1"),
    ("/level-five-visual-composition", "Level Five Visual Composition and Performance"),
    ("/level-five-visual-composition.json", "level_five_visual_composition_v1"),
    ("/self-test", "SV2-50"),
    ("/observation", "The observation now has a record"),
    ("/observation", "Record, not verdict"),
    ("/citations", "Every visible layer has a trail"),
    ("/evidence-states", "Every layer says what kind of truth it carries"),
    ("/missing-evidence", "Evidence ends visibly"),
    ("/hillshade", "Let the continuous land reveal its shape"),
    ("/audit", "not because it is certain"),
    ("/hunter", "AI organizes attention"),
]

UNSAFE_PHRASES = [
    "detected methane leak", "confirmed methane leak", "responsible facility",
    "illegal emission", "certified emissions confirmed", "enforcement-ready",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def ok(message: str) -> None:
    print(f"PASS: {message}")


def main() -> None:
    passed = 0

    for rel in REQUIRED_FILES:
        if not (ROOT / rel).exists():
            fail(f"missing required file {rel}")
        passed += 1

    client = app.test_client()
    for route in ROUTES:
        response = client.get(route)
        if response.status_code != 200:
            fail(f"{route} returned {response.status_code}")
        passed += 1

    for route, expected in REQUIRED_TEXT:
        text = client.get(route).get_data(as_text=True).lower()
        if expected.lower() not in text:
            fail(f"{route} missing expected text: {expected}")
        passed += 1

    combined = "\n".join(client.get(route).get_data(as_text=True).lower() for route in ROUTES if not route.endswith(".json"))
    for phrase in UNSAFE_PHRASES:
        if phrase in combined:
            fail(f"unsafe phrase found: {phrase}")
        passed += 1

    scene_json = client.get("/scene.json").get_json()
    if not scene_json or scene_json.get("build_label") != "SV2-57 · Final Scientific Audit and Proof Release":
        fail("scene.json missing SV2-57 final proof-release build label")
    passed += 1

    explorer = scene_json.get("reviewer_guided_exploration", {})
    required_explorer = {"contract_version", "pass_id", "data_state", "display_label", "families", "items", "links", "workflow", "interaction_policy", "claim_boundary"}
    if not required_explorer.issubset(explorer):
        fail("scene.json missing reviewer-guided exploration contract")
    passed += 1
    if explorer.get("pass_id") != "SV2-53" or explorer.get("data_state") != "reviewer_guided_exploration_ready":
        fail("reviewer-guided exploration state invalid")
    passed += 1
    family_ids = {family.get("id") for family in explorer.get("families", [])}
    if not {"observation", "terrain", "atmosphere", "interaction", "synthesis", "uncertainty"}.issubset(family_ids):
        fail("reviewer-guided exploration missing required evidence families")
    passed += 1
    if len(explorer.get("items", [])) < 12 or len(explorer.get("links", [])) < 10:
        fail("reviewer-guided exploration lacks sufficient review threads or relationships")
    passed += 1
    policy = explorer.get("interaction_policy", {})
    if not policy.get("uncertainty_always_available") or not policy.get("return_to_overview_required") or not policy.get("deep_routes_remain_available"):
        fail("reviewer-guided exploration guardrails missing")
    passed += 1
    if "does not add evidence" not in explorer.get("claim_boundary", "").lower():
        fail("reviewer-guided exploration missing scientific boundary")
    passed += 1
    if client.get("/reviewer-guided-evidence-exploration.json").get_json() != explorer:
        fail("reviewer-guided exploration route does not match scene contract")
    passed += 1

    disclosure = scene_json.get("progressive_disclosure", {})
    required_disclosure = {"contract_version", "pass_id", "data_state", "display_label", "default_level", "levels", "scene_policy", "navigation", "claim_boundary"}
    if not required_disclosure.issubset(disclosure):
        fail("scene.json missing progressive disclosure contract")
    passed += 1
    if disclosure.get("pass_id") != "SV2-54" or disclosure.get("data_state") != "progressive_disclosure_ready":
        fail("progressive disclosure state invalid")
    passed += 1
    level_ids = {level.get("id") for level in disclosure.get("levels", [])}
    if level_ids != {"overview", "context", "audit"}:
        fail("progressive disclosure levels invalid")
    passed += 1
    policy = disclosure.get("scene_policy", {})
    if policy.get("science_removed") or not policy.get("uncertainty_visible_in_overview") or not policy.get("deep_routes_preserved"):
        fail("progressive disclosure guardrails invalid")
    passed += 1
    if "changes visibility and reading order only" not in disclosure.get("claim_boundary", ""):
        fail("progressive disclosure missing scientific boundary")
    passed += 1
    if client.get("/progressive-disclosure.json").get_json() != disclosure:
        fail("progressive disclosure route does not match scene contract")
    passed += 1
    scene_html = client.get("/scene").get_data(as_text=True)
    if scene_html.count('data-disclosure-level=') != 3 or "Deep scientific audit" not in scene_html:
        fail("scene missing progressive disclosure controls")
    passed += 1
    if scene_html.count("scene-status-strip") != 1:
        fail("scene status hierarchy duplicated")
    passed += 1

    historical = scene_json.get("historical_weather", {})
    required_historical = {"contract_version", "pass_id", "provider", "source_type", "observation_timestamp", "data_state", "status", "selected_time_utc", "time_offset_minutes", "weather", "display_label", "scene_directive", "claim_boundary"}
    if not required_historical.issubset(historical):
        fail("scene.json missing historical weather contract")
    passed += 1
    if historical.get("pass_id") != "SV2-35" or historical.get("data_state") not in {"observation_time_unresolved", "observation_time_in_future", "historical_weather_cache", "provider_unavailable_no_historical_cache"}:
        fail("historical weather state invalid")
    passed += 1
    if historical.get("data_state") != "historical_weather_cache" and historical.get("weather") is not None:
        fail("historical weather invented values without retrieval")
    passed += 1
    if "not an on-site measurement" not in historical.get("claim_boundary", ""):
        fail("historical weather missing scientific boundary")
    passed += 1
    if client.get("/historical-weather.json").get_json() != historical:
        fail("historical weather route does not match scene contract")
    passed += 1


    stability = scene_json.get("atmospheric_stability", {})
    required_stability={"contract_version","pass_id","provider","source_type","observation_timestamp","data_state","status","selected_time_utc","time_offset_minutes","inputs","stability_class","confidence_band","confidence_score","screening_reasons","display_label","scene_directive","claim_boundary"}
    if not required_stability.issubset(stability): fail("scene.json missing atmospheric stability contract")
    passed += 1
    if stability.get("pass_id") != "SV2-35" or stability.get("data_state") not in {"observation_time_unresolved","observation_time_in_future","atmospheric_stability_screen","provider_unavailable_no_stability_cache"}: fail("atmospheric stability state invalid")
    passed += 1
    if stability.get("data_state") != "atmospheric_stability_screen" and (stability.get("inputs") is not None or stability.get("stability_class") != "unknown"): fail("atmospheric stability invented values without retrieval")
    passed += 1
    if stability.get("stability_class") not in {"stable","neutral","unstable","unknown"}: fail("atmospheric stability class invalid")
    passed += 1
    if not 0.0 <= float(stability.get("confidence_score",0.0)) <= 0.9: fail("atmospheric stability confidence outside bound")
    passed += 1
    if "not a measured turbulence profile" not in stability.get("claim_boundary",""): fail("atmospheric stability missing scientific boundary")
    passed += 1
    if client.get("/atmospheric-stability.json").get_json() != stability: fail("atmospheric stability route does not match scene contract")
    passed += 1


    boundary = scene_json.get("boundary_layer_depth", {})
    required_boundary={"contract_version","pass_id","provider","source_type","observation_timestamp","data_state","status","selected_time_utc","time_offset_minutes","boundary_layer_height_m","depth_band","confidence_band","confidence_score","display_label","scene_directive","claim_boundary"}
    if not required_boundary.issubset(boundary): fail("scene.json missing boundary-layer depth contract")
    passed += 1
    if boundary.get("pass_id") != "SV2-35" or boundary.get("data_state") not in {"observation_time_unresolved","observation_time_in_future","boundary_layer_depth_cache","provider_unavailable_no_boundary_layer_cache"}: fail("boundary-layer depth state invalid")
    passed += 1
    if boundary.get("data_state") != "boundary_layer_depth_cache" and boundary.get("boundary_layer_height_m") is not None: fail("boundary-layer depth invented value without retrieval")
    passed += 1
    if "not a measured mixing height" not in boundary.get("claim_boundary",""): fail("boundary-layer depth missing scientific boundary")
    passed += 1
    if client.get("/boundary-layer-depth.json").get_json() != boundary: fail("boundary-layer route does not match scene contract")
    passed += 1

    wind = scene_json.get("wind", {})
    required_wind = {"speed_mph", "from_degrees", "to_degrees", "timestamp", "provider", "data_state", "what_it_cannot_prove"}
    if not required_wind.issubset(wind):
        fail("scene.json missing wind contract fields")
    passed += 1
    if wind.get("data_state") not in {"live_current_conditions", "stale_cached_current_conditions", "default_vector_fallback"}:
        fail("wind data_state invalid")
    passed += 1
    if "not necessarily observation-time wind" not in wind.get("what_it_cannot_prove", ""):
        fail("wind missing observation-time boundary")
    passed += 1

    plume = scene_json.get("plume_visualization", {}).get("geometry", {})
    if plume.get("mode") != "map_registered_visual_reconstruction":
        fail("plume geometry mode missing")
    passed += 1

    behavior = scene_json.get("terrain_plume_behavior", {})
    required_behavior = {"mode", "data_state", "width_multiplier", "length_multiplier", "bend_degrees", "turbulence", "claim_boundary"}
    if not required_behavior.issubset(behavior):
        fail("scene.json missing terrain behavior contract")
    passed += 1
    if behavior.get("data_state") not in {"measured_terrain_applied", "neutral_pending_measured_terrain"}:
        fail("terrain behavior state invalid")
    passed += 1
    if abs(float(behavior.get("bend_degrees", 999))) > 12.0:
        fail("terrain visual bend exceeds safe cap")
    passed += 1

    flow = plume.get("flow_path", {})
    required_flow = {"mode", "data_state", "points", "max_lateral_shift_km", "terrain_response", "claim_boundary"}
    if not required_flow.issubset(flow):
        fail("scene.json missing terrain flow-path contract")
    passed += 1
    if len(flow.get("points", [])) != 11:
        fail("terrain flow path must contain 11 map-registered nodes")
    passed += 1
    if not 0 <= float(flow.get("max_lateral_shift_km", 99)) <= 1.35:
        fail("terrain flow lateral shift exceeds safe cap")
    passed += 1
    if "not atmospheric dispersion modeling" not in flow.get("claim_boundary", ""):
        fail("terrain flow path missing scientific boundary")
    passed += 1
    if len(plume.get("uncertainty_polygon", [])) < 22:
        fail("path-following uncertainty polygon missing")
    passed += 1

    expected = (float(wind.get("to_degrees", 0)) + float(behavior.get("bend_degrees", 0))) % 360
    actual = float(plume.get("wind_to_degrees", -999)) % 360
    if abs(((actual - expected + 180) % 360) - 180) > 0.2:
        fail("plume geometry does not follow wind plus bounded terrain behavior")
    passed += 1

    wind_json = client.get("/wind.json").get_json()
    if not wind_json or wind_json.get("provider") not in {"Open-Meteo", "Open-Meteo current wind connector"}:
        fail("wind.json missing provider")
    passed += 1

    terrain_json = client.get("/terrain.json").get_json()
    if not terrain_json or terrain_json.get("status") != "terrain_loader_sv2_12":
        fail("terrain contract regressed")
    passed += 1

    lighting = scene_json.get("terrain_lighting", {})
    required_lighting = {"mode", "data_state", "cells", "contours", "claim_boundary"}
    if not required_lighting.issubset(lighting):
        fail("scene.json missing terrain lighting contract")
    passed += 1
    if lighting.get("data_state") not in {"measured_terrain_lighting_applied", "neutral_pending_measured_terrain"}:
        fail("terrain lighting state invalid")
    passed += 1
    if lighting.get("data_state") == "measured_terrain_lighting_applied":
        if not 1 <= len(lighting.get("cells", [])) <= 16:
            fail("terrain lighting cell count invalid")
        if any(abs(float(cell.get("shade", 9))) > 1.0 for cell in lighting.get("cells", [])):
            fail("terrain lighting shade outside safe bounds")
    else:
        if lighting.get("cells") or lighting.get("contours"):
            fail("neutral terrain lighting fabricated geometry")
    passed += 1
    if "not a continuous dem" not in lighting.get("claim_boundary", "").lower():
        fail("terrain lighting missing sparse-sample boundary")
    passed += 1

    volume = scene_json.get("air_volume", {})
    required_volume = {"mode", "data_state", "core_opacity", "mid_opacity", "haze_opacity", "edge_falloff", "vertical_layer_count", "claim_boundary"}
    if not required_volume.issubset(volume):
        fail("scene.json missing air volume contract")
    passed += 1
    if not (0 < float(volume.get("haze_opacity", 0)) < float(volume.get("mid_opacity", 0)) < float(volume.get("core_opacity", 0)) <= 0.3):
        fail("air volume opacity layers are not safely ordered")
    passed += 1
    if int(volume.get("vertical_layer_count", 0)) != 3:
        fail("air volume must use three restrained visual layers")
    passed += 1
    if "do not represent measured methane concentration" not in volume.get("claim_boundary", ""):
        fail("air volume missing concentration boundary")
    passed += 1

    living = scene_json.get("living_wind", {})
    required_living = {"mode", "data_state", "cadence_multiplier", "spacing_multiplier", "sway_amplitude_px", "gust_cycle_seconds", "gust_strength", "terrain_wake_strength", "claim_boundary"}
    if not required_living.issubset(living):
        fail("scene.json missing living wind contract")
    passed += 1
    if not 0.55 <= float(living.get("cadence_multiplier", 0)) <= 1.75:
        fail("living wind cadence outside safe bounds")
    passed += 1
    if not 2.5 <= float(living.get("sway_amplitude_px", 0)) <= 13.0:
        fail("living wind sway outside safe bounds")
    passed += 1
    if not 0.04 <= float(living.get("gust_strength", 0)) <= 0.22:
        fail("living wind gust outside safe bounds")
    passed += 1
    if "not a measured turbulence field" not in living.get("claim_boundary", ""):
        fail("living wind missing turbulence boundary")
    passed += 1

    observation = scene_json.get("observation_contract", {})
    required_observation = {"contract_version", "pass_id", "observation_id", "provider", "product_type", "reported_time_utc", "coordinates", "source_url", "retrieved_at_utc", "geometry_status", "quantification_status", "confidence_status", "data_state", "missing_fields", "claim_boundary"}
    if not required_observation.issubset(observation):
        fail("scene.json missing observation evidence contract")
    passed += 1
    if observation.get("pass_id") != "SV2-35" or observation.get("data_state") not in {"manifest_loaded", "source_seed_manifest_incomplete"}:
        fail("observation contract state invalid")
    passed += 1
    if observation.get("source_url") is None and "source_url" not in observation.get("missing_fields", []):
        fail("missing source URL was not made explicit")
    passed += 1
    if "not itself a methane detection" not in observation.get("claim_boundary", ""):
        fail("observation contract missing detection boundary")
    passed += 1
    observation_json = client.get("/observation.json").get_json()
    if observation_json != observation:
        fail("observation route does not match scene contract")
    passed += 1

    citations = scene_json.get("citation_surface", {})
    required_citations = {"contract_version", "pass_id", "generated_at_utc", "entry_count", "traceable_entry_count", "status", "display_label", "entries", "claim_boundary"}
    if not required_citations.issubset(citations):
        fail("scene.json missing citation surface contract")
    passed += 1
    if citations.get("pass_id") != "SV2-35" or citations.get("status") != "citation_surface_active":
        fail("citation surface state invalid")
    passed += 1
    if citations.get("entry_count") != len(citations.get("entries", [])) or citations.get("entry_count", 0) < 6:
        fail("citation surface layer count invalid")
    passed += 1
    citation_fields = {"layer_id", "source", "source_type", "timestamp_utc", "retrieval_state", "status", "claim_class", "boundary"}
    if any(not citation_fields.issubset(item) for item in citations.get("entries", [])):
        fail("citation entry missing source/time/retrieval/boundary fields")
    passed += 1
    if "do not certify scientific conclusions" not in citations.get("claim_boundary", ""):
        fail("citation surface missing scientific boundary")
    passed += 1
    if client.get("/citations.json").get_json() != citations:
        fail("citation route does not match scene contract")
    passed += 1

    vocabulary = scene_json.get("evidence_vocabulary", {})
    required_vocabulary = {"contract_version", "pass_id", "status", "allowed_states", "definitions", "layer_count", "layers", "display_label", "claim_boundary"}
    if not required_vocabulary.issubset(vocabulary):
        fail("scene.json missing evidence-state vocabulary contract")
    passed += 1
    if vocabulary.get("pass_id") != "SV2-35" or vocabulary.get("status") != "controlled_vocabulary_active":
        fail("evidence-state vocabulary state invalid")
    passed += 1
    if set(vocabulary.get("allowed_states", [])) != set(vocabulary.get("definitions", {}).keys()):
        fail("evidence-state definitions and allowed states diverge")
    passed += 1
    if vocabulary.get("layer_count") != len(vocabulary.get("layers", [])) or vocabulary.get("layer_count", 0) < 10:
        fail("evidence-state layer count invalid")
    passed += 1
    if any(item.get("primary_state") not in vocabulary.get("allowed_states", []) for item in vocabulary.get("layers", [])):
        fail("layer uses an uncontrolled evidence state")
    passed += 1
    if client.get("/evidence-states.json").get_json() != vocabulary:
        fail("evidence-state route does not match scene contract")
    passed += 1

    missing = scene_json.get("missing_evidence", {})
    required_missing = {"contract_version", "pass_id", "status", "display_label", "present_count", "missing_count", "not_claimed_count", "completeness_ratio", "visual_strength", "downstream_break", "categories", "scene_directive", "claim_boundary"}
    if not required_missing.issubset(missing):
        fail("scene.json missing missing-evidence contract")
    passed += 1
    if missing.get("pass_id") != "SV2-35" or missing.get("status") != "missing_evidence_visible":
        fail("missing-evidence state invalid")
    passed += 1
    if missing.get("categories", {}).get("assumed") != []:
        fail("missing evidence contract contains silent assumptions")
    passed += 1
    if missing.get("missing_count", 0) < 5 or not 0.34 <= float(missing.get("visual_strength", 0)) <= 0.88:
        fail("missing evidence is not visibly reducing scene confidence")
    passed += 1
    if any(not item.get("visual_consequence") or not item.get("resolves_with") for item in missing.get("categories", {}).get("missing", [])):
        fail("missing evidence item lacks consequence or resolver")
    passed += 1
    if client.get("/missing-evidence.json").get_json() != missing:
        fail("missing-evidence route does not match scene contract")
    passed += 1

    geometry_adapter = scene_json.get("observation_geometry", {})
    required_geometry_adapter = {"contract_version", "pass_id", "adapter_status", "supported_payload_types", "supported_geometry_types", "observation_id", "source_geometry", "feature_count", "geometry_state", "display_label", "evidence_state", "validation_errors", "render_directive", "claim_boundary"}
    if not required_geometry_adapter.issubset(geometry_adapter):
        fail("scene.json missing observation geometry adapter contract")
    passed += 1
    if geometry_adapter.get("pass_id") != "SV2-35" or geometry_adapter.get("geometry_state") not in {"unavailable", "source_geometry_loaded", "invalid_rejected"}:
        fail("observation geometry adapter state invalid")
    passed += 1
    if geometry_adapter.get("geometry_state") == "unavailable" and geometry_adapter.get("source_geometry") is not None:
        fail("observation geometry adapter invented source geometry")
    passed += 1
    if client.get("/observation-geometry.json").get_json() != geometry_adapter:
        fail("observation geometry route does not match scene contract")
    passed += 1

    full_dem = scene_json.get("full_dem", {})
    required_dem = {"contract_version", "pass_id", "provider", "source_type", "bbox", "requested_grid", "approx_pixel_size_m", "data_state", "coverage_status", "coverage_ratio", "display_label", "claim_boundary"}
    if not required_dem.issubset(full_dem):
        fail("scene.json missing certified hillshade lane contract")
    passed += 1
    if full_dem.get("pass_id") != "SV2-35" or full_dem.get("data_state") not in {"continuous_dem_cache", "dem_loader_ready_cache_pending", "provider_unavailable_no_dem_cache"}:
        fail("certified hillshade lane state invalid")
    passed += 1
    if full_dem.get("data_state") != "continuous_dem_cache" and float(full_dem.get("coverage_ratio", 0)) != 0.0:
        fail("full DEM claims coverage without a valid raster cache")
    passed += 1
    if client.get("/dem.json").get_json() != full_dem:
        fail("DEM route does not match scene contract")
    passed += 1


    hillshade = scene_json.get("hillshade", {})
    required_hillshade = {"contract_version", "pass_id", "source_dem_sha256", "source_dem_provider", "source_dem_bbox", "illumination", "data_state", "coverage_status", "display_label", "claim_boundary"}
    if not required_hillshade.issubset(hillshade):
        fail("scene.json missing DEM-derived hillshade contract")
    passed += 1
    if hillshade.get("pass_id") != "SV2-35" or hillshade.get("data_state") not in {"dem_derived_hillshade_cache", "hillshade_ready_to_generate", "hillshade_unavailable_no_valid_dem", "hillshade_generation_failed"}:
        fail("hillshade state invalid")
    passed += 1
    illumination = hillshade.get("illumination", {})
    if illumination.get("azimuth_degrees") != 315.0 or illumination.get("altitude_degrees") != 45.0 or illumination.get("z_factor") != 1.0:
        fail("hillshade illumination contract changed")
    passed += 1
    if hillshade.get("data_state") == "dem_derived_hillshade_cache" and full_dem.get("data_state") != "continuous_dem_cache":
        fail("hillshade exists without a validated DEM")
    passed += 1
    if "not agency-certified" not in hillshade.get("claim_boundary", ""):
        fail("hillshade missing certification boundary")
    passed += 1
    if client.get("/hillshade.json").get_json() != hillshade:
        fail("hillshade route does not match scene contract")
    passed += 1

    derivatives = scene_json.get("slope_aspect", {})
    required_derivatives = {"contract_version", "pass_id", "source_dem_sha256", "source_dem_provider", "source_dem_bbox", "derivation", "data_state", "coverage_status", "display_label", "claim_boundary"}
    if not required_derivatives.issubset(derivatives):
        fail("scene.json missing slope/aspect contract")
    passed += 1
    if derivatives.get("pass_id") != "SV2-35" or derivatives.get("data_state") not in {"dem_derived_slope_aspect_cache", "slope_aspect_ready_to_generate", "slope_aspect_unavailable_no_valid_dem", "slope_aspect_generation_failed"}:
        fail("slope/aspect state invalid")
    passed += 1
    if derivatives.get("data_state") == "dem_derived_slope_aspect_cache" and full_dem.get("data_state") != "continuous_dem_cache":
        fail("slope/aspect exists without validated DEM")
    passed += 1
    if derivatives.get("derivation", {}).get("units") != "degrees":
        fail("slope/aspect units are not explicit")
    passed += 1
    if client.get("/slope-aspect.json").get_json() != derivatives:
        fail("slope/aspect route does not match scene contract")
    passed += 1


    landforms = scene_json.get("landforms", {})
    required_landforms={"contract_version","pass_id","source_dem_sha256","class_definitions","data_state","coverage_status","display_label","claim_boundary"}
    if not required_landforms.issubset(landforms): fail("scene.json missing landform contract")
    passed += 1
    if landforms.get("pass_id") != "SV2-35" or landforms.get("data_state") not in {"dem_derived_landform_cache","landforms_ready_to_generate","landforms_unavailable_no_valid_dem","landform_generation_failed"}: fail("landform state invalid")
    passed += 1
    if len(landforms.get("class_definitions",[])) < 10: fail("landform vocabulary incomplete")
    passed += 1
    if landforms.get("data_state")=="dem_derived_landform_cache" and full_dem.get("data_state")!="continuous_dem_cache": fail("landforms exist without validated DEM")
    passed += 1
    if client.get("/landforms.json").get_json() != landforms: fail("landform route does not match scene contract")
    passed += 1
    if "not field-surveyed geology" not in landforms.get("claim_boundary",""): fail("landform geological boundary missing")
    passed += 1

    terrain_confidence=scene_json.get("terrain_confidence",{})
    required_tc={"contract_version","pass_id","source_dem_sha256","data_state","overall_score","quality_grade","dimensions","claim_boundary"}
    if not required_tc.issubset(terrain_confidence): fail("scene.json missing terrain confidence contract")
    passed += 1
    if terrain_confidence.get("pass_id")!="SV2-35" or terrain_confidence.get("data_state") not in {"terrain_confidence_ready","terrain_confidence_ready_to_generate","terrain_confidence_unavailable_no_valid_dem","terrain_confidence_generation_failed"}: fail("terrain confidence state invalid")
    passed += 1
    if not 0.0 <= float(terrain_confidence.get("overall_score",0.0)) <= 1.0: fail("terrain confidence score out of bounds")
    passed += 1
    if client.get("/terrain-confidence.json").get_json()!=terrain_confidence: fail("terrain confidence route does not match scene contract")
    passed += 1
    if "does not validate methane" not in terrain_confidence.get("claim_boundary",""): fail("terrain confidence scientific boundary missing")
    passed += 1

    timing = scene_json.get("evidence_time", {})
    required_timing = {"mode", "data_state", "observation_time_label", "current_wind_time_label", "alignment_status", "display_label", "scene_directive", "claim_boundary"}
    if not required_timing.issubset(timing):
        fail("scene.json missing evidence-time alignment contract")
    passed += 1
    if timing.get("alignment_status") not in {"current_context_only", "not_event_time_wind"}:
        fail("evidence-time alignment falsely implies event-time weather")
    passed += 1
    if timing.get("data_state") == "event_time_wind_confirmed":
        fail("evidence-time contract falsely confirms event-time wind")
    passed += 1
    if "observation-time" not in timing.get("claim_boundary", "") and "event-time" not in timing.get("claim_boundary", ""):
        fail("evidence-time contract missing temporal boundary")
    passed += 1
    timing_json = client.get("/time-alignment.json").get_json()
    if timing_json != timing:
        fail("time-alignment route does not match scene contract")
    passed += 1

    evidence_json = client.get("/evidence.json").get_json()
    if not evidence_json or "wind_lane" not in evidence_json or "terrain_lane" not in evidence_json:
        fail("evidence packet missing wind or terrain lane")
    passed += 1

    self_test = client.get("/self-test.json").get_json()
    if not self_test or self_test.get("status") != "PASS" or self_test.get("failed") != 0:
        fail("internal self-test did not pass")
    passed += 1


    steering_conf=scene_json.get("terrain_steering_confidence",{})
    req_sc={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","confidence_statistics","uncertainty_statistics","contributors","downgrade_reasons","scene_directive","claim_boundary"}
    if not req_sc.issubset(steering_conf): fail("scene.json missing steering confidence contract")
    passed += 1
    if steering_conf.get("pass_id")!="SV2-35" or steering_conf.get("data_state") not in {"terrain_steering_confidence_cache","steering_confidence_unavailable_safe","steering_confidence_generation_failed"}: fail("steering confidence state invalid")
    passed += 1
    if steering_conf.get("data_state")=="terrain_steering_confidence_cache":
        if not 0<=float(steering_conf.get("confidence_statistics",{}).get("mean",-1))<=1: fail("steering confidence outside bounds")
        if not 0<=float(steering_conf.get("uncertainty_statistics",{}).get("mean",-1))<=1: fail("steering uncertainty outside bounds")
    passed += 1
    if "not confidence in methane presence" not in steering_conf.get("claim_boundary",""): fail("steering confidence boundary missing")
    passed += 1
    if client.get("/terrain-steering-confidence.json").get_json()!=steering_conf: fail("steering confidence route mismatch")
    passed += 1

    steering_volume=scene_json.get("steering_aware_air_volume",{})
    required_sv={"contract_version","pass_id","mode","data_state","display_label","steering_driver","modulation_strength","confidence_support","lateral_bias_px","curve_strength","channel_compression","uncertainty_expansion","claim_boundary"}
    if not required_sv.issubset(steering_volume): fail("steering-aware air volume contract incomplete")
    passed += 1
    if steering_volume.get("pass_id")!="SV2-35": fail("steering-aware air volume pass id invalid")
    passed += 1
    if not 0<=float(steering_volume.get("modulation_strength",-1))<=0.42: fail("steering volume modulation outside safe bounds")
    passed += 1
    if not 0.74<=float(steering_volume.get("channel_compression",0))<=1.18: fail("steering volume compression outside safe bounds")
    passed += 1
    if not 1<=float(steering_volume.get("uncertainty_expansion",0))<=1.32: fail("steering volume uncertainty expansion outside safe bounds")
    passed += 1
    if client.get("/steering-aware-air-volume.json").get_json()!=steering_volume: fail("steering-aware air volume route mismatch")
    passed += 1

    health = client.get("/health").get_json()
    if not health or health.get("status") != "ok" or health.get("pass_id") != "SV2-57":
        fail("health readiness contract did not pass")
    passed += 1

    run_local = (ROOT / "RUN_LOCAL.bat").read_text(encoding="utf-8", errors="ignore")
    launcher = (ROOT / "tools" / "launch_review.py").read_text(encoding="utf-8", errors="ignore")
    if 'cd /d "%~dp0"' not in run_local or 'cmd /k ""cd /d' in run_local.lower():
        fail("RUN_LOCAL.bat still contains unsafe Windows path quoting")
    passed += 1
    if "/health" not in launcher or "webbrowser.open_new_tab" not in launcher or "/scene" not in launcher or "OBSERVATION_URL" not in launcher or "CITATIONS_URL" not in launcher or "EVIDENCE_STATES_URL" not in launcher or "MISSING_EVIDENCE_URL" not in launcher or "OBSERVATION_GEOMETRY_URL" not in launcher or "DEM_URL" not in launcher or "DEM_REFRESH_URL" not in launcher or "HILLSHADE_URL" not in launcher or "HILLSHADE_REFRESH_URL" not in launcher or "SLOPE_ASPECT_URL" not in launcher or "SLOPE_ASPECT_REFRESH_URL" not in launcher or "LANDFORMS_REFRESH_URL" not in launcher or "TERRAIN_CONFIDENCE_REFRESH_URL" not in launcher or "MULTI_LEVEL_WIND_REFRESH_URL" not in launcher or "BOUNDARY_LAYER_DEPTH_REFRESH_URL" not in launcher or "GUST_VARIABILITY_REFRESH_URL" not in launcher:
        fail("readiness-gated browser launcher or terrain derivative contract missing")
    passed += 1
    interaction=scene_json.get("terrain_atmosphere_index",{})
    required_interaction={"contract_version","pass_id","layer","evidence_state","data_state","status","interaction_index","interaction_band","confidence_score","confidence_band","components","temporal_basis","display_label","scene_directive","claim_boundary"}
    if not required_interaction.issubset(interaction): fail("terrain-atmosphere interaction contract incomplete")
    if interaction.get("pass_id")!="SV2-35": fail("terrain-atmosphere interaction pass id invalid")
    if interaction.get("data_state") not in {"terrain_atmosphere_interaction_index","interaction_index_unavailable_safe"}: fail("terrain-atmosphere interaction state invalid")
    steering=scene_json.get("terrain_steering_field",{})
    if steering.get("pass_id")!="SV2-35": fail("terrain steering field pass id invalid")
    if steering.get("data_state") not in {"terrain_steering_field_cache","steering_field_unavailable_safe","steering_field_generation_failed"}: fail("terrain steering field state invalid")
    if steering.get("data_state")=="terrain_steering_field_cache":
        ratios=steering.get("field_statistics",{}).get("response_ratios",{})
        if set(ratios)!={"alignment","opposition","shelter","channeling","lateral_deflection"}: fail("terrain steering field categories invalid")
        if not 0 <= float(steering.get("field_statistics",{}).get("mean_strength",-1)) <= 1: fail("terrain steering field strength unbounded")
        ok("terrain steering field contract valid")
    if interaction.get("interaction_index") is not None and not 0 <= float(interaction.get("interaction_index")) <= 100: fail("terrain-atmosphere index outside bounds")
    if "not a plume-dispersion model" not in interaction.get("claim_boundary",""): fail("terrain-atmosphere claim boundary missing")

    if "TERRAIN_REFRESH_URL" not in launcher or "prepare_terrain" not in launcher or "neutral terrain mode" not in launcher or "prepare_slope_aspect" not in launcher or "prepare_landforms" not in launcher or "prepare_terrain_confidence" not in launcher or "prepare_multi_level_wind" not in launcher or "prepare_boundary_layer_depth" not in launcher or "prepare_gust_variability" not in launcher:
        fail("automatic terrain readiness launcher contract missing")
    if "landforms = prepare_landforms()" not in launcher or "LANDFORMS READY" not in launcher or "confidence = prepare_terrain_confidence()" not in launcher or "TERRAIN CONFIDENCE READY" not in launcher or "multi = prepare_multi_level_wind()" not in launcher or "MULTI-LEVEL WIND READY" not in launcher or "boundary = prepare_boundary_layer_depth()" not in launcher or "BOUNDARY-LAYER DEPTH READY" not in launcher or "variability = prepare_gust_variability()" not in launcher or "GUST VARIABILITY READY" not in launcher:
        fail("launcher does not execute terrain preparation chain")
    passed += 1
    if "PROJECT HEALTH SUMMARY" not in launcher or "READY FOR HUMAN REVIEW" not in launcher:
        fail("compact project health summary missing")
    passed += 1
    if "targets = [SCENE_URL]" not in launcher or "targets.extend" in launcher:
        fail("verification launcher opens more than the primary scene")
    passed += 1

    fixture={"hourly":{"time":["2026-01-01T11:00","2026-01-01T12:00","2026-01-01T13:00"],"wind_speed_10m":[4,7,9],"wind_direction_10m":[180,225,250],"wind_gusts_10m":[6,11,13],"temperature_2m":[10,11,12],"surface_pressure":[1012,1011,1010]}}
    from engine.historical_weather import historical_weather_context
    with tempfile.TemporaryDirectory() as d:
        fp=Path(d)/"fixture.json"; fp.write_text(json.dumps(fixture),encoding="utf-8")
        old_fixture=os.environ.get("AW_HISTORICAL_WEATHER_FIXTURE"); old_time=os.environ.get("AW_OBSERVATION_TIME_UTC")
        os.environ["AW_HISTORICAL_WEATHER_FIXTURE"]=str(fp); os.environ["AW_OBSERVATION_TIME_UTC"]="2026-01-01T12:20:00Z"
        try:
            ready=historical_weather_context({"reported_time_utc":"2026-01-01T12:20:00Z"},34.2,-119.1,refresh=True)
        finally:
            if old_fixture is None: os.environ.pop("AW_HISTORICAL_WEATHER_FIXTURE",None)
            else: os.environ["AW_HISTORICAL_WEATHER_FIXTURE"]=old_fixture
            if old_time is None: os.environ.pop("AW_OBSERVATION_TIME_UTC",None)
            else: os.environ["AW_OBSERVATION_TIME_UTC"]=old_time
        if ready.get("data_state") != "historical_weather_cache" or ready.get("selected_time_utc") != "2026-01-01T12:00:00Z" or ready.get("time_offset_minutes") != -20.0:
            fail("historical weather fixture selection failed")
        passed += 1
        if ready.get("weather",{}).get("wind_speed_10m_mph") != 7.0:
            fail("historical weather fixture values not preserved")
        passed += 1

    multi_fixture={"hourly":{"time":["2026-01-01T11:00","2026-01-01T12:00","2026-01-01T13:00"],"wind_speed_10m":[4,7,9],"wind_direction_10m":[180,225,250],"wind_speed_100m":[8,12,15],"wind_direction_100m":[195,255,275]}}
    from engine.multi_level_wind import multi_level_wind_context
    with tempfile.TemporaryDirectory() as d:
        fp=Path(d)/"multi_fixture.json"; fp.write_text(json.dumps(multi_fixture),encoding="utf-8")
        old_fixture=os.environ.get("AW_MULTI_LEVEL_WIND_FIXTURE"); old_time=os.environ.get("AW_OBSERVATION_TIME_UTC")
        os.environ["AW_MULTI_LEVEL_WIND_FIXTURE"]=str(fp); os.environ["AW_OBSERVATION_TIME_UTC"]="2026-01-01T12:20:00Z"
        try:
            multi=multi_level_wind_context({"reported_time_utc":"2026-01-01T12:20:00Z"},34.2,-119.1,refresh=True)
        finally:
            if old_fixture is None: os.environ.pop("AW_MULTI_LEVEL_WIND_FIXTURE",None)
            else: os.environ["AW_MULTI_LEVEL_WIND_FIXTURE"]=old_fixture
            if old_time is None: os.environ.pop("AW_OBSERVATION_TIME_UTC",None)
            else: os.environ["AW_OBSERVATION_TIME_UTC"]=old_time
        if multi.get("data_state")!="multi_level_wind_cache" or multi.get("selected_time_utc")!="2026-01-01T12:00:00Z" or multi.get("time_offset_minutes")!=-20.0:
            fail("multi-level wind fixture selection failed")
        passed += 1
        if [x.get("height_m") for x in multi.get("levels",[])] != [10,100]:
            fail("multi-level wind heights not preserved")
        passed += 1
        if multi.get("shear",{}).get("direction_change_degrees") != 30.0:
            fail("multi-level wind contrast incorrect")
        passed += 1

    if client.get("/multi-level-wind").status_code != 200 or client.get("/multi-level-wind.json").status_code != 200:
        fail("multi-level wind routes unavailable")
    passed += 1


    boundary_fixture={"hourly":{"time":["2026-01-01T11:00","2026-01-01T12:00","2026-01-01T13:00"],"boundary_layer_height":[180,640,1120]}}
    from engine.boundary_layer_depth import boundary_layer_depth_context
    with tempfile.TemporaryDirectory() as d:
        fp=Path(d)/"boundary_fixture.json"; fp.write_text(json.dumps(boundary_fixture),encoding="utf-8")
        old_fixture=os.environ.get("AW_BOUNDARY_LAYER_FIXTURE"); old_time=os.environ.get("AW_OBSERVATION_TIME_UTC")
        os.environ["AW_BOUNDARY_LAYER_FIXTURE"]=str(fp); os.environ["AW_OBSERVATION_TIME_UTC"]="2026-01-01T12:20:00Z"
        try:
            boundary_ready=boundary_layer_depth_context({"reported_time_utc":"2026-01-01T12:20:00Z"},34.2,-119.1,refresh=True)
        finally:
            if old_fixture is None: os.environ.pop("AW_BOUNDARY_LAYER_FIXTURE",None)
            else: os.environ["AW_BOUNDARY_LAYER_FIXTURE"]=old_fixture
            if old_time is None: os.environ.pop("AW_OBSERVATION_TIME_UTC",None)
            else: os.environ["AW_OBSERVATION_TIME_UTC"]=old_time
        if boundary_ready.get("data_state")!="boundary_layer_depth_cache" or boundary_ready.get("boundary_layer_height_m")!=640.0 or boundary_ready.get("time_offset_minutes")!=-20.0:
            fail("boundary-layer fixture selection failed")
        passed += 1
        if boundary_ready.get("depth_band")!="moderate": fail("boundary-layer depth band incorrect")
        passed += 1
    if client.get("/boundary-layer-depth").status_code != 200 or client.get("/boundary-layer-depth.json").status_code != 200:
        fail("boundary-layer routes unavailable")
    passed += 1

    variability=scene_json.get("gust_variability",{})
    required_variability={"contract_version","pass_id","provider","source_type","observation_timestamp","data_state","status","selected_time_utc","time_offset_minutes","window_start_utc","window_end_utc","expected_hour_count","available_hour_count","window_complete","samples","metrics","variability_class","confidence_band","confidence_score","display_label","scene_directive","claim_boundary"}
    if not required_variability.issubset(variability): fail("scene.json missing gust variability contract")
    passed += 1
    if variability.get("pass_id")!="SV2-35" or variability.get("data_state") not in {"observation_time_unresolved","observation_time_in_future","gust_variability_window_cache","provider_unavailable_no_variability_cache"}: fail("gust variability state invalid")
    passed += 1
    if variability.get("data_state")!="gust_variability_window_cache" and (variability.get("samples")!=[] or variability.get("metrics") is not None): fail("gust variability invented values without retrieval")
    passed += 1
    if "not measured turbulence" not in variability.get("claim_boundary",""): fail("gust variability scientific boundary missing")
    passed += 1
    if client.get("/gust-variability.json").get_json()!=variability: fail("gust variability route does not match scene contract")
    passed += 1

    variability_fixture={"hourly":{"time":["2026-01-01T10:00","2026-01-01T11:00","2026-01-01T12:00","2026-01-01T13:00","2026-01-01T14:00"],"wind_speed_10m":[4,6,8,11,7],"wind_direction_10m":[210,220,230,260,250],"wind_gusts_10m":[7,10,15,20,12]}}
    from engine.gust_variability import gust_variability_context
    with tempfile.TemporaryDirectory() as d:
        fp=Path(d)/"gust_fixture.json"; fp.write_text(json.dumps(variability_fixture),encoding="utf-8")
        old_fixture=os.environ.get("AW_GUST_VARIABILITY_FIXTURE"); old_time=os.environ.get("AW_OBSERVATION_TIME_UTC")
        os.environ["AW_GUST_VARIABILITY_FIXTURE"]=str(fp); os.environ["AW_OBSERVATION_TIME_UTC"]="2026-01-01T12:20:00Z"
        try:
            variability_ready=gust_variability_context({"reported_time_utc":"2026-01-01T12:20:00Z"},34.2,-119.1,refresh=True)
        finally:
            if old_fixture is None: os.environ.pop("AW_GUST_VARIABILITY_FIXTURE",None)
            else: os.environ["AW_GUST_VARIABILITY_FIXTURE"]=old_fixture
            if old_time is None: os.environ.pop("AW_OBSERVATION_TIME_UTC",None)
            else: os.environ["AW_OBSERVATION_TIME_UTC"]=old_time
        if variability_ready.get("data_state")!="gust_variability_window_cache" or variability_ready.get("available_hour_count")!=5 or variability_ready.get("time_offset_minutes")!=-20.0:
            fail("gust variability fixture selection failed")
        passed += 1
        metrics=variability_ready.get("metrics") or {}
        if metrics.get("window_speed_range_mph")!=7.0 or metrics.get("window_max_gust_mph")!=20.0:
            fail("gust variability metrics incorrect")
        passed += 1
        if variability_ready.get("variability_class") not in {"moderate","high"}: fail("gust variability class not responsive")
        passed += 1

    advection=scene_json.get("terrain_responsive_particle_advection",{})
    required_advection={"contract_version","pass_id","mode","evidence_state","data_state","status","display_label","dominant_driver","advection_authority","coherence","crosswind_drift_px","channel_speed_multiplier","shelter_speed_multiplier","opposition_drag","deflection_oscillation_px","uncertainty_jitter_px","response_bands","scene_directive","claim_boundary"}
    if not required_advection.issubset(advection): fail("scene.json missing particle-advection contract")
    passed += 1
    if advection.get("pass_id")!="SV2-35" or advection.get("data_state") not in {"terrain_responsive_particle_advection_ready","particle_advection_unavailable_safe"}: fail("particle-advection state invalid")
    passed += 1
    if advection.get("data_state")=="terrain_responsive_particle_advection_ready":
        if not 0<=float(advection.get("advection_authority",-1))<=0.46: fail("particle-advection authority outside bound")
        passed += 1
        if not 0<=float(advection.get("coherence",-1))<=1: fail("particle-advection coherence outside bound")
        passed += 1
        if len(advection.get("response_bands",[]))!=3: fail("particle-advection response bands missing")
        passed += 1
    if "not measured methane parcels" not in advection.get("claim_boundary",""): fail("particle-advection scientific boundary missing")
    passed += 1
    if client.get("/terrain-responsive-particle-advection.json").get_json()!=advection: fail("particle-advection route does not match scene contract")
    passed += 1
    plume_js=(ROOT/"static/js/plume_canvas.js").read_text(encoding="utf-8")
    for token in ["particleAdvection","bandEnvelope","channelSpeedMultiplier","uncertaintyJitter"]:
        if token not in plume_js: fail(f"particle-advection renderer token missing: {token}")
        passed += 1

    ridge=scene_json.get("ridge_spillover_shelter",{})
    required_ridge={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","spillover_statistics","shelter_statistics","confidence_support","particle_directives","scene_directive","claim_boundary"}
    if not required_ridge.issubset(ridge): fail("scene.json missing ridge spillover / lee shelter contract")
    passed += 1
    if ridge.get("pass_id")!="SV2-35" or ridge.get("data_state") not in {"ridge_spillover_shelter_cache","ridge_spillover_shelter_unavailable_safe","ridge_spillover_shelter_generation_failed"}: fail("ridge spillover / lee shelter state invalid")
    passed += 1
    directives=ridge.get("particle_directives") or {}
    if not (0<=float(directives.get("spillover_lift_px",0))<=8 and 0.82<=float(directives.get("lee_slowdown_multiplier",1))<=1 and 1<=float(directives.get("lee_spread_multiplier",1))<=1.18): fail("ridge/lee particle directives outside bounds")
    passed += 1
    if "not measured airflow" not in ridge.get("claim_boundary",""): fail("ridge/lee scientific boundary missing")
    passed += 1
    if client.get("/ridge-spillover-lee-shelter").status_code != 200 or client.get("/ridge-spillover-lee-shelter.json").status_code != 200: fail("ridge/lee routes unavailable")
    passed += 1
    map_js=(ROOT/"static/js/map_scene.js").read_text(encoding="utf-8")
    plume_js=(ROOT/"static/js/plume_canvas.js").read_text(encoding="utf-8")
    for token in ["awRidgeSpilloverPane","awLeeShelterPane","ridge-spillover-image","lee-side-shelter-image"]:
        if token not in map_js: fail(f"ridge/lee map renderer token missing: {token}")
        passed += 1
    for token in ["ridgeLeeReady","spilloverLift","leeSlowdown","leeSpread"]:
        if token not in plume_js: fail(f"ridge/lee particle renderer token missing: {token}")
        passed += 1

    canyon=scene_json.get("canyon_channeling",{})
    required_canyon={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","channeling_statistics","drainage_statistics","confidence_support","particle_directives","scene_directive","claim_boundary"}
    if not required_canyon.issubset(canyon): fail("scene.json missing canyon-channeling contract")
    passed += 1
    if canyon.get("pass_id")!="SV2-35" or canyon.get("data_state") not in {"canyon_channeling_drainage_cache","canyon_channeling_unavailable_safe","canyon_channeling_generation_failed"}: fail("canyon-channeling state invalid")
    passed += 1
    if "not measured airflow" not in canyon.get("claim_boundary",""): fail("canyon-channeling scientific boundary missing")
    passed += 1
    if client.get("/canyon-channeling-drainage-alignment").status_code!=200 or client.get("/canyon-channeling-drainage-alignment.json").status_code!=200: fail("canyon-channeling routes unavailable")
    passed += 1
    for token in ["awCanyonPane","awDrainagePane","canyon-channeling-image","drainage-alignment-image"]:
        if token not in map_js: fail(f"canyon map renderer token missing: {token}")
        passed += 1
    for token in ["canyonReady","canyonPullPx","drainageCoherence"]:
        if token not in plume_js: fail(f"canyon particle renderer token missing: {token}")
        passed += 1


    saddle=scene_json.get("saddle_gap_acceleration",{})
    required_saddle={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","saddle_statistics","gap_statistics","confidence_support","particle_directives","scene_directive","claim_boundary"}
    if not required_saddle.issubset(saddle): fail("scene.json missing saddle-gap contract")
    passed += 1
    if saddle.get("pass_id")!="SV2-36" or saddle.get("data_state") not in {"saddle_transfer_gap_cache","saddle_gap_unavailable_safe","saddle_gap_generation_failed"}: fail("saddle-gap state invalid")
    passed += 1
    if "not measured airflow" not in saddle.get("claim_boundary",""): fail("saddle-gap scientific boundary missing")
    passed += 1
    for token in ["awSaddlePane","awGapPane","saddle-transfer-image","gap-acceleration-image"]:
        if token not in map_js: fail(f"saddle-gap map renderer token missing: {token}")
        passed += 1
    for token in ["saddleGapReady","saddleTransferPx","gapCoherence"]:
        if token not in plume_js: fail(f"saddle-gap particle renderer token missing: {token}")
        passed += 1

    basin=scene_json.get("basin_retention_cold_air_pooling",{})
    required_basin={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","basin_statistics","cold_pooling_statistics","confidence_support","particle_directives","atmospheric_basis","scene_directive","claim_boundary"}
    if not required_basin.issubset(basin): fail("scene.json missing basin-retention contract")
    passed += 1
    if basin.get("pass_id")!="SV2-37" or basin.get("data_state") not in {"basin_retention_cold_air_pooling_cache","basin_retention_unavailable_safe","basin_retention_generation_failed"}: fail("basin-retention state invalid")
    passed += 1
    if "not measured temperature inversions" not in basin.get("claim_boundary",""): fail("basin-retention scientific boundary missing")
    passed += 1
    if client.get("/basin-retention-cold-air-pooling").status_code!=200 or client.get("/basin-retention-cold-air-pooling.json").status_code!=200: fail("basin-retention routes unavailable")
    passed += 1
    for token in ["awBasinRetentionPane","awColdPoolingPane","basin-retention-image","cold-air-pooling-image"]:
        if token not in map_js: fail(f"basin-retention map renderer token missing: {token}")
        passed += 1
    for token in ["basinRetentionReady","basinSlowdown","poolingBroadening","basinSettlingPx"]:
        if token not in plume_js: fail(f"basin-retention particle renderer token missing: {token}")
        passed += 1


    convergence=scene_json.get("terrain_convergence_accumulation",{})
    required_convergence={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","convergence_statistics","accumulation_statistics","confidence_support","particle_directives","atmospheric_basis","scene_directive","claim_boundary"}
    if not required_convergence.issubset(convergence): fail("scene.json missing terrain-convergence contract")
    passed += 1
    if convergence.get("pass_id")!="SV2-38" or convergence.get("data_state") not in {"terrain_convergence_accumulation_cache","terrain_convergence_unavailable_safe","terrain_convergence_generation_failed"}: fail("terrain-convergence state invalid")
    passed += 1
    if "not measured airflow convergence" not in convergence.get("claim_boundary",""): fail("terrain-convergence scientific boundary missing")
    passed += 1
    if client.get("/terrain-convergence-focused-accumulation").status_code!=200 or client.get("/terrain-convergence-focused-accumulation.json").status_code!=200: fail("terrain-convergence routes unavailable")
    passed += 1
    for token in ["awTerrainConvergencePane","awFocusedAccumulationPane","terrain-convergence-image","terrain-focused-accumulation-image"]:
        if token not in map_js: fail(f"terrain-convergence map renderer token missing: {token}")
        passed += 1
    for token in ["terrainConvergenceReady","convergencePullPx","focusSlowdown","focusBroadening"]:
        if token not in plume_js: fail(f"terrain-convergence particle renderer token missing: {token}")
        passed += 1


    divergence=scene_json.get("terrain_divergence_dispersion",{})
    required_divergence={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","divergence_statistics","dispersion_statistics","confidence_support","particle_directives","atmospheric_basis","scene_directive","claim_boundary"}
    if not required_divergence.issubset(divergence): fail("scene.json missing terrain-divergence contract")
    passed += 1
    if divergence.get("pass_id")!="SV2-39" or divergence.get("data_state") not in {"terrain_divergence_dispersion_cache","terrain_divergence_unavailable_safe","terrain_divergence_generation_failed"}: fail("terrain-divergence state invalid")
    passed += 1
    if "not measured airflow divergence" not in divergence.get("claim_boundary",""): fail("terrain-divergence scientific boundary missing")
    passed += 1
    if client.get("/terrain-divergence-dispersion").status_code!=200 or client.get("/terrain-divergence-dispersion.json").status_code!=200: fail("terrain-divergence routes unavailable")
    passed += 1
    for token in ["awTerrainDivergencePane","awTerrainDispersionPane","terrain-divergence-image","terrain-dispersion-image"]:
        if token not in map_js: fail(f"terrain-divergence map renderer token missing: {token}")
        passed += 1
    for token in ["terrainDivergenceReady","divergenceSpreadPx","dispersionBroadening","dispersionSpeed"]:
        if token not in plume_js: fail(f"terrain-divergence particle renderer token missing: {token}")
        passed += 1

    transitions=scene_json.get("terrain_transition_regimes",{})
    req={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","transition_statistics","boundary_statistics","regime_mix","confidence_support","particle_directives","atmospheric_basis","scene_directive","claim_boundary"}
    if not req.issubset(transitions): fail("scene.json missing terrain transition contract")
    passed += 1
    if transitions.get("pass_id")!="SV2-40": fail("terrain transition pass mismatch")
    passed += 1
    if "not measured atmospheric fronts" not in transitions.get("claim_boundary",""): fail("terrain transition boundary missing")
    passed += 1


    regime=scene_json.get("terrain_regime_confidence",{})
    req_regime={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","confidence_statistics","ambiguity_statistics","regime_support","downgrade_reasons","visual_directives","scene_directive","claim_boundary"}
    if not req_regime.issubset(regime): fail("scene.json missing terrain-regime confidence contract")
    passed += 1
    if regime.get("pass_id")!="SV2-41": fail("terrain-regime confidence pass mismatch")
    passed += 1
    if "Neither layer is confidence in methane presence" not in regime.get("claim_boundary",""): fail("terrain-regime confidence boundary missing")
    passed += 1
    if client.get("/terrain-regime-confidence").status_code!=200 or client.get("/terrain-regime-confidence.json").status_code!=200: fail("terrain-regime confidence routes unavailable")
    passed += 1
    for token in ["awRegimeConfidencePane","awBoundaryAmbiguityPane","terrain-regime-confidence-image","terrain-boundary-ambiguity-image"]:
        if token not in map_js: fail(f"terrain-regime confidence map token missing: {token}")
        passed += 1

    print(f"Passed: {passed}")
    print("Failed: 0")
    print(f"Total: {passed}")





if __name__ == "__main__":
    main()

# SV2-43 package markers
assert "integrated_terrain_response_v1" in (ROOT/"engine/integrated_terrain_response.py").read_text()
assert "integrated_response_authority_v1" in (ROOT/"engine/integrated_response_authority.py").read_text()
assert "awIntegratedResponsePane" in (ROOT/"static/js/map_scene.js").read_text()

assert "integrated_motion_orchestration_v1" in (ROOT/"engine/integrated_motion_orchestration.py").read_text()
assert "orchestratedSpeed" in (ROOT/"static/js/plume_canvas.js").read_text()
assert "contradictory_effects_allowed" in (ROOT/"engine/integrated_motion_orchestration.py").read_text()

assert "integrated_air_volume_orchestration_v1" in (ROOT/"engine/integrated_air_volume_orchestration.py").read_text()
assert "orchestratedVolumeWidth" in (ROOT/"static/js/plume_canvas.js").read_text()
assert "contradictory_shapes_allowed" in (ROOT/"engine/integrated_air_volume_orchestration.py").read_text()

assert "evidence_guided_focus_depth_v1" in (ROOT/"engine/evidence_guided_focus_depth.py").read_text()
assert "aw-evidence-focus-depth" in (ROOT/"static/js/map_scene.js").read_text()
assert "depth_of_field_simulation" in (ROOT/"engine/evidence_guided_focus_depth.py").read_text()

assert "atmospheric_light_legibility_v1" in (ROOT/"engine/atmospheric_light_legibility.py").read_text()
assert "aw-atmospheric-light-veil" in (ROOT/"static/js/map_scene.js").read_text()
assert "optical_density_simulation" in (ROOT/"engine/atmospheric_light_legibility.py").read_text()
assert "concentration_shading" in (ROOT/"engine/atmospheric_light_legibility.py").read_text()

assert "evidence_visual_hierarchy_v1" in (ROOT/"engine/evidence_visual_hierarchy.py").read_text()
assert "aw-evidence-hierarchy-veil" in (ROOT/"static/js/map_scene.js").read_text()
assert "color_as_concentration" in (ROOT/"engine/evidence_visual_hierarchy.py").read_text()
assert (ROOT/"MORNING_RESUME_CHECKPOINT_SV2_50.md").exists()


assert "scientific_annotation_choreography_v1" in (ROOT/"engine/scientific_annotation_choreography.py").read_text()
assert "scientific_storytelling_timeline_v1" in (ROOT/"engine/scientific_storytelling_timeline.py").read_text()
assert "aw-scientific-annotations" in (ROOT/"static/js/map_scene.js").read_text()
assert "aw-scientific-timeline" in (ROOT/"static/js/map_scene.js").read_text()
assert (ROOT/"MORNING_RESUME_CHECKPOINT_SV2_52.md").exists()

# SV2-55 package markers
assert "scientific_synthesis_decision_surface_v1" in (ROOT/"engine/scientific_synthesis_decision_surface.py").read_text()
assert (ROOT/"templates/scientific_synthesis_decision_surface.html").exists()
assert (ROOT/"CONTINUATION_CHECKPOINT_SV2_55.md").exists()

# SV2-57 package markers
assert "final_release_audit_v1" in (ROOT/"engine/final_release_audit.py").read_text()
assert (ROOT/"templates/release_proof.html").exists()
assert (ROOT/"RUN_VERIFY_SV2_57.bat").exists()
assert (ROOT/"RECOVERY_AND_CONTINUATION_SV2_57.md").exists()
