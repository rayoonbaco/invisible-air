(function () {
  'use strict';

  const LOWER_48_BOUNDS = L.latLngBounds([[24.4, -125.0], [49.5, -66.5]]);

  const PLANNED_NODES = [
    { name: 'Central Valley, California', latitude: 36.70, longitude: -119.70 },
    { name: 'Las Vegas Basin, Nevada', latitude: 36.17, longitude: -115.14 },
    { name: 'Phoenix Basin, Arizona', latitude: 33.45, longitude: -112.07 },
    { name: 'San Juan Basin, New Mexico', latitude: 36.75, longitude: -107.60 },
    { name: 'Denver-Julesburg Basin', latitude: 40.15, longitude: -104.75 },
    { name: 'Powder River Basin', latitude: 44.25, longitude: -105.50 },
    { name: 'Williston Basin', latitude: 47.80, longitude: -103.30 },
    { name: 'Anadarko Basin', latitude: 35.35, longitude: -98.55 },
    { name: 'Gulf Coast, Texas', latitude: 29.50, longitude: -95.10 },
    { name: 'Haynesville Region', latitude: 32.20, longitude: -93.75 },
    { name: 'Illinois Basin', latitude: 38.80, longitude: -88.50 },
    { name: 'Michigan Basin', latitude: 43.70, longitude: -84.50 },
    { name: 'Marcellus Region', latitude: 41.40, longitude: -77.80 },
    { name: 'New York-Pennsylvania Border', latitude: 42.00, longitude: -76.20 },
    { name: 'Ohio River Valley', latitude: 39.70, longitude: -82.50 },
    { name: 'Black Warrior Basin', latitude: 33.20, longitude: -87.50 },
    { name: 'South Florida', latitude: 26.20, longitude: -81.10 },
    { name: 'Central Appalachia', latitude: 37.60, longitude: -82.30 },
    { name: 'Pacific Northwest', latitude: 46.40, longitude: -122.40 },
    { name: 'Southern Rockies', latitude: 37.30, longitude: -106.20 }
  ];

  const PERSONALITIES = {
    'oxnard-coastal': { className: 'node-ocean', cadence: '6.8s', delay: '-1.2s' },
    'permian-basin': { className: 'node-amber', cadence: '4.9s', delay: '-2.8s' },
    'four-corners': { className: 'node-white', cadence: '5.7s', delay: '-.7s' },
    'appalachian-basin': { className: 'node-sage', cadence: '7.6s', delay: '-3.9s' },
    'uinta-basin': { className: 'node-silver', cadence: '6.2s', delay: '-2.1s' }
  };

  function cardinal(degrees) {
    const labels = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW'];
    return labels[Math.round((((Number(degrees) % 360) + 360) % 360) / 22.5) % 16];
  }

  function mph(mps) {
    return Math.round(Number(mps || 0) * 2.23694 * 10) / 10;
  }

  function destination(lat, lon, bearingDeg, distanceKm) {
    const radiusKm = 6371;
    const angular = distanceKm / radiusKm;
    const bearing = bearingDeg * Math.PI / 180;
    const lat1 = lat * Math.PI / 180;
    const lon1 = lon * Math.PI / 180;
    const lat2 = Math.asin(
      Math.sin(lat1) * Math.cos(angular) +
      Math.cos(lat1) * Math.sin(angular) * Math.cos(bearing)
    );
    const lon2 = lon1 + Math.atan2(
      Math.sin(bearing) * Math.sin(angular) * Math.cos(lat1),
      Math.cos(angular) - Math.sin(lat1) * Math.sin(lat2)
    );
    return [lat2 * 180 / Math.PI, lon2 * 180 / Math.PI];
  }


  function materialClass(profileId) {
    const map = {
      'methane-gas': 'material-methane',
      'fine-smoke-aerosol': 'material-smoke',
      'radioactive-mixed-release': 'material-radioactive',
      'hot-industrial-plume': 'material-industrial'
    };
    return map[profileId] || 'material-neutral';
  }

  function siteIcon(site) {
    return L.divIcon({
      className: 'national-site-foundation ' + materialClass(site.material_profile_id) + (site.status === 'curated_demo' ? ' is-curated' : ' is-planned'),
      html: '<span></span>', iconSize:[20,20], iconAnchor:[10,10]
    });
  }

  function scenarioIcon(scenario, active) {
    const personality = PERSONALITIES[scenario.id] || PERSONALITIES['oxnard-coastal'];
    return L.divIcon({
      className: 'national-scenario-icon living-node ' + personality.className + (active ? ' is-active' : ''),
      html:
        '<span class="node-orbit"></span>' +
        '<span class="node-halo"></span>' +
        '<span class="node-core" style="--node-cadence:' + personality.cadence + ';--node-delay:' + personality.delay + '"></span>',
      iconSize: [38, 38],
      iconAnchor: [19, 19]
    });
  }

  function plannedIcon() {
    return L.divIcon({
      className: 'national-planned-icon',
      html: '<span></span>',
      iconSize: [18, 18],
      iconAnchor: [9, 9]
    });
  }

  function createAmbientCanvas(shell) {
    const windowEl = shell.querySelector('.observatory-window');
    if (!windowEl || windowEl.querySelector('.national-ambient-canvas')) return;

    const canvas = document.createElement('canvas');
    canvas.className = 'national-ambient-canvas';
    canvas.setAttribute('aria-hidden', 'true');
    windowEl.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    const particles = [];
    let width = 0;
    let height = 0;
    let dpr = 1;
    let raf = null;

    function resize() {
      const rect = windowEl.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = Math.max(1, rect.width);
      height = Math.max(1, rect.height);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      canvas.style.width = width + 'px';
      canvas.style.height = height + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      if (!particles.length) {
        for (let i = 0; i < 22; i += 1) {
          particles.push({
            x: Math.random() * width,
            y: 90 + Math.random() * Math.max(100, height - 300),
            vx: 0.025 + Math.random() * 0.055,
            vy: -0.008 + Math.random() * 0.016,
            r: 0.35 + Math.random() * 0.7,
            a: 0.025 + Math.random() * 0.045,
            phase: Math.random() * Math.PI * 2
          });
        }
      }
    }

    function frame(time) {
      ctx.clearRect(0, 0, width, height);
      particles.forEach(function (p) {
        p.x += p.vx;
        p.y += p.vy + Math.sin(time * 0.00018 + p.phase) * 0.006;
        if (p.x > width + 8) p.x = -8;
        if (p.y < 70) p.y = height - 230;
        if (p.y > height - 180) p.y = 90;

        const alpha = p.a * (0.72 + Math.sin(time * 0.00035 + p.phase) * 0.28);
        ctx.beginPath();
        ctx.fillStyle = 'rgba(210,226,216,' + Math.max(0.008, alpha) + ')';
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fill();
      });
      raf = requestAnimationFrame(frame);
    }

    resize();
    window.addEventListener('resize', resize, { passive: true });
    raf = requestAnimationFrame(frame);

    document.addEventListener('visibilitychange', function () {
      if (document.hidden && raf) {
        cancelAnimationFrame(raf);
        raf = null;
      } else if (!document.hidden && !raf) {
        raf = requestAnimationFrame(frame);
      }
    });
  }

  function initNationalScenarios(map) {
    const shell = document.getElementById('main-content');
    if (!shell || !map || shell.dataset.nationalView !== 'true') return;

    let scenarios = [];
    let curatedSites = [];
    try {
      scenarios = JSON.parse(shell.dataset.scenarios || '[]');
      curatedSites = JSON.parse(shell.dataset.curatedSites || '[]');
    } catch (error) {
      console.error('Could not parse national scenarios', error);
      return;
    }

    document.body.classList.add('living-constellation-ready');
    createAmbientCanvas(shell);

    const activeLayer = L.layerGroup().addTo(map);
    const plannedLayer = L.layerGroup().addTo(map);
    const whisperLayer = L.layerGroup().addTo(map);
    const focusLayer = L.layerGroup().addTo(map);
    const siteFoundationLayer = L.layerGroup().addTo(map);

    curatedSites.forEach(function(site){
      const marker=L.marker([Number(site.latitude),Number(site.longitude)],{icon:siteIcon(site),keyboard:true,title:site.name,riseOnHover:true}).addTo(siteFoundationLayer);
      marker.bindTooltip('<strong>'+site.name+'</strong><span>'+site.context+'</span><span>Demonstration context · not incident verification</span>',{direction:'top',offset:[0,-9],opacity:.97,className:'national-scenario-tooltip living-tooltip site-foundation-tooltip'});
      marker.on('click',function(){ window.location.href='/?scenario='+encodeURIComponent(site.scenario_id)+'&material='+encodeURIComponent(site.material_profile_id)+'&site='+encodeURIComponent(site.id)+'&arrival=cinematic'; });
    });

    PLANNED_NODES.forEach(function (node) {
      const marker = L.marker(
        [node.latitude, node.longitude],
        {
          icon: plannedIcon(),
          keyboard: false,
          title: node.name + ' - planned',
          riseOnHover: false
        }
      ).addTo(plannedLayer);

      marker.bindTooltip(
        '<strong>' + node.name + '</strong><em>Planned scenario</em>',
        {
          direction: 'top',
          offset: [0, -7],
          opacity: 0.94,
          className: 'national-planned-tooltip'
        }
      );
    });

    scenarios.forEach(function (scenario) {
      const lat = Number(scenario.latitude);
      const lon = Number(scenario.longitude);
      const windTo = (Number(scenario.wind_from_deg || 0) + 180) % 360;
      const whisperEnd = destination(lat, lon, windTo, 185);

      L.polyline(
        [[lat, lon], whisperEnd],
        {
          pane: 'overlayPane',
          interactive: false,
          className: 'node-air-whisper whisper-' + scenario.id,
          opacity: 0.16,
          weight: 1.25,
          dashArray: '1 9',
          lineCap: 'round'
        }
      ).addTo(whisperLayer);

      const marker = L.marker(
        [lat, lon],
        {
          icon: scenarioIcon(scenario, false),
          keyboard: true,
          title: scenario.name,
          riseOnHover: true
        }
      ).addTo(activeLayer);

      marker.bindTooltip(
        '<strong>' + scenario.name + '</strong>' +
        '<span>' + scenario.source_label + '</span>' +
        '<span>' + cardinal(scenario.wind_from_deg) + ' wind - ' + mph(scenario.wind_speed_mps) + ' mph</span>' +
        '<span>Terrain response active</span>',
        {
          direction: 'top',
          offset: [0, -13],
          opacity: 0.98,
          className: 'national-scenario-tooltip living-tooltip'
        }
      );

      marker.on('mouseover', function () {
        focusLayer.clearLayers();
        L.circle([lat, lon], {
          radius: 105000,
          interactive: false,
          className: 'terrain-focus-ring',
          color: '#d7b06c',
          weight: 1,
          opacity: 0.26,
          fillColor: '#b7d4c7',
          fillOpacity: 0.035
        }).addTo(focusLayer);
        document.body.classList.add('node-hover-active');
      });

      marker.on('mouseout', function () {
        focusLayer.clearLayers();
        document.body.classList.remove('node-hover-active');
      });

      marker.on('click', function () {
        if (document.body.classList.contains('national-fly-active')) return;

        marker.setIcon(scenarioIcon(scenario, true));
        document.body.classList.add('national-fly-active');
        shell.setAttribute('data-fly-target', scenario.id);

        const targetZoom = Math.max(7.6, Math.min(8.8, map.getZoom() + 4.2));
        map.flyTo([lat, lon], targetZoom, {
          duration: 1.55,
          easeLinearity: 0.18,
          noMoveStart: false
        });

        window.setTimeout(function () {
          window.location.href = '/?scenario=' + encodeURIComponent(scenario.id) + '&arrival=cinematic';
        }, 1380);
      });
    });

    map.fitBounds(LOWER_48_BOUNDS, {
      paddingTopLeft: [34, 90],
      paddingBottomRight: [34, 214],
      animate: false
    });

    window.setTimeout(function () {
      map.invalidateSize();
    }, 120);
  }

  window.addEventListener('aw:map-ready', function (event) {
    const map = event.detail && event.detail.map;
    if (map) {
      window.setTimeout(function () {
        initNationalScenarios(map);
      }, 100);
    }
  });
})();