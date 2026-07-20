from __future__ import annotations


def hunter_lens() -> dict:
    return {
        "principle": "AI organizes attention; it does not create evidence.",
        "prompts": [
            {"lens": "Air", "cue": "wind direction", "question": "Does moving air support or complicate the visible plume direction?"},
            {"lens": "Land", "cue": "terrain influence", "question": "Does land shape appear to channel, open, or obscure the scene?"},
            {"lens": "Context", "cue": "map context", "question": "What nearby context helps orientation without blame?"},
            {"lens": "Time", "cue": "recurrence missing", "question": "Do we know if this repeats, or is this a single reported signal?"},
            {"lens": "Unknowns", "cue": "missing exact geometry", "question": "What missing layer could change the human read?"},
        ],
    }
