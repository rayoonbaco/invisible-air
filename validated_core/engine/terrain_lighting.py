from __future__ import annotations

import math


def _grid(samples: list[dict]) -> dict[tuple[int, int], dict]:
    return {
        (int(s['row']), int(s['col'])): s
        for s in samples
        if isinstance(s.get('elevation_m'), (int, float))
        and isinstance(s.get('row'), int)
        and isinstance(s.get('col'), int)
    }


def _norm(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.5
    return max(0.0, min(1.0, (value - low) / (high - low)))


def build_terrain_lighting(terrain: dict) -> dict:
    """Create a restrained lighting/relief contract from measured samples.

    This does not create a continuous DEM or certified hillshade. It converts the
    sparse measured sample grid into coarse visual cells and contour cues so the
    landform beneath the plume is easier to inspect.
    """
    samples = terrain.get('samples') or []
    measured = terrain.get('data_state') == 'measured_sample_cache'
    points = _grid(samples)
    if not measured or len(points) < 4:
        return {
            'mode': 'neutral_no_measured_lighting',
            'data_state': 'neutral_pending_measured_terrain',
            'cells': [],
            'contours': [],
            'sample_count': len(points),
            'local_relief_m': terrain.get('local_relief_m'),
            'display_label': 'terrain lighting pending measured elevation',
            'claim_boundary': 'No terrain-lighting interpretation is applied without measured elevation samples; this is not a continuous DEM or certified hillshade.',
        }

    elevations = [float(item['elevation_m']) for item in points.values()]
    low, high = min(elevations), max(elevations)
    relief = max(1.0, high - low)
    rows = max(row for row, _ in points) + 1
    cols = max(col for _, col in points) + 1
    cells: list[dict] = []

    # A northwest visual light direction. The result is a display aid, not a
    # solar-angle or remote-sensing hillshade product.
    light_x, light_y = -0.7071, -0.7071
    for row in range(rows - 1):
        for col in range(cols - 1):
            corners = [points.get((row, col)), points.get((row, col + 1)), points.get((row + 1, col + 1)), points.get((row + 1, col))]
            if any(item is None for item in corners):
                continue
            nw, ne, se, sw = corners
            z_nw, z_ne, z_se, z_sw = [float(item['elevation_m']) for item in corners]
            mean = (z_nw + z_ne + z_se + z_sw) / 4.0
            dz_x = ((z_ne + z_se) - (z_nw + z_sw)) / 2.0
            dz_y = ((z_sw + z_se) - (z_nw + z_ne)) / 2.0
            gradient = math.hypot(dz_x, dz_y)
            facing = 0.0 if gradient < 0.01 else (dz_x / gradient) * light_x + (dz_y / gradient) * light_y
            shade = max(-1.0, min(1.0, facing * min(1.0, gradient / max(35.0, relief * 0.18))))
            local_range = max(z_nw, z_ne, z_se, z_sw) - min(z_nw, z_ne, z_se, z_sw)
            cells.append({
                'row': row,
                'col': col,
                'polygon': [
                    {'lat': nw['lat'], 'lon': nw['lon']},
                    {'lat': ne['lat'], 'lon': ne['lon']},
                    {'lat': se['lat'], 'lon': se['lon']},
                    {'lat': sw['lat'], 'lon': sw['lon']},
                ],
                'mean_elevation_m': round(mean, 1),
                'elevation_normalized': round(_norm(mean, low, high), 4),
                'local_range_m': round(local_range, 1),
                'relief_intensity': round(min(1.0, local_range / max(40.0, relief * 0.3)), 4),
                'shade': round(shade, 4),
            })

    # Partial provider responses can leave enough measured points for terrain
    # context but no complete 2x2 cell for honest relief lighting. In that case,
    # remain explicitly sparse/neutral instead of claiming lighting is applied.
    if not cells:
        return {
            'mode': 'neutral_sparse_measured_grid',
            'data_state': 'neutral_pending_measured_terrain',
            'cells': [],
            'contours': [],
            'sample_count': len(points),
            'local_relief_m': round(relief, 1),
            'display_label': 'measured terrain sparse · relief lighting withheld',
            'claim_boundary': 'Measured elevations were available, but no complete local cell could be formed. No relief lighting is applied; this is not a continuous DEM or certified hillshade.',
        }

    # Coarse contour cues at quartiles. Segments are created where a threshold
    # crosses opposing edges of a measured cell. They are intentionally sparse.
    contours: list[dict] = []
    for level_index, fraction in enumerate((0.25, 0.5, 0.75), start=1):
        threshold = low + relief * fraction
        for cell in cells:
            polygon = cell['polygon']
            corner_samples = [
                points[(cell['row'], cell['col'])],
                points[(cell['row'], cell['col'] + 1)],
                points[(cell['row'] + 1, cell['col'] + 1)],
                points[(cell['row'] + 1, cell['col'])],
            ]
            crossings = []
            for idx in range(4):
                a, b = corner_samples[idx], corner_samples[(idx + 1) % 4]
                za, zb = float(a['elevation_m']), float(b['elevation_m'])
                if (za <= threshold < zb) or (zb <= threshold < za):
                    t = (threshold - za) / (zb - za)
                    crossings.append({
                        'lat': round(float(a['lat']) + (float(b['lat']) - float(a['lat'])) * t, 6),
                        'lon': round(float(a['lon']) + (float(b['lon']) - float(a['lon'])) * t, 6),
                    })
            if len(crossings) >= 2:
                contours.append({
                    'level_index': level_index,
                    'elevation_m': round(threshold, 1),
                    'points': crossings[:2],
                })

    return {
        'mode': 'measured_sample_local_relief_lighting',
        'data_state': 'measured_terrain_lighting_applied',
        'cells': cells,
        'contours': contours,
        'sample_count': len(points),
        'cell_count': len(cells),
        'contour_segment_count': len(contours),
        'min_elevation_m': round(low, 1),
        'max_elevation_m': round(high, 1),
        'local_relief_m': round(relief, 1),
        'light_direction': 'northwest visual illumination',
        'display_label': f'local relief lighting · {round(relief, 1)} m measured range',
        'claim_boundary': 'Coarse display lighting derived from sparse measured elevation samples; not a continuous DEM, certified hillshade, or atmospheric model.',
    }
