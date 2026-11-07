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

  function modeMatrix(instance) {
    var mode = state.mode;
    var motion = instance.motion;
    var group = motion ? motion.group : '';
    switch (mode) {
      case 'closed':
        return instance.transform;
      case 'open':
        if (group === 'front' || group === 'end' || group === 'balcony') {
          return mul(translate(addVec(motion.lift, motion.pull)), instance.transform);
        }
        return instance.transform;
      case 'remove-panels':
        return instance.transform;
      case 'roof':
        if (group === 'roof') return mul(translate(addVec(motion.lift, motion.pull)), instance.transform);
        return instance.transform;
      case 'explode':
        return mul(translate(instance.explode_mm), instance.transform);
      default:
        return assertNever(mode);
    }
  }

  function modeVisible(instance) {
    if (state.mode !== 'remove-panels') return true;
    var group = instance.motion ? instance.motion.group : '';
    return group !== 'front' && group !== 'end' && group !== 'balcony';
  }

  function modeCopy(mode) {
    switch (mode) {
      case 'closed':
        return 'Closed. Panels are seated and the roofs are on.';
      case 'open':
        return 'Open. Front and end panels are in the lifted-and-pulled pose. The balcony is off its ledges. Roofs stay on.';
      case 'remove-panels':
        return 'Panels off. Front panels, end panels, and the balcony are hidden. The frames and rear shear stay. Those hidden meshes are the same STLs.';
      case 'roof':
        return 'Roof off. The three roof shells are lifted clear of the plates. Panels stay seated.';
      case 'explode':
        return 'Exploded. Every instance, including furniture, is shifted along its manifest vector.';
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
    var facts = [
      [size.x.toFixed(0) + ' × ' + size.y.toFixed(0) + ' × ' + size.z.toFixed(0), 'Assembly, mm'],
      [String(manifest.parts.length), 'Printable parts'],
      [String(manifest.instances.length), 'Meshes in view'],
      [manifest.module_mm.clear_height + ' mm', 'Clear storey'],
      [Math.round(manifest.legacy_interface.depth_mm) + ' mm deep', 'Bay, not two tiles']
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
    order.appendChild(text('li', 'Print qa_coupon_socket_v1 and qa_coupon_plug_v1. The tongue should drop into the pocket. The two holes are a legacy size gauge, not a joint this house uses.'));
    order.appendChild(text('li', 'Print one bay: base, two front posts, two rear posts, one plate, one rear shear, one front panel, one end panel. Seat the posts, plate, shear, and panel before printing the other eight bays.'));
    order.appendChild(text('li', 'The rest of the kit is the same parts. Roofs, porch, balcony, partitions, and furniture come after a bay fits.'));
    printRoot.appendChild(order);
    var limits = document.createElement('ul');
    manifest.limits.forEach(function (line) {
      limits.appendChild(text('li', line));
    });
    printRoot.appendChild(limits);
    printRoot.appendChild(text('p', manifest.legacy_interface.conclusion, 'muted'));

    var table = document.createElement('table');
    var head = document.createElement('tr');
    ['Part', 'Qty', 'Printed size, mm', 'First bay'].forEach(function (label) {
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
      tr.appendChild(text('td', row.first_bay_print ? 'Yes' : ''));
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
