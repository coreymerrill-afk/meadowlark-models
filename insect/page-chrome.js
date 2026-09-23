(function (global) {
  'use strict';

  function showMissingStack() {
    const loading = document.getElementById('three-loading');
    const err = document.getElementById('three-error');
    if (loading) loading.classList.add('hidden');
    if (!err) return;
    err.classList.add('visible');
    err.innerHTML = '<strong>3D viewer scripts did not load</strong><br/>' +
      'Need <code>/insect/three-stack.js</code> and <code>/insect/page-chrome.js</code>.';
  }

  function initTabs(onSchematicShow) {
    const mainEl = document.getElementById('main');
    const tabButtons = Array.prototype.slice.call(document.querySelectorAll('nav.tabs [role="tab"]'));
    const panels = {
      schematic: document.getElementById('panel-schematic'),
      nature: document.getElementById('panel-nature'),
      path: document.getElementById('panel-path')
    };

    function activateTab(tab, opts) {
      opts = opts || {};
      const id = tab.dataset.tab;
      tabButtons.forEach(function (btn) {
        const on = btn === tab;
        btn.setAttribute('aria-selected', on ? 'true' : 'false');
        btn.tabIndex = on ? 0 : -1;
      });
      Object.keys(panels).forEach(function (key) {
        const el = panels[key];
        const on = key === id;
        el.classList.toggle('active', on);
        el.setAttribute('aria-hidden', on ? 'false' : 'true');
        if ('inert' in el) el.inert = !on;
      });
      mainEl.classList.toggle('is-3d', id === 'schematic');
      document.body.classList.toggle('is-schematic', id === 'schematic');
      mainEl.scrollTop = 0;
      if (id === 'schematic' && typeof onSchematicShow === 'function') onSchematicShow();
      if (opts.focus) tab.focus();
    }

    const tablist = document.querySelector('nav.tabs');
    tablist.addEventListener('keydown', function (ev) {
      const current = document.activeElement;
      const i = tabButtons.indexOf(current);
      if (i < 0) return;
      let next = -1;
      switch (ev.key) {
        case 'ArrowRight':
        case 'ArrowDown':
          next = (i + 1) % tabButtons.length;
          break;
        case 'ArrowLeft':
        case 'ArrowUp':
          next = (i - 1 + tabButtons.length) % tabButtons.length;
          break;
        case 'Home':
          next = 0;
          break;
        case 'End':
          next = tabButtons.length - 1;
          break;
        default: {
          const _exhaustive = ev.key;
          void _exhaustive;
          return;
        }
      }
      ev.preventDefault();
      ev.stopPropagation();
      activateTab(tabButtons[next], { focus: true });
    });
    tabButtons.forEach(function (btn) {
      btn.addEventListener('click', function () { activateTab(btn, { focus: true }); });
    });
    document.body.classList.toggle('is-schematic', mainEl.classList.contains('is-3d'));
    return { activateTab: activateTab };
  }

  function renderParts(PARTS, getApi) {
    const listEl = document.getElementById('part-list');
    PARTS.forEach(function (p) {
      const card = document.createElement('button');
      card.type = 'button';
      card.className = 'part-card';
      card.dataset.id = p.id;
      card.innerHTML = '<strong>' + p.name + '</strong><span class="muted">' + p.detail.split('.')[0] + '.</span>';
      listEl.appendChild(card);
      card.addEventListener('click', function () {
        const api = getApi();
        if (api) api.selectPart(p.id);
      });
    });
  }

  function measureWrap(wrap) {
    let w = wrap.clientWidth || 0;
    let h = wrap.clientHeight || 0;
    if (w < 8 || h < 8) {
      const rect = wrap.getBoundingClientRect();
      w = Math.max(w, Math.round(rect.width));
      h = Math.max(h, Math.round(rect.height));
    }
    if (w < 8) w = Math.max(320, window.innerWidth - 24);
    if (h < 8) h = Math.max(240, Math.round(window.innerHeight * 0.48));
    return { w: w, h: h };
  }

  function applyPortraitFov(camera, width, height, deskFov, phoneFov) {
    camera.fov = (width / height < 0.85) ? (phoneFov || 54) : (deskFov || 40);
  }

  function sizeCanvas(wrap, camera, renderer, deskFov, phoneFov) {
    const size = measureWrap(wrap);
    applyPortraitFov(camera, size.w, size.h, deskFov, phoneFov);
    camera.aspect = size.w / size.h;
    camera.updateProjectionMatrix();
    renderer.setSize(size.w, size.h, false);
    return size;
  }

  function wireExpand(getApi) {
    function relayout() {
      const api = typeof getApi === 'function' ? getApi() : null;
      if (api && typeof api.resize === 'function') api.resize();
    }
    function enterFs3d() {
      document.body.classList.add('fs-3d');
      const hud = document.getElementById('fs-hud');
      if (hud) hud.hidden = false;
      requestAnimationFrame(function () {
        relayout();
        requestAnimationFrame(relayout);
      });
      setTimeout(relayout, 80);
    }
    function exitFs3d() {
      document.body.classList.remove('fs-3d');
      const hud = document.getElementById('fs-hud');
      if (hud) hud.hidden = true;
      requestAnimationFrame(function () {
        relayout();
        requestAnimationFrame(relayout);
      });
      setTimeout(relayout, 80);
    }
    const btnExpand = document.getElementById('btn-expand');
    if (btnExpand) btnExpand.addEventListener('click', enterFs3d);
    const btnFsClose = document.getElementById('btn-fs-close');
    if (btnFsClose) btnFsClose.addEventListener('click', exitFs3d);
    document.addEventListener('keydown', function (ev) {
      if (ev.key !== 'Escape') return;
      if (document.body.classList.contains('fs-3d')) {
        exitFs3d();
        ev.preventDefault();
      }
    });
  }

  function observeWrap(wrap, onResize) {
    if (!wrap || typeof onResize !== 'function') return;
    window.addEventListener('resize', onResize);
    window.addEventListener('orientationchange', function () {
      setTimeout(onResize, 80);
      setTimeout(onResize, 250);
    });
    if (typeof ResizeObserver === 'function') {
      const ro = new ResizeObserver(function () { onResize(); });
      ro.observe(wrap);
    }
  }

  function wireSchematicInit(opts) {
    opts = opts || {};
    if (!global.MeadowlarkThree) {
      showMissingStack();
      return function () { return null; };
    }

    let threeInitStarted = false;
    let api = null;

    function relayout() { if (api) api.resize(); }

    function ensureThreeInit() {
      if (threeInitStarted) {
        relayout();
        return;
      }
      threeInitStarted = true;
      MeadowlarkThree.load({
        vendorBase: opts.vendorBase || '/vendor',
        label: opts.label || 'Flyer'
      }).then(function (stack) {
        api = opts.boot(stack.THREE, stack.OrbitControls, stack.via);
        const wrap = document.getElementById('canvas-wrap');
        observeWrap(wrap, relayout);
        requestAnimationFrame(function () {
          relayout();
          requestAnimationFrame(relayout);
        });
        setTimeout(relayout, 80);
      }).catch(function (err) {
        MeadowlarkThree.showError(err && err.message ? err.message : String(err));
      });
    }

    initTabs(function () {
      ensureThreeInit();
      requestAnimationFrame(function () {
        relayout();
        requestAnimationFrame(relayout);
      });
      setTimeout(relayout, 80);
    });
    renderParts(opts.parts, function () { return api; });
    wireExpand(function () { return api; });
    ensureThreeInit();
    return function () { return api; };
  }

  function tuneRenderer(renderer) {
    const coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, coarse ? 1.75 : 2));
  }

  function tuneControls(THREE, controls) {
    controls.enableDamping = true;
    controls.dampingFactor = 0.1;
    if ('screenSpacePanning' in controls) controls.screenSpacePanning = true;
    if ('enableKeys' in controls) controls.enableKeys = false;
    if (THREE.TOUCH) {
      controls.touches.ONE = THREE.TOUCH.ROTATE;
      controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;
    }
  }

  global.FlyerPage = {
    initTabs: initTabs,
    renderParts: renderParts,
    wireSchematicInit: wireSchematicInit,
    tuneRenderer: tuneRenderer,
    tuneControls: tuneControls,
    applyPortraitFov: applyPortraitFov,
    measureWrap: measureWrap,
    sizeCanvas: sizeCanvas,
    observeWrap: observeWrap,
    wireExpand: wireExpand,
    showMissingStack: showMissingStack
  };
})(window);
