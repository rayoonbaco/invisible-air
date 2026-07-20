from __future__ import annotations

import os
from datetime import datetime, timezone


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _format_gap(hours: float) -> str:
    magnitude = abs(hours)
    if magnitude < 1:
        return f"{round(magnitude * 60)} minutes"
    if magnitude < 48:
        return f"{magnitude:.1f} hours"
    return f"{magnitude / 24:.1f} days"


def build_evidence_time_alignment(observation: dict, wind: dict, historical_weather: dict | None = None) -> dict:
    """Separate evidence time from current-weather time without inventing event weather."""
    configured = os.environ.get("AW_OBSERVATION_TIME_UTC") or observation.get("timestamp")
    observation_time = _parse_iso(configured)
    current_wind_time = _parse_iso(wind.get("timestamp"))
    historical_weather = historical_weather or {}
    historical_ready = historical_weather.get("data_state") == "historical_weather_cache"

    if observation_time is None:
        return {
            "mode": "observation_time_unresolved",
            "data_state": "not_time_aligned",
            "observation_timestamp": None,
            "observation_time_label": "reported observation time unresolved",
            "current_wind_timestamp": wind.get("timestamp"),
            "current_wind_time_label": f"current wind · {wind.get('timestamp', 'time unavailable')}",
            "gap_hours": None,
            "gap_label": "temporal gap cannot be calculated",
            "alignment_status": "current_context_only",
            "display_label": "current wind context only · event-time alignment unavailable",
            "scene_directive": "Do not read the animated path as a reconstruction of the reported event.",
            "claim_boundary": "Current wind can orient present-day context, but it cannot reconstruct observation-time transport until the observation timestamp and event-time weather are connected.",
        }

    if historical_ready:
        selected = historical_weather.get("selected_time_utc")
        offset = historical_weather.get("time_offset_minutes")
        return {
            "mode": "historical_weather_connected",
            "data_state": "historical_context_available",
            "observation_timestamp": observation_time.isoformat(),
            "observation_time_label": f"reported observation · {observation_time.isoformat()}",
            "current_wind_timestamp": wind.get("timestamp"),
            "current_wind_time_label": f"current wind · {wind.get('timestamp', 'time unavailable')}",
            "historical_weather_timestamp": selected,
            "historical_offset_minutes": offset,
            "gap_hours": None,
            "gap_label": f"historical weather sample {abs(float(offset or 0)):.0f} minutes from observation",
            "alignment_status": "historical_context_available",
            "display_label": "historical weather connected · current wind remains separate",
            "scene_directive": "Use the retrieved historical weather as model-derived event-time context only; the animated plume still uses current wind until a later controlled pass changes that behavior.",
            "claim_boundary": "Historical weather improves temporal context but does not by itself reconstruct plume transport, validate methane geometry, or establish source responsibility.",
        }

    if current_wind_time is None:
        return {
            "mode": "observation_time_known_current_time_unresolved",
            "data_state": "not_time_aligned",
            "observation_timestamp": observation_time.isoformat(),
            "observation_time_label": f"reported observation · {observation_time.isoformat()}",
            "current_wind_timestamp": wind.get("timestamp"),
            "current_wind_time_label": "current wind time unavailable",
            "gap_hours": None,
            "gap_label": "temporal gap cannot be calculated",
            "alignment_status": "current_context_only",
            "display_label": "observation time known · current-weather time unresolved",
            "scene_directive": "Do not read the animated path as observation-time transport.",
            "claim_boundary": "Observation time alone is insufficient; event-time weather is still missing.",
        }

    gap_hours = (current_wind_time - observation_time).total_seconds() / 3600.0
    return {
        "mode": "known_observation_time_current_weather_comparison",
        "data_state": "time_gap_visible",
        "observation_timestamp": observation_time.isoformat(),
        "observation_time_label": f"reported observation · {observation_time.isoformat()}",
        "current_wind_timestamp": current_wind_time.isoformat(),
        "current_wind_time_label": f"current wind · {current_wind_time.isoformat()}",
        "gap_hours": round(gap_hours, 2),
        "gap_label": f"{_format_gap(gap_hours)} between observation and current wind",
        "alignment_status": "not_event_time_wind",
        "display_label": f"time gap visible · {_format_gap(gap_hours)}",
        "scene_directive": "Use current wind as present-day context only, not as the event reconstruction.",
        "claim_boundary": "A visible time gap does not supply observation-time wind; historical/event-time weather remains required before temporal reconstruction.",
    }
