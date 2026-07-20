from __future__ import annotations

from pathlib import Path

from engine.scene_config import default_scene_config

ROOT = Path(__file__).resolve().parents[1]
PASS_ID = "SV2-57"

REQUIRED_FILES = [
    "app.py", "engine/wind_loader.py", "engine/terrain_loader.py",
    "engine/terrain_plume_behavior.py", "engine/terrain_flow_path.py", "engine/terrain_lighting.py", "engine/air_volume.py", "engine/living_wind.py",
    "engine/pass_checks.py", "engine/evidence_time.py", "engine/observation_contract.py", "engine/citation_surface.py", "engine/evidence_vocabulary.py", "engine/missing_evidence.py", "engine/observation_geometry.py", "engine/full_dem.py", "engine/hillshade.py", "engine/slope_aspect.py", "engine/landform_classification.py", "engine/terrain_confidence.py", "engine/historical_weather.py", "engine/multi_level_wind.py", "engine/atmospheric_stability.py", "engine/boundary_layer_depth.py", "engine/gust_variability.py", "engine/terrain_atmosphere_index.py", "engine/terrain_steering_field.py", "engine/terrain_steering_confidence.py", "engine/steering_aware_air_volume.py", "engine/terrain_responsive_particle_advection.py", "engine/ridge_spillover_shelter.py", "engine/canyon_channeling.py", "engine/saddle_gap_acceleration.py", "engine/basin_retention_cold_air_pooling.py", "engine/terrain_convergence_accumulation.py", "engine/terrain_divergence_dispersion.py", "engine/terrain_transition_regimes.py", "engine/terrain_regime_confidence.py", "engine/integrated_terrain_response.py", "engine/integrated_response_authority.py", "engine/evidence_guided_focus_depth.py", "engine/atmospheric_light_legibility.py", "engine/progressive_disclosure.py", "engine/final_release_audit.py", "templates/scene.html", "templates/self_test.html", "templates/time_alignment.html", "templates/observation.html", "templates/citations.html", "templates/evidence_states.html", "templates/missing_evidence.html", "templates/observation_geometry.html", "templates/dem.html", "templates/hillshade.html", "templates/slope_aspect.html", "templates/landforms.html", "templates/terrain_confidence.html", "templates/historical_weather.html", "templates/multi_level_wind.html", "templates/atmospheric_stability.html", "templates/boundary_layer_depth.html", "templates/gust_variability.html", "templates/terrain_atmosphere_index.html", "templates/terrain_steering_field.html", "templates/terrain_steering_confidence.html", "templates/terrain_responsive_particle_advection.html", "templates/ridge_spillover_shelter.html", "templates/canyon_channeling.html", "templates/saddle_gap_acceleration.html", "templates/basin_retention_cold_air_pooling.html", "templates/terrain_convergence_accumulation.html", "templates/terrain_divergence_dispersion.html", "templates/terrain_transition_regimes.html", "templates/terrain_regime_confidence.html", "templates/integrated_terrain_response.html", "templates/integrated_response_authority.html", "templates/evidence_guided_focus_depth.html", "templates/atmospheric_light_legibility.html", "templates/progressive_disclosure.html", "templates/release_proof.html",
    "static/js/plume_canvas.js", "static/js/map_scene.js", "tests/smoke_test.py",
    "RUN_LOCAL.bat", "RUN_VERIFY_SV2_26.bat", "RUN_VERIFY_SV2_54.bat", "RUN_VERIFY_SV2_57.bat", "tools/launch_review.py",
    "RUN_SMOKE_TESTS.bat", "docs/TERRAIN_DRIVEN_FLOW_SV2_9.md", "docs/ELEVATION_LIGHTING_LOCAL_RELIEF_SV2_10.md", "docs/AIR_VOLUME_SV2_11.md", "docs/LIVING_WIND_SV2_12.md", "docs/EVIDENCE_TIME_ALIGNMENT_SV2_13.md", "docs/OBSERVATION_EVIDENCE_CONTRACT_SV2_14.md", "docs/CITATION_SURFACE_SV2_15.md", "docs/EVIDENCE_STATE_VOCABULARY_SV2_16.md", "docs/MISSING_EVIDENCE_VISUALIZATION_SV2_17.md", "docs/OBSERVATION_GEOMETRY_ADAPTER_SV2_18.md", "docs/FULL_DEM_ACQUISITION_SV2_19.md",
]

FORBIDDEN_CLAIMS = [
    "detected methane leak", "confirmed methane leak", "responsible facility",
    "illegal emission", "certified emissions confirmed", "enforcement-ready",
]


def run_internal_checks() -> dict:
    checks: list[dict] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    for rel in REQUIRED_FILES:
        record(f"file:{rel}", (ROOT / rel).exists(), "present" if (ROOT / rel).exists() else "missing")

    try:
        scene = default_scene_config()
        record("scene:build", True, scene.get("build_label", "scene built"))
    except Exception as exc:
        scene = {}
        record("scene:build", False, str(exc)[:180])

    wind = scene.get("wind", {})
    record("wind:contract", all(key in wind for key in ["speed_mph", "from_degrees", "to_degrees", "timestamp", "provider"]), wind.get("data_state", "missing"))
    record("wind:direction-range", 0 <= float(wind.get("from_degrees", -1)) < 360 and 0 <= float(wind.get("to_degrees", -1)) < 360, f"from {wind.get('from_degrees')} to {wind.get('to_degrees')}")
    record("wind:observation-time-boundary", "not necessarily observation-time wind" in wind.get("what_it_cannot_prove", ""), "boundary present")

    terrain = scene.get("terrain", {})
    record("terrain:contract", terrain.get("status") == "terrain_loader_sv2_12", terrain.get("status", "missing"))
    record("terrain:measured-or-neutral", terrain.get("data_state") in {"measured_sample_cache", "loader_ready_cache_pending", "provider_unavailable_no_measured_cache"}, terrain.get("data_state", "missing"))
    full_dem = scene.get("full_dem", {})
    record("dem:contract", all(key in full_dem for key in ["contract_version", "provider", "bbox", "requested_grid", "data_state", "coverage_status", "display_label", "claim_boundary"]), full_dem.get("data_state", "missing"))
    record("dem:honest-state", full_dem.get("data_state") in {"continuous_dem_cache", "dem_loader_ready_cache_pending", "provider_unavailable_no_dem_cache"}, full_dem.get("data_state", "missing"))
    record("dem:no-fabricated-coverage", full_dem.get("data_state") == "continuous_dem_cache" or float(full_dem.get("coverage_ratio", 0)) == 0.0, str(full_dem.get("coverage_ratio")))

    hillshade = scene.get("hillshade", {})
    record("hillshade:contract", all(key in hillshade for key in ["contract_version", "pass_id", "source_dem_sha256", "illumination", "data_state", "coverage_status", "display_label", "claim_boundary"]), hillshade.get("data_state", "missing"))
    record("hillshade:honest-state", hillshade.get("data_state") in {"dem_derived_hillshade_cache", "hillshade_ready_to_generate", "hillshade_unavailable_no_valid_dem", "hillshade_generation_failed"}, hillshade.get("data_state", "missing"))
    record("hillshade:fixed-illumination", hillshade.get("illumination", {}).get("azimuth_degrees") == 315.0 and hillshade.get("illumination", {}).get("altitude_degrees") == 45.0, str(hillshade.get("illumination")))
    record("hillshade:dem-required", hillshade.get("data_state") != "dem_derived_hillshade_cache" or full_dem.get("data_state") == "continuous_dem_cache", "no hillshade without valid DEM")
    record("hillshade:boundary", "not agency-certified" in hillshade.get("claim_boundary", ""), "certification boundary present")


    derivatives = scene.get("slope_aspect", {})
    record("slope-aspect:contract", all(key in derivatives for key in ["contract_version", "pass_id", "source_dem_sha256", "derivation", "data_state", "coverage_status", "display_label", "claim_boundary"]), derivatives.get("data_state", "missing"))
    record("slope-aspect:honest-state", derivatives.get("data_state") in {"dem_derived_slope_aspect_cache", "slope_aspect_ready_to_generate", "slope_aspect_unavailable_no_valid_dem", "slope_aspect_generation_failed"}, derivatives.get("data_state", "missing"))
    record("slope-aspect:dem-required", derivatives.get("data_state") != "dem_derived_slope_aspect_cache" or full_dem.get("data_state") == "continuous_dem_cache", "no derivatives without valid DEM")
    record("slope-aspect:units", derivatives.get("derivation", {}).get("units") == "degrees", str(derivatives.get("derivation")))
    record("slope-aspect:boundary", "not atmospheric transport" in derivatives.get("claim_boundary", "").lower(), "terrain-only boundary present")

    landforms = scene.get("landforms", {})
    record("landforms:contract", all(key in landforms for key in ["contract_version", "pass_id", "source_dem_sha256", "class_definitions", "data_state", "coverage_status", "display_label", "claim_boundary"]), landforms.get("data_state", "missing"))
    record("landforms:honest-state", landforms.get("data_state") in {"dem_derived_landform_cache", "landforms_ready_to_generate", "landforms_unavailable_no_valid_dem", "landform_generation_failed"}, landforms.get("data_state", "missing"))
    record("landforms:dem-required", landforms.get("data_state") != "dem_derived_landform_cache" or full_dem.get("data_state") == "continuous_dem_cache", "no classes without valid DEM")
    record("landforms:ready-after-valid-dem", full_dem.get("data_state") != "continuous_dem_cache" or landforms.get("data_state") == "dem_derived_landform_cache", landforms.get("display_label", "missing"))
    record("landforms:vocabulary", len(landforms.get("class_definitions", [])) >= 10, f"{len(landforms.get('class_definitions', []))} classes")
    record("landforms:boundary", "not field-surveyed geology" in landforms.get("claim_boundary", ""), "geomorphometric boundary present")
    terrain_confidence = scene.get("terrain_confidence", {})
    record("terrain-confidence:contract", all(k in terrain_confidence for k in ["contract_version","pass_id","source_dem_sha256","data_state","overall_score","quality_grade","dimensions","claim_boundary"]), terrain_confidence.get("data_state","missing"))
    record("terrain-confidence:honest-state", terrain_confidence.get("data_state") in {"terrain_confidence_ready","terrain_confidence_ready_to_generate","terrain_confidence_unavailable_no_valid_dem","terrain_confidence_generation_failed"}, terrain_confidence.get("data_state","missing"))
    record("terrain-confidence:ready-after-valid-dem", full_dem.get("data_state") != "continuous_dem_cache" or terrain_confidence.get("data_state") == "terrain_confidence_ready", terrain_confidence.get("display_label","missing"))
    record("terrain-confidence:bounded", 0.0 <= float(terrain_confidence.get("overall_score",0.0)) <= 1.0, str(terrain_confidence.get("overall_score")))
    record("terrain-confidence:dimensions", terrain_confidence.get("data_state") != "terrain_confidence_ready" or len(terrain_confidence.get("dimensions",{})) >= 8, f"{len(terrain_confidence.get('dimensions',{}))} dimensions")
    record("terrain-confidence:boundary", "does not validate methane" in terrain_confidence.get("claim_boundary",""), "scientific boundary present")

    behavior = scene.get("terrain_plume_behavior", {})
    record("terrain-behavior:contract", all(key in behavior for key in ["mode", "data_state", "width_multiplier", "length_multiplier", "bend_degrees", "turbulence", "claim_boundary"]), behavior.get("data_state", "missing"))
    record("terrain-behavior:safe-bend", abs(float(behavior.get("bend_degrees", 999))) <= 12.0, str(behavior.get("bend_degrees")))
    record("terrain-behavior:safe-width", 0.6 <= float(behavior.get("width_multiplier", 0)) <= 1.3, str(behavior.get("width_multiplier")))

    geometry = scene.get("plume_visualization", {}).get("geometry", {})
    flow = geometry.get("flow_path", {})
    points = flow.get("points", [])
    record("plume:map-registered", geometry.get("mode") == "map_registered_visual_reconstruction", geometry.get("mode", "missing"))
    record("flow:contract", all(key in flow for key in ["mode", "data_state", "points", "max_lateral_shift_km", "terrain_response", "claim_boundary"]), flow.get("mode", "missing"))
    record("flow:node-count", len(points) == 11, f"{len(points)} nodes")
    record("flow:safe-shift", 0 <= float(flow.get("max_lateral_shift_km", 99)) <= 1.35, f"{flow.get('max_lateral_shift_km')} km")
    record("flow:measured-or-neutral", flow.get("data_state") in {"measured_terrain_applied", "neutral_pending_measured_terrain"}, flow.get("data_state", "missing"))
    record("flow:boundary", "not atmospheric dispersion modeling" in flow.get("claim_boundary", ""), "boundary present")
    record("flow:path-following-uncertainty", len(geometry.get("uncertainty_polygon", [])) >= 22, f"{len(geometry.get('uncertainty_polygon', []))} polygon points")

    launch = (ROOT / "RUN_LOCAL.bat").read_text(encoding="utf-8", errors="ignore") if (ROOT / "RUN_LOCAL.bat").exists() else ""
    verify = (ROOT / "RUN_VERIFY_SV2_21.bat").read_text(encoding="utf-8", errors="ignore") if (ROOT / "RUN_VERIFY_SV2_21.bat").exists() else ""
    launch_py = (ROOT / "tools" / "launch_review.py").read_text(encoding="utf-8", errors="ignore") if (ROOT / "tools" / "launch_review.py").exists() else ""
    record("launcher:folder-safe", 'cd /d "%~dp0"' in launch, "launcher uses its own extracted folder")
    record("launcher:opens-scene", "SCENE_URL" in launch_py and "/scene" in launch_py, "scene URL wired")
    record("launcher:waits-for-health", "/health" in launch_py and "wait_for_server" in launch_py, "readiness polling wired")
    record("launcher:verify-mode", "--verify" in verify, "verification mode wired")
    record("launcher:single-page-open", "targets = [SCENE_URL]" in launch_py and "targets.extend" not in launch_py, "only the primary scene opens")
    record("launcher:opens-observation", "OBSERVATION_URL" in launch_py and "/observation" in launch_py, "observation review URL wired")
    record("launcher:health-summary", "PROJECT HEALTH SUMMARY" in launch_py, "compact health summary wired")
    record("terrain:auto-refresh-wired", "TERRAIN_REFRESH_URL" in launch_py and "prepare_terrain" in launch_py, "terrain prepared before scene")

    lighting = scene.get("terrain_lighting", {})
    record("relief:contract", all(key in lighting for key in ["mode", "data_state", "cells", "contours", "claim_boundary"]), lighting.get("data_state", "missing"))
    if lighting.get("data_state") == "measured_terrain_lighting_applied":
        record("relief:cells", 1 <= len(lighting.get("cells", [])) <= 16, f"{len(lighting.get('cells', []))} cells")
        record("relief:bounded-opacity-input", all(-1.0 <= float(cell.get("shade", 9)) <= 1.0 for cell in lighting.get("cells", [])), "shade bounded")
        record("relief:measured-range", float(lighting.get("local_relief_m", 0)) >= 0, str(lighting.get("local_relief_m")))
    else:
        record("relief:neutral-safe", lighting.get("cells") == [] and lighting.get("contours") == [], "no fabricated relief")


    volume = scene.get("air_volume", {})
    record("air-volume:contract", all(key in volume for key in ["mode", "data_state", "core_opacity", "mid_opacity", "haze_opacity", "edge_falloff", "vertical_layer_count", "claim_boundary"]), volume.get("data_state", "missing"))
    record("air-volume:layer-count", int(volume.get("vertical_layer_count", 0)) == 3, str(volume.get("vertical_layer_count")))
    record("air-volume:opacity-order", 0 < float(volume.get("haze_opacity", 0)) < float(volume.get("mid_opacity", 0)) < float(volume.get("core_opacity", 0)) <= 0.3, "haze < middle < core")
    record("air-volume:boundary", "do not represent measured methane concentration" in volume.get("claim_boundary", ""), "concentration boundary present")

    living = scene.get("living_wind", {})
    record("living-wind:contract", all(key in living for key in ["mode", "data_state", "cadence_multiplier", "spacing_multiplier", "sway_amplitude_px", "gust_cycle_seconds", "gust_strength", "terrain_wake_strength", "claim_boundary"]), living.get("mode", "missing"))
    record("living-wind:bounded-cadence", 0.55 <= float(living.get("cadence_multiplier", 0)) <= 1.75, str(living.get("cadence_multiplier")))
    record("living-wind:bounded-sway", 2.5 <= float(living.get("sway_amplitude_px", 0)) <= 13.0, str(living.get("sway_amplitude_px")))
    record("living-wind:bounded-gust", 0.04 <= float(living.get("gust_strength", 0)) <= 0.22, str(living.get("gust_strength")))
    record("living-wind:boundary", "not a measured turbulence field" in living.get("claim_boundary", ""), "turbulence boundary present")


    observation = scene.get("observation_contract", {})
    required_observation = ["contract_version", "pass_id", "observation_id", "provider", "product_type", "reported_time_utc", "coordinates", "source_url", "retrieved_at_utc", "geometry_status", "quantification_status", "confidence_status", "data_state", "missing_fields", "claim_boundary"]
    record("observation:contract", all(key in observation for key in required_observation), observation.get("contract_version", "missing"))
    record("observation:pass-id", observation.get("pass_id") == "SV2-35", observation.get("pass_id", "missing"))
    record("observation:state", observation.get("data_state") in {"manifest_loaded", "source_seed_manifest_incomplete"}, observation.get("data_state", "missing"))
    record("observation:coordinates", all(key in observation.get("coordinates", {}) for key in ["lat", "lon", "status"]), str(observation.get("coordinates", {})))
    record("observation:no-fabricated-source", observation.get("source_url") is not None or "source_url" in observation.get("missing_fields", []), "source URL present or explicitly missing")
    record("observation:boundary", "not itself a methane detection" in observation.get("claim_boundary", ""), "provenance boundary present")

    citations = scene.get("citation_surface", {})
    required_citations = ["contract_version", "pass_id", "generated_at_utc", "entry_count", "traceable_entry_count", "status", "display_label", "entries", "claim_boundary"]
    record("citations:contract", all(key in citations for key in required_citations), citations.get("contract_version", "missing"))
    record("citations:pass-id", citations.get("pass_id") == "SV2-35", citations.get("pass_id", "missing"))
    record("citations:layer-count", citations.get("entry_count") == len(citations.get("entries", [])) and citations.get("entry_count", 0) >= 6, citations.get("display_label", "missing"))
    record("citations:fields", all(all(key in item for key in ["layer_id", "source", "source_type", "timestamp_utc", "retrieval_state", "status", "claim_class", "boundary"]) for item in citations.get("entries", [])), "source/time/retrieval/boundary fields present")
    record("citations:boundary", "do not certify scientific conclusions" in citations.get("claim_boundary", ""), "citation boundary present")

    vocabulary = scene.get("evidence_vocabulary", {})
    required_vocabulary = ["contract_version", "pass_id", "status", "allowed_states", "definitions", "layer_count", "layers", "display_label", "claim_boundary"]
    record("vocabulary:contract", all(key in vocabulary for key in required_vocabulary), vocabulary.get("contract_version", "missing"))
    record("vocabulary:pass-id", vocabulary.get("pass_id") == "SV2-35", vocabulary.get("pass_id", "missing"))
    record("vocabulary:controlled-states", set(vocabulary.get("allowed_states", [])) == set(vocabulary.get("definitions", {}).keys()), f"{len(vocabulary.get('allowed_states', []))} states")
    record("vocabulary:one-primary-state", all(item.get("primary_state") in vocabulary.get("allowed_states", []) for item in vocabulary.get("layers", [])), "all layers use allowed state")
    record("vocabulary:layer-fields", all(all(key in item for key in ["layer_id", "primary_state", "state", "purpose", "represents", "does_not_represent"]) for item in vocabulary.get("layers", [])), "layer evidence metadata present")
    record("vocabulary:explicit-boundaries", any(item.get("primary_state") == "not_modeled" for item in vocabulary.get("layers", [])) and any(item.get("primary_state") == "not_claimed" for item in vocabulary.get("layers", [])), "not modeled and not claimed present")

    missing = scene.get("missing_evidence", {})
    required_missing = ["contract_version", "pass_id", "status", "display_label", "present_count", "missing_count", "not_claimed_count", "completeness_ratio", "visual_strength", "downstream_break", "categories", "scene_directive", "claim_boundary"]
    record("missing-evidence:contract", all(key in missing for key in required_missing), missing.get("status", "missing"))
    record("missing-evidence:pass-id", missing.get("pass_id") == "SV2-35", missing.get("pass_id", "missing"))
    record("missing-evidence:no-assumptions", missing.get("categories", {}).get("assumed") == [], "no silent assumptions")
    record("missing-evidence:visible-gaps", missing.get("missing_count", 0) >= 5 and 0.34 <= float(missing.get("visual_strength", 0)) <= 0.88, missing.get("display_label", "missing"))
    record("missing-evidence:resolvable", all(item.get("visual_consequence") and item.get("resolves_with") for item in missing.get("categories", {}).get("missing", [])), "every gap has consequence and resolver")
    record("missing-evidence:boundary", "does not estimate missing values" in missing.get("claim_boundary", ""), "no fabrication boundary present")

    geometry_adapter = scene.get("observation_geometry", {})
    record("geometry-adapter:contract", all(key in geometry_adapter for key in ["contract_version", "pass_id", "adapter_status", "supported_payload_types", "supported_geometry_types", "geometry_state", "display_label", "claim_boundary"]), geometry_adapter.get("adapter_status", "missing"))
    record("geometry-adapter:default-honesty", geometry_adapter.get("geometry_state") in {"unavailable", "source_geometry_loaded", "invalid_rejected"}, geometry_adapter.get("geometry_state", "missing"))
    record("geometry-adapter:no-invention", geometry_adapter.get("geometry_state") != "unavailable" or geometry_adapter.get("source_geometry") is None, "no geometry invented")
    record("geometry-adapter:separate-layer", "separate" in geometry_adapter.get("render_directive", "").lower() or geometry_adapter.get("geometry_state") == "unavailable", geometry_adapter.get("render_directive", "missing"))

    timing = scene.get("evidence_time", {})
    record("evidence-time:contract", all(key in timing for key in ["mode", "data_state", "observation_time_label", "current_wind_time_label", "alignment_status", "display_label", "scene_directive", "claim_boundary"]), timing.get("mode", "missing"))
    record("evidence-time:current-context-only", timing.get("alignment_status") in {"current_context_only", "not_event_time_wind"}, timing.get("alignment_status", "missing"))
    record("evidence-time:no-false-alignment", timing.get("data_state") != "event_time_wind_confirmed", timing.get("data_state", "missing"))
    record("evidence-time:boundary", "cannot reconstruct observation-time transport" in timing.get("claim_boundary", "") or "event-time weather" in timing.get("claim_boundary", ""), "temporal boundary present")

    interaction = scene.get("terrain_atmosphere_index", {})
    required_interaction={"contract_version","pass_id","layer","evidence_state","data_state","status","interaction_index","interaction_band","confidence_score","confidence_band","components","temporal_basis","display_label","scene_directive","claim_boundary"}
    record("terrain-atmosphere:contract", required_interaction.issubset(interaction), interaction.get("display_label","missing"))
    record("terrain-atmosphere:pass", interaction.get("pass_id")=="SV2-35", interaction.get("pass_id","missing"))
    record("terrain-atmosphere:state", interaction.get("data_state") in {"terrain_atmosphere_interaction_index","interaction_index_unavailable_safe"}, interaction.get("data_state","missing"))
    record("terrain-atmosphere:bounded", interaction.get("interaction_index") is None or 0 <= float(interaction.get("interaction_index")) <= 100, str(interaction.get("interaction_index")))
    record("terrain-atmosphere:components", interaction.get("data_state")!="terrain_atmosphere_interaction_index" or all(k in interaction.get("components",{}) for k in ["terrain_steering","terrain_shelter","channeling_potential","ridge_exposure","vertical_mixing_opportunity"]), "five components present")
    record("terrain-atmosphere:boundary", "not a plume-dispersion model" in interaction.get("claim_boundary",""), interaction.get("claim_boundary","missing"))

    steering = scene.get("terrain_steering_field", {})
    required_steering={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","field_statistics","scene_directive","claim_boundary"}
    record("steering-field:contract", required_steering.issubset(steering), steering.get("display_label","missing"))
    record("steering-field:pass", steering.get("pass_id")=="SV2-35", steering.get("pass_id","missing"))
    record("steering-field:state", steering.get("data_state") in {"terrain_steering_field_cache","steering_field_unavailable_safe","steering_field_generation_failed"}, steering.get("data_state","missing"))
    field_required = scene.get("full_dem",{}).get("data_state")=="continuous_dem_cache" and scene.get("wind",{}).get("data_state") in {"live_current_conditions","stale_cached_current_conditions","default_vector_fallback"}
    record("steering-field:required-when-supported", not field_required or steering.get("data_state")=="terrain_steering_field_cache", steering.get("data_state","missing"))
    record("steering-field:bounded", steering.get("data_state")!="terrain_steering_field_cache" or 0 <= float(steering.get("field_statistics",{}).get("mean_strength",-1)) <= 1, str(steering.get("field_statistics",{}).get("mean_strength")))
    record("steering-field:categories", steering.get("data_state")!="terrain_steering_field_cache" or set(steering.get("field_statistics",{}).get("response_ratios",{}))=={"alignment","opposition","shelter","channeling","lateral_deflection"}, "five spatial responses")
    record("steering-field:boundary", "not CFD" in steering.get("claim_boundary",""), steering.get("claim_boundary","missing"))
    steering_conf=scene.get("terrain_steering_confidence",{})
    req_sc={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","confidence_statistics","uncertainty_statistics","contributors","downgrade_reasons","scene_directive","claim_boundary"}
    record("steering-confidence:contract",req_sc.issubset(steering_conf),steering_conf.get("display_label","missing"))
    record("steering-confidence:pass",steering_conf.get("pass_id")=="SV2-35",steering_conf.get("pass_id","missing"))
    record("steering-confidence:state",steering_conf.get("data_state") in {"terrain_steering_confidence_cache","steering_confidence_unavailable_safe","steering_confidence_generation_failed"},steering_conf.get("data_state","missing"))
    sc_required=steering.get("data_state")=="terrain_steering_field_cache" and (scene.get("terrain_confidence") or {}).get("data_state")=="terrain_confidence_ready"
    record("steering-confidence:required-when-supported",not sc_required or steering_conf.get("data_state")=="terrain_steering_confidence_cache",steering_conf.get("data_state","missing"))
    record("steering-confidence:bounded",steering_conf.get("data_state")!="terrain_steering_confidence_cache" or 0<=float(steering_conf.get("confidence_statistics",{}).get("mean",-1))<=1,str(steering_conf.get("confidence_statistics",{}).get("mean")))
    record("steering-confidence:uncertainty-bounded",steering_conf.get("data_state")!="terrain_steering_confidence_cache" or 0<=float(steering_conf.get("uncertainty_statistics",{}).get("mean",-1))<=1,str(steering_conf.get("uncertainty_statistics",{}).get("mean")))
    record("steering-confidence:boundary","not confidence in methane presence" in steering_conf.get("claim_boundary",""),steering_conf.get("claim_boundary","missing"))
    volume=scene.get("steering_aware_air_volume") or scene.get("air_volume",{})
    req_volume={"contract_version","pass_id","mode","data_state","display_label","steering_driver","modulation_strength","confidence_support","lateral_bias_px","curve_strength","channel_compression","uncertainty_expansion","scene_directive","claim_boundary"}
    record("steering-volume:contract",req_volume.issubset(volume),volume.get("display_label","missing"))
    record("steering-volume:pass",volume.get("pass_id")=="SV2-35",volume.get("pass_id","missing"))
    record("steering-volume:state",volume.get("data_state") in {"steering_aware_air_volume_ready","steering_aware_volume_unavailable_safe"},volume.get("data_state","missing"))
    record("steering-volume:bounded",0<=float(volume.get("modulation_strength",0))<=0.42 and 0.74<=float(volume.get("channel_compression",1))<=1.18 and 1<=float(volume.get("uncertainty_expansion",1))<=1.32,"bounded visual modulation")
    record("steering-volume:boundary","not represent measured methane concentration" in volume.get("claim_boundary",""),volume.get("claim_boundary","missing"))

    integrated_volume=scene.get("integrated_air_volume_orchestration",{})
    req_iv={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","winning_regime","volume_authority","orchestration","conflict_controls","scene_directive","claim_boundary"}
    record("integrated-volume:contract",req_iv.issubset(integrated_volume),integrated_volume.get("display_label","missing"))
    record("integrated-volume:pass",integrated_volume.get("pass_id")=="SV2-45",integrated_volume.get("pass_id","missing"))
    record("integrated-volume:state",integrated_volume.get("data_state") in {"integrated_air_volume_orchestration_ready","integrated_air_volume_unavailable_safe"},integrated_volume.get("data_state","missing"))
    vo=integrated_volume.get("orchestration") or {}
    record("integrated-volume:bounded",0.84<=float(vo.get("width_multiplier",1))<=1.18 and 0.90<=float(vo.get("vertical_thickness_multiplier",1))<=1.12 and 0.88<=float(vo.get("downstream_diffusion_multiplier",1))<=1.20,"bounded volume orchestration")
    record("integrated-volume:no-contradictory-shapes",(integrated_volume.get("conflict_controls") or {}).get("contradictory_shapes_allowed") is False,"single coordinated volume profile")
    record("integrated-volume:boundary","not measured methane geometry" in integrated_volume.get("claim_boundary",""),integrated_volume.get("claim_boundary","missing"))

    release = scene.get("final_release_audit", {})
    required_release={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","checks","guardrails","launch_checklist","claim_boundary"}
    record("release:contract", required_release.issubset(release), release.get("display_label", "missing"))
    record("release:pass", release.get("pass_id") == "SV2-57", release.get("pass_id", "missing"))
    record("release:gates", release.get("passed_count") == release.get("total_count"), f"{release.get('passed_count')}/{release.get('total_count')}")
    record("release:guardrails", len(release.get("guardrails") or []) >= 5, "five non-negotiable boundaries")
    record("release:boundary", "does not validate methane detection" in release.get("claim_boundary", ""), release.get("claim_boundary", "missing"))

    text_paths = [ROOT / "templates" / "scene.html", ROOT / "engine" / "source_registry.py", ROOT / "engine" / "evidence_packet.py"]
    combined = "\n".join(path.read_text(encoding="utf-8").lower() for path in text_paths if path.exists())
    for index, phrase in enumerate(FORBIDDEN_CLAIMS, start=1):
        record(f"guardrail:unsafe-claim-{index}", phrase not in combined, "absent" if phrase not in combined else "unsafe phrase found")


    historical = scene.get("historical_weather", {})
    required_historical={"contract_version","pass_id","provider","source_type","observation_timestamp","data_state","status","selected_time_utc","time_offset_minutes","weather","display_label","scene_directive","claim_boundary"}
    record("historical-weather:contract", required_historical.issubset(historical), historical.get("display_label","missing"))
    record("historical-weather:pass", historical.get("pass_id")=="SV2-35", historical.get("pass_id","missing"))
    record("historical-weather:state", historical.get("data_state") in {"observation_time_unresolved","observation_time_in_future","historical_weather_cache","provider_unavailable_no_historical_cache"}, historical.get("data_state","missing"))
    record("historical-weather:no-invention", historical.get("data_state")=="historical_weather_cache" or historical.get("weather") is None, "weather absent unless retrieved")
    record("historical-weather:boundary", "not an on-site measurement" in historical.get("claim_boundary",""), historical.get("claim_boundary","missing"))

    multi = scene.get("multi_level_wind", {})
    required_multi={"contract_version","pass_id","provider","source_type","observation_timestamp","requested_levels_m","data_state","status","selected_time_utc","time_offset_minutes","levels","shear","display_label","scene_directive","claim_boundary"}
    record("multi-level-wind:contract", required_multi.issubset(multi), multi.get("display_label","missing"))
    record("multi-level-wind:pass", multi.get("pass_id")=="SV2-35", multi.get("pass_id","missing"))
    record("multi-level-wind:state", multi.get("data_state") in {"observation_time_unresolved","observation_time_in_future","multi_level_wind_cache","provider_unavailable_no_multi_level_cache"}, multi.get("data_state","missing"))
    record("multi-level-wind:no-invention", multi.get("data_state")=="multi_level_wind_cache" or multi.get("levels")==[], "levels absent unless retrieved")
    record("multi-level-wind:bounded-levels", multi.get("data_state")!="multi_level_wind_cache" or [x.get("height_m") for x in multi.get("levels",[])]==[10,100], str(multi.get("requested_levels_m")))
    record("multi-level-wind:boundary", "not an observed vertical profile" in multi.get("claim_boundary",""), multi.get("claim_boundary","missing"))

    stability = scene.get("atmospheric_stability", {})
    required_stability={"contract_version","pass_id","provider","source_type","observation_timestamp","data_state","status","selected_time_utc","time_offset_minutes","inputs","stability_class","confidence_band","confidence_score","screening_reasons","display_label","scene_directive","claim_boundary"}
    record("atmospheric-stability:contract", required_stability.issubset(stability), stability.get("display_label","missing"))
    record("atmospheric-stability:pass", stability.get("pass_id")=="SV2-35", stability.get("pass_id","missing"))
    record("atmospheric-stability:state", stability.get("data_state") in {"observation_time_unresolved","observation_time_in_future","atmospheric_stability_screen","provider_unavailable_no_stability_cache"}, stability.get("data_state","missing"))
    record("atmospheric-stability:no-invention", stability.get("data_state")=="atmospheric_stability_screen" or (stability.get("inputs") is None and stability.get("stability_class")=="unknown"), stability.get("stability_class","missing"))
    record("atmospheric-stability:bounded-class", stability.get("stability_class") in {"stable","neutral","unstable","unknown"}, stability.get("stability_class","missing"))
    record("atmospheric-stability:bounded-confidence", 0.0 <= float(stability.get("confidence_score",0.0)) <= 0.9, str(stability.get("confidence_score")))
    record("atmospheric-stability:boundary", "not a measured turbulence profile" in stability.get("claim_boundary",""), stability.get("claim_boundary","missing"))


    boundary = scene.get("boundary_layer_depth", {})
    required_boundary={"contract_version","pass_id","provider","source_type","observation_timestamp","data_state","status","selected_time_utc","time_offset_minutes","boundary_layer_height_m","depth_band","confidence_band","confidence_score","display_label","scene_directive","claim_boundary"}
    record("boundary-layer:contract", required_boundary.issubset(boundary), boundary.get("display_label","missing"))
    record("boundary-layer:pass", boundary.get("pass_id")=="SV2-35", boundary.get("pass_id","missing"))
    record("boundary-layer:state", boundary.get("data_state") in {"observation_time_unresolved","observation_time_in_future","boundary_layer_depth_cache","provider_unavailable_no_boundary_layer_cache"}, boundary.get("data_state","missing"))
    record("boundary-layer:no-invention", boundary.get("data_state")=="boundary_layer_depth_cache" or boundary.get("boundary_layer_height_m") is None, str(boundary.get("boundary_layer_height_m")))
    record("boundary-layer:bounded", boundary.get("boundary_layer_height_m") is None or 0 <= float(boundary.get("boundary_layer_height_m")) <= 10000, str(boundary.get("boundary_layer_height_m")))
    record("boundary-layer:boundary", "not a measured mixing height" in boundary.get("claim_boundary",""), boundary.get("claim_boundary","missing"))
    variability = scene.get("gust_variability", {})
    required_variability={"contract_version","pass_id","provider","source_type","observation_timestamp","data_state","status","selected_time_utc","time_offset_minutes","window_start_utc","window_end_utc","expected_hour_count","available_hour_count","window_complete","samples","metrics","variability_class","confidence_band","confidence_score","display_label","scene_directive","claim_boundary"}
    record("gust-variability:contract", required_variability.issubset(variability), variability.get("display_label","missing"))
    record("gust-variability:pass", variability.get("pass_id")=="SV2-35", variability.get("pass_id","missing"))
    record("gust-variability:state", variability.get("data_state") in {"observation_time_unresolved","observation_time_in_future","gust_variability_window_cache","provider_unavailable_no_variability_cache"}, variability.get("data_state","missing"))
    record("gust-variability:no-invention", variability.get("data_state")=="gust_variability_window_cache" or (variability.get("samples")==[] and variability.get("metrics") is None), variability.get("data_state","missing"))
    record("gust-variability:bounded-class", variability.get("variability_class") in {"low","moderate","high","unknown"}, variability.get("variability_class","missing"))
    record("gust-variability:window-count", 0 <= int(variability.get("available_hour_count",0)) <= int(variability.get("expected_hour_count",5)), str(variability.get("available_hour_count")))
    record("gust-variability:boundary", "not measured turbulence" in variability.get("claim_boundary",""), variability.get("claim_boundary","missing"))


    ridge = scene.get("ridge_spillover_shelter", {})
    required_ridge = {"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","spillover_statistics","shelter_statistics","confidence_support","particle_directives","scene_directive","claim_boundary"}
    record("ridge-lee:contract", required_ridge.issubset(ridge), ridge.get("display_label","missing"))
    record("ridge-lee:pass", ridge.get("pass_id")=="SV2-35", ridge.get("pass_id","missing"))
    record("ridge-lee:state", ridge.get("data_state") in {"ridge_spillover_shelter_cache","ridge_spillover_shelter_unavailable_safe","ridge_spillover_shelter_generation_failed"}, ridge.get("data_state","missing"))
    ridge_required = scene.get("full_dem",{}).get("data_state")=="continuous_dem_cache" and scene.get("terrain_steering_confidence",{}).get("data_state")=="terrain_steering_confidence_cache"
    record("ridge-lee:required-when-supported", not ridge_required or ridge.get("data_state")=="ridge_spillover_shelter_cache", ridge.get("data_state","missing"))
    directives = ridge.get("particle_directives") or {}
    record("ridge-lee:bounded-motion", 0<=float(directives.get("spillover_lift_px",0))<=8 and 0.82<=float(directives.get("lee_slowdown_multiplier",1))<=1 and 1<=float(directives.get("lee_spread_multiplier",1))<=1.18, str(directives))
    record("ridge-lee:boundary", "not measured airflow" in ridge.get("claim_boundary","") and "not" in ridge.get("claim_boundary",""), ridge.get("claim_boundary","missing"))


    saddle = scene.get("saddle_gap_acceleration", {})
    required_saddle={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","saddle_statistics","gap_statistics","confidence_support","particle_directives","scene_directive","claim_boundary"}
    record("saddle-gap:contract", required_saddle.issubset(saddle), saddle.get("display_label","missing"))
    record("saddle-gap:pass", saddle.get("pass_id")=="SV2-36", saddle.get("pass_id","missing"))
    record("saddle-gap:state", saddle.get("data_state") in {"saddle_transfer_gap_cache","saddle_gap_unavailable_safe","saddle_gap_generation_failed"}, saddle.get("data_state","missing"))
    record("saddle-gap:boundary", "not measured airflow" in saddle.get("claim_boundary",""), saddle.get("claim_boundary","missing"))
    canyon = scene.get("canyon_channeling", {})
    required_canyon={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","channeling_statistics","drainage_statistics","confidence_support","particle_directives","scene_directive","claim_boundary"}
    record("canyon-drainage:contract", required_canyon.issubset(canyon), canyon.get("display_label","missing"))
    record("canyon-drainage:pass", canyon.get("pass_id")=="SV2-35", canyon.get("pass_id","missing"))
    record("canyon-drainage:state", canyon.get("data_state") in {"canyon_channeling_drainage_cache","canyon_channeling_unavailable_safe","canyon_channeling_generation_failed"}, canyon.get("data_state","missing"))
    record("canyon-drainage:boundary", "not measured airflow" in canyon.get("claim_boundary",""), canyon.get("claim_boundary","missing"))


    basin = scene.get("basin_retention_cold_air_pooling", {})
    required_basin={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","basin_statistics","cold_pooling_statistics","confidence_support","particle_directives","atmospheric_basis","scene_directive","claim_boundary"}
    record("basin-retention:contract", required_basin.issubset(basin), basin.get("display_label","missing"))
    record("basin-retention:pass", basin.get("pass_id")=="SV2-37", basin.get("pass_id","missing"))
    record("basin-retention:state", basin.get("data_state") in {"basin_retention_cold_air_pooling_cache","basin_retention_unavailable_safe","basin_retention_generation_failed"}, basin.get("data_state","missing"))
    directives=basin.get("particle_directives") or {}
    record("basin-retention:bounded-motion", 0.84<=float(directives.get("retention_slowdown",1))<=1 and 1<=float(directives.get("pooling_broadening",1))<=1.16 and 0<=float(directives.get("settling_px",0))<=5, str(directives))
    record("basin-retention:boundary", "not measured temperature inversions" in basin.get("claim_boundary",""), basin.get("claim_boundary","missing"))

    convergence=scene.get("terrain_convergence_accumulation", {})
    required_convergence={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","convergence_statistics","accumulation_statistics","confidence_support","particle_directives","atmospheric_basis","scene_directive","claim_boundary"}
    record("terrain-convergence:contract", required_convergence.issubset(convergence), convergence.get("display_label","missing"))
    record("terrain-convergence:pass", convergence.get("pass_id")=="SV2-38", convergence.get("pass_id","missing"))
    record("terrain-convergence:state", convergence.get("data_state") in {"terrain_convergence_accumulation_cache","terrain_convergence_unavailable_safe","terrain_convergence_generation_failed"}, convergence.get("data_state","missing"))
    cd=convergence.get("particle_directives") or {}
    record("terrain-convergence:bounded-motion", 0<=float(cd.get("convergence_pull_px",0))<=7.5 and .86<=float(cd.get("focus_slowdown",1))<=1 and 1<=float(cd.get("focus_broadening",1))<=1.14, str(cd))
    record("terrain-convergence:boundary", "not measured airflow convergence" in convergence.get("claim_boundary",""), convergence.get("claim_boundary","missing"))


    divergence=scene.get("terrain_divergence_dispersion", {})
    required_divergence={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","divergence_statistics","dispersion_statistics","confidence_support","particle_directives","atmospheric_basis","scene_directive","claim_boundary"}
    record("terrain-divergence:contract", required_divergence.issubset(divergence), divergence.get("display_label","missing"))
    record("terrain-divergence:pass", divergence.get("pass_id")=="SV2-39", divergence.get("pass_id","missing"))
    record("terrain-divergence:state", divergence.get("data_state") in {"terrain_divergence_dispersion_cache","terrain_divergence_unavailable_safe","terrain_divergence_generation_failed"}, divergence.get("data_state","missing"))
    dd=divergence.get("particle_directives") or {}
    record("terrain-divergence:bounded-motion", 0<=float(dd.get("divergence_spread_px",0))<=8 and 1<=float(dd.get("dispersion_broadening",1))<=1.16 and 1<=float(dd.get("dispersion_speed_multiplier",1))<=1.08, str(dd))
    record("terrain-divergence:boundary", "not measured airflow divergence" in divergence.get("claim_boundary",""), divergence.get("claim_boundary","missing"))

    transitions=scene.get("terrain_transition_regimes", {})
    required_transitions={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","transition_statistics","boundary_statistics","regime_mix","confidence_support","particle_directives","atmospheric_basis","scene_directive","claim_boundary"}
    record("terrain-transitions:contract", required_transitions.issubset(transitions), transitions.get("display_label","missing"))
    record("terrain-transitions:pass", transitions.get("pass_id")=="SV2-40", transitions.get("pass_id","missing"))
    record("terrain-transitions:state", transitions.get("data_state") in {"terrain_transition_regimes_cache","terrain_transition_unavailable_safe","terrain_transition_generation_failed"}, transitions.get("data_state","missing"))
    td=transitions.get("particle_directives") or {}
    record("terrain-transitions:bounded-motion", 0<=float(td.get("transition_jitter_px",0))<=5.5 and 1<=float(td.get("boundary_softening",1))<=1.10 and 0<=float(td.get("regime_blend",0))<=.72, str(td))
    record("terrain-transitions:boundary", "not measured atmospheric fronts" in transitions.get("claim_boundary",""), transitions.get("claim_boundary","missing"))

    regime=scene.get("terrain_regime_confidence", {})
    required_regime={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","confidence_statistics","ambiguity_statistics","regime_support","downgrade_reasons","visual_directives","scene_directive","claim_boundary"}
    record("terrain-regime-confidence:contract", required_regime.issubset(regime), regime.get("display_label","missing"))
    record("terrain-regime-confidence:pass", regime.get("pass_id")=="SV2-41", regime.get("pass_id","missing"))
    record("terrain-regime-confidence:state", regime.get("data_state") in {"terrain_regime_confidence_cache","terrain_regime_confidence_unavailable_safe","terrain_regime_confidence_generation_failed"}, regime.get("data_state","missing"))
    vd=regime.get("visual_directives") or {}
    record("terrain-regime-confidence:bounded-visual", 0<=float(vd.get("confidence_glow",0))<=.55 and 0<=float(vd.get("ambiguity_veil",0))<=.52 and .84<=float(vd.get("boundary_fade",1))<=1, str(vd))
    record("terrain-regime-confidence:boundary", "Neither layer is confidence in methane presence" in regime.get("claim_boundary",""), regime.get("claim_boundary","missing"))

    integrated=scene.get("integrated_terrain_response",{})
    required_integrated={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","dominant_regime","response_statistics","agreement_statistics","component_support","visual_directives","scene_directive","claim_boundary"}
    record("integrated-response:contract",required_integrated.issubset(integrated),integrated.get("display_label","missing"))
    record("integrated-response:pass",integrated.get("pass_id")=="SV2-42",integrated.get("pass_id","missing"))
    record("integrated-response:state",integrated.get("data_state") in {"integrated_terrain_response_cache","integrated_terrain_response_unavailable_safe","integrated_terrain_response_generation_failed"},integrated.get("data_state","missing"))
    iv=integrated.get("visual_directives") or {}
    record("integrated-response:bounded-visual",0<=float(iv.get("field_opacity",0))<=.38 and 0<=float(iv.get("agreement_glow",0))<=.34 and 0<=float(iv.get("conflict_veil",0))<=.28,str(iv))
    record("integrated-response:boundary","not measured airflow" in integrated.get("claim_boundary",""),integrated.get("claim_boundary","missing"))

    authority=scene.get("integrated_response_authority",{})
    required_authority={"contract_version","pass_id","layer","evidence_state","data_state","status","display_label","authority_statistics","conflict_statistics","resolution_policy","winning_regime","suppressed_regimes","visual_directives","scene_directive","claim_boundary"}
    record("response-authority:contract",required_authority.issubset(authority),authority.get("display_label","missing"))
    record("response-authority:pass",authority.get("pass_id")=="SV2-43",authority.get("pass_id","missing"))
    record("response-authority:state",authority.get("data_state") in {"integrated_response_authority_cache","integrated_response_authority_unavailable_safe","integrated_response_authority_generation_failed"},authority.get("data_state","missing"))
    av=authority.get("visual_directives") or {}
    record("response-authority:bounded-visual",0<=float(av.get("authority_opacity",0))<=.40 and 0<=float(av.get("conflict_veil",0))<=.32 and 0<=float(av.get("motion_authority",0))<=.34,str(av))
    record("response-authority:conflict-preserved",bool((authority.get("resolution_policy") or {}).get("conflict_is_preserved",authority.get("status")!="ready")),str(authority.get("resolution_policy")))
    record("response-authority:boundary","not confidence in methane presence" in authority.get("claim_boundary",""),authority.get("claim_boundary","missing"))

    coherence=scene.get("integrated_scene_coherence",{})
    record("scene-coherence:contract", {"contract_version","pass_id","data_state","cadence_authority","phases","timing","claim_boundary"}.issubset(coherence), coherence.get("display_label","missing"))
    record("scene-coherence:pass", coherence.get("pass_id")=="SV2-46", coherence.get("pass_id","missing"))
    record("scene-coherence:bounded", 0<=float(coherence.get("cadence_authority",0))<=.35 and .6<=float((coherence.get("timing") or {}).get("transition_seconds",1.4))<=2.4, str(coherence.get("timing")))
    camera=scene.get("scientific_cinematic_camera",{})
    record("scientific-camera:contract", {"contract_version","pass_id","data_state","camera_authority","mode","keyframes","interaction_guardrails","claim_boundary"}.issubset(camera), camera.get("display_label","missing"))
    record("scientific-camera:pass", camera.get("pass_id")=="SV2-47", camera.get("pass_id","missing"))
    guard=camera.get("interaction_guardrails") or {}
    record("scientific-camera:bounded", 0<=float(camera.get("camera_authority",0))<=.26 and guard.get("max_zoom_delta",1)<=1 and guard.get("looping",False) is False, str(guard))
    record("scientific-camera:boundary", "adds no scientific evidence" in camera.get("claim_boundary","") or "add scientific evidence" in camera.get("claim_boundary",""), camera.get("claim_boundary","missing"))
    focus=scene.get("evidence_guided_focus_depth",{})
    record("focus-depth:contract", {"contract_version","pass_id","data_state","focus_authority","focus_target","depth_planes","visual_directives","interaction_guardrails","claim_boundary"}.issubset(focus), focus.get("display_label","missing"))
    record("focus-depth:pass", focus.get("pass_id")=="SV2-48", focus.get("pass_id","missing"))
    vd=focus.get("visual_directives") or {}
    record("focus-depth:bounded", 0<=float(focus.get("focus_authority",0))<=.24 and 0<=float(vd.get("max_blur_px",0))<=1.8 and vd.get("depth_of_field_simulation",False) is False, str(vd))
    record("focus-depth:uncertainty-visible", (focus.get("status")!="ready") or any(x.get("id")=="uncertainty" for x in focus.get("depth_planes",[])), str(focus.get("depth_planes")))
    record("focus-depth:boundary", "do not measure distance" in focus.get("claim_boundary","") or "do not measure" in focus.get("claim_boundary",""), focus.get("claim_boundary","missing"))
    lighting=scene.get("atmospheric_light_legibility",{})
    required_lighting={"contract_version","pass_id","data_state","lighting_authority","lighting_mode","legibility_scores","visual_directives","interaction_guardrails","claim_boundary"}
    record("atmospheric-light:contract", required_lighting.issubset(lighting), lighting.get("display_label","missing"))
    record("atmospheric-light:pass", lighting.get("pass_id")=="SV2-49", lighting.get("pass_id","missing"))
    lvd=lighting.get("visual_directives") or {}
    record("atmospheric-light:bounded", 0<=float(lighting.get("lighting_authority",0))<=.28 and 0<=float(lvd.get("max_shadow_opacity",0))<=.18 and 0<=float(lvd.get("max_glow_radius_px",0))<=13, str(lvd))
    record("atmospheric-light:no-false-optics", lvd.get("optical_density_simulation",False) is False and lvd.get("concentration_shading",False) is False and lvd.get("plume_thickness_inference",False) is False, str(lvd))
    record("atmospheric-light:uncertainty-visible", float((lighting.get("legibility_scores") or {}).get("uncertainty",0))>=.82, str(lighting.get("legibility_scores")))
    record("atmospheric-light:boundary", "do not measure concentration" in lighting.get("claim_boundary","") or "do not measure" in lighting.get("claim_boundary",""), lighting.get("claim_boundary","missing"))

    hierarchy=scene.get("evidence_visual_hierarchy",{})
    required_hierarchy={"contract_version","pass_id","data_state","hierarchy_authority","hierarchy_mode","priority_order","palette","contrast_rules","interaction_guardrails","claim_boundary"}
    record("visual-hierarchy:contract", required_hierarchy.issubset(hierarchy), hierarchy.get("display_label","missing"))
    record("visual-hierarchy:pass", hierarchy.get("pass_id")=="SV2-50", hierarchy.get("pass_id","missing"))
    rules=hierarchy.get("contrast_rules") or {}
    record("visual-hierarchy:bounded", 0<=float(hierarchy.get("hierarchy_authority",0))<=.30 and float(rules.get("uncertainty_prominence_floor",0))>=.90 and int(rules.get("simultaneous_accent_limit",99))<=3, str(rules))
    record("visual-hierarchy:no-false-color", rules.get("color_as_measurement",False) is False and rules.get("color_as_concentration",False) is False and rules.get("hidden_evidence_allowed",False) is False, str(rules))
    record("visual-hierarchy:boundary", "do not measure concentration" in hierarchy.get("claim_boundary","") or "do not measure" in hierarchy.get("claim_boundary",""), hierarchy.get("claim_boundary","missing"))


    annotations=scene.get("scientific_annotation_choreography",{})
    record("annotations:pass", annotations.get("pass_id")=="SV2-51", annotations.get("pass_id","missing"))
    record("annotations:boundary", "do not add observations" in annotations.get("claim_boundary","").lower(), annotations.get("claim_boundary","missing"))
    timeline=scene.get("scientific_storytelling_timeline",{})
    record("timeline:pass", timeline.get("pass_id")=="SV2-52", timeline.get("pass_id","missing"))
    record("timeline:phases", len(timeline.get("phases",[]))==7, str(len(timeline.get("phases",[]))))
    record("timeline:no-loop", (timeline.get("interaction_guardrails") or {}).get("no_loop") is True or timeline.get("status")=="unavailable_safe", str(timeline.get("interaction_guardrails")))

    disclosure=scene.get("progressive_disclosure",{})
    record("disclosure:pass", disclosure.get("pass_id")=="SV2-54", disclosure.get("pass_id","missing"))
    record("disclosure:contract", all(k in disclosure for k in ["contract_version","data_state","levels","scene_policy","navigation","claim_boundary"]), disclosure.get("data_state","missing"))
    level_ids={level.get("id") for level in disclosure.get("levels",[])}
    record("disclosure:levels", level_ids=={"overview","context","audit"}, str(sorted(level_ids)))
    policy=disclosure.get("scene_policy") or {}
    record("disclosure:science-preserved", policy.get("science_removed") is False and policy.get("deep_routes_preserved") is True, str(policy))
    record("disclosure:uncertainty-visible", policy.get("uncertainty_visible_in_overview") is True, str(policy.get("uncertainty_visible_in_overview")))
    record("disclosure:boundary", "changes visibility and reading order only" in disclosure.get("claim_boundary",""), disclosure.get("claim_boundary","missing"))

    passed = sum(1 for check in checks if check["passed"])
    failed = len(checks) - passed
    failed_checks = [check for check in checks if not check["passed"]]

    return {
        "pass_id": PASS_ID,
        "revision": "progressive-disclosure-scene-simplification-1",
        "status": "PASS" if failed == 0 else "FAIL",
        "passed": passed,
        "failed": failed,
        "total": len(checks),
        "failed_checks": failed_checks,
        "checks": checks,
        "note": "Internal checks verify measured-terrain flow nodes, bounded lateral steering, elevation lighting, layered air volume, living-wind motion bounds, observation provenance, citation traceability, controlled evidence vocabulary, visible missing-evidence consequences, evidence-time separation, validated DEM-derived hillshade, slope/aspect, landforms, and terrain confidence, historical-weather gating and retrieval, multi-level wind gating and retrieval, atmospheric-stability screening, boundary-layer-depth gating, gust-variability window completeness, terrain-steering confidence and uncertainty, steering-aware air-volume modulation, ridge-spillover and lee-side-shelter confidence gating, single-page launch readiness, progressive disclosure, scene simplification, and scientific guardrails.",
    }
