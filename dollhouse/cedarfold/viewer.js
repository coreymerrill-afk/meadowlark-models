/* Cedarfold viewer. Meshes are the CAD STLs. The hinge and drawers use the manifest transforms. */
(function () {
  'use strict';

  var state = {
    manifest: null,
    entries: [],
    byFile: {},
    failed: [],
    hinge: 0,
    drawer: 0,
    explode: false,
    coupons: false,
    selected: null,
    booted: false
  };

  function el(id) { return document.getElementById(id); }

  function text(tag, value, className) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    node.textContent = value;
    return node;
  }

  function assertNever(value) {
    throw new Error('Unhandled view: ' + String(value));
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

  function colorOf(instance) {
    var hex = instance.color || '#c4a06a';
    return parseInt(hex.replace('#', ''), 16);
  }

  function poseMatrix(instance) {
    var angle = instance.wing === 'garden' ? state.hinge * Math.PI / 180 : 0;
    var slide = instance.drawer_travel_mm ? state.drawer * instance.drawer_travel_mm : 0;
    var shift = instance.translate_mm || [0, 0, 0];
    var boom = state.explode && instance.explode_mm ? instance.explode_mm : [0, 0, 0];
    var x = shift[0] + boom[0];
    var y = shift[1] + slide + boom[1];
    var z = shift[2] + boom[2];
    var c = Math.cos(angle);
    var s = Math.sin(angle);
    return [
      c, -s, 0, c * x - s * y,
      s, c, 0, s * x + c * y,
      0, 0, 1, z,
      0, 0, 0, 1
    ];
  }

  function applyPose() {
    state.entries.forEach(function (entry) {
      var m = poseMatrix(entry.instance);
      entry.mesh.matrix.set(
        m[0], m[1], m[2], m[3],
        m[4], m[5], m[6], m[7],
        m[8], m[9], m[10], m[11],
        m[12], m[13], m[14], m[15]
      );
      entry.mesh.matrixAutoUpdate = false;
      entry.mesh.visible = state.coupons || entry.instance.role !== 'coupon';
    });
    var hinge = el('hinge-readout');
    if (hinge) hinge.textContent = 'Garden wing ' + Math.abs(state.hinge).toFixed(0) + '° from open';
    var drawer = el('drawer-readout');
    if (drawer && state.manifest) {
      drawer.textContent = 'Drawers ' + (state.drawer * state.manifest.drawer.travel_mm).toFixed(1) + ' mm out';
    }
  }

  function look(preset) {
    if (!state.camera || !state.controls || !state.manifest) return;
    var size = state.manifest.open_size_mm;
    var cx = (size.min_mm[0] + size.max_mm[0]) / 2;
    var cy = (size.min_mm[1] + size.max_mm[1]) / 2;
    var cz = (size.min_mm[2] + size.max_mm[2]) / 2;
    var eye = [cx + 240, cy + 540, cz + 120];
    var at = [cx, cy - 10, 120];
    switch (preset) {
      case 'outside':
        break;
      case 'hearth':
        eye = [-90, 390, 140];
        at = [-110, 60, 100];
        break;
      case 'garden':
        eye = [100, 400, 150];
        at = [100, 70, 110];
        break;
      case 'stairs':
        eye = [-50, 340, 130];
        at = [-50, 50, 90];
        break;
      case 'drawers':
        eye = [0, 480, 55];
        at = [0, 90, 24];
        break;
      case 'hinge':
        eye = [110, -150, 80];
        at = [0, 8, 40];
        break;
      default:
        assertNever(preset);
    }
    state.camera.position.set(eye[0], eye[1], eye[2]);
    state.controls.target.set(at[0], at[1], at[2]);
    state.controls.update();
  }

  function selectEntry(entry) {
    state.selected = entry ? entry.instance.id : null;
    state.entries.forEach(function (item) {
      var on = entry && item.mesh === entry.mesh;
      if (item.mesh.material && item.mesh.material.emissive) {
        item.mesh.material.emissive.setHex(on ? 0x4a3018 : 0x000000);
      }
    });
    document.querySelectorAll('#part-list button').forEach(function (button) {
      button.classList.toggle('on', entry && button.getAttribute('data-id') === entry.instance.id);
    });
    var label = el('picked');
    if (!label) return;
    if (!entry) {
      label.textContent = 'Click a part to name it.';
      return;
    }
    label.textContent = entry.instance.name + (entry.instance.print ? '' : ' — not a print part');
  }

  function boot(manifest) {
    var view = el('view');
    var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    if (THREE.sRGBEncoding) renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.setClearColor(0x241c17, 1);
    view.appendChild(renderer.domElement);
    var scene = new THREE.Scene();
    var camera = new THREE.PerspectiveCamera(35, 1, 1, 8000);
    camera.up.set(0, 0, 1);
    scene.add(new THREE.HemisphereLight(0xfff4e8, 0x2a211c, 0.85));
    var key = new THREE.DirectionalLight(0xfff1df, 1.35);
    key.position.set(-180, -420, 520);
    scene.add(key);
    var fill = new THREE.DirectionalLight(0xd7c4b0, 0.35);
    fill.position.set(300, 200, 180);
    scene.add(fill);
    var controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.maxPolarAngle = Math.PI * 0.96;
    controls.minDistance = 40;
    controls.maxDistance = 4000;
    state.camera = camera;
    state.controls = controls;
    state.renderer = renderer;
    state.scene = scene;

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
    look('outside');

    var raycaster = new THREE.Raycaster();
    var pointer = new THREE.Vector2();
    var press = null;
    view.addEventListener('pointerdown', function (event) {
      press = { x: event.clientX, y: event.clientY };
    });
    view.addEventListener('pointerup', function (event) {
      if (!press) return;
      var moved = (event.clientX - press.x) * (event.clientX - press.x) + (event.clientY - press.y) * (event.clientY - press.y);
      press = null;
      if (moved > 16) return;
      var rect = view.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      var hits = raycaster.intersectObjects(state.entries.filter(function (entry) {
        return entry.mesh.visible;
      }).map(function (entry) { return entry.mesh; }), false);
      if (!hits.length) {
        selectEntry(null);
        return;
      }
      var chosen = state.entries.filter(function (entry) { return entry.mesh === hits[0].object; })[0];
      selectEntry(chosen || null);
    });

    function frame() {
      controls.update();
      renderer.render(scene, camera);
      requestAnimationFrame(frame);
    }
    frame();
    state.booted = true;
  }

  function addInstance(instance, geometry) {
    var material = new THREE.MeshStandardMaterial({
      color: colorOf(instance),
      roughness: instance.role === 'catalog' ? 0.35 : 0.72,
      metalness: instance.role === 'catalog' ? 0.55 : 0.02,
      side: THREE.DoubleSide
    });
    var mesh = new THREE.Mesh(geometry, material);
    state.scene.add(mesh);
    state.entries.push({ instance: instance, mesh: mesh });
    applyPose();
  }

  function status(title, copy, offerRetry) {
    var node = el('view-status');
    if (!node) return;
    node.querySelector('strong').textContent = title;
    node.querySelector('p').textContent = copy;
    var button = node.querySelector('button');
    if (offerRetry && !button) {
      button = document.createElement('button');
      button.type = 'button';
      button.textContent = 'Retry failed parts';
      button.addEventListener('click', function () { loadFiles(state.failed.slice()); });
      node.appendChild(button);
    }
    if (!offerRetry && button) button.remove();
    node.hidden = false;
  }

  function hideStatus() {
    var node = el('view-status');
    if (node) node.hidden = true;
  }

  function uniqueFiles(instances) {
    var files = [];
    instances.forEach(function (instance) {
      if (files.indexOf(instance.file) === -1) files.push(instance.file);
    });
    return files;
  }

  function loadFiles(files) {
    if (!files.length) {
      hideStatus();
      return Promise.resolve();
    }
    var pending = files.slice();
    var done = 0;
    var total = files.length;
    state.failed = state.failed.filter(function (file) { return files.indexOf(file) === -1; });
    status('Loading the CAD meshes', 'Orbit works while parts arrive.', false);

    function next() {
      var file = pending.shift();
      if (!file) {
        if (state.failed.length) {
          status(
            'Some parts did not load',
            state.failed.length + ' file(s) failed. The parts that loaded stay on screen.',
            true
          );
        } else {
          hideStatus();
        }
        return Promise.resolve();
      }
      if (state.byFile[file]) {
        done += 1;
        return next();
      }
      return fetch('/dollhouse/cedarfold/' + file).then(function (response) {
        if (!response.ok) throw new Error(file + ' did not load (' + response.status + ')');
        return response.arrayBuffer();
      }).then(function (buffer) {
        var parsed = parseStl(buffer);
        var geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(parsed.positions, 3));
        geometry.computeVertexNormals();
        state.byFile[file] = geometry;
        state.manifest.instances.forEach(function (instance) {
          if (instance.file === file) addInstance(instance, geometry);
        });
        done += 1;
        status('Loading the CAD meshes', 'Loaded ' + done + ' of ' + total + ' files.', false);
        return next();
      }).catch(function (error) {
        if (state.failed.indexOf(file) === -1) state.failed.push(file);
        var node = el('error');
        if (node) node.textContent = String(error && error.message ? error.message : error);
        done += 1;
        return next();
      });
    }
    return next();
  }

  function fillParts() {
    var list = el('part-list');
    if (!list) return;
    list.textContent = '';
    state.manifest.instances.forEach(function (instance) {
      var button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('data-id', instance.id);
      button.textContent = instance.name;
      button.addEventListener('click', function () {
        var entry = state.entries.filter(function (item) { return item.instance.id === instance.id; })[0];
        selectEntry(entry || null);
      });
      list.appendChild(button);
    });
  }

  function wire() {
    var hinge = el('hinge');
    var drawer = el('drawer');
    if (hinge) {
      hinge.addEventListener('input', function () {
        state.hinge = -Number(hinge.value);
        applyPose();
      });
    }
    if (drawer) {
      drawer.addEventListener('input', function () {
        state.drawer = Number(drawer.value) / 100;
        applyPose();
      });
    }
    document.querySelectorAll('[data-hinge]').forEach(function (button) {
      button.addEventListener('click', function () {
        state.hinge = -Number(button.getAttribute('data-hinge'));
        if (hinge) hinge.value = String(Math.abs(state.hinge));
        document.querySelectorAll('[data-hinge]').forEach(function (other) {
          other.setAttribute('aria-pressed', other === button ? 'true' : 'false');
        });
        applyPose();
      });
    });
    document.querySelectorAll('[data-look]').forEach(function (button) {
      button.addEventListener('click', function () {
        var preset = button.getAttribute('data-look');
        if (preset === 'drawers') {
          state.drawer = 1;
          if (drawer) drawer.value = '100';
          applyPose();
        }
        document.querySelectorAll('[data-look]').forEach(function (other) {
          other.setAttribute('aria-pressed', other === button ? 'true' : 'false');
        });
        look(preset);
      });
    });
    var explode = el('explode');
    if (explode) {
      explode.addEventListener('click', function () {
        state.explode = !state.explode;
        explode.setAttribute('aria-pressed', state.explode ? 'true' : 'false');
        applyPose();
      });
    }
    var coupons = el('coupons');
    if (coupons) {
      coupons.addEventListener('click', function () {
        state.coupons = !state.coupons;
        coupons.setAttribute('aria-pressed', state.coupons ? 'true' : 'false');
        applyPose();
      });
    }
    var reset = el('reset-view');
    if (reset) {
      reset.addEventListener('click', function () {
        state.hinge = 0;
        state.drawer = 0;
        state.explode = false;
        if (hinge) hinge.value = '0';
        if (drawer) drawer.value = '0';
        if (explode) explode.setAttribute('aria-pressed', 'false');
        document.querySelectorAll('[data-hinge]').forEach(function (button) {
          button.setAttribute('aria-pressed', button.getAttribute('data-hinge') === '0' ? 'true' : 'false');
        });
        applyPose();
        look('outside');
      });
    }
  }

  fetch('/dollhouse/cedarfold/manifest.json').then(function (response) {
    if (!response.ok) throw new Error('manifest.json did not load (' + response.status + ')');
    return response.json();
  }).then(function (manifest) {
    state.manifest = manifest;
    if (typeof THREE === 'undefined' || !THREE.OrbitControls) {
      throw new Error('The 3D library did not load.');
    }
    boot(manifest);
    fillParts();
    wire();
    return loadFiles(uniqueFiles(manifest.instances));
  }).catch(function (error) {
    var message = String(error && error.message ? error.message : error);
    status('This view did not start', message, true);
    var node = el('error');
    if (node) node.textContent = message;
  });
})();
