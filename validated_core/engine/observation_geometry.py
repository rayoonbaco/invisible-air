from __future__ import annotations

import json
import os
from typing import Any

SUPPORTED_GEOMETRY_TYPES = ("Point", "Polygon", "MultiPolygon")
SUPPORTED_PAYLOAD_TYPES = ("Feature", "FeatureCollection", "RasterMask")


def _is_position(value: Any) -> bool:
    return isinstance(value, (list, tuple)) and len(value) >= 2 and all(isinstance(v, (int, float)) for v in value[:2])


def _validate_coordinates(geometry_type: str, coordinates: Any) -> bool:
    if geometry_type == "Point":
        return _is_position(coordinates)
    if geometry_type == "Polygon":
        return isinstance(coordinates, list) and bool(coordinates) and all(
            isinstance(ring, list) and len(ring) >= 4 and all(_is_position(p) for p in ring)
            for ring in coordinates
        )
    if geometry_type == "MultiPolygon":
        return isinstance(coordinates, list) and bool(coordinates) and all(
            _validate_coordinates("Polygon", polygon) for polygon in coordinates
        )
    return False


def _normalize_feature(feature: dict, index: int) -> dict:
    geometry = feature.get("geometry") or {}
    geometry_type = geometry.get("type")
    if geometry_type not in SUPPORTED_GEOMETRY_TYPES:
        raise ValueError(f"feature {index}: unsupported geometry type {geometry_type!r}")
    if not _validate_coordinates(geometry_type, geometry.get("coordinates")):
        raise ValueError(f"feature {index}: invalid {geometry_type} coordinates")
    properties = feature.get("properties") if isinstance(feature.get("properties"), dict) else {}
    return {
        "type": "Feature",
        "id": feature.get("id") or f"observation-geometry-{index + 1}",
        "geometry": {"type": geometry_type, "coordinates": geometry["coordinates"]},
        "properties": {
            "source_role": properties.get("source_role", "reported_observation_geometry"),
            "confidence": properties.get("confidence"),
            "provider_geometry_id": properties.get("provider_geometry_id"),
            "evidence_state": "observed",
        },
    }


def _parse_payload(raw_payload: Any) -> dict:
    if isinstance(raw_payload, str):
        raw_payload = json.loads(raw_payload)
    if not isinstance(raw_payload, dict):
        raise ValueError("geometry payload must be a JSON object")

    payload_type = raw_payload.get("type")
    if payload_type == "FeatureCollection":
        features = raw_payload.get("features")
        if not isinstance(features, list) or not features:
            raise ValueError("FeatureCollection requires at least one feature")
        normalized = [_normalize_feature(feature, i) for i, feature in enumerate(features)]
        return {"type": "FeatureCollection", "features": normalized}
    if payload_type == "Feature":
        return {"type": "FeatureCollection", "features": [_normalize_feature(raw_payload, 0)]}
    if payload_type == "RasterMask":
        required = {"url", "bbox", "width", "height"}
        if not required.issubset(raw_payload):
            raise ValueError("RasterMask requires url, bbox, width, and height")
        if not isinstance(raw_payload.get("bbox"), list) or len(raw_payload["bbox"]) != 4:
            raise ValueError("RasterMask bbox must contain four coordinates")
        return {
            "type": "RasterMask",
            "url": raw_payload["url"],
            "bbox": raw_payload["bbox"],
            "width": int(raw_payload["width"]),
            "height": int(raw_payload["height"]),
            "confidence": raw_payload.get("confidence"),
            "evidence_state": "observed",
        }
    raise ValueError(f"unsupported payload type {payload_type!r}")


def build_observation_geometry_adapter(observation_contract: dict, raw_payload: Any = None) -> dict:
    if raw_payload is None:
        raw_payload = os.environ.get("AW_OBSERVATION_GEOMETRY_JSON")

    base = {
        "contract_version": "observation_geometry_adapter_v1",
        "pass_id": "SV2-35",
        "adapter_status": "ready",
        "supported_payload_types": list(SUPPORTED_PAYLOAD_TYPES),
        "supported_geometry_types": list(SUPPORTED_GEOMETRY_TYPES),
        "observation_id": observation_contract.get("observation_id"),
        "source_geometry": None,
        "feature_count": 0,
        "geometry_state": "unavailable",
        "display_label": "adapter ready · source geometry unavailable",
        "evidence_state": "unavailable",
        "validation_errors": [],
        "render_directive": "Do not draw exact source-product geometry until a validated provider payload is loaded.",
        "claim_boundary": "The adapter normalizes provider geometry for review. It does not create plume geometry, validate methane detection, quantify emissions, or attribute responsibility.",
    }
    if raw_payload in (None, ""):
        return base

    try:
        normalized = _parse_payload(raw_payload)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        base.update({
            "adapter_status": "payload_rejected",
            "geometry_state": "invalid_rejected",
            "display_label": "source geometry rejected · validation failed",
            "evidence_state": "unknown",
            "validation_errors": [str(exc)],
        })
        return base

    feature_count = len(normalized.get("features", [])) if normalized.get("type") == "FeatureCollection" else 1
    base.update({
        "adapter_status": "geometry_loaded",
        "source_geometry": normalized,
        "feature_count": feature_count,
        "geometry_state": "source_geometry_loaded",
        "display_label": f"validated source geometry · {feature_count} feature{'s' if feature_count != 1 else ''}",
        "evidence_state": "observed",
        "render_directive": "Render source geometry as a separate observed layer; never merge it with the visual reconstruction.",
    })
    return base
