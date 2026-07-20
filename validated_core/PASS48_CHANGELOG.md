# Pass 48 — Establish the Governing Model

## Diagnosis
Pass 47 contained many scientifically relevant modules, but the visible result was not governed by one explicit field equation and contract.

## Files added
- `engine/governing_model.py`
- `data/pass48_benchmarks/*.json`
- `scripts/run_pass48_benchmarks.py`
- `tests/pass48/test_governing_model.py`
- `PASS48_GOVERNING_MODEL_BRIEF.md`
- `RUN_VERIFY_PASS48.bat` inside `validated_core`
- top-level `RUN_VERIFY_PASS48.bat` launcher
- top-level `PASS48_ESTABLISH_THE_GOVERNING_MODEL.md`

## File changed
- `app.py` — adds `/governing-field.json` without changing the existing observatory.

## Proof produced
- deterministic benchmark field JSON files;
- benchmark fingerprint manifest;
- controlled sensitivity tests.

## Remaining failure
The Pass 47 observatory still uses its legacy renderer. Pass 49 must render the governing model's influence and support grids directly.

## Verification executed in build environment
- 8/8 governing-model unit tests passed.
- Three benchmark field JSON outputs and fingerprint manifest generated.
- Python syntax compilation passed for the app route, model, benchmark script, and tests.
- Flask route runtime was not executed in the build environment because Flask was not installed there; the existing Windows project requirements include Flask and the route uses the existing app framework.
