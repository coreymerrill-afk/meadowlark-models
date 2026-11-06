/* Loads all 32 STLs. The default scene is assembly.json, not a made-up layout.
   Crank motion rotates only the wheel halves, axle, and crank about the kit axle. */
(function () {
  'use strict';

  var asm = window.MarbleAssembly;
  var state = {
    manifest: null,
    assembly: null,
    geometries: {},
    meshes: [],
    shelf: [],
    pathLine: null,
    crank: 0,
    explode: 0,
    shelfOn: false,
    pathOn: false,
    selected: null,
    booted: false,
    triangles: 0,
    loadedParts: 0,
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

  function partByName(name) {
    return state.manifest.parts.find(function (part) { return part.name === name; });
  }

  function matrixFor(entry) {
    return asm.poseMatrix(entry.instance.transform, entry.instance.part, state.crank, entry.explode, state.explode);
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
      applyMatrix(entry.mesh, matrixFor(entry));
    });
  }

  function select(id) {
    state.selected = id;
    state.meshes.concat(state.shelf).forEach(function (entry) {
      var on = entry.id === id;
      entry.mesh.material.emissive.setHex(on ? 0x552233 : 0x000000);
      entry.mesh.material.opacity = !id || on ? 1 : 0.45;
    });
    document.querySelectorAll('.part-row').forEach(function (row) {
      row.classList.toggle('on', row.dataset.part === (id ? id.split('#')[0] : ''));
    });
  }

  function showTab(id) {
    document.querySelectorAll('.tabs [role="tab"]').forEach(function (button) {
      var on = button.dataset.tab === id;
      button.setAttribute('aria-selected', on ? 'true' : 'false');
      button.tabIndex = on ? 0 : -1;
    });
    ['look', 'parts', 'print'].forEach(function (name) {
      var panel = el('panel-' + name);
      var on = name === id;
      if (name === 'look') {
        panel.classList.toggle('tab-parked', !on);
        panel.hidden = false;
      } else {
        panel.hidden = !on;
      }
    });
    if (id === 'look' && state.viewer) state.viewer.resize();
  }

  function bootTabs() {
    var buttons = Array.prototype.slice.call(document.querySelectorAll('.tabs [role="tab"]'));
    buttons.forEach(function (button) {
      button.addEventListener('click', function () { showTab(button.dataset.tab); });
    });
    document.querySelector('.tabs').addEventListener('keydown', function (event) {
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
      showTab(buttons[next].dataset.tab);
    });
  }

  function renderChrome() {
    var manifest = state.manifest;
    var counts = asm.pieceCounts(manifest.parts);
    el('rev').textContent = 'v' + manifest.version + ' · unprinted';
    el('title').textContent = manifest.name;
    el('sub').textContent = 'Six-paddle crank lift, then a downhill V-track with three curved corners, back into the inlet.';
    el('claim').textContent = asm.claimSentence();
    var facts = [
      [String(counts.defaultPieces), 'Default pieces, coupon separate'],
      [String(counts.unique), 'Unique STLs, extras included'],
      ['35 mm', 'Printed ball, supports on'],
      ['294 × 267.5 × 52', 'Largest part, mm'],
      ['330 × 320 × 325', 'H3C bed it is checked against']
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
    renderParts();
    renderPrint(counts);
    wireControls();
  }

  function badgeFor(part) {
    if (asm.OPTIONAL[part.name]) return ['Extra', 'extra'];
    if (part.name === 'fit_coupon') return ['First plate', 'scene'];
    if (part.name === 'lift_test_base') return ['Lift test', 'scene'];
    if (part.name === 'track_corner_left') return ['Spare', 'scene'];
    if (part.supports) return ['Supports', ''];
    if (part.brim) return ['Brim', 'wait'];
    return ['Loop', ''];
  }

  function roleOf(name) {
    if (asm.OPTIONAL[name]) return 'Optional extra. Not on the default loop, and not drop-in verified.';
    if (name === 'track_corner_left') return 'Spare left corner for experiments. Same corner family. Not placed on the loop.';
    if (name === 'fit_coupon') return 'Print this first. It is not one of the 40 factory pieces.';
    if (name === 'lift_test_base') return 'Lift-only test frame. Print this with the lift before the full circuit.';
    if (name === 'ball_35') return 'Preview balls sit on the sampled downhill path. They do not roll when you crank.';
    return 'On the default loop.';
  }

  function renderParts() {
    var list = el('part-list');
    clear(list);
    list.appendChild(text('p', 'Thirty-two unique meshes. The 3D factory shows the placed default loop only. Pink switch and merge parts, and the orange spinner set, stay in this list until a layout is actually checked.', 'muted'));
    state.manifest.parts.forEach(function (part) {
      var row = document.createElement('div');
      row.className = 'part-row';
      row.tabIndex = 0;
      row.dataset.part = part.name;
      var swatch = document.createElement('i');
      swatch.className = 'swatch';
      swatch.style.background = part.color;
      var body = document.createElement('div');
      var title = document.createElement('div');
      title.appendChild(text('strong', part.name.replace(/_/g, ' ')));
      title.appendChild(document.createTextNode(' '));
      var badgeInfo = badgeFor(part);
      var badge = text('span', badgeInfo[0], 'badge');
      if (badgeInfo[1]) badge.classList.add(badgeInfo[1]);
      title.appendChild(badge);
      body.appendChild(title);
      var size = part.extents_mm.map(function (n) { return (Math.round(n * 10) / 10).toString(); }).join(' × ');
      body.appendChild(text('div', part.qty + ' ×  ·  ' + size + ' mm. ' + part.desc + ' ' + roleOf(part.name), 'detail'));
      var link = document.createElement('a');
      link.href = '/marble-factory/stl/' + part.name + '.stl';
      link.setAttribute('download', part.name + '.stl');
      link.textContent = 'STL';
      link.className = 'qty';
      row.appendChild(swatch);
      row.appendChild(body);
      row.appendChild(link);
      function focusPart() {
        var placed = state.meshes.find(function (entry) { return entry.instance.part === part.name; });
        if (placed && !state.shelfOn) {
          select(placed.id);
          showTab('look');
        } else {
          state.shelfOn = true;
          applyMode();
          var shelf = state.shelf.find(function (entry) { return entry.part === part.name; });
          if (shelf) select(shelf.id);
          showTab('look');
          if (state.viewer) state.viewer.frame();
        }
      }
      row.addEventListener('click', function (event) {
        if (event.target.tagName === 'A') return;
        focusPart();
      });
      row.addEventListener('keydown', function (event) {
        if (event.key !== 'Enter' && event.key !== ' ') return;
        event.preventDefault();
        focusPart();
      });
      list.appendChild(row);
    });
  }

  function fileRow(kind, title, href, detail) {
    var row = document.createElement('div');
    row.className = 'dl-row';
    var badge = text('span', asm.fileKind(kind), 'badge');
    if (kind === 'assembly-scene') badge.classList.add('scene');
    var body = document.createElement('div');
    body.appendChild(text('strong', title));
    body.appendChild(text('div', detail, 'detail'));
    var link = document.createElement('a');
    link.href = href;
    link.setAttribute('download', '');
    link.textContent = 'Download';
    row.appendChild(badge);
    row.appendChild(body);
    row.appendChild(link);
    return row;
  }

  function renderPrint(counts) {
    var root = el('print-root');
    clear(root);
    root.appendChild(safetyCard());
    root.appendChild(firstCard());
    root.appendChild(filesCard(counts));
    root.appendChild(sliceCard());
    root.appendChild(routeCard());
    root.appendChild(stepsCard());
    root.appendChild(clearanceCard());
    root.appendChild(renderCard(
      '/marble-factory/renders/01_overview.png',
      'Top-view diagram of the default loop: lift, four long straights, one short straight, three right-hand corners, inlet.',
      'Diagram of the default route. Not a photograph.'
    ));
    root.appendChild(renderCard(
      '/marble-factory/renders/03_lift_mechanism.png',
      'Section of the paddle wheel: hub, six paddles, outer guide, pickup, and the exit chute.',
      'CAD section of the lift. The dashed curve is the 2D simulated centre, not a filmed marble.'
    ));
    root.appendChild(renderCard(
      '/marble-factory/renders/02_assembly_steps.png',
      'Assembly step diagram for the default factory.',
      'CAD assembly diagram, not a finished print.'
    ));
  }

  function safetyCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Not a certified toy'));
    var list = document.createElement('ul');
    [
      'Colorful on purpose, and still an adult-test prototype. Nothing here has been printed and measured.',
      'Balls are 35 mm, larger than the usual small-parts gauge. That does not make this a certified child toy.',
      'The front plate has 6 mm viewing slots. The inlet has to stay big enough for a 35 mm ball, so fingers can still reach the wheel. The inlet chute is about a 59 mm tunnel.',
      'Pinch points stay at the wheel. Not for children under 3. An adult supervises, and an adult runs the crank before any child does.',
      'Rolling, snap fit, and the paddle actually driving a ball are not physically verified. The 3D clearance check used a 17.15 mm radius, 0.35 mm inside the full 17.5 mm ball, so tangent contact was not counted as a hit.'
    ].forEach(function (line) { list.appendChild(text('li', line)); });
    card.appendChild(list);
    return card;
  }

  function firstCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Coupon, then the lift, then the circuit'));
    var list = document.createElement('ol');
    [
      'Print fit_coupon. It carries the repeating pegs, sockets, hexes, clip groove, and the small gate and retainer holes.',
      'Print the lift-only set on lift_test_base: both housings, two wheel halves, axle, crank, clip, pawl, stand_J11_h025, the inlet, and one or two balls.',
      'Check that the axle turns, the pawl clicks, a ball is picked up and let go onto the chute, the clip stays put, and the crank misses the inlet. If that fails, stop.',
      'Only then print the six tiles, nine stands, four long straights, one short straight, three right corners, and the rest of the balls.'
    ].forEach(function (line) { list.appendChild(text('li', line)); });
    card.appendChild(list);
    var link = document.createElement('a');
    link.href = '/marble-factory/stl/fit_coupon.stl';
    link.setAttribute('download', 'fit_coupon.stl');
    link.textContent = 'Download the fit coupon STL';
    card.appendChild(link);
    return card;
  }

  function filesCard(counts) {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Downloads'));
    card.appendChild(text('p', counts.unique + ' unique STLs, ' + counts.printed + ' pieces if you print every quantity, ' + counts.defaultPieces + ' in the default set. The coupon is separate. ' + counts.optionalPieces + ' optional extra pieces are in the ZIP and not on the loop. No G-code is included. Re-slice in Bambu Studio on the H3C profile.', 'muted'));
    card.appendChild(fileRow('kit-zip', 'Kit ZIP', '/marble-factory/marble-factory-kit.zip', 'STLs, manifest, assembly, colored 3MF, source, renders, and the reports.'));
    card.appendChild(fileRow('coupon', 'Fit coupon', '/marble-factory/stl/fit_coupon.stl', 'stl/fit_coupon.stl'));
    card.appendChild(fileRow('assembly-scene', 'Assembly 3MF', '/marble-factory/marble_factory_assembly.3mf', 'Colored assembly scene of the default loop. Not a Bambu plate and not pre-sliced.'));
    card.appendChild(fileRow('readme', 'README', '/marble-factory/README.md', 'Build order, colors, and the same limits as this page.'));
    card.appendChild(fileRow('readme', 'Validation report', '/marble-factory/reports/VALIDATION.md', 'The computational checks, including what they do not prove.'));
    card.appendChild(fileRow('readme', 'Slice report', '/marble-factory/slice/SLICE_REPORT.md', 'PrusaSlicer 2.7.4, generic 0.4 mm / 0.20 mm PLA. Not an official H3C profile.'));
    card.appendChild(fileRow('source', 'Generator source', '/marble-factory/src/export.py', 'src/ holds the Python that builds the meshes. The kit ZIP includes the whole src folder.'));
    var more = document.createElement('p');
    more.className = 'muted';
    more.appendChild(document.createTextNode('Also in src: '));
    ['assembly.py', 'lift.py', 'tracks.py', 'geom.py', 'validate.py', 'render.py', 'slice_all.py', 'lift2d.py', 'pawl2d.py', 'spinner2d.py', 'spinner_check.py'].forEach(function (name, index) {
      if (index) more.appendChild(document.createTextNode(', '));
      var link = document.createElement('a');
      link.href = '/marble-factory/src/' + name;
      link.textContent = name;
      more.appendChild(link);
    });
    more.appendChild(document.createTextNode('.'));
    card.appendChild(more);
    return card;
  }

  function sliceCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Slice check'));
    card.appendChild(text('p', 'All 32 unique STLs produced a non-empty toolpath in PrusaSlicer 2.7.4 on a generic 0.4 mm nozzle, 0.20 mm layer, PLA profile. That is not an official H3C profile, and the G-code from that check is not in this kit.'));
    var list = document.createElement('ul');
    [
      'ball_35 needs supports. The mesh is a 35 mm sphere with a 0.5 mm flat on the bed. This kit does not include hemisphere STLs.',
      'Brim is flagged for the nine stands, the axle, the clip, and the optional spinner rotor.',
      'The axle, crank, optional rotor, optional retainer, and track_corner_right warned about floating bridges or loose extrusions and still produced a toolpath.',
      'Largest part is lift_housing_back at 294.0 × 267.5 × 52.0 mm, inside a 330 × 320 × 325 mm H3C envelope. Re-check the slice in Bambu Studio before a real print.'
    ].forEach(function (line) { list.appendChild(text('li', line)); });
    card.appendChild(list);
    return card;
  }

  function routeCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Default route'));
    card.appendChild(text('p', 'Crank the six-paddle lift. The ball is meant to leave on a 7° chute, then go only downhill: 20 mm drop per 160 mm (7.13°) on the straights and the swept R=80 right corners, then 8.2 mm over 58.7 mm (7.96°) on the inlet, back into the lift.'));
    card.appendChild(text('p', 'Joints, in order: J0 (−80, 0) → J1 (−240, 0) → J2 (−320, 80) → J3 (−320, 240) → J4 (−240, 320) → J5 (−80, 320) → J6 (0, 320) → J7 (80, 240) → J11 (80, 80) → inlet.', 'muted'));
    card.appendChild(text('p', 'Switch, merge, and spinner are not on this circuit. Switch and merge still use an older 12 mm drop, so they are not drop-in with the 7.13° loop. The spinner track uses the same 20 mm / 160 mm drop as a straight, but its rotor, posts, and retainer were not given a verified factory layout. Do not treat them as a second finished factory.'));
    return card;
  }

  function stepsCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Assembly, once a print exists'));
    var list = document.createElement('ol');
    [
      'Dovetail the six base tiles into a 720 × 480 mm lattice. The joints and the two housing pegs at (0, 0) and (160, 0) land on that grid.',
      'Drop each stand into its socket. Heights are in the part name.',
      'Snap track modules on from J0, working downhill: long straight, right corner, long straight, right corner, long straight, short straight, right corner, long straight. Neighboring half-pegs share a socket.',
      'Seat the lift housing back in the sockets at (0, 0) and (160, 0). Slide the pawl onto its pin. The chute keel should sit in the first track without forcing the walls.',
      'Place the two wheel halves in the pocket with the hexes aligned. Fit the front plate on the pins.',
      'Insert the axle from the back, tip toward the front, through the back journal, both wheel hexes, and the front journal.',
      'Press the crank onto the front hex and snap the U-clip into the groove past the crank.',
      'Snap the inlet onto J11. Its nose lines up with the front-plate inlet. The kit says to turn the crank so the top moves toward the inlet side, counterclockwise as seen from the front. That spin is what the crank control here shows on the meshes.'
    ].forEach(function (line) { list.appendChild(text('li', line)); });
    card.appendChild(list);
    card.appendChild(text('p', 'No glue, no electronics, no screws in the design. If a joint is tight, the README says to scrape the peg lightly. Hex flats are 0.2 mm oversized in CAD. That fit is untested on a printer.', 'muted'));
    return card;
  }

  function clearanceCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Clearances in the CAD file'));
    card.appendChild(text('p', 'Design targets from the model. Not caliper readings.', 'muted'));
    var table = document.createElement('table');
    var c = state.manifest.clearances_mm;
    [
      ['Track peg in the stand socket', c.track_peg_r + ' mm peg, ' + c.stand_socket_r + ' mm socket, ' + c.peg_socket_radial + ' mm radial'],
      ['Wheel hex', c.wheel_hex_af + ' mm across flats into a ' + c.wheel_hex_hole_af + ' mm hole'],
      ['Crank hex', c.crank_hex_af + ' mm across flats into a ' + c.crank_hex_hole_af + ' mm hole'],
      ['Back journal', c.axle_jBack_r + ' mm axle, ' + c.housing_back_hole_r + ' mm hole'],
      ['Front journal', c.axle_jFront_r + ' mm axle, ' + c.housing_front_hole_r + ' mm hole'],
      ['Clip on the groove', 'groove r ' + c.clip_groove_r + ', seat r ' + c.clip_seat_r + ', throat ' + c.clip_throat],
      ['Default track slope', c.track_slope_deg + '° · ' + c.track_slope_note],
      ['Exit chute / inlet', c.chute_slope_deg + '° chute, ' + c.inlet_slope_deg + '° inlet'],
      ['Guide vs ball', String(c.guide_radial_on_ball)]
    ].forEach(function (row) {
      var tr = document.createElement('tr');
      tr.appendChild(text('td', row[0]));
      tr.appendChild(text('td', row[1]));
      table.appendChild(tr);
    });
    card.appendChild(table);
    return card;
  }

  function renderCard(src, alt, caption) {
    var fig = document.createElement('figure');
    fig.className = 'card';
    var img = document.createElement('img');
    img.src = src;
    img.alt = alt;
    img.width = 900;
    img.height = 700;
    fig.appendChild(img);
    fig.appendChild(text('figcaption', caption, 'muted'));
    return fig;
  }

  function modeCopy() {
    if (state.shelfOn) {
      el('mode-title').textContent = 'All 32 STLs, print orientation';
      el('mode-copy').textContent = 'Each file as exported, sitting on its own spot so you can see the mesh. This is not an assembled factory. Switch, merge, and spinner parts are here because they have no verified place on the loop.';
    } else if (state.pathOn) {
      el('mode-title').textContent = 'Default loop, with centre samples';
      el('mode-copy').textContent = 'The line is the computational ball-centre path along the downhill track and inlet. It is a sample trace, not a marble moving, and not a physics run. The crank still only turns the wheel, axle, and crank.';
    } else {
      el('mode-title').textContent = 'Default loop, assembled';
      el('mode-copy').textContent = 'Placed from assembly.json. Cranking turns the wheel halves, axle, and crank about the axle at (80, 0, 136) mm. The clip and pawl stay at their rest poses. The six balls are preview placements. They do not roll.';
    }
  }

  function applyMode() {
    state.meshes.forEach(function (entry) { entry.mesh.visible = !state.shelfOn; });
    state.shelf.forEach(function (entry) { entry.mesh.visible = state.shelfOn; });
    if (state.pathLine) state.pathLine.visible = state.pathOn && !state.shelfOn;
    el('btn-shelf').setAttribute('aria-pressed', state.shelfOn ? 'true' : 'false');
    el('btn-shelf').classList.toggle('on', state.shelfOn);
    el('btn-shelf').textContent = state.shelfOn ? 'Show the factory' : 'All 32 STLs';
    el('btn-path').setAttribute('aria-pressed', state.pathOn ? 'true' : 'false');
    el('btn-path').classList.toggle('on', state.pathOn);
    modeCopy();
  }

  function setCrank(deg) {
    var wrapped = ((deg % 360) + 360) % 360;
    state.crank = wrapped;
    el('crank').value = String(Math.round(wrapped));
    el('crank-read').textContent = Math.round(wrapped) + '°';
    updatePoses();
  }

  function stepCrank(delta) {
    setCrank(state.crank + delta);
  }

  function wireControls() {
    el('crank').addEventListener('input', function () {
      setCrank(Number(el('crank').value));
    });
    el('explode').addEventListener('input', function () {
      state.explode = Number(el('explode').value) / 100;
      el('explode-read').textContent = el('explode').value + '%';
      updatePoses();
    });
    el('btn-assemble').addEventListener('click', function () {
      state.explode = 0;
      el('explode').value = '0';
      el('explode-read').textContent = '0%';
      state.shelfOn = false;
      setCrank(0);
      applyMode();
      select(null);
    });
    el('btn-shelf').addEventListener('click', function () {
      state.shelfOn = !state.shelfOn;
      applyMode();
      if (state.viewer) state.viewer.frame();
    });
    el('btn-path').addEventListener('click', function () {
      state.pathOn = !state.pathOn;
      applyMode();
    });
    el('btn-crank-fwd').addEventListener('click', function () { stepCrank(15); });
    el('btn-crank-back').addEventListener('click', function () { stepCrank(-15); });
  }

  function bootViewer() {
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
    scene.add(new THREE.HemisphereLight(0xfff1ea, 0x1b2430, 0.9));
    var key = new THREE.DirectionalLight(0xfff4e5, 1.25);
    key.position.set(180, 320, 140);
    scene.add(key);
    var rim = new THREE.DirectionalLight(0x9fd4ff, 0.55);
    rim.position.set(-220, 80, -40);
    scene.add(rim);
    var fill = new THREE.DirectionalLight(0xff8aa0, 0.28);
    fill.position.set(40, 40, 260);
    scene.add(fill);

    var camera = new THREE.PerspectiveCamera(35, 1, 0.5, 20000);
    var controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    controls.dampingFactor = 0.08;
    controls.screenSpacePanning = true;
    controls.touches.ONE = THREE.TOUCH.ROTATE;
    controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;

    function makeMesh(geometry, color, id) {
      var material = new THREE.MeshStandardMaterial({
        color: new THREE.Color(color),
        roughness: 0.5,
        metalness: 0.03,
        transparent: true
      });
      var mesh = new THREE.Mesh(geometry, material);
      mesh.userData.id = id;
      return mesh;
    }

    var jobs = state.manifest.parts.map(function (part) {
      var url = '/marble-factory/stl/' + part.name + '.stl';
      return fetch(url).then(function (response) {
        if (!response.ok) throw new Error(part.name + ' returned ' + response.status);
        return response.arrayBuffer();
      }).then(function (buffer) {
        var parsed = asm.parseStl(buffer);
        if (parsed.triangles !== part.faces) {
          throw new Error(part.name + ' has ' + parsed.triangles + ' triangles, manifest says ' + part.faces);
        }
        var geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(parsed.positions, 3));
        geometry.computeVertexNormals();
        state.geometries[part.name] = geometry;
        state.loadedParts += 1;
        el('load-line').textContent = 'Loaded ' + state.loadedParts + ' of 32 STL files.';
      });
    });

    jobs.push(fetch('/marble-factory/reports/ball_paths.json').then(function (response) {
      if (!response.ok) throw new Error('ball_paths.json returned ' + response.status);
      return response.json();
    }).then(function (paths) {
      var loop = paths.default_loop;
      if (!loop || loop.length < 2) throw new Error('default loop path is missing');
      var positions = new Float32Array(loop.length * 3);
      loop.forEach(function (point, index) {
        positions[index * 3] = point[0];
        positions[index * 3 + 1] = point[1];
        positions[index * 3 + 2] = point[2];
      });
      var geometry = new THREE.BufferGeometry();
      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      state.pathLine = new THREE.Line(geometry, new THREE.LineBasicMaterial({ color: 0xfbbf24 }));
      state.pathLine.visible = false;
      state.pathLine.frustumCulled = false;
      root.add(state.pathLine);
    }));

    Promise.all(jobs).then(function () {
      state.assembly.instances.forEach(function (instance) {
        var id = instance.part + '#' + instance.index + '@' + instance.at;
        var mesh = makeMesh(state.geometries[instance.part], instance.color, id);
        var entry = {
          id: id,
          instance: instance,
          mesh: mesh,
          explode: asm.explodeMm(instance.part, instance.index)
        };
        applyMatrix(mesh, matrixFor(entry));
        root.add(mesh);
        state.meshes.push(entry);
        state.triangles += state.geometries[instance.part].getAttribute('position').count / 3;
      });
      state.manifest.parts.forEach(function (part, index) {
        var id = part.name + '#shelf';
        var mesh = makeMesh(state.geometries[part.name], part.color, id);
        var col = index % 8;
        var row = Math.floor(index / 8);
        applyMatrix(mesh, [
          [1, 0, 0, col * 360],
          [0, 1, 0, -row * 420],
          [0, 0, 1, 0],
          [0, 0, 0, 1]
        ]);
        mesh.visible = false;
        root.add(mesh);
        state.shelf.push({ id: id, part: part.name, mesh: mesh });
      });
      el('view-status').hidden = true;
      el('mode-note').hidden = false;
      applyMode();
      frame();
      state.booted = true;
    }).catch(function (error) {
      state.errors.push(String(error && error.message || error));
      el('error').textContent = String(error && error.message || error);
    });

    renderer.domElement.addEventListener('pointerdown', function (event) {
      if (event.target !== renderer.domElement) return;
      var rect = renderer.domElement.getBoundingClientRect();
      var ray = new THREE.Raycaster();
      ray.setFromCamera(new THREE.Vector2(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1
      ), camera);
      var pool = (state.shelfOn ? state.shelf : state.meshes).map(function (entry) { return entry.mesh; });
      var hits = ray.intersectObjects(pool, false);
      if (hits.length) select(hits[0].object.userData.id);
    });

    function resize() {
      var width = view.clientWidth;
      var height = view.clientHeight;
      if (!width || !height) return;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.fov = width / height < 0.85 ? 48 : 35;
      camera.updateProjectionMatrix();
    }

    function visibleRootBox() {
      var box = new THREE.Box3();
      var empty = true;
      root.children.forEach(function (child) {
        if (!child.visible) return;
        var childBox = new THREE.Box3().setFromObject(child);
        if (empty) {
          box.copy(childBox);
          empty = false;
        } else box.union(childBox);
      });
      return box;
    }

    function frame() {
      root.updateMatrixWorld(true);
      var box = visibleRootBox();
      var center = box.getCenter(new THREE.Vector3());
      var size = box.getSize(new THREE.Vector3());
      var radius = 0.5 * Math.max(size.x, size.y, size.z, 1);
      var dist = radius / Math.sin((camera.fov * Math.PI / 180) / 2) * 0.92;
      camera.position.set(center.x + dist * 0.72, center.y + dist * 0.48, center.z + dist * 0.82);
      camera.near = Math.max(0.5, radius / 100);
      camera.far = radius * 40;
      camera.updateProjectionMatrix();
      controls.target.copy(center);
      controls.update();
    }

    function lookFront() {
      root.updateMatrixWorld(true);
      var axle = new THREE.Vector3(80, 0, 136).applyMatrix4(root.matrixWorld);
      var width = view.clientWidth || 1;
      var height = view.clientHeight || 1;
      camera.fov = width / height < 0.85 ? 48 : 35;
      camera.position.set(axle.x + 30, axle.y + 70, axle.z - 340);
      camera.near = 1;
      camera.far = 8000;
      camera.updateProjectionMatrix();
      controls.target.copy(axle);
      controls.update();
    }

    el('btn-reset').addEventListener('click', frame);
    el('btn-front').addEventListener('click', function () {
      if (state.shelfOn) {
        state.shelfOn = false;
        applyMode();
      }
      lookFront();
    });

    function tick() {
      requestAnimationFrame(tick);
      if (el('panel-look').classList.contains('tab-parked')) return;
      controls.update();
      renderer.render(scene, camera);
    }

    window.addEventListener('resize', resize);
    resize();
    requestAnimationFrame(tick);
    state.viewer = { resize: resize, frame: frame, lookFront: lookFront };
  }

  function fail(error) {
    state.errors.push(String(error && error.message || error));
    el('error').textContent = String(error && error.message || error);
    el('claim').textContent = 'The model manifest did not load.';
  }

  Promise.all([
    fetch('/marble-factory/manifest.json').then(function (response) {
      if (!response.ok) throw new Error('manifest.json returned ' + response.status);
      return response.json();
    }),
    fetch('/marble-factory/assembly.json').then(function (response) {
      if (!response.ok) throw new Error('assembly.json returned ' + response.status);
      return response.json();
    })
  ]).then(function (pair) {
    state.manifest = pair[0];
    state.assembly = pair[1];
    if (state.manifest.parts.length !== 32) throw new Error('expected 32 parts');
    if (state.assembly.instances.length !== 38) throw new Error('expected 38 placed instances');
    renderChrome();
    bootTabs();
    bootViewer();
  }).catch(fail);

  window.__marble = {
    get booted() { return state.booted; },
    get triangles() { return state.triangles; },
    get errors() { return state.errors.slice(); },
    get loadedParts() { return state.loadedParts; },
    get assemblyCount() { return state.meshes.length; },
    get crank() { return state.crank; },
    get shelfOn() { return state.shelfOn; },
    setCrank: setCrank,
    sample: function (part, index, local) {
      var entry = state.meshes.find(function (item) {
        return item.instance.part === part && item.instance.index === index;
      });
      return asm.apply(matrixFor(entry), local);
    },
    axleDistance: function (part, index, local) {
      return asm.axisDistance(this.sample(part, index, local));
    }
  };
})();
