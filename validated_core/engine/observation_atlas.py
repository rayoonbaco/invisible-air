from __future__ import annotations

from typing import Any

SCIENTIFIC_STATE_LEGEND: tuple[dict[str, str], ...] = (
    {"id":"reported","label":"Reported","meaning":"A traceable source or observation record says this occurred or was observed."},
    {"id":"measured","label":"Measured","meaning":"A sensor, survey, or validated dataset directly supplies this property."},
    {"id":"contextual","label":"Contextual","meaning":"Later or surrounding information helps interpret the case but does not recreate the observation."},
    {"id":"inferred","label":"Inferred","meaning":"A review hypothesis derived from reported, measured, and contextual inputs; it is not a direct observation."},
)

REQUIRED_PACKAGE_FIELDS: tuple[str, ...] = (
    "case_id", "title", "source_record", "observation_time", "source_geometry",
    "provider_geometry", "terrain_bbox", "wind_context", "citations", "claim_boundaries",
)

OBSERVATION_CASES: tuple[dict[str, Any], ...] = (
    {
        "id": "ventura-oxnard", "title": "Ventura–Oxnard",
        "subtitle": "Coastal plain meeting complex terrain", "status": "validated_live",
        "status_label": "Validated live case", "available": True,
        "question": "How may current wind and terrain shape a possible movement from the reported source?",
        "source_note": "Uses the existing validated Invisible Air observation contract and Power House terrain chain.",
        "insight_label": "Field Insight",
        "field_insight": "Current wind carries the possible field toward rising terrain, while missing observation-time evidence limits the conclusion.",
        "visual_caption": "A reported source, current directional context, rising relief, and a visible gap where observation-time evidence should be.",
        "visual_signals": (
            {"name":"Land","kind":"terrain","state":"present","note":"Relief visible"},
            {"name":"Air","kind":"air","state":"context","note":"Current direction"},
            {"name":"Time","kind":"time","state":"missing","note":"Observation time absent"},
            {"name":"Trust","kind":"trust","state":"limited","note":"Evidence-limited"},
        ),
        "scientific_states": (
            {"state":"reported","label":"Reported","subject":"Source record","statement":"A traceable record anchors the source location used for review."},
            {"state":"measured","label":"Measured","subject":"Terrain","statement":"Validated elevation data describe the land surface and relief."},
            {"state":"contextual","label":"Contextual","subject":"Current wind","statement":"Present wind context guides review but is not observation-time wind."},
            {"state":"inferred","label":"Inferred","subject":"Possible movement","statement":"The visible field is a review reconstruction, not detected or verified transport."},
        ),
        "record_status": {
            "label":"Case record complete",
            "detail":"10/10 required record fields present",
            "interpretation":"Interpretation unresolved",
            "boundary":"Record completeness does not equal scientific certainty."
        },
        "comparison": {
            "terrain": "Coastal plain meeting steep relief",
            "atmosphere": "Current wind context only",
            "evidence_time": "Observation time unresolved",
            "uncertainty": "Elevated; interpretation remains evidence-limited",
            "provenance": "Existing source registry, citations, and validated terrain chain",
        },
        "package_fields_present": list(REQUIRED_PACKAGE_FIELDS),
        "living_state": {
            "mode": "awake",
            "label": "Observation awake",
            "now": "Current wind context is visible beside the reported source and terrain.",
            "holds": "The verified case package is present, while observation-time evidence and several scientific inputs remain unresolved.",
            "next": "Return when time-aligned wind, terrain confidence, or source evidence changes.",
            "memory": "The Atlas preserves the current interpretation without promoting it into a finding.",
        },
        "evidence_sequence": (
            {"label": "Reported", "state": "retained", "text": "A traceable source record anchors the case."},
            {"label": "Context added", "state": "current", "text": "Current wind and terrain provide a direction for review."},
            {"label": "Still missing", "state": "unresolved", "text": "Observation-time atmospheric evidence remains absent."},
        ),
        "temporal_trace": (
            {"label":"Source record","state":"retained","note":"Traceable record present"},
            {"label":"Observation time","state":"gap","note":"Atmospheric evidence absent"},
            {"label":"Current context","state":"context","note":"Wind and terrain added later"},
            {"label":"Next review","state":"open","note":"Interpretation may change"},
        ),
    },
    {
        "id": "open-basin", "title": "Open Basin",
        "subtitle": "Wind-dominant comparison case", "status": "awaiting_verified_package",
        "status_label": "Awaiting verified observation", "available": False,
        "question": "How does a possible movement read where terrain influence is comparatively weak?",
        "source_note": "Reserved until a traceable observation geometry, time, source record, and evidence package are supplied.",
        "insight_label": "Comparison Premise",
        "field_insight": "In low relief, wind would likely dominate the comparison, but no verified observation package is active yet.",
        "visual_caption": "A dormant low-relief premise. No source, timestamp, or atmospheric scene is drawn without a verified package.",
        "visual_signals": (
            {"name":"Land","kind":"terrain","state":"premise","note":"Low relief proposed"},
            {"name":"Air","kind":"air","state":"missing","note":"Context required"},
            {"name":"Time","kind":"time","state":"missing","note":"Timestamp required"},
            {"name":"Trust","kind":"trust","state":"withheld","note":"Not assessed"},
        ),
        "scientific_states": (
            {"state":"reported","label":"Reported","subject":"Case premise","statement":"A comparison question is reserved; no observation is reported."},
            {"state":"measured","label":"Measured","subject":"Terrain","statement":"No case-specific measured terrain package is active."},
            {"state":"contextual","label":"Contextual","subject":"Atmosphere","statement":"No observation-time or current atmospheric context is active."},
            {"state":"inferred","label":"Inferred","subject":"Movement","statement":"No movement interpretation is permitted until verified material arrives."},
        ),
        "record_status": {
            "label":"Case record incomplete",
            "detail":"0/10 required record fields present",
            "interpretation":"Interpretation withheld",
            "boundary":"No scene or conclusion is generated from a reserved premise."
        },
        "comparison": {"terrain":"Open or low-relief basin required","atmosphere":"Observation-time context required","evidence_time":"Timestamp required","uncertainty":"Not yet assessed","provenance":"Verified source package required"},
        "package_fields_present": [],
        "living_state": {
            "mode": "waiting",
            "label": "Waiting for evidence",
            "now": "The comparison premise is held without generating a scene.",
            "holds": "No verified observation geometry, timestamp, or source package is active.",
            "next": "Wake this case only when a complete, traceable package arrives.",
            "memory": "The empty place is intentional; absence remains visible rather than being filled with invention.",
        },
        "evidence_sequence": (
            {"label": "Reserved", "state": "retained", "text": "A comparison question has been defined."},
            {"label": "Package", "state": "unresolved", "text": "Verified evidence has not been supplied."},
            {"label": "Scene", "state": "withheld", "text": "Atmospheric visualization remains unavailable."},
        ),
        "temporal_trace": (
            {"label":"Premise","state":"retained","note":"Question reserved"},
            {"label":"Observation time","state":"gap","note":"Timestamp required"},
            {"label":"Evidence package","state":"gap","note":"Verified material required"},
            {"label":"Activation","state":"withheld","note":"Scene remains asleep"},
        ),
    },
    {
        "id": "mountain-corridor", "title": "Mountain Corridor",
        "subtitle": "Terrain-complex comparison case", "status": "awaiting_verified_package",
        "status_label": "Awaiting verified observation", "available": False,
        "question": "How may valleys, ridges, and gaps change the range of plausible movement?",
        "source_note": "Reserved until a traceable observation geometry, time, source record, and evidence package are supplied.",
        "insight_label": "Comparison Premise",
        "field_insight": "Complex relief could narrow plausible movement paths, but no verified observation package is active yet.",
        "visual_caption": "A dormant terrain-complex premise. The corridor remains a ghost until evidence can justify a scene.",
        "visual_signals": (
            {"name":"Land","kind":"terrain","state":"premise","note":"Complex relief proposed"},
            {"name":"Air","kind":"air","state":"missing","note":"Context required"},
            {"name":"Time","kind":"time","state":"missing","note":"Timestamp required"},
            {"name":"Trust","kind":"trust","state":"withheld","note":"Not assessed"},
        ),
        "scientific_states": (
            {"state":"reported","label":"Reported","subject":"Case premise","statement":"A comparison question is reserved; no observation is reported."},
            {"state":"measured","label":"Measured","subject":"Terrain","statement":"No case-specific measured terrain package is active."},
            {"state":"contextual","label":"Contextual","subject":"Atmosphere","statement":"No observation-time or current atmospheric context is active."},
            {"state":"inferred","label":"Inferred","subject":"Movement","statement":"No movement interpretation is permitted until verified material arrives."},
        ),
        "record_status": {
            "label":"Case record incomplete",
            "detail":"0/10 required record fields present",
            "interpretation":"Interpretation withheld",
            "boundary":"No scene or conclusion is generated from a reserved premise."
        },
        "comparison": {"terrain":"Valley, ridge, or gap geometry required","atmosphere":"Observation-time context required","evidence_time":"Timestamp required","uncertainty":"Not yet assessed","provenance":"Verified source package required"},
        "package_fields_present": [],
        "living_state": {
            "mode": "waiting",
            "label": "Waiting for evidence",
            "now": "The comparison premise is held without generating a scene.",
            "holds": "No verified observation geometry, timestamp, or source package is active.",
            "next": "Wake this case only when a complete, traceable package arrives.",
            "memory": "The empty place is intentional; absence remains visible rather than being filled with invention.",
        },
        "evidence_sequence": (
            {"label": "Reserved", "state": "retained", "text": "A comparison question has been defined."},
            {"label": "Package", "state": "unresolved", "text": "Verified evidence has not been supplied."},
            {"label": "Scene", "state": "withheld", "text": "Atmospheric visualization remains unavailable."},
        ),
        "temporal_trace": (
            {"label":"Premise","state":"retained","note":"Question reserved"},
            {"label":"Observation time","state":"gap","note":"Timestamp required"},
            {"label":"Evidence package","state":"gap","note":"Verified material required"},
            {"label":"Activation","state":"withheld","note":"Scene remains asleep"},
        ),
    },
)

def _case_payload(case: dict[str, Any]) -> dict[str, Any]:
    payload=dict(case)
    present=set(case.get("package_fields_present", []))
    payload["readiness"]={
        "present": len(present), "required": len(REQUIRED_PACKAGE_FIELDS),
        "percent": round(100*len(present)/len(REQUIRED_PACKAGE_FIELDS)),
        "missing": [field for field in REQUIRED_PACKAGE_FIELDS if field not in present],
    }
    return payload

def observation_atlas(selected_id: str | None = None) -> dict[str, Any]:
    selected = next((case for case in OBSERVATION_CASES if case["id"] == selected_id and case["available"]), OBSERVATION_CASES[0])
    cases=[_case_payload(case) for case in OBSERVATION_CASES]
    selected_payload=next(case for case in cases if case["id"]==selected["id"])
    return {
        "display_label": "Observation Atlas · comparison instrument",
        "selected_id": selected["id"], "selected": selected_payload, "cases": cases,
        "available_count": sum(1 for case in cases if case["available"]), "total_count": len(cases),
        "required_package_fields": list(REQUIRED_PACKAGE_FIELDS),
        "scientific_state_legend": list(SCIENTIFIC_STATE_LEGEND),
        "template_url": "/observation-atlas/template.json",
        "living_principle": "The Atlas records changes in evidence state, not merely the passage of time.",
        "living_note": "Awake cases may gain, lose, or qualify support as evidence changes. Waiting cases remain quiet until verified material arrives.",
        "boundary": "Only cases with a verified observation package may generate an atmospheric scene. Reserved cases remain unavailable rather than using invented geometry or evidence.",
    }
