# SV2-4 Terrain Loader

## Purpose

SV2-4 introduces the first measured-terrain data lane without pretending that terrain is already a dispersion model.

## Loader behavior

- A 5 x 5 point grid is generated across the current scene bbox.
- On explicit refresh, elevation points are requested from the configured USGS Elevation Point Query Service endpoint.
- Successful values are cached in `data/terrain_cache/default_scene_terrain.json`.
- Local relief, mean elevation, a dominant sampled change direction, and a restrained terrain class are derived from the cached points.
- Normal app startup never depends on an external service.

## Routes

- `/terrain` shows the terrain lane and its evidence state.
- `/terrain.json` returns the current contract/cache.
- `/terrain.json?refresh=1` attempts a live measured-elevation refresh.

## Evidence language

Measured elevation is geographic context. The terrain interpretation is a sampled review cue. It is not methane detection, exact plume geometry, source attribution, emissions quantification, or atmospheric dispersion modeling.

## Next terrain upgrades

1. Replace point sampling with a clipped DEM raster.
2. Derive hillshade, contours, slope, aspect, and local relief surfaces.
3. Register those visual products beneath the plume.
4. Test whether terrain visibly changes pathway interpretation while retaining uncertainty.
