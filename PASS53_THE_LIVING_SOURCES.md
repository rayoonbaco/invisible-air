# Pass 53 — The Living Sources

## Objective
Turn the multi-source atmospheric field into a direct, tactile scientific instrument without adding tabs, settings panels, or unsupported claims.

## What changed
- Every numbered source can be hovered to reveal a local observation whisper.
- Every numbered source can be dragged to a new map location.
- While dragging, the selected field softens and the source lifts visually.
- The governing model is called only after release, not continuously during movement.
- Only the moved source is recalculated.
- The previous and recalculated fields crossfade over 1.1 seconds.
- Undo now restores the previous source layout, including moved or newly added sources.
- Reset restores the original three curated sources and clears history.
- Pointer events support mouse, pen, and touch-capable browsers.

## Scientific boundary
Dragging changes source coordinates and recomputes the independent relative-influence field. It does not simulate measured concentration, chemical interaction, or a verified wildfire forecast.

## Scope deliberately excluded
No emission-rate sliders, chemistry, timelines, source cards, tabs, or additional model claims were added.
