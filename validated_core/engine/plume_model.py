from __future__ import annotations


def plume_model_contract() -> dict:
    return {
        "model_name": "wind_informed_visual_reconstruction",
        "purpose": "Create visible motion around a source-seeded observation for human review.",
        "inputs": [
            "source point",
            "wind speed",
            "wind direction",
            "terrain influence label",
            "uncertainty width",
        ],
        "outputs": [
            "animated particles",
            "translucent plume ribbon",
            "uncertainty envelope",
        ],
        "not_a": [
            "methane detector",
            "certified dispersion model",
            "exact plume-product geometry",
            "source attribution engine",
        ],
    }
