from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
import tifffile

from engine.full_dem import RASTER_FILE, full_dem_context

PASS_ID = "SV2-35"
CACHE_DIR = Path(__file__).resolve().parents[1] / "data" / "cache"
SPILLOVER_FILE = CACHE_DIR / "ridge_spillover_potential.png"
SHELTER_FILE = CACHE_DIR / "lee_side_shelter_potential.png"
META_FILE = CACHE_DIR / "ridge_spillover_shelter.json"


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _band(value: float) -> str:
    if value >= 0.72:
        return "high"
    if value >= 0.48:
        return "moderate-high"
    if value >= 0.28:
        return "moderate"
    if value >= 0.12:
        return "low-moderate"
    return "low"


def _shift(arr: np.ndarray, dy: int, dx: int) -> np.ndarray:
    shifted = np.roll(np.roll(arr, dy, axis=0), dx, axis=1)
    if dy > 0:
        shifted[:dy, :] = np.nan
    elif dy < 0:
        shifted[dy:, :] = np.nan
    if dx > 0:
        shifted[:, :dx] = np.nan
    elif dx < 0:
        shifted[:, dx:] = np.nan
    return shifted


def _unavailable(label: str, state: str = "ridge_spillover_shelter_unavailable_safe") -> dict[str, Any]:
    return {
        "contract_version": "ridge_spillover_shelter_v1",
        "pass_id": PASS_ID,
        "layer": "ridge_spillover_and_lee_side_shelter",
        "evidence_state": "inferred",
        "data_state": state,
        "status": "unavailable_safe",
        "display_label": label,
        "spillover_statistics": {},
        "shelter_statistics": {},
        "confidence_support": 0.0,
        "spillover_image_url": None,
        "shelter_image_url": None,
        "particle_directives": {
            "spillover_lift_px": 0.0,
            "lee_slowdown_multiplier": 1.0,
            "lee_spread_multiplier": 1.0,
            "crest_band": [0.40, 0.62],
            "lee_band": [0.56, 0.86],
        },
        "scene_directive": "Keep ridge-spillover and lee-side shelter effects hidden until validated terrain, wind, and steering confidence are available.",
        "claim_boundary": "Ridge spillover and lee-side shelter are DEM-derived visual potentials. They are not measured airflow, verified recirculation, rotor diagnosis, CFD, plume transport, concentration, exposure, or proof of actual atmospheric behavior.",
    }


def ridge_spillover_shelter_context(scene: dict, refresh: bool = False) -> dict[str, Any]:
    dem = scene.get("full_dem") or full_dem_context(scene)
    wind = scene.get("wind") or {}
    steering_confidence = scene.get("terrain_steering_confidence") or {}
    if dem.get("data_state") != "continuous_dem_cache" or not RASTER_FILE.exists():
        return _unavailable("ridge spillover and lee shelter unavailable · validated DEM missing")
    if wind.get("data_state") not in {"live_current_conditions", "stale_cached_current_conditions", "default_vector_fallback"}:
        return _unavailable("ridge spillover and lee shelter unavailable · wind context missing")
    if steering_confidence.get("data_state") != "terrain_steering_confidence_cache":
        return _unavailable("ridge spillover and lee shelter unavailable · steering confidence missing")

    wind_to = float(wind.get("to_degrees") or 0.0) % 360.0
    wind_speed = max(0.0, float(wind.get("speed_mph") or 0.0))
    source_hash = dem.get("raster_sha256") or dem.get("sha256") or "unknown"
    conf_mean = _clamp((steering_confidence.get("confidence_statistics") or {}).get("mean", 0.0))
    cache_key = hashlib.sha256(f"{source_hash}|{wind_to:.2f}|{wind_speed:.2f}|{conf_mean:.4f}|v1".encode()).hexdigest()
    if not refresh and META_FILE.exists() and SPILLOVER_FILE.exists() and SHELTER_FILE.exists():
        try:
            cached = json.loads(META_FILE.read_text(encoding="utf-8"))
            if cached.get("cache_key") == cache_key:
                return cached
        except Exception:
            pass

    try:
        elev = np.asarray(tifffile.imread(RASTER_FILE), dtype=np.float64)
        if elev.ndim > 2:
            elev = elev[0]
        valid = np.isfinite(elev)
        if valid.mean() < 0.90:
            return _unavailable("ridge spillover and lee shelter unavailable · DEM coverage insufficient")
        fill = float(np.nanmedian(elev[valid]))
        z = np.where(valid, elev, fill)
        approx = dem.get("approx_pixel_size_m") or {}
        px = float(approx.get("x") if isinstance(approx, dict) else approx or 30.0)
        py = float(approx.get("y") if isinstance(approx, dict) else approx or 30.0)
        gy, gx = np.gradient(z, py, px)
        slope = np.degrees(np.arctan(np.hypot(gx, gy)))

        theta = np.radians(wind_to)
        dx = int(round(np.sin(theta) * 5))
        dy = int(round(-np.cos(theta) * 5))
        if dx == 0 and dy == 0:
            dy = -5
        upwind = _shift(z, dy, dx)
        downwind = _shift(z, -dy, -dx)
        far_upwind = _shift(z, dy * 2, dx * 2)

        rise_from_upwind = np.maximum(0.0, z - upwind)
        drop_downwind = np.maximum(0.0, z - downwind)
        crest_relief = np.minimum(rise_from_upwind, drop_downwind)
        upwind_barrier = np.maximum.reduce([
            np.nan_to_num(np.maximum(0.0, upwind - z), nan=0.0),
            np.nan_to_num(np.maximum(0.0, far_upwind - z), nan=0.0),
        ])

        local_scale = max(35.0, float(np.nanpercentile(np.abs(z - np.nanmedian(z)), 75)) * 0.35)
        crest_signal = np.clip(crest_relief / local_scale, 0.0, 1.0)
        shelter_signal = np.clip(upwind_barrier / (local_scale * 1.25), 0.0, 1.0)
        slope_signal = np.clip(slope / 28.0, 0.0, 1.0)
        speed_support = _clamp(wind_speed / 16.0, 0.08, 1.0)
        confidence_gate = 0.35 + 0.65 * conf_mean

        spillover = np.clip(crest_signal * (0.42 + 0.58 * slope_signal) * speed_support * confidence_gate, 0.0, 1.0)
        lee_shelter = np.clip(shelter_signal * (0.62 + 0.38 * (1.0 - slope_signal)) * (0.48 + 0.52 * speed_support) * confidence_gate, 0.0, 1.0)
        support = valid & np.isfinite(upwind) & np.isfinite(downwind)
        spillover = np.nan_to_num(np.where(support, spillover, 0.0), nan=0.0, posinf=0.0, neginf=0.0)
        lee_shelter = np.nan_to_num(np.where(support, lee_shelter, 0.0), nan=0.0, posinf=0.0, neginf=0.0)

        spill_rgb = np.zeros((*spillover.shape, 4), dtype=np.uint8)
        spill_rgb[..., 0] = 125
        spill_rgb[..., 1] = 226
        spill_rgb[..., 2] = 255
        spill_rgb[..., 3] = np.clip((spillover - 0.08) / 0.92 * 185, 0, 185).astype(np.uint8)
        shelter_rgb = np.zeros((*lee_shelter.shape, 4), dtype=np.uint8)
        shelter_rgb[..., 0] = 104
        shelter_rgb[..., 1] = 116
        shelter_rgb[..., 2] = 172
        shelter_rgb[..., 3] = np.clip((lee_shelter - 0.06) / 0.94 * 170, 0, 170).astype(np.uint8)

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        Image.fromarray(spill_rgb, "RGBA").save(SPILLOVER_FILE)
        Image.fromarray(shelter_rgb, "RGBA").save(SHELTER_FILE)
        spill_sha = hashlib.sha256(SPILLOVER_FILE.read_bytes()).hexdigest()
        shelter_sha = hashlib.sha256(SHELTER_FILE.read_bytes()).hexdigest()

        spill_mean = float(np.mean(spillover[support]))
        shelter_mean = float(np.mean(lee_shelter[support]))
        spill_hot = float(np.mean(spillover[support] >= 0.45))
        shelter_hot = float(np.mean(lee_shelter[support] >= 0.45))
        lift_px = _clamp(spill_mean * conf_mean * 22.0, 0.0, 8.0)
        lee_slowdown = _clamp(1.0 - shelter_mean * conf_mean * 0.34, 0.82, 1.0)
        lee_spread = _clamp(1.0 + shelter_mean * (1.0 - conf_mean * 0.35) * 0.28, 1.0, 1.18)

        contract = {
            "contract_version": "ridge_spillover_shelter_v1",
            "pass_id": PASS_ID,
            "layer": "ridge_spillover_and_lee_side_shelter",
            "evidence_state": "inferred",
            "data_state": "ridge_spillover_shelter_cache",
            "status": "ready",
            "cache_key": cache_key,
            "source_dem_sha256": source_hash,
            "source_bbox": dem.get("bbox") or dem.get("requested_bbox"),
            "wind_to_degrees": round(wind_to, 1),
            "wind_speed_mph": round(wind_speed, 1),
            "temporal_basis": "current_atmospheric_context_only",
            "confidence_support": round(conf_mean, 4),
            "spillover_statistics": {
                "mean_potential": round(spill_mean, 4),
                "potential_band": _band(spill_mean),
                "elevated_cell_ratio": round(spill_hot, 4),
            },
            "shelter_statistics": {
                "mean_potential": round(shelter_mean, 4),
                "potential_band": _band(shelter_mean),
                "elevated_cell_ratio": round(shelter_hot, 4),
            },
            "spillover_image_url": "/ridge-spillover-image",
            "spillover_image_sha256": spill_sha,
            "shelter_image_url": "/lee-side-shelter-image",
            "shelter_image_sha256": shelter_sha,
            "particle_directives": {
                "spillover_lift_px": round(lift_px, 2),
                "lee_slowdown_multiplier": round(lee_slowdown, 4),
                "lee_spread_multiplier": round(lee_spread, 4),
                "crest_band": [0.40, 0.62],
                "lee_band": [0.56, 0.86],
            },
            "display_label": f"ridge spillover {_band(spill_mean)} · lee shelter {_band(shelter_mean)} · {round(conf_mean * 100)}% support",
            "scene_directive": "Show restrained crest illumination and a quiet lee-side shelter veil. Let visual tracers rise slightly near the crest envelope and slow or broaden modestly in the lee envelope, always gated by steering confidence.",
            "claim_boundary": "Ridge spillover and lee-side shelter are DEM-derived visual potentials. They are not measured airflow, verified recirculation, rotor diagnosis, CFD, plume transport, concentration, exposure, or proof of actual atmospheric behavior.",
        }
        META_FILE.write_text(json.dumps(contract, indent=2), encoding="utf-8")
        return contract
    except Exception as exc:
        out = _unavailable(f"ridge spillover and lee shelter generation failed · {type(exc).__name__}", "ridge_spillover_shelter_generation_failed")
        out["error_type"] = type(exc).__name__
        return out
