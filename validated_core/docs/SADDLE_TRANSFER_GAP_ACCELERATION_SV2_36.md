# SV2-36 — Saddle Transfer and Gap Acceleration

This pass derives map-registered saddle-transfer and gap-acceleration potentials from the validated DEM, available wind context, and steering confidence.

## Boundaries
These layers are visual heuristics. They are not measured airflow, verified Venturi acceleration, CFD, plume routing, methane concentration, travel time, exposure, or proof of actual atmospheric behavior.

## Motion limits
- Saddle transfer lift is capped at 6.5 pixels.
- Gap speed multiplier is capped at 1.18×.
- Gap coherence is capped at 88%.
