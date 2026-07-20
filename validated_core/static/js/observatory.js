(function(){
  const state={map:null,scene:null,ctx:null,canvas:null,path:[],source:null,start:0,raf:0,reduced:false,stage:0,stageStarted:0,timers:[],conversationTimers:[],minuteTimers:[],chapelTimer:0,minuteStarted:0,minutePhase:0,annotationU:.24};
  function markLoaded(){document.body.classList.add('map-loaded');}
  function text(id,value){const el=document.getElementById(id);if(el&&value)el.textContent=value;}
  function applyLiveScene(scene){
    const integrated=(scene&&scene.integrated_terrain_response)||{};
    const terrain=(scene&&scene.terrain_confidence)||{};
    const wind=(scene&&scene.wind)||{};
    const missing=(scene&&scene.missing_evidence)||{};
    text('observationStatus',integrated.display_label||'Integrated response remains evidence-limited');
    text('supportedBy',`${terrain.display_label||'Terrain confidence unavailable'} terrain · ${(wind.data_state||'wind context unavailable').replaceAll('_',' ')}`);
    text('stillUnknown',missing.display_label||'Unresolved evidence remains visible');
    const missingCount=Number(missing.missing_count||0);
    const terrainReady=Boolean(terrain.overall_score>0&&terrain.coverage_status&&terrain.coverage_status!=='unresolved');
    const eventWindReady=wind.data_state&& !['default_vector_fallback','wind_unavailable'].includes(wind.data_state);
    const judgment=(terrainReady&&eventWindReady&&missingCount<=2)?'Proceed with bounded interpretation.':'Hold the conclusion.';
    const judgmentReason=(judgment==='Hold the conclusion.')
      ?'The scene supports a direction for review, not a finding.'
      :'The available layers align, but the claim remains limited to the evidence shown.';
    text('chapelJudgment',judgment);
    text('chapelReason',judgmentReason);
    text('chapelJudgmentState',judgment==='Hold the conclusion.'?'Unresolved':'Bounded support');
    text('chapelSupported',`${terrain.display_label||'Terrain confidence unavailable'} and ${(wind.label||'available wind context').toLowerCase()}.`);
    text('chapelMissing',missing.display_label||'Unresolved evidence remains visible.');
    text('chapelAlternative','The observation-time atmosphere may differ from the current contextual reconstruction.');
    text('chapelNextAct',missingCount>0?'Inspect the missing inputs, observation record, and source trail before drawing a conclusion.':'Compare the aligned evidence and preserve the stated claim boundary.');
    text('observationExplanation',`Measured terrain is read against ${(wind.label||'available wind context').toLowerCase()}. The visible field is a reconstruction for human review, not direct methane detection.`);
    document.body.dataset.powerState=(scene&&scene.full_dem&&scene.full_dem.data_state==='continuous_dem_cache'&&integrated.data_state==='integrated_terrain_response_cache')?'ready':'limited';
    state.scene=scene;project();
  }
  async function refreshPowerState(){
    for(let attempt=0;attempt<6;attempt++){
      try{
        const response=await fetch('/scene.json?refresh_terrain=0&refresh_dem=0',{cache:'no-store'});
        if(response.ok){
          const live=await response.json();
          applyLiveScene(live);
          if(document.body.dataset.powerState==='ready')return;
        }
      }catch(_){ }
      await new Promise(resolve=>setTimeout(resolve,1200));
    }
  }

  function parseScene(){const shell=document.querySelector('.observatory-shell');try{return shell?JSON.parse(shell.dataset.scene||'{}'):{};}catch(_){return {};}}
  function initAtlas(){
    const select=document.getElementById('observationCase');
    const door=document.getElementById('gatehouseDoor');
    const compact=document.getElementById('gatehouseCompact');
    if(select)select.addEventListener('change',function(){const id=encodeURIComponent(select.value);window.location.assign('/observatory?case='+id);});
    function refreshGatehouseLayout(){
      const open=!!(door&&door.open);
      document.body.classList.toggle('gatehouse-open',open);
      if(state.map){setTimeout(function(){state.map.invalidateSize({pan:false});project();positionFieldAnnotation();},460);}
    }
    if(door){door.addEventListener('toggle',refreshGatehouseLayout);refreshGatehouseLayout();}
    if(compact&&door){compact.addEventListener('click',function(){
      const isCompact=door.classList.toggle('is-compact');
      compact.setAttribute('aria-pressed',String(isCompact));
      compact.textContent=isCompact?'Full evidence':'Compact view';
    });}
  }
  function initReplay(){const button=document.getElementById('replayObservation');if(!button)return;button.addEventListener('click',function(){button.blur();beginFirstMinute();});}
  function geometryFrom(scene){return ((((scene||{}).basemap||{}).plume_geometry)||{});}
  function resize(){if(!state.canvas)return;const r=state.canvas.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,2);state.canvas.width=Math.max(1,Math.round(r.width*dpr));state.canvas.height=Math.max(1,Math.round(r.height*dpr));state.ctx.setTransform(dpr,0,0,dpr,0,0);}
  function project(){if(!state.map||!state.scene)return;const g=geometryFrom(state.scene),raw=[g.source].concat(g.centerline||[]).filter(p=>p&&Number.isFinite(+p.lat)&&Number.isFinite(+p.lon));state.path=raw.map(p=>state.map.latLngToContainerPoint([+p.lat,+p.lon]));state.source=state.path[0]||null;}
  function pointAt(t){const pts=state.path;if(pts.length<2)return null;const lens=[];let total=0;for(let i=1;i<pts.length;i++){const dx=pts[i].x-pts[i-1].x,dy=pts[i].y-pts[i-1].y,l=Math.hypot(dx,dy);lens.push(l);total+=l;}let target=Math.max(0,Math.min(1,t))*total;for(let i=0;i<lens.length;i++){if(target<=lens[i]){const q=lens[i]?target/lens[i]:0;return{x:pts[i].x+(pts[i+1].x-pts[i].x)*q,y:pts[i].y+(pts[i+1].y-pts[i].y)*q};}target-=lens[i];}return pts[pts.length-1];}
  function ease(t){t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);}
  function stageAmount(stage,now,duration){if(state.stage<stage)return 0;if(state.stage>stage)return 1;return ease((now-state.stageStarted)/duration);}
  function strokeBreath(ctx,phase,alpha,width,offset,visible){if(state.path.length<2||visible<=0)return;const segments=84;ctx.beginPath();for(let i=0;i<=segments;i++){const u=(i/segments)*visible,p=pointAt(u);if(!p)continue;const wav=Math.sin(u*15+phase*4.8+offset)*Math.sin(Math.PI*u)*6.2,p2=pointAt(Math.min(1,u+.006))||p,dx=p2.x-p.x,dy=p2.y-p.y,len=Math.hypot(dx,dy)||1,x=p.x-dy/len*wav,y=p.y+dx/len*wav;if(i===0)ctx.moveTo(x,y);else ctx.lineTo(x,y);}const grad=ctx.createLinearGradient(state.path[0].x,state.path[0].y,state.path[state.path.length-1].x,state.path[state.path.length-1].y);grad.addColorStop(0,'rgba(194,139,84,'+(alpha*.86)+')');grad.addColorStop(.22,'rgba(220,226,206,'+alpha+')');grad.addColorStop(.62,'rgba(170,216,207,'+(alpha*.76)+')');grad.addColorStop(1,'rgba(170,216,207,0)');ctx.strokeStyle=grad;ctx.lineWidth=width;ctx.lineCap='round';ctx.lineJoin='round';ctx.stroke();}
  function drawTerrainLantern(ctx,progress,alpha){
    if(state.path.length<2||progress<=0||alpha<=0)return;
    const head=pointAt(Math.min(.96,progress));
    if(!head)return;
    const radius=78+42*Math.sin(Math.PI*Math.min(1,progress));
    const glow=ctx.createRadialGradient(head.x,head.y,2,head.x,head.y,radius);
    glow.addColorStop(0,'rgba(221,211,181,'+(alpha*.24)+')');
    glow.addColorStop(.38,'rgba(180,204,191,'+(alpha*.12)+')');
    glow.addColorStop(1,'rgba(180,204,191,0)');
    ctx.fillStyle=glow;
    ctx.beginPath();ctx.arc(head.x,head.y,radius,0,Math.PI*2);ctx.fill();
    ctx.save();ctx.globalAlpha=alpha*.18;strokeBreath(ctx,progress*.12,.32,28,2.4,progress);ctx.restore();
  }
  function strokeLivingWisp(ctx,phase,alpha,width,start,end,offset,drift,breaks){
    if(state.path.length<2||alpha<=0||end<=start)return;
    const segments=58;
    let drawing=false;
    ctx.beginPath();
    for(let i=0;i<=segments;i++){
      const q=i/segments,u=start+(end-start)*q,p=pointAt(u);
      if(!p)continue;
      const gap=breaks&&((q>.34&&q<.43)||(q>.71&&q<.79));
      const breath=.58+.42*Math.sin((q+phase)*Math.PI*2);
      if(gap&&breath<.86){drawing=false;continue;}
      const p2=pointAt(Math.min(1,u+.008))||p,dx=p2.x-p.x,dy=p2.y-p.y,len=Math.hypot(dx,dy)||1;
      const lift=(Math.sin(u*18+phase*6+offset)*5.2+Math.sin(u*7-phase*3)*2.4)*Math.sin(Math.PI*q);
      const wander=drift*Math.sin((q+phase)*Math.PI*2)*Math.sin(Math.PI*q);
      const x=p.x-dy/len*(lift+wander),y=p.y+dx/len*(lift+wander);
      if(!drawing){ctx.moveTo(x,y);drawing=true;}else ctx.lineTo(x,y);
    }
    const a=Math.max(0,alpha*(.78+.22*Math.sin(phase*Math.PI*2)));
    ctx.strokeStyle='rgba(196,221,211,'+a+')';
    ctx.lineWidth=width;
    ctx.lineCap='round';
    ctx.lineJoin='round';
    ctx.stroke();
  }
  function draw(ts){if(!state.ctx||!state.canvas)return;if(!state.start)state.start=ts;const w=state.canvas.clientWidth,h=state.canvas.clientHeight;state.ctx.clearRect(0,0,w,h);const elapsed=(ts-state.start)/1000,cycle=(elapsed%22)/22,sourceReveal=state.reduced?1:stageAmount(1,ts,1400),firstReveal=state.reduced?1:stageAmount(2,ts,2200),fullReveal=state.reduced?1:stageAmount(3,ts,3600),minuteElapsed=state.minuteStarted?Math.max(0,(ts-state.minuteStarted)/1000):0,terrainReveal=state.reduced?1:Math.max(0,Math.min(1,(minuteElapsed-7)/20));state.ctx.save();state.ctx.globalCompositeOperation='screen';drawTerrainLantern(state.ctx,terrainReveal,.72*fullReveal);strokeBreath(state.ctx,cycle,.105*fullReveal,17,0,Math.min(1,.18+.82*fullReveal));strokeBreath(state.ctx,(cycle+.05)%1,.27*Math.max(firstReveal,.34*fullReveal),3.8,1.7,Math.min(1,.20+.80*Math.max(firstReveal,fullReveal)));strokeBreath(state.ctx,(cycle+.11)%1,.12*fullReveal,1.1,3.4,fullReveal);const living=fullReveal*(state.reduced?.55:1);strokeLivingWisp(state.ctx,(cycle+.02)%1,.11*living,1.15,.08,.58,.7,4.4,false);strokeLivingWisp(state.ctx,(cycle+.19)%1,.085*living,.9,.22,.77,2.1,7.2,true);strokeLivingWisp(state.ctx,(cycle+.37)%1,.065*living,.72,.46,.96,4.8,9.5,true);strokeLivingWisp(state.ctx,(cycle+.61)%1,.045*living,.55,.63,1,1.3,12.0,true);if(state.source&&sourceReveal>0){const pulse=state.reduced?.45:(.31+.14*Math.sin(elapsed*.72)),radius=19+7*sourceReveal,rg=state.ctx.createRadialGradient(state.source.x,state.source.y,1,state.source.x,state.source.y,radius);rg.addColorStop(0,'rgba(215,166,101,'+(pulse*.72*sourceReveal)+')');rg.addColorStop(.38,'rgba(185,152,95,'+(pulse*.30*sourceReveal)+')');rg.addColorStop(1,'rgba(185,152,95,0)');state.ctx.fillStyle=rg;state.ctx.beginPath();state.ctx.arc(state.source.x,state.source.y,radius,0,Math.PI*2);state.ctx.fill();}state.ctx.restore();if(!state.reduced)state.raf=requestAnimationFrame(draw);}
  function setStage(stage){state.stage=stage;state.stageStarted=performance.now();document.body.dataset.invitationStage=String(stage);if(state.reduced)draw(performance.now());}
  function whisper(message,visible=true){
    const box=document.getElementById('curatorWhisper');
    const line=document.getElementById('curatorWhisperText');
    if(!box||!line)return;
    if(message)line.textContent=message;
    box.classList.toggle('is-visible',visible);
  }
  function positionFieldAnnotation(){
    const box=document.getElementById('fieldAnnotation');
    if(!box||!state.map||!state.path.length)return;
    const p=pointAt(state.annotationU);
    if(!p)return;
    const windowEl=document.getElementById('sceneWindow');
    const width=windowEl?windowEl.clientWidth:0;
    const height=windowEl?windowEl.clientHeight:0;
    const left=Math.max(24,Math.min(width-285,p.x+18));
    const top=Math.max(115,Math.min(height-145,p.y-48));
    box.style.left=left+'px';
    box.style.top=top+'px';
  }
  function annotate(kicker,message,u,visible=true){
    const box=document.getElementById('fieldAnnotation');
    const kickerEl=document.getElementById('fieldAnnotationKicker');
    const textEl=document.getElementById('fieldAnnotationText');
    if(!box||!kickerEl||!textEl)return;
    if(Number.isFinite(u))state.annotationU=Math.max(.05,Math.min(.95,u));
    if(kicker)kickerEl.textContent=kicker;
    if(message)textEl.textContent=message;
    positionFieldAnnotation();
    box.classList.toggle('is-visible',visible);
  }
  function directionAnnotation(){
    const wind=(state.scene&&state.scene.wind)||{};
    const label=(wind.label||'Current wind context').replace(/\s*·\s*/g,' — ');
    return label+'. Direction is contextual, not observation-time proof.';
  }
  function terrainAnnotation(){
    const steering=(state.scene&&state.scene.terrain_steering_field)||{};
    const label=(steering.display_label||'Terrain-conditioned redirection').replace(/\s*·\s*current context only/gi,'').replace(/\s*·\s*/g,' — ');
    return label+'.';
  }
  function supportAnnotation(){
    const confidence=(state.scene&&state.scene.terrain_steering_confidence)||{};
    const label=(confidence.display_label||'Support weakens downstream').replace(/\s*·\s*/g,' — ');
    return label+'.';
  }
  function terrainPhrase(){
    const scene=state.scene||{};
    const steering=scene.terrain_steering_field||{};
    const label=(steering.display_label||'Terrain begins shaping the possible movement').replace(/\s*·\s*current context only/gi,'');
    return label.charAt(0).toUpperCase()+label.slice(1)+'.';
  }
  function uncertaintyPhrase(){
    const scene=state.scene||{};
    const regime=scene.terrain_regime_confidence||{};
    const integrated=scene.integrated_terrain_response||{};
    if(regime.display_label)return regime.display_label.replace(/\s*·\s*/g,' — ')+'.';
    if(integrated.display_label)return integrated.display_label.replace(/\s*·\s*/g,' — ')+'.';
    return 'Support weakens downstream; human review remains essential.';
  }
  const cinematicChapters={
    0:['I','The field waits'],
    1:['I','The reported source'],
    2:['II','Direction enters'],
    3:['III','Possible movement'],
    4:['IV','Terrain answers'],
    5:['V','Support grows thin'],
    6:['VI','Judgment remains human'],
    7:['VII','Evidence and limits'],
    8:['VIII','The observation remains open']
  };
  function setCinematicChapter(phase){
    const chapter=cinematicChapters[phase]||cinematicChapters[0];
    text('cinematicChapterNumber',chapter[0]);
    text('cinematicChapterTitle',chapter[1]);
  }
  function setMinutePhase(phase){
    state.minutePhase=phase;
    document.body.dataset.firstMinutePhase=String(phase);
    setCinematicChapter(phase);
  }
  function closeDoors(){
    for(const id of ['understandDoor','chapelDoor','gatehouseDoor']){const door=document.getElementById(id);if(door)door.open=false;}
    document.body.classList.remove('gatehouse-open');
    document.body.dataset.chapelReady='false';
  }
  function scheduleMinute(delay,fn){state.minuteTimers.push(setTimeout(fn,delay));}
  function beginFirstMinute(){
    state.timers.forEach(clearTimeout);state.timers=[];
    state.conversationTimers.forEach(clearTimeout);state.conversationTimers=[];
    state.minuteTimers.forEach(clearTimeout);state.minuteTimers=[];
    clearTimeout(state.chapelTimer);
    closeDoors();whisper('',false);annotate('','',.2,false);setStage(0);setMinutePhase(0);state.minuteStarted=performance.now();
    if(state.reduced){setStage(3);setMinutePhase(8);document.body.dataset.chapelReady='true';return;}
    scheduleMinute(2600,()=>{setMinutePhase(1);setStage(1);whisper((((state.scene||{}).scientific_personality||{}).phrases||{}).source||'A reported source enters the field of view.',true);});
    scheduleMinute(6500,()=>{setMinutePhase(2);setStage(2);whisper((((state.scene||{}).scientific_personality||{}).phrases||{}).direction||'Current wind offers direction, not proof.',true);annotate('Direction',directionAnnotation(),.24,true);});
    scheduleMinute(11200,()=>{setMinutePhase(3);setStage(3);whisper('The possible movement begins to discover the land.',true);annotate('Possible movement','The field is a reconstruction for review, not a detected plume.',.39,true);});
    scheduleMinute(17800,()=>{setMinutePhase(4);whisper((((state.scene||{}).scientific_personality||{}).phrases||{}).terrain||terrainPhrase(),true);annotate('Terrain response',terrainAnnotation(),.57,true);});
    scheduleMinute(27000,()=>{setMinutePhase(5);whisper((((state.scene||{}).scientific_personality||{}).phrases||{}).uncertainty||uncertaintyPhrase(),true);annotate('Evidence boundary',supportAnnotation(),.78,true);});
    scheduleMinute(36500,()=>{setMinutePhase(6);whisper((((state.scene||{}).scientific_personality||{}).phrases||{}).judgment||'A useful observation can remain unresolved.',true);annotate('Human review',((((state.scene||{}).scientific_personality||{}).phrases||{}).next_act||'Look again where the evidence becomes thin.'),.88,true);document.body.dataset.chapelReady='true';});
    scheduleMinute(46500,()=>{setMinutePhase(7);whisper('Understanding begins when the evidence and its limits are viewed together.',true);annotate('Follow the reasoning','Open the evidence only after you have watched the field.',.67,true);});
    scheduleMinute(57000,()=>{setMinutePhase(8);whisper('',false);annotate('','',.67,false);});
  }
  function initBreath(map,scene){state.map=map;state.scene=scene;state.canvas=document.getElementById('observatoryBreath');if(!state.canvas)return;state.ctx=state.canvas.getContext('2d');state.reduced=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;resize();project();beginFirstMinute();map.on('move zoom resize',function(){resize();project();positionFieldAnnotation();if(state.reduced)draw(performance.now());});window.addEventListener('resize',function(){resize();project();positionFieldAnnotation();});cancelAnimationFrame(state.raf);state.start=0;state.raf=requestAnimationFrame(draw);}
  window.addEventListener('aw:map-ready',function(event){markLoaded();refreshPowerState();const map=event.detail&&event.detail.map;if(!map)return;const scene=parseScene(),geometry=geometryFrom(scene),points=[geometry.source].concat(geometry.centerline||[]).filter(Boolean).map(p=>[p.lat,p.lon]);if(points.length>1){const bounds=L.latLngBounds(points);setTimeout(function(){map.fitBounds(bounds,{paddingTopLeft:[190,135],paddingBottomRight:[220,150],maxZoom:11.05,animate:false});setTimeout(function(){initBreath(map,scene);},140);},420);}else initBreath(map,scene);});
  window.addEventListener('aw:map-unavailable',function(){document.body.classList.add('map-fallback-active');});
  initAtlas();
  initReplay();
})();

// Legacy acceptance phrase preserved: A reported source enters the instrument.
