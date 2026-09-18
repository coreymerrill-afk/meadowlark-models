(function (global) {
  'use strict';

  const THREE_UMD_JSDELIVR = 'https://cdn.jsdelivr.net/npm/three@0.149.0/build/three.min.js';
  const THREE_UMD_UNPKG = 'https://unpkg.com/three@0.149.0/build/three.min.js';
  const OC_UMD_JSDELIVR = 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/controls/OrbitControls.js';
  const OC_UMD_UNPKG = 'https://unpkg.com/three@0.128.0/examples/js/controls/OrbitControls.js';
  const THREE_ESM_MAP = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
  const OC_ESM_MAP = 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';
  const THREE_ESM_SH = 'https://esm.sh/three@0.160.0';
  const OC_ESM_SH = 'https://esm.sh/three@0.160.0/examples/jsm/controls/OrbitControls.js';

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      const existing = document.querySelector('script[data-fly-src="' + src + '"]');
      if (existing) {
        if (existing.dataset.loaded === '1') return resolve();
        existing.addEventListener('load', function () { resolve(); });
        existing.addEventListener('error', function () { reject(new Error('Failed: ' + src)); });
        return;
      }
      const s = document.createElement('script');
      s.src = src;
      s.async = false;
      s.dataset.flySrc = src;
      s.onload = function () { s.dataset.loaded = '1'; resolve(); };
      s.onerror = function () { reject(new Error('Failed to load ' + src)); };
      document.head.appendChild(s);
    });
  }

  function resolveOrbitControls() {
    if (!window.THREE) return null;
    if (window.THREE.OrbitControls) return window.THREE.OrbitControls;
    if (typeof window.OrbitControls === 'function') {
      window.THREE.OrbitControls = window.OrbitControls;
      return window.OrbitControls;
    }
    return null;
  }

  function umdSuccess(via) {
    const OC = resolveOrbitControls();
    if (window.THREE && OC) return { THREE: window.THREE, OrbitControls: OC, via: via };
    return null;
  }

  async function tryUmdPair(threeSrc, ocSrc, via) {
    await loadScript(threeSrc);
    await loadScript(ocSrc);
    const hit = umdSuccess(via);
    if (hit) return hit;
    throw new Error('UMD loaded but OrbitControls missing (' + via + ')');
  }

  function ensureThreeImportMap() {
    if (document.querySelector('script[type="importmap"]')) return;
    const s = document.createElement('script');
    s.type = 'importmap';
    s.textContent = JSON.stringify({ imports: { three: THREE_ESM_MAP } });
    document.head.appendChild(s);
  }

  function joinVendor(base, file) {
    const cleaned = String(base || '/insect/vendor').replace(/\/$/, '');
    return cleaned + '/' + file;
  }

  function localVendorBases(opts) {
    const requested = String((opts && opts.vendorBase) || '/insect/vendor').replace(/\/$/, '');
    const bases = ['/insect/vendor'];
    if (requested && bases.indexOf(requested) === -1) bases.push(requested);
    // Last-ditch relative paths if someone opened the HTML from disk.
    if (bases.indexOf('vendor') === -1) bases.push('vendor');
    if (bases.indexOf('../vendor') === -1) bases.push('../vendor');
    return bases;
  }

  async function load(opts) {
    opts = opts || {};
    const label = opts.label || 'Flyer';
    const errors = [];
    const bases = localVendorBases(opts);
    let i;
    for (i = 0; i < bases.length; i++) {
      const base = bases[i];
      try {
        return await tryUmdPair(
          joinVendor(base, 'three.min.js'),
          joinVendor(base, 'OrbitControls.js'),
          'local-umd:' + base
        );
      } catch (e) {
        errors.push(e);
        console.warn('[' + label + '] local UMD failed (' + base + ')', e);
      }
    }
    try { return await tryUmdPair(THREE_UMD_JSDELIVR, OC_UMD_JSDELIVR, 'cdn-jsdelivr-umd'); }
    catch (e) { errors.push(e); console.warn('[' + label + '] jsDelivr UMD failed', e); }
    try { return await tryUmdPair(THREE_UMD_UNPKG, OC_UMD_UNPKG, 'cdn-unpkg-umd'); }
    catch (e) { errors.push(e); console.warn('[' + label + '] unpkg UMD failed', e); }
    try {
      // Dynamic import is the CDN ESM fallback (same as /x1 and /burrito); not a module graph import.
      ensureThreeImportMap();
      const THREE = await import(THREE_ESM_MAP);
      const mod = await import(OC_ESM_MAP);
      return { THREE: THREE, OrbitControls: mod.OrbitControls, via: 'esm-importmap-0.160' };
    } catch (e) { errors.push(e); console.warn('[' + label + '] importmap ESM failed', e); }
    try {
      const THREE = await import(THREE_ESM_SH);
      const mod = await import(OC_ESM_SH);
      return { THREE: THREE, OrbitControls: mod.OrbitControls, via: 'esm-sh-0.160' };
    } catch (esmErr) {
      errors.push(esmErr);
      const msg = errors.map(function (x) { return (x && x.message) ? x.message : String(x); }).join(' | ');
      throw new Error('Three.js failed (UMD + ESM): ' + msg);
    }
  }

  function showError(msg) {
    const el = document.getElementById('three-error');
    const loading = document.getElementById('three-loading');
    if (loading) loading.classList.add('hidden');
    if (!el) { console.error(msg); return; }
    el.classList.add('visible');
    el.innerHTML = '<strong>3D viewer failed to load</strong><br/>' +
      String(msg).replace(/</g, '&lt;') +
      '<br/><br/>Prefer opening with local <code>/insect/vendor/</code>, or allow CDN (jsdelivr/unpkg).';
  }

  global.MeadowlarkThree = { load: load, showError: showError };
})(window);
