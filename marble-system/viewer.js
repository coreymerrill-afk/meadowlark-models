/* Layout A/B from scenes.json. Every mesh is an STL.
   v2 parts come from /marble-system/stl. The lift reuses /marble-factory/stl. */
(function () {
  'use strict';

  var asm = window.MarbleSystem;
  var state = {
    manifest: null,
    scenes: null,
    layout: 'A',
    geometries: {},
    meshes: [],
    shelf: [],
    heights: {},
    crank: 0,
    explode: 0,
    shelfOn: false,
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

  function scene() { return state.scenes[state.layout]; }

  var V1_MESH = {
    lift_housing_back: true,
    lift_housing_front: true,
    lift_wheel_half: true,
    lift_axle: true,
    lift_crank: true,
    lift_clip: true,
    lift_pawl: true
  };

  function stlUrl(part) {
    if (V1_MESH[part]) return '/marble-factory/stl/' + part + '.stl';
    return '/marble-system/stl/' + part + '.stl';
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

  function heightDelta(instance) {
    if (!instance.moves || !instance.heightId) return 0;
    var now = state.heights[state.layout + ':' + instance.heightId];
    if (now == null) return 0;
    return now - instance.H;
  }

  function matrixFor(instance) {
    return asm.poseMatrix(
      instance.transform,
      !!instance.spin,
      scene().axle,
      state.crank,
      heightDelta(instance),
      asm.explodeFor(instance.role),
      state.explode
    );
  }

  function updatePoses() {
    state.meshes.forEach(function (entry) {
      if (entry.layout !== state.layout) return;
      applyMatrix(entry.mesh, matrixFor(entry.instance));
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
      } else panel.hidden = !on;
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
      else return;
      event.preventDefault();
      buttons[next].focus();
      showTab(buttons[next].dataset.tab);
    });
  }

  function counts() {
    var track = 0;
    var families = state.manifest.parts.length;
    state.manifest.bom48.forEach(function (row) { track += row.qty; });
    return { track: track, families: families, supports: state.manifest.support_structures.total, wells: state.manifest.well_count };
  }

  function renderChrome() {
    var c = counts();
    el('rev').textContent = 'v' + state.manifest.version + ' · unprinted';
    el('title').textContent = 'Modular marble board';
    el('claim').textContent = asm.claimSentence();
    var facts = [
      [String(c.track), 'Track pieces in the box'],
      [String(c.families), 'Unique STL families'],
      [c.supports + ' × 4', 'Supports, three height classes'],
      [String(c.wells), 'Wells on a 40 mm lattice'],
      ['457.2 × 609.6', 'Board, mm · 18 × 24 in']
    ];
    var node = el('facts');
    clear(node);
    facts.forEach(function (fact) {
      var card = document.createElement('div');
      card.className = 'fact';
      card.appendChild(text('b', fact[0]));
      card.appendChild(text('span', fact[1]));
      node.appendChild(card);
    });
    renderParts();
    renderPrint();
    wireControls();
    setLayout('A');
  }

  function badgeFor(part) {
    if (part.bucket === 'track48') return ['In the 48', ''];
    if (part.bucket === 'support24') return ['Support', 'wait'];
    if (part.bucket === 'base') return ['Base', 'wait'];
    if (part.name === 'fit_coupon') return ['First plate', 'scene'];
    return ['Extra', 'extra'];
  }

  function renderParts() {
    var list = el('part-list');
    clear(list);
    var c = counts();
    list.appendChild(text('p', c.track + ' track pieces are the inventory. Layout A installs ' + state.scenes.A.installedTracks + ' of them and ' + state.scenes.A.installedPosts + ' of 24 posts. Layout B installs ' + state.scenes.B.installedTracks + ' tracks and ' + state.scenes.B.installedPosts + ' posts. The two layouts are not on the board together. Branched parts (split, merge, funnel, switch) are in the box and not in A or B.', 'muted'));
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
      var info = badgeFor(part);
      var badge = text('span', info[0], 'badge');
      if (info[1]) badge.classList.add(info[1]);
      title.appendChild(badge);
      body.appendChild(title);
      var size = part.extents_mm.map(function (n) { return String(n); }).join(' × ');
      body.appendChild(text('div', part.qty + ' ×  ·  ' + size + ' mm. ' + installedNote(part.name), 'detail'));
      var link = document.createElement('a');
      link.href = stlUrl(part.name);
      link.setAttribute('download', part.name + '.stl');
      link.className = 'qty';
      link.textContent = 'STL';
      row.appendChild(swatch);
      row.appendChild(body);
      row.appendChild(link);
      function focusPart() {
        var placed = state.meshes.find(function (entry) {
          return entry.layout === state.layout && entry.instance.part === part.name;
        });
        if (placed && !state.shelfOn) {
          select(placed.instance.id);
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

  function installedNote(name) {
    var a = state.scenes.A.instances.some(function (item) { return item.part === name; });
    var b = state.scenes.B.instances.some(function (item) { return item.part === name; });
    if (a && b) return 'Installed in both example layouts (not at the same time).';
    if (a) return 'Installed in layout A. Not in layout B.';
    if (b) return 'Installed in layout B. Not in layout A.';
    if (name.indexOf('lock_clip') === 0 || name === 'ball_cap') return 'Wear part. Spares are in the print quantity. PETG is the research recommendation for clips.';
    if (name === 'tile_latch') return 'Eight seam latches are in the print list. They are not posed in the example scenes.';
    return 'In the box. Not placed in layout A or B.';
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

  function renderPrint() {
    var root = el('print-root');
    clear(root);
    root.appendChild(limitsCard());
    root.appendChild(safetyCard());
    root.appendChild(firstCard());
    root.appendChild(filesCard());
    root.appendChild(researchCard());
    root.appendChild(heightCard());
    root.appendChild(renderCard('/marble-system/renders/05_layoutA_3d.png', 'CAD preview of layout A, the simple loop with the lift.', 'CAD preview of layout A. Not a photograph and not a print.'));
    root.appendChild(renderCard('/marble-system/renders/06_layoutB_3d.png', 'CAD preview of layout B, the descending helix example.', 'CAD preview of layout B. Helix sag on two end posts is untested.'));
    root.appendChild(renderCard('/marble-system/renders/01_board_wells.png', 'Plan of the 18 by 24 inch board and the wells that remain after seams are skipped.', 'Well plan. 117 sites, not a full 40 mm grid.'));
    root.appendChild(renderCard('/marble-system/renders/03_support_section.png', 'Section of a height support: sleeve, post, pawl, and ball cap.', 'Support section from the CAD render.'));
  }

  function limitsCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'What the 0-fail report actually checked'));
    var list = document.createElement('ul');
    [
      '36 unique solids are single bodies inside the 330 × 320 × 325 mm envelope. Tiles are 304.8 × 228.6 × 12 mm, so the long side is the H3C 330 mm axis.',
      'Rest-state track joints in the report (S160×CL90, CL90×S80, S160×S160, and the consecutive rails in A and B) came back at about 0 mm³. That is the latched track joint, not the clip.',
      'Clip ears, the cap bulge, and the socket lip are labelled designed snaps. Overlap there is the snap model, not a clearance fit. Insertion force is untested.',
      'ADAPT_OUT and ADAPT_IN were not boolean-checked against the v1 lift meshes. They follow the published keel and inlet numbers. Treat that joint as an untested interface.',
      'Route slope is centreline geometry (V vertex plus the 35 mm ball centre offset). It is not a solid ball swept through the parts, and it is not a rolling test.',
      'Layout B holds the helix on the entry post and the exit post. Sag of that span is untested. A third post would fit inside the count of 24, and this CAD does not add one.',
      'Creep, fatigue, tile warp, and child use are untested. Positive pawls are the design response to friction preload, not a measured life.'
    ].forEach(function (line) { list.appendChild(text('li', line)); });
    card.appendChild(list);
    return card;
  }

  function safetyCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Not a certified toy'));
    var list = document.createElement('ul');
    [
      'Same 35 mm ball as v1. That size is above the usual small-parts gauge and is still not a certification.',
      'The v1 lift inlet still admits fingers, and the wheel can pinch. An adult tests the crank before a child uses it.',
      '22.4 mm wells may admit a finger. The research note flags that for a physical review.',
      'Not for children under 3. No ASTM F963 or ISO 8124 claim.'
    ].forEach(function (line) { list.appendChild(text('li', line)); });
    card.appendChild(list);
    return card;
  }

  function firstCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Coupon, then one short support'));
    var list = document.createElement('ol');
    [
      'Print fit_coupon. It is the witness for the well, the rack, the tongue, and the ball cup.',
      'Print one short support: sleeve_short, post_short, lock_clip_short, and ball_cap. PETG is the research pick for the clip and the cap. PLA is acceptable for the stiff sleeve and post on a first look.',
      'Check that the sleeve seats, the pawl clicks on a 5 mm step, and the cap pulls off on purpose. If that fails, stop.',
      'Only then print tiles, the rest of the supports, and track. The v1 ball_35 still needs supports. Re-slice everything in Bambu Studio on the H3C profile.'
    ].forEach(function (line) { list.appendChild(text('li', line)); });
    card.appendChild(list);
    var link = document.createElement('a');
    link.href = '/marble-system/stl/fit_coupon.stl';
    link.setAttribute('download', 'fit_coupon.stl');
    link.textContent = 'Download the fit coupon STL';
    card.appendChild(link);
    return card;
  }

  function filesCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Downloads'));
    card.appendChild(text('p', '36 STL families. No G-code. The layout A 3MF is a colored assembly scene, not a sliced plate. Layout B is placed from the same STLs in the viewer. There is no layout B plate file.', 'muted'));
    card.appendChild(fileRow('kit-zip', 'Kit ZIP', '/marble-system/marble-system-v2-kit.zip', 'STLs, README, manifest, assembly records, layout A 3MF, source, and the reports.'));
    card.appendChild(fileRow('coupon', 'Fit coupon', '/marble-system/stl/fit_coupon.stl', 'stl/fit_coupon.stl'));
    card.appendChild(fileRow('individual-stl', 'Short sleeve', '/marble-system/stl/sleeve_short.stl', 'First support, with the post, clip, and cap.'));
    card.appendChild(fileRow('assembly-scene', 'Layout A 3MF', '/marble-system/kit/marble_system_v2_layoutA.3mf', 'Colored scene of layout A. Not a Bambu plate and not pre-sliced.'));
    card.appendChild(fileRow('readme', 'README', '/marble-system/README.md', 'Inventory, height classes, and the limits of the computational checks.'));
    card.appendChild(fileRow('readme', 'Research brief', '/marble-system/RESEARCH_BRIEF.md', 'The interface note and its sources. An earlier grid in that draft is not the CAD that shipped.'));
    card.appendChild(fileRow('readme', 'Validation JSON', '/marble-system/reports/validation.json', 'The 0-fail report. Read the limits above before treating that count as a finished mechanism.'));
    card.appendChild(fileRow('readme', 'Slice report', '/marble-system/slice/SLICE_REPORT.md', 'PrusaSlicer 2.7.4, generic 0.4 mm / 0.20 mm PLA, 36/36 nonempty. Not an official H3C profile.'));
    card.appendChild(fileRow('source', 'Generator', '/marble-system/src/layouts.py', 'src/layouts.py places A and B. src/parts.py and src/catalog.py build the solids.'));
    return card;
  }

  function researchCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Research the locks come from'));
    card.appendChild(text('p', 'These are the sources in the engineering brief. They argue for a detent that unloads after it clicks, because leftover bending force creeps. They do not give this kit a cycle life.', 'muted'));
    var list = document.createElement('ul');
    var sources = [
      ['Covestro, Snap-Fit Joints for Plastics', 'https://solutions.covestro.com/-/media/covestro/solution-center/brands/downloads/imported/1557218421.pdf'],
      ['BASF Snap-Fit Design Manual', 'https://productdesignonline.com/wp-content/uploads/2019/08/Snap-Fit-Design-Manual.pdf'],
      ['Klahn, Singer, Meboldt, Design Guidelines for Additive Manufactured Snap-Fit Joints, Procedia CIRP 50 (2016)', 'https://doi.org/10.1016/j.procir.2016.04.130'],
      ['Hubs, How do you design snap-fit joints for 3D printing?', 'https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/'],
      ['Bozkurt, Short-term creep of polymers used in additive manufacturing (2022)', 'https://doi.org/10.5545/sv-jme.2022.191'],
      ['ASTM D2990, creep of plastics', 'https://www.astm.org/d2990-17r25.html'],
      ['Bambu PLA Basic TDS', 'https://apple-tree.co.jp/wp/wp-content/themes/appletree/uploads/bambulab/datasheet/Bambu_PLA_Basic_TDS_EN.pdf'],
      ['Bambu PETG Basic TDS', 'https://store.bblcdn.com/s1/default/cb94589bf7994fdcbfa833badefae9cd/Bambu_PETG_Basic_Technical_Data_Sheet.pdf'],
      ['Ravensburger GraviTrax FAQ (usability precedent, not a compatible part)', 'https://ravensburger-en.mindtouch.us/Product_Information/Ravensburger/GraviTrax%C2%AE/FAQ_for_GraviTrax%C2%AE']
    ];
    sources.forEach(function (source) {
      var item = document.createElement('li');
      var link = document.createElement('a');
      link.href = source[1];
      link.textContent = source[0];
      item.appendChild(link);
      list.appendChild(item);
    });
    card.appendChild(list);
    card.appendChild(text('p', 'From that reading: height is a 5 mm pawl, not a friction slider. Roll is keyed. Pitch is ±15°. Track joints use a tongue, lugs, and a 0.5 mm downhill step. PETG is suggested for clips because PLA is a poorer cyclic flexure in the Hubs note. No year-of-play number is published.', 'muted'));
    return card;
  }

  function heightCard() {
    var card = document.createElement('article');
    card.className = 'card';
    card.appendChild(text('h2', 'Height classes'));
    card.appendChild(text('p', '70–230 mm ball-centre height is three overlapping classes, in 5 mm steps. It is not one post that travels the whole range.', 'muted'));
    var table = document.createElement('table');
    [['short', '8', '70–100'], ['medium', '10', '100–155'], ['tall', '6', '145–230']].forEach(function (row) {
      var tr = document.createElement('tr');
      tr.appendChild(text('td', row[0]));
      tr.appendChild(text('td', row[1] + ' structures'));
      tr.appendChild(text('td', row[2] + ' mm'));
      table.appendChild(tr);
    });
    card.appendChild(table);
    card.appendChild(text('p', 'Rails below 70 mm use the low_mount extra (6 in the print list). Layout A uses 3. Layout B uses 4. The v1 ball_35 is unchanged and still needs supports.', 'muted'));
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
    var current = scene();
    if (state.shelfOn) {
      el('mode-title').textContent = 'All 36 STL families, print orientation';
      el('mode-copy').textContent = 'One mesh of each family, in the exported print pose. Quantities are on the Inventory tab. This is not an assembled board.';
      return;
    }
    var title = state.layout === 'A' ? 'Layout A · simple loop' : 'Layout B · helix example';
    el('mode-title').textContent = title;
    el('mode-copy').textContent = current.installedTracks + ' of 48 track pieces and ' + current.installedPosts + ' of 24 posts are installed, plus ' + current.lowMounts + ' low mounts and the v1 lift. ' + current.note + ' The crank is illustrative. Balls are not in this scene.';
  }

  function applyMode() {
    state.meshes.forEach(function (entry) {
      entry.mesh.visible = !state.shelfOn && entry.layout === state.layout;
    });
    state.shelf.forEach(function (entry) { entry.mesh.visible = state.shelfOn; });
    el('btn-shelf').setAttribute('aria-pressed', state.shelfOn ? 'true' : 'false');
    el('btn-shelf').classList.toggle('on', state.shelfOn);
    el('btn-a').setAttribute('aria-pressed', state.layout === 'A' && !state.shelfOn ? 'true' : 'false');
    el('btn-b').setAttribute('aria-pressed', state.layout === 'B' && !state.shelfOn ? 'true' : 'false');
    el('btn-a').classList.toggle('on', state.layout === 'A' && !state.shelfOn);
    el('btn-b').classList.toggle('on', state.layout === 'B' && !state.shelfOn);
    modeCopy();
    renderHeight();
  }

  function setLayout(key) {
    state.layout = key;
    state.shelfOn = false;
    scene().instances.forEach(function (instance) {
      if (instance.heightId) state.heights[key + ':' + instance.heightId] = instance.H;
    });
    state.crank = 0;
    el('crank').value = '0';
    el('crank-read').textContent = '0°';
    state.explode = 0;
    el('explode').value = '0';
    el('explode-read').textContent = '0%';
    applyMode();
    updatePoses();
    select(null);
  }

  function renderHeight() {
    var row = el('height-row');
    clear(row);
    if (state.shelfOn) return;
    var seen = {};
    var posts = [];
    scene().instances.forEach(function (instance) {
      if (!instance.moves || instance.part.indexOf('post_') !== 0 || seen[instance.heightId]) return;
      seen[instance.heightId] = true;
      posts.push(instance);
    });
    if (!posts.length) return;
    row.appendChild(text('span', 'Post height', 'layout-read'));
    posts.forEach(function (instance) {
      var button = document.createElement('button');
      button.type = 'button';
      button.textContent = instance.kind + ' ' + state.heights[state.layout + ':' + instance.heightId] + ' mm';
      button.classList.toggle('on', state.selected === instance.id);
      button.addEventListener('click', function () {
        select(instance.id);
        renderHeight();
      });
      row.appendChild(button);
    });
    var current = posts.find(function (instance) { return instance.id === state.selected; }) || posts[0];
    var down = document.createElement('button');
    down.type = 'button';
    down.textContent = '5 mm down';
    var up = document.createElement('button');
    up.type = 'button';
    up.textContent = '5 mm up';
    function step(delta) {
      var key = state.layout + ':' + current.heightId;
      var next = state.heights[key] + delta;
      if (next < current.Hmin || next > current.Hmax) return;
      state.heights[key] = next;
      updatePoses();
      renderHeight();
    }
    down.addEventListener('click', function () { step(-5); });
    up.addEventListener('click', function () { step(5); });
    row.appendChild(down);
    row.appendChild(up);
    row.appendChild(text('span', current.kind + ' class ' + current.Hmin + '–' + current.Hmax + ' mm', 'layout-read'));
  }

  function select(id) {
    state.selected = id;
    state.meshes.concat(state.shelf).forEach(function (entry) {
      var on = (entry.instance ? entry.instance.id : entry.id) === id;
      entry.mesh.material.emissive.setHex(on ? 0x332266 : 0x000000);
      entry.mesh.material.opacity = !id || on ? 1 : 0.45;
    });
  }

  function setCrank(deg) {
    var wrapped = ((deg % 360) + 360) % 360;
    state.crank = wrapped;
    el('crank').value = String(Math.round(wrapped));
    el('crank-read').textContent = Math.round(wrapped) + '°';
    updatePoses();
  }

  function wireControls() {
    el('btn-a').addEventListener('click', function () { setLayout('A'); if (state.viewer) state.viewer.frame(); });
    el('btn-b').addEventListener('click', function () { setLayout('B'); if (state.viewer) state.viewer.frame(); });
    el('btn-crank-fwd').addEventListener('click', function () { setCrank(state.crank + 15); });
    el('btn-crank-back').addEventListener('click', function () { setCrank(state.crank - 15); });
    el('crank').addEventListener('input', function () { setCrank(Number(el('crank').value)); });
    el('explode').addEventListener('input', function () {
      state.explode = Number(el('explode').value) / 100;
      el('explode-read').textContent = el('explode').value + '%';
      updatePoses();
    });
    el('btn-assemble').addEventListener('click', function () {
      state.explode = 0;
      el('explode').value = '0';
      el('explode-read').textContent = '0%';
      setCrank(0);
      setLayout(state.layout);
    });
    el('btn-shelf').addEventListener('click', function () {
      state.shelfOn = !state.shelfOn;
      applyMode();
      if (state.viewer) state.viewer.frame();
    });
    el('btn-frame').addEventListener('click', function () { if (state.viewer) state.viewer.frame(); });
    el('btn-front').addEventListener('click', function () {
      state.shelfOn = false;
      applyMode();
      if (state.viewer) state.viewer.lookFront();
    });
    el('btn-wells').addEventListener('click', function () {
      state.shelfOn = false;
      applyMode();
      if (state.viewer) state.viewer.lookAt(152, 0, 40, 280);
    });
    el('btn-post').addEventListener('click', function () {
      state.shelfOn = false;
      applyMode();
      var post = scene().instances.find(function (item) { return item.part.indexOf('post_') === 0; });
      if (post) select(post.id);
      renderHeight();
      if (state.viewer && post) state.viewer.lookAt(post.transform[0][3], post.H, post.transform[1][3], 220);
    });
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

    var scene3 = new THREE.Scene();
    var root = new THREE.Group();
    root.rotation.x = -Math.PI / 2;
    scene3.add(root);
    scene3.add(new THREE.HemisphereLight(0xf4f0ff, 0x1b2430, 0.92));
    var key = new THREE.DirectionalLight(0xfff6ea, 1.2);
    key.position.set(200, 360, 120);
    scene3.add(key);
    var rim = new THREE.DirectionalLight(0x9eb6ff, 0.45);
    rim.position.set(-240, 80, -80);
    scene3.add(rim);

    var camera = new THREE.PerspectiveCamera(35, 1, 0.5, 20000);
    var controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    controls.dampingFactor = 0.08;
    controls.screenSpacePanning = true;
    controls.touches.ONE = THREE.TOUCH.ROTATE;
    controls.touches.TWO = THREE.TOUCH.DOLLY_PAN;

    var names = {};
    state.manifest.parts.forEach(function (part) { names[part.name] = part; });
    ['lift_housing_back', 'lift_housing_front', 'lift_wheel_half', 'lift_axle', 'lift_crank', 'lift_clip', 'lift_pawl'].forEach(function (name) {
      names[name] = names[name] || { name: name, faces: null };
    });

    var jobs = Object.keys(names).map(function (name) {
      return fetch(stlUrl(name)).then(function (response) {
        if (!response.ok) throw new Error(name + ' returned ' + response.status);
        return response.arrayBuffer();
      }).then(function (buffer) {
        var parsed = asm.parseStl(buffer);
        if (names[name].faces != null && parsed.triangles !== names[name].faces) {
          throw new Error(name + ' has ' + parsed.triangles + ' triangles, manifest says ' + names[name].faces);
        }
        var geometry = new THREE.BufferGeometry();
        geometry.setAttribute('position', new THREE.BufferAttribute(parsed.positions, 3));
        geometry.computeVertexNormals();
        state.geometries[name] = geometry;
        state.loadedParts += 1;
        el('load-line').textContent = 'Loaded ' + state.loadedParts + ' STL files.';
      });
    });

    Promise.all(jobs).then(function () {
      ['A', 'B'].forEach(function (key) {
        state.scenes[key].instances.forEach(function (instance) {
          if (instance.heightId && state.heights[key + ':' + instance.heightId] == null) {
            state.heights[key + ':' + instance.heightId] = instance.H;
          }
        });
        state.scenes[key].instances.forEach(function (instance) {
          var material = new THREE.MeshStandardMaterial({
            color: new THREE.Color(instance.color),
            roughness: 0.5,
            metalness: 0.03,
            transparent: true
          });
          var mesh = new THREE.Mesh(state.geometries[instance.part], material);
          mesh.userData.id = instance.id;
          var saved = state.layout;
          state.layout = key;
          applyMatrix(mesh, matrixFor(instance));
          state.layout = saved;
          mesh.visible = key === 'A';
          root.add(mesh);
          state.meshes.push({ layout: key, instance: instance, mesh: mesh });
          if (key === 'A') state.triangles += state.geometries[instance.part].getAttribute('position').count / 3;
        });
      });
      state.manifest.parts.forEach(function (part, index) {
        var material = new THREE.MeshStandardMaterial({
          color: new THREE.Color(part.color),
          roughness: 0.5,
          metalness: 0.03,
          transparent: true
        });
        var mesh = new THREE.Mesh(state.geometries[part.name], material);
        var col = index % 8;
        var row = Math.floor(index / 8);
        applyMatrix(mesh, [[1, 0, 0, col * 380], [0, 1, 0, -row * 320], [0, 0, 1, 0], [0, 0, 0, 1]]);
        mesh.visible = false;
        mesh.userData.id = part.name + '#shelf';
        root.add(mesh);
        state.shelf.push({ id: part.name + '#shelf', part: part.name, mesh: mesh });
      });
      el('view-status').hidden = true;
      el('mode-note').hidden = false;
      applyMode();
      updatePoses();
      frame();
      state.booted = true;
    }).catch(function (error) {
      state.errors.push(String(error && error.message || error));
      el('error').textContent = String(error && error.message || error);
    });

    renderer.domElement.addEventListener('pointerdown', function (event) {
      var rect = renderer.domElement.getBoundingClientRect();
      var ray = new THREE.Raycaster();
      ray.setFromCamera(new THREE.Vector2(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1
      ), camera);
      var pool = (state.shelfOn ? state.shelf : state.meshes.filter(function (entry) {
        return entry.layout === state.layout;
      })).map(function (entry) { return entry.mesh; });
      var hits = ray.intersectObjects(pool, false);
      if (!hits.length) return;
      select(hits[0].object.userData.id);
      renderHeight();
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

    function frame() {
      root.updateMatrixWorld(true);
      var box = new THREE.Box3();
      var empty = true;
      root.children.forEach(function (child) {
        if (!child.visible) return;
        var childBox = new THREE.Box3().setFromObject(child);
        if (empty) { box.copy(childBox); empty = false; }
        else box.union(childBox);
      });
      if (empty) return;
      var center = box.getCenter(new THREE.Vector3());
      var size = box.getSize(new THREE.Vector3());
      var radius = 0.5 * Math.max(size.x, size.y, size.z, 1);
      var dist = radius / Math.sin((camera.fov * Math.PI / 180) / 2) * 0.92;
      camera.position.set(center.x + dist * 0.7, center.y + dist * 0.46, center.z + dist * 0.78);
      camera.near = Math.max(0.5, radius / 100);
      camera.far = radius * 40;
      camera.updateProjectionMatrix();
      controls.target.copy(center);
      controls.update();
    }

    function lookWorld(x, y, z, dist) {
      root.updateMatrixWorld(true);
      var target = new THREE.Vector3(x, y, z).applyMatrix4(root.matrixWorld);
      camera.position.set(target.x + dist * 0.35, target.y + dist * 0.45, target.z + dist);
      camera.near = 1;
      camera.far = 8000;
      camera.updateProjectionMatrix();
      controls.target.copy(target);
      controls.update();
    }

    function lookFront() {
      var axle = scene().axle;
      lookWorld(axle[0], axle[1], axle[2], 340);
    }

    el('btn-frame').addEventListener('click', frame);

    function tick() {
      requestAnimationFrame(tick);
      if (el('panel-look').classList.contains('tab-parked')) return;
      controls.update();
      renderer.render(scene3, camera);
    }
    window.addEventListener('resize', resize);
    resize();
    requestAnimationFrame(tick);
    state.viewer = {
      resize: resize,
      frame: frame,
      lookFront: lookFront,
      lookAt: function (x, z, y, dist) { lookWorld(x, y, z, dist); }
    };
  }

  function fail(error) {
    state.errors.push(String(error && error.message || error));
    el('error').textContent = String(error && error.message || error);
    el('claim').textContent = 'The v2 manifest did not load.';
  }

  Promise.all([
    fetch('/marble-system/kit/manifest.json').then(function (response) {
      if (!response.ok) throw new Error('manifest.json returned ' + response.status);
      return response.json();
    }),
    fetch('/marble-system/scenes.json').then(function (response) {
      if (!response.ok) throw new Error('scenes.json returned ' + response.status);
      return response.json();
    })
  ]).then(function (pair) {
    state.manifest = pair[0];
    state.scenes = pair[1];
    if (state.manifest.parts.length !== 36) throw new Error('expected 36 STL families');
    if (state.manifest.bom48_sum !== 48) throw new Error('expected 48 track pieces');
    if (state.manifest.well_count !== 117) throw new Error('expected 117 wells');
    renderChrome();
    bootTabs();
    bootViewer();
  }).catch(fail);

  window.__marble2 = {
    get booted() { return state.booted; },
    get triangles() { return state.triangles; },
    get errors() { return state.errors.slice(); },
    get loadedParts() { return state.loadedParts; },
    get layout() { return state.layout; },
    get crank() { return state.crank; },
    setCrank: setCrank,
    setLayout: setLayout,
    stepHeight: function (id, delta) {
      var instance = scene().instances.find(function (item) { return item.heightId === id && item.moves && item.part.indexOf('post_') === 0; });
      if (!instance) return null;
      var key = state.layout + ':' + id;
      var next = state.heights[key] + delta;
      if (next < instance.Hmin || next > instance.Hmax) return state.heights[key];
      state.heights[key] = next;
      updatePoses();
      return next;
    },
    sample: function (id, local) {
      var entry = state.meshes.find(function (item) {
        return item.layout === state.layout && item.instance.id === id;
      });
      return asm.apply(matrixFor(entry.instance), local);
    }
  };
})();
