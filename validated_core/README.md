## Current verified pass: SV2-56 — Level Five Visual Composition and Performance

# SV2-36 — Saddle Transfer and Gap Acceleration

# Atmosphere Window Realtime — SV2-36

## Ridge Spillover and Lee-Side Shelter

SV2-36 adds confidence-gated, map-registered ridge-spillover and lee-side-shelter potentials derived from the validated DEM and available wind context. The fields remain visual heuristics, not CFD or measured airflow.

Run `RUN_VERIFY_SV2_34.bat`. The launcher opens only the main scene.

# Atmosphere Window Realtime

Atmosphere Window Realtime is a clean V2 scene engine for building a real atmospheric evidence window around a source-seeded methane observation.

## Current pass

**SV2-19 — Full DEM Acquisition**

The app preserves the map-registered plume scene and adds the first terrain data lane: a USGS elevation sample-grid connector, local cache, terrain influence classifier, terrain routes, and evidence boundaries. No relief value is fabricated when the measured cache is absent.

## Run locally

Double-click:

```text
RUN_LOCAL.bat
```

Or run:

```cmd
cd "C:\PROJECTS\ATMOSPHERE_WINDOW_REALTIME"
RUN_LOCAL.bat
```

Open:

```text
http://127.0.0.1:8000/scene
```

## Main routes

```text
/              launch window
/scene         realtime map-registered scene
/shot          screenshot mode
/scene.json    scene configuration
/map-surface   map surface and basemap mode notes
/terrain       terrain evidence lane
/terrain.json  terrain contract; add ?refresh=1 to attempt a measured cache
/evidence      evidence drawer
/data-status   layer registry
/audit         claim boundaries
/hunter        HUNTER Lens prompts
```

## What is real now

- Real browser-loaded map tiles when available.
- Source marker is defined by coordinates.
- Plume centerline and uncertainty envelope are defined by coordinates.
- Animated plume particles recalculate from map coordinates each frame.
- Basemap modes prepare for terrain/topo review.
- Terrain loader can explicitly sample and cache USGS elevation context.
- Cached samples produce local relief and a restrained terrain influence cue.

## What is not claimed

- The app did not detect methane.
- The moving plume is not live methane movement.
- The plume is not exact source-product geometry.
- The map is not methane evidence.
- The scene does not attribute responsibility, quantify certified emissions, or support enforcement.

## Next pass

**SV2-5** should replace point sampling with a clipped DEM raster and register hillshade/contours beneath the plume.

## SV2-5 — Live Wind Connector

The scene now loads current 10 m wind from Open-Meteo with a fifteen-minute local cache and a clearly labeled fallback vector. The map-registered visual corridor rotates to the current wind-to direction. Current weather is not presented as observation-time wind.

### Automatic pass checks

Double-click `RUN_SMOKE_TESTS.bat` after extracting each pass. A successful run ends with `PASS` and reports the number of checks. While the app is running, open `http://127.0.0.1:8000/self-test` for the lightweight in-app report.

Useful routes:

- `http://127.0.0.1:8000/scene`
- `http://127.0.0.1:8000/wind`
- `http://127.0.0.1:8000/wind.json?refresh=1`
- `http://127.0.0.1:8000/self-test`


## SV2-6 — Terrain-Affected Plume Behavior

This pass adds bounded terrain-aware visual behavior and one-click launch confirmation. Double-click `RUN_LOCAL.bat` to start the app and open `/scene`. Double-click `RUN_VERIFY_SV2_6.bat` to run smoke tests and open both `/scene` and `/self-test`. Terrain effects remain a visual review heuristic, not dispersion modeling.


## SV2-7 — Reliable Local Launch and Confirmation Gate

Double-click `RUN_LOCAL.bat`. It now starts from its own extracted folder, waits for `/health` to return ready, and only then opens `http://127.0.0.1:8000/scene`. It no longer uses the malformed nested `cmd /k` quotation pattern that failed on Windows.

For a tested launch, double-click `RUN_VERIFY_SV2_7.bat`. It runs the smoke suite, starts the server if needed, waits for readiness, and opens both `/scene` and `/self-test`.


## SV2-8 automatic terrain readiness

Use `RUN_VERIFY_SV2_8.bat`. It runs smoke tests, starts the server, attempts a measured USGS elevation cache, prints the terrain result, and opens `/scene` plus `/self-test`. Provider failure leaves the plume in honest neutral terrain mode.

## SV2-11 — Terrain-Driven Flow

Use `RUN_VERIFY_SV2_9.bat`. The launcher runs 93 smoke checks, prepares measured terrain, prints a compact project-health summary, and opens `/scene` plus `/self-test`.

The plume now follows an eleven-node, map-registered visual pathway. Sparse measured elevations are sampled on both sides of the current-wind axis; the pathway can shift gently toward relatively lower sampled ground and show added disruption where cross-path elevation contrast is stronger. Lateral steering is smoothed and capped at 1.35 km.

This remains a terrain-informed visual review heuristic—not atmospheric dispersion modeling, exact methane geometry, source attribution, or certified emissions analysis.


## SV2-11 — Air Volume
Measured elevation samples now create a restrained local-relief lighting veil and sparse contour cues beneath the plume. This is a coarse visual interpretation, not a continuous DEM or certified hillshade. Run `RUN_VERIFY_SV2_11.bat`.


## SV2-12 — Living Wind

**Runtime verification correction:** partial elevation responses that cannot form a complete relief cell now remain explicitly sparse/safe, and the verification launcher exits with failure while printing the exact failed check.

Current wind now changes motion cadence, particle spacing, gust pulses, cross-plume sway, turbulence pockets, and bounded terrain-wake cues. These are visual review devices, not a measured turbulence field or atmospheric simulation. Run `RUN_VERIFY_SV2_12.bat`.

## SV2-13 — Evidence-Time Alignment

Current wind and the reported observation now have separate time contracts. The default scene states that the observation timestamp is unresolved, labels current wind as present-day context only, and refuses to imply historical transport. A real ISO-8601 observation timestamp may later be supplied through `AW_OBSERVATION_TIME_UTC`; the app will display the gap without pretending that current wind is event-time weather.

Run `RUN_VERIFY_SV2_13.bat` and confirm both the standalone suite and live `/self-test` pass.

## SV2-14 — Observation Evidence Contract

The reported observation now has a formal provider-neutral record containing identity, provider, product type, time state, coordinates, source URL state, retrieval date state, geometry status, quantification status, confidence status, and an explicit missing-field list. No absent source metadata is fabricated.

Run `RUN_VERIFY_SV2_14.bat`, then inspect `/scene`, `/self-test`, and `/observation`.


## SV2-15 — Citation Surface

Every visible scientific layer now has a compact, machine-readable citation record with source, source type, time state, retrieval state, claim class, and boundary. Run `RUN_VERIFY_SV2_15.bat`, then inspect `/scene`, `/citations`, and `/self-test`.


## SV2-19 — Evidence-State Vocabulary

The scene now uses one controlled evidence language across observation, measured terrain, current context, contextual map layers, visual reconstruction, explicit unknowns, unavailable data, not-modeled science, and not-claimed conclusions. Run `RUN_VERIFY_SV2_16.bat`, then inspect `/scene`, `/evidence-states`, `/citations`, and `/self-test`.


## SV2-19 — Missing-Evidence Visualization
Missing evidence now has a formal contract, a dedicated review surface, and visible scene consequences. Run `RUN_VERIFY_SV2_17.bat`.

## SV2-19 — Observation Geometry Adapter

Adds `/observation-geometry` and `/observation-geometry.json`. The adapter validates provider-supplied Point, Polygon, MultiPolygon, FeatureCollection, or RasterMask contracts. The default scene remains geometry-unavailable and does not invent exact plume geometry.


## SV2-19 — Full DEM Acquisition

Adds a continuous USGS 3DEP TIFF acquisition and integrity-checked local cache for the scene bbox. Use `RUN_VERIFY_SV2_19.bat`, then inspect `/dem`, `/dem.json`, `/scene`, and `/self-test`. Provider failure remains safe and keeps the sparse measured terrain lane active.

## SV2-21 — Slope and Aspect

SV2-21 derives a continuous, reproducible hillshade from the validated USGS 3DEP DEM cache. The derivation records the DEM hash, requested bounds, output dimensions, fixed illumination azimuth (315°), altitude (45°), z-factor (1.0), generation time, and output hash.

Run `RUN_VERIFY_SV2_21.bat`. The verifier acquires the DEM, derives hillshade, validates the live contracts, and opens only `/scene`; every review surface remains available through navigation.

The hillshade is not agency-certified, methane evidence, event-time sunlight, or atmospheric transport modeling.


## One-page launch behavior
`RUN_VERIFY_SV2_21.bat` tests and prepares all layers but opens only `/scene`. Review pages remain available from the top navigation.


## SV2-27 corrected launcher

The verification launcher now executes the landform refresh endpoint after slope/aspect preparation. A valid continuous DEM can no longer finish with a merely pending landform cache while the pass reports approval. The live internal verifier also requires DEM-derived landforms whenever a valid DEM is present.


## SV2-27
Run `RUN_VERIFY_SV2_23.bat`. The launcher opens only `/scene` while testing all terrain confidence layers.


## SV2-27
Historical weather retrieval with observation-time gating, nearest-hour selection, cache provenance, and strict separation from current wind.

## SV2-27 — Boundary-Layer Depth
Adds timestamp-gated historical wind at nominal 10 m and 100 m heights. The levels remain contextual and do not drive plume geometry in this pass.


## SV2-27
Adds model-derived boundary-layer depth near verified observation time, with strict safe-unavailable behavior and no plume-height claim. Run `RUN_VERIFY_SV2_27.bat`.


## SV2-28 — Gust and Variability Window
Adds a timestamp-gated five-hour wind context window with gust factor, speed range, directional spread, completeness, and explicit scientific boundaries. Run `RUN_VERIFY_SV2_28.bat`; only `/scene` opens automatically.


## SV2-36
Adds a bounded Terrain–Atmosphere Interaction Index and review surface at `/terrain-atmosphere-index`.


## SV2-36
Adds spatial confidence and uncertainty for the Terrain Steering Field. Run `RUN_VERIFY_SV2_31.bat`.


## SV2-36
Steering-aware air volume adds confidence-gated visual shaping from the terrain steering field while preserving all scientific boundaries.


## SV2-36

Terrain-responsive particle advection adds bounded, confidence-gated visual tracer motion. Run `RUN_VERIFY_SV2_33.bat`; it opens only `/scene`.


## SV2-43
Adds confidence-gated terrain convergence and terrain-focused accumulation visual potentials. Run `RUN_VERIFY_SV2_38.bat`.


## SV2-43
Terrain transition zones and soft flow-regime boundaries are now map registered and confidence gated.


## SV2-43
Adds spatial terrain-regime confidence and boundary ambiguity with safe visual downgrades.


## SV2-43
Integrated Response Authority and Conflict Resolution adds agreement-weighted authority, preserved conflict, and bounded visual governance.


## SV2-44
Integrated response-driven motion orchestration coordinates bounded visual tracer motion under conflict-aware authority.

## SV2-48
Evidence-Guided Focus and Depth Composition coordinates the layered visual volume under one bounded, conflict-aware terrain-response profile.


## SV2-49
Atmospheric Light, Shadow, and Evidence Legibility coordinates restrained light, shadow, glow, edge separation, confidence illumination, and uncertainty luminance without treating optical styling as scientific measurement.


## SV2-50
Evidence-State Color, Contrast, and Visual Hierarchy Governance protects uncertainty visibility, limits simultaneous accents, and prevents visual intensity from implying concentration, probability, severity, or plume thickness. Run `RUN_VERIFY_SV2_50.bat`. The package includes `MORNING_RESUME_CHECKPOINT_SV2_50.md` and opens only `/scene`.


## SV2-51
Scientific Annotation Choreography and Contextual Labeling introduces evidence-first labels, collision avoidance, bounded timing, and reviewer override.

## SV2-53
Reviewer-Guided Evidence Exploration adds a one-time seven-phase scientific reveal that ends in a stable review frame.


## SV2-54

Progressive Disclosure and Scene Simplification reorganizes the full science stack into Overview, Context, and Deep audit visibility levels. Run `RUN_VERIFY_SV2_54.bat`.
