from __future__ import annotations


def scientific_personality_context(scene: dict) -> dict:
    """Return the restrained observational voice used across the instrument.

    This is not a persona and never expands the scientific claim. It translates
    live evidence state into a consistent cadence: notice, qualify, withhold, act.
    """
    wind = scene.get("wind", {})
    terrain = scene.get("terrain_confidence", {})
    missing = scene.get("missing_evidence", {})
    steering = scene.get("terrain_steering_field", {})

    wind_label = wind.get("label") or "Current wind context"
    terrain_label = terrain.get("display_label") or "Terrain confidence remains unresolved"
    steering_label = steering.get("display_label") or "Terrain may shape the possible movement"
    missing_label = missing.get("display_label") or "Unresolved evidence remains visible"

    return {
        "name": "The patient observer",
        "temperament": ["Attentive", "Specific", "Unhurried", "Evidence-bounded"],
        "method": "Notice. Qualify. Withhold. Invite review.",
        "phrases": {
            "source": "A reported source enters the field of view.",
            "direction": f"{wind_label} offers direction, not proof.",
            "terrain": f"{steering_label}. The land changes what is plausible.",
            "uncertainty": f"{missing_label}. The instrument leaves the gap visible.",
            "judgment": "A useful observation can remain unresolved.",
            "next_act": "Look again where the evidence becomes thin."
        },
        "evidence_posture": {
            "observed": terrain_label,
            "qualified": "Possible movement is reconstructed for review.",
            "withheld": "Transport, concentration, exposure, responsibility, and illegality are not inferred.",
            "invitation": "Inspect the record, then decide what deserves another look."
        },
        "boundary": "Scientific personality changes cadence, never claim authority."
    }
