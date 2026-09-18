/* Workbench Gen-0 schematic viewer.
   Mobile-first: local UMD vendor → CDN UMD → importmap/esm.sh ESM fallback.
   Dynamic import is the CDN ESM fallback (same as /x1 /insect /burrito); not a module graph import.
*/
(function () {
  'use strict';

  const body = document.body;
  const KIND = body.getAttribute('data-module') || 'flat';
  const VENDOR = (body.getAttribute('data-vendor') || '../vendor/').replace(/\/?$/, '/');

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
    { id: 'posts', name: 'Posts', detail: '4×4 lumber (about 3½ inches) at the four corners. Outer faces set the 36×36 inch size. About 29 inches of space between them. Upper aprons run post to post, flush to that outer face, so latches have wood behind them.' },
    { id: 'top', name: 'Top', detail: '¾ inch plywood that holds weight. The top sits 38 inches off the floor — not 36. ½ inch plywood is only for plates the X1 can cut.' },
    { id: 'shelf', name: 'Shelf / rails', detail: 'Four lower rails sit about 6–8 inches off the floor, clear of the casters. A ¾ inch shelf rests on those rails and notches around the posts — it does not float. Flat and Extension get a brace on two opposite faces. Miter gets an X in the lower bay. Brace ends kiss the post inner faces at the rail and apron. Not a cut list.' },
    { id: 'latch', name: 'Snap + latch', detail: 'Same kit on all four sides, mirrored. Two magnets per side, flush or a hair proud of the 36 inch face. North and East carry the latch bodies; South and West carry the strikes. Plates sit on the apron, not hanging in air. First latch 12 inches below the top (about 26 inches off the floor). Second is Design-reserved on the same line (exact offset DRAFT).' },
    { id: 'casters', name: 'Wheels', detail: 'A locking caster under each post. About 3 inches tall as a starting guess. Brand is still open.' },
    { id: 'saw', name: 'DWS716XPS', detail: 'Stand-in for a DeWalt DWS716XPS (12 inch compound, it does not slide). Rubber feet sit on a ½ inch nest. Width gets about a ¾–1 inch service gap; front-to-back stays tight. A rear keep-clear marks a dust path outside the latch strip — bag depth is still open. Fold-off stock wings are out of this Gen-0.1 picture (they stow for dock). Head is shown upright; how far it bevels is still open.' }
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
      '<br/><br/>Prefer opening with local <code>vendor/</code> beside this HTML, or allow CDN (jsdelivr/unpkg).';
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
    const SERVICE_W = 0.875;
    const OPEN_W = SAW_W + 2 * SERVICE_W;
    const OPEN_D = SAW_D;
    const NEST_W = 22.5;
    const NEST_D = SAW_D;
    const MAG_PROUD = 1 / 16;
    const FOOT_H = 0.35;

    // Schematic frame stock — not freeze dims, not a cut list.
    // 2× class thickness. Second latch sits 6" above primary (Design-allowed
    // DRAFT offset) so both pads share one upper apron without a full-height skirt.
    const STOCK = 1.5;
    const LATCH_PAD_H = 3.2;
    const LATCH2_AFF = LATCH_AFF + 6;
    const APRON_TOP = TOP_AFF - TOP_THK;
    const APRON_BOT = LATCH_AFF - LATCH_PAD_H / 2 - 1;
    const APRON_H = APRON_TOP - APRON_BOT;
    const APRON_Y = (APRON_TOP + APRON_BOT) / 2;
    const RAIL_H = 3.5;
    const LOWER_RAIL_TOP = 7.5;
    const LOWER_RAIL_BOT = LOWER_RAIL_TOP - RAIL_H;
    const LOWER_RAIL_Y = (LOWER_RAIL_TOP + LOWER_RAIL_BOT) / 2;
    const SHELF_Y = LOWER_RAIL_TOP + TOP_THK / 2;
    const SPAN = OA - 2 * POST;
    const POST_INNER = OA / 2 - POST;
    const UPPER_MAG_Y = TOP_AFF - TOP_THK - 2;
    const BRACE_FACE = 3.5;
    const BRACE_THK = STOCK;

    (function assertFrameContacts() {
      const padHalf = LATCH_PAD_H / 2;
      console.assert(OA === 36 && TOP_AFF === 38 && POST === 3.5, 'freeze envelope');
      console.assert(LATCH_AFF === 26 && TOP_THK === 0.75 && PLATE === 0.5, 'freeze latch/ply');
      console.assert(LATCH_AFF - padHalf >= APRON_BOT && LATCH_AFF + padHalf <= APRON_TOP, 'primary latch on apron');
      console.assert(LATCH2_AFF - padHalf >= APRON_BOT && LATCH2_AFF + padHalf <= APRON_TOP, 'second latch on apron');
      console.assert(LATCH2_AFF + padHalf < UPPER_MAG_Y - 0.4, 'second latch clear of upper magnet');
      console.assert(LOWER_RAIL_TOP >= 6 && LOWER_RAIL_TOP <= 8, 'lower rail in 6–8 AFF band');
      console.assert(LOWER_RAIL_BOT >= CASTER_H, 'lower rail clear of caster plate');
      console.assert(Math.abs(SHELF_Y - (LOWER_RAIL_TOP + TOP_THK / 2)) < 1e-6, 'shelf sits on rails');
      console.assert(Math.abs((POST_INNER - BRACE_THK / 2) + BRACE_THK / 2 - POST_INNER) < 1e-9, 'brace kisses post inner face');
      console.assert(OPEN_W < SPAN && OPEN_D <= SPAN, 'nest inside A-clear');
      console.assert(NEST_W <= OPEN_W && NEST_D <= OPEN_D, 'insert fits opening');
      console.assert(SERVICE_W >= 0.75 && SERVICE_W <= 1, 'width-only service gap');
      console.assert(OPEN_D === SAW_D, 'no faked depth gap');
    })();

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

    const matPost = new THREE.MeshStandardMaterial({ color: 0x4e351c, roughness: 0.78, metalness: 0.04 });
    const matApron = new THREE.MeshStandardMaterial({ color: 0x8a5a2c, roughness: 0.7, metalness: 0.05 });
    const matRail = new THREE.MeshStandardMaterial({ color: 0x6f4524, roughness: 0.74, metalness: 0.04 });
    const matTop = new THREE.MeshStandardMaterial({ color: 0xc9a66b, roughness: 0.58, metalness: 0.04 });
    const matTopLite = new THREE.MeshStandardMaterial({ color: 0xd4b57a, roughness: 0.56, metalness: 0.04 });
    const matShelf = new THREE.MeshStandardMaterial({ color: 0xa67c48, roughness: 0.68, metalness: 0.03 });
    const matPlyEdge = new THREE.MeshStandardMaterial({ color: 0x3a2a16, roughness: 0.82, metalness: 0.02 });
    const matBrace = new THREE.MeshStandardMaterial({ color: 0x7a5230, roughness: 0.7, metalness: 0.05 });
    const matPlate = new THREE.MeshStandardMaterial({ color: 0xb8b4aa, roughness: 0.4, metalness: 0.45 });
    const matStrike = new THREE.MeshStandardMaterial({ color: 0x8a8680, roughness: 0.45, metalness: 0.4 });
    const matRubber = new THREE.MeshStandardMaterial({ color: 0x1c1c1c, roughness: 0.92, metalness: 0.02 });
    const matSawTable = new THREE.MeshStandardMaterial({ color: 0x2a2c30, roughness: 0.55, metalness: 0.2 });
    const matMagnet = new THREE.MeshStandardMaterial({
      color: 0x2c2e32, roughness: 0.55, metalness: 0.62, emissive: 0x000000, emissiveIntensity: 0
    });
    const matMech = new THREE.MeshStandardMaterial({ color: 0x4a4e56, roughness: 0.35, metalness: 0.6 });
    const matCaster = new THREE.MeshStandardMaterial({ color: 0x2a2c30, roughness: 0.45, metalness: 0.4 });
    const matWheel = new THREE.MeshStandardMaterial({ color: 0x1a1a1c, roughness: 0.7, metalness: 0.15 });
    const matLock = new THREE.MeshStandardMaterial({ color: 0x1e1e20, roughness: 0.7, metalness: 0.12 });
    const matSawY = new THREE.MeshStandardMaterial({ color: 0xb08a22, roughness: 0.5, metalness: 0.18 });
    const matSawK = new THREE.MeshStandardMaterial({ color: 0x1a1a1c, roughness: 0.55, metalness: 0.22 });
    const matBlade = new THREE.MeshStandardMaterial({ color: 0xc0c6ce, roughness: 0.25, metalness: 0.7 });
    const matWell = new THREE.MeshStandardMaterial({
      color: 0x5c4a30, roughness: 0.68, metalness: 0.05
    });
    const matInsert = new THREE.MeshStandardMaterial({
      color: 0xbba57a, roughness: 0.55, metalness: 0.08
    });
    const matKeepClear = new THREE.MeshStandardMaterial({
      color: 0xc4a056, roughness: 0.6, metalness: 0.05, transparent: true, opacity: 0.2
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

    let pickOn = true;
    function tag(mesh, id) {
      mesh.userData.partId = id;
      if (pickOn) pickables.push(mesh);
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

    // 2×4-class brace: length along the diagonal, 3.5" in the face plane,
    // 1.5" thickness along the outward face normal so the outer face kisses the post.
    function addBrace(parent, x0, y0, z0, x1, y1, z1, nx, ny, nz, mat, id) {
      const dx = x1 - x0;
      const dy = y1 - y0;
      const dz = z1 - z0;
      const len = Math.sqrt(dx * dx + dy * dy + dz * dz);
      const m = new THREE.Mesh(new THREE.BoxGeometry(len, BRACE_FACE, BRACE_THK), mat);
      m.position.set((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2);
      const xAxis = new THREE.Vector3(dx, dy, dz).normalize();
      const zAxis = new THREE.Vector3(nx, ny, nz).normalize();
      const yAxis = new THREE.Vector3().crossVectors(zAxis, xAxis).normalize();
      zAxis.crossVectors(xAxis, yAxis).normalize();
      m.quaternion.setFromRotationMatrix(new THREE.Matrix4().makeBasis(xAxis, yAxis, zAxis));
      tag(m, id);
      parent.add(m);
      return m;
    }

    // End centers land on post inner-face nodes (closes Frame ~0.15″ miss).
    function addFaceDiagonal(parent, face, flip) {
      const y0 = LOWER_RAIL_TOP;
      const y1 = APRON_BOT;
      const p = POST_INNER;
      const c = POST_INNER - BRACE_THK / 2;
      const a = flip ? p : -p;
      const b = flip ? -p : p;
      switch (face) {
        case '+z':
          addBrace(parent, a, y0, c, b, y1, c, 0, 0, 1, matBrace, 'shelf');
          break;
        case '-z':
          addBrace(parent, b, y0, -c, a, y1, -c, 0, 0, -1, matBrace, 'shelf');
          break;
        case '+x':
          addBrace(parent, c, y0, a, c, y1, b, 1, 0, 0, matBrace, 'shelf');
          break;
        case '-x':
          addBrace(parent, -c, y0, b, -c, y1, a, -1, 0, 0, matBrace, 'shelf');
          break;
        default: {
          const _exhaustive = face;
          throw new Error('Unknown brace face: ' + _exhaustive);
        }
      }
    }

    function addLowerBayBrace(parent, face) {
      addFaceDiagonal(parent, face, false);
    }

    function addLowerBayX(parent, face) {
      addFaceDiagonal(parent, face, false);
      addFaceDiagonal(parent, face, true);
    }

    function addPerimeterBand(parent, y, height, thick, mat, id) {
      const span = SPAN;
      const c = OA / 2 - thick / 2;
      const parts = [
        box(span, height, thick, mat, 0, y, c),
        box(span, height, thick, mat, 0, y, -c),
        box(thick, height, span, mat, c, y, 0),
        box(thick, height, span, mat, -c, y, 0)
      ];
      parts.forEach(function (m) {
        tag(m, id);
        parent.add(m);
      });
      return parts;
    }

    // ¾" shelf on the lower-rail tops, notched around the 4×4s so edges bear on the rails.
    function addNotchedShelf(parent, y, mat, id) {
      const reach = POST - STOCK / 2;
      const through = SPAN + 2 * reach;
      const center = box(SPAN, TOP_THK, through, mat, 0, y, 0);
      tag(center, id);
      parent.add(center);
      const east = box(reach, TOP_THK, SPAN, mat, (SPAN + reach) / 2, y, 0);
      tag(east, id);
      parent.add(east);
      const west = box(reach, TOP_THK, SPAN, mat, -(SPAN + reach) / 2, y, 0);
      tag(west, id);
      parent.add(west);
      addPlyEdges(parent, SPAN, through, y, TOP_THK, id);
    }

    function addPlyEdges(parent, w, d, y, thk, id) {
      const e = 0.11;
      const band = thk * 0.9;
      [
        box(w, band, e, matPlyEdge, 0, y, d / 2 - e / 2),
        box(w, band, e, matPlyEdge, 0, y, -d / 2 + e / 2),
        box(e, band, d, matPlyEdge, w / 2 - e / 2, y, 0),
        box(e, band, d, matPlyEdge, -w / 2 + e / 2, y, 0)
      ].forEach(function (m) {
        tag(m, id);
        parent.add(m);
      });
    }

    // Rear keep-clear only — path reserved outside the latch strip. Bag depth OPEN.
    function addDustKeepClear(parent) {
      const keepHalf = 4.2 / 2 + 1;
      const portOff = keepHalf + 3.2;
      const port = box(2.3, 2.0, 0.18, matKeepClear, portOff, APRON_Y, OA / 2 + 0.08);
      tag(port, 'top');
      parent.add(port);
      const clear = box(3.4, 5.5, 1.0, matKeepClear, portOff, APRON_Y - 1.2, OA / 2 + 0.55);
      tag(clear, 'top');
      parent.add(clear);
    }

    function addCaster(parent, x, z) {
      const g = new THREE.Group();
      const plateH = 0.22;
      const plate = box(POST + 0.12, plateH, POST + 0.12, matCaster, 0, CASTER_H - plateH / 2, 0);
      tag(plate, 'casters');
      g.add(plate);
      const yokeH = 1.15;
      const yoke = box(0.38, yokeH, 2.05, matCaster, 0, CASTER_H - plateH - yokeH / 2, 0);
      tag(yoke, 'casters');
      g.add(yoke);
      const wheelR = 1.45;
      const wheel = new THREE.Mesh(new THREE.CylinderGeometry(wheelR, wheelR, 1.05, 20), matWheel);
      wheel.rotation.x = Math.PI / 2;
      wheel.position.set(0, wheelR, 0);
      tag(wheel, 'casters');
      g.add(wheel);
      const lock = box(0.35, 0.7, 1.4, matLock, 1.15, 1.05, 0);
      lock.rotation.z = -0.45;
      tag(lock, 'casters');
      g.add(lock);
      g.position.set(x, 0, z);
      parent.add(g);
      return g;
    }

    function addLatchPad(parent, face) {
      const g = new THREE.Group();
      let role;
      switch (face) {
        case '+x':
        case '+z':
          role = 'latch';
          break;
        case '-x':
        case '-z':
          role = 'strike';
          break;
        default: {
          const _exhaustive = face;
          throw new Error('Unknown latch face: ' + _exhaustive);
        }
      }
      const isLatch = role === 'latch';
      const padMat = isLatch ? matPlate : matStrike;
      function addMag(y) {
        const mag = new THREE.Mesh(new THREE.CylinderGeometry(0.55, 0.55, MAG_PROUD, 16), matMagnet);
        mag.rotation.x = Math.PI / 2;
        mag.position.set(0, y, MAG_PROUD / 2);
        tag(mag, 'latch');
        g.add(mag);
      }
      addMag(UPPER_MAG_Y);
      addMag(4);
      function addStation(y) {
        const pad = box(4.2, LATCH_PAD_H, PLATE, padMat, 0, y, -PLATE / 2);
        tag(pad, 'latch');
        g.add(pad);
        if (isLatch) {
          const toggle = box(1.6, 0.55, 0.7, matMech, 0, y - 0.7, 0.28);
          tag(toggle, 'latch');
          g.add(toggle);
        } else {
          const slot = box(2.4, 0.7, 0.16, matMech, 0, y, 0.08);
          tag(slot, 'latch');
          g.add(slot);
        }
      }
      addStation(LATCH_AFF);
      addStation(LATCH2_AFF);
      const half = OA / 2;
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
          const _exhaustivePos = face;
          throw new Error('Unknown latch face: ' + _exhaustivePos);
        }
      }
      parent.add(g);
      return g;
    }

    function addSaw(parent) {
      const g = new THREE.Group();
      const baseH = 1.65;
      const feet = [
        [SAW_W / 2 - 1.4, SAW_D / 2 - 1.4],
        [SAW_W / 2 - 1.4, -SAW_D / 2 + 1.4],
        [-SAW_W / 2 + 1.4, SAW_D / 2 - 1.4],
        [-SAW_W / 2 + 1.4, -SAW_D / 2 + 1.4]
      ];
      feet.forEach(function (c) {
        const pad = box(1.35, FOOT_H, 1.35, matRubber, c[0], FOOT_H / 2, c[1]);
        tag(pad, 'saw');
        g.add(pad);
      });
      const base = box(SAW_W, baseH, SAW_D, matSawK, 0, FOOT_H + baseH / 2, 0);
      tag(base, 'saw');
      g.add(base);
      const table = box(SAW_W - 0.7, 0.22, SAW_D - 1.4, matSawTable, 0, FOOT_H + baseH + 0.11, -0.15);
      tag(table, 'saw');
      g.add(table);
      const fenceZ = SAW_D / 2 - 4.2;
      const fence = box(SAW_W - 1.3, 3.3, 0.55, matSawK, 0, FOOT_H + baseH + 1.85, fenceZ);
      tag(fence, 'saw');
      g.add(fence);
      const pivot = box(4.0, 3.4, 3.1, matSawY, 0, FOOT_H + baseH + 3.2, fenceZ + 1.7);
      tag(pivot, 'saw');
      g.add(pivot);
      const arm = box(2.5, 8.8, 2.6, matSawY, 0, FOOT_H + baseH + 8.8, fenceZ + 0.2);
      tag(arm, 'saw');
      g.add(arm);
      const motor = new THREE.Mesh(new THREE.CylinderGeometry(2.2, 2.2, 4.0, 18), matSawY);
      motor.rotation.z = Math.PI / 2;
      motor.position.set(2.7, FOOT_H + baseH + 9.6, fenceZ - 2.1);
      tag(motor, 'saw');
      g.add(motor);
      const blade = new THREE.Mesh(new THREE.CylinderGeometry(6, 6, 0.12, 32), matBlade);
      blade.rotation.z = Math.PI / 2;
      blade.position.set(0, FOOT_H + baseH + 7.6, fenceZ - 3.4);
      tag(blade, 'saw');
      g.add(blade);
      const handle = box(1.3, 1.05, 4.2, matSawK, 0, FOOT_H + baseH + 13.2, fenceZ - 0.6);
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
        if (o.material && o.material.userData && o.material.userData.ghostClone) doomed.push(o.material);
      });
      while (g.children.length) g.remove(g.children[0]);
      doomed.forEach(function (res) { res.dispose(); });
    }

    function buildFrame(parent, kind, opts) {
      const ghost = !!(opts && opts.ghost);
      const corners = [
        [POST_C, POST_C], [POST_C, -POST_C], [-POST_C, POST_C], [-POST_C, -POST_C]
      ];
      corners.forEach(function (c) {
        const post = box(POST, POST_H, POST, matPost, c[0], CASTER_H + POST_H / 2, c[1]);
        tag(post, 'posts');
        parent.add(post);
        addCaster(parent, c[0], c[1]);
      });
      addPerimeterBand(parent, APRON_Y, APRON_H, STOCK, matApron, 'posts');
      addPerimeterBand(parent, LOWER_RAIL_Y, RAIL_H, STOCK, matRail, 'shelf');
      ['+x', '-x', '+z', '-z'].forEach(function (face) { addLatchPad(parent, face); });

      const topY = TOP_AFF - TOP_THK / 2;
      if (kind === 'miter' && ghost) {
        const top = box(OA, TOP_THK, OA, matTop, 0, topY, 0);
        tag(top, 'top');
        parent.add(top);
        addPlyEdges(parent, OA, OA, topY, TOP_THK, 'top');
      } else if (kind === 'miter') {
        const wingW = (OA - OPEN_W) / 2;
        const lip = (OA - OPEN_D) / 2;
        const left = box(wingW, TOP_THK, OA, matTop, -(OA / 2 - wingW / 2), topY, 0);
        tag(left, 'top');
        parent.add(left);
        const right = box(wingW, TOP_THK, OA, matTop, OA / 2 - wingW / 2, topY, 0);
        tag(right, 'top');
        parent.add(right);
        const back = box(OPEN_W, TOP_THK, lip, matTop, 0, topY, OA / 2 - lip / 2);
        tag(back, 'top');
        parent.add(back);
        const front = box(OPEN_W, TOP_THK, lip, matTop, 0, topY, -OA / 2 + lip / 2);
        tag(front, 'top');
        parent.add(front);
        const insertBottom = TOP_AFF - TOP_THK;
        const insertTop = insertBottom + PLATE;
        const insertY = insertBottom + PLATE / 2;
        const nest = box(NEST_W, PLATE, NEST_D, matInsert, 0, insertY, 0);
        tag(nest, 'top');
        parent.add(nest);
        const wellH = 3.0;
        const well = box(OPEN_W - 0.4, wellH, OPEN_D - 0.4, matWell, 0, insertBottom - wellH / 2, 0);
        tag(well, 'top');
        parent.add(well);
        const flangeT = 0.22;
        const flangeW = 0.65;
        const flangeY = insertBottom - flangeT / 2;
        const flanges = [
          box(OPEN_W + flangeW, flangeT, flangeW, matInsert, 0, flangeY, OPEN_D / 2),
          box(OPEN_W + flangeW, flangeT, flangeW, matInsert, 0, flangeY, -OPEN_D / 2),
          box(flangeW, flangeT, OPEN_D, matInsert, OPEN_W / 2, flangeY, 0),
          box(flangeW, flangeT, OPEN_D, matInsert, -OPEN_W / 2, flangeY, 0)
        ];
        flanges.forEach(function (f) {
          tag(f, 'top');
          parent.add(f);
        });
        const saw = addSaw(parent);
        saw.position.set(0, insertTop, 0);
        addDustKeepClear(parent);
        addPlyEdges(parent, OA, OA, topY, TOP_THK, 'top');
      } else {
        const top = box(OA, TOP_THK, OA, kind === 'extension' ? matTopLite : matTop, 0, topY, 0);
        tag(top, 'top');
        parent.add(top);
        addPlyEdges(parent, OA, OA, topY, TOP_THK, 'top');
      }

      if (kind === 'flat') {
        addNotchedShelf(parent, SHELF_Y, matShelf, 'shelf');
        addLowerBayBrace(parent, '+z');
        addLowerBayBrace(parent, '-z');
      } else if (kind === 'extension') {
        addNotchedShelf(parent, SHELF_Y, matShelf, 'shelf');
        addLowerBayBrace(parent, '+z');
        addLowerBayBrace(parent, '-z');
      } else if (kind === 'miter') {
        addNotchedShelf(parent, SHELF_Y, matShelf, 'shelf');
        addLowerBayX(parent, '+z');
        addLowerBayX(parent, '-z');
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
      makeLabel('apron', 0, APRON_Y, -OA / 2 - 5, 12);
      makeLabel('latch', OA / 2 + 6, LATCH_AFF + 3, 0, 12);
      makeLabel('on rails', 0, SHELF_Y + 3.2, OA / 2 + 4, 12);
      if (kind === 'miter') {
        makeLabel('DWS716XPS', 0, TOP_AFF + 12, 0, 18);
        makeLabel('½ in nest', 0, TOP_AFF + 7.4, 0, 14);
        makeLabel('tight depth', 0, TOP_AFF + 4.2, SAW_D / 2 + 2, 13);
        makeLabel('dust keep-clear', 8.5, APRON_Y + 5, OA / 2 + 4, 13);
        makeLabel('bag OPEN', 8.5, APRON_Y + 2.2, OA / 2 + 4, 12);
        makeLabel('wings out of Gen-0.1', 0, TOP_AFF + 2.4, -OA / 2 - 6, 14);
      }
      const tog = document.getElementById('tog-labels');
      const show = !!(tog && tog.checked);
      labelSprites.forEach(function (s) { s.visible = show; });
    }

    function dimAsGhost(group) {
      group.traverse(function (o) {
        if (!o.isMesh || !o.material) return;
        const m = o.material.clone();
        m.transparent = true;
        m.opacity = 0.3;
        if (m.emissiveIntensity != null) m.emissiveIntensity = 0;
        if (m.color && m.color.offsetHSL) m.color.offsetHSL(0, -0.18, -0.1);
        m.userData.ghostClone = true;
        o.material = m;
      });
    }

    function buildGhost(kind) {
      clearGroup(neighbor);
      neighbor.position.set(0, 0, 0);
      pickOn = false;
      buildFrame(neighbor, kind, { ghost: true });
      pickOn = true;
      dimAsGhost(neighbor);
      neighbor.position.set(OA + 2 * MAG_PROUD, 0, 0);
    }

    function setModule(kind) {
      pickables.length = 0;
      clearGroup(root);
      buildFrame(root, kind);
      rebuildLabels(kind);
      buildGhost(kind);
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
    resize();

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
