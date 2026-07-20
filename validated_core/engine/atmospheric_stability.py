from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "atmospheric_stability_cache"
ARCHIVE_URL = os.environ.get("AW_OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive")
VARIABLES = ("wind_speed_10m", "shortwave_radiation", "cloud_cover", "temperature_2m")


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
        "contract_version": "atmospheric_stability_screen_v1",
        "pass_id": "SV2-35",
        "provider": "Open-Meteo Historical Weather API",
        "source_type": "historical reanalysis / meteorological stability-screening context",
        "observation_timestamp": obs,
        "latitude": round(float(lat), 6),
        "longitude": round(float(lon), 6),
        "requested_variables": list(VARIABLES),
        "evidence_state": "inferred",
        "method": {
            "name": "bounded solar-wind-cloud screening heuristic",
            "version": "1.0",
            "classes": ["stable", "neutral", "unstable", "unknown"],
            "purpose": "Human-review screening of likely near-surface mixing tendency from archived meteorological inputs.",
        },
        "claim_boundary": "The stability class is a bounded screening inference from model-derived weather inputs. It is not a measured turbulence profile, formal Pasquill-Gifford class, boundary-layer diagnosis, plume-rise calculation, or dispersion-model result.",
    }


def _unavailable(obs, lat, lon, state, detail):
    out = _base(obs, lat, lon)
    out.update({
        "data_state": state,
        "status": "unavailable_safe",
        "selected_time_utc": None,
        "time_offset_minutes": None,
        "inputs": None,
        "stability_class": "unknown",
        "confidence_band": "unresolved",
        "confidence_score": 0.0,
        "screening_reasons": [],
        "cache_status": "none",
        "retrieved_at_utc": None,
        "provider_url": None,
        "display_label": detail,
        "scene_directive": "Keep vertical spread visually neutral and non-physical while stability evidence is unavailable.",
    })
    return out


def _cache_path(lat, lon, obs):
    key = f"{lat:.5f}|{lon:.5f}|{obs.isoformat()}".encode()
    return CACHE_DIR / f"stability_{sha256(key).hexdigest()[:20]}.json"


def _fixture():
    path = os.environ.get("AW_ATMOSPHERIC_STABILITY_FIXTURE")
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def _fetch(lat, lon, obs, timeout=12.0):
    fixture = _fixture()
    if fixture is not None:
        return fixture, "fixture://atmospheric-stability"
    date = obs.date().isoformat()
    query = urlencode({
        "latitude": lat,
        "longitude": lon,
        "start_date": date,
        "end_date": date,
        "hourly": ",".join(VARIABLES),
        "wind_speed_unit": "mph",
        "timezone": "UTC",
    })
    url = f"{ARCHIVE_URL}?{query}"
    req = Request(url, headers={"User-Agent": "InvisibleAir-AtmosphereWindow-SV2-35/1.0"})
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8")), url


def _nearest(payload, obs):
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    parsed=[]
    for i,value in enumerate(times):
        dt=_parse_iso(value)
        if dt is not None:
            parsed.append((abs((dt-obs).total_seconds()),i,dt))
    if not parsed:
        raise ValueError("provider returned no valid hourly timestamps")
    _,idx,selected=min(parsed,key=lambda x:x[0])
    def val(name):
        values=hourly.get(name) or []
        return values[idx] if idx < len(values) else None
    inputs={
        "wind_speed_10m_mph": round(float(val("wind_speed_10m")),1) if val("wind_speed_10m") is not None else None,
        "shortwave_radiation_w_m2": round(float(val("shortwave_radiation")),1) if val("shortwave_radiation") is not None else None,
        "cloud_cover_percent": round(float(val("cloud_cover")),1) if val("cloud_cover") is not None else None,
        "temperature_2m_c": round(float(val("temperature_2m")),1) if val("temperature_2m") is not None else None,
    }
    return inputs,selected,(selected-obs).total_seconds()/60.0


def _classify(inputs, offset_minutes):
    wind=inputs.get("wind_speed_10m_mph")
    solar=inputs.get("shortwave_radiation_w_m2")
    cloud=inputs.get("cloud_cover_percent")
    complete=sum(v is not None for v in (wind,solar,cloud))
    if complete < 2 or wind is None:
        return "unknown", "limited", 0.35, ["Insufficient archived inputs for a bounded stability screen."]
    reasons=[]
    if solar is not None and solar >= 350:
        if wind < 12:
            klass="unstable"; reasons.append("Strong solar heating with light-to-moderate near-surface wind favors convective mixing.")
        else:
            klass="neutral"; reasons.append("Strong wind moderates the effect of daytime surface heating.")
    elif solar is not None and solar >= 60:
        if wind < 8:
            klass="unstable"; reasons.append("Daytime heating with lighter wind suggests enhanced mixing.")
        else:
            klass="neutral"; reasons.append("Moderate-to-strong wind supports a neutral screening state.")
    else:
        if cloud is not None and cloud >= 70:
            klass="neutral"; reasons.append("Low solar input with extensive cloud cover limits strong nocturnal stabilization.")
        elif wind >= 10:
            klass="neutral"; reasons.append("Stronger near-surface wind supports mechanical mixing.")
        else:
            klass="stable"; reasons.append("Low solar input with lighter wind supports a stable screening state.")
    score=0.58 + 0.1*complete
    if abs(offset_minutes) <= 30: score += 0.08
    elif abs(offset_minutes) > 90: score -= 0.12
    score=max(0.35,min(0.9,score))
    band="strong" if score >= 0.8 else "moderate" if score >= 0.62 else "limited"
    return klass,band,round(score,2),reasons


def atmospheric_stability_context(observation, lat, lon, refresh=False):
    configured=os.environ.get("AW_OBSERVATION_TIME_UTC") or observation.get("reported_time_utc") or observation.get("timestamp")
    obs=_parse_iso(configured)
    if obs is None:
        return _unavailable(None,lat,lon,"observation_time_unresolved","atmospheric stability unavailable · observation time unresolved")
    if obs > datetime.now(timezone.utc):
        return _unavailable(obs.isoformat().replace('+00:00','Z'),lat,lon,"observation_time_in_future","atmospheric stability unavailable · observation time is in the future")
    cache=_cache_path(lat,lon,obs)
    if cache.exists() and not refresh:
        try:
            out=json.loads(cache.read_text(encoding="utf-8")); out["cache_status"]="cached"; return out
        except Exception:
            pass
    try:
        payload,url=_fetch(lat,lon,obs)
        inputs,selected,offset=_nearest(payload,obs)
        klass,band,score,reasons=_classify(inputs,offset)
        out=_base(obs.isoformat().replace('+00:00','Z'),lat,lon)
        out.update({
            "data_state":"atmospheric_stability_screen",
            "status":"ready",
            "selected_time_utc":selected.isoformat().replace('+00:00','Z'),
            "time_offset_minutes":round(offset,1),
            "inputs":inputs,
            "stability_class":klass,
            "confidence_band":band,
            "confidence_score":score,
            "screening_reasons":reasons,
            "cache_status":"refreshed",
            "retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
            "provider_url":url,
            "display_label":f"{klass} screening state · {band} support · nearest hour {abs(offset):.0f} min from observation",
            "scene_directive":"Use this class only as labeled mixing context. It does not yet alter plume height, spread, or transport geometry.",
        })
        CACHE_DIR.mkdir(parents=True,exist_ok=True)
        cache.write_text(json.dumps(out,indent=2),encoding="utf-8")
        return out
    except Exception as exc:
        if cache.exists():
            try:
                out=json.loads(cache.read_text(encoding="utf-8")); out["cache_status"]="cached_provider_unavailable"; out["provider_error"]=str(exc)[:180]; return out
            except Exception:
                pass
        return _unavailable(obs.isoformat().replace('+00:00','Z'),lat,lon,"provider_unavailable_no_stability_cache",f"atmospheric stability unavailable · {str(exc)[:120]}")
