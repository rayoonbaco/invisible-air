# SV2-20 — Certified Hillshade Lane

This pass derives a continuous, reproducible hillshade from the validated cached USGS 3DEP DEM.

"Certified" refers to the internal derivation contract: the source DEM hash, illumination azimuth, illumination altitude, z-factor, output dimensions, generation time, and output hash are recorded and testable. It does not mean the rendered hillshade is certified or endorsed by USGS or another agency.

## Fixed derivation

- illumination azimuth: 315 degrees
- illumination altitude: 45 degrees
- z-factor: 1.0
- source: validated continuous DEM cache only
- output: grayscale PNG registered to the DEM bounding box

## Failure behavior

No valid DEM means no hillshade. Sparse elevation points are not promoted into this lane. A failed or invalid raster derivation remains visibly unavailable.

## Boundary

The hillshade is terrain context. It is not methane evidence, event-time sunlight, atmospheric transport, or a scientific conclusion about emissions.
