from __future__ import annotations

from engine.air_volume import build_air_volume
from engine.living_wind import build_living_wind
from engine.evidence_time import build_evidence_time_alignment
from engine.observation_contract import build_observation_contract
from engine.citation_surface import build_citation_surface
from engine.evidence_vocabulary import build_evidence_vocabulary
from engine.missing_evidence import build_missing_evidence
from engine.observation_geometry import build_observation_geometry_adapter
from engine.basemap_surface import basemap_context
from engine.provenance import boundary_pack
from engine.source_registry import get_source_registry
from engine.spatial_plume import build_plume_geometry, destination_point
from engine.terrain_loader import terrain_context
from engine.full_dem import full_dem_context
from engine.hillshade import hillshade_context
from engine.slope_aspect import slope_aspect_context
from engine.landform_classification import landform_context
from engine.terrain_confidence import terrain_confidence_context
from engine.historical_weather import historical_weather_context
from engine.multi_level_wind import multi_level_wind_context
from engine.atmospheric_stability import atmospheric_stability_context
from engine.boundary_layer_depth import boundary_layer_depth_context
from engine.gust_variability import gust_variability_context
from engine.terrain_atmosphere_index import terrain_atmosphere_index_context
from engine.terrain_steering_field import terrain_steering_field_context
from engine.terrain_steering_confidence import terrain_steering_confidence_context
from engine.steering_aware_air_volume import build_steering_aware_air_volume
from engine.terrain_responsive_particle_advection import build_terrain_responsive_particle_advection
from engine.ridge_spillover_shelter import ridge_spillover_shelter_context
from engine.canyon_channeling import canyon_channeling_context
from engine.saddle_gap_acceleration import saddle_gap_context
from engine.basin_retention_cold_air_pooling import basin_retention_context
from engine.terrain_convergence_accumulation import terrain_convergence_context
from engine.terrain_divergence_dispersion import terrain_divergence_context
from engine.terrain_transition_regimes import terrain_transition_context
from engine.terrain_regime_confidence import terrain_regime_confidence_context
from engine.integrated_terrain_response import integrated_terrain_response_context
from engine.integrated_response_authority import integrated_response_authority_context
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
from engine.terrain_lighting import build_terrain_lighting
from engine.terrain_plume_behavior import terrain_affected_behavior
from engine.terrain_flow_path import build_terrain_flow_path
from engine.wind_loader import wind_context


def default_scene_config(refresh_wind: bool = False, refresh_terrain: bool = False, refresh_dem: bool = False, refresh_hillshade: bool = False, refresh_slope_aspect: bool = False, refresh_landforms: bool = False, refresh_terrain_confidence: bool = False, refresh_historical_weather: bool = False, refresh_multi_level_wind: bool = False, refresh_atmospheric_stability: bool = False, refresh_boundary_layer_depth: bool = False, refresh_gust_variability: bool = False) -> dict:
    """Build the frozen SV2-57 Level Five proof-release scene."""
    basemap = basemap_context()
    center = basemap["center"]
    wind = wind_context(center["lat"], center["lon"], refresh=refresh_wind)

    scene = {
        "scene_id": "case02_level_five_proof_release",
        "project_name": "Atmosphere Window",
        "strategic_name": "Invisible Air",
        "build_label": "SV2-57 · Final Scientific Audit and Proof Release",
        "headline": "Look into the hidden air.",
        "subhead": "A reported methane signal becomes visible as current wind, measured land, and uncertainty move together.",
        "scene_line": "A reported observation record over measured terrain, with confidence-gated terrain divergence and dispersion potential kept explicit and source-aware.",
        "location": {
            "label": basemap["display_place"],
            "lat": center["lat"],
            "lon": center["lon"],
            "bbox": [-119.33, 34.12, -118.77, 34.43],
            "display_note": "U.S. terrain-capable test geography. The map is orientation context only, not a methane observation.",
        },
        "observation": {
            "mode": "source_seeded",
            "gas": "methane",
            "display": "Reported methane signal",
            "geometry_status": "coordinate-registered visual reconstruction",
            "detected_by_app": False,
            "timestamp": None,
            "timestamp_status": "unresolved_until_source_manifest_is_loaded",
        },
        "basemap": basemap,
        "wind": wind,
        "boundary_pack": boundary_pack(),
        "source_registry": get_source_registry(),
    }

    terrain = terrain_context(scene, refresh=refresh_terrain)
    full_dem = full_dem_context(scene, refresh=refresh_dem)
    hillshade = hillshade_context(scene, refresh=refresh_hillshade)
    slope_aspect = slope_aspect_context(scene, refresh=refresh_slope_aspect)
    landforms = landform_context(scene, refresh=refresh_landforms)
    terrain_confidence = terrain_confidence_context(scene, refresh=refresh_terrain_confidence)
    behavior = terrain_affected_behavior(terrain, wind["to_degrees"])
    terrain_lighting = build_terrain_lighting(terrain)
    source_seed = basemap["source_seed_point"]
    observation_contract = build_observation_contract(source_seed)
    scene["observation_contract"] = observation_contract
    scene["observation"]["timestamp"] = observation_contract["reported_time_utc"]
    scene["observation"]["timestamp_status"] = observation_contract["data_state"]
    historical_weather = historical_weather_context(observation_contract, center["lat"], center["lon"], refresh=refresh_historical_weather)
    multi_level_wind = multi_level_wind_context(observation_contract, center["lat"], center["lon"], refresh=refresh_multi_level_wind)
    atmospheric_stability = atmospheric_stability_context(observation_contract, center["lat"], center["lon"], refresh=refresh_atmospheric_stability)
    boundary_layer_depth = boundary_layer_depth_context(observation_contract, center["lat"], center["lon"], refresh=refresh_boundary_layer_depth)
    gust_variability = gust_variability_context(observation_contract, center["lat"], center["lon"], refresh=refresh_gust_variability)
    terrain_atmosphere_index = terrain_atmosphere_index_context(terrain, landforms, terrain_confidence, wind, atmospheric_stability, boundary_layer_depth, gust_variability)
    terrain_steering_field = terrain_steering_field_context({**scene, "full_dem": full_dem, "wind": wind})
    terrain_steering_confidence = terrain_steering_confidence_context({**scene, "full_dem": full_dem, "wind": wind, "terrain_confidence": terrain_confidence, "terrain_steering_field": terrain_steering_field, "gust_variability": gust_variability, "atmospheric_stability": atmospheric_stability, "observation_contract": observation_contract})
    visual_bearing = wind["to_degrees"] + behavior["bend_degrees"]
    flow_path = build_terrain_flow_path(
        source_seed,
        visual_bearing,
        length_km=23.0 * behavior["length_multiplier"],
        terrain=terrain,
    )
    plume = build_plume_geometry(
        source_seed,
        visual_bearing,
        length_km=23.0 * behavior["length_multiplier"],
        width_km=5.8 * behavior["width_multiplier"],
        flow_path=flow_path,
    )
    air_volume_base = build_air_volume(behavior, flow_path)
    air_volume = build_steering_aware_air_volume(air_volume_base, terrain_steering_field, terrain_steering_confidence, terrain_atmosphere_index, wind)
    living_wind = build_living_wind(wind, behavior, flow_path)
    particle_advection = build_terrain_responsive_particle_advection(terrain_steering_field, terrain_steering_confidence, air_volume, living_wind, gust_variability)
    ridge_spillover_shelter = ridge_spillover_shelter_context({**scene, "full_dem": full_dem, "wind": wind, "terrain_steering_confidence": terrain_steering_confidence})
    canyon_channeling = canyon_channeling_context({**scene, "full_dem": full_dem, "wind": wind, "terrain_steering_confidence": terrain_steering_confidence})
    scene["canyon_channeling"] = canyon_channeling
    saddle_gap = saddle_gap_context(scene)
    scene["saddle_gap_acceleration"] = saddle_gap
    basin_retention = basin_retention_context({**scene, "full_dem": full_dem, "terrain_steering_confidence": terrain_steering_confidence, "atmospheric_stability": atmospheric_stability})
    scene["basin_retention_cold_air_pooling"] = basin_retention
    terrain_convergence = terrain_convergence_context({**scene, "full_dem": full_dem, "terrain_steering_confidence": terrain_steering_confidence, "terrain_steering_field": terrain_steering_field, "basin_retention_cold_air_pooling": basin_retention})
    scene["terrain_convergence_accumulation"] = terrain_convergence
    terrain_divergence = terrain_divergence_context({**scene, "full_dem": full_dem, "terrain_steering_confidence": terrain_steering_confidence, "terrain_steering_field": terrain_steering_field, "terrain_convergence_accumulation": terrain_convergence})
    scene["terrain_divergence_dispersion"] = terrain_divergence
    terrain_transitions = terrain_transition_context({**scene, "full_dem": full_dem, "terrain_steering_confidence": terrain_steering_confidence, "terrain_convergence_accumulation": terrain_convergence, "terrain_divergence_dispersion": terrain_divergence, "canyon_channeling": canyon_channeling, "ridge_spillover_shelter": ridge_spillover_shelter, "basin_retention_cold_air_pooling": basin_retention})
    scene["terrain_transition_regimes"] = terrain_transitions
    terrain_regime_confidence = terrain_regime_confidence_context({**scene, "full_dem": full_dem, "terrain_transition_regimes": terrain_transitions, "terrain_steering_confidence": terrain_steering_confidence})
    scene["terrain_regime_confidence"] = terrain_regime_confidence
    integrated_terrain_response = integrated_terrain_response_context({**scene, "full_dem": full_dem, "terrain_regime_confidence": terrain_regime_confidence, "terrain_transition_regimes": terrain_transitions, "terrain_convergence_accumulation": terrain_convergence, "terrain_divergence_dispersion": terrain_divergence})
    scene["integrated_terrain_response"] = integrated_terrain_response
    integrated_response_authority = integrated_response_authority_context({**scene, "integrated_terrain_response": integrated_terrain_response})
    scene["integrated_response_authority"] = integrated_response_authority
    integrated_motion_orchestration = integrated_motion_orchestration_context({**scene, "integrated_response_authority": integrated_response_authority, "integrated_terrain_response": integrated_terrain_response, "terrain_regime_confidence": terrain_regime_confidence})
    scene["integrated_motion_orchestration"] = integrated_motion_orchestration
    integrated_air_volume_orchestration = integrated_air_volume_orchestration_context({**scene, "integrated_response_authority": integrated_response_authority, "integrated_motion_orchestration": integrated_motion_orchestration, "integrated_terrain_response": integrated_terrain_response, "terrain_regime_confidence": terrain_regime_confidence})
    scene["integrated_air_volume_orchestration"] = integrated_air_volume_orchestration
    integrated_scene_coherence = integrated_scene_coherence_context({**scene, "integrated_motion_orchestration": integrated_motion_orchestration, "integrated_air_volume_orchestration": integrated_air_volume_orchestration, "integrated_response_authority": integrated_response_authority})
    scene["integrated_scene_coherence"] = integrated_scene_coherence
    scientific_camera = scientific_cinematic_camera_context({**scene, "integrated_scene_coherence": integrated_scene_coherence, "integrated_response_authority": integrated_response_authority, "integrated_terrain_response": integrated_terrain_response})
    scene["scientific_cinematic_camera"] = scientific_camera
    evidence_focus_depth = evidence_guided_focus_depth_context({**scene, "scientific_cinematic_camera": scientific_camera, "integrated_response_authority": integrated_response_authority, "integrated_terrain_response": integrated_terrain_response, "terrain_regime_confidence": terrain_regime_confidence})
    scene["evidence_guided_focus_depth"] = evidence_focus_depth
    atmospheric_light_legibility = atmospheric_light_legibility_context({**scene, "evidence_guided_focus_depth": evidence_focus_depth, "scientific_cinematic_camera": scientific_camera, "integrated_response_authority": integrated_response_authority, "terrain_regime_confidence": terrain_regime_confidence, "terrain_confidence": terrain_confidence})
    scene["atmospheric_light_legibility"] = atmospheric_light_legibility
    evidence_visual_hierarchy = evidence_visual_hierarchy_context({**scene, "atmospheric_light_legibility": atmospheric_light_legibility, "evidence_guided_focus_depth": evidence_focus_depth, "integrated_response_authority": integrated_response_authority})
    scene["evidence_visual_hierarchy"] = evidence_visual_hierarchy
    scientific_annotations = scientific_annotation_choreography_context({**scene, "evidence_visual_hierarchy": evidence_visual_hierarchy, "integrated_scene_coherence": integrated_scene_coherence})
    scene["scientific_annotation_choreography"] = scientific_annotations
    storytelling_timeline = scientific_storytelling_timeline_context({**scene, "scientific_annotation_choreography": scientific_annotations, "integrated_scene_coherence": integrated_scene_coherence, "evidence_visual_hierarchy": evidence_visual_hierarchy})
    scene["scientific_storytelling_timeline"] = storytelling_timeline
    reviewer_exploration = reviewer_guided_exploration_context({**scene, "scientific_annotation_choreography": scientific_annotations, "scientific_storytelling_timeline": storytelling_timeline})
    scene["reviewer_guided_exploration"] = reviewer_exploration
    progressive_disclosure = progressive_disclosure_context({**scene, "reviewer_guided_exploration": reviewer_exploration})
    scene["progressive_disclosure"] = progressive_disclosure
    scientific_synthesis = scientific_synthesis_decision_surface_context(scene)
    scene["scientific_synthesis_decision_surface"] = scientific_synthesis
    level_five_composition = level_five_visual_composition_context(scene)
    scene["level_five_visual_composition"] = level_five_composition
    evidence_time = build_evidence_time_alignment(scene["observation"], wind, historical_weather)
    scene["evidence_time"] = evidence_time
    final_release_audit = final_release_audit_context({**scene, "observation_contract": observation_contract, "terrain_confidence": terrain_confidence, "evidence_time": evidence_time, "integrated_terrain_response": integrated_terrain_response, "progressive_disclosure": progressive_disclosure, "scientific_synthesis_decision_surface": scientific_synthesis, "level_five_visual_composition": level_five_composition, "missing_evidence": build_missing_evidence(scene)})
    scene["final_release_audit"] = final_release_audit
    plume["terrain_behavior"] = behavior
    basemap["plume_geometry"] = plume
    basemap["terrain_lighting"] = terrain_lighting
    basemap["hillshade"] = hillshade
    basemap["slope_aspect"] = slope_aspect
    basemap["landforms"] = landforms
    basemap["terrain_confidence"] = terrain_confidence
    basemap["terrain_steering_field"] = terrain_steering_field
    basemap["terrain_steering_confidence"] = terrain_steering_confidence
    basemap["terrain_convergence_accumulation"] = terrain_convergence
    basemap["terrain_divergence_dispersion"] = terrain_divergence
    basemap["terrain_transition_regimes"] = terrain_transitions
    basemap["terrain_regime_confidence"] = terrain_regime_confidence
    basemap["integrated_response_authority"] = integrated_response_authority
    basemap["integrated_motion_orchestration"] = integrated_motion_orchestration
    basemap["integrated_air_volume_orchestration"] = integrated_air_volume_orchestration
    basemap["integrated_scene_coherence"] = integrated_scene_coherence
    basemap["scientific_cinematic_camera"] = scientific_camera
    basemap["evidence_guided_focus_depth"] = evidence_focus_depth
    basemap["atmospheric_light_legibility"] = atmospheric_light_legibility
    basemap["evidence_visual_hierarchy"] = evidence_visual_hierarchy
    basemap["scientific_annotation_choreography"] = scientific_annotations
    basemap["scientific_storytelling_timeline"] = storytelling_timeline
    basemap["reviewer_guided_exploration"] = reviewer_exploration
    basemap["progressive_disclosure"] = progressive_disclosure
    basemap["scientific_synthesis_decision_surface"] = scientific_synthesis
    basemap["level_five_visual_composition"] = level_five_composition
    basemap["final_release_audit"] = final_release_audit
    basemap["downwind_context_point"] = {
        **destination_point(source_seed["lat"], source_seed["lon"], wind["to_degrees"], 27.5),
        "label": "current-wind downwind orientation context",
    }

    scene["full_dem"] = full_dem
    scene["hillshade"] = hillshade
    scene["slope_aspect"] = slope_aspect
    scene["landforms"] = landforms
    scene["terrain_confidence"] = terrain_confidence
    scene["historical_weather"] = historical_weather
    scene["multi_level_wind"] = multi_level_wind
    scene["atmospheric_stability"] = atmospheric_stability
    scene["boundary_layer_depth"] = boundary_layer_depth
    scene["gust_variability"] = gust_variability
    scene["terrain_atmosphere_index"] = terrain_atmosphere_index
    scene["terrain_steering_field"] = terrain_steering_field
    scene["terrain_steering_confidence"] = terrain_steering_confidence
    scene["steering_aware_air_volume"] = air_volume
    scene["terrain_responsive_particle_advection"] = particle_advection
    scene["ridge_spillover_shelter"] = ridge_spillover_shelter
    scene["canyon_channeling"] = canyon_channeling
    scene["observation_geometry"] = build_observation_geometry_adapter(observation_contract)
    scene["observation"]["geometry_status"] = scene["observation_geometry"]["geometry_state"]
    scene["citation_surface"] = build_citation_surface(scene)
    scene["evidence_vocabulary"] = build_evidence_vocabulary(scene)
    scene["missing_evidence"] = build_missing_evidence(scene)

    scene.update({
        "terrain": terrain,
        "full_dem": full_dem,
        "hillshade": hillshade,
        "slope_aspect": slope_aspect,
        "landforms": landforms,
        "terrain_confidence": terrain_confidence,
        "historical_weather": historical_weather,
        "multi_level_wind": multi_level_wind,
        "atmospheric_stability": atmospheric_stability,
        "boundary_layer_depth": boundary_layer_depth,
        "gust_variability": gust_variability,
        "terrain_atmosphere_index": terrain_atmosphere_index,
        "terrain_steering_field": terrain_steering_field,
        "terrain_steering_confidence": terrain_steering_confidence,
        "steering_aware_air_volume": air_volume,
        "terrain_responsive_particle_advection": particle_advection,
        "ridge_spillover_shelter": ridge_spillover_shelter,
        "canyon_channeling": canyon_channeling,
            "saddle_gap_acceleration": saddle_gap,
            "terrain_convergence_accumulation": terrain_convergence,
            "terrain_divergence_dispersion": terrain_divergence,
            "terrain_transition_regimes": terrain_transitions,
            "terrain_regime_confidence": terrain_regime_confidence,
            "integrated_terrain_response": integrated_terrain_response,
            "integrated_response_authority": integrated_response_authority,
            "integrated_motion_orchestration": integrated_motion_orchestration,
            "integrated_air_volume_orchestration": integrated_air_volume_orchestration,
            "integrated_scene_coherence": integrated_scene_coherence,
            "scientific_cinematic_camera": scientific_camera,
            "evidence_guided_focus_depth": evidence_focus_depth,
            "atmospheric_light_legibility": atmospheric_light_legibility,
            "evidence_visual_hierarchy": evidence_visual_hierarchy,
            "scientific_annotation_choreography": scientific_annotations,
            "scientific_storytelling_timeline": storytelling_timeline,
            "reviewer_guided_exploration": reviewer_exploration,
        "terrain_plume_behavior": behavior,
        "terrain_lighting": terrain_lighting,
        "air_volume": air_volume,
        "living_wind": living_wind,
        "evidence_time": evidence_time,
        "observation_contract": observation_contract,
        "plume_visualization": {
            "mode": "layered_air_volume_map_registered_reconstruction",
            "particle_count": 260,
            "air_volume": air_volume,
            "particle_advection": particle_advection,
            "ridge_spillover_shelter": ridge_spillover_shelter,
        "canyon_channeling": canyon_channeling,
            "saddle_gap_acceleration": saddle_gap,
            "terrain_convergence_accumulation": terrain_convergence,
            "terrain_divergence_dispersion": terrain_divergence,
            "terrain_transition_regimes": terrain_transitions,
            "terrain_regime_confidence": terrain_regime_confidence,
            "integrated_terrain_response": integrated_terrain_response,
            "integrated_response_authority": integrated_response_authority,
            "integrated_motion_orchestration": integrated_motion_orchestration,
            "integrated_air_volume_orchestration": integrated_air_volume_orchestration,
            "integrated_scene_coherence": integrated_scene_coherence,
            "scientific_cinematic_camera": scientific_camera,
            "evidence_guided_focus_depth": evidence_focus_depth,
            "atmospheric_light_legibility": atmospheric_light_legibility,
            "evidence_visual_hierarchy": evidence_visual_hierarchy,
            "living_wind": living_wind,
        "evidence_time": evidence_time,
            "spread": 0.42 * behavior["width_multiplier"],
            "opacity": 0.68,
            "geometry": plume,
            "wind_state": wind["data_state"],
            "terrain_state": behavior["data_state"],
            "flow_state": flow_path["data_state"],
            "terrain_response": flow_path["terrain_response"],
            "boundary": "Present-day-wind-responsive, measured-terrain-informed layered air visualization; not observation-time transport, a measured turbulence field, measured concentration, exact methane plume-product geometry, or a dispersion model.",
        },
        "hunter_prompts": [
            {"label": "Air", "question": "Does current wind make the direction plausible, while observation-time wind remains unresolved?"},
            {"label": "Land", "question": "Does measured relief suggest widening, channeling, or disruption worth human review?"},
            {"label": "Context", "question": "What nearby map context helps orientation without blame?"},
            {"label": "Time", "question": "Is current weather being mistaken for observation-time weather?"},
            {"label": "Unknowns", "question": "What missing layer still controls the review?"},
        ],
    })
    return scene
