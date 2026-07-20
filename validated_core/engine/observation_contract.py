from __future__ import annotations

import os
from datetime import datetime, timezone
from urllib.parse import urlparse


def _iso_or_none(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _float_or_none(value: str | None) -> float | None:
    if value is None or not str(value).strip():
        return None
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def _safe_url(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"} and parsed.netloc:
        return text
    return None


def build_observation_contract(source_seed: dict | None = None) -> dict:
    """Build the provider-neutral SV2-35 observation evidence contract.

    Environment variables may supply a real manifest later. Missing fields remain
    explicit rather than being filled with invented metadata.
    """
    source_seed = source_seed or {}

    observation_id = os.getenv("AW_OBSERVATION_ID", "CASE02-SOURCE-SEED-001").strip()
    provider = os.getenv("AW_OBSERVATION_PROVIDER", "unresolved public-source provider").strip()
    product_type = os.getenv("AW_OBSERVATION_PRODUCT_TYPE", "reported methane observation seed").strip()
    source_url = _safe_url(os.getenv("AW_OBSERVATION_SOURCE_URL"))
    reported_time = _iso_or_none(os.getenv("AW_OBSERVATION_TIME_UTC"))
    retrieved_at = _iso_or_none(os.getenv("AW_OBSERVATION_RETRIEVED_AT_UTC"))
    lat = _float_or_none(os.getenv("AW_OBSERVATION_LAT"))
    lon = _float_or_none(os.getenv("AW_OBSERVATION_LON"))

    if lat is None:
        lat = _float_or_none(source_seed.get("lat"))
    if lon is None:
        lon = _float_or_none(source_seed.get("lon"))

    geometry_status = os.getenv("AW_OBSERVATION_GEOMETRY_STATUS", "point_seed_only").strip()
    quantification_status = os.getenv("AW_OBSERVATION_QUANTIFICATION_STATUS", "not_loaded").strip()
    confidence_status = os.getenv("AW_OBSERVATION_CONFIDENCE_STATUS", "source_unverified_in_app").strip()

    required_values = {
        "observation_id": observation_id,
        "provider": provider,
        "product_type": product_type,
        "reported_time_utc": reported_time,
        "latitude": lat,
        "longitude": lon,
        "source_url": source_url,
        "retrieved_at_utc": retrieved_at,
    }
    missing_fields = [key for key, value in required_values.items() if value in {None, "", "unresolved public-source provider"}]

    if source_url and reported_time and lat is not None and lon is not None and provider != "unresolved public-source provider":
        data_state = "manifest_loaded"
        status_label = "observation manifest loaded"
    else:
        data_state = "source_seed_manifest_incomplete"
        status_label = "source seed only · manifest incomplete"

    return {
        "contract_version": "observation_evidence_contract_v1",
        "pass_id": "SV2-35",
        "observation_id": observation_id,
        "provider": provider,
        "product_type": product_type,
        "reported_time_utc": reported_time,
        "coordinates": {"lat": lat, "lon": lon, "status": "reported_point" if lat is not None and lon is not None else "unresolved"},
        "source_url": source_url,
        "retrieved_at_utc": retrieved_at,
        "geometry_status": geometry_status,
        "quantification_status": quantification_status,
        "confidence_status": confidence_status,
        "data_state": data_state,
        "status_label": status_label,
        "missing_fields": missing_fields,
        "claim_class": "reported_observation_record",
        "what_is_supported": "A provider-neutral record now preserves the reported observation identity, source fields, time state, coordinates, product type, and missing evidence without inventing absent metadata.",
        "what_is_not_supported": "This contract does not prove methane detection by this app, exact plume geometry, emissions quantity, source responsibility, persistence, legality, or event-time transport.",
        "claim_boundary": "The observation record is a provenance container. It is not itself a methane detection, attribution, quantification, or enforcement finding.",
    }
