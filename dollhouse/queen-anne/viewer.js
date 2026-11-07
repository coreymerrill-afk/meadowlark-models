/* Queen Anne viewer. Every mesh is a manifest STL. Modes move or hide those meshes. */
(function () {
  'use strict';

  var state = {
    manifest: null,
    entries: [],
    mode: 'closed',
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
      case 'attachment':
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

  function modeVisible(instance) {
    if (state.mode === 'remove-panels') {
      var group = instance.motion ? instance.motion.group : '';
      return group !== 'front' && group !== 'end';
    }
    if (state.mode === 'attachment') {
      return instance.id === 'hall-l1-front' || instance.id === 'hall-l1-frame' || instance.role === 'coupon';
    }
    return true;
  }

  function modeCopy(mode) {
    switch (mode) {
      case 'closed':
        return 'Closed. Every roof sits on its own plate. Panels are on their sill hooks. This is the resting assembly, not the open view.';
      case 'open':
        return 'Open. Panels are lifted and pulled out. Roofs are slid, lifted, and parked up and back so they are obviously off their seats.';
      case 'remove-panels':
        return 'Panels hidden. The frames, floors, and roofs stay. The hidden panels are the same STLs.';
      case 'roof':
        return 'Roofs parked off their plates. Panels stay seated. Each roof is one solid that bears on its own frame.';
      case 'explode':
        return 'Exploded along the manifest vectors, including furniture.';
      case 'attachment':
        return 'Attachment. The entry frame and its panel, plus the coupon parts. The sill hook carries the panel. Magnet pockets are the open channels in the stiles and posts. Slide a capture bar in after the disc. 5.0 × 2.8 mm is nominal, not a proven fit.';
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
    document.querySelectorAll('.modes button').forEach(function (button) {
      button.setAttribute('aria-pressed', button.getAttribute('data-mode') === mode ? 'true' : 'false');
    });
    updatePoses();
  }

  function claim(manifest) {
    var flags = manifest.validation;
    if (flags.printed || flags.measured || flags.physically_verified || flags.forces_tested || flags.h3c_sliced) {
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

  document.querySelectorAll('.modes button').forEach(function (button) {
    button.addEventListener('click', function () {
      setMode(button.getAttribute('data-mode'));
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
