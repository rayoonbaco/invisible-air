# SV2-10 — Elevation Lighting and Local Relief

This pass converts the measured 5x5 elevation sample into a restrained visual relief layer beneath the plume.

## What is measured
- Point elevations returned by the USGS elevation service
- Sampled minimum, maximum, and local elevation range

## What is interpreted
- Coarse 4x4 lighting cells
- Northwest-facing visual illumination
- Sparse quartile contour cues
- Local relief intensity per cell

## Boundary
This is not a continuous DEM, certified hillshade, remote-sensing product, or atmospheric model. It is a coarse scene-reading aid derived from sparse measured points. The plume remains a visual review heuristic.
