from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.scene_config import default_scene_config


def label(contract: object) -> str:
    if isinstance(contract, dict):
        return str(contract.get("display_label") or contract.get("data_state") or "ready")
    return "missing"


def power_ready(scene: dict) -> bool:
    dem = scene.get("full_dem") or {}
    integrated = scene.get("integrated_terrain_response") or {}
    return (
        dem.get("data_state") == "continuous_dem_cache"
        and integrated.get("data_state") == "integrated_terrain_response_cache"
    )


def main() -> int:
    print("Checking the validated Power House state...")
    scene = default_scene_config()

    if not power_ready(scene):
        print("Power House cache is incomplete. Preparing the terrain chain now...")
        scene = default_scene_config(
            refresh_dem=True,
            refresh_hillshade=True,
            refresh_slope_aspect=True,
            refresh_landforms=True,
            refresh_terrain_confidence=True,
        )

    dem = scene.get("full_dem") or {}
    terrain = scene.get("terrain_confidence") or {}
    steering = scene.get("terrain_steering_field") or {}
    integrated = scene.get("integrated_terrain_response") or {}

    print("\nOBSERVATORY POWER CHECK")
    print(f"DEM ................. {label(dem)}")
    print(f"Terrain confidence .. {label(terrain)}")
    print(f"Steering field ...... {label(steering)}")
    print(f"Integrated response . {label(integrated)}")

    if power_ready(scene):
        print("\nPASS: The Observatory is connected to the validated Power House state.")
    else:
        print("\nWARNING: The Observatory will open honestly in evidence-limited mode.")
        print("The live panel will continue checking for prepared Power House state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
