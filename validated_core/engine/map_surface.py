from __future__ import annotations

from engine.basemap_surface import basemap_context


def map_surface_contract() -> dict:
    """Compatibility wrapper for SV2-2 map surface metadata."""
    return basemap_context()
