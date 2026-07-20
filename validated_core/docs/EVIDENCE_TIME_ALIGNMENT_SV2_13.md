# SV2-13 — Evidence-Time Alignment

This pass separates the reported observation clock from the current-weather clock.

- Current wind remains useful as present-day context.
- Current wind is not treated as observation-time wind.
- When a verified observation timestamp is unavailable, the temporal gap is shown as unresolved.
- If `AW_OBSERVATION_TIME_UTC` is later supplied with a real ISO-8601 timestamp, the app calculates and displays the gap while still refusing to imply event-time wind.

The moving path remains a visual review surface, not a historical transport reconstruction or dispersion model.
