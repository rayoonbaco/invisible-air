from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Literal

LayerStatus = Literal["planned", "static", "live_stub", "live", "missing"]
ClaimStrength = Literal["source_seeded", "context", "visual_reconstruction", "missing", "not_claimable"]


@dataclass(frozen=True)
class Provenance:
    layer_id: str
    status: LayerStatus
    source_label: str
    claim_strength: ClaimStrength
    what_is_real: str
    what_is_reconstruction: str
    what_is_missing: str
    boundary: str

    def to_dict(self) -> dict:
        return asdict(self)


def boundary_pack() -> dict:
    return {
        "core_boundary": "This app did not detect methane. It visualizes context around a source-seeded observation for human review.",
        "not_claimed": [
            "not methane detection",
            "not exact plume-product geometry",
            "not certified emissions quantification",
            "not facility attribution",
            "not enforcement or illegality",
        ],
        "safe_language": [
            "reported signal",
            "source-seeded observation",
            "visual plume reconstruction",
            "live/current wind context when available",
            "human review only",
        ],
    }
