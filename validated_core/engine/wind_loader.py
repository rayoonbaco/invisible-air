from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "wind_cache"
CACHE_FILE = CACHE_DIR / "default_scene_current_wind.json"
OPEN_METEO_URL = os.environ.get("AW_OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")
CACHE_MINUTES = int(os.environ.get("AW_WIND_CACHE_MINUTES", "15"))


def _cardinal(degrees: float) -> str:
    names = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return names[int((degrees % 360) / 22.5 + 0.5) % 16]


def _fallback_contract(lat: float, lon: float, reason: str = "live connector not yet resolved") -> dict:
    from_degrees = 248.0
    speed_mph = 12.0
    return {
        "layer": "wind",
        "status": "fallback_vector",
        "data_state": "default_vector_fallback",
        "mode": "fallback_until_live_current_wind",
        "provider": "Open-Meteo current wind connector",
        "source_label": "Open-Meteo current conditions when available",
        "latitude": lat,
        "longitude": lon,
        "speed_mph": speed_mph,
        "gust_mph": None,
        "from_degrees": from_degrees,
        "to_degrees": (from_degrees + 180.0) % 360.0,
        "direction_cardinal": _cardinal(from_degrees),
        "label": f"{_cardinal(from_degrees)} {speed_mph:g} mph · fallback",
        "timestamp": "not live",
        "retrieved_at_utc": None,
        "cache_status": "missing",
        "fallback_reason": reason,
        "claim_strength": "context_only",
        "what_it_can_help_see": "current wind can orient a visual review corridor",
        "what_it_cannot_prove": "current wind is not necessarily observation-time wind and cannot prove methane detection, exact plume geometry, source responsibility, or exposure",
    }


def _cache_is_fresh(payload: dict) -> bool:
    retrieved = payload.get("retrieved_at_utc")
    if not retrieved:
        return False
    try:
        stamp = datetime.fromisoformat(retrieved.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    return datetime.now(timezone.utc) - stamp <= timedelta(minutes=CACHE_MINUTES)


def _read_cache(lat: float, lon: float, allow_stale: bool = False) -> dict | None:
    if not CACHE_FILE.exists():
        return None
    try:
        payload = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None
    if abs(float(payload.get("latitude", 999)) - lat) > 0.01 or abs(float(payload.get("longitude", 999)) - lon) > 0.01:
        return None
    if not allow_stale and not _cache_is_fresh(payload):
        return None
    payload["cache_status"] = "fresh" if _cache_is_fresh(payload) else "stale"
    return payload


def refresh_wind_cache(lat: float, lon: float, timeout: float = 4.0) -> dict:
    query = urlencode({
        "latitude": lat,
        "longitude": lon,
        "current": "wind_speed_10m,wind_direction_10m,wind_gusts_10m",
        "wind_speed_unit": "mph",
        "timezone": "UTC",
    })
    request = Request(
        f"{OPEN_METEO_URL}?{query}",
        headers={"User-Agent": "InvisibleAir-AtmosphereWindow-SV2-5/1.0"},
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    current = payload.get("current") or {}
    speed = float(current["wind_speed_10m"])
    from_degrees = float(current["wind_direction_10m"]) % 360.0
    gust = current.get("wind_gusts_10m")
    gust_mph = round(float(gust), 1) if gust is not None else None
    observed_time = current.get("time") or "current time unavailable"
    retrieved_at = datetime.now(timezone.utc).isoformat()

    contract = {
        "layer": "wind",
        "status": "live_current_wind",
        "data_state": "live_current_conditions",
        "mode": "open_meteo_current_wind",
        "provider": "Open-Meteo",
        "source_label": "Open-Meteo current 10 m wind",
        "latitude": lat,
        "longitude": lon,
        "speed_mph": round(speed, 1),
        "gust_mph": gust_mph,
        "from_degrees": round(from_degrees, 1),
        "to_degrees": round((from_degrees + 180.0) % 360.0, 1),
        "direction_cardinal": _cardinal(from_degrees),
        "label": f"{_cardinal(from_degrees)} {speed:.1f} mph · current",
        "timestamp": observed_time,
        "retrieved_at_utc": retrieved_at,
        "cache_status": "refreshed",
        "fallback_reason": None,
        "claim_strength": "current_weather_context",
        "what_it_can_help_see": "current wind direction and speed can orient the map-registered visual review corridor",
        "what_it_cannot_prove": "current wind is not necessarily observation-time wind and cannot prove methane detection, exact plume geometry, source responsibility, or exposure",
    }
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return contract


def wind_context(lat: float, lon: float, refresh: bool = False) -> dict:
    """Return live current wind with cache and explicit fallback.

    Current wind is contextual. It must never be presented as observation-time
    wind until a historical/observation-time weather source is connected.
    """
    if not refresh:
        cached = _read_cache(lat, lon)
        if cached:
            return cached

    disabled = os.environ.get("AW_DISABLE_LIVE_FETCH", "0").lower() in {"1", "true", "yes"}
    if disabled:
        stale = _read_cache(lat, lon, allow_stale=True)
        if stale:
            stale["data_state"] = "stale_cached_current_conditions"
            stale["label"] = stale["label"].replace(" · current", " · cached")
            return stale
        return _fallback_contract(lat, lon, "live fetch disabled for offline test")

    try:
        return refresh_wind_cache(lat, lon)
    except Exception as exc:  # provider failure must not break the scene
        stale = _read_cache(lat, lon, allow_stale=True)
        if stale:
            stale["data_state"] = "stale_cached_current_conditions"
            stale["cache_status"] = "stale_provider_unavailable"
            stale["fallback_reason"] = str(exc)[:180]
            stale["label"] = stale["label"].replace(" · current", " · cached")
            return stale
        return _fallback_contract(lat, lon, str(exc)[:180])
