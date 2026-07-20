from __future__ import annotations

from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from engine.basemap_surface import basemap_context
from engine.evidence_packet import build_evidence_packet
from engine.hunter_lens import hunter_lens
from engine.plume_model import plume_model_contract
from engine.scene_config import default_scene_config
from engine.source_registry import get_source_registry
from engine.pass_checks import run_internal_checks
from engine.observation_contract import build_observation_contract
from engine.citation_surface import build_citation_surface
from engine.evidence_vocabulary import build_evidence_vocabulary
from engine.missing_evidence import build_missing_evidence
from engine.wind_loader import wind_context
from engine.terrain_loader import terrain_context
from engine.full_dem import full_dem_context, RASTER_FILE
from engine.hillshade import hillshade_context, HILLSHADE_FILE
from engine.slope_aspect import slope_aspect_context, SLOPE_FILE, ASPECT_FILE
from engine.landform_classification import landform_context, LANDFORM_FILE, CONFIDENCE_FILE
from engine.terrain_confidence import terrain_confidence_context, CONFIDENCE_RASTER_FILE
from engine.historical_weather import historical_weather_context
from engine.multi_level_wind import multi_level_wind_context
from engine.atmospheric_stability import atmospheric_stability_context
from engine.boundary_layer_depth import boundary_layer_depth_context
from engine.gust_variability import gust_variability_context
from engine.terrain_atmosphere_index import terrain_atmosphere_index_context
from engine.terrain_steering_field import terrain_steering_field_context, FIELD_FILE
from engine.terrain_steering_confidence import terrain_steering_confidence_context, CONFIDENCE_FILE as STEERING_CONFIDENCE_FILE, UNCERTAINTY_FILE as STEERING_UNCERTAINTY_FILE
from engine.ridge_spillover_shelter import ridge_spillover_shelter_context, SPILLOVER_FILE, SHELTER_FILE
from engine.canyon_channeling import canyon_channeling_context, CHANNEL_FILE, DRAINAGE_FILE
from engine.saddle_gap_acceleration import saddle_gap_context, SADDLE_FILE, GAP_FILE
from engine.basin_retention_cold_air_pooling import basin_retention_context, BASIN_FILE, COLD_POOL_FILE
from engine.terrain_convergence_accumulation import terrain_convergence_context, CONVERGENCE_FILE, ACCUMULATION_FILE
from engine.terrain_divergence_dispersion import terrain_divergence_context, DIVERGENCE_FILE, DISPERSION_FILE
from engine.terrain_transition_regimes import terrain_transition_context, TRANSITION_FILE, BOUNDARY_FILE
from engine.terrain_regime_confidence import terrain_regime_confidence_context, CONFIDENCE_FILE as REGIME_CONFIDENCE_FILE, AMBIGUITY_FILE as BOUNDARY_AMBIGUITY_FILE
from engine.integrated_terrain_response import integrated_terrain_response_context, FIELD_FILE as INTEGRATED_FIELD_FILE, AGREEMENT_FILE as INTEGRATED_AGREEMENT_FILE
from engine.integrated_response_authority import integrated_response_authority_context, AUTHORITY_FILE as RESPONSE_AUTHORITY_FILE, CONFLICT_FILE as RESPONSE_CONFLICT_FILE
from engine.integrated_motion_orchestration import integrated_motion_orchestration_context
from engine.integrated_air_volume_orchestration import integrated_air_volume_orchestration_context
from engine.integrated_scene_coherence import integrated_scene_coherence_context
from engine.scientific_cinematic_camera import scientific_cinematic_camera_context
from engine.evidence_guided_focus_depth import evidence_guided_focus_depth_context
from engine.atmospheric_light_legibility import atmospheric_light_legibility_context
from engine.evidence_visual_hierarchy import evidence_visual_hierarchy_context
from engine.scientific_annotation_choreography import scientific_annotation_choreography_context
from engine.scientific_storytelling_timeline import scientific_storytelling_timeline_context
from engine.reviewer_guided_exploration import reviewer_guided_exploration_context
from engine.progressive_disclosure import progressive_disclosure_context
from engine.scientific_synthesis_decision_surface import scientific_synthesis_decision_surface_context
from engine.level_five_visual_composition import level_five_visual_composition_context
from engine.final_release_audit import final_release_audit_context
from engine.observation_atlas import observation_atlas
from engine.scientific_personality import scientific_personality_context
from engine.governing_model import input_from_dict, run_governing_model

app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "Invisible Air", "pass_id": "SV2-57", "release_id": "FINAL-INSTRUMENT"})


@app.get("/")
def index():
    scene = default_scene_config()
    return render_template("index.html", scene=scene)


@app.get("/scene")
def scene():
    scene_config = default_scene_config()
    return render_template("scene.html", scene=scene_config)


@app.get("/observatory")
def observatory():
    selected_case = request.args.get("case", "ventura-oxnard")
    scene_config = default_scene_config()
    scene_config["scientific_personality"] = scientific_personality_context(scene_config)
    atlas = observation_atlas(selected_case)
    return render_template("observatory.html", scene=scene_config, atlas=atlas)




def _observatory_governing_input(scene_config):
    """Translate the active Observatory scene into the Pass 48 field contract.

    Missing atmospheric or terrain evidence uses explicit neutral defaults and is
    recorded in the returned manifest by the governing model.
    """
    observation = scene_config.get("observation_contract", {})
    coordinates = observation.get("coordinates", {})
    location = scene_config.get("location", {})
    wind = scene_config.get("wind", {})
    stability = scene_config.get("atmospheric_stability", {})
    boundary = scene_config.get("boundary_layer_depth", {})
    variability = scene_config.get("gust_variability", {})
    terrain_field = scene_config.get("terrain_steering_field", {})
    terrain_confidence = scene_config.get("terrain_confidence", {})

    stability_class = str(stability.get("stability_class") or "neutral").lower()
    if stability_class not in {"very_unstable", "unstable", "neutral", "stable", "very_stable"}:
        stability_class = "neutral"

    metrics = variability.get("metrics") or {}
    direction_variability = float(metrics.get("direction_range_deg") or metrics.get("circular_std_deg") or 12.0)
    speed_mph = float(wind.get("speed_mph") or 8.0)
    gust_mph = wind.get("gust_mph")
    gust_factor = float(gust_mph) / speed_mph if gust_mph and speed_mph > 0 else 1.20

    steering_stats = terrain_field.get("field_statistics") or {}
    terrain_available = terrain_field.get("status") not in {None, "unavailable_safe"}
    regime = "complex" if terrain_available else "open"
    alignment = steering_stats.get("dominant_alignment_deg")
    evidence_support = float(terrain_confidence.get("overall_score") or (0.82 if terrain_available else 0.62))

    return {
        "source": {
            "latitude": float(coordinates.get("lat") or location.get("lat") or 34.2256),
            "longitude": float(coordinates.get("lon") or location.get("lon") or -119.1189),
            "relative_strength": 1.0,
            "release_height_m": 10.0,
            "release_duration_minutes": 60.0,
            "pollutant_phase": "gas",
        },
        "meteorology": {
            "wind_from_deg": float(wind.get("from_degrees") or 248.0),
            "wind_speed_mps": max(0.2, speed_mph * 0.44704),
            "stability_class": stability_class,
            "boundary_layer_depth_m": float(boundary.get("boundary_layer_height_m") or 650.0),
            "direction_variability_deg": max(0.0, min(35.0, direction_variability)),
            "gust_factor": max(1.0, min(2.5, gust_factor)),
        },
        "terrain": {
            "regime": regime,
            "alignment_deg": float(alignment) if alignment is not None else None,
            "response_strength": 0.8 if terrain_available else 0.0,
            "evidence_support": max(0.2, min(1.0, evidence_support)),
        },
        "grid": {
            "domain_downwind_km": 80.0,
            "domain_crosswind_km": 40.0,
            "nx": 241,
            "ny": 161,
        },
    }


@app.route("/governing-field.json", methods=["GET", "POST"])
def governing_field_json():
    """Pass 48 deterministic field contract; does not alter the legacy observatory renderer."""
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
    else:
        case = request.args.get("case", "open_terrain_west_wind")
        safe_case = "".join(ch for ch in case if ch.isalnum() or ch in {"_", "-"})
        path = Path(__file__).resolve().parent / "data" / "pass48_benchmarks" / f"{safe_case}.json"
        if not path.exists():
            return jsonify({"error": "unknown benchmark case", "case": case}), 404
        import json
        payload = json.loads(path.read_text(encoding="utf-8"))
    try:
        return jsonify(run_governing_model(input_from_dict(payload)))
    except (TypeError, ValueError) as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/observatory-field.json")
def observatory_field_json():
    """Pass 49 model-driven field for the active Observatory scene."""
    scene_config = default_scene_config()
    payload = _observatory_governing_input(scene_config)
    terrain_mode = request.args.get("terrain", "on").lower()
    profile_override = request.args.get("terrain_profile")
    if terrain_mode in {"off", "0", "false"}:
        payload.setdefault("terrain", {})["local_response_enabled"] = False
    if profile_override in {"open", "valley_aligned", "cross_ridge", "complex"}:
        payload.setdefault("terrain", {})["local_profile"] = profile_override
    result = run_governing_model(input_from_dict(payload))
    result["observatory"] = {
        "source_label": scene_config.get("location", {}).get("label", "Selected source"),
        "wind_label": scene_config.get("wind", {}).get("label", "Wind context unavailable"),
        "input_translation": payload,
    }
    return jsonify(result)


@app.get("/scientific-personality.json")
def scientific_personality_json():
    scene_config = default_scene_config()
    return jsonify(scientific_personality_context(scene_config))


@app.get("/atlas")
def atlas_room():
    selected_case = request.args.get("case", "ventura-oxnard")
    return render_template("atlas.html", atlas=observation_atlas(selected_case))


@app.get("/library")
def library_room():
    return render_template("library_room.html")


@app.get("/about")
def about_room():
    return render_template("about_room.html")


@app.get("/observation-atlas.json")
def observation_atlas_json():
    selected_case = request.args.get("case", "ventura-oxnard")
    return jsonify(observation_atlas(selected_case))


@app.get("/observation-atlas/template.json")
def observation_atlas_template():
    path = Path(__file__).resolve().parent / "data" / "observation_atlas" / "CASE_PACKAGE_TEMPLATE.json"
    return send_file(path, mimetype="application/json", as_attachment=True, download_name="INVISIBLE_AIR_CASE_PACKAGE_TEMPLATE.json")


@app.get("/shot")
def shot():
    scene_config = default_scene_config()
    scene_config["terrain"] = terrain_context(scene_config)
    return render_template("scene.html", scene=scene_config, shot_mode=True)


@app.get("/scene.json")
def scene_json():
    refresh = request.args.get("refresh_wind", "0").lower() in {"1", "true", "yes"}
    refresh_terrain = request.args.get("refresh_terrain", "0").lower() in {"1", "true", "yes"}
    refresh_dem = request.args.get("refresh_dem", "0").lower() in {"1", "true", "yes"}
    refresh_hillshade = request.args.get("refresh_hillshade", "0").lower() in {"1", "true", "yes"}
    refresh_slope_aspect = request.args.get("refresh_slope_aspect", "0").lower() in {"1", "true", "yes"}
    refresh_landforms = request.args.get("refresh_landforms", "0").lower() in {"1", "true", "yes"}
    refresh_terrain_confidence = request.args.get("refresh_terrain_confidence", "0").lower() in {"1", "true", "yes"}
    refresh_historical_weather = request.args.get("refresh_historical_weather", "0").lower() in {"1", "true", "yes"}
    refresh_multi_level_wind = request.args.get("refresh_multi_level_wind", "0").lower() in {"1", "true", "yes"}
    refresh_atmospheric_stability = request.args.get("refresh_atmospheric_stability", "0").lower() in {"1", "true", "yes"}
    refresh_boundary_layer_depth = request.args.get("refresh_boundary_layer_depth", "0").lower() in {"1", "true", "yes"}
    refresh_gust_variability = request.args.get("refresh_gust_variability", "0").lower() in {"1", "true", "yes"}
    scene_config = default_scene_config(refresh_wind=refresh, refresh_terrain=refresh_terrain, refresh_dem=refresh_dem, refresh_hillshade=refresh_hillshade, refresh_slope_aspect=refresh_slope_aspect, refresh_landforms=refresh_landforms, refresh_terrain_confidence=refresh_terrain_confidence, refresh_historical_weather=refresh_historical_weather, refresh_multi_level_wind=refresh_multi_level_wind, refresh_atmospheric_stability=refresh_atmospheric_stability, refresh_boundary_layer_depth=refresh_boundary_layer_depth, refresh_gust_variability=refresh_gust_variability)
    scene_config["terrain"] = terrain_context(scene_config)
    return jsonify(scene_config)


@app.get("/map-surface")
def map_surface():
    return render_template("map_surface.html", basemap=basemap_context())


@app.get("/map-surface.json")
def map_surface_json():
    return jsonify(basemap_context())


@app.get("/terrain")
def terrain():
    scene_config = default_scene_config()
    return render_template("terrain.html", terrain=terrain_context(scene_config))


@app.get("/terrain.json")
def terrain_json():
    scene_config = default_scene_config()
    refresh = request.args.get("refresh", "0").lower() in {"1", "true", "yes"}
    return jsonify(terrain_context(scene_config, refresh=refresh))



@app.get("/dem")
def dem():
    scene_config = default_scene_config()
    return render_template("dem.html", dem=scene_config["full_dem"], scene=scene_config)


@app.get("/dem.json")
def dem_json():
    scene_config = default_scene_config()
    refresh = request.args.get("refresh", "0").lower() in {"1", "true", "yes"}
    return jsonify(full_dem_context(scene_config, refresh=refresh))


@app.get("/dem-file")
def dem_file():
    scene_config = default_scene_config()
    contract = full_dem_context(scene_config)
    if contract.get("data_state") != "continuous_dem_cache" or not RASTER_FILE.exists():
        return jsonify({"status": "not_available", "detail": contract.get("display_label")}), 404
    return send_file(RASTER_FILE, mimetype="image/tiff", as_attachment=True, download_name="invisible_air_scene_dem.tif")

@app.get("/hillshade")
def hillshade():
    scene_config = default_scene_config()
    return render_template("hillshade.html", hillshade=scene_config["hillshade"], scene=scene_config)


@app.get("/hillshade.json")
def hillshade_json():
    scene_config = default_scene_config()
    refresh = request.args.get("refresh", "0").lower() in {"1", "true", "yes"}
    return jsonify(hillshade_context(scene_config, refresh=refresh))


@app.get("/hillshade-image")
def hillshade_image():
    scene_config = default_scene_config()
    contract = hillshade_context(scene_config)
    if contract.get("data_state") != "dem_derived_hillshade_cache" or not HILLSHADE_FILE.exists():
        return jsonify({"status": "not_available", "detail": contract.get("display_label")}), 404
    return send_file(HILLSHADE_FILE, mimetype="image/png", max_age=0)



@app.get("/slope-aspect")
def slope_aspect():
    scene_config = default_scene_config()
    return render_template("slope_aspect.html", derivatives=scene_config["slope_aspect"], scene=scene_config)


@app.get("/slope-aspect.json")
def slope_aspect_json():
    scene_config = default_scene_config()
    refresh = request.args.get("refresh", "0").lower() in {"1", "true", "yes"}
    return jsonify(slope_aspect_context(scene_config, refresh=refresh))


@app.get("/slope-image")
def slope_image():
    scene_config = default_scene_config()
    contract = slope_aspect_context(scene_config)
    if contract.get("data_state") != "dem_derived_slope_aspect_cache" or not SLOPE_FILE.exists():
        return jsonify({"status": "not_available", "detail": contract.get("display_label")}), 404
    return send_file(SLOPE_FILE, mimetype="image/png", max_age=0)


@app.get("/aspect-image")
def aspect_image():
    scene_config = default_scene_config()
    contract = slope_aspect_context(scene_config)
    if contract.get("data_state") != "dem_derived_slope_aspect_cache" or not ASPECT_FILE.exists():
        return jsonify({"status": "not_available", "detail": contract.get("display_label")}), 404
    return send_file(ASPECT_FILE, mimetype="image/png", max_age=0)


@app.get("/landforms")
def landforms():
    scene_config=default_scene_config()
    return render_template("landforms.html", landforms=scene_config["landforms"], scene=scene_config)

@app.get("/landforms.json")
def landforms_json():
    scene_config=default_scene_config()
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(landform_context(scene_config,refresh=refresh))

@app.get("/landform-image")
def landform_image():
    scene_config=default_scene_config(); contract=landform_context(scene_config)
    if contract.get("data_state")!="dem_derived_landform_cache" or not LANDFORM_FILE.exists():
        return jsonify({"status":"not_available","detail":contract.get("display_label")}),404
    return send_file(LANDFORM_FILE,mimetype="image/png",max_age=0)

@app.get("/landform-confidence-image")
def landform_confidence_image():
    scene_config=default_scene_config(); contract=landform_context(scene_config)
    if contract.get("data_state")!="dem_derived_landform_cache" or not CONFIDENCE_FILE.exists():
        return jsonify({"status":"not_available","detail":contract.get("display_label")}),404
    return send_file(CONFIDENCE_FILE,mimetype="image/png",max_age=0)


@app.get("/terrain-confidence")
def terrain_confidence():
    scene_config=default_scene_config()
    return render_template("terrain_confidence.html", confidence=scene_config["terrain_confidence"], scene=scene_config)

@app.get("/terrain-confidence.json")
def terrain_confidence_json():
    scene_config=default_scene_config()
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(terrain_confidence_context(scene_config,refresh=refresh))

@app.get("/terrain-confidence-image")
def terrain_confidence_image():
    scene_config=default_scene_config(); contract=terrain_confidence_context(scene_config)
    if contract.get("data_state")!="terrain_confidence_ready" or not CONFIDENCE_RASTER_FILE.exists():
        return jsonify({"status":"not_available","detail":contract.get("display_label")}),404
    return send_file(CONFIDENCE_RASTER_FILE,mimetype="image/png",max_age=0)


@app.get("/historical-weather")
def historical_weather():
    scene_config=default_scene_config()
    return render_template("historical_weather.html", historical=scene_config["historical_weather"], scene=scene_config)

@app.get("/historical-weather.json")
def historical_weather_json():
    scene_config=default_scene_config()
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(historical_weather_context(scene_config["observation_contract"], scene_config["location"]["lat"], scene_config["location"]["lon"], refresh=refresh))

@app.get("/favicon.ico")
def favicon():
    return ("", 204)


@app.get("/wind")
def wind():
    scene_config = default_scene_config()
    return render_template("wind.html", wind=scene_config["wind"], scene=scene_config)


@app.get("/wind.json")
def wind_json():
    scene_config = default_scene_config()
    refresh = request.args.get("refresh", "0").lower() in {"1", "true", "yes"}
    return jsonify(wind_context(scene_config["location"]["lat"], scene_config["location"]["lon"], refresh=refresh))



@app.get("/multi-level-wind")
def multi_level_wind():
    scene_config=default_scene_config()
    return render_template("multi_level_wind.html", multi=scene_config["multi_level_wind"], scene=scene_config)

@app.get("/multi-level-wind.json")
def multi_level_wind_json():
    scene_config=default_scene_config()
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(multi_level_wind_context(scene_config["observation_contract"], scene_config["location"]["lat"], scene_config["location"]["lon"], refresh=refresh))


@app.get("/atmospheric-stability")
def atmospheric_stability():
    scene_config=default_scene_config()
    return render_template("atmospheric_stability.html", stability=scene_config["atmospheric_stability"], scene=scene_config)

@app.get("/atmospheric-stability.json")
def atmospheric_stability_json():
    scene_config=default_scene_config()
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(atmospheric_stability_context(scene_config["observation_contract"], scene_config["location"]["lat"], scene_config["location"]["lon"], refresh=refresh))


@app.get("/boundary-layer-depth")
def boundary_layer_depth():
    scene_config=default_scene_config()
    return render_template("boundary_layer_depth.html", boundary=scene_config["boundary_layer_depth"], scene=scene_config)

@app.get("/boundary-layer-depth.json")
def boundary_layer_depth_json():
    scene_config=default_scene_config()
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(boundary_layer_depth_context(scene_config["observation_contract"], scene_config["location"]["lat"], scene_config["location"]["lon"], refresh=refresh))


@app.get("/gust-variability")
def gust_variability():
    scene_config=default_scene_config()
    return render_template("gust_variability.html", variability=scene_config["gust_variability"], scene=scene_config)

@app.get("/gust-variability.json")
def gust_variability_json():
    scene_config=default_scene_config()
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(gust_variability_context(scene_config["observation_contract"], scene_config["location"]["lat"], scene_config["location"]["lon"], refresh=refresh))


@app.get("/terrain-steering-field")
def terrain_steering_field():
    scene_config=default_scene_config()
    return render_template("terrain_steering_field.html", field=scene_config["terrain_steering_field"], scene=scene_config)

@app.get("/terrain-steering-field.json")
def terrain_steering_field_json():
    scene_config=default_scene_config()
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(terrain_steering_field_context(scene_config,refresh=refresh))

@app.get("/terrain-steering-field-image")
def terrain_steering_field_image():
    scene_config=default_scene_config(); contract=terrain_steering_field_context(scene_config)
    if contract.get("data_state")!="terrain_steering_field_cache" or not FIELD_FILE.exists():
        return jsonify({"status":"not_available","detail":contract.get("display_label")}),404
    return send_file(FIELD_FILE,mimetype="image/png",max_age=0)


@app.get("/terrain-steering-confidence")
def terrain_steering_confidence():
    scene_config=default_scene_config()
    return render_template("terrain_steering_confidence.html", confidence=scene_config["terrain_steering_confidence"], scene=scene_config)

@app.get("/terrain-steering-confidence.json")
def terrain_steering_confidence_json():
    scene_config=default_scene_config()
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(terrain_steering_confidence_context(scene_config,refresh=refresh))

@app.get("/terrain-steering-confidence-image")
def terrain_steering_confidence_image():
    scene_config=default_scene_config(); contract=terrain_steering_confidence_context(scene_config)
    if contract.get("data_state")!="terrain_steering_confidence_cache" or not STEERING_CONFIDENCE_FILE.exists(): return jsonify({"status":"not_available","detail":contract.get("display_label")}),404
    return send_file(STEERING_CONFIDENCE_FILE,mimetype="image/png",max_age=0)

@app.get("/terrain-steering-uncertainty-image")
def terrain_steering_uncertainty_image():
    scene_config=default_scene_config(); contract=terrain_steering_confidence_context(scene_config)
    if contract.get("data_state")!="terrain_steering_confidence_cache" or not STEERING_UNCERTAINTY_FILE.exists(): return jsonify({"status":"not_available","detail":contract.get("display_label")}),404
    return send_file(STEERING_UNCERTAINTY_FILE,mimetype="image/png",max_age=0)


@app.get("/steering-aware-air-volume")
def steering_aware_air_volume():
    scene_config=default_scene_config()
    return render_template("steering_aware_air_volume.html", volume=scene_config["steering_aware_air_volume"], scene=scene_config)

@app.get("/steering-aware-air-volume.json")
def steering_aware_air_volume_json():
    scene_config=default_scene_config()
    return jsonify(scene_config["steering_aware_air_volume"])


@app.get("/terrain-responsive-particle-advection")
def terrain_responsive_particle_advection():
    scene_config = default_scene_config()
    return render_template("terrain_responsive_particle_advection.html", advection=scene_config["terrain_responsive_particle_advection"], scene=scene_config)

@app.get("/terrain-responsive-particle-advection.json")
def terrain_responsive_particle_advection_json():
    scene_config = default_scene_config()
    return jsonify(scene_config["terrain_responsive_particle_advection"])


@app.get("/ridge-spillover-lee-shelter")
def ridge_spillover_lee_shelter():
    scene_config = default_scene_config()
    return render_template("ridge_spillover_shelter.html", ridge=scene_config["ridge_spillover_shelter"], scene=scene_config)

@app.get("/ridge-spillover-lee-shelter.json")
def ridge_spillover_lee_shelter_json():
    scene_config = default_scene_config()
    refresh = request.args.get("refresh", "0").lower() in {"1", "true", "yes"}
    return jsonify(ridge_spillover_shelter_context(scene_config, refresh=refresh))

@app.get("/ridge-spillover-image")
def ridge_spillover_image():
    scene_config = default_scene_config(); contract = ridge_spillover_shelter_context(scene_config)
    if contract.get("data_state") != "ridge_spillover_shelter_cache" or not SPILLOVER_FILE.exists():
        return jsonify({"status":"not_available","detail":contract.get("display_label")}), 404
    return send_file(SPILLOVER_FILE, mimetype="image/png", max_age=0)

@app.get("/lee-side-shelter-image")
def lee_side_shelter_image():
    scene_config = default_scene_config(); contract = ridge_spillover_shelter_context(scene_config)
    if contract.get("data_state") != "ridge_spillover_shelter_cache" or not SHELTER_FILE.exists():
        return jsonify({"status":"not_available","detail":contract.get("display_label")}), 404
    return send_file(SHELTER_FILE, mimetype="image/png", max_age=0)

@app.get("/self-test")
def self_test():
    return render_template("self_test.html", report=run_internal_checks())


@app.get("/self-test.json")
def self_test_json():
    return jsonify(run_internal_checks())


@app.get("/time-alignment")
def time_alignment():
    scene_config = default_scene_config()
    return render_template("time_alignment.html", alignment=scene_config["evidence_time"], scene=scene_config)


@app.get("/time-alignment.json")
def time_alignment_json():
    return jsonify(default_scene_config()["evidence_time"])


@app.get("/observation")
def observation():
    scene_config = default_scene_config()
    return render_template("observation.html", observation=scene_config["observation_contract"], scene=scene_config, atlas=observation_atlas("ventura-oxnard"))


@app.get("/observation.json")
def observation_json():
    return jsonify(default_scene_config()["observation_contract"])


@app.get("/citations")
def citations():
    scene_config = default_scene_config()
    return render_template("citations.html", citations=scene_config["citation_surface"], scene=scene_config)


@app.get("/citations.json")
def citations_json():
    return jsonify(default_scene_config()["citation_surface"])


@app.get("/evidence-states")
def evidence_states():
    scene_config = default_scene_config()
    return render_template("evidence_states.html", vocabulary=scene_config["evidence_vocabulary"], scene=scene_config)


@app.get("/evidence-states.json")
def evidence_states_json():
    return jsonify(default_scene_config()["evidence_vocabulary"])


@app.get("/observation-geometry")
def observation_geometry():
    scene_config = default_scene_config()
    return render_template("observation_geometry.html", geometry=scene_config["observation_geometry"], scene=scene_config)


@app.get("/observation-geometry.json")
def observation_geometry_json():
    return jsonify(default_scene_config()["observation_geometry"])


@app.get("/missing-evidence")
def missing_evidence():
    scene_config = default_scene_config()
    return render_template("missing_evidence.html", missing=scene_config["missing_evidence"], scene=scene_config)


@app.get("/missing-evidence.json")
def missing_evidence_json():
    return jsonify(default_scene_config()["missing_evidence"])



@app.get("/terrain-atmosphere-index")
def terrain_atmosphere_index():
    scene_config=default_scene_config()
    return render_template("terrain_atmosphere_index.html", index=scene_config["terrain_atmosphere_index"], scene=scene_config)

@app.get("/terrain-atmosphere-index.json")
def terrain_atmosphere_index_json():
    scene_config=default_scene_config()
    return jsonify(scene_config["terrain_atmosphere_index"])

@app.get("/evidence")
def evidence():
    packet = build_evidence_packet()
    return render_template("evidence.html", packet=packet)


@app.get("/evidence.json")
def evidence_json():
    return jsonify(build_evidence_packet())


@app.get("/data-status")
def data_status():
    return render_template("data_status.html", registry=get_source_registry())


@app.get("/data-status.json")
def data_status_json():
    return jsonify({"registry": get_source_registry()})


@app.get("/audit")
def audit():
    scene = default_scene_config()
    plume = plume_model_contract()
    return render_template("audit.html", scene=scene, plume=plume)


@app.get("/audit.json")
def audit_json():
    return jsonify({"scene": default_scene_config(), "plume_model": plume_model_contract()})


@app.get("/hunter")
def hunter():
    return render_template("hunter.html", hunter=hunter_lens())


@app.get("/hunter.json")
def hunter_json():
    return jsonify(hunter_lens())


@app.get("/canyon-channeling-drainage-alignment")
def canyon_channeling_page():
    scene_config=default_scene_config()
    return render_template("canyon_channeling.html", channel=scene_config["canyon_channeling"], scene=scene_config)

@app.get("/canyon-channeling-drainage-alignment.json")
def canyon_channeling_json():
    scene_config=default_scene_config(); refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(canyon_channeling_context(scene_config, refresh=refresh))

@app.get("/canyon-channeling-image")
def canyon_channeling_image():
    scene_config=default_scene_config(); contract=canyon_channeling_context(scene_config)
    if contract.get("data_state")!="canyon_channeling_drainage_cache" or not CHANNEL_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(CHANNEL_FILE,mimetype="image/png")

@app.get("/drainage-alignment-image")
def drainage_alignment_image():
    scene_config=default_scene_config(); contract=canyon_channeling_context(scene_config)
    if contract.get("data_state")!="canyon_channeling_drainage_cache" or not DRAINAGE_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(DRAINAGE_FILE,mimetype="image/png")

@app.get("/saddle-transfer-gap-acceleration")
def saddle_transfer_gap_page():
    scene_config=default_scene_config()
    return render_template("saddle_gap_acceleration.html", saddle=scene_config["saddle_gap_acceleration"], scene=scene_config)

@app.get("/saddle-transfer-gap-acceleration.json")
def saddle_transfer_gap_json():
    scene_config=default_scene_config(); refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(saddle_gap_context(scene_config, refresh=refresh))

@app.get("/saddle-transfer-image")
def saddle_transfer_image():
    scene_config=default_scene_config(); contract=saddle_gap_context(scene_config)
    if contract.get("data_state")!="saddle_transfer_gap_cache" or not SADDLE_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(SADDLE_FILE,mimetype="image/png")

@app.get("/gap-acceleration-image")
def gap_acceleration_image():
    scene_config=default_scene_config(); contract=saddle_gap_context(scene_config)
    if contract.get("data_state")!="saddle_transfer_gap_cache" or not GAP_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(GAP_FILE,mimetype="image/png")

@app.get("/basin-retention-cold-air-pooling")
def basin_retention_page():
    scene_config=default_scene_config()
    return render_template("basin_retention_cold_air_pooling.html", basin=scene_config["basin_retention_cold_air_pooling"], scene=scene_config)

@app.get("/basin-retention-cold-air-pooling.json")
def basin_retention_json():
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(basin_retention_context(default_scene_config(), refresh=refresh))

@app.get("/basin-retention-image")
def basin_retention_image():
    contract=basin_retention_context(default_scene_config())
    if contract.get("data_state")!="basin_retention_cold_air_pooling_cache" or not BASIN_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(BASIN_FILE,mimetype="image/png")

@app.get("/cold-air-pooling-image")
def cold_air_pooling_image():
    contract=basin_retention_context(default_scene_config())
    if contract.get("data_state")!="basin_retention_cold_air_pooling_cache" or not COLD_POOL_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(COLD_POOL_FILE,mimetype="image/png")


@app.get("/terrain-convergence-focused-accumulation")
def terrain_convergence_page():
    scene_config=default_scene_config()
    return render_template("terrain_convergence_accumulation.html", convergence=scene_config["terrain_convergence_accumulation"], scene=scene_config)

@app.get("/terrain-convergence-focused-accumulation.json")
def terrain_convergence_json():
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(terrain_convergence_context(default_scene_config(), refresh=refresh))

@app.get("/terrain-convergence-image")
def terrain_convergence_image():
    contract=terrain_convergence_context(default_scene_config())
    if contract.get("data_state")!="terrain_convergence_accumulation_cache" or not CONVERGENCE_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(CONVERGENCE_FILE,mimetype="image/png")

@app.get("/terrain-focused-accumulation-image")
def terrain_focused_accumulation_image():
    contract=terrain_convergence_context(default_scene_config())
    if contract.get("data_state")!="terrain_convergence_accumulation_cache" or not ACCUMULATION_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(ACCUMULATION_FILE,mimetype="image/png")

@app.get("/terrain-divergence-dispersion")
def terrain_divergence_page():
    scene_config=default_scene_config()
    return render_template("terrain_divergence_dispersion.html", divergence=scene_config["terrain_divergence_dispersion"], scene=scene_config)

@app.get("/terrain-divergence-dispersion.json")
def terrain_divergence_json():
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(terrain_divergence_context(default_scene_config(), refresh=refresh))

@app.get("/terrain-divergence-image")
def terrain_divergence_image():
    c=terrain_divergence_context(default_scene_config())
    if c.get("data_state")!="terrain_divergence_dispersion_cache" or not DIVERGENCE_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(DIVERGENCE_FILE,mimetype="image/png")

@app.get("/terrain-dispersion-image")
def terrain_dispersion_image():
    c=terrain_divergence_context(default_scene_config())
    if c.get("data_state")!="terrain_divergence_dispersion_cache" or not DISPERSION_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(DISPERSION_FILE,mimetype="image/png")

@app.get("/terrain-transition-regimes")
def terrain_transition_page():
    scene_config=default_scene_config()
    return render_template("terrain_transition_regimes.html", transitions=scene_config["terrain_transition_regimes"], scene=scene_config)

@app.get("/terrain-transition-regimes.json")
def terrain_transition_json():
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(terrain_transition_context(default_scene_config(), refresh=refresh))

@app.get("/terrain-transition-image")
def terrain_transition_image():
    c=terrain_transition_context(default_scene_config())
    if c.get("data_state")!="terrain_transition_regimes_cache" or not TRANSITION_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(TRANSITION_FILE,mimetype="image/png")

@app.get("/flow-regime-boundary-image")
def flow_regime_boundary_image():
    c=terrain_transition_context(default_scene_config())
    if c.get("data_state")!="terrain_transition_regimes_cache" or not BOUNDARY_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(BOUNDARY_FILE,mimetype="image/png")

@app.get("/terrain-regime-confidence")
def terrain_regime_confidence_page():
    scene_config=default_scene_config()
    return render_template("terrain_regime_confidence.html", regime=scene_config["terrain_regime_confidence"], scene=scene_config)

@app.get("/terrain-regime-confidence.json")
def terrain_regime_confidence_json():
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(terrain_regime_confidence_context(default_scene_config(),refresh=refresh))

@app.get("/terrain-regime-confidence-image")
def terrain_regime_confidence_image():
    c=terrain_regime_confidence_context(default_scene_config())
    if c.get("data_state")!="terrain_regime_confidence_cache" or not REGIME_CONFIDENCE_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(REGIME_CONFIDENCE_FILE,mimetype="image/png")

@app.get("/terrain-boundary-ambiguity-image")
def terrain_boundary_ambiguity_image():
    c=terrain_regime_confidence_context(default_scene_config())
    if c.get("data_state")!="terrain_regime_confidence_cache" or not BOUNDARY_AMBIGUITY_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(BOUNDARY_AMBIGUITY_FILE,mimetype="image/png")

@app.get("/integrated-terrain-response")
def integrated_terrain_response_page():
    scene_config=default_scene_config()
    return render_template("integrated_terrain_response.html", integrated=scene_config["integrated_terrain_response"], scene=scene_config)

@app.get("/integrated-terrain-response.json")
def integrated_terrain_response_json():
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(integrated_terrain_response_context(default_scene_config(),refresh=refresh))

@app.get("/integrated-terrain-response-image")
def integrated_terrain_response_image():
    c=integrated_terrain_response_context(default_scene_config())
    if c.get("data_state")!="integrated_terrain_response_cache" or not INTEGRATED_FIELD_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(INTEGRATED_FIELD_FILE,mimetype="image/png")

@app.get("/integrated-terrain-agreement-image")
def integrated_terrain_agreement_image():
    c=integrated_terrain_response_context(default_scene_config())
    if c.get("data_state")!="integrated_terrain_response_cache" or not INTEGRATED_AGREEMENT_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(INTEGRATED_AGREEMENT_FILE,mimetype="image/png")


@app.get("/integrated-air-volume-orchestration")
def integrated_air_volume_orchestration_page():
    scene_config=default_scene_config()
    return render_template("integrated_air_volume_orchestration.html", volume=scene_config["integrated_air_volume_orchestration"], scene=scene_config)

@app.get("/integrated-air-volume-orchestration.json")
def integrated_air_volume_orchestration_json():
    return jsonify(integrated_air_volume_orchestration_context(default_scene_config()))

@app.get("/integrated-motion-orchestration")
def integrated_motion_orchestration_page():
    scene_config=default_scene_config()
    return render_template("integrated_motion_orchestration.html", orchestration=scene_config["integrated_motion_orchestration"], scene=scene_config)

@app.get("/integrated-motion-orchestration.json")
def integrated_motion_orchestration_json():
    return jsonify(integrated_motion_orchestration_context(default_scene_config()))

@app.get("/integrated-response-authority")
def integrated_response_authority_page():
    scene_config=default_scene_config()
    return render_template("integrated_response_authority.html", authority=scene_config["integrated_response_authority"], scene=scene_config)

@app.get("/integrated-response-authority.json")
def integrated_response_authority_json():
    refresh=request.args.get("refresh","0").lower() in {"1","true","yes"}
    return jsonify(integrated_response_authority_context(default_scene_config(),refresh=refresh))

@app.get("/integrated-response-authority-image")
def integrated_response_authority_image():
    c=integrated_response_authority_context(default_scene_config())
    if c.get("data_state")!="integrated_response_authority_cache" or not RESPONSE_AUTHORITY_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(RESPONSE_AUTHORITY_FILE,mimetype="image/png")

@app.get("/integrated-response-conflict-image")
def integrated_response_conflict_image():
    c=integrated_response_authority_context(default_scene_config())
    if c.get("data_state")!="integrated_response_authority_cache" or not RESPONSE_CONFLICT_FILE.exists(): return jsonify({"status":"unavailable"}),404
    return send_file(RESPONSE_CONFLICT_FILE,mimetype="image/png")


@app.get("/evidence-guided-focus-depth")
def evidence_guided_focus_depth_page():
    scene_config=default_scene_config()
    return render_template("evidence_guided_focus_depth.html", focus=scene_config["evidence_guided_focus_depth"], scene=scene_config)

@app.get("/evidence-guided-focus-depth.json")
def evidence_guided_focus_depth_json():
    return jsonify(default_scene_config()["evidence_guided_focus_depth"])



@app.get("/atmospheric-light-legibility")
def atmospheric_light_legibility_page():
    scene_config = default_scene_config()
    return render_template("atmospheric_light_legibility.html", lighting=scene_config["atmospheric_light_legibility"], scene=scene_config)

@app.get("/atmospheric-light-legibility.json")
def atmospheric_light_legibility_json():
    return jsonify(default_scene_config()["atmospheric_light_legibility"])

@app.get("/evidence-visual-hierarchy")
def evidence_visual_hierarchy_page():
    scene_config = default_scene_config()
    return render_template("evidence_visual_hierarchy.html", hierarchy=scene_config["evidence_visual_hierarchy"], scene=scene_config)

@app.get("/evidence-visual-hierarchy.json")
def evidence_visual_hierarchy_json():
    return jsonify(default_scene_config()["evidence_visual_hierarchy"])


@app.get("/scientific-annotation-choreography")
def scientific_annotation_choreography_page():
    scene_config=default_scene_config()
    return render_template("scientific_annotation_choreography.html", annotations=scene_config["scientific_annotation_choreography"], scene=scene_config)

@app.get("/scientific-annotation-choreography.json")
def scientific_annotation_choreography_json():
    return jsonify(default_scene_config()["scientific_annotation_choreography"])

@app.get("/scientific-storytelling-timeline")
def scientific_storytelling_timeline_page():
    scene_config=default_scene_config()
    return render_template("scientific_storytelling_timeline.html", timeline=scene_config["scientific_storytelling_timeline"], scene=scene_config)

@app.get("/scientific-storytelling-timeline.json")
def scientific_storytelling_timeline_json():
    return jsonify(default_scene_config()["scientific_storytelling_timeline"])


@app.get("/reviewer-guided-evidence-exploration")
def reviewer_guided_evidence_exploration_page():
    scene_config = default_scene_config()
    return render_template("reviewer_guided_exploration.html", exploration=scene_config["reviewer_guided_exploration"], scene=scene_config)

@app.get("/reviewer-guided-evidence-exploration.json")
def reviewer_guided_evidence_exploration_json():
    return jsonify(default_scene_config()["reviewer_guided_exploration"])


@app.get("/progressive-disclosure")
def progressive_disclosure_page():
    scene_config = default_scene_config()
    return render_template("progressive_disclosure.html", disclosure=scene_config["progressive_disclosure"], scene=scene_config)

@app.get("/progressive-disclosure.json")
def progressive_disclosure_json():
    return jsonify(default_scene_config()["progressive_disclosure"])


@app.get("/scientific-synthesis")
def scientific_synthesis_page():
    scene_config = default_scene_config()
    return render_template("scientific_synthesis_decision_surface.html", synthesis=scene_config["scientific_synthesis_decision_surface"], scene=scene_config)

@app.get("/scientific-synthesis.json")
def scientific_synthesis_json():
    return jsonify(default_scene_config()["scientific_synthesis_decision_surface"])


@app.get("/level-five-visual-composition")
def level_five_visual_composition_page():
    scene_config = default_scene_config()
    return render_template("level_five_visual_composition.html", composition=scene_config["level_five_visual_composition"], scene=scene_config)

@app.get("/level-five-visual-composition.json")
def level_five_visual_composition_json():
    return jsonify(default_scene_config()["level_five_visual_composition"])



@app.get("/integrated-scene-coherence")
def integrated_scene_coherence_page():
    scene_config=default_scene_config()
    return render_template("integrated_scene_coherence.html", coherence=scene_config["integrated_scene_coherence"], scene=scene_config)

@app.get("/integrated-scene-coherence.json")
def integrated_scene_coherence_json():
    return jsonify(default_scene_config()["integrated_scene_coherence"])

@app.get("/scientific-cinematic-camera")
def scientific_cinematic_camera_page():
    scene_config=default_scene_config()
    return render_template("scientific_cinematic_camera.html", camera=scene_config["scientific_cinematic_camera"], scene=scene_config)

@app.get("/scientific-cinematic-camera.json")
def scientific_cinematic_camera_json():
    return jsonify(default_scene_config()["scientific_cinematic_camera"])


@app.get("/release-proof")
def release_proof_page():
    scene_config = default_scene_config()
    return render_template("release_proof.html", release=scene_config["final_release_audit"], scene=scene_config)


@app.get("/release-proof.json")
def release_proof_json():
    return jsonify(default_scene_config()["final_release_audit"])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
