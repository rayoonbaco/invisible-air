from __future__ import annotations


def _item(item_id: str, label: str, state: str, consequence: str, resolves_with: str, evidence_state: str) -> dict:
    return {
        "item_id": item_id,
        "label": label,
        "state": state,
        "visual_consequence": consequence,
        "resolves_with": resolves_with,
        "evidence_state": evidence_state,
    }


def build_missing_evidence(scene: dict) -> dict:
    observation = scene.get("observation_contract", {})
    terrain = scene.get("terrain", {})
    evidence_time = scene.get("evidence_time", {})
    hillshade = scene.get("hillshade", {})
    stability = scene.get("atmospheric_stability", {})

    present = [
        _item("source_coordinates", "Source coordinates", "present", "Source marker remains sharp and map-registered.", "Already available in the seeded record.", "observed"),
        _item("current_wind", "Current wind", "present", "Current-direction motion remains visible.", "Already available as present-day context.", "current_context"),
    ]
    if terrain.get("data_state") == "measured_sample_cache":
        present.append(_item("measured_terrain", "Measured terrain samples", "present", "Terrain response remains available as a fallback.", "Already available from the measured terrain cache.", "measured"))
    if hillshade.get("data_state") == "dem_derived_hillshade_cache":
        present.append(_item("dem_hillshade", "DEM-derived hillshade", "present", "Continuous terrain relief remains visible beneath the air volume.", "Already derived from the validated DEM cache.", "measured"))

    missing = []
    if hillshade.get("data_state") != "dem_derived_hillshade_cache":
        missing.append(_item("dem_hillshade", "DEM-derived hillshade", "missing", "Continuous relief is withheld and sparse terrain remains visually secondary.", "A valid DEM cache followed by a successful hillshade derivation.", "unavailable"))
    if not observation.get("reported_time_utc"):
        missing.append(_item("observation_time", "Reported observation time", "missing", "The timeline remains broken and the scene cannot claim event-time alignment.", "A verified UTC timestamp from the source manifest.", "unavailable"))
    if not observation.get("source_url"):
        missing.append(_item("source_url", "Observation source URL", "missing", "The observation badge remains unresolved and citation completeness stays partial.", "A traceable provider or product URL.", "unavailable"))
    if observation.get("geometry_status") not in {"source_geometry_loaded", "exact_product_geometry_loaded"}:
        missing.append(_item("source_geometry", "Source-product geometry", "missing", "The plume boundary fades and remains a reconstruction rather than observed geometry.", "Provider geometry, raster mask, or confidence polygon.", "unavailable"))
    if evidence_time.get("alignment_status") != "event_time_wind_confirmed":
        missing.append(_item("event_time_wind", "Observation-time wind", "missing", "The animated path is visibly reduced to current-context guidance only.", "Historical meteorology aligned to the reported observation time.", "unavailable"))
    if stability.get("data_state") == "atmospheric_stability_screen":
        present.append(_item("atmospheric_stability", "Atmospheric stability screen", "present", "Mixing tendency is available as a labeled screening inference only.", "Already derived from archived meteorological inputs.", "inferred"))
    else:
        missing.append(_item("atmospheric_stability", "Atmospheric stability", "missing", "Vertical spread remains visually restrained and non-physical.", "A defensible stability class or model-derived boundary-layer state.", "unavailable"))
    missing.extend([
        _item("vertical_profile", "Vertical plume profile", "missing", "No physical height or vertical concentration profile is displayed.", "Observed or modeled vertical structure with units and provenance.", "unavailable"),
        _item("dispersion_model", "Atmospheric dispersion output", "missing", "The flow body keeps broken downstream certainty and cannot become a prediction surface.", "A documented model run with inputs, version, and assumptions.", "not_modeled"),
    ])

    not_claimed = [
        _item("facility_responsibility", "Facility responsibility", "not_claimed", "No blame marker or responsibility label appears.", "Outside the product claim boundary.", "not_claimed"),
        _item("certified_quantification", "Certified emissions quantification", "not_claimed", "No mass-rate scale or certified total is displayed.", "Outside the current evidence and product boundary.", "not_claimed"),
        _item("illegality", "Illegality or enforcement status", "not_claimed", "No compliance verdict appears in the scene.", "Outside the product claim boundary.", "not_claimed"),
    ]

    total_review_items = len(present) + len(missing)
    completeness = round(len(present) / total_review_items, 3) if total_review_items else 0.0
    visual_strength = round(max(0.34, min(0.88, 0.42 + completeness * 0.48)), 3)
    downstream_break = round(max(0.18, min(0.62, 0.58 - completeness * 0.35)), 3)

    return {
        "contract_version": "1.0",
        "pass_id": "SV2-35",
        "status": "missing_evidence_visible",
        "display_label": f"{len(missing)} unresolved evidence inputs",
        "present_count": len(present),
        "missing_count": len(missing),
        "not_claimed_count": len(not_claimed),
        "completeness_ratio": completeness,
        "visual_strength": visual_strength,
        "downstream_break": downstream_break,
        "categories": {
            "present": present,
            "missing": missing,
            "assumed": [],
            "not_claimed": not_claimed,
        },
        "scene_directive": "Missing evidence must reduce visual confidence through fade, interruption, or unresolved markers; it must never be silently replaced.",
        "claim_boundary": "Missing-evidence visualization communicates data absence and review limits. It does not estimate missing values, validate a source claim, or increase scientific certainty.",
    }
