(function () {
  'use strict';

  function isCinematicArrival() {
    const params = new URLSearchParams(window.location.search);
    return params.get('arrival') === 'cinematic';
  }

  function hardResetCanvas(canvas) {
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const width = Math.max(1, Math.round(rect.width * dpr));
    const height = Math.max(1, Math.round(rect.height * dpr));

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext && canvas.getContext('2d');
    if (ctx) {
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = 'source-over';
      ctx.filter = 'none';
      ctx.clearRect(0, 0, width, height);
    }
  }

  function resetAtmosphericCanvases() {
    const selectors = [
      '.plume-canvas',
      '.governing-field-canvas',
      'canvas[data-atmospheric-field]',
      '.observatory-window canvas'
    ];

    const seen = new Set();

    selectors.forEach(function (selector) {
      document.querySelectorAll(selector).forEach(function (canvas) {
        if (seen.has(canvas)) return;
        seen.add(canvas);
        if (canvas.classList.contains('national-ambient-canvas')) return;
        hardResetCanvas(canvas);
      });
    });
  }

  function waitForVisibleTiles(map, timeoutMs) {
    return new Promise(function (resolve) {
      let resolved = false;
      let pending = 0;
      let loaded = 0;
      const cleanup = [];

      function finish() {
        if (resolved) return;
        resolved = true;
        cleanup.forEach(function (fn) { fn(); });
        resolve();
      }

      map.eachLayer(function (layer) {
        if (!layer || typeof layer.on !== 'function') return;
        if (!(layer instanceof L.TileLayer)) return;

        pending += 1;

        const onLoad = function () {
          loaded += 1;
          if (loaded >= pending) finish();
        };

        layer.on('load', onLoad);
        cleanup.push(function () { layer.off('load', onLoad); });

        if (layer.isLoading && !layer.isLoading()) loaded += 1;
      });

      if (pending === 0 || loaded >= pending) {
        window.setTimeout(finish, 80);
      }

      window.setTimeout(finish, timeoutMs || 1800);
    });
  }

  function nextFrames(count) {
    return new Promise(function (resolve) {
      function step(remaining) {
        if (remaining <= 0) {
          resolve();
          return;
        }
        requestAnimationFrame(function () { step(remaining - 1); });
      }
      step(count || 2);
    });
  }

  async function stabilizeArrival(map) {
    const body = document.body;
    const shell = document.getElementById('main-content');
    if (!body || !shell) return;

    body.classList.add('cinematic-arrival-pending');
    body.classList.remove('cinematic-arrival-ready');

    map.stop();
    map.invalidateSize({ pan: false, debounceMoveend: true });

    await waitForVisibleTiles(map, 1900);
    await nextFrames(2);

    resetAtmosphericCanvases();

    window.dispatchEvent(new Event('resize'));
    map.fire('resize');
    map.fire('moveend');
    map.fire('zoomend');

    await nextFrames(3);

    body.classList.remove('cinematic-arrival-pending');
    body.classList.add('cinematic-arrival-ready');

    window.setTimeout(function () {
      window.dispatchEvent(new Event('resize'));
      map.invalidateSize({ pan: false, debounceMoveend: true });
    }, 180);
  }

  window.addEventListener('aw:map-ready', function (event) {
    if (!isCinematicArrival()) return;

    const map = event.detail && event.detail.map;
    if (!map) return;

    let timer = null;

    function scheduleStabilization(delay) {
      if (timer) window.clearTimeout(timer);
      timer = window.setTimeout(function () {
        stabilizeArrival(map);
      }, delay || 120);
    }

    map.on('movestart zoomstart', function () {
      document.body.classList.add('cinematic-arrival-pending');
      document.body.classList.remove('cinematic-arrival-ready');
    });

    map.on('moveend zoomend', function () {
      scheduleStabilization(140);
    });

    scheduleStabilization(220);
  });
})();