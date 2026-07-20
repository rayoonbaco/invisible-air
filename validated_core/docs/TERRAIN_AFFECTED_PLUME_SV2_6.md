# SV2-6 — Terrain-Affected Plume Behavior

This pass makes measured terrain context visibly affect the coordinate-registered plume reconstruction.

When a valid USGS elevation cache exists, sampled relief changes the visual corridor's width, length, turbulence, and a small capped bend toward the sampled landform axis. When measured terrain is unavailable, behavior remains neutral and explicitly unresolved.

This is a visual review heuristic. It is not methane detection, exact plume-product geometry, atmospheric dispersion modeling, source attribution, emissions quantification, or enforcement evidence.

## One-click confirmation

- `RUN_LOCAL.bat` starts the server and opens `/scene`.
- `RUN_VERIFY_SV2_6.bat` runs smoke tests, starts the server, then opens `/scene` and `/self-test`.
