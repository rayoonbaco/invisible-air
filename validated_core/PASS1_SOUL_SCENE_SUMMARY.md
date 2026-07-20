# Invisible Air - Pass 1 Soul Scene Reconstruction

## Purpose
Move the primary `/scene` experience from dashboard-first to phenomenon-first without changing the scientific engines or data contracts.

## Files changed
- `templates/scene.html`
- `static/css/styles.css`

## What changed
- Removed the separate oversized editorial introduction above the scene.
- Removed the permanent external report column from the page layout.
- Made the map and atmospheric reconstruction fill the working viewport.
- Added a restrained in-scene introduction: `See the air.`
- Reduced the default evidence status to four quiet state markers.
- Converted the former report column into a compact in-scene interpretation panel.
- Kept Context and Audit as progressive-disclosure states.
- Preserved evidence routes, citations, scientific boundaries, terrain logic, wind logic, plume rendering, and all scientific contracts.
- Added responsive behavior for tablet and phone widths.

## Scientific boundary
This pass changes visibility, hierarchy, and composition only. It does not upgrade source evidence, observation-time weather, provider plume geometry, or transport-model authority.

## Verification
- Python compile: PASS
- Smoke tests: 499 passed, 0 failed
- Release audit: PASS
- Release gates: 7/7
- Routes checked: 8
- `/scene` Flask response: HTTP 200

## Local run
Run `RUN_VERIFY_SV2_57.bat`, then open:

`http://127.0.0.1:8000/scene`

## Human visual review
Confirm that:
1. the air scene dominates the first viewport;
2. the right interpretation panel does not obscure the source or main movement;
3. the Scene / Context / Audit controls work;
4. evidence routes remain accessible;
5. the new opening reads as an uncertain reconstruction rather than direct methane detection.
