# Pass 22A — Power to the Observatory

This correction pass preserves the complete Pass 22 visual choreography and repairs the connection between the validated Power House and the Observatory interpretation panel.

## Changes

- `RUN_OBSERVATORY.bat` now prepares and validates the DEM-derived scientific chain before opening the Observatory.
- `tools/prepare_observatory.py` refreshes the required terrain contracts in dependency order and verifies the final live scene state.
- The Observatory interpretation panel now refreshes from `/scene.json` after the map opens, replacing stale or startup-limited labels with current Power House values.
- The invitation sequence, framing, typography, atmospheric choreography, and claim boundaries are unchanged.

## Acceptance condition

When the DEM and integrated response are ready, the Observatory must not display `validated DEM missing` or `integrated response unavailable`.
