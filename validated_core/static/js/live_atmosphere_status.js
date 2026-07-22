(function () {
  'use strict';
  const REFRESH_MS = 600000;
  let activeSource = null;

  function scenarioId() {
    const shell = document.getElementById('main-content');
    const params = new URLSearchParams(window.location.search);
    if (params.get('scenario')) return params.get('scenario');
    if (!shell) return null;
    try {
      const scene = JSON.parse(shell.dataset.scene || '{}');
      return (scene.active_scenario || {}).id || shell.dataset.activeScenarioId || null;
    } catch (error) {
      return shell.dataset.activeScenarioId || null;
    }
  }

  function cardinal(deg) {
    const labels = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
    return labels[Math.round((((Number(deg) % 360) + 360) % 360) / 22.5) % 16];
  }

  function formatCoord(value, positive, negative) {
    const n = Number(value);
    return Math.abs(n).toFixed(3) + '° ' + (n >= 0 ? positive : negative);
  }

  function updateIdentity(data) {
    if (!activeSource) return;
    const title = document.getElementById('activeObservationTitle');
    const context = document.getElementById('activeObservationContext');
    const mode = document.getElementById('activeExperimentMode');
    const badge = document.getElementById('stateIntegrityBadge');
    const assumption = document.getElementById('activeReleaseAssumption');
    if (title) title.textContent = 'Active Source ' + activeSource.number;
    if (context) context.textContent = formatCoord(activeSource.latitude, 'N', 'S') + ' · ' + formatCoord(activeSource.longitude, 'E', 'W');
    if (mode) mode.textContent = (activeSource.kind === 'visitor' ? 'Visitor-added source' : 'Relocated curated source') + ' · local atmospheric inputs';
    if (assumption) {
      const release = activeSource.releaseAssumption || {};
      const height = Number.isFinite(Number(release.releaseHeightM)) ? Math.round(Number(release.releaseHeightM)) : 10;
      const duration = Number.isFinite(Number(release.durationMinutes)) ? Math.round(Number(release.durationMinutes)) : 60;
      assumption.innerHTML = '<span>Release assumption</span><b>' + height + ' m release height · ' + duration + ' min continuous relative release · normalized strength</b>';
      assumption.dataset.provenance = activeSource.kind === 'visitor' ? 'visitor-assumed' : 'curated-assumed';
    }
    if (badge) {
      const synchronized = data && data.data_state !== 'unavailable';
      badge.textContent = synchronized ? 'Synchronized' : 'Fallback inputs';
      badge.dataset.state = synchronized ? 'synchronized' : 'fallback';
    }
    document.body.dataset.activeSourceLatitude = String(activeSource.latitude);
    document.body.dataset.activeSourceLongitude = String(activeSource.longitude);
    document.body.dataset.atmosphericLocationMode = data && data.location_mode ? data.location_mode : 'active_source';
  }

  function updateWindLine(data) {
    const line = document.getElementById('activeWindLine');
    const terrain = document.getElementById('terrainStatus');
    if (!line || !data || data.data_state === 'unavailable') return;
    const mph = Math.round(Number(data.wind_speed_mps || 0) * 2.23694 * 10) / 10;
    const terrainText = terrain ? terrain.textContent : 'terrain response on';
    line.innerHTML = cardinal(data.wind_direction_deg) + ' wind · ' + mph + ' mph · <span id="terrainStatus">' + terrainText + '</span>';
  }

  function render(data) {
    const panel = document.getElementById('liveAtmospherePanel');
    if (!panel) return;
    updateIdentity(data);
    if (!data || data.data_state === 'unavailable') {
      panel.innerHTML = '<span>Atmospheric inputs</span><b>Live conditions unavailable</b><small>Using scenario fallback inputs for the active model run.</small>';
      panel.classList.add('is-unavailable');
      const badge = document.getElementById('stateIntegrityBadge');
      if (badge) { badge.textContent = 'Fallback inputs'; badge.dataset.state = 'fallback'; }
      return;
    }
    const mph = Math.round(Number(data.wind_speed_mps || 0) * 2.23694 * 10) / 10;
    const gust = Math.round(Number(data.wind_gust_mps || 0) * 2.23694 * 10) / 10;
    const sourceNote = activeSource ? '<small class="live-source-location">Source ' + activeSource.number + ' · ' + formatCoord(activeSource.latitude, 'N', 'S') + ', ' + formatCoord(activeSource.longitude, 'E', 'W') + '</small>' : '';
    panel.classList.remove('is-unavailable');
    panel.innerHTML =
      '<div class="live-atmosphere-heading"><span><i></i>' +
      (data.data_state === 'live' ? 'Live atmosphere' : 'Cached live atmosphere') +
      '</span><small>' + (data.observation_time_utc || '') + '</small></div>' + sourceNote +
      '<div class="live-atmosphere-grid">' +
      '<span><small>Wind</small><b>' + cardinal(data.wind_direction_deg) + ' / ' + mph + ' mph</b></span>' +
      '<span><small>Gust</small><b>' + gust + ' mph</b></span>' +
      '<span><small>Stability</small><b>' + String(data.stability_class).replaceAll('_',' ') + '</b></span>' +
      '<span><small>Boundary layer</small><b>' + Math.round(data.boundary_layer_height_m) + ' m</b></span>' +
      '<span><small>Temperature</small><b>' + Math.round(data.temperature_c) + ' C</b></span>' +
      '<span><small>Humidity</small><b>' + Math.round(data.relative_humidity_percent) + '%</b></span>' +
      '</div>';
    updateWindLine(data);
  }

  async function load(force) {
    const id = scenarioId();
    if (!id) return;
    const url = new URL('/api/live-atmosphere/' + encodeURIComponent(id), window.location.origin);
    if (activeSource) {
      url.searchParams.set('source_lat', Number(activeSource.latitude).toFixed(6));
      url.searchParams.set('source_lon', Number(activeSource.longitude).toFixed(6));
    }
    if (force) url.searchParams.set('refresh', '1');
    try {
      const response = await fetch(url, { cache: 'no-store' });
      render(await response.json());
    } catch (error) {
      render({ data_state: 'unavailable' });
    }
  }

  window.addEventListener('ia:active-source-state', function (event) {
    const detail = event.detail || {};
    if (!Number.isFinite(Number(detail.latitude)) || !Number.isFinite(Number(detail.longitude))) return;
    activeSource = {
      number: Number(detail.number || 1),
      latitude: Number(detail.latitude),
      longitude: Number(detail.longitude),
      kind: detail.kind === 'visitor' ? 'visitor' : 'curated',
      releaseAssumption: detail.releaseAssumption || null
    };
    if (detail.liveAtmosphere) render(detail.liveAtmosphere);
    else load(false);
  });

  window.addEventListener('load', function () {
    load(false);
    window.setInterval(function () { load(true); }, REFRESH_MS);
  });
})();
