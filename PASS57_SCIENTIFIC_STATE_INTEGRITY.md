# PASS 57 — Scientific State Integrity

## Objective
Make the active source coordinates, live atmospheric inputs, displayed wind, and governing field use one authoritative location state.

## Changes
- `/observatory-field.json` now fetches live atmosphere for the actual source coordinates, including moved and visitor-added sources.
- `/api/live-atmosphere/<scenario>` accepts validated `source_lat` and `source_lon` overrides.
- Moving a source publishes an active-source state event to the interface.
- The right panel identifies the active source and its coordinates.
- The summary wind line and live-atmosphere panel update from the same source-specific weather record used by the model.
- Scenario identity remains the parent demonstration context, while the active experiment is clearly labeled separately.
- Fallback behavior remains explicit when live weather is unavailable.

## Scientific boundary
The source location and weather inputs are aligned, but the displayed field remains a relative modeled influence field, not measured smoke concentration, exposure, AQI, or a forecast.

## Verification
- Python syntax compilation passed.
- JavaScript syntax checks passed.
- Pass 56 site/material registry test passed.
- Static state-integrity contract checks passed.
- Full Flask route suite could not run in this Linux workspace because Flask is not installed and the bundled virtual environment is Windows-based.
