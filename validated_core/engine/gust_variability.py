from __future__ import annotations

import json
import math
import os
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "gust_variability_cache"
ARCHIVE_URL = os.environ.get("AW_OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive")
VARIABLES = ("wind_speed_10m", "wind_direction_10m", "wind_gusts_10m")
WINDOW_HOURS = 2


def _parse_iso(value):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _base(obs, lat, lon):
    return {
        "contract_version": "gust_variability_window_v1",
        "pass_id": "SV2-35",
        "provider": "Open-Meteo Historical Weather API",
        "source_type": "historical reanalysis / bounded wind-variability context",
        "observation_timestamp": obs,
        "latitude": round(float(lat), 6),
        "longitude": round(float(lon), 6),
        "requested_variables": list(VARIABLES),
        "requested_window_hours_each_side": WINDOW_HOURS,
        "evidence_state": "modeled",
        "method": {
            "name": "nearest-hour centered variability window",
            "version": "1.0",
            "purpose": "Show short-window changes in modeled wind speed, direction, and gust context around a verified observation time.",
        },
        "claim_boundary": "The gust and variability window is model-derived hourly context. It is not measured turbulence, a sub-hourly gust chronology, a turbulence intensity estimate, a plume-dispersion calculation, or proof of intermittent emissions.",
    }


def _unavailable(obs, lat, lon, state, detail):
    out = _base(obs, lat, lon)
    out.update({
        "data_state": state,
        "status": "unavailable_safe",
        "selected_time_utc": None,
        "time_offset_minutes": None,
        "window_start_utc": None,
        "window_end_utc": None,
        "expected_hour_count": 2 * WINDOW_HOURS + 1,
        "available_hour_count": 0,
        "window_complete": False,
        "samples": [],
        "metrics": None,
        "variability_class": "unknown",
        "confidence_band": "unresolved",
        "confidence_score": 0.0,
        "cache_status": "none",
        "retrieved_at_utc": None,
        "provider_url": None,
        "display_label": detail,
        "scene_directive": "Keep gust and short-window variability visually neutral while observation-time evidence is unavailable.",
    })
    return out


def _cache_path(lat, lon, obs):
    key = f"{lat:.5f}|{lon:.5f}|{obs.isoformat()}|{WINDOW_HOURS}".encode()
    return CACHE_DIR / f"gust_variability_{sha256(key).hexdigest()[:20]}.json"


def _fixture():
    path = os.environ.get("AW_GUST_VARIABILITY_FIXTURE")
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def _fetch(lat, lon, obs, timeout=12.0):
    fixture = _fixture()
    if fixture is not None:
        return fixture, "fixture://gust-variability-window"
    start = (obs - timedelta(hours=WINDOW_HOURS + 1)).date().isoformat()
    end = (obs + timedelta(hours=WINDOW_HOURS + 1)).date().isoformat()
    query = urlencode({
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "hourly": ",".join(VARIABLES),
        "wind_speed_unit": "mph",
        "timezone": "UTC",
    })
    url = f"{ARCHIVE_URL}?{query}"
    req = Request(url, headers={"User-Agent": "InvisibleAir-AtmosphereWindow-SV2-35/1.0"})
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8")), url


def _angular_difference(a, b):
    raw = abs((float(a) % 360.0) - (float(b) % 360.0))
    return min(raw, 360.0 - raw)


def _circular_spread(directions):
    if not directions:
        return None
    radians = [math.radians(float(v) % 360.0) for v in directions]
    mean_x = sum(math.cos(v) for v in radians) / len(radians)
    mean_y = sum(math.sin(v) for v in radians) / len(radians)
    mean = math.degrees(math.atan2(mean_y, mean_x)) % 360.0
    return round(max(_angular_difference(v, mean) for v in directions), 1)


def _select_window(payload, obs):
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    speeds = hourly.get("wind_speed_10m") or []
    directions = hourly.get("wind_direction_10m") or []
    gusts = hourly.get("wind_gusts_10m") or []
    candidates = []
    for i, value in enumerate(times):
        dt = _parse_iso(value)
        if dt is not None:
            candidates.append((abs((dt - obs).total_seconds()), i, dt))
    if not candidates:
        raise ValueError("provider returned no valid hourly timestamps")
    _, center_index, selected = min(candidates, key=lambda x: x[0])
    start_time = selected - timedelta(hours=WINDOW_HOURS)
    end_time = selected + timedelta(hours=WINDOW_HOURS)
    samples = []
    for i, value in enumerate(times):
        dt = _parse_iso(value)
        if dt is None or dt < start_time or dt > end_time:
            continue
        speed = speeds[i] if i < len(speeds) else None
        direction = directions[i] if i < len(directions) else None
        gust = gusts[i] if i < len(gusts) else None
        if speed is None or direction is None or gust is None:
            continue
        samples.append({
            "time_utc": dt.isoformat().replace("+00:00", "Z"),
            "wind_speed_10m_mph": round(float(speed), 1),
            "wind_direction_10m_degrees": round(float(direction) % 360.0, 1),
            "wind_gusts_10m_mph": round(float(gust), 1),
        })
    if not samples:
        raise ValueError("provider returned no complete wind samples inside the requested window")
    selected_sample = min(samples, key=lambda s: abs((_parse_iso(s["time_utc"]) - selected).total_seconds()))
    speed_values = [s["wind_speed_10m_mph"] for s in samples]
    gust_values = [s["wind_gusts_10m_mph"] for s in samples]
    direction_values = [s["wind_direction_10m_degrees"] for s in samples]
    selected_speed = max(0.1, selected_sample["wind_speed_10m_mph"])
    metrics = {
        "selected_sustained_speed_mph": selected_sample["wind_speed_10m_mph"],
        "selected_gust_speed_mph": selected_sample["wind_gusts_10m_mph"],
        "selected_gust_factor": round(selected_sample["wind_gusts_10m_mph"] / selected_speed, 2),
        "window_min_speed_mph": round(min(speed_values), 1),
        "window_max_speed_mph": round(max(speed_values), 1),
        "window_speed_range_mph": round(max(speed_values) - min(speed_values), 1),
        "window_max_gust_mph": round(max(gust_values), 1),
        "window_direction_spread_degrees": _circular_spread(direction_values),
    }
    return samples, metrics, selected, (selected - obs).total_seconds() / 60.0, start_time, end_time


def _classify(metrics, complete, offset_minutes):
    speed_range = float(metrics.get("window_speed_range_mph") or 0.0)
    direction_spread = float(metrics.get("window_direction_spread_degrees") or 0.0)
    gust_factor = float(metrics.get("selected_gust_factor") or 1.0)
    points = 0
    if speed_range >= 8: points += 2
    elif speed_range >= 4: points += 1
    if direction_spread >= 45: points += 2
    elif direction_spread >= 20: points += 1
    if gust_factor >= 1.8: points += 2
    elif gust_factor >= 1.4: points += 1
    klass = "high" if points >= 4 else "moderate" if points >= 2 else "low"
    score = 0.82 if complete else 0.62
    if abs(offset_minutes) > 30: score -= 0.08
    if abs(offset_minutes) > 90: score -= 0.12
    score = max(0.35, min(0.88, score))
    band = "strong" if score >= 0.8 else "moderate" if score >= 0.62 else "limited"
    return klass, band, round(score, 2)


def gust_variability_context(observation, lat, lon, refresh=False):
    configured = os.environ.get("AW_OBSERVATION_TIME_UTC") or observation.get("reported_time_utc") or observation.get("timestamp")
    obs = _parse_iso(configured)
    if obs is None:
        return _unavailable(None, lat, lon, "observation_time_unresolved", "gust variability unavailable · observation time unresolved")
    if obs > datetime.now(timezone.utc):
        return _unavailable(obs.isoformat().replace("+00:00", "Z"), lat, lon, "observation_time_in_future", "gust variability unavailable · observation time is in the future")
    cache = _cache_path(lat, lon, obs)
    if cache.exists() and not refresh:
        try:
            out = json.loads(cache.read_text(encoding="utf-8")); out["cache_status"] = "cached"; return out
        except Exception:
            pass
    try:
        payload, url = _fetch(lat, lon, obs)
        samples, metrics, selected, offset, window_start, window_end = _select_window(payload, obs)
        expected = 2 * WINDOW_HOURS + 1
        complete = len(samples) == expected
        klass, confidence, score = _classify(metrics, complete, offset)
        out = _base(obs.isoformat().replace("+00:00", "Z"), lat, lon)
        out.update({
            "data_state": "gust_variability_window_cache",
            "status": "ready",
            "selected_time_utc": selected.isoformat().replace("+00:00", "Z"),
            "time_offset_minutes": round(offset, 1),
            "window_start_utc": window_start.isoformat().replace("+00:00", "Z"),
            "window_end_utc": window_end.isoformat().replace("+00:00", "Z"),
            "expected_hour_count": expected,
            "available_hour_count": len(samples),
            "window_complete": complete,
            "samples": samples,
            "metrics": metrics,
            "variability_class": klass,
            "confidence_band": confidence,
            "confidence_score": score,
            "cache_status": "refreshed",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "provider_url": url,
            "display_label": f"{klass} short-window variability · {len(samples)}/{expected} hours · nearest hour {abs(offset):.0f} min from observation",
            "scene_directive": "Use gust and directional variability only as labeled short-window context. It does not yet alter plume geometry or claim turbulence.",
        })
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(out, indent=2), encoding="utf-8")
        return out
    except Exception as exc:
        if cache.exists():
            try:
                out = json.loads(cache.read_text(encoding="utf-8")); out["cache_status"] = "cached_provider_unavailable"; out["provider_error"] = str(exc)[:180]; return out
            except Exception:
                pass
        return _unavailable(obs.isoformat().replace("+00:00", "Z"), lat, lon, "provider_unavailable_no_variability_cache", f"gust variability unavailable · {str(exc)[:120]}")
