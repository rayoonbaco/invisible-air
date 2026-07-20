# Realtime Scene Architecture

## Goal

Build a real scene engine that can eventually render:

```text
real terrain + real map context + live/current wind + source-seeded or exact methane observation + animated plume reconstruction + evidence boundaries
```

## Principle

Real place first. Interpretation second. Text last.

## V2-1 scope

V2-1 creates the skeleton only. It does not yet fetch DEMs, live wind, or exact plume geometry.

## Scene flow

```text
scene_config -> source registry -> scene template -> canvas plume renderer -> evidence drawer
```

## Future live data order

1. basemap / real map surface
2. terrain DEM / hillshade / contours
3. current wind connector
4. observation source manifest
5. exact plume geometry when verified
