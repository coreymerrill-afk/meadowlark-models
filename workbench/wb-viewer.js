/* Workbench Gen-0 schematic viewer.
   Mobile-first: local UMD vendor → CDN UMD → importmap/esm.sh ESM fallback.
   Dynamic import is the CDN ESM fallback (same as /x1 /insect /burrito); not a module graph import.
*/
(function () {
  'use strict';

  const body = document.body;
  const KIND = body.getAttribute('data-module') || 'flat';
  const VENDOR = (body.getAttribute('data-vendor') || '/workbench/vendor/').replace(/\/?$/, '/');

  const THREE_LOCAL = VENDOR + 'three.min.js';
  const OC_LOCAL = VENDOR + 'OrbitControls.js';
  const THREE_UMD_JSDELIVR = 'https://cdn.jsdelivr.net/npm/three@0.149.0/build/three.min.js';
  const THREE_UMD_UNPKG = 'https://unpkg.com/three@0.149.0/build/three.min.js';
  const OC_UMD_JSDELIVR = 'https://cdn.jsdelivr.net/gh/mrdoob/three.js@r128/examples/js/controls/OrbitControls.js';
  const OC_UMD_UNPKG = 'https://unpkg.com/three@0.128.0/examples/js/controls/OrbitControls.js';
  const THREE_ESM_MAP = 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';
  const OC_ESM_MAP = 'https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/controls/OrbitControls.js';
  const THREE_ESM_SH = 'https://esm.sh/three@0.160.0';
  const OC_ESM_SH = 'https://esm.sh/three@0.160.0/examples/jsm/controls/OrbitControls.js';

  const PARTS = [
    { id: 'posts', name: 'Posts', detail: '4×4 lumber (about 3½ inches) at the four corners. Outer faces set the 36×36 inch size. About 29 inches of space between them.' },
    { id: 'top', name: 'Top', detail: '¾ inch plywood that holds weight. The top sits 38 inches off the floor — not 36. ½ inch plywood is only for plates the X1 can cut.' },
    { id: 'shelf', name: 'Shelf / brace', detail: 'A ¾ inch shelf and/or a diagonal brace so the table does not rack. Not a final lumber list.' },
    { id: 'latch', name: 'Snap + latch', detail: 'Same on all four sides. Two magnets per side snap the tables together; then two latches take the load. The first sits 12 inches below the top (about 26 inches off the floor) — not 18. The second is Design-reserved on the same line, typically 6–8 inches above or below (exact offset DRAFT).' },
    { id: 'casters', name: 'Wheels', detail: 'A locking caster under each post. About 3 inches tall as a starting guess. Brand is still open.' },
    { id: 'saw', name: 'DWS716XPS', detail: 'Stand-in for a DeWalt DWS716XPS. Base about 27.2 × 22.4 inches — fits the 29 inch opening, tight front-to-back. Removable inserts so a later saw can swap in. How far the head swings is still open.' }
  ];

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      const existing = document.querySelector('script[data-wb-src="' + src + '"]');
      if (existing) {
        if (existing.dataset.loaded === '1') return resolve();
        existing.addEventListener('load', function () { resolve(); });
        existing.addEventListener('error', function () { reject(new Error('Failed: ' + src)); });
        return;
      }
      const s = document.createElement('script');
      s.src = src;
      s.async = false;
      s.dataset.wbSrc = src;
      s.onload = function () { s.dataset.loaded = '1'; resolve(); };
      s.onerror = function () { reject(new Error('Failed to load ' + src)); };
      document.head.appendChild(s);
    });
  }

  function resolveOrbitControls() {
    if (!window.THREE) return null;
    if (window.THREE.OrbitControls) return window.THREE.OrbitControls;
    if (typeof window.OrbitControls === 'function') return window.OrbitControls;
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

  async function loadThreeStack() {
    const errors = [];
    try { return await tryUmdPair(THREE_LOCAL, OC_LOCAL, 'local-umd'); }
    catch (e) { errors.push(e); console.warn('[Workbench] local UMD failed', e); }
    try { return await tryUmdPair(THREE_UMD_JSDELIVR, OC_UMD_JSDELIVR, 'cdn-jsdelivr-umd'); }
    catch (e) { errors.push(e); console.warn('[Workbench] jsDelivr UMD failed', e); }
    try { return await tryUmdPair(THREE_UMD_UNPKG, OC_UMD_UNPKG, 'cdn-unpkg-umd'); }
    catch (e) { errors.push(e); console.warn('[Workbench] unpkg UMD failed', e); }
    try {
      ensureThreeImportMap();
      const THREE = await import(THREE_ESM_MAP);
      const mod = await import(OC_ESM_MAP);
      return { THREE: THREE, OrbitControls: mod.OrbitControls, via: 'esm-importmap-0.160' };
    } catch (e) { errors.push(e); console.warn('[Workbench] importmap ESM failed', e); }
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

  function showThreeError(msg) {
    const el = document.getElementById('three-error');
    const loading = document.getElementById('three-loading');
    if (loading) loading.classList.add('hidden');
    if (!el) { console.error(msg); return; }
    el.classList.add('visible');
    el.innerHTML = '<strong>3D viewer failed to load</strong><br/>' +
      String(msg).replace(/</g, '&lt;') +
      '<br/><br/>Prefer opening with local <code>/workbench/vendor/</code>, or allow CDN (jsdelivr/unpkg).';
  }

  const listEl = document.getElementById('part-list');
  PARTS.forEach(function (p) {
    if (p.id === 'saw' && KIND !== 'miter') return;
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'part-card';
    card.dataset.id = p.id;
    card.innerHTML = '<strong>' + p.name + '</strong><span class="muted">' + p.detail.split('.')[0] + '.</span>';
    listEl.appendChild(card);
    card.addEventListener('click', function () {
      if (api) api.selectPart(p.id);
    });
  });

  let api = null;

  loadThreeStack().then(function (stack) {
    api = boot(stack.THREE, stack.OrbitControls, stack.via);
    api.setModule(KIND);
  }).catch(function (err) {
    showThreeError(err && err.message ? err.message : String(err));
  });

  function boot(THREE, OrbitControls, via) {
    const loading = document.getElementById('three-loading');
    const wrap = document.getElementById('canvas-wrap');

    const OA = 36;
    const POST = 3.5;
    const TOP_AFF = 38;
    const TOP_THK = 0.75;
    const PLATE = 0.5;
    const CASTER_H = 3.25;
    const LATCH_AFF = 26;
    const POST_C = OA / 2 - POST / 2;
    const POST_H = TOP_AFF - TOP_THK - CASTER_H;
    const SAW_W = 22.4;
    const SAW_D = 27.2;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x16130c);
    scene.fog = new THREE.Fog(0x16130c, 90, 220);

    const camera = new THREE.PerspectiveCamera(40, 1, 0.5, 400);
    camera.position.set(58, 50, 64);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    if (renderer.outputColorSpace !== undefined && THREE.SRGBColorSpace) {
      renderer.outputColorSpace = THREE.SRGBColorSpace;
    }
    wrap.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 20, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.1;
    controls.minDistance = 28;
    controls.maxDistance = 160;
    controls.maxPolarAngle = Math.PI * 0.49;
    if ('enableKeys' in controls) controls.enableKeys = false;
    if (THREE.TOUCH) {
      controls.touches.ONE = THREE.TOUCH.ROTATE;
      controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;
    }

    scene.add(new THREE.AmbientLight(0xfff3d0, 0.46));
    const key = new THREE.DirectionalLight(0xffffff, 0.85);
    key.position.set(40, 70, 30);
    scene.add(key);
    scene.add(new THREE.HemisphereLight(0xffe8a3, 0x2a2010, 0.42));
    const rim = new THREE.DirectionalLight(0xf5b942, 0.38);
    rim.position.set(-40, 28, -20);
    scene.add(rim);

    const grid = new THREE.GridHelper(120, 40, 0x8a6a30, 0x2a2416);
    grid.position.y = 0.02;
    scene.add(grid);
    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(70, 48),
      new THREE.MeshStandardMaterial({ color: 0x1a1710, roughness: 0.95, metalness: 0.05 })
    );
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    const matPost = new THREE.MeshStandardMaterial({ color: 0x6b4f2a, roughness: 0.72, metalness: 0.08 });
    const matTop = new THREE.MeshStandardMaterial({ color: 0xd4b07a, roughness: 0.62, metalness: 0.05 });
    const matTopLite = new THREE.MeshStandardMaterial({ color: 0xe0c48a, roughness: 0.58, metalness: 0.05 });
    const matShelf = new THREE.MeshStandardMaterial({ color: 0xb08958, roughness: 0.7, metalness: 0.04 });
    const matBrace = new THREE.MeshStandardMaterial({ color: 0x8a6a40, roughness: 0.68, metalness: 0.06 });
    const matPlate = new THREE.MeshStandardMaterial({ color: 0xb8b4aa, roughness: 0.4, metalness: 0.45 });
    const matMagnet = new THREE.MeshStandardMaterial({
      color: 0xf5b942, roughness: 0.32, metalness: 0.55, emissive: 0x7a5208, emissiveIntensity: 0.35
    });
    const matMech = new THREE.MeshStandardMaterial({ color: 0x4a4e56, roughness: 0.35, metalness: 0.6 });
    const matCaster = new THREE.MeshStandardMaterial({ color: 0x2a2c30, roughness: 0.45, metalness: 0.4 });
    const matWheel = new THREE.MeshStandardMaterial({ color: 0x1a1a1c, roughness: 0.7, metalness: 0.15 });
    const matLock = new THREE.MeshStandardMaterial({ color: 0xf5b942, roughness: 0.4, metalness: 0.3 });
    const matGhost = new THREE.MeshStandardMaterial({
      color: 0xf5b942, roughness: 0.5, metalness: 0.1, transparent: true, opacity: 0.16
    });
    const matSawY = new THREE.MeshStandardMaterial({ color: 0xf4c430, roughness: 0.45, metalness: 0.2 });
    const matSawK = new THREE.MeshStandardMaterial({ color: 0x1c1c1e, roughness: 0.5, metalness: 0.25 });
    const matBlade = new THREE.MeshStandardMaterial({ color: 0xc0c6ce, roughness: 0.25, metalness: 0.7 });
    const matWell = new THREE.MeshStandardMaterial({
      color: 0x8a7348, roughness: 0.55, metalness: 0.08, transparent: true, opacity: 0.5
    });
    const matInsert = new THREE.MeshStandardMaterial({
      color: 0xc4b896, roughness: 0.5, metalness: 0.12, transparent: true, opacity: 0.85
    });

    function box(w, h, d, mat, x, y, z) {
      const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
      m.position.set(x || 0, y || 0, z || 0);
      return m;
    }

    const root = new THREE.Group();
    scene.add(root);
    const neighbor = new THREE.Group();
    neighbor.visible = false;
    scene.add(neighbor);

    const pickables = [];
    const labelSprites = [];
    let highlight = null;

    function tag(mesh, id) {
      mesh.userData.partId = id;
      pickables.push(mesh);
    }

    function makeLabel(text, x, y, z, scale) {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      canvas.width = 768;
      canvas.height = 192;
      ctx.fillStyle = 'rgba(28, 22, 10, 0.78)';
      ctx.fillRect(16, 16, 736, 160);
      ctx.font = '700 56px system-ui,sans-serif';
      ctx.fillStyle = '#fde68a';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(text, 384, 96);
      const tex = new THREE.CanvasTexture(canvas);
      if (tex.colorSpace !== undefined && THREE.SRGBColorSpace) tex.colorSpace = THREE.SRGBColorSpace;
      const spr = new THREE.Sprite(new THREE.SpriteMaterial({
        map: tex, transparent: true, depthTest: false, depthWrite: false
      }));
      spr.position.set(x, y, z);
      spr.scale.set(scale || 14, (scale || 14) * 0.28, 1);
      spr.renderOrder = 12;
      labelSprites.push(spr);
      root.add(spr);
      return spr;
    }

    function addBrace(parent, x0, y0, z0, x1, y1, z1, mat, id) {
      const dx = x1 - x0;
      const dy = y1 - y0;
      const dz = z1 - z0;
      const len = Math.sqrt(dx * dx + dy * dy + dz * dz);
      const m = new THREE.Mesh(new THREE.BoxGeometry(len, 1.5, 3.5), mat);
      m.position.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
      const dir = new THREE.Vector3(dx, dy, dz).normalize();
      m.quaternion.setFromUnitVectors(new THREE.Vector3(1, 0, 0), dir);
      tag(m, id);
      parent.add(m);
      return m;
    }

    function addCaster(parent, x, z) {
      const g = new THREE.Group();
      const plate = box(3.4, 0.28, 3.4, matCaster, 0, CASTER_H - 0.14, 0);
      tag(plate, 'casters');
      g.add(plate);
      const yoke = box(0.35, 1.4, 2.2, matCaster, 0, 1.4, 0);
      tag(yoke, 'casters');
      g.add(yoke);
      const wheel = new THREE.Mesh(new THREE.CylinderGeometry(1.5, 1.5, 1.05, 20), matWheel);
      wheel.rotation.x = Math.PI / 2;
      wheel.position.set(0, 1.5, 0);
      tag(wheel, 'casters');
      g.add(wheel);
      const lock = box(0.35, 0.7, 1.4, matLock, 1.15, 1.15, 0);
      lock.rotation.z = -0.45;
      tag(lock, 'casters');
      g.add(lock);
      g.position.set(x, 0, z);
      parent.add(g);
      return g;
    }

    function addLatchPad(parent, face) {
      const g = new THREE.Group();
      const upperMagY = TOP_AFF - TOP_THK - 2;
      const lowerMagY = 4;
      function addMag(y) {
        const mag = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, 0.22, 16), matMagnet);
        mag.rotation.x = Math.PI / 2;
        mag.position.set(0, y, PLATE / 2 + 0.1);
        tag(mag, 'latch');
        g.add(mag);
      }
      addMag(upperMagY);
      addMag(lowerMagY);
      const pad = box(4.2, 3.2, PLATE, matPlate, 0, LATCH_AFF, 0);
      tag(pad, 'latch');
      g.add(pad);
      const toggle = box(1.6, 0.55, 0.7, matMech, 0, LATCH_AFF - 0.7, PLATE / 2 + 0.25);
      tag(toggle, 'latch');
      g.add(toggle);
      const reservedY = LATCH_AFF - 7;
      const pad2 = box(4.2, 3.2, PLATE, matPlate, 0, reservedY, 0);
      tag(pad2, 'latch');
      g.add(pad2);
      const toggle2 = box(1.6, 0.55, 0.7, matMech, 0, reservedY - 0.7, PLATE / 2 + 0.25);
      tag(toggle2, 'latch');
      g.add(toggle2);
      const half = OA / 2 + PLATE / 2;
      switch (face) {
        case '+x':
          g.position.set(half, 0, 0);
          g.rotation.y = Math.PI / 2;
          break;
        case '-x':
          g.position.set(-half, 0, 0);
          g.rotation.y = -Math.PI / 2;
          break;
        case '+z':
          g.position.set(0, 0, half);
          break;
        case '-z':
          g.position.set(0, 0, -half);
          g.rotation.y = Math.PI;
          break;
        default: {
          const _exhaustive = face;
          throw new Error('Unknown latch face: ' + _exhaustive);
        }
      }
      parent.add(g);
      return g;
    }

    function addSaw(parent) {
      const g = new THREE.Group();
      const base = box(SAW_W, 2.2, SAW_D, matSawK, 0, 1.1, 0);
      tag(base, 'saw');
      g.add(base);
      const fence = box(SAW_W - 1, 3.2, 0.6, matSawK, 0, 3.6, -SAW_D / 2 + 5);
      tag(fence, 'saw');
      g.add(fence);
      const arm = box(3.2, 10, 3.6, matSawY, 0, 8.2, -1.2);
      tag(arm, 'saw');
      g.add(arm);
      const motor = new THREE.Mesh(new THREE.CylinderGeometry(2.4, 2.4, 4.2, 18), matSawY);
      motor.rotation.z = Math.PI / 2;
      motor.position.set(2.6, 10.2, 1.4);
      tag(motor, 'saw');
      g.add(motor);
      const blade = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 0.12, 32), matBlade);
      blade.rotation.z = Math.PI / 2;
      blade.position.set(-0.4, 8.4, 2.6);
      tag(blade, 'saw');
      g.add(blade);
      const handle = box(1.4, 1.1, 4.5, matSawK, 0, 13.4, -0.4);
      tag(handle, 'saw');
      g.add(handle);
      parent.add(g);
      return g;
    }

    function clearGroup(g) {
      const doomed = [];
      g.traverse(function (o) {
        if (o.geometry) doomed.push(o.geometry);
        if (o.material && o.material.map && o.material.map.dispose) doomed.push(o.material.map);
      });
      while (g.children.length) g.remove(g.children[0]);
      doomed.forEach(function (res) { res.dispose(); });
    }

    function buildFrame(parent, kind) {
      const corners = [
        [POST_C, POST_C], [POST_C, -POST_C], [-POST_C, POST_C], [-POST_C, -POST_C]
      ];
      corners.forEach(function (c) {
        const post = box(POST, POST_H, POST, matPost, c[0], CASTER_H + POST_H / 2, c[1]);
        tag(post, 'posts');
        parent.add(post);
        addCaster(parent, c[0], c[1]);
      });
      ['+x', '-x', '+z', '-z'].forEach(function (face) { addLatchPad(parent, face); });

      const topY = TOP_AFF - TOP_THK / 2;
      if (kind === 'miter') {
        const wingW = (OA - SAW_W) / 2;
        const lip = (OA - SAW_D) / 2;
        const left = box(wingW, TOP_THK, OA, matTop, -(OA / 2 - wingW / 2), topY, 0);
        tag(left, 'top');
        parent.add(left);
        const right = box(wingW, TOP_THK, OA, matTop, OA / 2 - wingW / 2, topY, 0);
        tag(right, 'top');
        parent.add(right);
        const back = box(SAW_W, TOP_THK, lip, matTop, 0, topY, OA / 2 - lip / 2);
        tag(back, 'top');
        parent.add(back);
        const front = box(SAW_W, TOP_THK, lip, matTop, 0, topY, -OA / 2 + lip / 2);
        tag(front, 'top');
        parent.add(front);
        const well = box(SAW_W - 0.2, 4.2, SAW_D - 0.2, matWell, 0, TOP_AFF - 2.4, 0);
        tag(well, 'top');
        parent.add(well);
        const insertL = box(0.7, 0.35, SAW_D - 1, matInsert, -SAW_W / 2 + 0.55, TOP_AFF - 0.2, 0);
        tag(insertL, 'top');
        parent.add(insertL);
        const insertR = box(0.7, 0.35, SAW_D - 1, matInsert, SAW_W / 2 - 0.55, TOP_AFF - 0.2, 0);
        tag(insertR, 'top');
        parent.add(insertR);
        const saw = addSaw(parent);
        saw.position.set(0, TOP_AFF - 4.6, 0);
      } else {
        const top = box(OA, TOP_THK, OA, kind === 'extension' ? matTopLite : matTop, 0, topY, 0);
        tag(top, 'top');
        parent.add(top);
        if (kind === 'flat') {
          const drawer = box(18, 4.5, 14, matShelf, 0, TOP_AFF - TOP_THK - 3.2, -6);
          tag(drawer, 'shelf');
          parent.add(drawer);
        }
      }

      const shelfY = 12;
      if (kind === 'flat') {
        const shelf = box(29, TOP_THK, 29, matShelf, 0, shelfY, 0);
        tag(shelf, 'shelf');
        parent.add(shelf);
        addBrace(parent, -POST_C + 1.2, CASTER_H + 4, POST_C - 1.9, POST_C - 1.2, TOP_AFF - 6, POST_C - 1.9, matBrace, 'shelf');
        addBrace(parent, POST_C - 1.2, CASTER_H + 4, -POST_C + 1.9, -POST_C + 1.2, TOP_AFF - 6, -POST_C + 1.9, matBrace, 'shelf');
      } else if (kind === 'extension') {
        [-8, 0, 8].forEach(function (x) {
          const slat = box(3.2, TOP_THK, 29, matShelf, x, shelfY, 0);
          tag(slat, 'shelf');
          parent.add(slat);
        });
        addBrace(parent, -POST_C + 1.2, CASTER_H + 4, POST_C - 1.9, POST_C - 1.2, TOP_AFF - 6, POST_C - 1.9, matBrace, 'shelf');
      } else if (kind === 'miter') {
        addBrace(parent, -POST_C + 1.2, CASTER_H + 4, POST_C - 1.9, POST_C - 1.2, TOP_AFF - 6, POST_C - 1.9, matBrace, 'shelf');
        const rearShelf = box(22, TOP_THK, 8, matShelf, 0, shelfY, 10);
        tag(rearShelf, 'shelf');
        parent.add(rearShelf);
      } else {
        const _exhaustive = kind;
        throw new Error('Unknown module: ' + _exhaustive);
      }
    }

    function rebuildLabels(kind) {
      labelSprites.slice().forEach(function (s) {
        root.remove(s);
        if (s.material && s.material.map) s.material.map.dispose();
        if (s.material) s.material.dispose();
      });
      labelSprites.length = 0;
      makeLabel('36×36 in', 0, TOP_AFF + 3.2, OA / 2 + 2, 16);
      makeLabel('38 in tall', -OA / 2 - 6, TOP_AFF, 0, 14);
      makeLabel('latch', OA / 2 + 6, LATCH_AFF + 3, 0, 12);
      if (kind === 'miter') {
        makeLabel('DWS716XPS', 0, TOP_AFF + 12, 0, 18);
        makeLabel('tight fit', 0, TOP_AFF + 7, SAW_D / 2 + 2, 14);
      }
      const tog = document.getElementById('tog-labels');
      const show = !tog || tog.checked;
      labelSprites.forEach(function (s) { s.visible = show; });
    }

    function buildGhost() {
      clearGroup(neighbor);
      const ghost = box(OA, TOP_AFF - 2, OA, matGhost, OA + 0.6, (TOP_AFF - 2) / 2 + 1, 0);
      neighbor.add(ghost);
      const pad = box(6, 4, 0.4, matMagnet, OA / 2 + 0.4, LATCH_AFF, 0);
      neighbor.add(pad);
    }

    function setModule(kind) {
      pickables.length = 0;
      clearGroup(root);
      buildFrame(root, kind);
      rebuildLabels(kind);
      buildGhost();
      highlight = new THREE.Mesh(
        new THREE.TorusGeometry(4, 0.12, 8, 40),
        new THREE.MeshBasicMaterial({ color: 0xf5b942, transparent: true, opacity: 0.9 })
      );
      highlight.rotation.x = Math.PI / 2;
      highlight.visible = false;
      root.add(highlight);
      selectPart(null);
    }

    function selectPart(id) {
      document.querySelectorAll('.part-card').forEach(function (el) {
        el.classList.toggle('selected', el.dataset.id === id);
      });
      const p = PARTS.find(function (x) { return x.id === id; });
      const detail = document.getElementById('sel-detail');
      if (p && highlight) {
        detail.classList.add('visible');
        document.getElementById('sel-title').textContent = p.name;
        document.getElementById('sel-body').textContent = p.detail;
        highlight.visible = true;
        const hits = pickables.filter(function (m) { return m.userData.partId === id; });
        if (hits.length) {
          const box3 = new THREE.Box3();
          hits.forEach(function (m) { box3.expandByObject(m); });
          const c = box3.getCenter(new THREE.Vector3());
          const size = box3.getSize(new THREE.Vector3());
          highlight.position.copy(c);
          highlight.scale.setScalar(Math.max(1.1, Math.max(size.x, size.z) * 0.22));
        }
      } else {
        detail.classList.remove('visible');
        if (highlight) highlight.visible = false;
      }
    }

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    wrap.addEventListener('pointerdown', function (ev) {
      if (ev.button !== 0) return;
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((ev.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((ev.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(pickables, true);
      if (hits.length) {
        let o = hits[0].object;
        while (o && o.userData.partId == null) o = o.parent;
        if (o && o.userData.partId) selectPart(o.userData.partId);
      }
    });

    function setView(pos, tgt) {
      camera.position.set(pos.x, pos.y, pos.z);
      controls.target.set(tgt.x, tgt.y, tgt.z);
      controls.update();
    }
    document.getElementById('btn-reset').onclick = function () {
      setView({ x: 58, y: 50, z: 64 }, { x: 0, y: 20, z: 0 });
      selectPart(null);
    };
    document.getElementById('btn-iso').onclick = function () {
      setView({ x: 62, y: 42, z: 62 }, { x: 0, y: 19, z: 0 });
    };
    document.getElementById('btn-top').onclick = function () {
      setView({ x: 0.4, y: 110, z: 0.2 }, { x: 0, y: 20, z: 0 });
    };
    document.getElementById('btn-side').onclick = function () {
      setView({ x: 0, y: 22, z: 90 }, { x: 0, y: 20, z: 0 });
    };
    document.getElementById('tog-labels').addEventListener('change', function (e) {
      labelSprites.forEach(function (s) { s.visible = e.target.checked; });
    });
    document.getElementById('tog-neighbor').addEventListener('change', function (e) {
      neighbor.visible = e.target.checked;
    });

    function resize() {
      const w = wrap.clientWidth || 1;
      const h = wrap.clientHeight || 1;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h, false);
    }
    window.addEventListener('resize', resize);
    window.addEventListener('orientationchange', function () {
      setTimeout(resize, 80);
      setTimeout(resize, 250);
    });
    if (typeof ResizeObserver === 'function') {
      const ro = new ResizeObserver(function () { resize(); });
      ro.observe(wrap);
    }
    resize();

    function enterFs3d() {
      document.body.classList.add('fs-3d');
      const hud = document.getElementById('fs-hud');
      if (hud) hud.hidden = false;
      requestAnimationFrame(function () {
        resize();
        requestAnimationFrame(resize);
      });
      setTimeout(resize, 80);
    }
    function exitFs3d() {
      document.body.classList.remove('fs-3d');
      const hud = document.getElementById('fs-hud');
      if (hud) hud.hidden = true;
      requestAnimationFrame(function () {
        resize();
        requestAnimationFrame(resize);
      });
      setTimeout(resize, 80);
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

    if (loading) {
      loading.textContent = 'Ready · Three via ' + via;
      setTimeout(function () { loading.classList.add('hidden'); }, 350);
    }

    function animate() {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    }
    requestAnimationFrame(animate);

    return { resize: resize, selectPart: selectPart, setModule: setModule };
  }
})();
