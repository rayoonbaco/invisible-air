# SV2-5 — Live Wind Connector

This pass adds a current-wind connector using Open-Meteo, a fifteen-minute local cache, and a failure-safe fallback vector.

## Scene consequences

- Current 10 m wind speed and direction are loaded for the scene coordinate.
- The map-registered visual plume corridor is rebuilt from the current wind-to direction.
- The scene labels current, cached, or fallback status explicitly.
- Observation-time wind remains unresolved.

## Claim boundary

Current wind is weather context. It is not necessarily the wind at the time of a methane observation. It does not prove detection, exact plume geometry, responsibility, exposure, or emissions quantity.

## Internal smoke tests

Every pass now keeps executable internal checks in two forms:

- `RUN_SMOKE_TESTS.bat` runs the full offline route/contract/guardrail suite.
- `/self-test` and `/self-test.json` show lightweight in-app contract checks.

The tests deliberately disable live fetching so provider outages cannot create false failures.
