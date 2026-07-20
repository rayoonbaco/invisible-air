# SV2-3 - Map-Registered Plume + Terrain Basemap Prep

## Purpose
SV2-3 moves the plume from screen-only positioning into map coordinate space.

The source marker, plume centerline, uncertainty envelope, and animated particles now share latitude/longitude geometry. This prepares the scene for real terrain, wind, and exact observation geometry later.

## What is real now
- Browser-loaded map tiles when internet access is available.
- Source marker defined by latitude/longitude.
- Plume centerline and uncertainty envelope defined by latitude/longitude.
- Canvas particles are redrawn from map coordinates each frame.
- Basemap mode selector for standard, terrain/topo prep, and dark review.

## What is still reconstruction
- The plume is still a visual reconstruction.
- The source seed is not exact methane product geometry.
- The wind vector is a default configuration until live wind is connected.
- Terrain mode is a basemap preparation step, not DEM-derived science yet.

## Boundary
Coordinate registration makes the scene more spatially honest, but it does not make the plume an observed product geometry. Exact plume geometry must come from a verified observation product before it can be shown as source product data.
