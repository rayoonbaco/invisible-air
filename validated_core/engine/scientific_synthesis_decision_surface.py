from __future__ import annotations
from typing import Any

PASS_ID = "SV2-55"


def _label(value: Any, fallback: str = "Unavailable") -> str:
    if isinstance(value, dict):
        return str(value.get("display_label") or value.get("label") or value.get("status_label") or fallback)
    return str(value or fallback)


def scientific_synthesis_decision_surface_context(scene: dict[str, Any]) -> dict[str, Any]:
    observation = scene.get("observation_contract") or {}
    terrain = scene.get("terrain_confidence") or {}
    wind = scene.get("wind") or {}
    historical = scene.get("historical_weather") or {}
    integrated = scene.get("integrated_terrain_response") or {}
    authority = scene.get("integrated_response_authority") or {}
    regime = scene.get("terrain_regime_confidence") or {}
    missing = scene.get("missing_evidence") or {}
    evidence_time = scene.get("evidence_time") or {}

    missing_count = missing.get("unresolved_count")
    if missing_count is None:
        inputs = missing.get("unresolved_inputs") or missing.get("items") or []
        missing_count = len(inputs) if isinstance(inputs, list) else 0

    sections = [
        {
            "id": "observed",
            "label": "Observed",
            "state": "source_seeded",
            "summary": f"Reported observation record {observation.get('observation_id', 'CASE02-SOURCE-SEED-001')} is present as a source seed.",
            "boundary": "The application did not detect methane and does not verify the reported event.",
        },
        {
            "id": "measured_context",
            "label": "Measured context",
            "state": "measured",
            "summary": _label(terrain, "Measured terrain context unavailable"),
            "boundary": "Terrain derivatives describe landform context, not atmospheric transport.",
        },
        {
            "id": "modeled_context",
            "label": "Modeled context",
            "state": "context",
            "summary": f"Current wind: {_label(wind)}. Observation-time weather: {_label(historical)}.",
            "boundary": "Present-day wind cannot reconstruct observation-time transport.",
        },
        {
            "id": "terrain_interpretation",
            "label": "Terrain-supported interpretation",
            "state": "inferred",
            "summary": _label(integrated, "Integrated terrain response unavailable"),
            "boundary": "This is a DEM-derived visual interpretation, not CFD or verified plume routing.",
        },
        {
            "id": "uncertainty",
            "label": "Uncertainty",
            "state": "uncertain",
            "summary": f"{_label(regime)}. {_label(authority)}.",
            "boundary": "Low agreement or conflict reduces visual authority rather than creating certainty.",
        },
        {
            "id": "missing_evidence",
            "label": "Missing evidence",
            "state": "unknown",
            "summary": f"{missing_count} unresolved evidence inputs remain visible. {_label(evidence_time)}.",
            "boundary": "Missing evidence is not silently inferred or replaced by current conditions.",
        },
    ]

    recommendation = {
        "label": "Recommended human review",
        "action": "Confirm the source observation record, observation timestamp, provider geometry, and observation-time weather before interpreting transport or responsibility.",
        "priority": "evidence_completion_first",
        "not_an_enforcement_action": True,
    }

    return {
        "contract_version": "scientific_synthesis_decision_surface_v1",
        "pass_id": PASS_ID,
        "data_state": "scientific_synthesis_ready",
        "display_label": "scientific synthesis ready · evidence-separated · human review required",
        "headline": "What the evidence supports — and what it does not.",
        "sections": sections,
        "recommended_review": recommendation,
        "decision_policy": {
            "human_in_the_loop_required": True,
            "source_responsibility_attribution": False,
            "methane_detection_claim": False,
            "exact_plume_geometry_claim": False,
            "certified_quantification_claim": False,
            "enforcement_readiness_claim": False,
        },
        "claim_boundary": (
            "The scientific synthesis organizes available evidence for human review. It does not detect methane, "
            "reconstruct verified transport, quantify emissions, determine exposure, establish illegality, or attribute responsibility."
        ),
    }
