# SV2-2 — Real Map Surface

## Purpose

Replace the abstract placeholder surface with a real web-map surface under the animated plume canvas.

## Decision

Use a no-key Leaflet/OpenStreetMap standard tile endpoint for the first real map surface.

## Boundary

The basemap is geographic context only. It is not methane evidence, exact plume-product geometry, attribution, certified quantification, enforcement, or facility responsibility.

## Fallback

If browser internet access or tile loading fails, the app keeps the local fallback surface visible and preserves the same claim boundary.

## Next

SV2-3 should add a real terrain loader: DEM, hillshade, local relief, slope, contours, and terrain influence metadata.
