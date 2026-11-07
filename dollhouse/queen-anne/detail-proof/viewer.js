(function () {
  var COLORS = {
    floor: 0xc4894e,
    "door-frame": 0xf3ead8,
    "window-wall": 0x6f917c,
    sash: 0xe7dcc8,
    sofa: 0x8d5a32,
    chair: 0xa56b3c,
    table: 0xc4894e,
    bookcase: 0x6a432c,
    "stair-sample": 0x8d5a32,
    light: 0xe6c98a,
    beam: 0xf6efe4,
    lace: 0xf3ead8,
    bracket: 0xf3ead8,
    "shingle-sample": 0x2a3642
  };
  var SHOTS = {
    room: { pos: [70, -150, 78], at: [84, 64, 36] },
    window: { pos: [96, -48, 62], at: [79, 118, 96] },
    lace: { pos: [250, -30, 28], at: [250, 23, 8] },
    bracket: { pos: [188, 30, 36], at: [208, 52, 16] },
    shingles: { pos: [250, 60, 48], at: [222, 112, 12] },
    light: { pos: [16, 50, 128], at: [46, 78, 142] },
    neutral: { pos: [70, -150, 78], at: [84, 64, 36] },
    section: { pos: [10, 70, 80], at: [79, 119, 90] }
  };

  var view = document.getElementById("view");
  var status = document.getElementById("status");
  var renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0x12161c, 1);
  renderer.localClippingEnabled = true;
  if (THREE.ACESFilmicToneMapping !== undefined) {
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
  }
  view.appendChild(renderer.domElement);

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(32, 1, 0.5, 4000);
  camera.up.set(0, 0, 1);
  var controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.target.set(80, 70, 40);
  camera.position.set(80, -180, 90);

  scene.add(new THREE.HemisphereLight(0xfff6ee, 0x1c2420, 0.55));
  var key = new THREE.DirectionalLight(0xfff1e0, 1.45);
  key.position.set(-80, -160, 220);
  scene.add(key);
  var fill = new THREE.DirectionalLight(0xb7c6d4, 0.32);
  fill.position.set(200, 80, 60);
  scene.add(fill);

  var clip = new THREE.Plane(new THREE.Vector3(0, -1, 0), 119.2);
  var meshes = [];
  var neutral = false;
  var section = false;

  function material(id) {
    var color = neutral ? 0xb7b1a6 : (COLORS[id] || 0xcccccc);
    var mats = new THREE.MeshStandardMaterial({
      color: color,
      roughness: id === "shingle-sample" ? 0.78 : 0.55,
      metalness: id === "light" ? 0.22 : 0.03,
      side: THREE.DoubleSide,
      clippingPlanes: section ? [clip] : []
    });
    return mats;
  }

  function applyLook() {
    meshes.forEach(function (entry) {
      entry.mesh.material.dispose();
      entry.mesh.material = material(entry.id);
    });
  }

  function shot(name) {
    var item = SHOTS[name];
    camera.position.set(item.pos[0], item.pos[1], item.pos[2]);
    controls.target.set(item.at[0], item.at[1], item.at[2]);
    neutral = name === "neutral";
    section = name === "section";
    applyLook();
    controls.update();
    document.querySelectorAll("button[data-shot]").forEach(function (button) {
      button.setAttribute("aria-pressed", button.getAttribute("data-shot") === name ? "true" : "false");
    });
  }

  function parseStl(buffer) {
    var viewIn = new DataView(buffer);
    var faces = viewIn.getUint32(80, true);
    var geom = new THREE.BufferGeometry();
    var positions = new Float32Array(faces * 9);
    var normals = new Float32Array(faces * 9);
    var offset = 84;
    for (var i = 0; i < faces; i += 1) {
      var base = i * 9;
      normals[base] = normals[base + 3] = normals[base + 6] = viewIn.getFloat32(offset, true);
      normals[base + 1] = normals[base + 4] = normals[base + 7] = viewIn.getFloat32(offset + 4, true);
      normals[base + 2] = normals[base + 5] = normals[base + 8] = viewIn.getFloat32(offset + 8, true);
      offset += 12;
      for (var v = 0; v < 3; v += 1) {
        positions[base + v * 3] = viewIn.getFloat32(offset, true);
        positions[base + v * 3 + 1] = viewIn.getFloat32(offset + 4, true);
        positions[base + v * 3 + 2] = viewIn.getFloat32(offset + 8, true);
        offset += 12;
      }
      offset += 2;
    }
    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geom.setAttribute("normal", new THREE.BufferAttribute(normals, 3));
    return geom;
  }

  function resize() {
    var width = view.clientWidth;
    var height = view.clientHeight;
    if (!width || !height) return;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
  }
  window.addEventListener("resize", resize);
  resize();

  document.querySelectorAll("button[data-shot]").forEach(function (button) {
    button.addEventListener("click", function () { shot(button.getAttribute("data-shot")); });
  });

  fetch("assembly.json").then(function (response) { return response.json(); }).then(function (assembly) {
    return Promise.all(assembly.instances.map(function (instance) {
      return fetch(instance.file).then(function (response) { return response.arrayBuffer(); }).then(function (buffer) {
        var mesh = new THREE.Mesh(parseStl(buffer), material(instance.id));
        scene.add(mesh);
        meshes.push({ id: instance.id, mesh: mesh });
      });
    }));
  }).then(function () {
    status.textContent = meshes.length + " solids, already placed. Neutral and Section are the same meshes.";
    shot("room");
  }).catch(function (error) {
    status.textContent = String(error);
  });

  function frame() {
    requestAnimationFrame(frame);
    controls.update();
    renderer.render(scene, camera);
  }
  frame();
}());
