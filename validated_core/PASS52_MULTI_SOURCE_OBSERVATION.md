# Pass 52 — Multi-Source Observation

## Purpose

Give the Atmospheric Observatory one memorable public interaction without adding tabs, cards, or an advanced control dashboard.

## What changed

- Three curated source pins are present in each local scenario.
- Visitors can arm **Add source** and place up to two additional sources directly on the map.
- **Undo** removes the most recent visitor source; **Reset** restores the three curated sources.
- Every source is sent through the existing governing model independently.
- The browser composites the independent dimensionless fields so traces may overlap, merge visually, or remain separate.
- Numbered source markers make the relationship between origins and fields legible.
- Terrain comparison, material selection, live conditions, and the existing scenario pipeline remain intact.

## Scientific boundary

Overlap represents combined relative influence. It is not measured smoke concentration, chemical interaction, exposure, AQI, a smoke forecast, or a fire perimeter.

## Governing-model status

The numerical governing model was not rewritten. The endpoint now accepts bounded source-coordinate overrides so the same model can be evaluated independently at several locations.
