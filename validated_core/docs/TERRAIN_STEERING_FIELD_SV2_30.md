# SV2-35 — Terrain Steering Field

This pass adds a map-registered spatial heuristic derived from the validated DEM and available wind context. Each supported cell is classified by its strongest bounded response: alignment, opposition, shelter, channeling, or lateral deflection.

The field is deliberately restrained and remains separate from the plume visualization. It does not claim CFD, measured airflow, methane transport, concentration, or actual atmospheric behavior.
