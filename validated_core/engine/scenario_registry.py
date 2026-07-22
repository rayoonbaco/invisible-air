from __future__ import annotations

from engine.material_profiles import apply_material_profile, get_material_profile

SCENARIOS = {
    "oxnard-coastal": {"id":"oxnard-coastal","name":"Oxnard, California","region":"Southern California coast","source_label":"Coastal methane source scenario","record":"IA-DEMO-OXNARD-001","latitude":34.2256,"longitude":-119.1189,"wind_from_deg":250.0,"wind_speed_mps":4.9,"stability_class":"neutral","terrain_profile":"complex","terrain_regime":"complex","material_profile_id":"methane-gas","interpretation":"Atmospheric influence is modeled east-northeast from the Oxnard source. The bright corridor shows the strongest relative influence; the softer outer field shows wider plausible influence; broken texture indicates weakening model support."},
    "permian-basin": {"id":"permian-basin","name":"Permian Basin, Texas","region":"West Texas energy basin","source_label":"Basin source scenario","record":"IA-DEMO-PERMIAN-001","latitude":31.9973,"longitude":-102.0779,"wind_from_deg":205.0,"wind_speed_mps":5.4,"stability_class":"neutral","terrain_profile":"open","terrain_regime":"open","material_profile_id":"methane-gas","interpretation":"Atmospheric influence is modeled northeast across open basin terrain. The narrow bright corridor shows the strongest relative influence, while the outer field broadens as support weakens with distance."},
    "four-corners": {"id":"four-corners","name":"Four Corners","region":"Colorado Plateau","source_label":"Plateau source scenario","record":"IA-DEMO-FOURCORNERS-001","latitude":36.73,"longitude":-108.21,"wind_from_deg":235.0,"wind_speed_mps":4.2,"stability_class":"stable","terrain_profile":"complex","terrain_regime":"complex","material_profile_id":"methane-gas","interpretation":"Atmospheric influence is modeled northeast through complex plateau terrain. Terrain response bends and fragments the outer field while the central corridor retains the strongest relative influence."},
    "appalachian-basin": {"id":"appalachian-basin","name":"Appalachian Basin","region":"Northern Appalachian terrain","source_label":"Ridge-and-valley source scenario","record":"IA-DEMO-APPALACHIAN-001","latitude":40.4406,"longitude":-79.9959,"wind_from_deg":265.0,"wind_speed_mps":3.8,"stability_class":"neutral","terrain_profile":"valley_aligned","terrain_regime":"valley","material_profile_id":"methane-gas","interpretation":"Atmospheric influence is modeled eastward with bounded valley alignment. The strongest corridor follows the transport axis while the wider field narrows where terrain support is stronger."},
    "uinta-basin": {"id":"uinta-basin","name":"Uinta Basin, Utah","region":"Intermountain basin","source_label":"Cold-basin source scenario","record":"IA-DEMO-UINTA-001","latitude":40.4555,"longitude":-109.5287,"wind_from_deg":225.0,"wind_speed_mps":2.7,"stability_class":"stable","terrain_profile":"valley_aligned","terrain_regime":"valley","material_profile_id":"methane-gas","interpretation":"Atmospheric influence is modeled northeast under stable basin conditions. The field remains concentrated near the central corridor, with texture showing where terrain and distance reduce model support."},
}
DEFAULT_SCENARIO_ID = "oxnard-coastal"

def list_scenarios():
    return [dict(item) for item in SCENARIOS.values()]

def get_scenario(scenario_id):
    return dict(SCENARIOS.get(scenario_id or '', SCENARIOS[DEFAULT_SCENARIO_ID]))

def apply_scenario(scene, scenario, material_profile_id=None):
    profile = get_material_profile(material_profile_id or scenario.get('material_profile_id'))
    apply_material_profile(scene, profile)
    observation = scene.setdefault('observation_contract', {})
    observation['observation_id'] = scenario['record']
    observation['product_type'] = scenario['source_label']
    observation['coordinates'] = {'lat': scenario['latitude'], 'lon': scenario['longitude']}
    scene.setdefault('location', {}).update({'lat': scenario['latitude'], 'lon': scenario['longitude'], 'label': scenario['name']})
    mph = round(scenario['wind_speed_mps'] / 0.44704, 1)
    scene.setdefault('wind', {}).update({'from_degrees': scenario['wind_from_deg'], 'speed_mph': mph, 'speed_mps': scenario['wind_speed_mps'], 'direction_cardinal': _cardinal(scenario['wind_from_deg']), 'data_state': 'fixed scenario conditions', 'label': f"{_cardinal(scenario['wind_from_deg'])} · {mph} mph"})
    scene.setdefault('atmospheric_stability', {})['stability_class'] = scenario['stability_class']
    scene['active_scenario'] = scenario
    # Scenario handoff contract: all coordinate-bearing surfaces agree.
    latitude = float(scenario["latitude"])
    longitude = float(scenario["longitude"])

    # Local scene bounds are part of the same handoff contract.
    longitude_span = float(scenario.get("local_longitude_span", 0.72))
    latitude_span = float(scenario.get("local_latitude_span", 0.48))
    scenario_local_bbox = [
        longitude - longitude_span / 2.0,
        latitude - latitude_span / 2.0,
        longitude + longitude_span / 2.0,
        latitude + latitude_span / 2.0,
    ]

    location = scene.setdefault("location", {})
    location["lat"] = latitude
    location["lon"] = longitude
    location["label"] = scenario["name"]
    location["bbox"] = scenario_local_bbox


    basemap = scene.setdefault("basemap", {})
    basemap["center"] = {"lat": latitude, "lon": longitude}
    basemap["zoom"] = int(scenario.get("local_zoom", 9))
    basemap["display_place"] = scenario["name"]
    basemap["source_seed_point"] = {
        "lat": latitude,
        "lon": longitude,
        "label": scenario["source_label"],
        "placement_note": "Scenario-selected source coordinate.",
    }

    plume_geometry = basemap.setdefault("plume_geometry", {})
    plume_geometry["source"] = {"lat": latitude, "lon": longitude}

    scene["source_seed_point"] = {
        "lat": latitude,
        "lon": longitude,
        "label": scenario["source_label"],
    }
    scene["active_scenario"] = scenario
    scene["scenario_handoff"] = {
        "scenario_id": scenario["id"],
        "latitude": latitude,
        "longitude": longitude,
        "map_center": [latitude, longitude],
        "local_bbox": scenario_local_bbox,
        "status": "geography_synchronized",
        "material_profile_id": profile["id"],
        "material_contract_status": "material_profile_contract_ready",
    }

    return scene

def _cardinal(degrees):
    labels = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']
    return labels[int((degrees % 360) / 22.5 + 0.5) % 16]
