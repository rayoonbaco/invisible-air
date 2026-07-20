# SV2-35 — Ridge Spillover and Lee-Side Shelter

SV2-35 derives two map-registered terrain potentials from the validated DEM, available wind direction, and steering-field confidence.

- Ridge spillover potential identifies crest-like cells with higher terrain on neither immediate side along the wind axis.
- Lee-side shelter potential identifies downwind cells with higher terrain in the upwind sampling direction.
- Both fields are confidence-gated and use current atmospheric context only when observation time is unresolved.
- The fields may modulate visual tracers within hard bounds, but do not calculate airflow, recirculation, rotor zones, plume transport, concentration, exposure, or travel time.

The outputs are review heuristics, not CFD or field measurements.
