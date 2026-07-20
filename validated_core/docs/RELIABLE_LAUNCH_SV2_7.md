# SV2-7 — Reliable Local Launch and Confirmation Gate

This pass removes nested Windows `cmd` quoting from the startup path.

`RUN_LOCAL.bat` now prepares the environment and delegates startup to `tools/launch_review.py`. The Python launcher:

1. checks whether the server is already running;
2. starts `app.py` in a separate console only when needed;
3. polls `/health` until the Flask app actually responds;
4. opens `/scene` only after readiness is confirmed;
5. prints the exact manual URL if Windows declines the browser-open request.

`RUN_VERIFY_SV2_7.bat` first runs the complete smoke suite, then opens both `/scene` and `/self-test` after the server is ready.

This pass changes operational reliability only. It does not strengthen methane, plume-geometry, terrain, attribution, or quantification claims.
