/* Loads manifest.json and the STL for every assembly instance.
   Transforms are the manifest 4x4s. Joints use the manifest pivot and axis. */
(function () {
  'use strict';

  var asm = window.ObservatoryAssembly;
  var state = {
    manifest: null,
    meshes: [],
    motions: {},
    explode: 0,
    selected: null,
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

  function spinsFor(instance) {
    return state.manifest.pivots.filter(function (pivot) {
      return pivot.instance_ids.indexOf(instance.id) !== -1;
    }).map(function (pivot) {
      return {
        pivot: pivot.origin_mm,
        axis: pivot.axis,
        home: pivot.home_deg,
        angle: state.motions[pivot.id],
        sign: pivot.delta_sign
      };
    });
  }

  function matrixFor(instance) {
    return asm.poseMatrix(instance.transform, spinsFor(instance), instance.explode_mm, state.explode);
  }

  function applyMatrix(mesh, matrix) {
    mesh.matrix.set(
      matrix[0][0], matrix[0][1], matrix[0][2], matrix[0][3],
      matrix[1][0], matrix[1][1], matrix[1][2], matrix[1][3],
      matrix[2][0], matrix[2][1], matrix[2][2], matrix[2][3],
      matrix[3][0], matrix[3][1], matrix[3][2], matrix[3][3]
    );
    mesh.matrixAutoUpdate = false;
  }

  function updatePoses() {
    state.meshes.forEach(function (entry) {
      applyMatrix(entry.mesh, matrixFor(entry.instance));
    });
  }

  function select(id) {
    state.selected = id;
    state.meshes.forEach(function (entry) {
      var on = entry.instance.id === id;
      entry.mesh.material.emissive.setHex(on ? 0x335566 : 0x000000);
      entry.mesh.material.opacity = !id || on ? 1 : 0.38;
    });
    document.querySelectorAll('.part-row').forEach(function (row) {
      row.classList.toggle('on', row.dataset.id === id);
    });
  }

  function renderChrome(manifest) {
    el('rev').textContent = 'v' + manifest.version + ' · unprinted';
    el('title').textContent = manifest.name;
    el('sub').textContent = manifest.description;
    el('claim').textContent = asm.claimSentence(manifest);

    var size = manifest.assembled_size_mm;
    var facts = [
      [manifest.target_printer.nozzle_mm + ' mm', 'Nozzle only'],
      [manifest.target_printer.material_first, 'First material'],
      [size.x.toFixed(0) + ' × ' + size.z.toFixed(0) + ' mm', 'Envelope, with feet'],
      [size.limit + ' mm', 'Must stay under']
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

    var motions = el('motion-panel');
    clear(motions);
    manifest.pivots.forEach(function (pivot) {
      state.motions[pivot.id] = pivot.home_deg;
      var label = document.createElement('label');
      label.className = 'slider';
      var name = text('span', pivot.label);
      var input = document.createElement('input');
      input.type = 'range';
      input.min = String(pivot.limits_deg[0]);
      input.max = String(pivot.limits_deg[1]);
      input.step = '1';
      input.value = String(pivot.home_deg);
      input.setAttribute('aria-label', pivot.label);
      var read = text('span', formatAngle(pivot));
      input.addEventListener('input', function () {
        state.motions[pivot.id] = Number(input.value);
        read.textContent = formatAngle(pivot);
        updatePoses();
      });
      label.appendChild(name);
      label.appendChild(input);
      label.appendChild(read);
      motions.appendChild(label);
    });

    var explode = el('explode');
    explode.addEventListener('input', function () {
      state.explode = Number(explode.value) / 100;
      el('explode-read').textContent = explode.value + '%';
      updatePoses();
    });
    el('btn-assemble').addEventListener('click', function () {
      state.explode = 0;
      explode.value = '0';
      el('explode-read').textContent = '0%';
      manifest.pivots.forEach(function (pivot) {
        state.motions[pivot.id] = pivot.home_deg;
      });
      motions.querySelectorAll('input').forEach(function (input, index) {
        input.value = String(manifest.pivots[index].home_deg);
        input.parentNode.lastChild.textContent = formatAngle(manifest.pivots[index]);
      });
      updatePoses();
    });

    renderParts(manifest);
    renderPrint(manifest);
  }

  function formatAngle(pivot) {
    var value = state.motions[pivot.id];
    if (pivot.id === 'telescope_altitude') return value + '° up';
    return value + '°';
  }

  function renderParts(manifest) {
    var list = el('part-list');
    clear(list);
    manifest.parts.forEach(function (part) {
      var row = document.createElement('div');
      row.className = 'part-row';
      row.dataset.id = part.id;
      var swatch = document.createElement('i');
      swatch.className = 'swatch';
      swatch.style.background = part.color_hex;
      var body = document.createElement('div');
      body.appendChild(text('strong', part.id.replace(/_/g, ' ')));
      body.appendChild(text('div', part.quantity + ' × ' + part.material + ' · ' + part.color_name + '. ' + part.print_notes, 'detail'));
      var link = document.createElement('a');
      link.href = '/observatory/' + part.filename;
      link.setAttribute('download', '');
      link.textContent = 'STL';
      row.appendChild(swatch);
      row.appendChild(body);
      row.appendChild(link);
      row.addEventListener('click', function (event) {
        if (event.target.tagName === 'A') return;
        var instance = state.meshes.find(function (entry) { return entry.instance.part_id === part.id; });
        if (instance) select(instance.instance.id);
      });
      list.appendChild(row);
    });
  }

  function renderPrint(manifest) {
    var root = el('print-root');
    clear(root);
    if (manifest.slice && manifest.slice.summary) {
      var sliceCard = document.createElement('article');
      sliceCard.className = 'card';
      sliceCard.appendChild(text('h2', 'Slice check'));
      sliceCard.appendChild(text('p', manifest.slice.summary));
      if (manifest.slice.planet_ringed) {
        sliceCard.appendChild(text('p', 'Ringed planet: ' + manifest.slice.planet_ringed));
      }
      root.appendChild(sliceCard);
    }
    root.appendChild(couponCard(manifest));
    root.appendChild(downloadCard(manifest));
    root.appendChild(stepsCard(manifest));
    root.appendChild(clearanceCard(manifest));
  }

  function couponCard(manifest) {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', manifest.coupon.title));
    card.appendChild(text('p', manifest.coupon.purpose, 'muted'));
    var list = document.createElement('ol');
    manifest.coupon.steps.forEach(function (step) { list.appendChild(text('li', step)); });
    card.appendChild(list);
    var link = document.createElement('a');
    link.href = '/observatory/' + manifest.coupon.stl;
    link.setAttribute('download', '');
    link.textContent = 'Download the coupon STL';
    card.appendChild(link);
    var checks = document.createElement('ul');
    manifest.coupon.checks.forEach(function (check) {
      checks.appendChild(text('li', check.title + ' — ' + check.result));
    });
    card.appendChild(checks);
    return card;
  }

  function downloadCard(manifest) {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Files'));
    card.appendChild(text('p', 'The 3MF is a colored assembly scene, not a Bambu plate. Re-slice the STLs in Bambu Studio on the H3C profile. The ringed planet needs supports.', 'muted'));
    var files = [
      ['coupon-stl', 'First-print coupon', manifest.artifacts.coupon_stl],
      ['individual-part-stls', 'STL package', manifest.artifacts.stl_zip],
      ['colored-assembly-scene', 'Colored 3MF scene', manifest.artifacts.scene_3mf],
      ['source', 'Generator source', manifest.artifacts.generator]
    ];
    files.forEach(function (file) {
      var row = document.createElement('div');
      row.className = 'dl-row';
      var badge = text('span', asm.fileKind(file[0]), 'badge');
      if (file[0] === 'colored-assembly-scene') badge.classList.add('scene');
      var body = document.createElement('div');
      body.appendChild(text('strong', file[1]));
      body.appendChild(text('div', file[0] === 'colored-assembly-scene' ? manifest.artifacts.scene_3mf_note : file[2], 'detail'));
      var link = document.createElement('a');
      link.href = '/observatory/' + file[2];
      link.setAttribute('download', '');
      link.textContent = 'Download';
      row.appendChild(badge);
      row.appendChild(body);
      row.appendChild(link);
      card.appendChild(row);
    });
    return card;
  }

  function stepsCard(manifest) {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Assembly'));
    var list = document.createElement('ol');
    manifest.assembly_steps.forEach(function (step) { list.appendChild(text('li', step)); });
    card.appendChild(list);
    card.appendChild(text('p', manifest.target_printer.notes, 'muted'));
    return card;
  }

  function clearanceCard(manifest) {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Design clearances'));
    card.appendChild(text('p', manifest.clearances.note, 'muted'));
    var table = document.createElement('table');
    var rows = [
      ['Axle', manifest.clearances.axle_diameter + ' mm into a ' + manifest.clearances.spin_bore_diameter + ' mm bore'],
      ['Orrery bore', manifest.clearances.orrery_bore_diameter + ' mm'],
      ['Hinge pin', manifest.clearances.hinge_pin_diameter + ' mm into a ' + manifest.clearances.hinge_hole_diameter + ' mm hole'],
      ['Dome skirt', manifest.clearances.dome_skirt_radial_clearance_per_side + ' mm radial, ' + manifest.clearances.dome_skirt_axial_gap + ' mm above the groove floor'],
      ['Deck above the shelf', manifest.clearances.deck_above_shelf + ' mm'],
      ['Inlay', manifest.clearances.inlay_lateral_gap_per_side + ' mm per side']
    ];
    rows.forEach(function (row) {
      var tr = document.createElement('tr');
      tr.appendChild(text('td', row[0]));
      tr.appendChild(text('td', row[1]));
      table.appendChild(tr);
    });
    card.appendChild(table);
    var bed = manifest.target_printer.bed_mm.join(' × ');
    var source = document.createElement('p');
    source.className = 'muted';
    source.appendChild(document.createTextNode('H3C bed ' + bed + ' mm, from '));
    var link = document.createElement('a');
    link.href = manifest.target_printer.bed_source;
    link.textContent = 'Bambu Lab H3C specifications';
    source.appendChild(link);
    source.appendChild(document.createTextNode('.'));
    card.appendChild(source);
    return card;
  }

  function bootTabs() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.tabs [role="tab"]'));
    function show(id) {
      buttons.forEach(function (button) {
        var on = button.dataset.tab === id;
        button.setAttribute('aria-selected', on ? 'true' : 'false');
        button.tabIndex = on ? 0 : -1;
      });
      ['observe', 'parts', 'print'].forEach(function (name) {
        var panel = el('panel-' + name);
        var on = name === id;
        if (name === 'observe') {
          panel.classList.toggle('tab-parked', !on);
          panel.hidden = false;
        } else {
          panel.hidden = !on;
        }
      });
      if (id === 'observe' && state.viewer) state.viewer.resize();
    }
    buttons.forEach(function (button) {
      button.addEventListener('click', function () { show(button.dataset.tab); });
    });
    var list = document.querySelector('.tabs');
    list.addEventListener('keydown', function (event) {
      var index = buttons.indexOf(document.activeElement);
      if (index < 0) return;
      var next = index;
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % buttons.length;
      else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + buttons.length) % buttons.length;
      else if (event.key === 'Home') next = 0;
      else if (event.key === 'End') next = buttons.length - 1;
      else return;
      event.preventDefault();
      buttons[next].focus();
      show(buttons[next].dataset.tab);
    });
  }

  function bootViewer(manifest) {
    var THREE = window.THREE;
    var view = el('view');
    var coarse = window.matchMedia('(pointer: coarse)').matches;
    var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, coarse ? 1.75 : 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    view.appendChild(renderer.domElement);

    var scene = new THREE.Scene();
    var root = new THREE.Group();
    root.rotation.x = -Math.PI / 2;
    scene.add(root);
    scene.add(new THREE.HemisphereLight(0xd5e4ff, 0x2a2118, 0.85));
    var key = new THREE.DirectionalLight(0xffe2b8, 1.35);
    key.position.set(80, 140, 60);
    scene.add(key);
    var rim = new THREE.DirectionalLight(0x9fd4ff, 0.7);
    rim.position.set(-90, 40, -70);
    scene.add(rim);

    var camera = new THREE.PerspectiveCamera(35, 1, 0.1, 5000);
    var controls = new (THREE.OrbitControls || window.OrbitControls)(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.screenSpacePanning = true;
    controls.touches.ONE = THREE.TOUCH.ROTATE;
    controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) controls.enableDamping = false;

    var partById = {};
    manifest.parts.forEach(function (part) { partById[part.id] = part; });
    var geometryCache = {};

    function colorOf(partId) {
      var hex = partById[partId].color_hex;
      return new THREE.Color(hex);
    }

    var jobs = manifest.assembly_instances.filter(function (instance) {
      return instance.scene === 'assembly';
    }).map(function (instance) {
      var file = '/observatory/' + partById[instance.part_id].filename;
      var ready = geometryCache[file] || fetch(file).then(function (response) {
        if (!response.ok) throw new Error(file + ' returned ' + response.status);
        return response.arrayBuffer();
      }).then(function (buffer) {
        var parsed = asm.parseStl(buffer);
        var geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(parsed.positions, 3));
        geometry.computeVertexNormals();
        geometryCache[file] = geometry;
        return geometry;
      });
      geometryCache[file] = ready;
      return Promise.resolve(ready).then(function (geometry) {
        var metal = /brass|gold/i.test(partById[instance.part_id].color_name) ? 0.28 : 0.04;
        var material = new THREE.MeshStandardMaterial({
          color: colorOf(instance.part_id),
          roughness: metal > 0.2 ? 0.38 : 0.52,
          metalness: metal,
          transparent: true
        });
        var mesh = new THREE.Mesh(geometry, material);
        applyMatrix(mesh, instance.transform);
        mesh.userData.instanceId = instance.id;
        root.add(mesh);
        state.meshes.push({ mesh: mesh, instance: instance });
        state.triangles += geometry.getAttribute('position').count / 3;
      });
    });

    Promise.all(jobs).then(function () {
      el('view-status').hidden = true;
      frame();
      state.booted = true;
    }).catch(function (error) {
      state.errors.push(String(error.message || error));
      el('error').textContent = String(error.message || error);
    });

    renderer.domElement.addEventListener('pointerdown', function (event) {
      var rect = renderer.domElement.getBoundingClientRect();
      var ray = new THREE.Raycaster();
      var ndc = new THREE.Vector2(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1
      );
      ray.setFromCamera(ndc, camera);
      var hits = ray.intersectObjects(state.meshes.map(function (entry) { return entry.mesh; }), false);
      if (hits.length) select(hits[0].object.userData.instanceId);
    });

    function resize() {
      var width = view.clientWidth;
      var height = view.clientHeight;
      if (!width || !height) return;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      if (width / height < 0.85) camera.fov = 46;
      camera.updateProjectionMatrix();
    }

    function frame() {
      var box = new THREE.Box3().setFromObject(root);
      var center = box.getCenter(new THREE.Vector3());
      var size = box.getSize(new THREE.Vector3());
      var radius = 0.5 * Math.max(size.x, size.y, size.z, 1);
      var dist = radius / Math.sin((camera.fov * Math.PI / 180) / 2) * 0.78;
      camera.position.set(center.x + dist * 0.78, center.y + dist * 0.42, center.z + dist * 0.86);
      camera.near = Math.max(0.1, radius / 80);
      camera.far = radius * 40;
      camera.updateProjectionMatrix();
      controls.target.copy(center);
      controls.update();
    }

    el('btn-reset').addEventListener('click', frame);
    el('btn-turn').addEventListener('click', function () {
      controls.autoRotate = !controls.autoRotate;
      el('btn-turn').classList.toggle('on', controls.autoRotate);
      el('btn-turn').setAttribute('aria-pressed', controls.autoRotate ? 'true' : 'false');
    });

    var playing = false;
    el('btn-play').addEventListener('click', function () {
      playing = !playing;
      el('btn-play').classList.toggle('on', playing);
      el('btn-play').setAttribute('aria-pressed', playing ? 'true' : 'false');
    });

    function tick(now) {
      requestAnimationFrame(tick);
      if (el('panel-observe').classList.contains('tab-parked')) return;
      if (playing) {
        manifest.pivots.forEach(function (pivot) {
          var span = pivot.limits_deg[1] - pivot.limits_deg[0];
          var phase = (Math.sin(now / 1400 + pivot.label.length) + 1) / 2;
          state.motions[pivot.id] = pivot.limits_deg[0] + span * phase;
        });
        document.querySelectorAll('#motion-panel input').forEach(function (input, index) {
          var pivot = manifest.pivots[index];
          input.value = String(state.motions[pivot.id]);
          input.parentNode.lastChild.textContent = formatAngle(pivot);
        });
        updatePoses();
      }
      controls.update();
      renderer.render(scene, camera);
    }

    window.addEventListener('resize', resize);
    resize();
    requestAnimationFrame(tick);
    state.viewer = { resize: resize, frame: frame };
  }

  function fail(error) {
    state.errors.push(String(error.message || error));
    el('error').textContent = String(error.message || error);
    el('claim').textContent = 'The model manifest did not load.';
  }

  fetch('/observatory/manifest.json').then(function (response) {
    if (!response.ok) throw new Error('manifest.json returned ' + response.status);
    return response.json();
  }).then(function (manifest) {
    state.manifest = manifest;
    renderChrome(manifest);
    bootTabs();
    bootViewer(manifest);
  }).catch(fail);

  window.__observatory = {
    get booted() { return state.booted; },
    get triangles() { return state.triangles; },
    get errors() { return state.errors.slice(); },
    get motions() { return state.motions; },
    sample: function (instanceId, local) {
      var entry = state.meshes.find(function (item) { return item.instance.id === instanceId; });
      var fromState = asm.apply(matrixFor(entry.instance), local);
      var e = entry.mesh.matrix.elements;
      var fromMesh = asm.apply([
        [e[0], e[4], e[8], e[12]],
        [e[1], e[5], e[9], e[13]],
        [e[2], e[6], e[10], e[14]],
        [e[3], e[7], e[11], e[15]]
      ], local);
      return { fromState: fromState, fromMesh: fromMesh };
    },
    hinge: function () {
      var tube = state.manifest.assembly_instances.find(function (item) { return item.part_id === 'telescope_tube'; });
      var pivot = state.manifest.pivots.find(function (item) { return item.id === 'telescope_altitude'; });
      return {
        point: this.sample(tube.id, [0, 0, tube.trunnion_z, 1]),
        pivot: pivot.origin_mm,
        triangles: state.triangles
      };
    }
  };
})();
