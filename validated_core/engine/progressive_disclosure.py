from __future__ import annotations

from typing import Any

PASS_ID = "SV2-54"


def progressive_disclosure_context(scene: dict[str, Any]) -> dict[str, Any]:
    """Define visibility tiers without removing scientific content."""
    immediate = [
        "reported_observation",
        "measured_terrain",
        "current_wind",
        "integrated_response",
        "confidence_uncertainty",
    ]
    context = [
        "terrain_steering",
        "terrain_regimes",
        "historical_atmosphere",
        "provenance",
        "missing_evidence",
        "annotations_timeline",
    ]
    audit = [
        "derived_rasters",
        "component_contracts",
        "source_registry",
        "machine_readable_json",
        "smoke_tests",
        "claim_boundaries",
    ]
    return {
        "contract_version": "progressive_disclosure_v1",
        "pass_id": PASS_ID,
        "data_state": "progressive_disclosure_ready",
        "display_label": "progressive disclosure active · calm overview · context on demand · full audit preserved",
        "default_level": "overview",
        "levels": [
            {
                "id": "overview",
                "label": "Overview",
                "description": "The minimum complete scientific scene: place, observation, present context, primary interpretation, confidence, and uncertainty.",
                "content": immediate,
            },
            {
                "id": "context",
                "label": "Context",
                "description": "Supporting terrain, atmospheric, provenance, and missing-evidence context shown on demand.",
                "content": context,
            },
            {
                "id": "audit",
                "label": "Deep audit",
                "description": "All derived layers, numerical contracts, routes, smoke tests, and claim boundaries remain available.",
                "content": audit,
            },
        ],
        "scene_policy": {
            "science_removed": False,
            "uncertainty_visible_in_overview": True,
            "missing_evidence_available_in_context": True,
            "deep_routes_preserved": True,
            "default_status_items_max": 6,
            "default_navigation_items_max": 6,
            "reviewer_can_change_level": True,
            "selection_persists_locally": True,
        },
        "navigation": {
            "primary": ["Scene", "Explore", "Evidence", "Observation", "Audit"],
            "technical_routes_location": "deep_audit_drawer",
        },
        "claim_boundary": (
            "Progressive disclosure changes visibility and reading order only. It does not remove evidence, "
            "increase confidence, detect methane, reconstruct transport, quantify emissions, or attribute responsibility."
        ),
    }
