# Pass 48 — Governing Model Brief

## Decision

Pass 48 establishes one active scientific contract without replacing the Pass 47 observatory renderer. The legacy visual system remains intact until Pass 49 consumes these grids.

## Output

The governing engine returns two deterministic, dimensionless grids:

1. **Relative modeled atmospheric influence** — normalized to 0–1 within one run.
2. **Model support** — 0–1 support derived independently from distance, lateral displacement, input variability, terrain evidence, and terrain conflict.

These outputs are not regulatory concentration, exposure, danger, health risk, probability, or source attribution.

## Governing flow

`source initialization → wind transport → stability/turbulence spread → boundary-layer mixing → bounded terrain response → downwind attenuation → normalized influence field`

A separate support calculation follows:

`distance support × lateral support × wind-variability support × terrain support × terrain-evidence support`

## Active inputs and effects

| Input | Unit | Direct model effect |
|---|---:|---|
| Wind direction | degrees from north | Sets primary wind-to transport bearing |
| Wind speed | m/s | Increases downwind decay length and centroid reach |
| Stability class | categorical | Sets crosswind growth and decay coefficient |
| Direction variability | degrees | Widens spread and reduces support |
| Gust factor | ratio | Widens spread and reduces support |
| Boundary-layer depth | m | Scales raw relative mixing before normalization |
| Relative source strength | relative units | Scales raw field before normalization |
| Release height | m | Sets initial spread and near-source transition |
| Terrain regime | categorical | Bounded direction and spread adjustment |
| Terrain evidence support | 0–1 | Reduces support, never invents influence |

## Coefficient governance

- Model version: `ia_governing_model_v1.0.0`
- Coefficient version: `ia_coefficients_2026-07-20`
- Every output includes its complete input manifest and a deterministic fingerprint.
- Terrain steering is capped and cannot rotate transport arbitrarily.
- A future coefficient change requires a new coefficient version and regenerated benchmark fingerprints.

## Scientific basis

The structure follows established atmospheric-dispersion concepts: advection by mean wind, stability-dependent turbulent spread, boundary-layer mixing context, source-release geometry, terrain interaction, and downwind attenuation. Pass 48 does not claim that its selected coefficients are regulatory or empirically validated. They are explicit, inspectable prototype coefficients.

Professional foundations to cite in the public scientific-basis page include EPA AERMOD documentation for boundary-layer and terrain-aware dispersion concepts, NOAA HYSPLIT documentation for transport and dispersion concepts, and USGS 3DEP documentation for terrain inputs. Those references justify the ingredients; they do not validate Invisible Air's custom weighting.

## Acceptance evidence

Pass 48 tests require:

- identical input → identical field and fingerprint;
- wind direction → expected transport rotation;
- wind speed → measurable reach change;
- stability → measurable spread change;
- variability/gusts → measurable support reduction;
- boundary-layer depth → measurable mixing-factor change;
- terrain regime → bounded direction or spread change;
- every returned grid value stays within 0–1.
