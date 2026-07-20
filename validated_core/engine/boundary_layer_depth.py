from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "boundary_layer_depth_cache"
ARCHIVE_URL = os.environ.get("AW_OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive")
VARIABLE = "boundary_layer_height"


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
        "contract_version": "boundary_layer_depth_context_v1",
        "pass_id": "SV2-35",
        "provider": "Open-Meteo Historical Weather API",
        "source_type": "historical model-derived boundary-layer context",
        "observation_timestamp": obs,
        "latitude": round(float(lat), 6),
        "longitude": round(float(lon), 6),
        "requested_variable": VARIABLE,
        "units": "m above ground level",
        "evidence_state": "modeled",
        "claim_boundary": "Boundary-layer depth is model-derived atmospheric context near the observation time. It is not a measured mixing height, plume-height estimate, release-height estimate, turbulence profile, exposure boundary, or dispersion-model result.",
    }


def _unavailable(obs, lat, lon, state, detail):
    out = _base(obs, lat, lon)
    out.update({
        "data_state": state,
        "status": "unavailable_safe",
        "selected_time_utc": None,
        "time_offset_minutes": None,
        "boundary_layer_height_m": None,
        "depth_band": "unknown",
        "confidence_band": "unresolved",
        "confidence_score": 0.0,
        "cache_status": "none",
        "retrieved_at_utc": None,
        "provider_url": None,
        "display_label": detail,
        "scene_directive": "Keep vertical extent visually neutral and non-physical while boundary-layer depth is unavailable.",
    })
    return out


def _cache_path(lat, lon, obs):
    key = f"{lat:.5f}|{lon:.5f}|{obs.isoformat()}".encode()
    return CACHE_DIR / f"boundary_layer_{sha256(key).hexdigest()[:20]}.json"


def _fixture():
    path = os.environ.get("AW_BOUNDARY_LAYER_FIXTURE")
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return None


def _fetch(lat, lon, obs, timeout=12.0):
    fixture = _fixture()
    if fixture is not None:
        return fixture, "fixture://boundary-layer-depth"
    date = obs.date().isoformat()
    query = urlencode({
        "latitude": lat,
        "longitude": lon,
        "start_date": date,
        "end_date": date,
        "hourly": VARIABLE,
        "timezone": "UTC",
    })
    url = f"{ARCHIVE_URL}?{query}"
    req = Request(url, headers={"User-Agent": "InvisibleAir-AtmosphereWindow-SV2-35/1.0"})
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8")), url


def _nearest(payload, obs):
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    values = hourly.get(VARIABLE) or []
    candidates=[]
    for i,value in enumerate(times):
        dt=_parse_iso(value)
        if dt is not None and i < len(values) and values[i] is not None:
            candidates.append((abs((dt-obs).total_seconds()),i,dt,float(values[i])))
    if not candidates:
        raise ValueError("provider returned no valid boundary-layer-height values")
    _,_,selected,height=min(candidates,key=lambda x:x[0])
    return round(max(0.0,height),1), selected, (selected-obs).total_seconds()/60.0


def _band(height):
    if height < 250: return "shallow"
    if height < 750: return "moderate"
    if height < 1500: return "deep"
    return "very_deep"


def boundary_layer_depth_context(observation, lat, lon, refresh=False):
    configured=os.environ.get("AW_OBSERVATION_TIME_UTC") or observation.get("reported_time_utc") or observation.get("timestamp")
    obs=_parse_iso(configured)
    if obs is None:
        return _unavailable(None,lat,lon,"observation_time_unresolved","boundary-layer depth unavailable · observation time unresolved")
    if obs > datetime.now(timezone.utc):
        return _unavailable(obs.isoformat().replace('+00:00','Z'),lat,lon,"observation_time_in_future","boundary-layer depth unavailable · observation time is in the future")
    cache=_cache_path(lat,lon,obs)
    if cache.exists() and not refresh:
        try:
            out=json.loads(cache.read_text(encoding="utf-8")); out["cache_status"]="cached"; return out
        except Exception:
            pass
    try:
        payload,url=_fetch(lat,lon,obs)
        height,selected,offset=_nearest(payload,obs)
        score=0.82 if abs(offset)<=30 else 0.68 if abs(offset)<=90 else 0.5
        confidence="strong" if score>=0.8 else "moderate" if score>=0.62 else "limited"
        out=_base(obs.isoformat().replace('+00:00','Z'),lat,lon)
        out.update({
            "data_state":"boundary_layer_depth_cache",
            "status":"ready",
            "selected_time_utc":selected.isoformat().replace('+00:00','Z'),
            "time_offset_minutes":round(offset,1),
            "boundary_layer_height_m":height,
            "depth_band":_band(height),
            "confidence_band":confidence,
            "confidence_score":round(score,2),
            "cache_status":"refreshed",
            "retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),
            "provider_url":url,
            "display_label":f"{height:.0f} m model-derived boundary layer · {_band(height).replace('_',' ')} · nearest hour {abs(offset):.0f} min from observation",
            "scene_directive":"Use boundary-layer depth only as labeled vertical-context evidence. It does not yet set plume height or vertical spread.",
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
        return _unavailable(obs.isoformat().replace('+00:00','Z'),lat,lon,"provider_unavailable_no_boundary_layer_cache",f"boundary-layer depth unavailable · {str(exc)[:120]}")
