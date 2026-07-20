(function () {
  function setLevel(level) {
    const valid = ['overview', 'context', 'audit'];
    if (!valid.includes(level)) level = 'overview';
    document.body.classList.remove('disclosure-overview', 'disclosure-context', 'disclosure-audit');
    document.body.classList.add('disclosure-' + level);
    window.dispatchEvent(new CustomEvent('aw:disclosure-level', { detail: { level: level } }));
    document.querySelectorAll('[data-disclosure-level]').forEach(function (button) {
      button.classList.toggle('active', button.dataset.disclosureLevel === level);
    });
  }
  window.addEventListener('DOMContentLoaded', function () {
    document.body.classList.add('scene-ready');
    // Every visit begins with the phenomenon. Deeper science is requested, never inherited.
    setLevel('overview');
    document.querySelectorAll('[data-disclosure-level]').forEach(function (button) {
      button.addEventListener('click', function () { setLevel(button.dataset.disclosureLevel); });
    });
  });
})();


(function(){
  function chooseQuality(){
    var reduced=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var cores=navigator.hardwareConcurrency||4;
    var memory=navigator.deviceMemory||4;
    if(reduced||cores<=2||memory<=2) return 'reduced';
    if(cores<=4||memory<=4) return 'balanced';
    return 'high';
  }
  function applyQuality(q){
    document.body.classList.remove('aw-quality-high','aw-quality-balanced','aw-quality-reduced');
    document.body.classList.add('aw-quality-'+q);
    var indicator=document.getElementById('performanceIndicator');
    if(indicator){ indicator.dataset.quality=q; indicator.querySelector('b').textContent='Adaptive scene · '+q; }
    window.dispatchEvent(new CustomEvent('aw:quality',{detail:{profile:q,maxDevicePixelRatio:q==='high'?1.75:(q==='balanced'?1.35:1)}}));
  }
  window.addEventListener('DOMContentLoaded',function(){
    applyQuality(chooseQuality());
    document.addEventListener('visibilitychange',function(){ document.body.classList.toggle('aw-scene-paused',document.hidden); });
  });
})();
