from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "live_weather_cache"
CACHE_TTL_SECONDS = 3600
RATE_LIMIT_COOLDOWN_SECONDS = 900
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
COOLDOWN_FILE = CACHE_DIR / "_provider_cooldown.json"


def _rounded_coordinates(lat: float, lon: float) -> tuple[float, float]:
    return round(float(lat), 2), round(float(lon), 2)


def _cache_path(lat: float, lon: float) -> Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    rounded_lat, rounded_lon = _rounded_coordinates(lat, lon)
    return CACHE_DIR / f"{rounded_lat:.2f}_{rounded_lon:.2f}.json"


def _read_cache(lat: float, lon: float):
    path = _cache_path(lat, lon)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data["_cache_age_seconds"] = max(0, round(time.time() - float(data.get("_cached_at_epoch", 0))))
        return data
    except Exception:
        return None


def _write_cache(lat: float, lon: float, data: dict[str, Any]) -> None:
    payload = dict(data)
    payload["_cached_at_epoch"] = time.time()
    _cache_path(lat, lon).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _read_cooldown() -> dict[str, Any]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not COOLDOWN_FILE.exists():
        return {}
    try:
        return json.loads(COOLDOWN_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _set_cooldown(error_text: str) -> None:
    payload = {
        "until_epoch": time.time() + RATE_LIMIT_COOLDOWN_SECONDS,
        "error": error_text,
        "set_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    COOLDOWN_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _cooldown_active() -> tuple[bool, dict[str, Any]]:
    data = _read_cooldown()
    try:
        active = float(data.get("until_epoch", 0)) > time.time()
    except (TypeError, ValueError):
        active = False
    return active, data


def _closest_hour_index(times: list[str]) -> int:
    now = datetime.now(timezone.utc)
    best_i, best_delta = 0, float("inf")
    for i, value in enumerate(times or []):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = abs((dt.astimezone(timezone.utc) - now).total_seconds())
            if delta < best_delta:
                best_i, best_delta = i, delta
        except ValueError:
            pass
    return best_i


def _stability(is_day: int, cloud: float, wind: float, pbl: float) -> str:
    if is_day:
        if pbl >= 1400 and cloud < 45 and wind < 5.5:
            return "unstable"
        if pbl >= 850:
            return "neutral"
        return "stable"
    if cloud >= 75 or wind >= 5.5:
        return "neutral"
    if pbl <= 350 and wind < 3.5:
        return "very_stable"
    return "stable"


def fetch_live_atmosphere(lat: float, lon: float, force_refresh: bool = False) -> dict[str, Any]:
    cached = _read_cache(lat, lon)
    if cached and not force_refresh and cached.get("_cache_age_seconds", 999999) < CACHE_TTL_SECONDS:
        cached["data_state"] = "cached_live"
        return cached

    cooldown_is_active, cooldown = _cooldown_active()
    if cooldown_is_active and not force_refresh:
        if cached:
            cached["data_state"] = "stale_cached_live"
            cached["live_error"] = cooldown.get("error", "Provider temporarily rate-limited")
            cached["provider_cooldown_active"] = True
            return cached
        return {
            "provider": "Open-Meteo",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "latitude": lat,
            "longitude": lon,
            "data_state": "unavailable",
            "live_error": cooldown.get("error", "Provider temporarily rate-limited"),
            "provider_cooldown_active": True,
        }

    params = {
        "latitude": f"{lat:.6f}",
        "longitude": f"{lon:.6f}",
        "current": "temperature_2m,relative_humidity_2m,surface_pressure,cloud_cover,wind_speed_10m,wind_direction_10m,wind_gusts_10m,is_day",
        "hourly": "boundary_layer_height",
        "wind_speed_unit": "ms",
        "timezone": "UTC",
        "forecast_hours": 6,
        "past_hours": 3,
    }

    try:
        req = Request(OPEN_METEO_URL + "?" + urlencode(params), headers={"User-Agent": "Invisible-Air/1.0"})
        with urlopen(req, timeout=12) as response:
            raw = json.loads(response.read().decode("utf-8"))

        current = raw.get("current") or {}
        hourly = raw.get("hourly") or {}
        idx = _closest_hour_index(hourly.get("time") or [])
        pbl_values = hourly.get("boundary_layer_height") or []
        pbl = float(pbl_values[idx] if idx < len(pbl_values) and pbl_values[idx] is not None else 650.0)
        wind = max(0.2, float(current.get("wind_speed_10m") or 0.2))
        gust = max(wind, float(current.get("wind_gusts_10m") or wind))
        cloud = float(current.get("cloud_cover") or 0.0)
        is_day = int(current.get("is_day") or 0)
        gust_factor = max(1.0, min(2.5, gust / wind))
        variability = max(6.0, min(35.0, 8.0 + (gust_factor - 1.0) * 24.0))

        data = {
            "provider": "Open-Meteo",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "observation_time_utc": current.get("time"),
            "latitude": float(raw.get("latitude", lat)),
            "longitude": float(raw.get("longitude", lon)),
            "temperature_c": float(current.get("temperature_2m") or 0.0),
            "relative_humidity_percent": float(current.get("relative_humidity_2m") or 0.0),
            "surface_pressure_hpa": float(current.get("surface_pressure") or 0.0),
            "cloud_cover_percent": cloud,
            "wind_speed_mps": wind,
            "wind_direction_deg": float(current.get("wind_direction_10m") or 0.0),
            "wind_gust_mps": gust,
            "is_day": is_day,
            "boundary_layer_height_m": pbl,
            "stability_class": _stability(is_day, cloud, wind, pbl),
            "direction_variability_deg": variability,
            "gust_factor": gust_factor,
            "data_state": "live",
        }
        _write_cache(lat, lon, data)
        if COOLDOWN_FILE.exists():
            COOLDOWN_FILE.unlink()
        return data

    except HTTPError as exc:
        error_text = f"HTTP Error {exc.code}: {exc.reason}"
        if exc.code == 429:
            _set_cooldown(error_text)
        if cached:
            cached["data_state"] = "stale_cached_live"
            cached["live_error"] = error_text
            cached["provider_cooldown_active"] = exc.code == 429
            return cached
        return {
            "provider": "Open-Meteo",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "latitude": lat,
            "longitude": lon,
            "data_state": "unavailable",
            "live_error": error_text,
            "provider_cooldown_active": exc.code == 429,
        }

    except Exception as exc:
        if cached:
            cached["data_state"] = "stale_cached_live"
            cached["live_error"] = str(exc)
            return cached
        return {
            "provider": "Open-Meteo",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "latitude": lat,
            "longitude": lon,
            "data_state": "unavailable",
            "live_error": str(exc),
        }


def apply_live_atmosphere(payload: dict[str, Any], live: dict[str, Any]) -> dict[str, Any]:
    if live.get("data_state") == "unavailable":
        return payload
    met = payload.setdefault("meteorology", {})
    met.update({
        "wind_from_deg": float(live["wind_direction_deg"]),
        "wind_speed_mps": float(live["wind_speed_mps"]),
        "stability_class": str(live["stability_class"]),
        "boundary_layer_depth_m": float(live["boundary_layer_height_m"]),
        "direction_variability_deg": float(live["direction_variability_deg"]),
        "gust_factor": float(live["gust_factor"]),
    })
    return payload
