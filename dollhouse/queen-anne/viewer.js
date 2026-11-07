/* Queen Anne viewer. Every mesh is a manifest STL. Modes move or hide those meshes. */
(function () {
  'use strict';

  var state = {
    manifest: null,
    entries: [],
    mode: 'closed',
    storey: 1,
    booted: false,
    triangles: 0,
    errors: []
  };

  function el(id) { return document.getElementById(id); }

  function clear(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function text(tag, value, className) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = value;
    return node;
  }

  function assertNever(value) {
    throw new Error('Unhandled case: ' + String(value));
  }

  function parseStl(buffer) {
    var bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
    if (bytes.length < 84) throw new Error('STL is too small');
    var view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    var count = view.getUint32(80, true);
    if (!(count > 0 && 84 + count * 50 === bytes.length)) throw new Error('Expected a binary STL');
    var positions = new Float32Array(count * 9);
    var offset = 84;
    var i, v, base;
    for (i = 0; i < count; i++) {
      offset += 12;
      for (v = 0; v < 3; v++) {
        base = i * 9 + v * 3;
        positions[base] = view.getFloat32(offset, true);
        positions[base + 1] = view.getFloat32(offset + 4, true);
        positions[base + 2] = view.getFloat32(offset + 8, true);
        offset += 12;
      }
      offset += 2;
    }
    return { positions: positions, triangles: count };
  }

  function applyMatrix(mesh, matrix) {
    mesh.matrix.set(
      matrix[0][0], matrix[0][1], matrix[0][2], matrix[0][3],
      matrix[1][0], matrix[1][1], matrix[1][2], matrix[1][3],
      matrix[2][0], matrix[2][1], matrix[2][2], matrix[2][3],
      matrix[3][0], matrix[3][1], matrix[3][2], matrix[3][3]
    );
    mesh.matrixAutoUpdate = false;
    mesh.matrixWorldNeedsUpdate = true;
  }

  function addVec(a, b) {
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  }

  function translate(v) {
    return [
      [1, 0, 0, v[0]],
      [0, 1, 0, v[1]],
      [0, 0, 1, v[2]],
      [0, 0, 0, 1]
    ];
  }

  function mul(a, b) {
    var o = [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]];
    var i, j;
    for (i = 0; i < 4; i++) {
      for (j = 0; j < 4; j++) {
        o[i][j] = a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j] + a[i][3] * b[3][j];
      }
    }
    return o;
  }

  function motionVector(motion, park) {
    var v = [0, 0, 0];
    if (!motion) return v;
    if (motion.slide) v = addVec(v, motion.slide);
    if (motion.lift) v = addVec(v, motion.lift);
    if (motion.pull) v = addVec(v, motion.pull);
    if (park && motion.park) v = addVec(v, motion.park);
    return v;
  }

  function modeMatrix(instance) {
    var mode = state.mode;
    var motion = instance.motion;
    var group = motion ? motion.group : '';
    switch (mode) {
      case 'closed':
      case 'plan':
      case 'lighting':
        return instance.transform;
      case 'attachment':
        if (instance.id === 'hall-l1-front' && motion && motion.pull) {
          return mul(translate([0, motion.pull[1] * 0.45, 0]), instance.transform);
        }
        return instance.transform;
      case 'open':
        if (group === 'front' || group === 'end') {
          return mul(translate(motionVector(motion, false)), instance.transform);
        }
        if (group === 'roof') return mul(translate(motionVector(motion, true)), instance.transform);
        return instance.transform;
      case 'remove-panels':
        return instance.transform;
      case 'roof':
        if (group === 'roof') return mul(translate(motionVector(motion, true)), instance.transform);
        return instance.transform;
      case 'explode':
        return mul(translate(instance.explode_mm), instance.transform);
      default:
        return assertNever(mode);
    }
  }

  function levelOf(instance) {
    var id = instance.id;
    if (id.indexOf('l3') >= 0 || id === 'loft-chair') return 3;
    if (id.indexOf('l2') >= 0 || id.indexOf('floor') >= 0 || id === 'stair-upper' || id.indexOf('bed') >= 0) return 2;
    return 1;
  }

  function modeVisible(instance) {
    if (state.mode === 'remove-panels') {
      var group = instance.motion ? instance.motion.group : '';
      return group !== 'front' && group !== 'end';
    }
    if (state.mode === 'attachment') {
      return instance.id === 'hall-l1-front' || instance.id === 'hall-l1-frame' || instance.role === 'coupon';
    }
    if (state.mode === 'plan') {
      return instance.role !== 'roof' && instance.role !== 'panel' && instance.role !== 'coupon' && instance.role !== 'sample' && levelOf(instance) === state.storey;
    }
    if (state.mode === 'lighting') {
      return instance.role !== 'panel' && instance.role !== 'coupon';
    }
    return true;
  }

  function modeCopy(mode) {
    switch (mode) {
      case 'closed':
        return 'Closed. One house: parlor, entry, living room and bay, porch, bedrooms, and the tower loft. Roofs sit on their plates. Panels are seated on flat faces.';
      case 'open':
        return 'Open. Each facade has moved straight out along its normal. No hook and no slide. Roofs are lifted and parked clear of the plates.';
      case 'remove-panels':
        return 'Panels hidden. Frames, floors, stairs, and roofs stay. The hidden panels are the same STLs.';
      case 'roof':
        return 'Roofs lifted straight off their plates and parked. Panels stay seated. Each roof is one solid.';
      case 'explode':
        return 'Exploded along the manifest vectors, including furniture.';
      case 'plan':
        return 'Storey ' + state.storey + '. Roofs and facades are hidden so the rooms, stair, and doorways on this floor are visible. The drawing under the view uses the same coordinates.';
      case 'attachment':
        return 'Attachment. The entry panel is pulled straight out. Nothing hooks it. The capture bars on the coupon close the magnet slots only. 5.0 × 2.8 mm is nominal, not a proven fit, and the holding force was not calculated.';
      case 'lighting':
        return 'Lighting. Fixtures stay on the fixed frame. The drawing shows the route from each lamp to the adult bay, and the cross section of the ceiling puck. The 6 × 6 × 3 mm cavity is not a measured LED.';
      default:
        return assertNever(mode);
    }
  }

  function updatePoses() {
    state.entries.forEach(function (entry) {
      applyMatrix(entry.mesh, modeMatrix(entry.instance));
      entry.mesh.visible = modeVisible(entry.instance);
    });
    el('mode-copy').textContent = modeCopy(state.mode);
  }

  function setMode(mode) {
    state.mode = mode;
    document.querySelectorAll('.modes button[data-mode]').forEach(function (button) {
      button.setAttribute('aria-pressed', button.getAttribute('data-mode') === mode ? 'true' : 'false');
    });
    updatePoses();
    look();
    var plan = el('plan-card');
    var lights = el('light-card');
    if (plan) plan.classList.toggle('is-focus', mode === 'plan');
    if (lights) lights.classList.toggle('is-focus', mode === 'lighting');
  }

  function look() {
    if (!state.camera || !state.controls || !state.manifest) return;
    var size = state.manifest.assembled_size_mm;
    var cx = (size.min_mm[0] + size.max_mm[0]) / 2;
    var cy = (size.min_mm[1] + size.max_mm[1]) / 2;
    var cz = size.max_mm[2] * 0.42;
    var camera = state.camera;
    var controls = state.controls;
    if (state.mode === 'plan') {
      camera.position.set(cx, cy - size.y * 0.15, size.max_mm[2] + size.y * 0.95);
      controls.target.set(cx, cy, state.storey === 1 ? 20 : (state.storey === 2 ? 140 : 260));
    } else if (state.mode === 'attachment') {
      camera.position.set(280, -220, 80);
      controls.target.set(280, 20, 60);
    } else if (state.mode === 'lighting') {
      camera.position.set(cx + size.x * 0.2, cy - size.y * 1.35, cz + 80);
      controls.target.set(cx, cy, 80);
    } else if (state.mode === 'open') {
      camera.position.set(cx + size.x * 0.35, cy - size.y * 1.85, cz + size.z * 0.35);
      controls.target.set(cx, cy, cz);
    } else {
      camera.position.set(cx + size.x * 0.85, cy - size.y * 1.15, cz + size.z * 0.45);
      controls.target.set(cx, cy, cz);
    }
    controls.update();
  }

  function svgEl(name, attrs) {
    var node = document.createElementNS('http://www.w3.org/2000/svg', name);
    Object.keys(attrs).forEach(function (key) { node.setAttribute(key, attrs[key]); });
    return node;
  }

  function drawPlan(storey) {
    var host = el('plan-svg');
    if (!host || !state.manifest || !state.manifest.plan) return;
    var level = state.manifest.plan.storeys.filter(function (item) { return item.storey === storey; })[0];
    clear(host);
    if (!level) return;
    var minX = -70;
    var maxX = 560;
    var minY = -70;
    var maxY = 250;
    var scale = 1.05;
    function X(value) { return (value - minX) * scale; }
    function Y(value) { return (maxY - value) * scale; }
    host.style.position = 'relative';
    host.style.height = ((maxY - minY) * scale) + 'px';
    host.style.background = '#243040';
    host.setAttribute('role', 'img');
    host.setAttribute('aria-label', 'Floor plan of storey ' + storey);
    function mark(item, style) {
      var node = document.createElement('div');
      node.style.position = 'absolute';
      node.style.left = X(item.x0) + 'px';
      node.style.top = Y(item.y1) + 'px';
      node.style.width = Math.max(4, (item.x1 - item.x0) * scale) + 'px';
      node.style.height = Math.max(4, (item.y1 - item.y0) * scale) + 'px';
      node.style.boxSizing = 'border-box';
      Object.keys(style).forEach(function (key) { node.style[key] = style[key]; });
      host.appendChild(node);
      return node;
    }
    (level.rooms || []).forEach(function (room) {
      var node = mark(room, {
        background: '#314158',
        border: '2px solid #e0b07a',
        color: '#f4f1ea',
        fontSize: '12px',
        fontWeight: '700',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: '2px'
      });
      node.textContent = room.name;
    });
    (level.stairs || []).forEach(function (stair) {
      var node = mark(stair, {
        background: 'repeating-linear-gradient(90deg, transparent, transparent 5px, #e0b07a 5px, #e0b07a 7px)',
        border: '2px dashed #e0b07a'
      });
      node.title = stair.id;
    });
    (level.doors || []).forEach(function (door) {
      mark(door, { background: '#8eb4c8', zIndex: '2' });
    });
    (level.lights || []).forEach(function (light) {
      var node = document.createElement('div');
      node.style.position = 'absolute';
      node.style.left = (X(light.x) - 5) + 'px';
      node.style.top = (Y(light.y) - 5) + 'px';
      node.style.width = '10px';
      node.style.height = '10px';
      node.style.borderRadius = '50%';
      node.style.background = light.kind === 'lantern' ? '#f0d78c' : '#fff4d2';
      node.style.border = '2px solid #1a140c';
      node.style.zIndex = '3';
      node.title = light.id;
      host.appendChild(node);
    });
    var copy = el('plan-copy');
    if (copy) {
      var names = (level.rooms || []).map(function (room) { return room.name; }).join(', ');
      copy.textContent = 'Storey ' + storey + ' at ' + level.floor_z + ' mm. ' + names + '. Dashed bands are the stair. Blue marks are doorways. Dots are lamps on the fixed frame.';
    }
  }

  function drawLighting() {
    var host = el('light-svg');
    if (!host || !state.manifest || !state.manifest.lighting) return;
    clear(host);
    var light = state.manifest.lighting;
    var svg = svgEl('svg', { viewBox: '0 0 420 220', role: 'img', 'aria-label': 'Ceiling fixture cross section' });
    svg.appendChild(svgEl('rect', { x: 0, y: 0, width: 420, height: 220, fill: '#1a1f27' }));
    svg.appendChild(svgEl('rect', { x: 40, y: 36, width: 250, height: 28, fill: '#d9c7a4' }));
    svg.appendChild(svgEl('rect', { x: 70, y: 40, width: 150, height: 8, fill: '#1a1f27' }));
    svg.appendChild(svgEl('rect', { x: 148, y: 64, width: 24, height: 18, fill: '#e6d7b0' }));
    svg.appendChild(svgEl('rect', { x: 132, y: 78, width: 56, height: 36, rx: 18, fill: '#e6d7b0' }));
    svg.appendChild(svgEl('rect', { x: 146, y: 88, width: 28, height: 14, fill: '#1a1f27' }));
    svg.appendChild(svgEl('rect', { x: 150, y: 108, width: 8, height: 8, fill: '#1a1f27' }));
    svg.appendChild(svgEl('rect', { x: 164, y: 108, width: 8, height: 8, fill: '#1a1f27' }));
    var labels = [
      [40, 28, '4×3 channel'],
      [78, 54, 'resistor pocket, not in the lamp'],
      [196, 74, '2 mm feed'],
      [196, 100, '6×6×3 cavity'],
      [196, 128, 'captive diffuser']
    ];
    labels.forEach(function (row) {
      var text = svgEl('text', { x: row[0], y: row[1], fill: '#e8eaed', 'font-size': 11 });
      text.textContent = row[2];
      svg.appendChild(text);
    });
    host.appendChild(svg);
    var note = el('light-copy');
    if (note) {
      note.textContent = light.fixture_count + ' fixtures on this house. Research scenario was 24 LEDs and 0.48 A, which is not this count. At the 20 mA planning figure this house is ' + light.house_budget_A_at_20mA + ' A, and that current was not measured. ' + light.protection_note;
    }
    var routes = el('light-routes');
    if (routes) {
      clear(routes);
      (light.route || []).forEach(function (line) { routes.appendChild(text('li', line)); });
    }
  }

  function claim(manifest) {
    var flags = manifest.validation;
    if (flags.printed || flags.measured || flags.physically_verified || flags.forces_tested || flags.h3c_sliced || flags.electrically_tested || flags.protection_finalized || flags.led_fit_validated) {
      throw new Error('manifest claims a test that was not run');
    }
    if (!flags.cad_validated) return 'CAD checks did not pass. Not printed.';
    return 'CAD-checked, unprinted model. Forces, fatigue, and stability were not tested. Not a toy-safety certification and not an H3C slice.';
  }

  function renderChrome(manifest) {
    el('rev').textContent = 'v' + manifest.version + ' · unprinted';
    el('title').textContent = manifest.name;
    el('sub').textContent = manifest.scale + ' · ' + manifest.description;
    el('claim').textContent = claim(manifest);
    var size = manifest.assembled_size_mm;
    var magnet = manifest.magnet || {};
    var facts = [
      [size.x.toFixed(0) + ' × ' + size.y.toFixed(0) + ' × ' + size.z.toFixed(0), 'Assembly, mm'],
      [String(manifest.rooms.length), 'Different rooms'],
      [String(manifest.parts.length), 'Printable parts'],
      [magnet.nominal_mm[0] + ' × ' + magnet.nominal_mm[1], 'Nominal magnet, mm'],
      [String((manifest.lighting && manifest.lighting.fixture_count) || 0), 'Light fixtures'],
      [magnet.status === 'NOMINAL_NOT_FIT_APPROVED' ? 'Not proven' : 'Check', 'Pocket fit']
    ];
    var factsNode = el('facts');
    clear(factsNode);
    facts.forEach(function (fact) {
      var node = document.createElement('div');
      node.className = 'fact';
      node.appendChild(text('b', fact[0]));
      node.appendChild(text('span', fact[1]));
      factsNode.appendChild(node);
    });

    var printRoot = el('print-root');
    clear(printRoot);
    var order = document.createElement('ol');
    (manifest.magnet_install_steps || []).forEach(function (line) {
      order.appendChild(text('li', line));
    });
    printRoot.appendChild(order);
    var rooms = document.createElement('ul');
    (manifest.rooms || []).forEach(function (room) {
      rooms.appendChild(text('li', room.id + ', storey ' + room.storey + ': ' + room.note));
    });
    printRoot.appendChild(rooms);
    var limits = document.createElement('ul');
    manifest.limits.forEach(function (line) {
      limits.appendChild(text('li', line));
    });
    printRoot.appendChild(limits);
    printRoot.appendChild(text('p', (manifest.legacy_interface && manifest.legacy_interface.note) || '', 'muted'));
    drawPlan(state.storey);
    drawLighting();

    var table = document.createElement('table');
    var head = document.createElement('tr');
    ['Part', 'Qty', 'Printed size, mm', 'Z, mm'].forEach(function (label) {
      head.appendChild(text('th', label));
    });
    var thead = document.createElement('thead');
    thead.appendChild(head);
    table.appendChild(thead);
    var body = document.createElement('tbody');
    manifest.bom.forEach(function (row) {
      var part = manifest.parts.filter(function (item) { return item.id === row.part; })[0];
      var tr = document.createElement('tr');
      var name = document.createElement('td');
      var link = document.createElement('a');
      link.href = '/dollhouse/queen-anne/' + row.file;
      link.textContent = row.part;
      name.appendChild(link);
      tr.appendChild(name);
      tr.appendChild(text('td', String(row.qty)));
      tr.appendChild(text('td', part.bbox_mm.map(function (value) { return Math.round(value); }).join(' × ')));
      tr.appendChild(text('td', part.bbox_mm[2] + ' tall'));
      body.appendChild(tr);
    });
    table.appendChild(body);
    el('part-list').appendChild(table);
  }

  function bootViewer(manifest, geometries) {
    var view = el('view');
    var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    if (THREE.sRGBEncoding) renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.setClearColor(0x14181e, 1);
    view.appendChild(renderer.domElement);

    var scene = new THREE.Scene();
    var size = manifest.assembled_size_mm;
    var center = new THREE.Vector3(
      (size.min_mm[0] + size.max_mm[0]) / 2,
      (size.min_mm[1] + size.max_mm[1]) / 2,
      size.max_mm[2] * 0.42
    );
    var camera = new THREE.PerspectiveCamera(38, 1, 1, 8000);
    camera.position.set(center.x + size.x * 0.85, center.y - size.y * 1.7, center.z + size.z * 0.55);
    camera.up.set(0, 0, 1);

    var hemi = new THREE.HemisphereLight(0xf4f7fb, 0x2a313c, 0.85);
    scene.add(hemi);
    var key = new THREE.DirectionalLight(0xfff4e8, 1.15);
    key.position.set(400, -600, 900);
    scene.add(key);
    var fill = new THREE.DirectionalLight(0xc5d4e8, 0.4);
    fill.position.set(-500, 300, 200);
    scene.add(fill);

    var ground = new THREE.Mesh(
      new THREE.CircleGeometry(900, 48),
      new THREE.MeshStandardMaterial({ color: 0x1c222b, roughness: 1, metalness: 0 })
    );
    ground.position.set(center.x, center.y, -0.4);
    scene.add(ground);

    manifest.instances.forEach(function (instance) {
      var geometry = geometries[instance.part];
      var material = new THREE.MeshStandardMaterial({
        color: instance.color,
        roughness: instance.role === 'roof' ? 0.62 : 0.78,
        metalness: instance.role === 'roof' ? 0.08 : 0.03,
        side: THREE.DoubleSide
      });
      var mesh = new THREE.Mesh(geometry, material);
      scene.add(mesh);
      state.entries.push({ instance: instance, mesh: mesh });
      state.triangles += geometry.attributes.position.count / 3;
    });

    var controls = new THREE.OrbitControls(camera, renderer.domElement);
    state.camera = camera;
    state.controls = controls;
    controls.target.copy(center);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.maxPolarAngle = Math.PI * 0.92;
    controls.minDistance = 180;
    controls.maxDistance = 2800;
    controls.update();

    function resize() {
      var width = view.clientWidth;
      var height = view.clientHeight;
      if (!width || !height) return;
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
    }
    resize();
    window.addEventListener('resize', resize);
    if (window.ResizeObserver) new ResizeObserver(resize).observe(view);

    function frame() {
      controls.update();
      renderer.render(scene, camera);
      requestAnimationFrame(frame);
    }
    updatePoses();
    frame();
    var status = el('view-status');
    if (status) status.remove();
    state.booted = true;
  }

  function fail(error) {
    state.errors.push(String(error));
    el('error').textContent = String(error && error.message ? error.message : error);
  }

  document.querySelectorAll('.modes button[data-mode]').forEach(function (button) {
    button.addEventListener('click', function () {
      setMode(button.getAttribute('data-mode'));
    });
  });
  document.querySelectorAll('[data-storey]').forEach(function (button) {
    button.addEventListener('click', function () {
      state.storey = Number(button.getAttribute('data-storey'));
      document.querySelectorAll('[data-storey]').forEach(function (other) {
        other.setAttribute('aria-pressed', other === button ? 'true' : 'false');
      });
      if (state.mode !== 'plan') setMode('plan');
      else {
        updatePoses();
        look();
        drawPlan(state.storey);
      }
    });
  });

  fetch('/dollhouse/queen-anne/manifest.json')
    .then(function (response) {
      if (!response.ok) throw new Error('Manifest did not load');
      return response.json();
    })
    .then(function (manifest) {
      state.manifest = manifest;
      renderChrome(manifest);
      var ids = [];
      manifest.parts.forEach(function (part) {
        if (ids.indexOf(part.id) === -1) ids.push(part.id);
      });
      var geometries = {};
      var done = 0;
      return Promise.all(ids.map(function (id) {
        var part = manifest.parts.filter(function (item) { return item.id === id; })[0];
        return fetch('/dollhouse/queen-anne/' + part.file).then(function (response) {
          if (!response.ok) throw new Error(part.file + ' did not load');
          return response.arrayBuffer();
        }).then(function (buffer) {
          var parsed = parseStl(buffer);
          var geometry = new THREE.BufferGeometry();
          geometry.setAttribute('position', new THREE.BufferAttribute(parsed.positions, 3));
          geometry.computeVertexNormals();
          geometries[id] = geometry;
          done += 1;
          var status = el('view-status');
          if (status) status.querySelector('p').textContent = 'Loaded ' + done + ' of ' + ids.length + ' STLs.';
        });
      })).then(function () {
        bootViewer(manifest, geometries);
      });
    })
    .catch(fail);

  window.__queenAnne = state;
})();
