# Invisible Air Dynamic Release Integrity Team

Double-click `RUN_RELEASE_INTEGRITY_TEAM.bat` for the complete pre-GitHub gate.

The test council contains seven specialist roles:

- **Sentinel** — project structure, syntax, secrets, and repository hygiene
- **Navigator** — route and navigation integrity
- **Curator** — public wording, accessibility-oriented contracts, and claim boundaries
- **Experimentalist** — governing-model, renderer, source, journal, and full regression suites
- **Responder** — bad routes and malformed-input behavior
- **Performance** — route response timing and payload checks
- **Release Council** — produces one objective `GO` or `NO-GO` decision

## Normal use

1. Close unrelated programs if the computer is under heavy load.
2. Double-click `RUN_RELEASE_INTEGRITY_TEAM.bat`.
3. Wait for the report to open.
4. Do not push to GitHub unless the top decision is **GO**.
5. The reports are saved in `release_integrity/latest/` as HTML, Markdown, and JSON.

## Live application probe

Start the Observatory in one window, then double-click:

`RUN_RELEASE_INTEGRITY_TEAM_WITH_LIVE_APP.bat`

This adds HTTP checks against `http://127.0.0.1:8000`.

## Honest limitation

No automated suite can guarantee perfection or certify real atmospheric truth. This suite is designed to make regressions, broken contracts, stale state, route failures, performance problems, embedded secrets, and release-hygiene problems difficult to miss before GitHub and Render.
