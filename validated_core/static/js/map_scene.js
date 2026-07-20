(function () {
  function setFallback(message) {
    document.body.classList.add('map-fallback-active');
    const fallback = document.getElementById('mapFallback');
    if (fallback && message) {
      fallback.querySelector('span').textContent = message;
    }
  }

  function labelIcon(html, className) {
    return L.divIcon({
      html,
      className: 'aw-map-label ' + (className || ''),
      iconSize: null,
    });
  }

  function latLngFrom(obj) {
    return [obj.lat, obj.lon];
  }

  function markSciencePane(map, paneName) {
    const pane = map.getPane(paneName);
    if (pane) pane.classList.add('aw-science-raster-pane');
  }

  function applySciencePaneVisibility(map, level) {
    if (!map) return;
    const essence = level === 'overview';
    map.getContainer().querySelectorAll('.aw-science-raster-pane').forEach(function (pane) {
      pane.style.display = essence ? 'none' : '';
      pane.setAttribute('aria-hidden', essence ? 'true' : 'false');
    });
  }

  function initMapSurface() {
    const mapEl = document.getElementById('mapLayer');
    if (!mapEl) return;
    const config = JSON.parse(mapEl.dataset.map || '{}');

    if (!window.L) {
      setFallback('Leaflet did not load. The scene is still valid as a fallback visual surface.');
      window.dispatchEvent(new CustomEvent('aw:map-unavailable'));
      return;
    }

    try {
      const center = config.center || { lat: 34.26, lon: -119.03 };
      const modes = config.basemap_modes || [];
      const defaultModeId = config.default_mode || 'standard';
      const defaultMode = modes.find(m => m.id === defaultModeId) || modes[0] || {};

      const map = L.map(mapEl, {
        zoomControl: true,
        attributionControl: false,
        dragging: true,
        scrollWheelZoom: true,
        doubleClickZoom: true,
        boxZoom: true,
        keyboard: true,
        tap: true,
        touchZoom: true,
      }).setView([center.lat, center.lon], config.zoom || 11);

      mapEl.__awMap = map;
      window.__AW_MAP__ = map;
      window.addEventListener('aw:disclosure-level', function (event) {
        applySciencePaneVisibility(map, (event.detail || {}).level || 'overview');
      });

      let activeTile = null;
      function applyMode(modeId) {
        const selected = modes.find(m => m.id === modeId) || defaultMode;
        if (activeTile) map.removeLayer(activeTile);
        let tileErrors = 0;
        activeTile = L.tileLayer(selected.tile_url || config.tile_url, {
          maxZoom: 18,
          attribution: selected.attribution || config.attribution || 'Map data © OpenStreetMap contributors',
          className: 'aw-osm-tile aw-tile-' + (selected.id || 'standard'),
        });
        activeTile.on('tileerror', function () {
          tileErrors += 1;
          if (tileErrors > 3) {
            setFallback('Map tiles failed to load. Showing the local fallback surface and preserving attribution/boundaries.');
          }
        });
        activeTile.on('load', function () {
          document.body.classList.add('map-loaded');
        });
        activeTile.addTo(map);
        document.querySelectorAll('[data-basemap-mode]').forEach(btn => {
          btn.classList.toggle('active', btn.dataset.basemapMode === (selected.id || modeId));
        });
        const attribution = document.querySelector('.map-attribution');
        if (attribution) {
          attribution.textContent = (selected.attribution || config.attribution || 'Map data © OpenStreetMap contributors') + ' · geographic context only · not methane evidence';
        }
      }
      applyMode(defaultModeId);

      document.querySelectorAll('[data-basemap-mode]').forEach(btn => {
        btn.addEventListener('click', () => applyMode(btn.dataset.basemapMode));
      });

      const hillshade = config.hillshade || {};
      if (hillshade.data_state === 'dem_derived_hillshade_cache' && hillshade.source_dem_bbox) {
        map.createPane('awHillshadePane');
        map.getPane('awHillshadePane').style.zIndex = 245;
        map.getPane('awHillshadePane').style.pointerEvents = 'none'; markSciencePane(map, 'awHillshadePane');
        const b = hillshade.source_dem_bbox;
        const imageUrl = (hillshade.image_url || '/hillshade-image') + '?sha=' + encodeURIComponent(hillshade.image_sha256 || 'current');
        L.imageOverlay(imageUrl, [[b[1], b[0]], [b[3], b[2]]], {
          pane: 'awHillshadePane', opacity: 0.42, interactive: false,
          className: 'aw-dem-hillshade aw-science-surface'
        }).addTo(map);
        const sceneWindow = document.getElementById('sceneWindow');
        if (sceneWindow) sceneWindow.classList.add('hillshade-active');
      }

      const steeringField = config.terrain_steering_field || {};
      if (steeringField.data_state === 'terrain_steering_field_cache' && steeringField.source_dem_bbox) {
        map.createPane('awSteeringPane');
        map.getPane('awSteeringPane').style.zIndex = 252;
        map.getPane('awSteeringPane').style.pointerEvents = 'none'; markSciencePane(map, 'awSteeringPane');
        const sb = steeringField.source_dem_bbox;
        const steeringUrl = (steeringField.image_url || '/terrain-steering-field-image') + '?sha=' + encodeURIComponent(steeringField.image_sha256 || 'current');
        L.imageOverlay(steeringUrl, [[sb[1], sb[0]], [sb[3], sb[2]]], {
          pane: 'awSteeringPane', opacity: 0.52, interactive: false,
          className: 'aw-terrain-steering-field'
        }).addTo(map);
        const sceneWindow = document.getElementById('sceneWindow');
        if (sceneWindow) sceneWindow.classList.add('steering-field-active');
      }
      const steeringConfidence = config.terrain_steering_confidence || {};
      if (steeringConfidence.data_state === 'terrain_steering_confidence_cache' && steeringConfidence.source_bbox) {
        map.createPane('awSteeringConfidencePane');
        map.getPane('awSteeringConfidencePane').style.zIndex = 253;
        map.getPane('awSteeringConfidencePane').style.pointerEvents = 'none'; markSciencePane(map, 'awSteeringConfidencePane');
        const cb = steeringConfidence.source_bbox;
        const confidenceUrl = (steeringConfidence.confidence_image_url || '/terrain-steering-confidence-image') + '?sha=' + encodeURIComponent(steeringConfidence.confidence_image_sha256 || 'current');
        L.imageOverlay(confidenceUrl, [[cb[1], cb[0]], [cb[3], cb[2]]], {pane:'awSteeringConfidencePane', opacity:0.24, interactive:false, className:'aw-steering-confidence'}).addTo(map);
        if (sceneWindow) sceneWindow.classList.add('steering-confidence-active');
      }

      const ridgeLee = config.ridge_spillover_shelter || {};
      if (ridgeLee.data_state === 'ridge_spillover_shelter_cache' && ridgeLee.source_bbox) {
        const rb = ridgeLee.source_bbox;
        map.createPane('awLeeShelterPane');
        map.getPane('awLeeShelterPane').style.zIndex = 254;
        map.getPane('awLeeShelterPane').style.pointerEvents = 'none'; markSciencePane(map, 'awLeeShelterPane');
        const shelterUrl = (ridgeLee.shelter_image_url || '/lee-side-shelter-image') + '?sha=' + encodeURIComponent(ridgeLee.shelter_image_sha256 || 'current');
        L.imageOverlay(shelterUrl, [[rb[1], rb[0]], [rb[3], rb[2]]], {pane:'awLeeShelterPane', opacity:0.28, interactive:false, className:'aw-lee-side-shelter'}).addTo(map);
        map.createPane('awRidgeSpilloverPane');
        map.getPane('awRidgeSpilloverPane').style.zIndex = 255;
        map.getPane('awRidgeSpilloverPane').style.pointerEvents = 'none'; markSciencePane(map, 'awRidgeSpilloverPane');
        const spillUrl = (ridgeLee.spillover_image_url || '/ridge-spillover-image') + '?sha=' + encodeURIComponent(ridgeLee.spillover_image_sha256 || 'current');
        L.imageOverlay(spillUrl, [[rb[1], rb[0]], [rb[3], rb[2]]], {pane:'awRidgeSpilloverPane', opacity:0.34, interactive:false, className:'aw-ridge-spillover'}).addTo(map);
        const sceneWindow = document.getElementById('sceneWindow');
        if (sceneWindow) sceneWindow.classList.add('ridge-lee-active');
      }

      const canyon = config.canyon_channeling || {};
      if (canyon.data_state === 'canyon_channeling_drainage_cache' && canyon.source_bbox) {
        const cb = canyon.source_bbox;
        map.createPane('awDrainagePane'); map.getPane('awDrainagePane').style.zIndex=256; map.getPane('awDrainagePane').style.pointerEvents='none'; markSciencePane(map, 'awDrainagePane');
        L.imageOverlay((canyon.drainage_image_url||'/drainage-alignment-image')+'?sha='+encodeURIComponent(canyon.drainage_image_sha256||'current'), [[cb[1],cb[0]],[cb[3],cb[2]]], {pane:'awDrainagePane',opacity:0.24,interactive:false,className:'aw-drainage-alignment'}).addTo(map);
        map.createPane('awCanyonPane'); map.getPane('awCanyonPane').style.zIndex=257; map.getPane('awCanyonPane').style.pointerEvents='none'; markSciencePane(map, 'awCanyonPane');
        L.imageOverlay((canyon.channel_image_url||'/canyon-channeling-image')+'?sha='+encodeURIComponent(canyon.channel_image_sha256||'current'), [[cb[1],cb[0]],[cb[3],cb[2]]], {pane:'awCanyonPane',opacity:0.28,interactive:false,className:'aw-canyon-channeling'}).addTo(map);
      }
      const saddleGap = config.saddle_gap_acceleration || {};
      if (saddleGap.data_state === 'saddle_transfer_gap_cache' && saddleGap.source_bbox) {
        const sb = saddleGap.source_bbox;
        map.createPane('awSaddlePane'); map.getPane('awSaddlePane').style.zIndex=258; map.getPane('awSaddlePane').style.pointerEvents='none'; markSciencePane(map, 'awSaddlePane');
        L.imageOverlay((saddleGap.saddle_image_url||'/saddle-transfer-image')+'?sha='+encodeURIComponent(saddleGap.saddle_image_sha256||'current'), [[sb[1],sb[0]],[sb[3],sb[2]]], {pane:'awSaddlePane',opacity:0.25,interactive:false,className:'aw-saddle-transfer'}).addTo(map);
        map.createPane('awGapPane'); map.getPane('awGapPane').style.zIndex=259; map.getPane('awGapPane').style.pointerEvents='none'; markSciencePane(map, 'awGapPane');
        L.imageOverlay((saddleGap.gap_image_url||'/gap-acceleration-image')+'?sha='+encodeURIComponent(saddleGap.gap_image_sha256||'current'), [[sb[1],sb[0]],[sb[3],sb[2]]], {pane:'awGapPane',opacity:0.27,interactive:false,className:'aw-gap-acceleration'}).addTo(map);
      }


      const terrainConvergence = config.terrain_convergence_accumulation || {};
      if (terrainConvergence.data_state === 'terrain_convergence_accumulation_cache' && terrainConvergence.source_bbox) {
        const tb = terrainConvergence.source_bbox;
        map.createPane('awTerrainConvergencePane'); map.getPane('awTerrainConvergencePane').style.zIndex=250; map.getPane('awTerrainConvergencePane').style.pointerEvents='none'; markSciencePane(map, 'awTerrainConvergencePane');
        L.imageOverlay((terrainConvergence.convergence_image_url||'/terrain-convergence-image')+'?sha='+encodeURIComponent(terrainConvergence.convergence_image_sha256||'current'), [[tb[1],tb[0]],[tb[3],tb[2]]], {pane:'awTerrainConvergencePane',opacity:0.23,interactive:false,className:'aw-terrain-convergence'}).addTo(map);
        map.createPane('awFocusedAccumulationPane'); map.getPane('awFocusedAccumulationPane').style.zIndex=251; map.getPane('awFocusedAccumulationPane').style.pointerEvents='none'; markSciencePane(map, 'awFocusedAccumulationPane');
        L.imageOverlay((terrainConvergence.accumulation_image_url||'/terrain-focused-accumulation-image')+'?sha='+encodeURIComponent(terrainConvergence.accumulation_image_sha256||'current'), [[tb[1],tb[0]],[tb[3],tb[2]]], {pane:'awFocusedAccumulationPane',opacity:0.18,interactive:false,className:'aw-focused-accumulation'}).addTo(map);
      }



      const terrainTransitions = config.terrain_transition_regimes || {};
      if (terrainTransitions.data_state === 'terrain_transition_regimes_cache' && terrainTransitions.source_bbox) {
        const xb=terrainTransitions.source_bbox;
        map.createPane('awTerrainTransitionPane'); map.getPane('awTerrainTransitionPane').style.zIndex=246; map.getPane('awTerrainTransitionPane').style.pointerEvents='none'; markSciencePane(map, 'awTerrainTransitionPane');
        L.imageOverlay((terrainTransitions.transition_image_url||'/terrain-transition-image')+'?sha='+encodeURIComponent(terrainTransitions.transition_image_sha256||'current'), [[xb[1],xb[0]],[xb[3],xb[2]]], {pane:'awTerrainTransitionPane',opacity:0.18,interactive:false}).addTo(map);
        map.createPane('awFlowRegimeBoundaryPane'); map.getPane('awFlowRegimeBoundaryPane').style.zIndex=247; map.getPane('awFlowRegimeBoundaryPane').style.pointerEvents='none'; markSciencePane(map, 'awFlowRegimeBoundaryPane');
        L.imageOverlay((terrainTransitions.boundary_image_url||'/flow-regime-boundary-image')+'?sha='+encodeURIComponent(terrainTransitions.boundary_image_sha256||'current'), [[xb[1],xb[0]],[xb[3],xb[2]]], {pane:'awFlowRegimeBoundaryPane',opacity:0.22,interactive:false}).addTo(map);
      }

      const integrated = config.integrated_terrain_response || {};
      if (integrated.data_state === 'integrated_terrain_response_cache' && integrated.source_bbox) {
        if (!map.getPane('awIntegratedResponsePane')) { map.createPane('awIntegratedResponsePane'); markSciencePane(map, 'awIntegratedResponsePane'); map.getPane('awIntegratedResponsePane').style.zIndex = 347; }
        const ib=integrated.source_bbox;
        L.imageOverlay((integrated.field_image_url||'/integrated-terrain-response-image')+'?sha='+encodeURIComponent(integrated.field_image_sha256||'current'), [[ib[1],ib[0]],[ib[3],ib[2]]], {pane:'awIntegratedResponsePane',opacity:Math.min(0.24,Number((integrated.visual_directives||{}).field_opacity||0.16)),interactive:false}).addTo(map);
      }
      const regimeConfidence = config.terrain_regime_confidence || {};
      if (regimeConfidence.data_state === 'terrain_regime_confidence_cache' && regimeConfidence.source_bbox) {
        const rb=regimeConfidence.source_bbox;
        map.createPane('awRegimeConfidencePane'); map.getPane('awRegimeConfidencePane').style.zIndex=244; map.getPane('awRegimeConfidencePane').style.pointerEvents='none'; markSciencePane(map, 'awRegimeConfidencePane');
        L.imageOverlay((regimeConfidence.confidence_image_url||'/terrain-regime-confidence-image')+'?sha='+encodeURIComponent(regimeConfidence.confidence_image_sha256||'current'), [[rb[1],rb[0]],[rb[3],rb[2]]], {pane:'awRegimeConfidencePane',opacity:0.16,interactive:false}).addTo(map);
        map.createPane('awBoundaryAmbiguityPane'); map.getPane('awBoundaryAmbiguityPane').style.zIndex=245; map.getPane('awBoundaryAmbiguityPane').style.pointerEvents='none'; markSciencePane(map, 'awBoundaryAmbiguityPane');
        L.imageOverlay((regimeConfidence.ambiguity_image_url||'/terrain-boundary-ambiguity-image')+'?sha='+encodeURIComponent(regimeConfidence.ambiguity_image_sha256||'current'), [[rb[1],rb[0]],[rb[3],rb[2]]], {pane:'awBoundaryAmbiguityPane',opacity:0.15,interactive:false}).addTo(map);
      }

      const terrainDivergence = config.terrain_divergence_dispersion || {};
      if (terrainDivergence.data_state === 'terrain_divergence_dispersion_cache' && terrainDivergence.source_bbox) {
        const db = terrainDivergence.source_bbox;
        map.createPane('awTerrainDivergencePane'); map.getPane('awTerrainDivergencePane').style.zIndex=248; map.getPane('awTerrainDivergencePane').style.pointerEvents='none'; markSciencePane(map, 'awTerrainDivergencePane');
        L.imageOverlay((terrainDivergence.divergence_image_url||'/terrain-divergence-image')+'?sha='+encodeURIComponent(terrainDivergence.divergence_image_sha256||'current'), [[db[1],db[0]],[db[3],db[2]]], {pane:'awTerrainDivergencePane',opacity:0.20,interactive:false}).addTo(map);
        map.createPane('awTerrainDispersionPane'); map.getPane('awTerrainDispersionPane').style.zIndex=249; map.getPane('awTerrainDispersionPane').style.pointerEvents='none'; markSciencePane(map, 'awTerrainDispersionPane');
        L.imageOverlay((terrainDivergence.dispersion_image_url||'/terrain-dispersion-image')+'?sha='+encodeURIComponent(terrainDivergence.dispersion_image_sha256||'current'), [[db[1],db[0]],[db[3],db[2]]], {pane:'awTerrainDispersionPane',opacity:0.16,interactive:false}).addTo(map);
      }

      const basinRetention = config.basin_retention_cold_air_pooling || {};
      if (basinRetention.data_state === 'basin_retention_cold_air_pooling_cache' && basinRetention.source_bbox) {
        const bb = basinRetention.source_bbox;
        map.createPane('awBasinRetentionPane'); map.getPane('awBasinRetentionPane').style.zIndex=252; map.getPane('awBasinRetentionPane').style.pointerEvents='none'; markSciencePane(map, 'awBasinRetentionPane');
        L.imageOverlay((basinRetention.basin_image_url||'/basin-retention-image')+'?sha='+encodeURIComponent(basinRetention.basin_image_sha256||'current'), [[bb[1],bb[0]],[bb[3],bb[2]]], {pane:'awBasinRetentionPane',opacity:0.22,interactive:false,className:'aw-basin-retention'}).addTo(map);
        map.createPane('awColdPoolingPane'); map.getPane('awColdPoolingPane').style.zIndex=253; map.getPane('awColdPoolingPane').style.pointerEvents='none'; markSciencePane(map, 'awColdPoolingPane');
        L.imageOverlay((basinRetention.cold_pooling_image_url||'/cold-air-pooling-image')+'?sha='+encodeURIComponent(basinRetention.cold_pooling_image_sha256||'current'), [[bb[1],bb[0]],[bb[3],bb[2]]], {pane:'awColdPoolingPane',opacity:0.20,interactive:false,className:'aw-cold-air-pooling'}).addTo(map);
      }

      const terrainLighting = config.terrain_lighting || {};
      const lightingGroup = L.layerGroup().addTo(map);
      if (terrainLighting.data_state === 'measured_terrain_lighting_applied') {
        map.createPane('awReliefPane');
        map.getPane('awReliefPane').style.zIndex = 260;
        map.getPane('awReliefPane').classList.add('aw-relief-pane'); markSciencePane(map, 'awReliefPane');
        (terrainLighting.cells || []).forEach(function (cell) {
          const shade = Number(cell.shade || 0);
          const relief = Number(cell.relief_intensity || 0);
          const isLit = shade >= 0;
          const fill = isLit ? '#d9f2df' : '#07151c';
          const opacity = Math.min(0.28, 0.055 + Math.abs(shade) * 0.13 + relief * 0.08);
          L.polygon((cell.polygon || []).map(latLngFrom), {
            pane: 'awReliefPane', color: fill, weight: 0.35, opacity: 0.12,
            fillColor: fill, fillOpacity: opacity, interactive: false,
            className: 'aw-relief-cell'
          }).addTo(lightingGroup);
        });
        (terrainLighting.contours || []).forEach(function (segment) {
          L.polyline((segment.points || []).map(latLngFrom), {
            pane: 'awReliefPane', color: '#d5ead8', weight: 0.8,
            opacity: segment.level_index === 2 ? 0.42 : 0.26,
            dashArray: segment.level_index === 2 ? null : '3 5',
            interactive: false, className: 'aw-contour-line'
          }).addTo(lightingGroup);
        });
        const sceneWindow = document.getElementById('sceneWindow');
        if (sceneWindow) sceneWindow.classList.add('relief-active');
      }

      const plume = config.plume_geometry || {};
      const source = plume.source || config.source_seed_point;
      const downwind = plume.downwind_end || config.downwind_context_point;
      const uncertainty = plume.uncertainty_polygon || [];
      const centerline = plume.centerline || (source && downwind ? [source, downwind] : []);

      const overlayGroup = L.layerGroup().addTo(map);

      if (uncertainty.length) {
        L.polygon(uncertainty.map(latLngFrom), {
          color: '#75f6e2',
          weight: 1,
          opacity: 0.42,
          fillColor: '#75f6e2',
          fillOpacity: 0.035,
          dashArray: '7 10',
          interactive: false,
          className: 'aw-uncertainty-envelope',
        }).addTo(overlayGroup);
      }

      if (centerline.length >= 2) {
        L.polyline(centerline.map(latLngFrom), {
          color: '#d9fbff',
          weight: 1.5,
          opacity: 0.62,
          interactive: false,
          className: 'aw-flow-centerline',
        }).addTo(overlayGroup);
        const mid = centerline[Math.floor(centerline.length / 2)];
        L.marker(latLngFrom(mid), {
          icon: labelIcon('<b>TERRAIN FLOW PATH</b><span>measured-land visual heuristic</span>', 'aw-label-wind'),
          interactive: false,
        }).addTo(overlayGroup);
      }

      if (source) {
        L.circleMarker(latLngFrom(source), {
          radius: 6,
          color: '#ffbf59',
          fillColor: '#ffbf59',
          fillOpacity: 0.92,
          weight: 1.5,
          opacity: 0.95,
          className: 'aw-source-marker aw-essence-source',
        }).addTo(overlayGroup);
        L.circle(latLngFrom(source), {
          radius: 1800,
          color: '#ffbf59',
          opacity: 0.32,
          fillOpacity: 0.04,
          dashArray: '5 7',
          className: 'aw-source-radius',
        }).addTo(overlayGroup);
        L.marker(latLngFrom(source), {
          icon: labelIcon('<b>REPORTED SIGNAL</b><span>source seed · not detection</span>', 'aw-label-source'),
          interactive: false,
        }).addTo(overlayGroup);
      }

      // PASS 18 - Frame the terrain-shaped sentence.
      // Sampled camera experiments showed that cropping the registered corridor made the
      // source readable but pushed the atmospheric response out of frame. Fit the complete
      // source-to-uncertainty geometry, then use asymmetric breathing room so the source sits
      // near the lower-left third and the terrain response has room to unfold.
      if (source && centerline.length >= 2) {
        const compositionPoints = [latLngFrom(source)].concat(centerline.map(latLngFrom));
        const compositionBounds = L.latLngBounds(compositionPoints);
        setTimeout(function () {
          if (!mapEl.dataset.userMoved) {
            map.fitBounds(compositionBounds, {
              paddingTopLeft: [150, 110],
              paddingBottomRight: [230, 150],
              maxZoom: 10.65,
              animate: false
            });
          }
        }, 320);
      }

      map.once('dragstart zoomstart', function () { mapEl.dataset.userMoved = 'true'; });

      if (downwind) {
        L.circleMarker(latLngFrom(downwind), {
          radius: 5,
          color: '#75f6e2',
          fillColor: '#75f6e2',
          fillOpacity: 0.48,
          weight: 1.2,
          opacity: 0.75,
          className: 'aw-context-marker aw-downwind-context',
        }).addTo(overlayGroup);
        L.marker(latLngFrom(downwind), {
          icon: labelIcon('<b>DOWNWIND</b><span>orientation only</span>', 'aw-label-context'),
          interactive: false,
        }).addTo(overlayGroup);
      }

      map.on('move zoom resize', function () {
        window.dispatchEvent(new CustomEvent('aw:map-change'));
      });

      setTimeout(function () {
        map.invalidateSize();
        applySciencePaneVisibility(map, document.body.classList.contains('disclosure-overview') ? 'overview' : (document.body.classList.contains('disclosure-audit') ? 'audit' : 'context'));
      requestAnimationFrame(function () {
        applySciencePaneVisibility(map, document.body.classList.contains('disclosure-overview') ? 'overview' : (document.body.classList.contains('disclosure-audit') ? 'audit' : 'context'));
      });
      window.dispatchEvent(new CustomEvent('aw:map-ready', { detail: { map } }));
      }, 250);
    } catch (err) {
      setFallback('Map shell could not initialize. The local fallback still shows the review surface.');
      console.error('[Atmosphere Window] map init failed:', err);
      window.dispatchEvent(new CustomEvent('aw:map-unavailable'));
    }
  }

  window.addEventListener('DOMContentLoaded', initMapSurface);
})();


(function(){
  function installScientificCamera(){
    const map=window.__AW_MAP__; const el=document.getElementById('mapLayer');
    if(!map||!el||el.__awScientificCameraInstalled) return;
    const cfg=JSON.parse(el.dataset.map||'{}').scientific_cinematic_camera||{};
    if(cfg.data_state!=='scientific_cinematic_camera_ready') return;
    el.__awScientificCameraInstalled=true;
    if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    let cancelled=false; const cancel=()=>{cancelled=true;};
    ['dragstart','zoomstart','mousedown','touchstart','wheel','keydown'].forEach(e=>map.on(e,cancel));
    const frames=cfg.keyframes||[]; const baseZoom=map.getZoom();
    let delay=900;
    frames.slice(1).forEach(frame=>{ delay+=Number(frame.duration_ms||1600); setTimeout(()=>{if(cancelled)return; map.flyTo([frame.lat,frame.lon],baseZoom+Number(frame.zoom_delta||0),{animate:true,duration:Math.max(.6,Number(frame.duration_ms||1600)/1000)});},delay); });
  }
  window.addEventListener('load',()=>setTimeout(installScientificCamera,700));
  window.addEventListener('aw:map-ready',()=>setTimeout(installScientificCamera,500));
})();


(function(){
  function installEvidenceFocusDepth(){
    const el=document.getElementById('mapLayer'); if(!el||el.__awFocusDepthInstalled) return;
    const cfg=(JSON.parse(el.dataset.map||'{}').evidence_guided_focus_depth)||{};
    if(cfg.data_state!=='evidence_guided_focus_depth_ready') return;
    el.__awFocusDepthInstalled=true;
    const v=cfg.visual_directives||{};
    const overlay=document.createElement('div'); overlay.className='aw-evidence-focus-depth';
    overlay.style.setProperty('--aw-focus-vignette',String(v.vignette_opacity||0));
    overlay.style.setProperty('--aw-focus-edge',String(v.edge_fade||0));
    overlay.dataset.focusTarget=cfg.focus_target||'stable_review_frame';
    overlay.setAttribute('aria-hidden','true'); el.appendChild(overlay);
    el.classList.add('aw-focus-depth-active');
    el.style.setProperty('--aw-terrain-contrast',String(v.terrain_contrast||1));
    el.style.setProperty('--aw-air-emphasis',String(v.air_volume_emphasis||1));
    const cancel=()=>{overlay.style.opacity='0';el.classList.remove('aw-focus-depth-active');};
    ['pointerdown','wheel','keydown','touchstart'].forEach(name=>window.addEventListener(name,cancel,{once:true,passive:true}));
  }
  window.addEventListener('load',()=>setTimeout(installEvidenceFocusDepth,900));
  window.addEventListener('aw:map-ready',()=>setTimeout(installEvidenceFocusDepth,700));
})();


(function(){
  function installAtmosphericLightLegibility(){
    const el=document.getElementById('mapLayer'); if(!el||el.__awAtmosphericLightInstalled) return;
    const cfg=(JSON.parse(el.dataset.map||'{}').atmospheric_light_legibility)||{};
    if(cfg.data_state!=='atmospheric_light_legibility_ready') return;
    el.__awAtmosphericLightInstalled=true;
    const v=cfg.visual_directives||{};
    el.classList.add('aw-atmospheric-light-active');
    el.style.setProperty('--aw-terrain-shadow',String(v.terrain_shadow||0));
    el.style.setProperty('--aw-terrain-highlight',String(v.terrain_highlight||0));
    el.style.setProperty('--aw-air-glow',String(v.air_glow||0));
    el.style.setProperty('--aw-edge-separation',String(v.edge_separation||0));
    el.style.setProperty('--aw-confidence-light',String(v.confidence_illumination||0));
    el.style.setProperty('--aw-uncertainty-luminance',String(v.uncertainty_luminance||1));
    el.style.setProperty('--aw-light-radius',String(v.max_glow_radius_px||8)+'px');
    const veil=document.createElement('div'); veil.className='aw-atmospheric-light-veil'; veil.dataset.lightingMode=cfg.lighting_mode||'balanced_review_light'; veil.setAttribute('aria-hidden','true'); el.appendChild(veil);
    const cancel=()=>{veil.style.opacity='0';el.classList.remove('aw-atmospheric-light-active');};
    ['pointerdown','wheel','keydown','touchstart'].forEach(name=>window.addEventListener(name,cancel,{once:true,passive:true}));
  }
  window.addEventListener('load',()=>setTimeout(installAtmosphericLightLegibility,1050));
  window.addEventListener('aw:map-ready',()=>setTimeout(installAtmosphericLightLegibility,850));
})();


(function(){
  function installEvidenceVisualHierarchy(){
    const el=document.getElementById('mapLayer'); if(!el||el.__awEvidenceHierarchyInstalled) return;
    const cfg=(JSON.parse(el.dataset.map||'{}').evidence_visual_hierarchy)||{};
    if(cfg.data_state!=='evidence_visual_hierarchy_ready') return;
    el.__awEvidenceHierarchyInstalled=true;
    const rules=cfg.contrast_rules||{};
    el.classList.add('aw-evidence-hierarchy-active');
    el.style.setProperty('--aw-evidence-saturation',String(rules.accent_saturation_cap||.62));
    el.style.setProperty('--aw-secondary-opacity',String(rules.secondary_layer_opacity_cap||.46));
    const veil=document.createElement('div'); veil.className='aw-evidence-hierarchy-veil'; veil.dataset.hierarchyMode=cfg.hierarchy_mode||'balanced_evidence_hierarchy'; veil.setAttribute('aria-hidden','true'); el.appendChild(veil);
    const cancel=()=>{veil.style.opacity='0';};
    ['pointerdown','wheel','keydown','touchstart'].forEach(name=>window.addEventListener(name,cancel,{once:true,passive:true}));
  }
  window.addEventListener('load',()=>setTimeout(installEvidenceVisualHierarchy,1200));
  window.addEventListener('aw:map-ready',()=>setTimeout(installEvidenceVisualHierarchy,950));
})();


(function(){
  function installScientificAnnotations(){
    const el=document.getElementById('mapLayer'); if(!el||el.__awAnnotationsInstalled) return;
    const cfg=(JSON.parse(el.dataset.map||'{}').scientific_annotation_choreography)||{};
    if(cfg.data_state!=='scientific_annotation_choreography_ready') return;
    el.__awAnnotationsInstalled=true;
    const tray=document.createElement('div'); tray.className='aw-scientific-annotations'; tray.setAttribute('aria-label','Scientific evidence annotations');
    (cfg.priority_labels||[]).slice(0,cfg.label_budget||6).forEach((label,i)=>{ const tag=document.createElement('span'); tag.className='aw-scientific-annotation'; tag.textContent=label; tag.dataset.annotationIndex=String(i); tag.style.animationDelay=String((cfg.timing?.entry_ms||700)+i*(cfg.timing?.stagger_ms||420))+'ms'; tray.appendChild(tag); });
    el.appendChild(tray);
    const cancel=()=>{tray.classList.add('aw-reviewer-controlled');};
    ['pointerdown','wheel','keydown','touchstart'].forEach(n=>window.addEventListener(n,cancel,{once:true,passive:true}));
  }
  window.addEventListener('load',()=>setTimeout(installScientificAnnotations,1250));
  window.addEventListener('aw:map-ready',()=>setTimeout(installScientificAnnotations,1000));
})();

(function(){
  function installScientificTimeline(){
    const el=document.getElementById('mapLayer'); if(!el||el.__awTimelineInstalled) return;
    const cfg=(JSON.parse(el.dataset.map||'{}').scientific_storytelling_timeline)||{};
    if(cfg.data_state!=='scientific_storytelling_timeline_ready') return;
    el.__awTimelineInstalled=true;
    if(window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const bar=document.createElement('div'); bar.className='aw-scientific-timeline'; const label=document.createElement('span'); const skip=document.createElement('button'); skip.type='button'; skip.textContent='Stable review'; skip.setAttribute('aria-label','Skip to stable review frame'); bar.append(label,skip); el.appendChild(bar);
    let stopped=false; const phases=cfg.phases||[];
    const stop=()=>{stopped=true; label.textContent='Stable review frame'; bar.classList.add('aw-timeline-complete');}; skip.addEventListener('click',stop);
    phases.forEach(ph=>setTimeout(()=>{if(!stopped){label.textContent=ph.label; bar.dataset.phase=ph.id;}},Number(ph.start_ms||0)));
    setTimeout(stop,Number(cfg.total_duration_ms||14400));
    ['pointerdown','wheel','keydown','touchstart'].forEach(n=>window.addEventListener(n,stop,{once:true,passive:true}));
  }
  window.addEventListener('load',()=>setTimeout(installScientificTimeline,1400));
  window.addEventListener('aw:map-ready',()=>setTimeout(installScientificTimeline,1150));
})();

(function(){
  function installReviewerEvidenceExplorer(){
    const el=document.getElementById('mapLayer');
    if(!el||el.__awReviewerExplorerInstalled) return;
    let mapCfg={};
    try{mapCfg=JSON.parse(el.dataset.map||'{}');}catch(_){return;}
    const cfg=mapCfg.reviewer_guided_exploration||{};
    if(cfg.data_state!=='reviewer_guided_exploration_ready') return;
    el.__awReviewerExplorerInstalled=true;

    const shell=document.createElement('section');
    shell.className='aw-evidence-explorer';
    shell.setAttribute('aria-label','Reviewer-guided evidence explorer');
    shell.innerHTML='<button type="button" class="aw-explorer-launch" aria-expanded="false">Explore evidence</button><div class="aw-explorer-panel" hidden><div class="aw-explorer-head"><div><b>Evidence explorer</b><span>Follow one scientific thread at a time.</span></div><button type="button" class="aw-explorer-close" aria-label="Close evidence explorer">×</button></div><div class="aw-explorer-breadcrumb"><button type="button" data-family="overview">Overview</button><span>›</span><strong>All evidence</strong></div><input class="aw-explorer-search" type="search" placeholder="Search terrain, wind, confidence…" aria-label="Search scientific evidence"><div class="aw-explorer-families"></div><div class="aw-explorer-results"></div><div class="aw-explorer-boundary"></div></div>';
    el.appendChild(shell);

    const launch=shell.querySelector('.aw-explorer-launch');
    const panel=shell.querySelector('.aw-explorer-panel');
    const close=shell.querySelector('.aw-explorer-close');
    const search=shell.querySelector('.aw-explorer-search');
    const familyBox=shell.querySelector('.aw-explorer-families');
    const results=shell.querySelector('.aw-explorer-results');
    const crumb=shell.querySelector('.aw-explorer-breadcrumb strong');
    const boundary=shell.querySelector('.aw-explorer-boundary');
    let activeFamily='overview';
    let query='';

    const families=cfg.families||[];
    const items=cfg.items||[];
    const links=cfg.links||[];
    const byId=Object.fromEntries(items.map(i=>[i.id,i]));

    function relatedIds(id){
      const out=new Set([id]);
      links.forEach(pair=>{if(pair[0]===id)out.add(pair[1]);if(pair[1]===id)out.add(pair[0]);});
      return out;
    }

    function applySceneFocus(item){
      el.classList.toggle('aw-review-focus-active',!!item);
      el.dataset.reviewFamily=item?item.family:'overview';
      document.querySelectorAll('.scene-status-strip span').forEach(span=>{
        if(!item){span.classList.remove('aw-review-match','aw-review-muted');return;}
        const hay=(span.textContent||'').toLowerCase();
        const terms=[item.title,item.family].concat(item.keywords||[]).map(v=>String(v).toLowerCase());
        const match=terms.some(t=>t&&hay.includes(t));
        span.classList.toggle('aw-review-match',match);
        span.classList.toggle('aw-review-muted',!match);
      });
      const annotations=el.querySelector('.aw-scientific-annotations');
      if(annotations) annotations.classList.toggle('aw-reviewer-controlled',!!item);
    }

    function openRoute(route){
      if(route) window.open(route,'_blank','noopener');
    }

    function render(){
      familyBox.innerHTML='';
      families.forEach(f=>{
        const b=document.createElement('button'); b.type='button'; b.textContent=f.label; b.dataset.family=f.id;
        b.classList.toggle('active',f.id===activeFamily); b.addEventListener('click',()=>{activeFamily=f.id;query='';search.value='';crumb.textContent=f.label;applySceneFocus(null);render();});
        familyBox.appendChild(b);
      });
      const q=query.trim().toLowerCase();
      const filtered=items.filter(item=>{
        const familyOk=activeFamily==='overview'||item.family===activeFamily;
        const hay=[item.title,item.summary,item.why,item.not_claimed,item.family].concat(item.keywords||[]).join(' ').toLowerCase();
        return familyOk&&(!q||hay.includes(q));
      });
      results.innerHTML='';
      if(!filtered.length){results.innerHTML='<p class="aw-explorer-empty">No matching evidence thread. Unavailable evidence has not been hidden.</p>';return;}
      filtered.forEach(item=>{
        const card=document.createElement('article'); card.className='aw-explorer-card'; card.dataset.item=item.id;
        card.innerHTML='<div class="aw-explorer-card-title"><b></b><span></span></div><p class="aw-explorer-summary"></p><details><summary>Why this is visible</summary><p class="aw-explorer-why"></p><p class="aw-explorer-not"></p><div class="aw-explorer-related"></div></details><div class="aw-explorer-actions"><button type="button" data-action="focus">Focus in scene</button><button type="button" data-action="route">Open deep review</button></div>';
        card.querySelector('b').textContent=item.title;
        card.querySelector('.aw-explorer-card-title span').textContent=String(item.state||'unknown').replaceAll('_',' ');
        card.querySelector('.aw-explorer-summary').textContent=item.summary;
        card.querySelector('.aw-explorer-why').textContent=item.why;
        card.querySelector('.aw-explorer-not').textContent='Not claimed: '+item.not_claimed;
        const rel=card.querySelector('.aw-explorer-related');
        [...relatedIds(item.id)].filter(id=>id!==item.id&&byId[id]).forEach(id=>{const chip=document.createElement('button');chip.type='button';chip.textContent=byId[id].title;chip.addEventListener('click',()=>{activeFamily='overview';query=byId[id].title;search.value=query;crumb.textContent='Linked evidence';render();});rel.appendChild(chip);});
        card.querySelector('[data-action="focus"]').addEventListener('click',()=>{applySceneFocus(item);crumb.textContent=item.title;card.classList.add('active');});
        card.querySelector('[data-action="route"]').addEventListener('click',()=>openRoute(item.route));
        results.appendChild(card);
      });
    }

    boundary.textContent=cfg.claim_boundary||'';
    launch.addEventListener('click',()=>{panel.hidden=false;launch.setAttribute('aria-expanded','true');shell.classList.add('open');render();});
    close.addEventListener('click',()=>{panel.hidden=true;launch.setAttribute('aria-expanded','false');shell.classList.remove('open');applySceneFocus(null);});
    search.addEventListener('input',()=>{query=search.value;activeFamily='overview';crumb.textContent=query?'Search results':'All evidence';render();});
    shell.querySelector('[data-family="overview"]').addEventListener('click',()=>{activeFamily='overview';query='';search.value='';crumb.textContent='All evidence';applySceneFocus(null);render();});
    render();
  }
  window.addEventListener('load',()=>setTimeout(installReviewerEvidenceExplorer,1550));
  window.addEventListener('aw:map-ready',()=>setTimeout(installReviewerEvidenceExplorer,1250));
})();
