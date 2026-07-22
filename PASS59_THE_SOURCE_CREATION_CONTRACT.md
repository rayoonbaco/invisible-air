# PASS 59 — The Source Creation Contract

## Purpose
Make visitor-added sources scientifically legible at the moment they are created.

## Added
- A visible release-assumption line in the active experiment contract.
- Visitor-source creation status that distinguishes local atmospheric inputs from assumed release conditions.
- Source hover language that states the assumed release height.
- A deterministic post-creation explanation: the Observatory fetched local atmosphere and applied a normalized release assumption; it did not infer a measured emissions rate.
- Newly added sources become the active experiment after their fields load.

## Boundary
A dropped pin is not evidence of an actual release. The generated field is a relative modeled influence field under explicit assumptions.
