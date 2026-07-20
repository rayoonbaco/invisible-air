# Pass 49 — The Governing Field Becomes Visible

## Diagnosis
Pass 48 established one deterministic atmospheric-field model, but the Observatory still loaded the legacy procedural plume renderer and a separate animated breath layer. Scientific inputs and visible pixels therefore remained disconnected.

## Files changed
- `app.py` — adds `/observatory-field.json` and translates the active scene into the governing-model input contract.
- `templates/observatory.html` — loads the governing-field renderer instead of `plume_canvas.js`.
- `static/js/governing_field_renderer.js` — renders influence as brightness and support as deterministic texture.
- `static/css/observatory.css` — retires the legacy breath layer in the Observatory.

## Proof added
- `tests/pass49/test_renderer_contract.py`
- `scripts/render_pass49_proof.py`
- `artifacts/pass49/open-terrain-model-driven-field.png`
- `artifacts/pass49/renderer_metrics.json`

## Scientific boundary
The visible field is run-normalized relative modeled atmospheric influence. It is not concentration, exposure, danger, probability, or a verified transport reconstruction.
