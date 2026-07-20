# SV2-19 — Observation Geometry Adapter

This pass adds a provider-neutral geometry adapter for Point, Polygon, MultiPolygon, FeatureCollection, and bounded raster-mask metadata.

The default state is `adapter ready · source geometry unavailable`. No exact geometry is invented. Validated provider geometry, when supplied through `AW_OBSERVATION_GEOMETRY_JSON`, remains a separate observed layer and is never merged with the current-wind visual reconstruction.
