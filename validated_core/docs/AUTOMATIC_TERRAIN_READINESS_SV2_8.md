# SV2-8 — Automatic Terrain Readiness

The reliable launcher now attempts a measured USGS elevation sample before opening the review scene.

## Behavior

- The server starts and passes `/health` first.
- The launcher requests `/terrain.json?refresh=1`.
- Twenty-five elevation points are sampled in a bounded five-worker pool.
- A usable cache requires at least four measured samples.
- The launcher prints either `TERRAIN READY` or `TERRAIN NOT MEASURED` before opening `/scene`.
- Provider failure never fabricates terrain and never blocks the scene; the plume remains in neutral terrain mode.

## Scientific boundary

Sampled elevation context can inform a restrained visual review heuristic. It is not atmospheric dispersion modeling, exact plume geometry, methane detection, emissions quantification, or source attribution.
