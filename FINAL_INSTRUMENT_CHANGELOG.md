# Invisible Air — Final Instrument Sprint

## Purpose
Convert the Pass 50 campus-style Observatory into one direct scientific instrument.

## Primary transformation
The public `/observatory` route now reduces to:

source -> atmospheric field -> visual interpretation -> scientific basis

## Files changed
- `validated_core/templates/observatory.html`
- `validated_core/static/js/governing_field_renderer.js`
- `validated_core/static/css/observatory.css`

## Files added
- `validated_core/tests/final/test_final_instrument.py`
- `validated_core/RUN_VERIFY_FINAL.bat`
- `FINAL_INSTRUMENT_CHANGELOG.md`

## Visible changes
- Removed Gatehouse, Chapel, replay sequence, cinematic annotations, and campus navigation from the primary route.
- Retained the Roycroft typography, terrain map, restrained brass details, and dark scientific atmosphere.
- Enlarged the field by fitting the map to the active model footprint instead of the full computational domain.
- Suppressed legacy rectangular image overlays on the Observatory.
- Strengthened the field with a model-derived glow pass and deterministic texture.
- Added one compact source card.
- Added a two-concept legend: brightness and texture.
- Added one compact Model & Scientific Basis drawer.
- Added a terrain-on / terrain-off comparison control.

## Scientific boundary
The visible output is a run-relative modeled atmospheric influence field. It is not measured concentration, exposure, danger, health risk, or probability.
