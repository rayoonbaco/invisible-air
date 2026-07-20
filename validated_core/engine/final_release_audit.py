from __future__ import annotations

from datetime import datetime, timezone

NON_NEGOTIABLE_GUARDRAILS = [
    "The application does not detect methane.",
    "The visual reconstruction is not exact provider plume geometry.",
    "The application does not provide certified emissions quantification.",
    "The application does not verify atmospheric transport or exposure.",
    "The application does not attribute responsibility, illegality, or enforcement readiness.",
]


def final_release_audit_context(scene: dict) -> dict:
    observation = scene.get("observation_contract") or {}
    terrain = scene.get("terrain_confidence") or {}
    synthesis = scene.get("scientific_synthesis_decision_surface") or {}
    disclosure = scene.get("progressive_disclosure") or {}
    composition = scene.get("level_five_visual_composition") or {}
    missing = scene.get("missing_evidence") or {}
    integrated = scene.get("integrated_terrain_response") or {}
    evidence_time = scene.get("evidence_time") or {}

    checks = [
        {"name": "Observation contract", "passed": bool(observation), "detail": observation.get("display_label", "missing")},
        {"name": "Terrain evidence contract", "passed": terrain.get("data_state") in {"terrain_confidence_ready", "terrain_confidence_unavailable_no_valid_dem"}, "detail": terrain.get("display_label", "unavailable")},
        {"name": "Evidence-time separation", "passed": bool(evidence_time), "detail": evidence_time.get("display_label", "missing")},
        {"name": "Integrated response contract", "passed": integrated.get("data_state") in {"integrated_terrain_response_cache", "integrated_terrain_response_unavailable_safe"}, "detail": integrated.get("display_label", "missing")},
        {"name": "Progressive disclosure", "passed": disclosure.get("data_state") == "progressive_disclosure_ready", "detail": disclosure.get("display_label", "missing")},
        {"name": "Scientific synthesis", "passed": synthesis.get("data_state") == "scientific_synthesis_ready", "detail": synthesis.get("display_label", "missing")},
        {"name": "Level Five composition", "passed": composition.get("status") == "ready", "detail": composition.get("display_label", "missing")},
    ]
    passed = sum(1 for item in checks if item["passed"])
    unresolved = int(missing.get("unresolved_count", len(missing.get("items") or [])) or 0)
    return {
        "contract_version": "final_release_audit_v1",
        "pass_id": "SV2-57",
        "layer": "final_scientific_audit_launch_readiness",
        "evidence_state": "release_governance",
        "data_state": "proof_release_ready" if passed == len(checks) else "release_review_required",
        "status": "ready" if passed == len(checks) else "review_required",
        "display_label": f"Final release audit · {passed}/{len(checks)} release gates passed",
        "release_name": "Invisible Air · Atmosphere Window Realtime · Level Five Proof Release",
        "release_id": "SV2-57",
        "generated_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "checks": checks,
        "passed_count": passed,
        "total_count": len(checks),
        "unresolved_evidence_count": unresolved,
        "launch_state": "human_review_ready_with_explicit_evidence_gaps" if passed == len(checks) else "hold_for_review",
        "proof_surfaces": [
            {"label": "Living scientific scene", "path": "/scene"},
            {"label": "Evidence explorer", "path": "/reviewer-guided-evidence-exploration"},
            {"label": "Scientific synthesis", "path": "/scientific-synthesis"},
            {"label": "Internal audit", "path": "/self-test"},
            {"label": "Release proof", "path": "/release-proof"},
        ],
        "guardrails": NON_NEGOTIABLE_GUARDRAILS,
        "launch_checklist": [
            "Run RUN_VERIFY_SV2_57.bat from a fresh extracted folder.",
            "Confirm the verifier reports zero failed smoke tests.",
            "Confirm /scene and /release-proof return HTTP 200.",
            "Review all visible unknowns before public demonstration.",
            "Use the proof release as a human-review prototype, not an operational emissions determination system.",
        ],
        "scene_directive": "Freeze the science, preserve every evidence boundary, and make the proof release reproducible and recoverable.",
        "claim_boundary": "Release readiness confirms software integrity, evidence-state discipline, and review usability only. It does not validate methane detection, exact plume geometry, emissions quantity, atmospheric transport, exposure, responsibility, illegality, or enforcement readiness.",
    }
