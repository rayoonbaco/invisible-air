from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "http://127.0.0.1:8000"
TERRAIN_TRANSITION_REFRESH_URL = BASE_URL + "/terrain-transition-regimes.json?refresh=1"
TERRAIN_REGIME_CONFIDENCE_REFRESH_URL = BASE_URL + "/terrain-regime-confidence.json?refresh=1"
INTEGRATED_TERRAIN_RESPONSE_REFRESH_URL = BASE_URL + "/integrated-terrain-response.json?refresh=1"
HEALTH_URL = f"{BASE_URL}/health"
SCENE_URL = f"{BASE_URL}/scene"
SELF_TEST_URL = f"{BASE_URL}/self-test"
OBSERVATION_URL = f"{BASE_URL}/observation"
CITATIONS_URL = f"{BASE_URL}/citations"
EVIDENCE_STATES_URL = f"{BASE_URL}/evidence-states"
MISSING_EVIDENCE_URL = f"{BASE_URL}/missing-evidence"
OBSERVATION_GEOMETRY_URL = f"{BASE_URL}/observation-geometry"
DEM_URL = f"{BASE_URL}/dem"
DEM_REFRESH_URL = f"{BASE_URL}/dem.json?refresh=1"
HILLSHADE_URL = f"{BASE_URL}/hillshade"
HILLSHADE_REFRESH_URL = f"{BASE_URL}/hillshade.json?refresh=1"
SLOPE_ASPECT_URL = f"{BASE_URL}/slope-aspect"
SLOPE_ASPECT_REFRESH_URL = f"{BASE_URL}/slope-aspect.json?refresh=1"
LANDFORMS_URL = f"{BASE_URL}/landforms"
LANDFORMS_REFRESH_URL = f"{BASE_URL}/landforms.json?refresh=1"
TERRAIN_CONFIDENCE_URL = f"{BASE_URL}/terrain-confidence"
TERRAIN_CONFIDENCE_REFRESH_URL = f"{BASE_URL}/terrain-confidence.json?refresh=1"
HISTORICAL_WEATHER_URL = f"{BASE_URL}/historical-weather"
HISTORICAL_WEATHER_REFRESH_URL = f"{BASE_URL}/historical-weather.json?refresh=1"
MULTI_LEVEL_WIND_URL = f"{BASE_URL}/multi-level-wind"
MULTI_LEVEL_WIND_REFRESH_URL = f"{BASE_URL}/multi-level-wind.json?refresh=1"
ATMOSPHERIC_STABILITY_REFRESH_URL = f"{BASE_URL}/atmospheric-stability.json?refresh=1"
BOUNDARY_LAYER_DEPTH_REFRESH_URL = f"{BASE_URL}/boundary-layer-depth.json?refresh=1"
GUST_VARIABILITY_REFRESH_URL = f"{BASE_URL}/gust-variability.json?refresh=1"
TERRAIN_STEERING_FIELD_REFRESH_URL = f"{BASE_URL}/terrain-steering-field.json?refresh=1"
TERRAIN_STEERING_CONFIDENCE_REFRESH_URL = f"{BASE_URL}/terrain-steering-confidence.json?refresh=1"
CANYON_CHANNELING_REFRESH_URL = f"{BASE_URL}/canyon-channeling-drainage-alignment.json?refresh=1"
SADDLE_GAP_REFRESH_URL = f"{BASE_URL}/saddle-transfer-gap-acceleration.json?refresh=1"
BASIN_RETENTION_REFRESH_URL = f"{BASE_URL}/basin-retention-cold-air-pooling.json?refresh=1"
TERRAIN_CONVERGENCE_REFRESH_URL = f"{BASE_URL}/terrain-convergence-focused-accumulation.json?refresh=1"
TERRAIN_REFRESH_URL = f"{BASE_URL}/terrain.json?refresh=1"


def read_json(url: str, timeout: float) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, urllib.error.URLError):
        return None


def server_ready(timeout: float = 1.0) -> bool:
    payload = read_json(HEALTH_URL, timeout)
    return bool(payload and payload.get("status") == "ok")


def start_server() -> subprocess.Popen:
    env = os.environ.copy()
    env["AW_DISABLE_LIVE_FETCH"] = "0"
    kwargs: dict = {"cwd": str(ROOT), "env": env}
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_CONSOLE
    else:
        kwargs["stdout"] = subprocess.DEVNULL
        kwargs["stderr"] = subprocess.DEVNULL
        kwargs["start_new_session"] = True
    return subprocess.Popen([sys.executable, "app.py"], **kwargs)


def wait_for_server(seconds: int = 60) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if server_ready(timeout=1.5):
            return True
        time.sleep(1)
    return False


def prepare_dem(timeout: int = 70) -> dict:
    print("Preparing continuous USGS 3DEP DEM before opening the scene...")
    payload = read_json(DEM_REFRESH_URL, timeout)
    if not payload:
        return {"ready": False, "label": "DEM request unavailable; sparse terrain retained"}
    return {"ready": payload.get("data_state") == "continuous_dem_cache", "label": payload.get("display_label", "DEM state unknown"), "bytes": payload.get("byte_size", 0)}


def prepare_hillshade(timeout: int = 60) -> dict:
    print("Deriving reproducible hillshade from the validated DEM...")
    payload = read_json(HILLSHADE_REFRESH_URL, timeout)
    if not payload:
        return {"ready": False, "label": "hillshade request unavailable"}
    return {
        "ready": payload.get("data_state") == "dem_derived_hillshade_cache",
        "label": payload.get("display_label", "hillshade state unknown"),
        "bytes": payload.get("byte_size", 0),
    }


def prepare_slope_aspect(timeout: int = 60) -> dict:
    print("Deriving continuous slope and aspect from the validated DEM...")
    payload = read_json(SLOPE_ASPECT_REFRESH_URL, timeout)
    if not payload:
        return {"ready": False, "label": "slope/aspect request unavailable"}
    return {"ready": payload.get("data_state") == "dem_derived_slope_aspect_cache", "label": payload.get("display_label", "slope/aspect state unknown")}


def prepare_landforms(timeout: int = 60) -> dict:
    print("Classifying DEM-derived landforms...")
    payload=read_json(LANDFORMS_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"label":"landform request unavailable"}
    return {"ready":payload.get("data_state")=="dem_derived_landform_cache","label":payload.get("display_label","landform state unknown")}


def prepare_terrain_confidence(timeout: int = 60) -> dict:
    print("Scoring terrain evidence confidence...")
    payload=read_json(TERRAIN_CONFIDENCE_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"label":"terrain-confidence request unavailable"}
    return {"ready":payload.get("data_state")=="terrain_confidence_ready","label":payload.get("display_label","terrain-confidence state unknown")}


def prepare_historical_weather(timeout: int = 30) -> dict:
    print("Retrieving observation-time historical weather when the evidence clock allows it...")
    payload=read_json(HISTORICAL_WEATHER_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"historical weather request unavailable"}
    ready=payload.get("data_state")=="historical_weather_cache"
    safe=payload.get("data_state") in {"observation_time_unresolved","observation_time_in_future","provider_unavailable_no_historical_cache"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","historical weather state unknown"),"state":payload.get("data_state")}


def prepare_multi_level_wind(timeout: int = 30) -> dict:
    print("Retrieving 10 m and 100 m historical wind when the evidence clock allows it...")
    payload=read_json(MULTI_LEVEL_WIND_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"multi-level wind request unavailable"}
    ready=payload.get("data_state")=="multi_level_wind_cache"
    safe=payload.get("data_state") in {"observation_time_unresolved","observation_time_in_future","provider_unavailable_no_multi_level_cache"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","multi-level wind state unknown"),"state":payload.get("data_state")}


def prepare_atmospheric_stability(timeout: int = 30) -> dict:
    print("Screening atmospheric stability when the evidence clock allows it...")
    payload=read_json(ATMOSPHERIC_STABILITY_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"atmospheric stability request unavailable"}
    ready=payload.get("data_state")=="atmospheric_stability_screen"
    safe=payload.get("data_state") in {"observation_time_unresolved","observation_time_in_future","provider_unavailable_no_stability_cache"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","atmospheric stability state unknown"),"state":payload.get("data_state")}


def prepare_boundary_layer_depth(timeout: int = 30) -> dict:
    print("Retrieving observation-time boundary-layer depth when the evidence clock allows it...")
    payload=read_json(BOUNDARY_LAYER_DEPTH_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"boundary-layer depth request unavailable"}
    ready=payload.get("data_state")=="boundary_layer_depth_cache"
    safe=payload.get("data_state") in {"observation_time_unresolved","observation_time_in_future","provider_unavailable_no_boundary_layer_cache"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","boundary-layer depth state unknown"),"state":payload.get("data_state")}


def prepare_gust_variability(timeout: int = 30) -> dict:
    print("Retrieving observation-time gust and short-window variability when the evidence clock allows it...")
    payload=read_json(GUST_VARIABILITY_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"gust variability request unavailable"}
    ready=payload.get("data_state")=="gust_variability_window_cache"
    safe=payload.get("data_state") in {"observation_time_unresolved","observation_time_in_future","provider_unavailable_no_variability_cache"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","gust variability state unknown"),"state":payload.get("data_state")}


def prepare_terrain_steering_field(timeout: int = 45) -> dict:
    print("Deriving map-registered terrain steering field from the validated DEM and available wind context...")
    payload=read_json(TERRAIN_STEERING_FIELD_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"terrain steering field request unavailable"}
    ready=payload.get("data_state")=="terrain_steering_field_cache"
    safe=payload.get("data_state") in {"steering_field_unavailable_safe","steering_field_generation_failed"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","terrain steering field state unknown"),"state":payload.get("data_state")}



def prepare_terrain_steering_confidence(timeout: int = 45) -> dict:
    print("Scoring spatial steering-field confidence and uncertainty...")
    payload=read_json(TERRAIN_STEERING_CONFIDENCE_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"steering confidence request unavailable"}
    ready=payload.get("data_state")=="terrain_steering_confidence_cache"
    safe=payload.get("data_state") in {"steering_confidence_unavailable_safe","steering_confidence_generation_failed"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","steering confidence state unknown"),"state":payload.get("data_state")}



def prepare_saddle_gap(timeout: int = 45) -> dict:
    print("Deriving saddle transfer and gap acceleration from measured terrain...")
    payload=read_json(SADDLE_GAP_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"saddle transfer request unavailable"}
    ready=payload.get("data_state")=="saddle_transfer_gap_cache"
    safe=payload.get("data_state") in {"saddle_gap_unavailable_safe","saddle_gap_generation_failed"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","saddle transfer state unknown")}


def prepare_basin_retention(timeout: int = 45) -> dict:
    print("Deriving basin retention and conditional cold-air pooling from measured terrain...")
    payload=read_json(BASIN_RETENTION_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"basin retention request unavailable"}
    ready=payload.get("data_state")=="basin_retention_cold_air_pooling_cache"
    safe=payload.get("data_state") in {"basin_retention_unavailable_safe","basin_retention_generation_failed"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","basin retention state unknown")}

def prepare_terrain_convergence(timeout: int = 45) -> dict:
    print("Deriving terrain convergence and focused-accumulation potential...")
    payload=read_json(TERRAIN_CONVERGENCE_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"terrain convergence request unavailable"}
    ready=payload.get("data_state")=="terrain_convergence_accumulation_cache"
    safe=payload.get("data_state") in {"terrain_convergence_unavailable_safe","terrain_convergence_generation_failed"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","terrain convergence state unknown")}

def prepare_canyon_channeling(timeout: int = 45) -> dict:
    print("Deriving canyon channeling and drainage alignment from measured terrain...")
    payload=read_json(CANYON_CHANNELING_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"canyon channeling request unavailable"}
    ready=payload.get("data_state")=="canyon_channeling_drainage_cache"
    safe=payload.get("data_state") in {"canyon_channeling_unavailable_safe","canyon_channeling_generation_failed"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","canyon channeling state unknown")}

def prepare_terrain_transitions(timeout: int = 45) -> dict:
    print("Deriving terrain transition zones and flow-regime boundaries...")
    payload=read_json(TERRAIN_TRANSITION_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"terrain transition request unavailable"}
    ready=payload.get("data_state")=="terrain_transition_regimes_cache"
    safe=payload.get("data_state") in {"terrain_transition_unavailable_safe","terrain_transition_generation_failed"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","terrain transition state unknown")}

def prepare_terrain_regime_confidence(timeout: int = 45) -> dict:
    print("Scoring terrain-regime confidence and boundary ambiguity...")
    payload=read_json(TERRAIN_REGIME_CONFIDENCE_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"safe":False,"label":"regime confidence request unavailable"}
    ready=payload.get("data_state")=="terrain_regime_confidence_cache"
    safe=payload.get("data_state") in {"terrain_regime_confidence_unavailable_safe","terrain_regime_confidence_generation_failed"}
    return {"ready":ready,"safe":safe,"label":payload.get("display_label","regime confidence state unknown")}

def prepare_integrated_terrain_response(timeout: int = 60) -> dict:
    print("Synthesizing the integrated terrain-response field...")
    payload=read_json(INTEGRATED_TERRAIN_RESPONSE_REFRESH_URL,timeout)
    if not payload:return {"ready":False,"label":"integrated response request unavailable"}
    return {"ready":payload.get("data_state")=="integrated_terrain_response_cache","label":payload.get("display_label","integrated response state unknown")}


def prepare_terrain(timeout: int = 45) -> dict:
    print("Preparing measured terrain context before opening the scene...")
    payload = read_json(TERRAIN_REFRESH_URL, timeout)
    if not payload:
        return {"ready": False, "label": "terrain request unavailable; neutral mode retained"}
    ready = payload.get("data_state") == "measured_sample_cache" and int(payload.get("sample_count", 0)) >= 4
    return {
        "ready": ready,
        "label": payload.get("display_label", payload.get("data_state", "terrain state unknown")),
        "sample_count": payload.get("sample_count", 0),
    }



def print_health_summary() -> None:
    scene = read_json(f"{BASE_URL}/scene.json", 8) or {}
    report = read_json(f"{BASE_URL}/self-test.json", 8) or {}
    terrain = scene.get("terrain", {})
    wind = scene.get("wind", {})
    plume = scene.get("plume_visualization", {})
    flow = plume.get("geometry", {}).get("flow_path", {})
    print(f"\n{scene.get('build_label', 'SV2-53')} PROJECT HEALTH SUMMARY")
    print(f"PASS {report.get('passed', '?')} / {report.get('total', '?')}")
    print("Launcher ............. OK")
    print("Scene ................ OK" if scene else "Scene ................ CHECK")
    print(f"Terrain .............. {'READY' if terrain.get('data_state') == 'measured_sample_cache' else 'NEUTRAL'}")
    print(f"Wind ................. {str(wind.get('data_state', 'unknown')).upper()}")
    print(f"Flow Path ............ {str(flow.get('terrain_response', 'unknown')).upper()}")
    lighting = scene.get('terrain_lighting', {})
    relief_state = 'READY' if lighting.get('data_state') == 'measured_terrain_lighting_applied' else ('SPARSE/SAFE' if lighting.get('mode') == 'neutral_sparse_measured_grid' else 'NEUTRAL')
    print(f"Relief Lighting ...... {relief_state}")
    volume = scene.get('air_volume', {})
    print(f"Air Volume ........... {'READY' if volume.get('mode') == 'layered_air_volume_visual_reconstruction' else 'CHECK'}")
    living = scene.get('living_wind', {})
    print(f"Living Wind .......... {'READY' if living.get('mode') == 'live_wind_responsive_visual_motion' else 'CHECK'}")
    observation = scene.get('observation_contract', {})
    print(f"Observation Record ... {str(observation.get('data_state', 'unknown')).upper()}")
    citations = scene.get('citation_surface', {})
    print(f"Citation Surface .... {str(citations.get('status', 'unknown')).upper()} · {citations.get('display_label', 'unknown')}")
    vocabulary = scene.get('evidence_vocabulary', {})
    print(f"Evidence Language ... {str(vocabulary.get('status', 'unknown')).upper()} · {vocabulary.get('display_label', 'unknown')}")
    missing = scene.get('missing_evidence', {})
    print(f"Missing Evidence .... {str(missing.get('status', 'unknown')).upper()} · {missing.get('display_label', 'unknown')}")
    full_dem = scene.get('full_dem', {})
    dem_state = 'READY' if full_dem.get('data_state') == 'continuous_dem_cache' else 'PENDING/SAFE'
    print(f"Full DEM ............. {dem_state} · {full_dem.get('display_label', 'unknown')}")
    hillshade = scene.get('hillshade', {})
    hillshade_state = 'READY' if hillshade.get('data_state') == 'dem_derived_hillshade_cache' else 'UNAVAILABLE/SAFE'
    print(f"Hillshade ............ {hillshade_state} · {hillshade.get('display_label', 'unknown')}")
    derivatives = scene.get('slope_aspect', {})
    derivatives_state = 'READY' if derivatives.get('data_state') == 'dem_derived_slope_aspect_cache' else 'UNAVAILABLE/SAFE'
    print(f"Slope + Aspect ....... {derivatives_state} · {derivatives.get('display_label', 'unknown')}")
    landforms=scene.get('landforms',{})
    landform_state='READY' if landforms.get('data_state')=='dem_derived_landform_cache' else 'UNAVAILABLE/SAFE'
    print(f"Landforms ............ {landform_state} · {landforms.get('display_label','unknown')}")
    tc=scene.get('terrain_confidence',{})
    tc_state='READY' if tc.get('data_state')=='terrain_confidence_ready' else 'UNAVAILABLE/SAFE'
    print(f"Terrain Confidence ... {tc_state} · {tc.get('display_label','unknown')}")
    historical=scene.get("historical_weather",{})
    historical_state="READY" if historical.get("data_state")=="historical_weather_cache" else "UNAVAILABLE/SAFE"
    print(f"Historical Weather ... {historical_state} · {historical.get('display_label','unknown')}")
    multi=scene.get("multi_level_wind",{})
    multi_state="READY" if multi.get("data_state")=="multi_level_wind_cache" else "UNAVAILABLE/SAFE"
    print(f"Multi-Level Wind ..... {multi_state} · {multi.get('display_label','unknown')}")
    stability=scene.get("atmospheric_stability",{})
    stability_state="READY" if stability.get("data_state")=="atmospheric_stability_screen" else "UNAVAILABLE/SAFE"
    print(f"Atmospheric Stability . {stability_state} · {stability.get('display_label','unknown')}")
    boundary=scene.get("boundary_layer_depth",{})
    boundary_state="READY" if boundary.get("data_state")=="boundary_layer_depth_cache" else "UNAVAILABLE/SAFE"
    print(f"Boundary Layer ......... {boundary_state} · {boundary.get('display_label','unknown')}")
    variability=scene.get("gust_variability",{})
    variability_state="READY" if variability.get("data_state")=="gust_variability_window_cache" else "UNAVAILABLE/SAFE"
    print(f"Gust Variability ...... {variability_state} · {variability.get('display_label','unknown')}")
    interaction=scene.get("terrain_atmosphere_index",{})
    interaction_state="READY" if interaction.get("data_state")=="terrain_atmosphere_interaction_index" else "UNAVAILABLE/SAFE"
    print(f"Terrain-Air Index ..... {interaction_state} · {interaction.get('display_label','unknown')}")
    steering=scene.get("terrain_steering_field",{})
    steering_state="READY" if steering.get("data_state")=="terrain_steering_field_cache" else "UNAVAILABLE/SAFE"
    print(f"Steering Field ........ {steering_state} · {steering.get('display_label','unknown')}")
    steering_conf=scene.get("terrain_steering_confidence",{})
    steering_conf_state="READY" if steering_conf.get("data_state")=="terrain_steering_confidence_cache" else "UNAVAILABLE/SAFE"
    print(f"Steering Confidence ... {steering_conf_state} · {steering_conf.get('display_label','unknown')}")
    explorer = scene.get("reviewer_guided_exploration", {})
    explorer_state = "READY" if explorer.get("data_state") == "reviewer_guided_exploration_ready" else "CHECK"
    print(f"Evidence Explorer .... {explorer_state} · {explorer.get('display_label', 'unknown')}")
    disclosure = scene.get("progressive_disclosure", {})
    disclosure_state = "READY" if disclosure.get("data_state") == "progressive_disclosure_ready" else "CHECK"
    print(f"Scene Simplification . {disclosure_state} · {disclosure.get('display_label', 'unknown')}")
    geometry_adapter = scene.get('observation_geometry', {})
    print(f"Steering Volume ...... {'READY' if scene.get('steering_aware_air_volume',{}).get('data_state')=='steering_aware_air_volume_ready' else 'UNAVAILABLE/SAFE'} · {scene.get('steering_aware_air_volume',{}).get('display_label','unknown')}")
    particle=scene.get('terrain_responsive_particle_advection',{})
    particle_state='READY' if particle.get('data_state')=='terrain_responsive_particle_advection_ready' else 'UNAVAILABLE/SAFE'
    print(f"Particle Advection ... {particle_state} · {particle.get('display_label','unknown')}")
    saddle=scene.get('saddle_gap_acceleration',{})
    saddle_state='READY' if saddle.get('data_state')=='saddle_transfer_gap_cache' else 'UNAVAILABLE/SAFE'
    print(f"Saddle + Gap ......... {saddle_state} · {saddle.get('display_label','unknown')}")
    basin=scene.get('basin_retention_cold_air_pooling',{})
    basin_state='READY' if basin.get('data_state')=='basin_retention_cold_air_pooling_cache' else 'UNAVAILABLE/SAFE'
    print(f"Basin + Cold Air ..... {basin_state} · {basin.get('display_label','unknown')}")
    convergence=scene.get('terrain_convergence_accumulation',{})
    convergence_state='READY' if convergence.get('data_state')=='terrain_convergence_accumulation_cache' else 'UNAVAILABLE/SAFE'
    print(f"Convergence + Focus .. {convergence_state} · {convergence.get('display_label','unknown')}")
    trans=scene.get("terrain_transition_regimes", {})
    print(f"Terrain Transitions ... {'READY' if trans.get('data_state')=='terrain_transition_regimes_cache' else 'UNAVAILABLE/SAFE'} · {trans.get('display_label','unknown')}")
    regime=scene.get("terrain_regime_confidence",{})
    print(f"Regime Confidence .... {'READY' if regime.get('data_state')=='terrain_regime_confidence_cache' else 'UNAVAILABLE/SAFE'} · {regime.get('display_label','unknown')}")
    integrated=scene.get("integrated_terrain_response",{})
    print(f"Integrated Response .. {'READY' if integrated.get('data_state')=='integrated_terrain_response_cache' else 'UNAVAILABLE/SAFE'} · {integrated.get('display_label','unknown')}")
    print(f"Geometry Adapter .... {str(geometry_adapter.get('adapter_status', 'unknown')).upper()} · {geometry_adapter.get('display_label', 'unknown')}")
    timing = scene.get('evidence_time', {})
    print(f"Evidence Time ........ {str(timing.get('alignment_status', 'unknown')).upper()}")
    print("Plume ................ REGISTERED" if plume.get('geometry', {}).get('mode') == 'map_registered_visual_reconstruction' else "Plume ................ CHECK")
    print(f"Smoke Tests .......... {report.get('status', 'UNKNOWN')}")
    print("Scientific Claims .... PASS" if report.get('status') == 'PASS' else "Scientific Claims .... CHECK")
    if report.get('status') == 'PASS':
        print("READY FOR HUMAN REVIEW")
    else:
        print("REVIEW REQUIRED")
        for check in report.get('failed_checks', []):
            print(f"FAILED CHECK ......... {check.get('name')}: {check.get('detail')}")

def open_url(url: str) -> bool:
    try:
        return bool(webbrowser.open_new_tab(url))
    except webbrowser.Error:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Start Invisible Air, build terrain convergence and focused accumulation, and open only the primary scene.")
    parser.add_argument("--verify", action="store_true", help="Open both the scene and self-test pages.")
    parser.add_argument("--wait", type=int, default=60, help="Maximum seconds to wait for the server.")
    parser.add_argument("--skip-terrain-refresh", action="store_true", help="Skip automatic terrain preparation.")
    args = parser.parse_args()

    started_here = False
    if not server_ready():
        print("Starting the Invisible Air server in a separate window...")
        start_server()
        started_here = True
    else:
        print("Invisible Air is already running.")

    print(f"Waiting for {HEALTH_URL} to report ready...")
    if not wait_for_server(args.wait):
        print("ERROR: The local server did not become ready within the time limit.")
        print("Review the separate server window for the exact Python error.")
        return 1

    if not args.skip_terrain_refresh:
        dem = prepare_dem()
        if dem["ready"]:
            print(f"FULL DEM READY: {dem['label']} ({dem.get('bytes', 0)} bytes)")
        else:
            print(f"FULL DEM NOT CACHED: {dem['label']}")
            print("The scene will retain sparse measured terrain and clearly label the raster gap.")
        hillshade = prepare_hillshade()
        if hillshade["ready"]:
            print(f"HILLSHADE READY: {hillshade['label']} ({hillshade.get('bytes', 0)} bytes)")
        else:
            print(f"HILLSHADE NOT GENERATED: {hillshade['label']}")
            print("The scene will withhold continuous hillshade rather than use an invalid derivative.")
        derivatives = prepare_slope_aspect()
        if derivatives["ready"]:
            print(f"SLOPE + ASPECT READY: {derivatives['label']}")
        else:
            print(f"SLOPE + ASPECT NOT GENERATED: {derivatives['label']}")
            print("The scene will withhold these derivatives rather than infer them.")
        landforms = prepare_landforms()
        if landforms["ready"]:
            print(f"LANDFORMS READY: {landforms['label']}")
        else:
            print(f"LANDFORMS NOT GENERATED: {landforms['label']}")
            print("The scene will withhold landform classes rather than infer them.")
        confidence = prepare_terrain_confidence()
        if confidence["ready"]:
            print(f"TERRAIN CONFIDENCE READY: {confidence['label']}")
        else:
            print(f"TERRAIN CONFIDENCE NOT GENERATED: {confidence['label']}")
            print("The scene will expose the terrain confidence gap rather than imply quality.")
        historical = prepare_historical_weather()
        if historical["ready"]:
            print(f"HISTORICAL WEATHER READY: {historical['label']}")
        elif historical["safe"]:
            print(f"HISTORICAL WEATHER UNAVAILABLE/SAFE: {historical['label']}")
        else:
            print(f"HISTORICAL WEATHER CHECK: {historical['label']}")
        multi = prepare_multi_level_wind()
        if multi["ready"]:
            print(f"MULTI-LEVEL WIND READY: {multi['label']}")
        elif multi["safe"]:
            print(f"MULTI-LEVEL WIND UNAVAILABLE/SAFE: {multi['label']}")
        else:
            print(f"MULTI-LEVEL WIND CHECK: {multi['label']}")
        stability = prepare_atmospheric_stability()
        if stability["ready"]:
            print(f"ATMOSPHERIC STABILITY READY: {stability['label']}")
        elif stability["safe"]:
            print(f"ATMOSPHERIC STABILITY UNAVAILABLE/SAFE: {stability['label']}")
        else:
            print(f"ATMOSPHERIC STABILITY CHECK: {stability['label']}")
        boundary = prepare_boundary_layer_depth()
        if boundary["ready"]:
            print(f"BOUNDARY-LAYER DEPTH READY: {boundary['label']}")
        elif boundary["safe"]:
            print(f"BOUNDARY-LAYER DEPTH UNAVAILABLE/SAFE: {boundary['label']}")
        else:
            print(f"BOUNDARY-LAYER DEPTH CHECK: {boundary['label']}")
        variability = prepare_gust_variability()
        if variability["ready"]:
            print(f"GUST VARIABILITY READY: {variability['label']}")
        elif variability["safe"]:
            print(f"GUST VARIABILITY UNAVAILABLE/SAFE: {variability['label']}")
        else:
            print(f"GUST VARIABILITY CHECK: {variability['label']}")
        steering = prepare_terrain_steering_field()
        if steering["ready"]:
            print(f"TERRAIN STEERING FIELD READY: {steering['label']}")
        elif steering["safe"]:
            print(f"TERRAIN STEERING FIELD UNAVAILABLE/SAFE: {steering['label']}")
        else:
            print(f"TERRAIN STEERING FIELD CHECK: {steering['label']}")
        steering_conf = prepare_terrain_steering_confidence()
        if steering_conf["ready"]:
            print(f"STEERING CONFIDENCE READY: {steering_conf['label']}")
        else:
            print(f"STEERING CONFIDENCE UNAVAILABLE/SAFE: {steering_conf['label']}")
        canyon=prepare_canyon_channeling()
        if canyon["ready"]: print(f"CANYON + DRAINAGE READY: {canyon['label']}")
        elif canyon["safe"]: print(f"CANYON + DRAINAGE UNAVAILABLE/SAFE: {canyon['label']}")
        else: print(f"CANYON + DRAINAGE CHECK: {canyon['label']}")
        saddle=prepare_saddle_gap()
        if saddle["ready"]: print(f"SADDLE + GAP READY: {saddle['label']}")
        elif saddle["safe"]: print(f"SADDLE + GAP UNAVAILABLE/SAFE: {saddle['label']}")
        else: print(f"SADDLE + GAP CHECK: {saddle['label']}")
        basin=prepare_basin_retention()
        if basin["ready"]: print(f"BASIN + COLD AIR READY: {basin['label']}")
        elif basin["safe"]: print(f"BASIN + COLD AIR UNAVAILABLE/SAFE: {basin['label']}")
        else: print(f"BASIN + COLD AIR CHECK: {basin['label']}")
        convergence=prepare_terrain_convergence()
        if convergence["ready"]: print(f"CONVERGENCE + FOCUS READY: {convergence['label']}")
        elif convergence["safe"]: print(f"CONVERGENCE + FOCUS UNAVAILABLE/SAFE: {convergence['label']}")
        else: print(f"CONVERGENCE + FOCUS CHECK: {convergence['label']}")
        transitions=prepare_terrain_transitions()
        if transitions["ready"]: print(f"TERRAIN TRANSITIONS READY: {transitions['label']}")
        elif transitions["safe"]: print(f"TERRAIN TRANSITIONS UNAVAILABLE/SAFE: {transitions['label']}")
        else: print(f"TERRAIN TRANSITIONS CHECK: {transitions['label']}")
        regime_conf=prepare_terrain_regime_confidence()
        integrated_response=prepare_integrated_terrain_response()
        if regime_conf["ready"]: print(f"REGIME CONFIDENCE READY: {regime_conf['label']}")
        elif regime_conf["safe"]: print(f"REGIME CONFIDENCE UNAVAILABLE/SAFE: {regime_conf['label']}")
        else: print(f"REGIME CONFIDENCE CHECK: {regime_conf['label']}")
        terrain = prepare_terrain()
        if terrain["ready"]:
            print(f"TERRAIN READY: {terrain['label']} ({terrain.get('sample_count', 0)} samples)")
        else:
            print(f"TERRAIN NOT MEASURED: {terrain['label']}")
            print("The scene will open safely in neutral terrain mode.")

    # Verification remains comprehensive, but only the primary scene opens in the browser.
    targets = [SCENE_URL]

    failed = []
    for target in targets:
        print(f"Opening {target}")
        if not open_url(target):
            failed.append(target)
        time.sleep(0.7)

    if failed:
        print("The server is ready, but Windows did not confirm browser launch.")
        print("Open this exact page manually:")
        for target in failed:
            print(target)
        return 2

    report = read_json(f"{BASE_URL}/self-test.json", 8) or {}
    print_health_summary()
    if report.get("status") != "PASS":
        print("\nFAIL: The pages opened, but the live internal verification found a runtime problem.")
        print("Do not treat this pass as approved until the failed check is corrected.")
        return 3
    print("\nPASS: Terrain preparation completed and the exact confirmation page opened.")
    if started_here:
        print("The server remains running in its separate window.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
