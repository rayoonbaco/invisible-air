# Final launch acceptance fix

The historical `tests/campus_acceptance_test.py` validates the retired Pass 22-47 campus experience.
It intentionally expects Gatehouse, Chapel, replay, and other elements removed from the Final Instrument.

`RUN_OBSERVATORY.bat` now runs `validated_core/tests/final/test_final_instrument.py`, which validates the active product contract:

- simplified Observatory route
- model and scientific-basis controls
- governing influence and support grids
- terrain-on versus terrain-off behavior
- absence of the retired procedural plume and campus workflow

The historical suite remains in the archive for provenance, but it is no longer a launch gate.
