(function () {
  'use strict';

  var slug = document.body.getAttribute('data-slug');
  if (!slug) return;

  var scene, camera, renderer, controls, wrap, model;
  var userMoved = false;
  var grain = null;
  var hovered = null;
  var pinned = null;
  var partByName = {};
  var zoom = {
    scale: 1,
    x: 0,
    y: 0,
    pointers: new Map(),
    pinch: null
  };

  function el(id) { return document.getElementById(id); }

  function showError(msg) {
    var loading = el('three-loading');
    if (loading) loading.hidden = true;
    var box = el('three-error');
    if (!box) return;
    box.hidden = false;
    box.textContent = msg;
  }

  function money(n) {
    var sign = n < 0 ? '-' : '';
    return sign + '$' + Math.abs(n).toFixed(2);
  }

  function mapVec(x, y, z) {
    return new THREE.Vector3(x, z, -y);
  }

  function cleanRing(outline) {
    var pts = [];
    var i, p, prev;
    for (i = 0; i < outline.length; i++) {
      p = outline[i];
      prev = pts[pts.length - 1];
      if (prev && Math.abs(prev[0] - p[0]) < 1e-6 && Math.abs(prev[1] - p[1]) < 1e-6) continue;
      pts.push([p[0], p[1]]);
    }
    if (pts.length > 1) {
      var a = pts[0], b = pts[pts.length - 1];
      if (Math.abs(a[0] - b[0]) < 1e-6 && Math.abs(a[1] - b[1]) < 1e-6) pts.pop();
    }
    return pts;
  }

  function signedArea(pts) {
    var a = 0, i, p, q;
    for (i = 0; i < pts.length; i++) {
      p = pts[i];
      q = pts[(i + 1) % pts.length];
      a += p[0] * q[1] - q[0] * p[1];
    }
    return a / 2;
  }

  function paintUVs(geom) {
    var pos = geom.getAttribute('position');
    var uv = geom.getAttribute('uv');
    if (!pos || !uv) return;
    var i;
    for (i = 0; i < pos.count; i++) uv.setXY(i, pos.getX(i) / 160, pos.getY(i) / 160);
    uv.needsUpdate = true;
  }

  function makeGrain() {
    var c = document.createElement('canvas');
    c.width = 256;
    c.height = 128;
    var g = c.getContext('2d');
    g.fillStyle = '#ffffff';
    g.fillRect(0, 0, 256, 128);
    var i, y;
    for (i = 0; i < 22; i++) {
      y = (i + 0.15) * (128 / 22);
      g.strokeStyle = 'rgba(80, 46, 18, ' + (0.08 + (i % 4) * 0.04) + ')';
      g.lineWidth = i % 5 === 0 ? 2 : 1;
      g.beginPath();
      g.moveTo(0, y);
      g.bezierCurveTo(80, y + 2, 160, y - 2, 256, y + 1);
      g.stroke();
    }
    var tex = new THREE.CanvasTexture(c);
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    if (THREE.sRGBEncoding) tex.encoding = THREE.sRGBEncoding;
    tex.anisotropy = 4;
    return tex;
  }

  var TINT = {
    carcass: 0xd7b48a,
    shelf: 0xdec4a0,
    drawer: 0xc99668,
    feet: 0xc9a56f,
    cleat: 0xb58358,
    top: 0xe2c39a,
    door: 0xc9a27a,
    tray: 0xd8c2a0,
    option: 0xd2b48c,
    sign: 0xc4a882
  };
  var mats = {};
  function matFor(group) {
    var key = TINT[group] ? group : 'carcass';
    if (!mats[key]) {
      mats[key] = new THREE.MeshStandardMaterial({
        map: grain,
        color: TINT[key],
        roughness: 0.78,
        metalness: 0.02,
        flatShading: true,
        side: THREE.DoubleSide,
        polygonOffset: true,
        polygonOffsetFactor: 1,
        polygonOffsetUnits: 1
      });
    }
    return mats[key];
  }

  function toVec2(pts) {
    var out = [];
    var i;
    for (i = 0; i < pts.length; i++) out.push(new THREE.Vector2(pts[i][0], pts[i][1]));
    return out;
  }

  function panelGeometry(part) {
    var pts = cleanRing(part.outline || []);
    if (pts.length < 3) return null;
    var outline = toVec2(pts);
    var outlineCW = THREE.ShapeUtils.isClockWise(outline);
    if (outlineCW) {
      outline.reverse();
      outlineCW = false;
    }
    var shape = new THREE.Shape(outline);
    var holes = Array.isArray(part.holes) ? part.holes : [];
    var h, ring, hole, holeCW;
    for (h = 0; h < holes.length; h++) {
      ring = cleanRing(holes[h] || []);
      if (ring.length < 3) continue;
      hole = toVec2(ring);
      holeCW = THREE.ShapeUtils.isClockWise(hole);
      if (holeCW === outlineCW) hole.reverse();
      shape.holes.push(new THREE.Path(hole));
    }
    var depth = Math.max(1, part.thickness - 0.4);
    var geom = new THREE.ExtrudeGeometry(shape, { depth: depth, bevelEnabled: false, steps: 1 });
    paintUVs(geom);
    return { geom: geom, depth: depth };
  }

  function addPanel(root, movers, part, modelCenter) {
    var built = panelGeometry(part);
    if (!built) return false;
    var mesh = new THREE.Mesh(built.geom, matFor(part.group).clone());
    var eu = mapVec(part.u[0], part.u[1], part.u[2]);
    var ev = mapVec(part.v[0], part.v[1], part.v[2]);
    var en = mapVec(part.n[0], part.n[1], part.n[2]);
    var basis = new THREE.Matrix4().makeBasis(eu, ev, en);
    mesh.quaternion.setFromRotationMatrix(basis);
    var origin = mapVec(part.origin[0], part.origin[1], part.origin[2]);
    origin.addScaledVector(en, (part.thickness - built.depth) / 2);
    mesh.position.copy(origin);
    mesh.name = part.name;
    mesh.userData.kind = 'panel';
    mesh.userData.group = part.group;
    mesh.userData.optional = !!part.optional;
    var edgeMat = new THREE.LineBasicMaterial({ color: 0x3a2918 });
    mesh.userData.edgeMat = edgeMat;
    mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(built.geom, 28), edgeMat));
    root.add(mesh);
    var center = mapVec(part.center[0], part.center[1], part.center[2]);
    movers.push({
      obj: mesh,
      base: origin.clone(),
      away: center.sub(modelCenter),
      normal: en.clone()
    });
    return true;
  }

  function addCasters(root, movers, data, modelCenter) {
    var feet = [];
    var i, part;
    for (i = 0; i < data.parts.length; i++) {
      part = data.parts[i];
      if (part.name.indexOf('FOOT-A') === 0) feet.push(part);
    }
    if (!feet.length) return;
    var plateMat = new THREE.MeshStandardMaterial({ color: 0x3a3a3a, roughness: 0.4, metalness: 0.6 });
    var steelMat = new THREE.MeshStandardMaterial({ color: 0x6a6e72, roughness: 0.35, metalness: 0.7 });
    var wheelMat = new THREE.MeshStandardMaterial({ color: 0x1c1c1c, roughness: 0.9, metalness: 0.05 });
    var plateGeo = new THREE.BoxGeometry(94, 5, 64);
    var stemGeo = new THREE.CylinderGeometry(8, 10, 42, 12);
    var wheelDia = 75;
    for (i = 0; i < feet.length; i++) {
      part = feet[i];
      var group = new THREE.Group();
      group.name = 'CASTER-' + part.name;
      group.userData.kind = 'caster';
      group.userData.group = 'casters';
      group.userData.optional = true;
      group.position.set(part.center[0], 0, -part.center[1]);
      var wheel = new THREE.Mesh(new THREE.CylinderGeometry(wheelDia / 2, wheelDia / 2, 24, 24), wheelMat);
      wheel.rotation.z = Math.PI / 2;
      wheel.position.y = wheelDia / 2;
      var plate = new THREE.Mesh(plateGeo, plateMat);
      plate.position.y = part.origin[2] - 2.6;
      var stem = new THREE.Mesh(stemGeo, steelMat);
      stem.position.y = (part.origin[2] + wheelDia / 2) / 2;
      group.add(wheel);
      group.add(stem);
      group.add(plate);
      root.add(group);
      var away = new THREE.Vector3(part.center[0], part.origin[2] / 2, -part.center[1]).sub(modelCenter);
      movers.push({
        obj: group,
        base: group.position.clone(),
        away: away,
        normal: new THREE.Vector3()
      });
    }
  }

  function buildModel(data) {
    var root = new THREE.Group();
    root.name = slug;
    var movers = [];
    var overall = data.overall;
    var modelCenter = new THREE.Vector3(overall.width / 2, overall.height / 2, -overall.depth / 2);
    var missing = [];
    var i, part;
    for (i = 0; i < data.parts.length; i++) {
      part = data.parts[i];
      partByName[part.name] = part;
      try {
        if (!addPanel(root, movers, part, modelCenter)) missing.push(part.name);
      } catch (err) {
        missing.push(part.name);
      }
    }
    addCasters(root, movers, data, modelCenter);
    scene.add(root);
    var grid = new THREE.GridHelper(3200, 16, 0x5c4c3c, 0x3a3128);
    grid.position.set(overall.width / 2, -0.6, -overall.depth / 2);
    var gridMats = Array.isArray(grid.material) ? grid.material : [grid.material];
    gridMats.forEach(function (m) { m.transparent = true; m.opacity = 0.45; });
    scene.add(grid);
    model = { root: root, movers: movers, data: data, missing: missing };
  }

  function toggleInput(group) {
    return document.querySelector('[data-toggle="' + group + '"]');
  }

  function groupOn(group) {
    var input = toggleInput(group);
    if (!input) return true;
    return input.checked;
  }

  function desiredVisible(ud) {
    if (ud.kind === 'caster') return groupOn('casters');
    if (ud.optional && toggleInput(ud.group)) return groupOn(ud.group);
    return true;
  }

  function litName() {
    return hovered || pinned;
  }

  function applyVisibility() {
    if (!model) return;
    var name = litName();
    var i, obj, ud;
    for (i = 0; i < model.movers.length; i++) {
      obj = model.movers[i].obj;
      ud = obj.userData;
      obj.visible = desiredVisible(ud) || obj.name === name;
    }
  }

  function applyExplode() {
    if (!model) return;
    var slider = el('explode');
    var k = Number(slider.value) / 100;
    slider.setAttribute('aria-valuenow', slider.value);
    slider.setAttribute('aria-valuetext', slider.value + ' percent exploded');
    var i, item;
    for (i = 0; i < model.movers.length; i++) {
      item = model.movers[i];
      item.obj.position.copy(item.base);
      item.obj.position.addScaledVector(item.away, k * 0.72);
      item.obj.position.addScaledVector(item.normal, k * 40);
    }
  }

  function visibleBox() {
    var box = new THREE.Box3();
    var any = false;
    function walk(obj) {
      if (!obj.visible) return;
      if (obj.geometry) {
        if (!obj.geometry.boundingBox) obj.geometry.computeBoundingBox();
        var b = obj.geometry.boundingBox.clone();
        b.applyMatrix4(obj.matrixWorld);
        if (!b.isEmpty()) {
          box.union(b);
          any = true;
        }
      }
      var i;
      for (i = 0; i < obj.children.length; i++) walk(obj.children[i]);
    }
    model.root.updateMatrixWorld(true);
    walk(model.root);
    return any ? box : null;
  }

  function fitCamera(preserveDir) {
    if (!model || !camera || !wrap || !controls) return;
    var w = wrap.clientWidth;
    var h = wrap.clientHeight;
    if (w < 2 || h < 2) return;
    var box = visibleBox();
    if (!box) return;
    var center = box.getCenter(new THREE.Vector3());
    var size = box.getSize(new THREE.Vector3());
    var radius = 0.5 * Math.sqrt(size.x * size.x + size.y * size.y + size.z * size.z);
    if (!(radius > 1)) return;
    var aspect = w / h;
    camera.aspect = aspect;
    camera.fov = aspect < 0.85 ? 50 : 36;
    camera.updateProjectionMatrix();
    var vFov = camera.fov * Math.PI / 180;
    var hFov = 2 * Math.atan(Math.tan(vFov / 2) * aspect);
    var dist = Math.max(radius / Math.sin(vFov / 2), radius / Math.sin(hFov / 2)) * 1.28;
    var dir;
    if (preserveDir) {
      dir = camera.position.clone().sub(controls.target);
      if (dir.lengthSq() < 1) dir.set(0.9, 0.55, 1.08);
    } else {
      dir = new THREE.Vector3(0.9, 0.55, 1.08);
    }
    dir.normalize();
    camera.position.copy(center).addScaledVector(dir, dist);
    camera.near = Math.max(0.5, dist / 250);
    camera.far = Math.max(30000, dist * 14);
    camera.updateProjectionMatrix();
    controls.target.copy(center);
    controls.minDistance = Math.max(40, radius * 0.2);
    controls.maxDistance = Math.max(radius * 14, dist * 4);
    controls.update();
  }

  function projectedFits() {
    if (!model || !camera) return false;
    var box = visibleBox();
    if (!box) return false;
    var xs = [box.min.x, box.max.x];
    var ys = [box.min.y, box.max.y];
    var zs = [box.min.z, box.max.z];
    var ix, iy, iz, v;
    for (ix = 0; ix < 2; ix++) {
      for (iy = 0; iy < 2; iy++) {
        for (iz = 0; iz < 2; iz++) {
          v = new THREE.Vector3(xs[ix], ys[iy], zs[iz]).project(camera);
          if (v.z < -1.02 || v.z > 1.02) return false;
          if (v.x < -1.02 || v.x > 1.02) return false;
          if (v.y < -1.02 || v.y > 1.02) return false;
        }
      }
    }
    return true;
  }

  function resize() {
    if (!renderer || !camera || !wrap) return;
    var w = wrap.clientWidth;
    var h = wrap.clientHeight;
    if (w < 2 || h < 2) return;
    var exploded = el('explode') && Number(el('explode').value) > 0;
    if (!userMoved || exploded) fitCamera(userMoved);
    else {
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    }
    renderer.setSize(w, h, false);
  }

  function paintPart(mesh, on) {
    if (!mesh.isMesh || !mesh.material || !mesh.material.emissive) return;
    mesh.material.emissive.setHex(on ? 0xc47b12 : 0x000000);
    mesh.material.emissiveIntensity = on ? 0.7 : 0;
    if (mesh.userData.edgeMat) mesh.userData.edgeMat.color.setHex(on ? 0xf0b429 : 0x3a2918);
  }

  function showHighlight() {
    if (!model) return;
    var name = litName();
    var i;
    for (i = 0; i < model.movers.length; i++) {
      var obj = model.movers[i].obj;
      if (obj.isMesh) paintPart(obj, obj.name === name);
    }
    var buttons = document.querySelectorAll('button.part');
    for (i = 0; i < buttons.length; i++) {
      var btn = buttons[i];
      var hit = btn.getAttribute('data-part') === name;
      var pressed = btn.getAttribute('data-part') === pinned;
      btn.classList.toggle('is-lit', hit);
      btn.setAttribute('aria-pressed', pressed ? 'true' : 'false');
    }
    var note = el('lit-note');
    if (note) {
      if (!name) note.textContent = '';
      else note.textContent = name + ' is lit in the model.';
    }
    applyVisibility();
  }

  function revealGroup(name) {
    var part = partByName[name];
    if (!part || !part.optional) return;
    var input = toggleInput(part.group);
    if (input && !input.checked) {
      input.checked = true;
      applyVisibility();
      var exploded = Number(el('explode').value) > 0;
      if (exploded || !userMoved) fitCamera(userMoved);
    }
  }

  function closest(target, selector) {
    var node = target && target.nodeType === 1 ? target : (target && target.parentElement);
    if (!node || !node.closest) return null;
    return node.closest(selector);
  }

  function wireParts() {
    document.addEventListener('pointerover', function (e) {
      var btn = closest(e.target, 'button.part');
      if (!btn) return;
      hovered = btn.getAttribute('data-part');
      showHighlight();
    });
    document.addEventListener('pointerout', function (e) {
      var btn = closest(e.target, 'button.part');
      if (!btn) return;
      var rel = e.relatedTarget;
      if (rel && btn.contains(rel)) return;
      if (hovered === btn.getAttribute('data-part')) hovered = null;
      showHighlight();
    });
    document.addEventListener('focusin', function (e) {
      var btn = closest(e.target, 'button.part');
      if (!btn) return;
      hovered = btn.getAttribute('data-part');
      showHighlight();
    });
    document.addEventListener('focusout', function (e) {
      var btn = closest(e.target, 'button.part');
      if (!btn) return;
      if (hovered === btn.getAttribute('data-part')) hovered = null;
      showHighlight();
    });
    document.addEventListener('click', function (e) {
      var btn = closest(e.target, 'button.part');
      if (!btn) return;
      var name = btn.getAttribute('data-part');
      pinned = pinned === name ? null : name;
      if (pinned) revealGroup(pinned);
      showHighlight();
    });
  }

  function canWebGL() {
    try {
      var canvas = document.createElement('canvas');
      var gl = canvas.getContext('webgl', { failIfMajorPerformanceCaveat: false }) || canvas.getContext('experimental-webgl');
      return !!gl;
    } catch (err) {
      return false;
    }
  }

  function boot3d(data) {
    if (!window.THREE || !window.THREE.OrbitControls) {
      showError('The 3D view did not start. The model scripts could not be loaded.');
      return;
    }
    if (!canWebGL()) {
      showError('The 3D view did not start. This browser could not open WebGL.');
      return;
    }
    wrap = el('canvas-wrap');
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x241e18);
    camera = new THREE.PerspectiveCamera(36, 1, 0.5, 30000);
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    } catch (err) {
      showError('The 3D view did not start. This browser could not open WebGL.');
      return;
    }
    if (!renderer.getContext()) {
      showError('The 3D view did not start. This browser could not open WebGL.');
      return;
    }
    var coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, coarse ? 1.75 : 2));
    if ('outputEncoding' in renderer && THREE.sRGBEncoding) renderer.outputEncoding = THREE.sRGBEncoding;
    wrap.appendChild(renderer.domElement);
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = false;
    controls.screenSpacePanning = true;
    controls.maxPolarAngle = Math.PI * 0.92;
    if (THREE.TOUCH) {
      controls.touches.ONE = THREE.TOUCH.ROTATE;
      controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;
    }
    controls.addEventListener('start', function () { userMoved = true; });
    scene.add(new THREE.HemisphereLight(0xfff1df, 0x3a3228, 0.92));
    var sun = new THREE.DirectionalLight(0xfff6ea, 1.05);
    sun.position.set(700, 1400, 480);
    scene.add(sun);
    var fill = new THREE.DirectionalLight(0xf0d7b4, 0.38);
    fill.position.set(-600, 420, -500);
    scene.add(fill);
    grain = makeGrain();
    buildModel(data);
    applyVisibility();
    applyExplode();
    el('three-loading').hidden = true;
    var status = el('model-status');
    if (status) {
      status.textContent = model.missing.length
        ? 'The model is ready, with ' + model.missing.length + ' parts left out.'
        : 'The model is ready.';
    }
    window.addEventListener('resize', resize);
    if (window.ResizeObserver) new ResizeObserver(resize).observe(wrap);
    resize();
    renderer.setAnimationLoop(function () { renderer.render(scene, camera); });
    window.__furniture = {
      ready: true,
      slug: slug,
      missing: model.missing.slice(),
      partCount: model.data.parts.length,
      visibleCount: function () {
        var n = 0, i;
        for (i = 0; i < model.movers.length; i++) if (model.movers[i].obj.visible) n++;
        return n;
      },
      fits: projectedFits,
      highlight: function () { return litName(); },
      slots: slotsOpen,
      aim: function (x, y, z) {
        userMoved = true;
        var dir = new THREE.Vector3(x, y, z);
        if (dir.lengthSq() < 1e-6) dir.set(0.9, 0.55, 1.08);
        camera.position.copy(controls.target).add(dir);
        fitCamera(true);
        if (renderer && wrap) renderer.setSize(wrap.clientWidth, wrap.clientHeight, false);
      }
    };
  }

  function ringCentroid(ring) {
    var a = 0;
    var b = 0;
    var i;
    if (!ring || !ring.length) return null;
    for (i = 0; i < ring.length; i++) {
      a += ring[i][0];
      b += ring[i][1];
    }
    return [a / ring.length, b / ring.length];
  }

  function pointInRing(x, y, ring) {
    var inside = false;
    var i, j, xi, yi, xj, yj;
    for (i = 0, j = ring.length - 1; i < ring.length; j = i++) {
      xi = ring[i][0];
      yi = ring[i][1];
      xj = ring[j][0];
      yj = ring[j][1];
      if (((yi > y) !== (yj > y)) && (x < ((xj - xi) * (y - yi)) / ((yj - yi) || 1e-9) + xi)) inside = !inside;
    }
    return inside;
  }

  function slotsOpen() {
    var report = { checked: 0, open: 0, blocked: 0, parts: [] };
    if (!model) return report;
    var raycaster = new THREE.Raycaster();
    var i, item, mesh, part, holes, picks, h, center, local, world, normal, hits, opened, blocked;
    for (i = 0; i < model.movers.length; i++) {
      item = model.movers[i];
      mesh = item.obj;
      if (!mesh.isMesh) continue;
      part = partByName[mesh.name];
      holes = part && Array.isArray(part.holes) ? part.holes : [];
      if (!holes.length) continue;
      picks = [];
      for (h = 0; h < holes.length && picks.length < 6; h++) {
        center = ringCentroid(holes[h]);
        if (center && pointInRing(center[0], center[1], holes[h])) picks.push(center);
      }
      if (!picks.length) {
        for (h = 0; h < holes.length && picks.length < 6; h++) {
          center = ringCentroid(holes[h]);
          if (center) picks.push(center);
        }
      }
      opened = 0;
      blocked = 0;
      for (h = 0; h < picks.length; h++) {
        center = picks[h];
        local = new THREE.Vector3(center[0], center[1], Math.max(0.2, (part.thickness - 0.4) / 2));
        world = mesh.localToWorld(local);
        normal = new THREE.Vector3(0, 0, 1).applyQuaternion(mesh.getWorldQuaternion(new THREE.Quaternion())).normalize();
        raycaster.set(world.clone().addScaledVector(normal, 80), normal.clone().negate());
        hits = raycaster.intersectObject(mesh, false);
        report.checked += 1;
        if (hits.length) {
          blocked += 1;
          report.blocked += 1;
        } else {
          opened += 1;
          report.open += 1;
        }
      }
      report.parts.push({ name: mesh.name, holes: holes.length, open: opened, blocked: blocked });
    }
    return report;
  }

  function wireModelUi() {
    var slider = el('explode');
    if (slider) {
      slider.addEventListener('input', function () {
        applyExplode();
        fitCamera(userMoved);
      });
    }
    var toggles = document.querySelectorAll('[data-toggle]');
    var i;
    for (i = 0; i < toggles.length; i++) {
      toggles[i].addEventListener('change', function () {
        applyVisibility();
        var exploded = Number(el('explode').value) > 0;
        if (exploded || !userMoved) fitCamera(userMoved);
      });
    }
    var reset = el('btn-reset');
    if (reset) {
      reset.addEventListener('click', function () {
        userMoved = false;
        fitCamera(false);
      });
    }
    wireFullscreen();
  }

  function isPortrait() {
    return window.matchMedia && window.matchMedia('(orientation: portrait)').matches;
  }

  function fsElement() {
    return document.fullscreenElement || document.webkitFullscreenElement || null;
  }

  function modelStage() {
    return el('model-stage');
  }

  function inNativeFs() {
    var stage = modelStage();
    return !!(stage && fsElement() === stage);
  }

  function inFallbackFs() {
    var stage = modelStage();
    return !!(stage && stage.classList.contains('is-fs'));
  }

  function inFullscreen() {
    return inNativeFs() || inFallbackFs();
  }

  function syncFsChrome() {
    var stage = modelStage();
    var on = inFullscreen();
    var openBtn = el('btn-fullscreen');
    var exitBtn = el('btn-exit-fs');
    if (openBtn) openBtn.hidden = on;
    if (exitBtn) exitBtn.hidden = !on;
    document.body.classList.toggle('fs-lock', inFallbackFs());
    if (!stage) return;
    var landscape = !isPortrait();
    var turned = on && inFallbackFs() && !landscape;
    var hint = el('rotate-hint');
    stage.classList.toggle('is-turned', turned);
    if (hint) hint.hidden = !(on && !landscape && !turned);
  }

  function refitAfterLayout() {
    window.requestAnimationFrame(function () {
      window.requestAnimationFrame(function () {
        if (wrap && camera) {
          fitCamera(userMoved);
          if (renderer) renderer.setSize(wrap.clientWidth, wrap.clientHeight, false);
        } else {
          resize();
        }
      });
    });
  }

  function lockLandscape() {
    try {
      if (screen.orientation && typeof screen.orientation.lock === 'function') {
        var pending = screen.orientation.lock('landscape');
        if (pending && typeof pending.then === 'function') {
          pending.then(function () { syncFsChrome(); refitAfterLayout(); }).catch(function () { syncFsChrome(); refitAfterLayout(); });
          return;
        }
      }
    } catch (err) {
      /* lock is unsupported or was refused */
    }
    syncFsChrome();
    refitAfterLayout();
  }

  function enterFallback() {
    var stage = modelStage();
    if (!stage) return;
    stage.classList.add('is-fs');
    syncFsChrome();
    lockLandscape();
  }

  function exitFullscreen() {
    var stage = modelStage();
    if (stage) stage.classList.remove('is-fs', 'is-turned');
    try {
      if (screen.orientation && typeof screen.orientation.unlock === 'function') screen.orientation.unlock();
    } catch (err) {
      /* unlock can throw when nothing was locked */
    }
    var exit = document.exitFullscreen || document.webkitExitFullscreen;
    if (fsElement() && exit) {
      var pending = exit.call(document);
      if (pending && typeof pending.catch === 'function') pending.catch(function () {});
    }
    syncFsChrome();
    refitAfterLayout();
  }

  function enterFullscreen() {
    var stage = modelStage();
    if (!stage) return;
    var req = stage.requestFullscreen || stage.webkitRequestFullscreen;
    if (!req) {
      enterFallback();
      return;
    }
    try {
      var pending = req.call(stage);
      if (pending && typeof pending.then === 'function') {
        pending.then(function () { lockLandscape(); }).catch(function () { enterFallback(); });
      } else {
        lockLandscape();
      }
    } catch (err) {
      enterFallback();
    }
  }

  function wireFullscreen() {
    var openBtn = el('btn-fullscreen');
    var exitBtn = el('btn-exit-fs');
    if (openBtn) openBtn.addEventListener('click', enterFullscreen);
    if (exitBtn) exitBtn.addEventListener('click', exitFullscreen);
    document.addEventListener('fullscreenchange', function () {
      syncFsChrome();
      refitAfterLayout();
    });
    document.addEventListener('webkitfullscreenchange', function () {
      syncFsChrome();
      refitAfterLayout();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && inFullscreen()) exitFullscreen();
    });
    window.addEventListener('orientationchange', function () {
      if (inFullscreen()) {
        syncFsChrome();
        refitAfterLayout();
      }
    });
  }

  function applyZoomTransform() {
    var img = el('zoom-img');
    if (!img) return;
    img.style.transform = 'translate(' + zoom.x + 'px,' + zoom.y + 'px) scale(' + zoom.scale + ')';
  }

  function zoomAt(clientX, clientY, next) {
    var stage = el('zoom-stage');
    var rect = stage.getBoundingClientRect();
    var px = clientX - rect.left;
    var py = clientY - rect.top;
    var ix = (px - zoom.x) / zoom.scale;
    var iy = (py - zoom.y) / zoom.scale;
    zoom.scale = Math.min(8, Math.max(1, next));
    zoom.x = px - ix * zoom.scale;
    zoom.y = py - iy * zoom.scale;
    applyZoomTransform();
  }

  function resetZoom() {
    zoom.scale = 1;
    zoom.x = 0;
    zoom.y = 0;
    applyZoomTransform();
  }

  function openZoom(src, title, alt) {
    var dialog = el('zoom');
    var img = el('zoom-img');
    var heading = el('zoom-title');
    if (!dialog || !img) return;
    heading.textContent = title || 'Cut sheet';
    img.alt = alt || title || 'Cut sheet';
    img.src = src;
    resetZoom();
    if (typeof dialog.showModal === 'function' && !dialog.open) dialog.showModal();
  }

  function wireZoom() {
    var dialog = el('zoom');
    var stage = el('zoom-stage');
    if (!dialog || !stage) return;
    document.addEventListener('click', function (e) {
      var opener = closest(e.target, '.sheet-open');
      if (!opener) return;
      var img = opener.querySelector('img');
      if (!img) return;
      openZoom(img.currentSrc || img.src, opener.getAttribute('data-title'), img.alt);
    });
    el('zoom-close').addEventListener('click', function () { dialog.close(); });
    el('zoom-in').addEventListener('click', function () {
      var rect = stage.getBoundingClientRect();
      zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, zoom.scale * 1.35);
    });
    el('zoom-out').addEventListener('click', function () {
      var rect = stage.getBoundingClientRect();
      zoomAt(rect.left + rect.width / 2, rect.top + rect.height / 2, zoom.scale / 1.35);
    });
    el('zoom-fit').addEventListener('click', resetZoom);
    el('zoom-labels').addEventListener('click', function () {
      var rect = stage.getBoundingClientRect();
      var target = Math.max(1.8, Math.min(4.5, 1500 / Math.max(rect.width, 1)));
      zoom.scale = target;
      zoom.x = 16;
      zoom.y = 16;
      applyZoomTransform();
    });
    stage.addEventListener('wheel', function (e) {
      e.preventDefault();
      var factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
      zoomAt(e.clientX, e.clientY, zoom.scale * factor);
    }, { passive: false });
    stage.addEventListener('dblclick', function (e) {
      zoomAt(e.clientX, e.clientY, zoom.scale < 2 ? 2.6 : 1);
      if (zoom.scale === 1) resetZoom();
    });
    stage.addEventListener('pointerdown', function (e) {
      zoom.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (zoom.pointers.size === 1) {
        zoom.pinch = null;
        zoom.drag = { id: e.pointerId, x: e.clientX, y: e.clientY, ox: zoom.x, oy: zoom.y };
        stage.classList.add('is-grabbing');
      } else if (zoom.pointers.size === 2) {
        zoom.drag = null;
        var pts = Array.from(zoom.pointers.values());
        zoom.pinch = {
          dist: Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y) || 1,
          scale: zoom.scale,
          cx: (pts[0].x + pts[1].x) / 2,
          cy: (pts[0].y + pts[1].y) / 2
        };
      }
    });
    stage.addEventListener('pointermove', function (e) {
      if (!zoom.pointers.has(e.pointerId)) return;
      zoom.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (zoom.pointers.size >= 2 && zoom.pinch) {
        var pts = Array.from(zoom.pointers.values());
        var dist = Math.hypot(pts[0].x - pts[1].x, pts[0].y - pts[1].y) || 1;
        zoomAt(zoom.pinch.cx, zoom.pinch.cy, zoom.pinch.scale * (dist / zoom.pinch.dist));
        return;
      }
      if (zoom.drag && zoom.drag.id === e.pointerId) {
        zoom.x = zoom.drag.ox + (e.clientX - zoom.drag.x);
        zoom.y = zoom.drag.oy + (e.clientY - zoom.drag.y);
        applyZoomTransform();
      }
    });
    function endPointer(e) {
      zoom.pointers.delete(e.pointerId);
      if (zoom.drag && zoom.drag.id === e.pointerId) zoom.drag = null;
      if (zoom.pointers.size < 2) zoom.pinch = null;
      if (zoom.pointers.size === 0) stage.classList.remove('is-grabbing');
    }
    stage.addEventListener('pointerup', endPointer);
    stage.addEventListener('pointercancel', endPointer);
  }

  function wireCalc() {
    var node = el('calc-data');
    var out = el('calc-out');
    if (!node || !out) return;
    var data = JSON.parse(node.textContent);
    var fields = ['sheet-cost', 'hardware-cost', 'selling-price', 'labor-rate'].map(el);
    var scenarioPick = el('machine-scenario');

    function row(label, value, bad) {
      var div = document.createElement('div');
      if (bad) div.className = 'neg';
      var strong = document.createElement('strong');
      strong.textContent = label;
      var span = document.createElement('span');
      span.textContent = value;
      div.appendChild(strong);
      div.appendChild(span);
      return div;
    }

    function render() {
      var sheet = Number(fields[0].value);
      var hardware = Number(fields[1].value);
      var price = Number(fields[2].value);
      var rate = Number(fields[3].value);
      out.replaceChildren();
      if (![sheet, hardware, price, rate].every(Number.isFinite)) {
        out.appendChild(row('Margin', 'Enter a number in each field', true));
        return;
      }
      var choice = scenarioChoice();
      var wear = choice.hours * choice.wearPerHour;
      var cost = sheet + hardware + data.fixedCost + wear;
      var gross = price - cost;
      var pct = price === 0 ? null : (gross / price) * 100;
      var fees = price * data.feeRate;
      var labor = data.laborHours * rate;
      var net = gross - fees - labor;
      var hours = choice.hours;
      var perHour = hours ? net / hours : null;
      var grossHour = hours ? gross / hours : null;
      out.appendChild(row('Machine time', fmtHours(hours) + (choice.assumption ? ' (assumption)' : ''), false));
      out.appendChild(row('Cost per unit', money(cost), cost < 0));
      out.appendChild(row('Gross margin', money(gross) + (pct === null ? '' : ' (' + pct.toFixed(1) + '%)'), gross < 0));
      out.appendChild(row('Fees (10%)', money(fees), false));
      out.appendChild(row('Labor', money(labor), false));
      out.appendChild(row('Net after fees and labor', money(net), net < 0));
      out.appendChild(row('Profit per machine hour', perHour === null ? '—' : money(grossHour) + ' gross, ' + money(perHour) + ' net', net < 0));
    }

    function fmtHours(n) {
      var text = (Math.round(n * 100) / 100).toFixed(2).replace(/\.00$/, '').replace(/(\.\d)0$/, '$1');
      return text + ' h';
    }

    function scenarioChoice() {
      var list = data.scenarios || [];
      var id = scenarioPick ? scenarioPick.value : (data.defaultScenario || 'mid');
      var i;
      for (i = 0; i < list.length; i++) if (list[i].id === id) return list[i];
      if (list.length) return list[0];
      return { hours: data.machineHours || 0, wearPerHour: 0, assumption: false };
    }

    fields.forEach(function (input) { input.addEventListener('input', render); });
    if (scenarioPick) scenarioPick.addEventListener('change', render);
    render();
  }

  wireParts();
  wireZoom();
  wireCalc();
  wireModelUi();

  fetch('/furniture-data/' + slug + '/parts.json').then(function (res) {
    if (!res.ok) throw new Error('parts');
    return res.json();
  }).then(function (data) {
    boot3d(data);
  }).catch(function () {
    showError('The 3D view did not start. The part file could not be loaded.');
  });
})();
