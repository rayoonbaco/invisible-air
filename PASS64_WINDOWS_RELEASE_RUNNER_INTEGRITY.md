# Pass 64 — Windows Release Runner Integrity

This pass repairs false NO-GO results caused by the release runner rather than the application.

## Repairs

- Replaced naive JavaScript delimiter counting, which misread valid modern JavaScript regex/template syntax, with an honest dependency-free corruption and completeness check when Node.js is unavailable.
- Preserved full `node --check` validation whenever Node.js is installed.
- Added `validated_core` to `PYTHONPATH` for direct unittest execution so `app` and `engine` imports resolve exactly as they do under pytest.
- Forced UTF-8 for direct test execution so Windows CP1252 defaults cannot fail on typographic characters in templates.
- Kept all application, API, live-route, scientific-language, performance, and release-gate checks blocking.

No governing model, UI, renderer behavior, or scientific wording was changed.
