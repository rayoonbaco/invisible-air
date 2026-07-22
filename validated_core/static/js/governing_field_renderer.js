(function () {
  'use strict';

  const state = { map: null, canvas: null, ctx: null, fields: [], resizeObserver: null, sourcePhase: 0, animationFrame: null, dpr: 1, bakedSources: [], userSources: [], addArmed: false, loadingToken: 0, drag: null, hoverIndex: -1, tooltip: null, history: [], transition: null, lastObservation: '', lastExplanation: '', journal: [], journalSequence: 0 };

  function activeScenarioId() {
    const params = new URLSearchParams(window.location.search);
    if (params.get('scenario')) return params.get('scenario');

    const shell = document.getElementById('main-content');
    if (!shell) return '';

    if (shell.dataset.activeScenarioId) return shell.dataset.activeScenarioId;

    try {
      const scene = JSON.parse(shell.dataset.scene || '{}');
      return (scene.active_scenario || {}).id || '';
    } catch (error) {
      return '';
    }
  }

  function expectedScenarioSource() {
    const shell = document.getElementById('main-content');
    if (!shell) return null;

    try {
      const scene = JSON.parse(shell.dataset.scene || '{}');
      const handoff = scene.scenario_handoff || {};
      const active = scene.active_scenario || {};
      const lat = Number(handoff.latitude != null ? handoff.latitude : active.latitude);
      const lon = Number(handoff.longitude != null ? handoff.longitude : active.longitude);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
      return { latitude: lat, longitude: lon };
    } catch (error) {
      return null;
    }
  }

  function sourceDistanceKm(a, b) {
    if (!a || !b) return Infinity;
    const toRad = value => value * Math.PI / 180;
    const earthKm = 6371.0088;
    const dLat = toRad(Number(b.latitude) - Number(a.latitude));
    const dLon = toRad(Number(b.longitude) - Number(a.longitude));
    const lat1 = toRad(Number(a.latitude));
    const lat2 = toRad(Number(b.latitude));
    const h = Math.sin(dLat / 2) ** 2 +
      Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
    return earthKm * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
  }

  function bearingBetween(a, b) {
    const toRad = value => value * Math.PI / 180;
    const toDeg = value => value * 180 / Math.PI;
    const lat1 = toRad(Number(a.latitude));
    const lat2 = toRad(Number(b.latitude));
    const dLon = toRad(Number(b.longitude) - Number(a.longitude));
    const y = Math.sin(dLon) * Math.cos(lat2);
    const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
    return (toDeg(Math.atan2(y, x)) + 360) % 360;
  }

  function cardinalDirection(degrees) {
    const labels = ['north', 'northeast', 'east', 'southeast', 'south', 'southwest', 'west', 'northwest'];
    return labels[Math.round(((Number(degrees) % 360) + 360) % 360 / 45) % 8];
  }

  function boundsArea(bounds) {
    if (!bounds || !bounds.isValid()) return 0;
    const south = bounds.getSouth(); const north = bounds.getNorth();
    const west = bounds.getWest(); const east = bounds.getEast();
    const midLat = (south + north) * Math.PI / 360;
    return Math.max(0, north - south) * Math.max(0, east - west) * Math.max(0.15, Math.cos(midLat));
  }

  function boundsOverlapRatio(a, b) {
    if (!a || !b || !a.isValid() || !b.isValid()) return 0;
    const south = Math.max(a.getSouth(), b.getSouth());
    const north = Math.min(a.getNorth(), b.getNorth());
    const west = Math.max(a.getWest(), b.getWest());
    const east = Math.min(a.getEast(), b.getEast());
    if (north <= south || east <= west) return 0;
    const midLat = (south + north) * Math.PI / 360;
    const intersection = (north - south) * (east - west) * Math.max(0.15, Math.cos(midLat));
    return intersection / Math.max(1e-9, Math.min(boundsArea(a), boundsArea(b)));
  }

  function strongestOverlap(entry, entries, movedIndex) {
    const own = activeBounds(entry.contract);
    let best = { index: -1, ratio: 0 };
    entries.forEach(function (candidate, index) {
      if (index === movedIndex || !candidate) return;
      const ratio = boundsOverlapRatio(own, activeBounds(candidate.contract));
      if (ratio > best.ratio) best = { index:index, ratio:ratio };
    });
    return best;
  }

  function percentChange(before, after) {
    const base = Math.max(Math.abs(Number(before) || 0), 1e-9);
    return (Number(after || 0) - Number(before || 0)) / base;
  }

  function transportComponents(fromSource, toSource, transportBearing) {
    const distance = sourceDistanceKm(fromSource, toSource);
    const bearing = bearingBetween(fromSource, toSource);
    const delta = ((bearing - transportBearing + 540) % 360) - 180;
    const radians = delta * Math.PI / 180;
    return {
      distance: distance,
      alongKm: distance * Math.cos(radians),
      crossKm: distance * Math.sin(radians)
    };
  }

  function buildMoveExplanation(index, oldEntry, newEntry, beforeEntries) {
    const oldDiag = oldEntry.contract.diagnostics || {};
    const newDiag = newEntry.contract.diagnostics || {};
    const afterEntries = beforeEntries.slice(); afterEntries[index] = newEntry;
    const oldOverlap = strongestOverlap(oldEntry, beforeEntries, index);
    const newOverlap = strongestOverlap(newEntry, afterEntries, index);
    const overlapDelta = newOverlap.ratio - oldOverlap.ratio;
    const relationIndex = newOverlap.index >= 0 ? newOverlap.index : oldOverlap.index;
    const transport = Number(newDiag.effective_transport_deg || newEntry.contract.grid.transport_bearing_deg || 0);

    if (relationIndex >= 0 && Math.abs(overlapDelta) >= 0.055) {
      const peerBefore = beforeEntries[relationIndex];
      const peerAfter = afterEntries[relationIndex];
      const oldGeometry = transportComponents(oldEntry.source, peerBefore.source, transport);
      const newGeometry = transportComponents(newEntry.source, peerAfter.source, transport);
      const crossChange = Math.abs(newGeometry.crossKm) - Math.abs(oldGeometry.crossKm);
      const totalChange = newGeometry.distance - oldGeometry.distance;
      if (overlapDelta < 0) {
        if (crossChange > 2.0) {
          return 'The relocation increased cross-corridor separation from Source ' + (relationIndex + 1) + ' under the same transport direction, so the displayed fields intersect less.';
        }
        return 'The relocation increased modeled separation from Source ' + (relationIndex + 1) + ' by ' + Math.abs(totalChange).toFixed(totalChange >= 10 ? 0 : 1) + ' km, reducing the shared displayed footprint.';
      }
      if (crossChange < -2.0) {
        return 'The relocation placed Source ' + (index + 1) + ' closer to Source ' + (relationIndex + 1) + ' across the current transport corridor, so more of their displayed fields intersect.';
      }
      return 'The relocation reduced modeled separation from Source ' + (relationIndex + 1) + ', increasing the shared displayed footprint under unchanged atmospheric inputs.';
    }

    const oldBearing = Number(oldDiag.effective_transport_deg || oldEntry.contract.grid.transport_bearing_deg || 0);
    const newBearing = Number(newDiag.effective_transport_deg || newEntry.contract.grid.transport_bearing_deg || 0);
    const turn = ((newBearing - oldBearing + 540) % 360) - 180;
    const oldTerrainTurn = Number(oldDiag.terrain_turn_deg || 0);
    const newTerrainTurn = Number(newDiag.terrain_turn_deg || 0);
    if (Math.abs(turn) >= 8 && Math.abs(newTerrainTurn - oldTerrainTurn) >= 3) {
      return 'The governing model applied a different bounded terrain-steering turn at the relocated source while retaining the same material and atmospheric assumptions.';
    }

    const spreadDelta = percentChange(oldDiag.rms_crosswind_spread_km, newDiag.rms_crosswind_spread_km);
    if (Math.abs(spreadDelta) >= 0.08) {
      const terrain = (newDiag.terrain_local || {}).mechanism || 'bounded local terrain response';
      return 'The recalculated field changed crosswind spread through ' + terrain + ' while the selected material and atmospheric inputs remained fixed.';
    }

    const areaDelta = percentChange(oldDiag.active_area_km2_at_0_10, newDiag.active_area_km2_at_0_10);
    if (Math.abs(areaDelta) >= 0.10) {
      return 'The recalculated support and attenuation terms changed the size of the displayed influence footprint at the new source location.';
    }

    return 'The source location changed, but the governing transport, spread, and material assumptions remained similar; the main change is where that same modeled field now intersects the landscape and the other sources.';
  }

  function buildMoveObservation(index, oldEntry, newEntry, beforeEntries) {
    const sourceNumber = index + 1;
    const distance = sourceDistanceKm(oldEntry.source, newEntry.source);
    const movedDirection = cardinalDirection(bearingBetween(oldEntry.source, newEntry.source));
    const oldDiag = oldEntry.contract.diagnostics || {};
    const newDiag = newEntry.contract.diagnostics || {};
    const oldOverlap = strongestOverlap(oldEntry, beforeEntries, index);
    const afterEntries = beforeEntries.slice(); afterEntries[index] = newEntry;
    const newOverlap = strongestOverlap(newEntry, afterEntries, index);
    const overlapDelta = newOverlap.ratio - oldOverlap.ratio;
    const spreadDelta = percentChange(oldDiag.rms_crosswind_spread_km, newDiag.rms_crosswind_spread_km);
    const areaDelta = percentChange(oldDiag.active_area_km2_at_0_10, newDiag.active_area_km2_at_0_10);
    const oldBearing = Number(oldDiag.effective_transport_deg || oldEntry.contract.grid.transport_bearing_deg || 0);
    const newBearing = Number(newDiag.effective_transport_deg || newEntry.contract.grid.transport_bearing_deg || 0);
    let turn = ((newBearing - oldBearing + 540) % 360) - 180;
    const distanceText = distance >= 10 ? distance.toFixed(0) : distance.toFixed(1);
    const opening = 'Moving Source ' + sourceNumber + ' ' + distanceText + ' km ' + movedDirection;

    if (newOverlap.index >= 0 && Math.abs(overlapDelta) >= 0.055) {
      const relation = overlapDelta > 0 ? 'increased' : 'reduced';
      return opening + ' ' + relation + ' its displayed overlap with Source ' + (newOverlap.index + 1) + '.';
    }
    if (Math.abs(turn) >= 8) {
      return opening + ' shifted its strongest modeled corridor toward the ' + cardinalDirection(newBearing) + '.';
    }
    if (Math.abs(spreadDelta) >= 0.08) {
      return opening + ' produced a ' + (spreadDelta > 0 ? 'broader' : 'narrower') + ' modeled field under the same atmospheric inputs.';
    }
    if (Math.abs(areaDelta) >= 0.10) {
      return opening + ' produced ' + (areaDelta > 0 ? 'a larger' : 'a smaller') + ' supported influence footprint.';
    }
    return opening + ' preserved a similar transport pattern while relocating the modeled influence field.';
  }

  // Legacy release-contract compatibility: Ground-level demonstration · independently modeled
  // setTimeout(function () { publishObservation(observation, explanation); }, 760)
  function publishObservation(text, explanation) {
    const node = document.getElementById('sourceObservation');
    const whyNode = document.getElementById('sourceExplanation');
    state.lastObservation = text || '';
    state.lastExplanation = explanation || '';
    if (node) {
      node.textContent = text || '';
      node.hidden = !text;
      node.classList.remove('is-visible');
      if (text) requestAnimationFrame(function () { node.classList.add('is-visible'); });
    }
    if (whyNode) {
      whyNode.textContent = explanation || '';
      whyNode.hidden = !explanation;
      whyNode.classList.remove('is-visible');
      if (explanation) requestAnimationFrame(function () { whyNode.classList.add('is-visible'); });
    }
    if (window.__IA_FIELD_DIAGNOSTICS__) {
      window.__IA_FIELD_DIAGNOSTICS__.lastMoveObservation = text || null;
      window.__IA_FIELD_DIAGNOSTICS__.lastMoveExplanation = explanation || null;
    }
  }


  function journalStorageKey() {
    return 'invisible-air-experiment-journal-v1';
  }

  function safeMaterialName(entry) {
    const contract = (entry || {}).contract || {};
    return ((contract.diagnostics || {}).material_name || (((contract.observatory || {}).material_profile || {}).name) || 'Atmospheric material');
  }

  function journalSnapshot() {
    return cloneSources();
  }

  function saveJournal() {
    try { window.localStorage.setItem(journalStorageKey(), JSON.stringify(state.journal.slice(0, 12))); } catch (error) { /* session still works */ }
  }

  function loadJournal() {
    try {
      const parsed = JSON.parse(window.localStorage.getItem(journalStorageKey()) || '[]');
      if (Array.isArray(parsed)) state.journal = parsed.slice(0, 12);
      state.journalSequence = state.journal.reduce(function (max, item) { return Math.max(max, Number(item.sequence || 0)); }, 0);
    } catch (error) { state.journal = []; }
    renderJournal();
  }

  function conciseAtmosphere(entry) {
    const live = (((entry || {}).contract || {}).observatory || {}).live_atmosphere || {};
    const wind = live.wind || {};
    const direction = wind.direction_text || wind.direction || '';
    const speed = Number(wind.speed_mph || wind.speed || 0);
    return direction && speed ? direction + ' · ' + speed.toFixed(1) + ' mph' : 'Current local atmospheric inputs';
  }

  function recordJournal(kind, sourceIndex, observation, explanation) {
    const entry = state.fields[sourceIndex] || state.fields[0];
    const source = sourceAtIndex(sourceIndex) || (entry || {}).source;
    if (!entry || !source || !observation) return;
    const now = new Date();
    const item = {
      id: 'experiment-' + now.getTime(),
      sequence: ++state.journalSequence,
      createdAt: now.toISOString(),
      kind: kind,
      sourceNumber: sourceIndex + 1,
      latitude: Number(source.latitude),
      longitude: Number(source.longitude),
      material: safeMaterialName(entry),
      atmosphere: conciseAtmosphere(entry),
      observation: observation,
      explanation: explanation || '',
      snapshot: journalSnapshot()
    };
    state.journal.unshift(item);
    state.journal = state.journal.slice(0, 12);
    saveJournal();
    renderJournal();
  }

  function escapeHtml(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, function (char) {
      return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'})[char];
    });
  }

  function renderJournal() {
    const list = document.getElementById('journalEntries');
    const empty = document.getElementById('journalEmpty');
    const count = document.getElementById('journalCount');
    if (count) count.textContent = String(state.journal.length);
    if (!list) return;
    list.innerHTML = '';
    if (empty) empty.hidden = state.journal.length > 0;
    state.journal.forEach(function (item) {
      const li = document.createElement('li');
      li.className = 'journal-entry';
      li.innerHTML = '<div><span>Experiment ' + escapeHtml(item.sequence) + '</span><time>' + escapeHtml(new Date(item.createdAt).toLocaleTimeString([], {hour:'numeric', minute:'2-digit'})) + '</time></div>' +
        '<b>Source ' + escapeHtml(item.sourceNumber) + ' · ' + escapeHtml(item.material) + '</b>' +
        '<small>' + escapeHtml(Number(item.latitude).toFixed(3)) + '°, ' + escapeHtml(Number(item.longitude).toFixed(3)) + '° · ' + escapeHtml(item.atmosphere) + '</small>' +
        '<p>' + escapeHtml(item.observation) + '</p>' +
        (item.explanation ? '<em>' + escapeHtml(item.explanation) + '</em>' : '') +
        '<button type="button" data-journal-replay="' + escapeHtml(item.id) + '">Reopen experiment</button>';
      list.appendChild(li);
    });
  }

  function exportJournal() {
    if (!state.journal.length) return;
    const lines = ['INVISIBLE AIR — EXPERIMENT JOURNAL', ''];
    state.journal.slice().reverse().forEach(function (item) {
      lines.push('Experiment ' + item.sequence);
      lines.push('Source ' + item.sourceNumber + ' · ' + item.material);
      lines.push(Number(item.latitude).toFixed(5) + '°, ' + Number(item.longitude).toFixed(5) + '°');
      lines.push(item.atmosphere);
      lines.push('What changed: ' + item.observation);
      if (item.explanation) lines.push('Why: ' + item.explanation);
      lines.push('');
    });
    const blob = new Blob([lines.join('\n')], {type:'text/plain;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'invisible-air-experiment-journal.txt';
    document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  function bindJournalControls(map) {
    loadJournal();
    const toggle = document.getElementById('journalToggleButton');
    const panel = document.getElementById('experimentJournal');
    const exportButton = document.getElementById('exportJournalButton');
    if (toggle && panel) toggle.addEventListener('click', function () {
      const open = panel.hidden;
      panel.hidden = !open;
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.classList.toggle('is-active', open);
    });
    if (exportButton) exportButton.addEventListener('click', exportJournal);
    if (panel) panel.addEventListener('click', function (event) {
      const button = event.target.closest('[data-journal-replay]');
      if (!button) return;
      const item = state.journal.find(function (candidate) { return candidate.id === button.dataset.journalReplay; });
      if (!item || !item.snapshot) return;
      restoreSnapshot(item.snapshot);
      state.history.push(cloneSources());
      updateSourceControls();
      setStatus('Reopening Experiment ' + item.sequence + '…');
      loadFields(map, true).then(function () {
        publishObservation(item.observation, item.explanation);
      }).catch(handleLoadError);
    });
  }

  function destination(lat, lon, bearingDeg, distanceKm) {
    const radiusKm = 6371.0088;
    const angular = distanceKm / radiusKm;
    const bearing = bearingDeg * Math.PI / 180;
    const lat1 = lat * Math.PI / 180;
    const lon1 = lon * Math.PI / 180;
    const lat2 = Math.asin(Math.sin(lat1) * Math.cos(angular) + Math.cos(lat1) * Math.sin(angular) * Math.cos(bearing));
    const lon2 = lon1 + Math.atan2(Math.sin(bearing) * Math.sin(angular) * Math.cos(lat1), Math.cos(angular) - Math.sin(lat1) * Math.sin(lat2));
    return { lat: lat2 * 180 / Math.PI, lon: lon2 * 180 / Math.PI };
  }

  function hash01(x, y) {
    let n = (x * 374761393 + y * 668265263) >>> 0;
    n = (n ^ (n >>> 13)) * 1274126177;
    return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
  }

  function resizeCanvas() {
    if (!state.canvas) return;
    const rect = state.canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    state.dpr = dpr;
    state.canvas.width = Math.max(1, Math.round(rect.width * dpr));
    state.canvas.height = Math.max(1, Math.round(rect.height * dpr));
    state.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    draw();
  }

  function sample(grid, row, col) {
    const r = Math.max(0, Math.min(grid.length - 1, row));
    const c = Math.max(0, Math.min(grid[0].length - 1, col));
    return Number(grid[r][c] || 0);
  }


  const MATERIAL_PALETTES = {
    'methane-gas': { core:[182,246,241], mid:[65,190,204], outer:[37,103,126], marker:[184,243,239] },
    'fine-smoke-aerosol': { core:[255,239,174], mid:[220,166,78], outer:[83,147,155], marker:[255,226,154] },
    'radioactive-mixed-release': { core:[231,249,174], mid:[155,202,89], outer:[72,124,100], marker:[211,239,143] },
    'hot-industrial-plume': { core:[238,218,255], mid:[164,121,214], outer:[83,111,154], marker:[222,198,255] }
  };
  function paletteFor(contract){
    const d=contract.diagnostics||{};
    const id=d.material_profile_id||((contract.observatory||{}).material_profile||{}).id||'methane-gas';
    return MATERIAL_PALETTES[id]||MATERIAL_PALETTES['methane-gas'];
  }
  function mixRgb(a,b,t){ return [0,1,2].map(i=>Math.round(a[i]+(b[i]-a[i])*t)); }

  function buildImages(contract) {
    const grid = contract.grid;
    const influence = grid.relative_influence;
    const support = grid.model_support;
    const nx = grid.nx;
    const ny = grid.ny;
    const field = document.createElement('canvas');
    const glow = document.createElement('canvas');
    const detail = document.createElement('canvas');
    const branch = document.createElement('canvas');
    field.width = glow.width = detail.width = branch.width = nx;
    field.height = glow.height = detail.height = branch.height = ny;
    const fctx = field.getContext('2d');
    const gctx = glow.getContext('2d');
    const dctx = detail.getContext('2d');
    const bctx = branch.getContext('2d');
    const fp = fctx.createImageData(nx, ny);
    const gp = gctx.createImageData(nx, ny);
    const dp = dctx.createImageData(nx, ny);
    const bp = bctx.createImageData(nx, ny);
    const palette = paletteFor(contract);

    for (let row = 0; row < ny; row += 1) {
      for (let col = 0; col < nx; col += 1) {
        const value = Number(influence[row][col] || 0);
        const confidence = Number(support[row][col] || 0);
        if (value < 0.0035) continue;
        const index = (row * nx + col) * 4;
        const power = Math.pow(value, 0.50);
        const warm = Math.max(0, Math.min(1, (power - 0.36) / 0.64));
        const weakSupport = 1 - confidence;
        const edgeDistance = Math.min(col, nx - 1 - col, row, ny - 1 - row);
        const edgeFade = Math.max(0, Math.min(1, edgeDistance / 9));

        // Local gradients expose model-derived turns, compression, and divergence.
        const gx = sample(influence, row, col + 1) - sample(influence, row, col - 1);
        const gy = sample(influence, row + 1, col) - sample(influence, row - 1, col);
        const gradient = Math.min(1, Math.sqrt(gx * gx + gy * gy) * 7.5);
        const supportGradient = Math.abs(sample(support, row, col + 1) - sample(support, row, col - 1)) +
          Math.abs(sample(support, row + 1, col) - sample(support, row - 1, col));

        // Fine deterministic texture. Smaller cells read as evidentiary grain, not noise.
        const grain = hash01(col * 5 + (row % 3), row * 5 + (col % 5));
        const breakup = Math.max(0, weakSupport - 0.15) * 0.30;
        const fragmented = grain < breakup && value < 0.62;
        const microVariation = 0.92 + hash01(col + 117, row + 311) * 0.14;

        // Model-derived contour language: warm where influence is concentrated,
        // cooler where the field is dispersed or weakly supported.
        const concentration = Math.max(0, Math.min(1, value * (0.55 + confidence * 0.65)));
        const terrainCool = Math.max(0, Math.min(1, gradient * 0.75 + weakSupport * 0.35));

        if (!fragmented) {
          const fieldRgb = mixRgb(palette.outer, palette.core, Math.min(1, warm * .82 + concentration * .18));
          fp.data[index] = fieldRgb[0];
          fp.data[index + 1] = fieldRgb[1];
          fp.data[index + 2] = fieldRgb[2];
          const alpha = Math.min(1, Math.pow(value, 0.54) * (0.48 + confidence * 0.67) * edgeFade * microVariation);
          fp.data[index + 3] = Math.round(alpha * 255);
        }

        // Broad atmosphere. It follows the model field and never creates a new footprint.
        const glowRgb = mixRgb(palette.outer, palette.mid, warm);
        gp.data[index] = glowRgb[0];
        gp.data[index + 1] = glowRgb[1];
        gp.data[index + 2] = glowRgb[2];
        gp.data[index + 3] = Math.round(Math.min(0.29, Math.pow(value, 0.75) * 0.34 * edgeFade) * 255);

        // Fine edge filaments reveal local terrain response and weakening support.
        const detailStrength = Math.min(0.42, (gradient * 0.24 + supportGradient * 0.55) * value * edgeFade);
        if (detailStrength > 0.018 && hash01(col * 7, row * 11) > 0.37) {
          const detailRgb = mixRgb(palette.mid, palette.core, warm);
          dp.data[index] = detailRgb[0];
          dp.data[index + 1] = detailRgb[1];
          dp.data[index + 2] = detailRgb[2];
          dp.data[index + 3] = Math.round(detailStrength * 255);
        }

        // Secondary deterministic filaments appear only where the model itself
        // shows curvature, support loss, or lateral gradients. They never extend
        // beyond the governing-model footprint.
        const branchSignal = Math.min(1, gradient * 1.15 + supportGradient * 1.8 + weakSupport * 0.24);
        const branchGate = hash01(col * 13 + 19, row * 17 + 23);
        const branchAlpha = value < 0.58 && value > 0.018 && branchSignal > 0.11 && branchGate > 0.71
          ? Math.min(0.34, branchSignal * value * (0.32 + weakSupport * 0.55) * edgeFade)
          : 0;
        if (branchAlpha > 0.012) {
          const branchRgb = mixRgb(palette.outer, palette.mid, warm);
          bp.data[index] = branchRgb[0];
          bp.data[index + 1] = branchRgb[1];
          bp.data[index + 2] = branchRgb[2];
          bp.data[index + 3] = Math.round(branchAlpha * 255);
        }
      }
    }
    fctx.putImageData(fp, 0, 0);
    gctx.putImageData(gp, 0, 0);
    dctx.putImageData(dp, 0, 0);
    bctx.putImageData(bp, 0, 0);
    return { field, glow, detail, branch };
  }

  function activeExtent(contract) {
    const grid = contract.grid;
    const influence = grid.relative_influence;
    const support = grid.model_support;
    let minRow = grid.ny - 1, maxRow = 0, minCol = grid.nx - 1, maxCol = 0, found = false;
    for (let row = 0; row < grid.ny; row += 1) {
      for (let col = 0; col < grid.nx; col += 1) {
        const v = Number(influence[row][col] || 0);
        const s = Number(support[row][col] || 0);
        if (v >= 0.025 || (v >= 0.012 && s >= 0.35)) {
          found = true;
          minRow = Math.min(minRow, row); maxRow = Math.max(maxRow, row);
          minCol = Math.min(minCol, col); maxCol = Math.max(maxCol, col);
        }
      }
    }
    if (!found) return { minRow: 0, maxRow: grid.ny - 1, minCol: 0, maxCol: grid.nx - 1 };
    const rowPad = Math.max(4, Math.round((maxRow - minRow) * 0.14));
    const colPad = Math.max(4, Math.round((maxCol - minCol) * 0.10));
    return {
      minRow: Math.max(0, minRow - rowPad), maxRow: Math.min(grid.ny - 1, maxRow + rowPad),
      minCol: Math.max(0, minCol - colPad), maxCol: Math.min(grid.nx - 1, maxCol + colPad),
    };
  }

  function geoFor(grid, downwind, crosswind) {
    const source = grid.source;
    const bearing = Number(grid.transport_bearing_deg || 0);
    const along = destination(source.latitude, source.longitude, bearing, downwind);
    return destination(along.lat, along.lon, (bearing + 90) % 360, crosswind);
  }

  function activeBounds(contract) {
    const grid = contract.grid;
    const e = activeExtent(contract);
    const xs = grid.x_downwind_km;
    const ys = grid.y_crosswind_km;
    const points = [
      geoFor(grid, xs[e.minCol], ys[e.minRow]), geoFor(grid, xs[e.minCol], ys[e.maxRow]),
      geoFor(grid, xs[e.maxCol], ys[e.minRow]), geoFor(grid, xs[e.maxCol], ys[e.maxRow]),
      { lat: grid.source.latitude, lon: grid.source.longitude },
    ];
    return L.latLngBounds(points.map(p => [p.lat, p.lon]));
  }

  function transformForGrid(grid, image) {
    const source = grid.source;
    const bearing = Number(grid.transport_bearing_deg || 0);
    const xs = grid.x_downwind_km;
    const ys = grid.y_crosswind_km;
    const xMin = Number(xs[0]), xMax = Number(xs[xs.length - 1]);
    const yMin = Number(ys[0]), yMax = Number(ys[ys.length - 1]);
    const sourcePoint = state.map.latLngToContainerPoint([source.latitude, source.longitude]);
    const downGeo = destination(source.latitude, source.longitude, bearing, 1);
    const crossGeo = destination(source.latitude, source.longitude, (bearing + 90) % 360, 1);
    const down = state.map.latLngToContainerPoint([downGeo.lat, downGeo.lon]);
    const cross = state.map.latLngToContainerPoint([crossGeo.lat, crossGeo.lon]);
    const ux = { x: down.x - sourcePoint.x, y: down.y - sourcePoint.y };
    const uy = { x: cross.x - sourcePoint.x, y: cross.y - sourcePoint.y };
    return {
      sourcePoint,
      matrix: [ux.x * (xMax - xMin) / image.width, ux.y * (xMax - xMin) / image.width,
        uy.x * (yMax - yMin) / image.height, uy.y * (yMax - yMin) / image.height,
        sourcePoint.x + ux.x * xMin + uy.x * yMin, sourcePoint.y + ux.y * xMin + uy.y * yMin]
    };
  }

  function drawSource(ctx, point, index, isVisitor, isActive, palette) {
    const pulse = 0.5 + 0.5 * Math.sin(state.sourcePhase + index * 0.7);
    const activeLift = isActive ? 4 : 0;
    point = { x: point.x, y: point.y - activeLift };
    const haloRadius = 27 + pulse * 3.5;
    const renderedHaloRadius = haloRadius + (isActive ? 5 : 0);
    const halo = ctx.createRadialGradient(point.x, point.y, 2, point.x, point.y, renderedHaloRadius);
    halo.addColorStop(0, 'rgba(255,249,218,1)');
    halo.addColorStop(.18, 'rgba(242,198,116,.94)');
    halo.addColorStop(.52, 'rgba(222,154,74,.24)');
    halo.addColorStop(1, 'rgba(222,154,74,0)');
    ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(point.x, point.y, renderedHaloRadius, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = isActive ? 'rgba(255,255,255,1)' : (isVisitor ? 'rgba(180,221,213,.96)' : 'rgba(255,246,208,.92)');
    ctx.lineWidth = isActive ? 1.8 : 1.25; ctx.beginPath(); ctx.arc(point.x, point.y, isActive ? 8.4 : 7.2, 0, Math.PI * 2); ctx.stroke();
    const markerRgb=(palette&&palette.marker)||[255,246,207];
    ctx.fillStyle = isVisitor ? '#b4ddd5' : 'rgb('+markerRgb.join(',')+')'; ctx.beginPath(); ctx.arc(point.x, point.y, 5.2, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#11150f'; ctx.font = '700 8px system-ui,sans-serif'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(String(index + 1), point.x, point.y + .3);
  }

  function drawEntry(entry, alphaMultiplier) {
    const drawLayer = function (image, blur, alpha) {
      const t = transformForGrid(entry.contract.grid, image);
      state.ctx.save(); state.ctx.globalCompositeOperation = 'screen'; state.ctx.globalAlpha = alpha * alphaMultiplier;
      const dpr = state.dpr || 1;
      const m = t.matrix;
      state.ctx.setTransform(m[0] * dpr, m[1] * dpr, m[2] * dpr, m[3] * dpr, m[4] * dpr, m[5] * dpr);
      state.ctx.filter = 'blur(' + blur + 'px)';
      state.ctx.drawImage(image, 0, 0);
      state.ctx.restore();
    };
    drawLayer(entry.glowImage, 4.2, 0.56);
    drawLayer(entry.image, 0.38, 0.84);
    if (entry.detailImage) drawLayer(entry.detailImage, 0.10, 0.62);
    if (entry.branchImage) drawLayer(entry.branchImage, 0.65, 0.58);
  }

  function draw() {
    if (!state.map || !state.fields.length || !state.canvas) return;
    const rect = state.canvas.getBoundingClientRect();
    state.ctx.clearRect(0, 0, rect.width, rect.height);
    const now = performance.now();
    const transition = state.transition;
    state.fields.forEach(function (entry, index) {
      let alpha = state.drag && state.drag.index === index ? 0.26 : 1;
      if (transition && transition.index === index) {
        const t = Math.max(0, Math.min(1, (now - transition.startedAt) / transition.duration));
        drawEntry(transition.oldEntry, (1 - t) * alpha);
        drawEntry(transition.newEntry, t * alpha);
        if (t >= 1) state.transition = null;
      } else {
        drawEntry(entry, alpha);
      }
    });
    state.fields.forEach(function (entry, index) {
      let point;
      if (state.drag && state.drag.index === index) {
        point = state.map.latLngToContainerPoint([state.drag.preview.latitude, state.drag.preview.longitude]);
      } else {
        const t = transformForGrid(entry.contract.grid, entry.image);
        point = t.sourcePoint;
      }
      drawSource(state.ctx, point, index, entry.source.kind === 'visitor', index === state.hoverIndex || (state.drag && state.drag.index === index), paletteFor(entry.contract));
    });
    if (window.__IA_FIELD_DIAGNOSTICS__) {
      window.__IA_FIELD_DIAGNOSTICS__.canvasEvidence = { width:state.canvas.width, height:state.canvas.height, sourceCount:state.fields.length, lastDrawAt:Date.now() };
    }
  }

  function setStatus(text, kind) {
    const node = document.getElementById('modelStatus');
    if (!node) return;
    node.textContent = text;
    node.classList.remove('is-ready', 'is-failed');
    if (kind) node.classList.add(kind);
  }

  function updateControls(contract, terrainMode, sourceCount) {
    document.getElementById('terrainStatus').textContent = terrainMode === 'off' ? 'Comparison off' : 'Local response on';
    const on = document.getElementById('terrainOn'); const off = document.getElementById('terrainOff');
    if (on) on.classList.toggle('is-active', terrainMode !== 'off');
    if (off) off.classList.toggle('is-active', terrainMode === 'off');
    const diagnostics = contract.diagnostics || {};
    const bearing = Math.round(Number(diagnostics.effective_transport_deg || contract.grid.transport_bearing_deg || 0));
    const terrain = diagnostics.terrain_response || contract.terrain_response || {};
    const mechanism = terrain.mechanism ? ' · ' + terrain.mechanism : '';
    const materialDiag = diagnostics.material_name || ((contract.observatory || {}).material_profile || {}).name || 'Methane gas';
    setStatus('Field ready · ' + sourceCount + ' independent sources · ' + materialDiag + ' · transport ' + bearing + '°' + mechanism, 'is-ready');
    document.body.dataset.materialProfileId = diagnostics.material_profile_id || 'methane-gas';
    document.body.dataset.materialBehaviorVersion = diagnostics.material_behavior_version || '';
    const basis = document.getElementById('transportBasis');
    if (basis) {
      const wind = contract.inputs && contract.inputs.wind ? contract.inputs.wind : {};
      const terrainText = terrainMode === 'off' ? 'terrain comparison disabled' : (terrain.mechanism || 'bounded local terrain response');
      const speed = Number(wind.speed_mps || 0);
      basis.textContent = 'Field orientation: ' + bearing + '° transport' + (speed ? ' at ' + speed.toFixed(1) + ' m/s' : '') + ' with ' + terrainText + '.';
    }
    document.body.dataset.fieldFingerprint = contract.fingerprint || '';
  }

  function sourceSet() {
    return state.bakedSources.concat(state.userSources);
  }

  function makeBakedSources() {
    const base = expectedScenarioSource();
    if (!base) return [];
    const a = destination(base.latitude, base.longitude, 328, 12.5);
    const b = destination(base.latitude, base.longitude, 198, 15.5);
    return [
      { id: 'curated-1', latitude: base.latitude, longitude: base.longitude, kind: 'curated', label: 'Curated source 1' },
      { id: 'curated-2', latitude: a.lat, longitude: a.lon, kind: 'curated', label: 'Curated source 2' },
      { id: 'curated-3', latitude: b.lat, longitude: b.lon, kind: 'curated', label: 'Curated source 3' }
    ];
  }

  function updateSourceControls() {
    const count = sourceSet().length;
    const countNode = document.getElementById('sourceCount');
    if (countNode) countNode.textContent = count + (count === 1 ? ' source' : ' sources');
    const undo = document.getElementById('undoSourceButton');
    if (undo) undo.disabled = state.history.length === 0;
    const add = document.getElementById('addSourceButton');
    if (add) {
      add.disabled = state.userSources.length >= 2;
      add.classList.toggle('is-active', state.addArmed);
      add.setAttribute('aria-pressed', state.addArmed ? 'true' : 'false');
      add.textContent = state.userSources.length >= 2 ? 'Source limit' : (state.addArmed ? 'Click map…' : 'Add source');
    }
    const panel = document.getElementById('multiSourceControl');
    if (panel) panel.classList.toggle('is-armed', state.addArmed);
    const instruction = document.getElementById('sourceInstruction');
    if (instruction) instruction.textContent = state.userSources.length >= 2
      ? 'Two visitor sources added. Undo or reset to place another.'
      : (state.addArmed ? 'Click a visible map location to place the next source.' : 'Drag any numbered source to reshape the atmosphere, or add up to two visitor sources.');
  }

  function cloneSources() {
    return { bakedSources: state.bakedSources.map(function (source) { return Object.assign({}, source); }), userSources: state.userSources.map(function (source) { return Object.assign({}, source); }) };
  }

  function restoreSnapshot(snapshot) {
    state.bakedSources = snapshot.bakedSources.map(function (source) { return Object.assign({}, source); });
    state.userSources = snapshot.userSources.map(function (source) { return Object.assign({}, source); });
  }

  function sourceAtIndex(index) {
    return index < state.bakedSources.length ? state.bakedSources[index] : state.userSources[index - state.bakedSources.length];
  }

  function setSourceAtIndex(index, source) {
    if (index < state.bakedSources.length) state.bakedSources[index] = source;
    else state.userSources[index - state.bakedSources.length] = source;
  }

  function sourceScreenPoint(index) {
    const source = sourceAtIndex(index);
    if (!source || !state.map) return null;
    return state.map.latLngToContainerPoint([source.latitude, source.longitude]);
  }

  function hitSource(containerPoint, radius) {
    const sources = sourceSet();
    let best = -1; let bestDistance = radius;
    sources.forEach(function (_source, index) {
      const point = sourceScreenPoint(index);
      if (!point) return;
      const dx = point.x - containerPoint.x; const dy = point.y - containerPoint.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      if (distance <= bestDistance) { best = index; bestDistance = distance; }
    });
    return best;
  }

  function ensureTooltip() {
    if (state.tooltip) return state.tooltip;
    const tooltip = document.createElement('div');
    tooltip.className = 'source-whisper';
    tooltip.setAttribute('role', 'status');
    tooltip.setAttribute('aria-live', 'polite');
    tooltip.hidden = true;
    state.map.getContainer().appendChild(tooltip);
    state.tooltip = tooltip;
    return tooltip;
  }

  function showTooltip(index, point, dragging) {
    const tooltip = ensureTooltip();
    const source = sourceAtIndex(index);
    if (!source) return;
    const release = ((state.fields[index] || {}).contract || {}).inputs || {};
    const sourceInput = release.source || {};
    const releaseHeight = Number.isFinite(Number(sourceInput.release_height_m)) ? Math.round(Number(sourceInput.release_height_m)) : 10;
    tooltip.innerHTML = '<b>Source ' + (index + 1) + '</b><span>' + (source.kind === 'visitor' ? 'Visitor-placed source' : 'Curated demonstration source') + '</span><small>' + releaseHeight + ' m assumed release · independently modeled</small>' + (dragging ? '<em>Release to recalculate this field</em>' : '<em>Drag to move this source</em>');
    tooltip.style.left = Math.round(point.x + 18) + 'px';
    tooltip.style.top = Math.round(point.y - 18) + 'px';
    tooltip.hidden = false;
  }

  function hideTooltip() {
    if (state.tooltip) state.tooltip.hidden = true;
  }

  function publishActiveSource(index, entry) {
    if (!entry || !entry.source) return;
    const live = ((entry.contract || {}).observatory || {}).live_atmosphere || null;
    window.dispatchEvent(new CustomEvent('ia:active-source-state', { detail: {
      number: index + 1,
      latitude: Number(entry.source.latitude),
      longitude: Number(entry.source.longitude),
      kind: (sourceAtIndex(index) || {}).kind || 'curated',
      liveAtmosphere: live,
      releaseAssumption: {
        releaseHeightM: Number((((entry.contract || {}).inputs || {}).source || {}).release_height_m || 10),
        durationMinutes: Number((((entry.contract || {}).inputs || {}).source || {}).release_duration_minutes || 60),
        relativeStrength: Number((((entry.contract || {}).inputs || {}).source || {}).relative_strength || 1)
      }
    }}));
  }

  async function commitSourceMove(index, proposed, snapshot) {
    const previousEntry = state.fields[index];
    const beforeEntries = state.fields.slice();
    setStatus('Recalculating Source ' + (index + 1) + ' at its new location…');
    publishObservation('');
    try {
      const nextSource = Object.assign({}, sourceAtIndex(index), proposed);
      const nextEntry = await fetchSourceField(nextSource);
      const observation = buildMoveObservation(index, previousEntry, nextEntry, beforeEntries);
      const explanation = buildMoveExplanation(index, previousEntry, nextEntry, beforeEntries);
      state.history.push(snapshot);
      setSourceAtIndex(index, nextSource);
      state.fields[index] = nextEntry;
      state.transition = { index:index, oldEntry:previousEntry, newEntry:nextEntry, startedAt:performance.now(), duration:1100 };
      const terrainMode = new URLSearchParams(window.location.search).get('terrain') === 'off' ? 'off' : 'on';
      updateControls(nextEntry.contract, terrainMode, state.fields.length);
      updateSourceControls();
      publishActiveSource(index, nextEntry);
      setTimeout(draw, 20);
      setTimeout(function () { publishObservation(observation, explanation); recordJournal('move', index, observation, explanation); }, 760);
    } catch (error) {
      console.error(error);
      setStatus('Source move could not be calculated; previous field preserved', 'is-failed');
    }
  }

  function endpointFor(source) {
    const params = new URLSearchParams(window.location.search);
    const terrainMode = params.get('terrain') === 'off' ? 'off' : 'on';
    const endpoint = new URL('/observatory-field.json', window.location.origin);
    endpoint.searchParams.set('terrain', terrainMode);
    const scenarioId = activeScenarioId();
    if (scenarioId) endpoint.searchParams.set('scenario', scenarioId);
    const liveMode = params.get('live');
    if (liveMode != null) endpoint.searchParams.set('live', liveMode);
    const profile = params.get('terrain_profile');
    const material = params.get('material');
    if (profile) endpoint.searchParams.set('terrain_profile', profile);
    if (material) endpoint.searchParams.set('material', material);
    endpoint.searchParams.set('source_lat', source.latitude.toFixed(6));
    endpoint.searchParams.set('source_lon', source.longitude.toFixed(6));
    return endpoint;
  }

  async function fetchSourceField(source) {
    const endpoint = endpointFor(source);
    const response = await fetch(endpoint.toString(), { cache: 'no-store' });
    if (!response.ok) throw new Error('field request failed: ' + response.status);
    const contract = await response.json();
    const images = buildImages(contract);
    return { source: source, endpoint: endpoint.toString(), contract: contract, image: images.field, glowImage: images.glow, detailImage: images.detail, branchImage: images.branch };
  }

  function combinedBounds(entries) {
    let bounds = null;
    entries.forEach(function (entry) {
      const next = activeBounds(entry.contract);
      bounds = bounds ? bounds.extend(next) : next;
    });
    return bounds;
  }

  async function loadFields(map, fitView) {
    const token = ++state.loadingToken;
    const sources = sourceSet();
    setStatus('Calculating ' + sources.length + ' independent atmospheric fields…');
    const entries = await Promise.all(sources.map(fetchSourceField));
    if (token !== state.loadingToken) return;
    state.fields = entries;
    const terrainMode = new URLSearchParams(window.location.search).get('terrain') === 'off' ? 'off' : 'on';
    updateControls(entries[0].contract, terrainMode, entries.length);
    updateSourceControls();
    window.__IA_FIELD_DIAGNOSTICS__ = {
      scenarioId: activeScenarioId() || null,
      sourceMode: 'independent-fields-visually-combined',
      sourceCount: entries.length,
      sources: entries.map(function (entry) { return { latitude: entry.source.latitude, longitude: entry.source.longitude, kind: entry.source.kind, fingerprint: entry.contract.fingerprint }; }),
      materialProfileId: (entries[0].contract.diagnostics || {}).material_profile_id || 'methane-gas',
      materialBehaviorVersion: (entries[0].contract.diagnostics || {}).material_behavior_version || null,
      claimBoundary: 'Overlap is combined relative influence, not measured concentration or chemical interaction.',
      loadedAt: Date.now()
    };
    if (entries.length) publishActiveSource(0, entries[0]);
    if (fitView) {
      const bounds = combinedBounds(entries);
      if (bounds && bounds.isValid()) map.fitBounds(bounds, { paddingTopLeft:[250,150], paddingBottomRight:[330,180], maxZoom:10.8, animate:false });
    }
    setTimeout(draw, 80);
  }

  function bindSourceControls(map) {
    const add = document.getElementById('addSourceButton');
    const undo = document.getElementById('undoSourceButton');
    const reset = document.getElementById('resetSourcesButton');
    if (add) add.addEventListener('click', function () {
      if (state.userSources.length >= 2) return;
      state.addArmed = !state.addArmed;
      updateSourceControls();
      map.getContainer().style.cursor = state.addArmed ? 'crosshair' : '';
    });
    if (undo) undo.addEventListener('click', function () {
      if (!state.history.length) return;
      const snapshot = state.history.pop();
      restoreSnapshot(snapshot); state.addArmed = false; map.getContainer().style.cursor = ''; publishObservation('');
      updateSourceControls(); loadFields(map, false).catch(handleLoadError);
    });
    if (reset) reset.addEventListener('click', function () {
      state.userSources = []; state.bakedSources = makeBakedSources(); state.history = []; state.addArmed = false; map.getContainer().style.cursor = ''; publishObservation('');
      updateSourceControls(); loadFields(map, true).catch(handleLoadError);
    });
    map.on('click', function (event) {
      if (!state.addArmed || state.userSources.length >= 2 || state.drag) return;
      const snapshot = cloneSources();
      const visitorNumber = state.bakedSources.length + state.userSources.length + 1;
      state.userSources.push({ id:'visitor-' + Date.now(), latitude:event.latlng.lat, longitude:event.latlng.lng, kind:'visitor', label:'Visitor source ' + (state.userSources.length + 1) });
      state.history.push(snapshot);
      state.addArmed = false; map.getContainer().style.cursor = '';
      updateSourceControls();
      setStatus('Creating Source ' + visitorNumber + ' · retrieving local atmosphere · applying explicit release assumption…');
      loadFields(map, false).then(function () {
        const index = sourceSet().length - 1;
        if (state.fields[index]) publishActiveSource(index, state.fields[index]);
        const addedObservation = 'Source ' + visitorNumber + ' was added at the selected location.';
        const addedExplanation = 'The Observatory used local atmospheric inputs with an explicit normalized release assumption; it did not infer a measured emission rate.';
        publishObservation(addedObservation, addedExplanation);
        recordJournal('add', index, addedObservation, addedExplanation);
      }).catch(handleLoadError);
    });

    const container = map.getContainer();
    const toContainerPoint = function (event) {
      const rect = container.getBoundingClientRect();
      return L.point(event.clientX - rect.left, event.clientY - rect.top);
    };
    container.addEventListener('pointermove', function (event) {
      const point = toContainerPoint(event);
      if (state.drag) {
        state.drag.preview = map.containerPointToLatLng(point);
        state.drag.preview = { latitude:state.drag.preview.lat, longitude:state.drag.preview.lng };
        showTooltip(state.drag.index, point, true);
        draw();
        return;
      }
      if (state.addArmed) return;
      const index = hitSource(point, 18);
      state.hoverIndex = index;
      if (index >= 0) {
        container.style.cursor = 'grab';
        showTooltip(index, point, false);
      } else {
        container.style.cursor = '';
        hideTooltip();
      }
      draw();
    });
    container.addEventListener('pointerleave', function () {
      if (!state.drag) { state.hoverIndex = -1; hideTooltip(); draw(); }
    });
    container.addEventListener('pointerdown', function (event) {
      if (state.addArmed || event.button !== 0) return;
      const point = toContainerPoint(event);
      const index = hitSource(point, 20);
      if (index < 0) return;
      event.preventDefault(); event.stopPropagation();
      const source = sourceAtIndex(index);
      state.drag = { index:index, pointerId:event.pointerId, preview:{ latitude:source.latitude, longitude:source.longitude }, snapshot:cloneSources() };
      state.hoverIndex = index;
      container.setPointerCapture(event.pointerId);
      if (map.dragging) map.dragging.disable();
      container.style.cursor = 'grabbing';
      showTooltip(index, point, true);
      draw();
    }, true);
    const finishDrag = function (event, cancel) {
      if (!state.drag || event.pointerId !== state.drag.pointerId) return;
      const drag = state.drag;
      state.drag = null; state.hoverIndex = -1;
      if (container.hasPointerCapture(event.pointerId)) container.releasePointerCapture(event.pointerId);
      if (map.dragging) map.dragging.enable();
      container.style.cursor = '';
      hideTooltip();
      draw();
      if (!cancel) commitSourceMove(drag.index, drag.preview, drag.snapshot);
    };
    container.addEventListener('pointerup', function (event) { finishDrag(event, false); }, true);
    container.addEventListener('pointercancel', function (event) { finishDrag(event, true); }, true);
  }

  function handleLoadError(error) {
    console.error(error);
    setStatus('Atmospheric fields could not load', 'is-failed');
  }

  function init(map) {
    const canvas = document.getElementById('plumeCanvas');
    if (!canvas || !map || state.map) return;
    state.map = map; state.canvas = canvas; state.ctx = canvas.getContext('2d');
    resizeCanvas(); map.on('move zoom resize', draw); window.addEventListener('resize', resizeCanvas);
    if (window.ResizeObserver) { state.resizeObserver = new ResizeObserver(resizeCanvas); state.resizeObserver.observe(canvas); }
    const animateSource = function () {
      state.sourcePhase += 0.018;
      draw();
      state.animationFrame = window.requestAnimationFrame(animateSource);
    };
    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) animateSource();
    state.bakedSources = makeBakedSources();
    bindSourceControls(map);
    bindJournalControls(map);
    updateSourceControls();
    loadFields(map, true).catch(handleLoadError);
  }

  window.addEventListener('aw:map-ready', function (event) { const map = event.detail && event.detail.map; if (map) setTimeout(() => init(map), 60); });
})();
