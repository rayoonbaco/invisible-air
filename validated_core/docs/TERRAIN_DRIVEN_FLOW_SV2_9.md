# SV2-9 — Terrain-Driven Flow

## Purpose
Use the measured 5 × 5 elevation sample grid to make the visual review pathway respond to landform context instead of remaining a straight wind-axis graphic.

## What changed
- Eleven map-registered pathway nodes are generated downwind.
- Each interior node compares interpolated elevation on the left and right sides of the wind axis.
- The visual pathway can shift gently toward relatively lower sampled ground.
- Cross-path elevation contrast increases the visible disruption cue.
- Lateral movement is smoothed twice and capped at 1.35 km.
- The plume canvas follows the curved node path.
- The uncertainty boundary is now a path-following tube rather than a single straight ellipse when terrain data is available.

## Scientific boundary
This is a sparse-elevation visual review heuristic. It is not atmospheric fluid dynamics, methane transport simulation, exact plume geometry, source attribution, or certified emissions analysis.

## Honest fallback
When measured terrain is unavailable, the path remains on the neutral current-wind axis.
