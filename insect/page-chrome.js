(function (global) {
  'use strict';

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

  function wireSchematicInit(opts) {
    opts = opts || {};
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
        vendorBase: opts.vendorBase || 'vendor',
        label: opts.label || 'Flyer'
      }).then(function (stack) {
        api = opts.boot(stack.THREE, stack.OrbitControls, stack.via);
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
    ensureThreeInit();
    return function () { return api; };
  }

  global.FlyerPage = {
    initTabs: initTabs,
    renderParts: renderParts,
    wireSchematicInit: wireSchematicInit
  };
})(window);
