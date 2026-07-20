# SV2-27 — Terrain Confidence

This pass scores the terrain evidence stack across DEM coverage, valid-cell ratio, source resolution, cache integrity, derivative completeness, landform completeness, and landform classification confidence. It also hardens landform local-relief calculation by clamping tiny negative floating-point values before square root.

The composite score is an evidence-quality summary, not scientific certainty and not methane confidence.
