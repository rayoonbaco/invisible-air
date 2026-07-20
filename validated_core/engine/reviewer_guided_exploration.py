from __future__ import annotations

from typing import Any

PASS_ID = "SV2-53"


def _state(record: dict[str, Any] | None, fallback: str = "unknown") -> str:
    record = record or {}
    return str(record.get("data_state") or record.get("status") or fallback)


def _label(record: dict[str, Any] | None, fallback: str) -> str:
    record = record or {}
    return str(record.get("display_label") or fallback)


def reviewer_guided_exploration_context(scene: dict[str, Any]) -> dict[str, Any]:
    """Build the reviewer-facing evidence index without adding scientific claims."""
    missing = scene.get("missing_evidence") or {}
    missing_count = int((missing.get("summary") or {}).get("missing_count", 0) or 0)

    families = [
        {
            "id": "overview",
            "label": "Overview",
            "description": "Reported observation, measured place, current context, interpretation, and visible limits.",
            "keywords": ["overview", "case", "scene", "review"],
        },
        {
            "id": "observation",
            "label": "Observation",
            "description": "The source-seeded observation record, geometry status, evidence time, and citations.",
            "keywords": ["observation", "source", "record", "geometry", "citation", "time"],
        },
        {
            "id": "terrain",
            "label": "Terrain",
            "description": "Measured elevation, hillshade, slope, landforms, and terrain evidence quality.",
            "keywords": ["terrain", "dem", "hillshade", "slope", "aspect", "landforms", "relief"],
        },
        {
            "id": "atmosphere",
            "label": "Atmosphere",
            "description": "Current wind and safely unavailable observation-time atmospheric context.",
            "keywords": ["wind", "weather", "stability", "boundary layer", "gust", "atmosphere"],
        },
        {
            "id": "interaction",
            "label": "Interaction",
            "description": "Terrain-air steering, regimes, convergence, divergence, transfer, shelter, and uncertainty.",
            "keywords": ["steering", "interaction", "regime", "convergence", "divergence", "shelter", "channel", "saddle", "basin"],
        },
        {
            "id": "synthesis",
            "label": "Synthesis",
            "description": "Integrated response, bounded authority, motion, volume, and visual orchestration.",
            "keywords": ["integrated", "response", "authority", "motion", "volume", "timeline", "annotation"],
        },
        {
            "id": "uncertainty",
            "label": "Uncertainty",
            "description": "Confidence, ambiguity, conflicts, missing inputs, and explicit claim boundaries.",
            "keywords": ["uncertainty", "confidence", "ambiguity", "conflict", "missing", "unknown", "not claimed"],
        },
    ]

    items = [
        {"id": "observation-record", "family": "observation", "title": "Observation record", "state": _state(scene.get("observation_contract")), "summary": _label(scene.get("observation_contract"), "Source-seeded record"), "why": "Anchors the scene to a reported record rather than an app detection.", "not_claimed": "Not a methane detection, verdict, or facility attribution.", "route": "/observation", "keywords": ["source", "manifest", "record"]},
        {"id": "evidence-time", "family": "observation", "title": "Evidence time", "state": str((scene.get("evidence_time") or {}).get("alignment_status", "unknown")), "summary": str((scene.get("evidence_time") or {}).get("display_label", "Current context only")), "why": "Separates present-day context from unresolved observation-time conditions.", "not_claimed": "Not a reconstruction of event-time transport.", "route": "/evidence-time", "keywords": ["time", "historical", "current context"]},
        {"id": "citations", "family": "observation", "title": "Citation surface", "state": _state(scene.get("citation_surface")), "summary": _label(scene.get("citation_surface"), "Citation status"), "why": "Keeps visible layers traceable to their source class.", "not_claimed": "A citation does not certify the interpretation.", "route": "/citations", "keywords": ["provenance", "source", "traceable"]},
        {"id": "full-dem", "family": "terrain", "title": "Measured terrain foundation", "state": _state(scene.get("full_dem")), "summary": _label(scene.get("full_dem"), "DEM status"), "why": "Provides the continuous elevation basis for derived terrain interpretation.", "not_claimed": "Not atmospheric evidence or methane evidence.", "route": "/dem", "keywords": ["dem", "elevation", "measured"]},
        {"id": "terrain-confidence", "family": "terrain", "title": "Terrain confidence", "state": _state(scene.get("terrain_confidence")), "summary": _label(scene.get("terrain_confidence"), "Terrain confidence status"), "why": "Reports quality and completeness of the terrain evidence lane.", "not_claimed": "Not confidence in methane presence or transport.", "route": "/terrain-confidence", "keywords": ["confidence", "terrain quality"]},
        {"id": "current-wind", "family": "atmosphere", "title": "Current wind context", "state": _state(scene.get("wind")), "summary": f"{(scene.get('wind') or {}).get('cardinal_from', 'wind')} {(scene.get('wind') or {}).get('speed_mph', '?')} mph", "why": "Orients the present-day visual pathway.", "not_claimed": "Not necessarily observation-time wind.", "route": "/wind", "keywords": ["wind", "current", "direction"]},
        {"id": "historical-weather", "family": "atmosphere", "title": "Historical weather", "state": _state(scene.get("historical_weather")), "summary": _label(scene.get("historical_weather"), "Historical weather status"), "why": "Shows whether observation-time atmospheric context is available.", "not_claimed": "Unavailable values remain unavailable; none are invented.", "route": "/historical-weather", "keywords": ["historical", "weather", "observation time"]},
        {"id": "steering-field", "family": "interaction", "title": "Terrain steering field", "state": _state(scene.get("terrain_steering_field")), "summary": _label(scene.get("terrain_steering_field"), "Steering field status"), "why": "Organizes bounded DEM-derived terrain response relative to available wind context.", "not_claimed": "Not measured airflow, CFD, or verified plume routing.", "route": "/terrain-steering-field", "keywords": ["steering", "channeling", "deflection"]},
        {"id": "steering-confidence", "family": "uncertainty", "title": "Steering confidence and uncertainty", "state": _state(scene.get("terrain_steering_confidence")), "summary": _label(scene.get("terrain_steering_confidence"), "Steering confidence status"), "why": "Limits how much authority the steering heuristic receives.", "not_claimed": "Not confidence in methane or exact transport.", "route": "/terrain-steering-confidence", "keywords": ["confidence", "uncertainty", "steering"]},
        {"id": "terrain-regimes", "family": "interaction", "title": "Terrain regimes and boundaries", "state": _state(scene.get("terrain_transition_regimes")), "summary": _label(scene.get("terrain_transition_regimes"), "Terrain regime status"), "why": "Shows where confined, transfer, dispersive, and mixed terrain responses may transition.", "not_claimed": "Not a measured atmospheric front or plume edge.", "route": "/terrain-transition-regimes", "keywords": ["regime", "transition", "boundary"]},
        {"id": "integrated-response", "family": "synthesis", "title": "Integrated terrain response", "state": _state(scene.get("integrated_terrain_response")), "summary": _label(scene.get("integrated_terrain_response"), "Integrated response status"), "why": "Synthesizes component terrain interpretations while retaining agreement and conflict.", "not_claimed": "Not a physical atmospheric simulation.", "route": "/integrated-terrain-response", "keywords": ["integrated", "response", "agreement"]},
        {"id": "response-authority", "family": "synthesis", "title": "Response authority", "state": _state(scene.get("integrated_response_authority")), "summary": _label(scene.get("integrated_response_authority"), "Response authority status"), "why": "Controls how strongly the integrated interpretation may influence the visual scene.", "not_claimed": "Authority governs visualization only.", "route": "/integrated-response-authority", "keywords": ["authority", "conflict", "winner"]},
        {"id": "motion-orchestration", "family": "synthesis", "title": "Motion orchestration", "state": _state(scene.get("integrated_motion_orchestration")), "summary": _label(scene.get("integrated_motion_orchestration"), "Motion orchestration status"), "why": "Coordinates bounded visual tracer behavior under one conflict-aware plan.", "not_claimed": "Particles are not measured methane parcels.", "route": "/integrated-motion-orchestration", "keywords": ["motion", "particles", "advection"]},
        {"id": "missing-evidence", "family": "uncertainty", "title": "Missing evidence", "state": _state(missing), "summary": f"{missing_count} unresolved evidence inputs", "why": "Keeps absent inputs visible instead of silently filling gaps.", "not_claimed": "Missing evidence cannot be replaced by visual plausibility.", "route": "/missing-evidence", "keywords": ["missing", "gap", "unknown"]},
        {"id": "claim-boundaries", "family": "uncertainty", "title": "Scientific claim boundaries", "state": "active", "summary": "Detection, exact geometry, quantification, transport, exposure, and responsibility remain unclaimed.", "why": "Prevents visual interpretation from becoming an unsupported conclusion.", "not_claimed": "No methane detection, certified quantification, enforcement conclusion, or responsibility attribution.", "route": "/boundaries", "keywords": ["boundary", "not claimed", "guardrail"]},
    ]

    links = [
        ["observation-record", "evidence-time"], ["observation-record", "citations"],
        ["full-dem", "terrain-confidence"], ["full-dem", "steering-field"],
        ["current-wind", "steering-field"], ["historical-weather", "evidence-time"],
        ["steering-field", "steering-confidence"], ["steering-field", "terrain-regimes"],
        ["terrain-regimes", "integrated-response"], ["steering-confidence", "response-authority"],
        ["integrated-response", "response-authority"], ["response-authority", "motion-orchestration"],
        ["missing-evidence", "steering-confidence"], ["claim-boundaries", "integrated-response"],
    ]

    return {
        "contract_version": "reviewer_guided_evidence_exploration_v1",
        "pass_id": PASS_ID,
        "layer": "reviewer_guided_evidence_exploration",
        "evidence_state": "interface_governance",
        "data_state": "reviewer_guided_exploration_ready",
        "status": "ready",
        "display_label": f"reviewer-guided evidence exploration · {len(families)-1} evidence families · {len(items)} review threads",
        "default_family": "overview",
        "families": families,
        "items": items,
        "links": links,
        "workflow": ["observation", "terrain", "atmosphere", "interaction", "synthesis", "uncertainty"],
        "interaction_policy": {
            "single_family_focus": True,
            "unrelated_layers_muted_not_removed": True,
            "uncertainty_always_available": True,
            "search_enabled": True,
            "breadcrumb_enabled": True,
            "return_to_overview_required": True,
            "deep_routes_remain_available": True,
        },
        "scene_directive": "Let the reviewer follow one evidence thread at a time while preserving uncertainty, provenance, and a direct return to the complete scene.",
        "claim_boundary": "Evidence exploration changes reading order and visual emphasis only. It does not add evidence, increase confidence, detect methane, reconstruct transport, quantify emissions, or attribute responsibility.",
    }
