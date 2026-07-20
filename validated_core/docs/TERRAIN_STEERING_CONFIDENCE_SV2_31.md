# SV2-35 — Steering-Field Confidence and Uncertainty

This pass adds spatial confidence and uncertainty to the DEM-derived Terrain Steering Field. Confidence combines terrain-evidence quality, steering-signal strength, spatial coherence, and available atmospheric support. Missing observation-time atmosphere visibly downgrades the result.

The confidence field applies only to the terrain-steering heuristic. It is not confidence in methane presence, plume position, actual airflow, emissions magnitude, or attribution.
