(function () {
  function initPlume() {
    const shell = document.querySelector('.scene-shell');
    const canvas = document.getElementById('plumeCanvas');
    if (!shell || !canvas) return;

    const scene = JSON.parse(shell.dataset.scene || '{}');
    const ctx = canvas.getContext('2d');
    const particles = [];
    const plumeConfig = scene.plume_visualization || {};
    const geometry = plumeConfig.geometry || {};
    const particleCount = Math.min(plumeConfig.particle_count || 180, 42);
    const terrainBehavior = scene.terrain_plume_behavior || {};
    const flowPath = geometry.flow_path || {};
    const terrainTurbulence = Number(terrainBehavior.turbulence || 0.18);
    const terrainWidth = Number(terrainBehavior.width_multiplier || 1.0);
    const terrainMeasured = flowPath.data_state === 'measured_terrain_applied';
    const airVolume = plumeConfig.air_volume || scene.steering_aware_air_volume || scene.air_volume || {};
    const particleAdvection = plumeConfig.particle_advection || scene.terrain_responsive_particle_advection || {};
    const integratedMotion = plumeConfig.integrated_motion_orchestration || scene.integrated_motion_orchestration || {};
    const integratedVolume = plumeConfig.integrated_air_volume_orchestration || scene.integrated_air_volume_orchestration || {};
    const integratedVolumeReady = integratedVolume.data_state === "integrated_air_volume_orchestration_ready";
    const integratedVolumePlan = integratedVolume.orchestration || {};
    const orchestratedVolumeWidth = integratedVolumeReady ? Number(integratedVolumePlan.width_multiplier || 1) : 1;
    const orchestratedVolumeThickness = integratedVolumeReady ? Number(integratedVolumePlan.vertical_thickness_multiplier || 1) : 1;
    const orchestratedCoreOpacity = integratedVolumeReady ? Number(integratedVolumePlan.core_opacity_multiplier || 1) : 1;
    const orchestratedHazeOpacity = integratedVolumeReady ? Number(integratedVolumePlan.haze_opacity_multiplier || 1) : 1;
    const orchestratedVolumeAsymmetry = integratedVolumeReady ? Number(integratedVolumePlan.asymmetry_px || 0) : 0;
    const orchestratedVolumeLift = integratedVolumeReady ? Number(integratedVolumePlan.lift_px || 0) : 0;
    const orchestratedVolumeSettling = integratedVolumeReady ? Number(integratedVolumePlan.settling_px || 0) : 0;
    const orchestratedVolumeDiffusion = integratedVolumeReady ? Number(integratedVolumePlan.downstream_diffusion_multiplier || 1) : 1;
    const integratedMotionReady = integratedMotion.data_state === "integrated_motion_orchestration_ready";
    const motionPlan = integratedMotion.orchestration || {};
    const orchestratedSpeed = integratedMotionReady ? Number(motionPlan.speed_multiplier || 1) : 1;
    const orchestratedCoherence = integratedMotionReady ? Number(motionPlan.coherence || 0) : 0;
    const orchestratedCompression = integratedMotionReady ? Number(motionPlan.compression || 1) : 1;
    const orchestratedSpread = integratedMotionReady ? Number(motionPlan.lateral_spread || 1) : 1;
    const orchestratedLift = integratedMotionReady ? Number(motionPlan.lift_px || 0) : 0;
    const orchestratedSettling = integratedMotionReady ? Number(motionPlan.settling_px || 0) : 0;
    const orchestratedJitter = integratedMotionReady ? Number(motionPlan.uncertainty_jitter_px || 0) : 0;
    const advectionReady = particleAdvection.data_state === "terrain_responsive_particle_advection_ready";
    const advectionAuthority = Number(particleAdvection.advection_authority || 0);
    const motionCoherence = Number(particleAdvection.coherence || 0);
    const crosswindDrift = Number(particleAdvection.crosswind_drift_px || 0);
    const channelSpeedMultiplier = Number(particleAdvection.channel_speed_multiplier || 1);
    const shelterSpeedMultiplier = Number(particleAdvection.shelter_speed_multiplier || 1);
    const oppositionDrag = Number(particleAdvection.opposition_drag || 0);
    const deflectionOscillation = Number(particleAdvection.deflection_oscillation_px || 0);
    const uncertaintyJitter = Number(particleAdvection.uncertainty_jitter_px || 0);
    const responseBands = Array.isArray(particleAdvection.response_bands) ? particleAdvection.response_bands : [];
    const ridgeLee = plumeConfig.ridge_spillover_shelter || scene.ridge_spillover_shelter || {};
    const ridgeLeeReady = ridgeLee.data_state === "ridge_spillover_shelter_cache";
    const canyon = plumeConfig.canyon_channeling || scene.canyon_channeling || {};
    const canyonReady = canyon.data_state === "canyon_channeling_drainage_cache";
    const canyonDirectives = canyon.particle_directives || {};
    const canyonPullPx = Number(canyonDirectives.channel_pull_px || 0);
    const canyonSpeed = Number(canyonDirectives.channel_speed_multiplier || 1);
    const drainageCoherence = Number(canyonDirectives.drainage_coherence || 0);
    const canyonBand = canyonDirectives.channel_band || [0.18, 0.78];
    const saddleGap = plumeConfig.saddle_gap_acceleration || scene.saddle_gap_acceleration || {};

    const terrainConvergence = plumeConfig.terrain_convergence_accumulation || scene.terrain_convergence_accumulation || {};
    const terrainConvergenceReady = terrainConvergence.data_state === "terrain_convergence_accumulation_cache";
    const convergencePullPx = terrainConvergenceReady ? Number((terrainConvergence.particle_directives||{}).convergence_pull_px||0) : 0;
    const focusSlowdown = terrainConvergenceReady ? Number((terrainConvergence.particle_directives||{}).focus_slowdown||1) : 1;
    const focusBroadening = terrainConvergenceReady ? Number((terrainConvergence.particle_directives||{}).focus_broadening||1) : 1;
    const focusBand = terrainConvergenceReady ? ((terrainConvergence.particle_directives||{}).focus_band||[0.48,0.90]) : [0.48,0.90];

    const terrainDivergence = plumeConfig.terrain_divergence_dispersion || scene.terrain_divergence_dispersion || {};
    const terrainDivergenceReady = terrainDivergence.data_state === "terrain_divergence_dispersion_cache";
    const divergenceSpreadPx = terrainDivergenceReady ? Number((terrainDivergence.particle_directives||{}).divergence_spread_px||0) : 0;
    const dispersionBroadening = terrainDivergenceReady ? Number((terrainDivergence.particle_directives||{}).dispersion_broadening||1) : 1;
    const dispersionSpeed = terrainDivergenceReady ? Number((terrainDivergence.particle_directives||{}).dispersion_speed_multiplier||1) : 1;
    const dispersionBand = terrainDivergenceReady ? ((terrainDivergence.particle_directives||{}).dispersion_band||[0.56,0.96]) : [0.56,0.96];
    const basinRetention = plumeConfig.basin_retention_cold_air_pooling || scene.basin_retention_cold_air_pooling || {};
    const basinRetentionReady = basinRetention.data_state === "basin_retention_cold_air_pooling_cache";
    const basinSlowdown = basinRetentionReady ? Number((basinRetention.particle_directives||{}).retention_slowdown||1) : 1;
    const poolingBroadening = basinRetentionReady ? Number((basinRetention.particle_directives||{}).pooling_broadening||1) : 1;
    const basinSettlingPx = basinRetentionReady ? Number((basinRetention.particle_directives||{}).settling_px||0) : 0;
    const saddleGapReady = saddleGap.data_state === "saddle_transfer_gap_cache";
    const saddleDirectives = saddleGap.particle_directives || {};
    const saddleTransferPx = Number(saddleDirectives.saddle_transfer_px || 0);
    const gapSpeed = Number(saddleDirectives.gap_speed_multiplier || 1);
    const gapCoherence = Number(saddleDirectives.gap_coherence || 0);
    const saddleBand = saddleDirectives.saddle_band || [0.24, 0.62];
    const gapBand = saddleDirectives.gap_band || [0.34, 0.76];
    const ridgeDirectives = ridgeLee.particle_directives || {};
    const spilloverLift = Number(ridgeDirectives.spillover_lift_px || 0);
    const leeSlowdown = Number(ridgeDirectives.lee_slowdown_multiplier || 1);
    const leeSpread = Number(ridgeDirectives.lee_spread_multiplier || 1);
    const crestBand = Array.isArray(ridgeDirectives.crest_band) ? ridgeDirectives.crest_band : [0.40, 0.62];
    const leeBand = Array.isArray(ridgeDirectives.lee_band) ? ridgeDirectives.lee_band : [0.56, 0.86];
    const steeringBias = Number(airVolume.lateral_bias_px || 0);
    const steeringCurve = Number(airVolume.curve_strength || 0);
    const channelCompression = Number(airVolume.channel_compression || 1) * orchestratedVolumeWidth;
    const uncertaintyExpansion = Number(airVolume.uncertainty_expansion || 1) * orchestratedVolumeDiffusion;
    const layerAsymmetry = Number(airVolume.layer_asymmetry || 0) + orchestratedVolumeAsymmetry;
    const coreOpacity = Number(airVolume.core_opacity || 0.22) * orchestratedCoreOpacity;
    const midOpacity = Number(airVolume.mid_opacity || 0.12);
    const hazeOpacity = Number(airVolume.haze_opacity || 0.06) * orchestratedHazeOpacity;
    const verticalOffset = Number(airVolume.vertical_offset_px || 7) * orchestratedVolumeThickness - orchestratedVolumeLift + orchestratedVolumeSettling;
    const scaleGrowth = Number(airVolume.particle_scale_growth || 4.2);
    const livingWind = plumeConfig.living_wind || scene.living_wind || {};
    const cadenceMultiplier = Number(livingWind.cadence_multiplier || 1);
    const spacingMultiplier = Number(livingWind.spacing_multiplier || 1);
    const swayAmplitude = Number(livingWind.sway_amplitude_px || 5);
    const gustStrength = Number(livingWind.gust_strength || 0.08);
    const gustCycleMs = Math.max(4500, Number(livingWind.gust_cycle_seconds || 7) * 1000);
    const wakeStrength = Number(livingWind.terrain_wake_strength || 0);
    const pocketCount = Math.max(1, Number(livingWind.turbulence_pockets || 2));
    const missingEvidence = scene.missing_evidence || {};
    const evidenceStrength = Number(missingEvidence.visual_strength || 0.7);
    const downstreamBreak = Number(missingEvidence.downstream_break || 0.3);
    let width = 0;
    let height = 0;
    let map = null;
    let mapReady = false;

    function resize() {
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      width = Math.floor(rect.width * dpr);
      height = Math.floor(rect.height * dpr);
      canvas.width = width;
      canvas.height = height;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function randParticle(randomize) {
      return {
        t: randomize ? Math.pow(Math.random(), spacingMultiplier) : 0,
        speed: (0.0019 + Math.random() * 0.0044) * cadenceMultiplier,
        lateral: (Math.random() - 0.5) * 2,
        wobble: Math.random() * Math.PI * 2,
        size: 1.0 + Math.random() * 3.0,
        phase: Math.random() * Math.PI * 2,
        responseSeed: Math.random(),
        previousX: null,
        previousY: null,
        ageOffset: Math.random(),
      };
    }

    for (let i = 0; i < particleCount; i++) particles.push(randParticle(true));

    function latLngToPoint(obj) {
      if (!map || !obj) return null;
      const p = map.latLngToContainerPoint([obj.lat, obj.lon]);
      return { x: p.x, y: p.y };
    }

    function screenPath() {
      const sourcePath = geometry.centerline || [];
      return sourcePath.map(latLngToPoint).filter(Boolean);
    }

    function pathPoint(points, t) {
      if (!points || points.length < 2) return null;
      const clamped = Math.max(0, Math.min(0.999999, t));
      const scaled = clamped * (points.length - 1);
      const index = Math.min(points.length - 2, Math.floor(scaled));
      const local = scaled - index;
      const a = points[index];
      const b = points[index + 1];
      const x = a.x + (b.x - a.x) * local;
      const y = a.y + (b.y - a.y) * local;
      const vx = b.x - a.x;
      const vy = b.y - a.y;
      const length = Math.max(1, Math.hypot(vx, vy));
      return { x, y, nx: -vy / length, ny: vx / length, segmentLength: length };
    }

    function fallbackPoint(t, lateral, wobble) {
      const rect = canvas.getBoundingClientRect();
      const sx = rect.width * 0.21;
      const sy = rect.height * 0.58;
      const ex = rect.width * 0.75;
      const ey = rect.height * 0.48;
      const x = sx + (ex - sx) * t;
      const y = sy + (ey - sy) * t;
      const spread = rect.height * (0.035 + t * 0.16);
      return { x, y: y + lateral * spread + Math.sin(wobble + t * 11) * 5 };
    }


    function rangeEnvelope(t, band) {
      const start = Number(band[0] || 0);
      const end = Number(band[1] || 1);
      if (t < start || t > end || end <= start) return 0;
      return Math.sin(Math.PI * ((t - start) / (end - start)));
    }

    function bandEnvelope(t, driver) {
      let influence = 0;
      for (const band of responseBands) {
        if (driver && band.driver !== driver) continue;
        const start = Number(band.start || 0);
        const end = Number(band.end || 1);
        if (t < start || t > end || end <= start) continue;
        const local = (t - start) / (end - start);
        influence = Math.max(influence, Math.sin(Math.PI * local) * Number(band.weight || 0));
      }
      return influence;
    }

    function registeredPoint(t, lateral, wobble, responseSeed) {
      const points = screenPath();
      const base = pathPoint(points, t);
      if (!base) return fallbackPoint(t, lateral, wobble);
      const totalLength = points.reduce((sum, p, i) => i ? sum + Math.hypot(p.x - points[i - 1].x, p.y - points[i - 1].y) : 0, 0);
      const spread = Math.max(16, Math.min(190, totalLength * (0.022 + t * 0.105) * terrainWidth * channelCompression * uncertaintyExpansion * orchestratedCompression * orchestratedSpread));
      const waveScale = terrainMeasured ? 1.0 : 0.45;
      const now = performance.now();
      const gustPhase = (now % gustCycleMs) / gustCycleMs * Math.PI * 2;
      const livingSway = Math.sin(gustPhase + wobble + t * 6.5) * swayAmplitude * (0.25 + t * 0.75);
      let pocket = 0;
      for (let i = 1; i <= pocketCount; i++) {
        const center = i / (pocketCount + 1);
        const distance = (t - center) / 0.10;
        pocket += Math.exp(-distance * distance) * Math.sin(wobble * (i + 1) + now * 0.0014) * swayAmplitude * 0.28;
      }
      const wakeEnvelope = terrainMeasured ? Math.max(0, Math.sin(Math.PI * Math.min(1, Math.max(0, (t - 0.38) / 0.62)))) : 0;
      const terrainWake = Math.sin(wobble + now * 0.0011 + t * 18) * totalLength * 0.018 * wakeStrength * wakeEnvelope;
      const wave = (Math.sin(wobble + t * (9 + terrainTurbulence * 13)) * Math.min(22, totalLength * (0.006 + terrainTurbulence * 0.018)) * waveScale) + livingSway + pocket + terrainWake;
      const steeringEnvelope = Math.sin(Math.PI * Math.max(0, Math.min(1, t)));
      const steeringShift = steeringBias * steeringEnvelope + steeringCurve * totalLength * 0.018 * Math.sin(Math.PI * t) * (0.45 + t);
      const asymmetric = layerAsymmetry * spread * t;
      const channelBand = advectionReady ? bandEnvelope(t, 'channeling') : 0;
      const deflectBand = advectionReady ? Math.max(bandEnvelope(t, 'lateral_deflection'), bandEnvelope(t, particleAdvection.dominant_driver)) : 0;
      const uncertaintyBand = advectionReady ? bandEnvelope(t, 'uncertainty') : 0;
      const particleSign = responseSeed < 0.5 ? -1 : 1;
      const responsiveDrift = crosswindDrift * Math.sin(Math.PI * t) * (0.35 + deflectBand);
      const responsiveWave = Math.sin(wobble * 1.7 + now * 0.001 + t * 21) * deflectionOscillation * deflectBand * (0.45 + 0.55 * advectionAuthority);
      const uncertaintyWave = Math.sin(wobble * 2.3 + now * 0.0018 + t * 29) * (uncertaintyJitter + orchestratedJitter) * uncertaintyBand * particleSign * (1 - 0.55 * motionCoherence);
      const channelPull = -lateral * spread * channelBand * advectionAuthority * 0.34;
      const crestEnvelope = ridgeLeeReady ? rangeEnvelope(t, crestBand) : 0;
      const leeEnvelope = ridgeLeeReady ? rangeEnvelope(t, leeBand) : 0;
      const ridgeLift = -spilloverLift * crestEnvelope - orchestratedLift * Math.sin(Math.PI * t) * (0.35 + 0.65 * motionCoherence);
      const leeBroadening = lateral * spread * (leeSpread - 1) * leeEnvelope;
      const canyonEnvelope = canyonReady ? rangeEnvelope(t, canyonBand) : 0;
      const canyonPull = -lateral * canyonPullPx * canyonEnvelope * (0.4 + 0.6 * drainageCoherence);
      const saddleEnvelope = saddleGapReady ? rangeEnvelope(t, saddleBand) : 0;
      const gapEnvelope = saddleGapReady ? rangeEnvelope(t, gapBand) : 0;
      const saddleTransfer = -saddleTransferPx * saddleEnvelope * (0.35 + 0.65 * gapCoherence);
      const gapTightening = -lateral * spread * (gapSpeed - 1) * gapEnvelope * 0.55;
      const focusEnvelope = terrainConvergenceReady ? rangeEnvelope(t, focusBand) : 0;
      const convergencePull = -lateral * convergencePullPx * focusEnvelope;
      const dispersionEnvelope = terrainDivergenceReady ? rangeEnvelope(t, dispersionBand) : 0;
      const divergenceSpread = lateral * divergenceSpreadPx * dispersionEnvelope;
      const focusedBroadening = lateral * spread * (focusBroadening - 1) * focusEnvelope;
      const offset = lateral * spread + wave + steeringShift + asymmetric + responsiveDrift + responsiveWave + uncertaintyWave + channelPull + ridgeLift + leeBroadening + canyonPull + saddleTransfer + gapTightening + convergencePull + focusedBroadening;
      return {
        x: base.x + base.nx * offset,
        y: base.y + base.ny * offset,
      };
    }

    function drawPathStroke(points, lineWidth, alpha) {
      if (points.length < 2) return;
      const grad = ctx.createLinearGradient(points[0].x, points[0].y, points[points.length - 1].x, points[points.length - 1].y);
      grad.addColorStop(0, `rgba(255, 197, 91, ${alpha * 1.15})`);
      grad.addColorStop(0.18, `rgba(194, 246, 238, ${alpha})`);
      grad.addColorStop(0.62, `rgba(132, 220, 255, ${alpha * 0.72})`);
      grad.addColorStop(1, 'rgba(132, 220, 255, 0)');
      ctx.strokeStyle = grad;
      ctx.lineWidth = lineWidth;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        const current = points[i];
        const previous = points[i - 1];
        const mx = (previous.x + current.x) / 2;
        const my = (previous.y + current.y) / 2;
        ctx.quadraticCurveTo(previous.x, previous.y, mx, my);
      }
      const last = points[points.length - 1];
      ctx.lineTo(last.x, last.y);
      ctx.stroke();
    }

    function drawVolumeLayer(points, widthScale, alpha, yOffset, blurPx) {
      if (points.length < 2) return;
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.filter = `blur(${blurPx}px)`;
      ctx.translate(0, yOffset);
      const length = points.reduce((sum, p, i) => i ? sum + Math.hypot(p.x - points[i - 1].x, p.y - points[i - 1].y) : 0, 0);
      const interruptedAlpha = alpha * evidenceStrength;
      drawPathStroke(points, Math.max(8, Math.min(170, length * widthScale * terrainWidth)), interruptedAlpha);
      ctx.restore();
    }




    // PASS 18 - Terrain-Shaped Air.
    // One coherent field remains, but its width, brightness, and continuity now respond
    // visibly to the terrain contracts already computed by the scientific engine.
    // Narrowing suggests channeling or convergence; broadening suggests lee spread or
    // divergence; broken continuity represents uncertainty rather than disappearance by accident.
    function drawTerrainShapedBreath(points, now, essence, movement) {
      if (!essence || !points || points.length < 2) return;
      const pulse = 0.94 + Math.sin(now * 0.00020) * 0.06;
      const samples = 72;
      const baseLanes = [-0.34, -0.16, 0, 0.16, 0.34];

      ctx.save();
      ctx.globalCompositeOperation = 'screen';

      // A quiet broad field establishes immediate continuity without becoming a plume body.
      ctx.globalAlpha *= (0.72 + movement.awaken * 0.10 + movement.converse * 0.10) * pulse;
      drawVolumeLayer(points, 0.075 * uncertaintyExpansion, hazeOpacity * 0.78, verticalOffset * 0.28, 16);

      // Terrain-readable stream families. Their geometry is generated by registeredPoint(),
      // while local alpha and line width expose the terrain response at a glance.
      for (let laneIndex = 0; laneIndex < baseLanes.length; laneIndex++) {
        const lane = baseLanes[laneIndex];
        let segment = [];
        for (let i = 0; i < samples; i++) {
          const t = i / (samples - 1);
          const phase = now * 0.00018 + laneIndex * 1.37;
          const channel = advectionReady ? bandEnvelope(t, 'channeling') : 0;
          const shelter = advectionReady ? bandEnvelope(t, 'shelter') : 0;
          const uncertainty = advectionReady ? bandEnvelope(t, 'uncertainty') : 0;
          const focus = terrainConvergenceReady ? rangeEnvelope(t, focusBand) : 0;
          const divergence = terrainDivergenceReady ? rangeEnvelope(t, dispersionBand) : 0;
          const crest = ridgeLeeReady ? rangeEnvelope(t, crestBand) : 0;
          const lee = ridgeLeeReady ? rangeEnvelope(t, leeBand) : 0;

          const breathing = Math.sin(phase + t * 7.2) * (0.012 + t * 0.025);
          const terrainLane = lane * (1 - channel * 0.48 - focus * 0.36 + divergence * 0.70 + lee * 0.30);
          const p = registeredPoint(t, terrainLane + breathing, phase, (laneIndex + 1) / (baseLanes.length + 1));
          if (!p) continue;

          const confidenceFade = Math.max(0.06, evidenceStrength * (1 - uncertainty * 0.78) * (1 - Math.max(0, t - 0.72) * 1.65));
          const breakWave = 0.54 + 0.46 * Math.sin(laneIndex * 2.4 + i * 0.78 + now * 0.00028);
          const continuity = uncertainty > 0.32 ? (breakWave > uncertainty * 0.72 ? 1 : 0) : 1;

          if (!continuity) {
            if (segment.length > 1) drawTerrainSegment(segment, laneIndex, channel, focus, divergence, shelter, crest, confidenceFade);
            segment = [];
            continue;
          }
          segment.push({x:p.x, y:p.y, t, channel, focus, divergence, shelter, crest, confidenceFade});
        }
        if (segment.length > 1) {
          const m = segment[Math.floor(segment.length/2)];
          drawTerrainSegment(segment, laneIndex, m.channel, m.focus, m.divergence, m.shelter, m.crest, m.confidenceFade);
        }
      }
      ctx.restore();
    }

    function drawTerrainSegment(segment, laneIndex, channel, focus, divergence, shelter, crest, confidenceFade) {
      const first = segment[0];
      const last = segment[segment.length - 1];
      const grad = ctx.createLinearGradient(first.x, first.y, last.x, last.y);
      const laneStrength = laneIndex === 2 ? 1.0 : 0.72;
      const alpha = (0.13 + channel * 0.05 + focus * 0.045 + crest * 0.025 - shelter * 0.025) * confidenceFade * laneStrength;
      grad.addColorStop(0, `rgba(255, 202, 104, ${alpha * 0.82})`);
      grad.addColorStop(0.18, `rgba(198, 244, 232, ${alpha})`);
      grad.addColorStop(0.62, `rgba(132, 220, 236, ${alpha * 0.78})`);
      grad.addColorStop(1, `rgba(116, 197, 224, ${alpha * 0.18})`);
      ctx.save();
      ctx.strokeStyle = grad;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.filter = laneIndex === 2 ? 'blur(0.7px)' : 'blur(1.5px)';
      ctx.lineWidth = Math.max(0.8, (laneIndex === 2 ? 2.4 : 1.35) * (1 - channel * 0.18 - focus * 0.12 + divergence * 0.42));
      ctx.beginPath();
      ctx.moveTo(first.x, first.y);
      for (let i = 1; i < segment.length; i++) {
        const a = segment[i - 1];
        const b = segment[i];
        ctx.quadraticCurveTo(a.x, a.y, (a.x + b.x) / 2, (a.y + b.y) / 2);
      }
      ctx.lineTo(last.x, last.y);
      ctx.stroke();
      ctx.restore();
    }

    function drawAmbientAir(now, essence) {
      if (!essence) return;
      const rect = canvas.getBoundingClientRect();
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.filter = 'blur(18px)';
      for (let band = 0; band < 5; band++) {
        const yBase = rect.height * (0.20 + band * 0.15);
        const drift = Math.sin(now * (0.000035 + band * 0.000006) + band * 1.8) * rect.width * 0.035;
        const grad = ctx.createLinearGradient(-80 + drift, yBase, rect.width + 80 + drift, yBase + 30);
        grad.addColorStop(0, 'rgba(150, 224, 232, 0)');
        grad.addColorStop(0.28, `rgba(150, 224, 232, ${0.010 + band * 0.002})`);
        grad.addColorStop(0.62, `rgba(184, 235, 226, ${0.014 + band * 0.002})`);
        grad.addColorStop(1, 'rgba(150, 224, 232, 0)');
        ctx.strokeStyle = grad;
        ctx.lineWidth = 34 + band * 8;
        ctx.beginPath();
        ctx.moveTo(-120 + drift, yBase);
        ctx.bezierCurveTo(rect.width * 0.28, yBase - 14, rect.width * 0.62, yBase + 24, rect.width + 120 + drift, yBase - 8);
        ctx.stroke();
      }
      ctx.restore();
    }

    function drawFieldRibbons(now, essence) {
      if (!essence) return;
      const ribbonCount = 11;
      const samples = 44;
      for (let ribbon = 0; ribbon < ribbonCount; ribbon++) {
        const points = [];
        const phase = now * (0.000055 + ribbon * 0.0000025) + ribbon * 0.71;
        const lane = ((ribbon / (ribbonCount - 1)) - 0.5) * 0.72;
        for (let i = 0; i < samples; i++) {
          const t = i / (samples - 1);
          const breathing = Math.sin(phase + t * (4.2 + ribbon * 0.11)) * (0.055 + t * 0.14);
          const lateral = lane * (0.42 + t * 0.82) + breathing;
          const p = mapReady
            ? registeredPoint(t, lateral, phase, (ribbon + 1) / (ribbonCount + 1))
            : fallbackPoint(t, lateral, phase);
          if (p) points.push(p);
        }
        if (points.length < 2) continue;
        const support = 0.075 * evidenceStrength * (1 - ribbon * 0.018);
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        ctx.filter = `blur(${1.6 + (ribbon % 3) * 0.9}px)`;
        ctx.globalAlpha = 0.46;
        drawPathStroke(points, 0.75 + (ribbon % 4) * 0.28, support);
        ctx.restore();
      }
    }

    function drawAtmosphericVeils(now, essence) {
      if (!essence) return;
      const samples = 34;
      const veilCount = 4;
      for (let veil = 0; veil < veilCount; veil++) {
        const points = [];
        const phase = now * (0.00010 + veil * 0.000018) + veil * 1.7;
        for (let i = 0; i < samples; i++) {
          const t = i / (samples - 1);
          const lateral = Math.sin(phase + t * (5.4 + veil * 0.55)) * (0.10 + veil * 0.035);
          const p = mapReady
            ? registeredPoint(t, lateral, phase + veil, (veil + 1) / (veilCount + 1))
            : fallbackPoint(t, lateral, phase + veil);
          if (p) points.push(p);
        }
        if (points.length < 2) continue;
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        ctx.filter = `blur(${10 + veil * 4}px)`;
        ctx.globalAlpha = 0.18 - veil * 0.026;
        const widthScale = 0.030 + veil * 0.016;
        drawPathStroke(points, Math.max(10, width * widthScale), 0.24 - veil * 0.028);
        ctx.restore();
      }
    }


    function drawSegmentedField(now, essence) {
      if (!essence) return;
      const samples = 72;
      const lanes = 9;
      for (let laneIndex = 0; laneIndex < lanes; laneIndex++) {
        const lane = (laneIndex - (lanes - 1) / 2) / ((lanes - 1) / 2);
        const phase = now * (0.00007 + laneIndex * 0.000002) + laneIndex * 0.83;
        let segment = [];
        for (let i = 0; i < samples; i++) {
          const t = i / (samples - 1);
          const uncertainty = Math.max(0, (t - 0.42) / 0.58);
          const breathe = Math.sin(phase + t * 6.2) * (0.025 + t * 0.085);
          const lateral = lane * (0.18 + t * 0.50) + breathe;
          const p = mapReady ? registeredPoint(t, lateral, phase, (laneIndex + 1) / (lanes + 1)) : fallbackPoint(t, lateral, phase);
          const breakSignal = Math.sin(t * 46 + laneIndex * 1.9 + now * 0.00045);
          const shouldBreak = t > 0.54 && breakSignal > (0.52 + evidenceStrength * 0.20 - uncertainty * 0.12);
          if (p && !shouldBreak) {
            segment.push({...p, t});
          } else if (segment.length > 1) {
            drawFieldSegment(segment, laneIndex);
            segment = [];
          } else {
            segment = [];
          }
        }
        if (segment.length > 1) drawFieldSegment(segment, laneIndex);
      }
    }

    function drawFieldSegment(points, laneIndex) {
      const startT = points[0].t;
      const endT = points[points.length - 1].t;
      const midT = (startT + endT) * 0.5;
      const support = Math.max(0.10, 1 - Math.max(0, midT - 0.34) * 1.25);
      const grad = ctx.createLinearGradient(points[0].x, points[0].y, points[points.length - 1].x, points[points.length - 1].y);
      grad.addColorStop(0, `rgba(244, 220, 153, ${0.16 * support})`);
      grad.addColorStop(0.20, `rgba(188, 242, 229, ${0.19 * support})`);
      grad.addColorStop(0.72, `rgba(126, 211, 235, ${0.12 * support})`);
      grad.addColorStop(1, `rgba(126, 211, 235, ${0.02 * support})`);
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.strokeStyle = grad;
      ctx.lineWidth = 1.05 + (laneIndex % 3) * 0.28;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.shadowBlur = 5 + midT * 6;
      ctx.shadowColor = `rgba(138, 224, 237, ${0.14 * support})`;
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        const a = points[i - 1];
        const b = points[i];
        const mx = (a.x + b.x) / 2;
        const my = (a.y + b.y) / 2;
        ctx.quadraticCurveTo(a.x, a.y, mx, my);
      }
      const last = points[points.length - 1];
      ctx.lineTo(last.x, last.y);
      ctx.stroke();
      ctx.restore();
    }



    // PASS 10 - Visual Symphony: cadence, counterpoint, and silence.
    // The atmospheric field is orchestrated in slow phrases rather than equal-weight effects.
    function drawVisualSymphony(now, essence) {
      if (!essence) return;
      const phrase = (Math.sin(now * 0.00018) + 1) * 0.5;
      const longBreath = (Math.sin(now * 0.000075 - 0.9) + 1) * 0.5;
      const families = 5;
      const samples = 58;

      for (let family = 0; family < families; family++) {
        const laneBase = (family - (families - 1) / 2) / ((families - 1) / 2);
        const points = [];
        const phase = now * (0.000032 + family * 0.000003) + family * 1.37;
        for (let i = 0; i < samples; i++) {
          const t = i / (samples - 1);
          const opening = Math.sin(Math.min(1, t / 0.22) * Math.PI * 0.5);
          const uncertainty = Math.max(0, (t - 0.48) / 0.52);
          const terrainPhrase = Math.sin(phase + t * (3.9 + family * 0.16)) * (0.018 + t * 0.075);
          const counterMotion = Math.sin(phase * 0.61 - t * 7.1) * (0.010 + uncertainty * 0.055);
          const lateral = laneBase * (0.08 + t * 0.34) * opening + terrainPhrase + counterMotion;
          const p = mapReady
            ? registeredPoint(t, lateral, phase, (family + 1) / (families + 1))
            : fallbackPoint(t, lateral, phase);
          if (p) points.push({...p, t});
        }
        if (points.length < 2) continue;

        const grad = ctx.createLinearGradient(points[0].x, points[0].y, points[points.length - 1].x, points[points.length - 1].y);
        const familyAlpha = 0.055 + family * 0.006;
        grad.addColorStop(0, `rgba(255, 202, 103, ${familyAlpha * (0.85 + phrase * 0.15)})`);
        grad.addColorStop(0.16, `rgba(213, 244, 228, ${familyAlpha * 1.28})`);
        grad.addColorStop(0.48, `rgba(145, 226, 236, ${familyAlpha * (0.96 + longBreath * 0.18)})`);
        grad.addColorStop(0.76, `rgba(118, 197, 224, ${familyAlpha * 0.44})`);
        grad.addColorStop(1, 'rgba(118, 197, 224, 0)');

        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        ctx.strokeStyle = grad;
        ctx.lineWidth = 1.15 + family * 0.38 + phrase * 0.35;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.shadowBlur = 5 + family * 1.2;
        ctx.shadowColor = `rgba(133, 225, 235, ${0.07 + longBreath * 0.035})`;
        ctx.beginPath();
        ctx.moveTo(points[0].x, points[0].y);
        for (let i = 1; i < points.length; i++) {
          const a = points[i - 1];
          const b = points[i];
          const mx = (a.x + b.x) / 2;
          const my = (a.y + b.y) / 2;
          ctx.quadraticCurveTo(a.x, a.y, mx, my);
        }
        const last = points[points.length - 1];
        ctx.lineTo(last.x, last.y);
        ctx.stroke();
        ctx.restore();
      }

      // A few broad breaths create atmosphere between the lines, never a solid plume body.
      const base = mapReady ? screenPath() : [];
      if (base.length >= 2) {
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        ctx.filter = `blur(${18 + longBreath * 8}px)`;
        const grad = ctx.createLinearGradient(base[0].x, base[0].y, base[base.length - 1].x, base[base.length - 1].y);
        grad.addColorStop(0, `rgba(255, 202, 112, ${0.030 + phrase * 0.012})`);
        grad.addColorStop(0.28, `rgba(172, 235, 226, ${0.043 + longBreath * 0.014})`);
        grad.addColorStop(0.68, 'rgba(126, 210, 230, 0.020)');
        grad.addColorStop(1, 'rgba(126, 210, 230, 0)');
        ctx.strokeStyle = grad;
        ctx.lineWidth = Math.max(28, Math.min(78, width * (0.040 + longBreath * 0.010)));
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(base[0].x, base[0].y);
        for (let i = 1; i < base.length; i++) {
          const a = base[i - 1];
          const b = base[i];
          ctx.quadraticCurveTo(a.x, a.y, (a.x + b.x) / 2, (a.y + b.y) / 2);
        }
        ctx.stroke();
        ctx.restore();
      }
    }


    // PASS 11 - Field of Possibility: the atmosphere reads as zones and tendencies,
    // not a single certain route. Calm pockets, active corridors, and dissolving edges
    // are all derived from the same registered path and confidence envelope.
    function drawPossibilityField(now, essence) {
      if (!essence) return;
      const base = mapReady ? screenPath() : [];
      if (base.length < 2) return;

      const breath = (Math.sin(now * 0.000085) + 1) * 0.5;
      const slowPulse = (Math.sin(now * 0.000031 - 1.2) + 1) * 0.5;
      const nodes = 8;

      ctx.save();
      ctx.globalCompositeOperation = 'screen';

      for (let i = 0; i < nodes; i++) {
        const t = 0.05 + (i / (nodes - 1)) * 0.88;
        const uncertainty = Math.max(0, (t - 0.42) / 0.58);
        const phase = now * (0.000045 + i * 0.000002) + i * 1.17;
        const lateral = Math.sin(phase) * (0.03 + t * 0.14);
        const center = mapReady
          ? registeredPoint(t, lateral, phase, (i + 1) / (nodes + 1))
          : fallbackPoint(t, lateral, phase);
        if (!center) continue;

        const calmBand = advectionReady ? bandEnvelope(t, 'shelter') : 0;
        const channelBand = advectionReady ? bandEnvelope(t, 'channeling') : 0;
        const focusBandValue = terrainConvergenceReady ? rangeEnvelope(t, focusBand) : 0;
        const divergenceBand = terrainDivergenceReady ? rangeEnvelope(t, dispersionBand) : 0;

        const activity = Math.max(0.08, 0.32 + channelBand * 0.42 + focusBandValue * 0.30 - calmBand * 0.22);
        const spread = 1 + divergenceBand * 0.65 + uncertainty * 0.75;
        const coherence = Math.max(0.08, (1 - uncertainty * 0.78) * evidenceStrength);
        const radiusX = (38 + i * 7) * spread * (0.90 + breath * 0.10);
        const radiusY = (18 + i * 4) * (0.92 + slowPulse * 0.08);

        const warm = Math.max(0, 1 - t / 0.20);
        const alpha = (0.026 + activity * 0.034) * coherence;
        const inner = ctx.createRadialGradient(center.x, center.y, 0, center.x, center.y, radiusX);
        inner.addColorStop(0, warm
          ? `rgba(255, 210, 126, ${alpha * (0.90 + warm * 0.55)})`
          : `rgba(157, 231, 234, ${alpha})`);
        inner.addColorStop(0.42, `rgba(126, 216, 232, ${alpha * 0.66})`);
        inner.addColorStop(0.78, `rgba(112, 194, 220, ${alpha * 0.22})`);
        inner.addColorStop(1, 'rgba(112, 194, 220, 0)');

        ctx.save();
        ctx.translate(center.x, center.y);
        ctx.rotate(Math.sin(phase * 0.61) * 0.16);
        ctx.scale(1, radiusY / radiusX);
        ctx.fillStyle = inner;
        ctx.beginPath();
        ctx.arc(0, 0, radiusX, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        // Sparse contour arcs make the field legible without drawing a route.
        if (i > 0 && i < nodes - 1 && coherence > 0.12) {
          const arcAlpha = alpha * (0.62 - uncertainty * 0.34);
          ctx.save();
          ctx.strokeStyle = `rgba(177, 238, 232, ${arcAlpha})`;
          ctx.lineWidth = 0.7 + activity * 0.55;
          ctx.setLineDash(uncertainty > 0.45 ? [5, 8 + uncertainty * 7] : []);
          ctx.beginPath();
          ctx.ellipse(center.x, center.y, radiusX * 0.72, radiusY * 0.72, Math.sin(phase) * 0.10, -0.82, 0.96);
          ctx.stroke();
          ctx.restore();
        }
      }

      ctx.restore();
    }

    function drawTerrainReveal(points, essence) {
      if (!essence || points.length < 2) return;
      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      ctx.filter = 'blur(22px)';
      const grad = ctx.createLinearGradient(points[0].x, points[0].y, points[points.length - 1].x, points[points.length - 1].y);
      grad.addColorStop(0, 'rgba(255, 205, 112, 0.080)');
      grad.addColorStop(0.22, 'rgba(175, 238, 226, 0.072)');
      grad.addColorStop(0.68, 'rgba(126, 207, 229, 0.040)');
      grad.addColorStop(1, 'rgba(126, 207, 229, 0)');
      ctx.strokeStyle = grad;
      ctx.lineWidth = Math.max(34, Math.min(105, width * 0.075));
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        const a = points[i - 1];
        const b = points[i];
        ctx.quadraticCurveTo(a.x, a.y, (a.x + b.x) / 2, (a.y + b.y) / 2);
      }
      ctx.stroke();
      ctx.restore();
    }


    // PASS 13 - Terrain as Narrator: the world reveals the atmospheric tendency.
    // Light gathers where the registered field meets terrain influence, then loses
    // continuity downstream as evidentiary support weakens. This is visual emphasis,
    // not measured irradiance, concentration, or observed transport.
    function drawTerrainNarration(now, essence) {
      if (!essence) return;
      const base = mapReady ? screenPath() : [];
      if (base.length < 2) return;

      const breath = (Math.sin(now * 0.000072 - 0.8) + 1) * 0.5;
      const reveal = (Math.sin(now * 0.000041 + 0.35) + 1) * 0.5;
      const stations = 11;

      ctx.save();
      ctx.globalCompositeOperation = 'screen';

      for (let i = 0; i < stations; i++) {
        const t = 0.035 + (i / (stations - 1)) * 0.90;
        const uncertainty = Math.max(0, (t - 0.44) / 0.56);
        const phase = now * (0.000028 + i * 0.0000014) + i * 0.91;
        const channel = advectionReady ? bandEnvelope(t, 'channeling') : 0;
        const shelter = advectionReady ? bandEnvelope(t, 'shelter') : 0;
        const focus = terrainConvergenceReady ? rangeEnvelope(t, focusBand) : 0;
        const divergence = terrainDivergenceReady ? rangeEnvelope(t, dispersionBand) : 0;
        const lateral = Math.sin(phase) * (0.012 + t * 0.038) * (1 + divergence * 0.65);
        const center = registeredPoint(t, lateral, phase, (i + 1) / (stations + 1));
        if (!center) continue;

        const nextT = Math.min(0.995, t + 0.018);
        const next = registeredPoint(nextT, lateral, phase, (i + 1) / (stations + 1));
        if (!next) continue;
        const angle = Math.atan2(next.y - center.y, next.x - center.x);

        const support = Math.max(0.055, evidenceStrength * (1 - uncertainty * 0.82));
        const continuity = uncertainty > 0.28
          ? Math.max(0.12, 0.55 + 0.45 * Math.sin(i * 2.31 + now * 0.00022))
          : 1;
        const terrainResponse = 0.70 + channel * 0.34 + focus * 0.26 - shelter * 0.18;
        const rx = (44 + i * 8) * (1 + divergence * 0.42) * (0.94 + breath * 0.09);
        const ry = (10 + i * 2.1) * (0.88 + reveal * 0.16) * (1 + shelter * 0.22);
        const alpha = (0.018 + terrainResponse * 0.025) * support * continuity;

        ctx.save();
        ctx.translate(center.x, center.y);
        ctx.rotate(angle);
        ctx.scale(1, ry / rx);
        const glow = ctx.createRadialGradient(0, 0, 0, 0, 0, rx);
        const warm = Math.max(0, 1 - t / 0.18);
        glow.addColorStop(0, warm
          ? `rgba(255, 211, 130, ${alpha * 1.35})`
          : `rgba(188, 236, 224, ${alpha * 1.15})`);
        glow.addColorStop(0.38, `rgba(137, 216, 224, ${alpha * 0.62})`);
        glow.addColorStop(0.78, `rgba(102, 183, 208, ${alpha * 0.20})`);
        glow.addColorStop(1, 'rgba(102, 183, 208, 0)');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(0, 0, rx, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();

        // Sparse cross-contours suggest terrain catching and redirecting the field.
        if (i > 0 && i < stations - 1 && continuity > 0.25) {
          ctx.save();
          ctx.translate(center.x, center.y);
          ctx.rotate(angle + Math.PI / 2);
          ctx.strokeStyle = `rgba(202, 241, 229, ${alpha * (0.70 - uncertainty * 0.28)})`;
          ctx.lineWidth = 0.55 + channel * 0.35 + focus * 0.28;
          ctx.setLineDash(uncertainty > 0.42 ? [3, 7 + uncertainty * 8] : []);
          ctx.beginPath();
          ctx.moveTo(-ry * 1.8, 0);
          ctx.quadraticCurveTo(0, Math.sin(phase) * 3.5, ry * 1.8, 0);
          ctx.stroke();
          ctx.restore();
        }
      }

      // A restrained relief corridor binds the illuminated terrain moments together.
      ctx.save();
      ctx.filter = `blur(${24 + breath * 10}px)`;
      const grad = ctx.createLinearGradient(base[0].x, base[0].y, base[base.length - 1].x, base[base.length - 1].y);
      grad.addColorStop(0, `rgba(255, 211, 128, ${0.035 + reveal * 0.012})`);
      grad.addColorStop(0.24, `rgba(183, 235, 224, ${0.042 + breath * 0.012})`);
      grad.addColorStop(0.62, 'rgba(123, 202, 220, 0.020)');
      grad.addColorStop(0.86, 'rgba(112, 190, 214, 0.006)');
      grad.addColorStop(1, 'rgba(112, 190, 214, 0)');
      ctx.strokeStyle = grad;
      ctx.lineWidth = Math.max(42, Math.min(118, width * 0.082));
      ctx.lineCap = 'round';
      ctx.beginPath();
      ctx.moveTo(base[0].x, base[0].y);
      for (let i = 1; i < base.length; i++) {
        const a = base[i - 1];
        const b = base[i];
        ctx.quadraticCurveTo(a.x, a.y, (a.x + b.x) / 2, (a.y + b.y) / 2);
      }
      ctx.stroke();
      ctx.restore();
      ctx.restore();
    }

    function drawSourceBreath(points, now, essence) {
      if (!essence || !points || points.length < 2) return;
      const source = points[0];
      const next = points[Math.min(2, points.length - 1)];
      const dx = next.x - source.x;
      const dy = next.y - source.y;
      const angle = Math.atan2(dy, dx);
      const pulse = (Math.sin(now * 0.0015) + 1) * 0.5;

      ctx.save();
      ctx.globalCompositeOperation = 'screen';
      for (let i = 0; i < 1; i++) {
        const phase = (pulse + i / 3) % 1;
        const radius = 8 + phase * 22;
        ctx.strokeStyle = `rgba(255, 194, 88, ${0.12 * (1 - phase)})`;
        ctx.lineWidth = 1.1;
        ctx.beginPath();
        ctx.arc(source.x, source.y, radius, 0, Math.PI * 2);
        ctx.stroke();
      }

      const fan = ctx.createLinearGradient(source.x, source.y, source.x + dx * 1.8, source.y + dy * 1.8);
      fan.addColorStop(0, 'rgba(255, 194, 88, 0.22)');
      fan.addColorStop(0.34, 'rgba(210, 244, 232, 0.11)');
      fan.addColorStop(1, 'rgba(160, 232, 244, 0)');
      ctx.fillStyle = fan;
      ctx.translate(source.x, source.y);
      ctx.rotate(angle);
      ctx.beginPath();
      ctx.moveTo(0, -8);
      ctx.quadraticCurveTo(38, -22, 92, -8);
      ctx.lineTo(92, 8);
      ctx.quadraticCurveTo(38, 22, 0, 8);
      ctx.closePath();
      ctx.fill();
      ctx.restore();
    }

    // PASS 12 - The Second Movement: a thirty-second reveal with four quiet acts.
    // The choreography changes emphasis, never evidence. It lets a human first notice,
    // then follow, then understand, then release the field back into uncertainty.
    function smoothstep(edge0, edge1, value) {
      const x = Math.max(0, Math.min(1, (value - edge0) / Math.max(0.0001, edge1 - edge0)));
      return x * x * (3 - 2 * x);
    }

    function secondMovement(now) {
      const cycleSeconds = 30;
      const t = (now / 1000) % cycleSeconds;
      const listen = 1 - smoothstep(2.0, 7.0, t) + smoothstep(27.0, 30.0, t);
      const awaken = smoothstep(2.0, 7.0, t) * (1 - smoothstep(10.0, 15.0, t));
      const converse = smoothstep(8.0, 14.0, t) * (1 - smoothstep(20.0, 25.0, t));
      const release = smoothstep(18.0, 24.0, t) * (1 - smoothstep(28.0, 30.0, t));
      return {
        listen: Math.max(0, Math.min(1, listen)),
        awaken: Math.max(0, Math.min(1, awaken)),
        converse: Math.max(0, Math.min(1, converse)),
        release: Math.max(0, Math.min(1, release)),
      };
    }

    function withAtmosphericWeight(weight, drawFn) {
      if (weight <= 0.005) return;
      ctx.save();
      ctx.globalAlpha *= Math.max(0, Math.min(1, weight));
      drawFn();
      ctx.restore();
    }

    function drawBody(rect, now) {
      const points = mapReady ? screenPath() : [];
      if (points.length >= 2) {
        const essence = document.body.classList.contains('disclosure-overview');
        if (essence) {
          // PASS 12: the visual field unfolds like a second movement rather than arriving all at once.
          const movement = secondMovement(now);
          // PASS 14 - Addition by Subtraction.
          // The terrain carries the meaning; atmosphere appears only where it improves understanding.
          withAtmosphericWeight(0.10 + movement.listen * 0.12 + movement.release * 0.06, () => drawAmbientAir(now, true));
          withAtmosphericWeight(0.10 + movement.awaken * 0.22 + movement.converse * 0.14, () => drawTerrainReveal(points, true));
          withAtmosphericWeight(0.34 + movement.awaken * 0.46 + movement.converse * 0.34 + movement.release * 0.10, () => drawTerrainNarration(now, true));
          withAtmosphericWeight(0.018 + movement.converse * 0.10 + movement.release * 0.05, () => drawPossibilityField(now, true));
          // PASS 18: the single earned breath now exposes terrain behavior directly.
          drawTerrainShapedBreath(points, now, true, movement);
          withAtmosphericWeight(0.12 + movement.listen * 0.08 + movement.awaken * 0.16, () => drawSourceBreath(points, now, true));
        } else {
          drawVolumeLayer(points, 0.19 * uncertaintyExpansion, hazeOpacity, verticalOffset, 18);
          drawVolumeLayer(points, 0.115 * channelCompression, midOpacity, verticalOffset * 0.35, 10);
          drawVolumeLayer(points, 0.055, coreOpacity, -verticalOffset * 0.25, 4);
          drawVolumeLayer(points, 0.022, coreOpacity * 0.72, -verticalOffset * 0.55, 1.5);
        }
      } else {
        ctx.save();
        ctx.globalCompositeOperation = 'screen';
        const grad = ctx.createRadialGradient(rect.width * .34, rect.height * .55, 10, rect.width * .52, rect.height * .54, rect.width * .40);
        grad.addColorStop(0, `rgba(166,244,236,${coreOpacity})`);
        grad.addColorStop(.42, `rgba(108,210,255,${midOpacity})`);
        grad.addColorStop(1, 'rgba(108,210,255,0)');
        ctx.fillStyle = grad;
        ctx.beginPath();
        ctx.ellipse(rect.width * .48, rect.height * .55, rect.width * .34, rect.height * .14, -0.08, 0, Math.PI * 2);
        ctx.fill();
        ctx.restore();
      }
    }

    function draw() {
      const rect = canvas.getBoundingClientRect();
      ctx.clearRect(0, 0, rect.width, rect.height);
      const now = performance.now();
      drawBody(rect, now);
      ctx.globalCompositeOperation = 'lighter';
      for (const p of particles) {
        const gustPulse = 1 + Math.sin((now % gustCycleMs) / gustCycleMs * Math.PI * 2 + p.phase) * gustStrength;
        const channelBand = advectionReady ? bandEnvelope(p.t, 'channeling') : 0;
        const shelterBand = advectionReady ? bandEnvelope(p.t, 'shelter') : 0;
        const oppositionBand = advectionReady ? bandEnvelope(p.t, 'opposition') : 0;
        const leeEnvelope = ridgeLeeReady ? rangeEnvelope(p.t, leeBand) : 0;
        const ridgeLeeSpeed = ridgeLeeReady ? (1 - leeEnvelope * (1 - leeSlowdown)) : 1;
        const focusEnvelope = terrainConvergenceReady ? rangeEnvelope(p.t, focusBand) : 0;
        const focusSpeed = terrainConvergenceReady ? (1 - focusEnvelope * (1 - focusSlowdown)) : 1;
        const dispersionEnvelope = terrainDivergenceReady ? rangeEnvelope(p.t, dispersionBand) : 0;
        const terrainDispersionSpeed = terrainDivergenceReady ? (1 + dispersionEnvelope * (dispersionSpeed - 1)) : 1;
        const terrainSpeed = (1 + channelBand * (channelSpeedMultiplier - 1) - shelterBand * (1 - shelterSpeedMultiplier) - oppositionBand * oppositionDrag) * ridgeLeeSpeed * focusSpeed * terrainDispersionSpeed;
        p.t += p.speed * orchestratedSpeed * Math.max(0.58, gustPulse * terrainSpeed);
        const jitter = Math.sin(Date.now() * (0.0007 + terrainTurbulence * 0.0012) + p.phase) * (0.00016 + terrainTurbulence * 0.00038);
        const t = Math.min(1, p.t + jitter);
        const pos = mapReady ? registeredPoint(t, p.lateral, p.wobble, p.responseSeed) : fallbackPoint(t, p.lateral, p.wobble);
        const fadeIn = Math.min(1, t / 0.12);
        const fadeOut = Math.max(0, 1 - t);
        const edgeFade = Math.pow(fadeOut, Number(airVolume.edge_falloff || 0.82));
        const gapWave = t > 0.58 ? Math.max(0.18, 1 - downstreamBreak * (0.45 + 0.55 * Math.sin(t * 38 + p.phase))) : 1;
        const essence = document.body.classList.contains('disclosure-overview');
        const confidenceFade = 1 - Math.max(0, t - 0.38) * (0.56 + downstreamBreak * 0.44);
        const fragmentWave = t > 0.46
          ? Math.max(0, Math.sin((t * 31) + p.phase * 1.7 + p.ageOffset * 8))
          : 1;
        const coherenceWindow = t < 0.42
          ? 1
          : Math.max(0.10, 1 - ((t - 0.42) / 0.58) * (0.55 + downstreamBreak * 0.28));
        const fragmentGate = t > 0.55 && p.responseSeed > (0.58 + evidenceStrength * 0.22)
          ? fragmentWave * coherenceWindow
          : coherenceWindow;
        const baseAlpha = fadeIn * edgeFade * evidenceStrength * gapWave * confidenceFade * fragmentGate;
        const alpha = Math.min(essence ? 0.045 : 0.26, baseAlpha * (essence ? 0.045 : 0.26));
        const radius = p.size * (1 + t * scaleGrowth * (essence ? 0.34 : 1)) * (0.72 + coherenceWindow * 0.14);
        const layerLift = Math.sin(p.phase) * verticalOffset * (0.25 + t * 0.55);
        pos.y -= layerLift;

        if (essence && p.previousX !== null && alpha > 0.007) {
          // Fine directional traces reveal a living field; fragmentation carries uncertainty.
          ctx.save();
          ctx.globalCompositeOperation = 'lighter';
          const warm = Math.max(0, 1 - t / 0.16);
          const red = Math.round(174 + warm * 70);
          const green = Math.round(239 - warm * 32);
          const blue = Math.round(246 - warm * 128);
          ctx.strokeStyle = `rgba(${red}, ${green}, ${blue}, ${alpha * 0.78})`;
          ctx.lineWidth = Math.max(0.28, radius * (0.12 + coherenceWindow * 0.035));
          ctx.lineCap = 'round';
          ctx.shadowBlur = 2 + t * 4;
          ctx.shadowColor = `rgba(${red}, ${green}, ${blue}, ${alpha * 0.42})`;
          ctx.beginPath();
          ctx.moveTo(p.previousX, p.previousY);
          ctx.lineTo(pos.x, pos.y);
          ctx.stroke();
          ctx.restore();
        }

        ctx.beginPath();
        const warm = Math.max(0, 1 - t / 0.18);
        const dotRed = Math.round(178 + warm * 70);
        const dotGreen = Math.round(239 - warm * 36);
        const dotBlue = Math.round(248 - warm * 138);
        ctx.shadowBlur = (essence ? 1.5 : 8) + t * (essence ? 2.5 : 12);
        ctx.shadowColor = `rgba(${dotRed}, ${dotGreen}, ${dotBlue}, ${alpha * 0.42})`;
        ctx.fillStyle = `rgba(${dotRed}, ${dotGreen}, ${dotBlue}, ${alpha * (essence ? 0.08 : 1)})`;
        ctx.arc(pos.x, pos.y, radius * (essence ? 0.16 : 1), 0, Math.PI * 2);
        ctx.fill();
        p.previousX = pos.x;
        p.previousY = pos.y;
        if (p.t > 1 || pos.x < -80 || pos.x > rect.width + 80 || pos.y < -80 || pos.y > rect.height + 80) Object.assign(p, randParticle(false));
      }
      requestAnimationFrame(draw);
    }

    function adoptMap(candidate) { map = candidate || window.__AW_MAP__ || null; mapReady = !!map; }
    resize();
    window.addEventListener('resize', resize);
    window.addEventListener('aw:map-ready', (evt) => adoptMap(evt.detail?.map));
    window.addEventListener('aw:map-change', () => adoptMap(window.__AW_MAP__));
    window.addEventListener('aw:map-unavailable', () => { mapReady = false; });
    setTimeout(() => adoptMap(window.__AW_MAP__), 450);
    draw();
  }
  window.addEventListener('DOMContentLoaded', initPlume);
})();
