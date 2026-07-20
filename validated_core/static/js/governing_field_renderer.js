(function () {
  'use strict';

  const state = { map: null, canvas: null, ctx: null, field: null, image: null, glowImage: null, detailImage: null, branchImage: null, resizeObserver: null, sourcePhase: 0, animationFrame: null };

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
          fp.data[index] = Math.round(82 + 172 * warm + 12 * concentration);
          fp.data[index + 1] = Math.round(173 + 74 * warm - 8 * terrainCool);
          fp.data[index + 2] = Math.round(194 - 77 * warm + 12 * terrainCool);
          const alpha = Math.min(1, Math.pow(value, 0.54) * (0.48 + confidence * 0.67) * edgeFade * microVariation);
          fp.data[index + 3] = Math.round(alpha * 255);
        }

        // Broad atmosphere. It follows the model field and never creates a new footprint.
        gp.data[index] = Math.round(86 + 155 * warm);
        gp.data[index + 1] = Math.round(171 + 70 * warm);
        gp.data[index + 2] = Math.round(184 - 51 * warm);
        gp.data[index + 3] = Math.round(Math.min(0.29, Math.pow(value, 0.75) * 0.34 * edgeFade) * 255);

        // Fine edge filaments reveal local terrain response and weakening support.
        const detailStrength = Math.min(0.42, (gradient * 0.24 + supportGradient * 0.55) * value * edgeFade);
        if (detailStrength > 0.018 && hash01(col * 7, row * 11) > 0.37) {
          dp.data[index] = Math.round(115 + 125 * warm);
          dp.data[index + 1] = Math.round(196 + 48 * warm);
          dp.data[index + 2] = Math.round(201 - 61 * warm);
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
          bp.data[index] = Math.round(104 + 112 * warm);
          bp.data[index + 1] = Math.round(189 + 38 * warm);
          bp.data[index + 2] = Math.round(204 - 42 * warm);
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

  function transformForGrid(grid) {
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
      matrix: [ux.x * (xMax - xMin) / state.image.width, ux.y * (xMax - xMin) / state.image.width,
        uy.x * (yMax - yMin) / state.image.height, uy.y * (yMax - yMin) / state.image.height,
        sourcePoint.x + ux.x * xMin + uy.x * yMin, sourcePoint.y + ux.y * xMin + uy.y * yMin]
    };
  }

  function drawSource(ctx, point) {
    const pulse = 0.5 + 0.5 * Math.sin(state.sourcePhase);
    const haloRadius = 27 + pulse * 3.5;
    const halo = ctx.createRadialGradient(point.x, point.y, 2, point.x, point.y, haloRadius);
    halo.addColorStop(0, 'rgba(255,249,218,1)');
    halo.addColorStop(.16, 'rgba(242,198,116,.96)');
    halo.addColorStop(.48, 'rgba(222,154,74,.30)');
    halo.addColorStop(1, 'rgba(222,154,74,0)');
    ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(point.x, point.y, haloRadius, 0, Math.PI * 2); ctx.fill();
    ctx.strokeStyle = 'rgba(255,242,190,' + (0.28 + pulse * 0.14) + ')';
    ctx.lineWidth = 0.7; ctx.beginPath(); ctx.arc(point.x, point.y, 10.5 + pulse * 1.8, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeStyle = 'rgba(255,246,208,.92)'; ctx.lineWidth = 1.2; ctx.beginPath(); ctx.arc(point.x, point.y, 6.5, 0, Math.PI * 2); ctx.stroke();
    ctx.fillStyle = '#fff6cf'; ctx.beginPath(); ctx.arc(point.x, point.y, 3.4, 0, Math.PI * 2); ctx.fill();
  }

  function draw() {
    if (!state.map || !state.field || !state.image) return;
    const rect = state.canvas.getBoundingClientRect();
    state.ctx.clearRect(0, 0, rect.width, rect.height);
    const t = transformForGrid(state.field.grid);
    const drawLayer = function (image, blur, alpha) {
      state.ctx.save(); state.ctx.globalCompositeOperation = 'screen'; state.ctx.globalAlpha = alpha;
      state.ctx.setTransform.apply(state.ctx, t.matrix); state.ctx.filter = 'blur(' + blur + 'px)'; state.ctx.drawImage(image, 0, 0); state.ctx.restore();
    };
    drawLayer(state.glowImage, 4.4, 0.74);
    drawLayer(state.image, 0.38, 1);
    if (state.detailImage) drawLayer(state.detailImage, 0.10, 0.82);
    if (state.branchImage) drawLayer(state.branchImage, 0.65, 0.78);
    drawSource(state.ctx, t.sourcePoint);
  }

  function setStatus(text, kind) {
    const node = document.getElementById('modelStatus');
    if (!node) return;
    node.textContent = text;
    node.classList.remove('is-ready', 'is-failed');
    if (kind) node.classList.add(kind);
  }

  function updateControls(contract, terrainMode) {
    document.getElementById('terrainStatus').textContent = terrainMode === 'off' ? 'Comparison off' : 'Local response on';
    const on = document.getElementById('terrainOn'); const off = document.getElementById('terrainOff');
    if (on) on.classList.toggle('is-active', terrainMode !== 'off');
    if (off) off.classList.toggle('is-active', terrainMode === 'off');
    const diagnostics = contract.diagnostics || {};
    const bearing = Math.round(Number(diagnostics.effective_transport_deg || contract.grid.transport_bearing_deg || 0));
    const terrain = diagnostics.terrain_response || contract.terrain_response || {};
    const mechanism = terrain.mechanism ? ' · ' + terrain.mechanism : '';
    setStatus('Field ready · transport ' + bearing + '°' + mechanism, 'is-ready');
    const basis = document.getElementById('transportBasis');
    if (basis) {
      const wind = contract.inputs && contract.inputs.wind ? contract.inputs.wind : {};
      const terrainText = terrainMode === 'off' ? 'terrain comparison disabled' : (terrain.mechanism || 'bounded local terrain response');
      const speed = Number(wind.speed_mps || 0);
      basis.textContent = 'Field orientation: ' + bearing + '° transport' + (speed ? ' at ' + speed.toFixed(1) + ' m/s' : '') + ' with ' + terrainText + '.';
    }
    document.body.dataset.fieldFingerprint = contract.fingerprint || '';
  }

  async function loadField(map) {
    const params = new URLSearchParams(window.location.search);
    const terrainMode = params.get('terrain') === 'off' ? 'off' : 'on';
    const profile = params.get('terrain_profile');
    const endpoint = new URL('/observatory-field.json', window.location.origin);
    endpoint.searchParams.set('terrain', terrainMode);
    if (profile) endpoint.searchParams.set('terrain_profile', profile);
    const response = await fetch(endpoint.toString(), { cache: 'no-store' });
    if (!response.ok) throw new Error('field request failed: ' + response.status);
    const contract = await response.json();
    state.field = contract;
    const images = buildImages(contract); state.image = images.field; state.glowImage = images.glow; state.detailImage = images.detail; state.branchImage = images.branch;
    updateControls(contract, terrainMode);
    map.fitBounds(activeBounds(contract), { paddingTopLeft: [250, 150], paddingBottomRight: [330, 180], maxZoom: 11.8, animate: false });
    setTimeout(draw, 140);
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
    loadField(map).catch(function (error) { console.error(error); setStatus('Atmospheric field could not load', 'is-failed'); });
  }

  window.addEventListener('aw:map-ready', function (event) { const map = event.detail && event.detail.map; if (map) setTimeout(() => init(map), 60); });
})();
