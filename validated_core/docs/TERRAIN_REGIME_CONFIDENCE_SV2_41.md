# SV2-41 — Terrain-Regime Confidence and Boundary Ambiguity

This pass scores spatial support for the DEM-derived terrain-regime interpretation and marks locations where adjacent terrain-response classes are weakly separated.

## Outputs
- map-registered regime-confidence illumination
- map-registered boundary-ambiguity veil
- confidence and ambiguity statistics
- downgrade reasons and source hashes

## Scientific boundary
Terrain-regime confidence is confidence in the supporting terrain interpretation only. Boundary ambiguity is not an atmospheric front, plume edge, methane-confidence layer, concentration field, exposure estimate, or proof of actual airflow.
