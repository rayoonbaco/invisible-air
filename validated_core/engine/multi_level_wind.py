from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "multi_level_wind_cache"
ARCHIVE_URL = os.environ.get("AW_OPEN_METEO_ARCHIVE_URL", "https://archive-api.open-meteo.com/v1/archive")
LEVELS = (
    {"key":"10m","height_m":10,"speed":"wind_speed_10m","direction":"wind_direction_10m","label":"near-surface wind"},
    {"key":"100m","height_m":100,"speed":"wind_speed_100m","direction":"wind_direction_100m","label":"lower atmospheric wind"},
)


def _parse_iso(value):
    if not value:return None
    try: dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    except (TypeError,ValueError):return None
    if dt.tzinfo is None:dt=dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _cardinal(deg):
    names=["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return names[int((float(deg)%360)/22.5+0.5)%16]


def _base(obs,lat,lon):
    return {
      "contract_version":"multi_level_wind_v1","pass_id":"SV2-35",
      "provider":"Open-Meteo Historical Weather API","source_type":"historical reanalysis / archived height-level wind context",
      "observation_timestamp":obs,"latitude":round(float(lat),6),"longitude":round(float(lon),6),
      "requested_levels_m":[10,100],"evidence_state":"modeled",
      "claim_boundary":"Height-level winds are model-derived context at nominal heights. They are not an observed vertical profile, turbulence measurement, plume-height estimate, or atmospheric dispersion model."
    }


def _unavailable(obs,lat,lon,state,detail):
    out=_base(obs,lat,lon);out.update({"data_state":state,"status":"unavailable_safe","selected_time_utc":None,"time_offset_minutes":None,"levels":[],"shear":None,"cache_status":"none","retrieved_at_utc":None,"provider_url":None,"display_label":detail,"scene_directive":"Keep the atmospheric volume visually neutral across height when multi-level wind evidence is unavailable."});return out


def _fixture():
    value=os.environ.get("AW_MULTI_LEVEL_WIND_FIXTURE")
    if not value:return None
    try:return json.loads(Path(value).read_text(encoding="utf-8"))
    except Exception:return None


def _fetch(lat,lon,obs,timeout=12.0):
    fix=_fixture()
    if fix is not None:return fix,"fixture://multi-level-wind"
    date=obs.date().isoformat()
    hourly=",".join([x for level in LEVELS for x in (level["speed"],level["direction"])])
    url=f"{ARCHIVE_URL}?"+urlencode({"latitude":lat,"longitude":lon,"start_date":date,"end_date":date,"hourly":hourly,"wind_speed_unit":"mph","timezone":"UTC"})
    req=Request(url,headers={"User-Agent":"InvisibleAir-AtmosphereWindow-SV2-35/1.0"})
    with urlopen(req,timeout=timeout) as response:return json.loads(response.read().decode("utf-8")),url


def _select(payload,obs):
    hourly=payload.get("hourly") or {};times=hourly.get("time") or []
    candidates=[]
    for idx,value in enumerate(times):
        dt=_parse_iso(value)
        if dt:candidates.append((abs((dt-obs).total_seconds()),idx,dt))
    if not candidates:raise ValueError("provider returned no valid hourly timestamps")
    _,idx,selected=min(candidates,key=lambda x:x[0])
    levels=[]
    for spec in LEVELS:
        speeds=hourly.get(spec["speed"]) or [];directions=hourly.get(spec["direction"]) or []
        speed=speeds[idx] if idx<len(speeds) else None;direction=directions[idx] if idx<len(directions) else None
        if speed is None or direction is None:continue
        levels.append({"level_key":spec["key"],"height_m":spec["height_m"],"label":spec["label"],"wind_speed_mph":round(float(speed),1),"wind_direction_degrees":round(float(direction)%360,1),"wind_direction_cardinal":_cardinal(direction)})
    if len(levels)<2:raise ValueError("provider did not return both requested height levels")
    low,high=levels[0],levels[-1]
    raw=abs(high["wind_direction_degrees"]-low["wind_direction_degrees"]);turn=min(raw,360-raw)
    shear={"speed_change_mph":round(high["wind_speed_mph"]-low["wind_speed_mph"],1),"direction_change_degrees":round(turn,1),"interpretation":"height-level contrast for human review only"}
    return levels,shear,selected,(selected-obs).total_seconds()/60


def multi_level_wind_context(observation,lat,lon,refresh=False):
    configured=os.environ.get("AW_OBSERVATION_TIME_UTC") or observation.get("reported_time_utc") or observation.get("timestamp")
    obs=_parse_iso(configured)
    if obs is None:return _unavailable(None,lat,lon,"observation_time_unresolved","multi-level wind unavailable · observation time unresolved")
    if obs>datetime.now(timezone.utc):return _unavailable(obs.isoformat().replace('+00:00','Z'),lat,lon,"observation_time_in_future","multi-level wind unavailable · observation time is in the future")
    key=sha256(f"{lat:.5f}|{lon:.5f}|{obs.isoformat()}".encode()).hexdigest()[:20];path=CACHE_DIR/f"multi_level_{key}.json"
    if path.exists() and not refresh:
        try:out=json.loads(path.read_text(encoding="utf-8"));out["cache_status"]="cached";return out
        except Exception:pass
    try:
        payload,url=_fetch(lat,lon,obs);levels,shear,selected,offset=_select(payload,obs)
        out=_base(obs.isoformat().replace('+00:00','Z'),lat,lon);out.update({"data_state":"multi_level_wind_cache","status":"ready","selected_time_utc":selected.isoformat().replace('+00:00','Z'),"time_offset_minutes":round(offset,1),"levels":levels,"shear":shear,"cache_status":"refreshed","retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace('+00:00','Z'),"provider_url":url,"display_label":f"multi-level wind ready · 10 m + 100 m · nearest hour {abs(offset):.0f} min from observation","scene_directive":"Use height-level contrast as review context only; do not drive vertical plume geometry until a later controlled pass."})
        CACHE_DIR.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(out,indent=2),encoding="utf-8");return out
    except Exception as exc:
        return _unavailable(obs.isoformat().replace('+00:00','Z'),lat,lon,"provider_unavailable_no_multi_level_cache",f"multi-level wind unavailable · {str(exc)[:120]}")
