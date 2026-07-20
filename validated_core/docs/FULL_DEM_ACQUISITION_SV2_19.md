# SV2-19 — Full DEM Acquisition

This pass adds a continuous USGS 3DEP raster acquisition lane for the scene bbox. The raster is cached as a TIFF with a JSON sidecar containing bbox, grid size, approximate pixel size, retrieval time, byte size, SHA-256 integrity, coverage state, and failure state.

The pass does not yet claim hillshade, slope, aspect, curvature, landform classification, or 3D terrain. Those depend on this raster and remain separate passes. Provider failure leaves the prior sparse terrain lane active and explicitly marks the continuous DEM as unavailable.
