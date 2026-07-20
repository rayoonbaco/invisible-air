from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "historical_weather_cache"
ARCHIVE_URL = os.environ.get("AW_OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive")


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _cardinal(degrees: float) -> str:
    names = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return names[int((degrees % 360) / 22.5 + 0.5) % 16]


def _base(observation_time: str | None, lat: float, lon: float) -> dict:
    return {
        "contract_version": "historical_weather_retrieval_v1",
        "pass_id": "SV2-35",
        "provider": "Open-Meteo Historical Weather API",
        "source_type": "historical reanalysis / archived weather context",
        "observation_timestamp": observation_time,
        "latitude": round(float(lat), 6),
        "longitude": round(float(lon), 6),
        "requested_variables": ["wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", "temperature_2m", "surface_pressure"],
        "evidence_state": "modeled",
        "claim_boundary": "Historical weather is model-derived meteorological context near the reported observation time. It is not an on-site measurement, methane detection, exact plume transport, exposure estimate, or attribution finding.",
    }


def _unavailable(observation_time: str | None, lat: float, lon: float, state: str, detail: str) -> dict:
    payload = _base(observation_time, lat, lon)
    payload.update({
        "data_state": state,
        "status": "unavailable_safe",
        "selected_time_utc": None,
        "time_offset_minutes": None,
        "weather": None,
        "cache_status": "none",
        "retrieved_at_utc": None,
        "provider_url": None,
        "display_label": detail,
        "scene_directive": "Keep current wind and observation-time weather visually separate. Do not reconstruct the reported event from current conditions.",
    })
    return payload


def _cache_path(lat: float, lon: float, observation_time: datetime) -> Path:
    key = f"{lat:.5f}|{lon:.5f}|{observation_time.isoformat()}".encode()
    return CACHE_DIR / f"historical_{sha256(key).hexdigest()[:20]}.json"


def _read_fixture() -> dict | None:
    fixture = os.environ.get("AW_HISTORICAL_WEATHER_FIXTURE")
    if not fixture:
        return None
    try:
        return json.loads(Path(fixture).read_text(encoding="utf-8"))
    except Exception:
        return None


def _fetch_archive(lat: float, lon: float, observation_time: datetime, timeout: float = 12.0) -> tuple[dict, str]:
    fixture = _read_fixture()
    if fixture is not None:
        return fixture, "fixture://historical-weather"
    date = observation_time.date().isoformat()
    query = urlencode({
        "latitude": lat,
        "longitude": lon,
        "start_date": date,
        "end_date": date,
        "hourly": "wind_speed_10m,wind_direction_10m,wind_gusts_10m,temperature_2m,surface_pressure",
        "wind_speed_unit": "mph",
        "timezone": "UTC",
    })
    url = f"{ARCHIVE_URL}?{query}"
    request = Request(url, headers={"User-Agent": "InvisibleAir-AtmosphereWindow-SV2-35/1.0"})
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8")), url


def _select_hour(payload: dict, observation_time: datetime) -> tuple[dict, datetime, float]:
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        raise ValueError("provider returned no hourly timestamps")
    parsed = []
    for idx, value in enumerate(times):
        dt = _parse_iso(value)
        if dt is not None:
            parsed.append((abs((dt-observation_time).total_seconds()), idx, dt))
    if not parsed:
        raise ValueError("provider timestamps were invalid")
    _, idx, selected = min(parsed, key=lambda item:item[0])
    def at(name):
        values=hourly.get(name) or []
        return values[idx] if idx < len(values) else None
    speed=at("wind_speed_10m")
    direction=at("wind_direction_10m")
    gust=at("wind_gusts_10m")
    weather={
        "wind_speed_10m_mph": round(float(speed),1) if speed is not None else None,
        "wind_direction_10m_degrees": round(float(direction)%360,1) if direction is not None else None,
        "wind_direction_cardinal": _cardinal(float(direction)) if direction is not None else None,
        "wind_gusts_10m_mph": round(float(gust),1) if gust is not None else None,
        "temperature_2m_c": round(float(at("temperature_2m")),1) if at("temperature_2m") is not None else None,
        "surface_pressure_hpa": round(float(at("surface_pressure")),1) if at("surface_pressure") is not None else None,
    }
    offset=(selected-observation_time).total_seconds()/60.0
    return weather, selected, offset


def historical_weather_context(observation: dict, lat: float, lon: float, refresh: bool=False) -> dict:
    configured=os.environ.get("AW_OBSERVATION_TIME_UTC") or observation.get("reported_time_utc") or observation.get("timestamp")
    obs_dt=_parse_iso(configured)
    if obs_dt is None:
        return _unavailable(None,lat,lon,"observation_time_unresolved","historical weather unavailable · observation time unresolved")
    if obs_dt > datetime.now(timezone.utc):
        return _unavailable(obs_dt.isoformat().replace('+00:00','Z'),lat,lon,"observation_time_in_future","historical weather unavailable · observation time is in the future")
    cache_path=_cache_path(lat,lon,obs_dt)
    if cache_path.exists() and not refresh:
        try:
            cached=json.loads(cache_path.read_text(encoding="utf-8"))
            cached["cache_status"]="cached"
            return cached
        except Exception:
            pass
    try:
        provider_payload, provider_url=_fetch_archive(lat,lon,obs_dt)
        weather, selected, offset=_select_hour(provider_payload,obs_dt)
        result=_base(obs_dt.isoformat().replace('+00:00','Z'),lat,lon)
        result.update({
            "data_state":"historical_weather_cache",
            "status":"ready",
            "selected_time_utc":selected.isoformat().replace('+00:00','Z'),
            "time_offset_minutes":round(offset,1),
            "weather":weather,
            "cache_status":"refreshed",
            "retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
            "provider_url":provider_url,
            "display_label":f"historical weather ready · nearest hour {abs(offset):.0f} min from observation",
            "scene_directive":"Historical wind may support event-time context, but it remains model-derived and is not yet driving the plume visualization.",
        })
        CACHE_DIR.mkdir(parents=True,exist_ok=True)
        cache_path.write_text(json.dumps(result,indent=2),encoding="utf-8")
        return result
    except Exception as exc:
        if cache_path.exists():
            try:
                cached=json.loads(cache_path.read_text(encoding="utf-8")); cached["cache_status"]="cached_provider_unavailable"; cached["provider_error"]=str(exc)[:180]; return cached
            except Exception: pass
        return _unavailable(obs_dt.isoformat().replace('+00:00','Z'),lat,lon,"provider_unavailable_no_historical_cache",f"historical weather unavailable · {str(exc)[:120]}")
