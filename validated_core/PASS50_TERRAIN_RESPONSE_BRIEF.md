# Pass 50 — Terrain Demonstrably Matters

Pass 50 adds a bounded, deterministic, cell-level terrain response to the Pass 48 governing model and Pass 49 renderer contract.

## Active terrain effects

- **Valley alignment:** attracts the preferred corridor toward a gently varying valley axis and compresses crosswind width.
- **Cross-ridge resistance:** reduces transmission at a ridge, weakens support in the lee, and creates deterministic divergence around the barrier.
- **Complex terrain:** adds bounded local steering, roughness-driven widening, and spatial support reduction.
- **Open terrain:** leaves the field unchanged.

The response is a screening-scale approximation, not computational fluid dynamics and not a regulatory terrain-dispersion calculation.

## Terrain-on / terrain-off proof

The Observatory endpoint accepts:

- `/observatory-field.json?terrain=on`
- `/observatory-field.json?terrain=off`
- `/observatory-field.json?terrain_profile=valley_aligned`
- `/observatory-field.json?terrain_profile=cross_ridge`
- `/observatory-field.json?terrain_profile=complex`

The permanent benchmark suite saves paired PNG and JSON outputs in `artifacts/pass50`.
