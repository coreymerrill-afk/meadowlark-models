/* Pasta cooker viewer.
   Loads the Blender 4.2.9 glTF binaries in this folder. No stand-in geometry.
   The files are a small glTF subset: triangles, tightly packed float attributes,
   uint16 indices, node translation/rotation, and PBR factors without textures.
   Anything outside that subset stops the load instead of drawing a guess. */
(function () {
  "use strict";

  var ROOT = "/pasta-cooker/";
  var VIEWS = {
    exterior: {
      id: "exterior",
      file: "pasta-cooker-assembled.glb",
      meshes: 115,
      vertices: 35948,
      label: "Exterior",
      note: "Full case from pasta-cooker-assembled.glb. Interior parts are inside the shell.",
      labels: ["lid", "ui", "water", "drain"]
    },
    cutaway: {
      id: "cutaway",
      file: "pasta-cooker-cutaway.glb",
      meshes: 95,
      vertices: 26632,
      label: "Cutaway",
      note: "Case and lid are hidden in pasta-cooker-cutaway.glb. The vessel wall is sectioned so the basket and plumbing can be read.",
      labels: ["water", "salt", "channel", "basket", "vessel", "base", "circ", "drain", "lift", "elec"]
    },
    exploded: {
      id: "exploded",
      file: "pasta-cooker-exploded.glb",
      meshes: 102,
      vertices: 28709,
      label: "Exploded",
      note: "Modules are moved apart in pasta-cooker-exploded.glb. Plumbing stays in the assembled reference position. This is not a connected working configuration.",
      labels: ["basket", "lid", "water", "salt", "channel", "drain", "elec"]
    }
  };

  var PARTS = [
    {
      id: "water",
      path: "water",
      swatch: "#3aa0c8",
      title: "Clean water",
      callout: { exterior: "Clean water tank", cutaway: "01 Clean water", exploded: "Water reservoir" },
      prefer: ["Clean tank viewing strip", "01 Clean water removable tank"],
      about: "Removable clean-water tank, fill cap, carry handle, and level marks. The blue route continues through a metering pump and a cold-feed pipe into the heated channel. Metering sensors, valve internals, and backflow compliance are not designed."
    },
    {
      id: "salt",
      path: "salt",
      swatch: "#d9d0b4",
      title: "Salt dose",
      callout: { exterior: "Salt dose", cutaway: "02 Salt dose", exploded: "Salt dosing module" },
      prefer: ["02 Separate salt hopper", "Salt auger dosing chute"],
      about: "Separate hopper, funnel, and an illustrative auger chute dose into the vessel so salt stays out of the clean-water and heater path. Feed rate, bridging, and moisture sealing need testing."
    },
    {
      id: "channel",
      path: "heat",
      swatch: "#e25a32",
      title: "Heated channel",
      callout: { exterior: "Heated channel", cutaway: "03 Heated channel", exploded: "Channel heater module" },
      prefer: ["Heated channel serpentine", "03 Flow through heater block"],
      about: "Orange serpentine flow-through channel, then an elevated rim outlet and air-gap concept into the vessel. Pressure drop, scale, dry-fire, and service access are not solved. This is not a pressure cooker."
    },
    {
      id: "basket",
      path: "cook",
      swatch: "#c5ced1",
      title: "Pasta basket",
      callout: { exterior: "Pasta basket", cutaway: "04 Pasta basket", exploded: "Lift / drain basket" },
      prefer: ["04 Basket top rim", "Dry pasta illustrative 00"],
      about: "Removable basket. Ribs and hoops stand in for perforations; they are not a manufacturable screen. The pasta strands are illustrative. No actuator, limit switch, lock, or motion is in the file."
    },
    {
      id: "vessel",
      path: "cook",
      swatch: "#9aa7ad",
      title: "Cooking vessel",
      callout: { exterior: "Cooking vessel", cutaway: "05 Cooking vessel", exploded: "Cooking vessel" },
      prefer: ["05 Vessel section wall", "Vessel rolled rim"],
      about: "Stainless-colored vessel. The wall is sectioned in the model so the inside can be seen. The nominal exterior envelope, about 480 × 360 × 410 mm, is indicative only. Coordinates in the GLB are meters."
    },
    {
      id: "base",
      path: "heat",
      swatch: "#e25a32",
      title: "Base heater",
      callout: { exterior: "Base heater", cutaway: "06 Base heater", exploded: "Base heater" },
      prefer: ["06 Direct vessel heater plate"],
      about: "Orange plate under the vessel. A second heat input, kept in addition to the heated channel. Splitting a household circuit does not create extra energy. No power arbitration, sensor, or thermal cutout is implemented."
    },
    {
      id: "circ",
      path: "circ",
      swatch: "#1faf78",
      title: "Guarded circulation",
      callout: { exterior: "Guarded circulation", cutaway: "07 Guarded circulation", exploded: "Guarded circulation" },
      prefer: ["Gentle broad return loop", "07 Recirculation pump"],
      about: "Green loop: side suction outside the basket, recirculation pump, and a broad tangential return. No pasta through the pump is the intent. The ribbed guard is a visual placeholder. Flow and starch behavior are unvalidated."
    },
    {
      id: "drain",
      path: "drain",
      swatch: "#b58362",
      title: "Drain / waste",
      callout: { exterior: "Removable waste drawer", cutaway: "08 Drain / waste", exploded: "Waste drawer" },
      prefer: ["Waste access drawer face", "08 Removable waste drawer"],
      about: "Brown vessel-bottom drain, a valve-actuator concept, and a removable drawer. No safe drain timing, venting, or full-tank sensing is implemented."
    },
    {
      id: "lift",
      path: "lift",
      swatch: "#8d98a0",
      title: "Lift + load cell",
      callout: { exterior: "Lift + load cell", cutaway: "09 Lift + load cell", exploded: "Lift + load cell" },
      prefer: ["09 Lift rail tower", "Portion load cell concept"],
      about: "Lift rail, carriage, and basket bridge indicate an automated lift and drain. The green block is a conceptual load cell. No actuator sizing, switches, or locking is in the model."
    },
    {
      id: "elec",
      path: "elec",
      swatch: "#5c6b73",
      title: "Electrical isolation",
      callout: { exterior: "Electrical isolation", cutaway: "10 Electrics (rear)", exploded: "Wet / dry separation" },
      prefer: ["10 Sealed electrical concept bay", "Wet dry isolation barrier"],
      about: "Rear low compartment and a separating wall show intended wet/dry segregation. They are packaging intent only: not proof of waterproofing, grounding, leak sensing, or electrical compliance."
    },
    {
      id: "lid",
      path: "steam",
      swatch: "#f4f1ea",
      title: "Vented lid",
      callout: { exterior: "Lift-off vented lid", cutaway: "Lift-off vented lid", exploded: "Removable lid" },
      prefer: ["Steam guarded lid", "Rear steam vent 0"],
      about: "Removable lid with rear-facing steam vents and a cool-touch grip concept. Not an interlock, and not a demonstrated safe vent direction."
    },
    {
      id: "ui",
      path: "ui",
      swatch: "#7dcec4",
      title: "Shape + portion",
      callout: { exterior: "Shape + portion control", cutaway: "Shape + portion control", exploded: "Shape + portion control" },
      prefer: ["Shape and portion display", "Shape setting rotary dial"],
      about: "Dial and screen represent a shape and portion selection. There is no weighing or control implementation. The load cell is the separate block on the lift."
    },
    {
      id: "case",
      path: "case",
      swatch: "#e7e4dc",
      title: "Exterior case",
      callout: { exterior: "Exterior case", cutaway: "Exterior case", exploded: "Exterior case" },
      prefer: ["Exterior front fascia", "Top deck"],
      about: "Ivory case, graphite top deck, drip tray, and feet. Hidden in the cutaway file. The exploded file keeps the tray and feet and moves some modules off them."
    }
  ];

  var RULES = [
    ["lift", function (n) { return n.indexOf("09 ") === 0 || n.indexOf("Lift ") === 0 || n.indexOf("Portion load") === 0 || n.indexOf("Basket lift") === 0; }],
    ["basket", function (n) { return n.indexOf("04 ") === 0 || n.indexOf("Basket ") === 0 || n.indexOf("Dry pasta") === 0; }],
    ["water", function (n) { return n.indexOf("01 ") === 0 || n.indexOf("Clean tank") === 0 || n.indexOf("Tank level") === 0 || n === "Metering pump" || n.indexOf("A Clean") === 0 || n.indexOf("B Metered") === 0; }],
    ["channel", function (n) { return n.indexOf("03 ") === 0 || n.indexOf("Heated channel") === 0 || n.indexOf("C Heated") === 0; }],
    ["base", function (n) { return n.indexOf("06 ") === 0; }],
    ["salt", function (n) { return n.indexOf("02 ") === 0 || n.indexOf("Salt ") === 0; }],
    ["circ", function (n) { return n.indexOf("07 ") === 0 || n.indexOf("Guarded ") === 0 || n.indexOf("Gentle ") === 0 || n.indexOf("Suction ") === 0 || n.indexOf("Broad ") === 0; }],
    ["drain", function (n) { return n.indexOf("08 ") === 0 || n.indexOf("Waste ") === 0 || n.indexOf("D Vessel") === 0 || n.indexOf("Drain valve") === 0; }],
    ["lid", function (n) { return n.indexOf("Steam ") === 0 || n.indexOf("Cool touch") === 0 || n.indexOf("Rear steam") === 0; }],
    ["ui", function (n) { return n.indexOf("Shape") === 0 || n === "PASTA / 01" || n.indexOf("SHAPE") === 0 || n === "LIFT + DRAIN"; }],
    ["elec", function (n) { return n.indexOf("10 ") === 0 || n.indexOf("Wet dry") === 0; }],
    ["case", function (n) { return n.indexOf("Exterior ") === 0 || n === "Top deck" || n.indexOf("Structural ") === 0 || n.indexOf("Isolated foot") === 0; }],
    ["vessel", function (n) { return n.indexOf("05 ") === 0 || n.indexOf("Vessel ") === 0; }]
  ];

  function matchPart(name) {
    var i;
    for (i = 0; i < RULES.length; i += 1) {
      if (RULES[i][1](name)) return RULES[i][0];
    }
    return "";
  }

  function partById(id) {
    var i;
    for (i = 0; i < PARTS.length; i += 1) {
      if (PARTS[i].id === id) return PARTS[i];
    }
    return null;
  }

  var viewEl = document.getElementById("view");
  var statusEl = document.getElementById("load-status");
  var statusText = document.getElementById("load-status-text");
  var noteEl = document.getElementById("view-note");
  var errorEl = document.getElementById("error");
  var listEl = document.getElementById("part-list");
  var aboutEl = document.getElementById("part-about");
  var aboutTitle = document.getElementById("part-title");
  var leaders = document.getElementById("leaders");
  var nameLayer = document.getElementById("name-layer");

  var renderer;
  var scene;
  var camera;
  var controls;
  var root = null;
  var frameHome = null;
  var current = VIEWS.exterior;
  var pathFilter = "all";
  var selectedId = "";
  var labelButtons = {};
  var loadToken = 0;
  var ready = false;

  function setStatus(title, body) {
    statusEl.hidden = false;
    statusEl.querySelector("strong").textContent = title;
    statusText.textContent = body;
  }

  function fail(message) {
    ready = false;
    document.documentElement.dataset.pastaReady = "0";
    errorEl.textContent = message;
    setStatus("The Blender model did not load", message);
  }

  function componentCount(type) {
    if (type === "SCALAR") return 1;
    if (type === "VEC2") return 2;
    if (type === "VEC3") return 3;
    throw new Error("Unsupported accessor type " + type);
  }

  function readAccessor(json, bin, index, cache) {
    if (cache.has(index)) return cache.get(index);
    var acc = json.accessors[index];
    if (!acc || acc.bufferView === undefined) throw new Error("Missing accessor " + index);
    if (acc.sparse) throw new Error("Sparse accessors are not in these files");
    if (acc.normalized) throw new Error("Normalized accessors are not in these files");
    var view = json.bufferViews[acc.bufferView];
    if (!view || view.byteStride) throw new Error("Interleaved buffer views are not in these files");
    var width = componentCount(acc.type);
    var start = (view.byteOffset || 0) + (acc.byteOffset || 0);
    var array;
    if (acc.componentType === 5126) {
      array = new Float32Array(bin.slice(start, start + acc.count * width * 4));
    } else if (acc.componentType === 5123) {
      array = new Uint16Array(bin.slice(start, start + acc.count * width * 2));
    } else if (acc.componentType === 5125) {
      array = new Uint32Array(bin.slice(start, start + acc.count * width * 4));
    } else {
      throw new Error("Unsupported component type " + acc.componentType);
    }
    if (array.length !== acc.count * width) throw new Error("Short buffer for accessor " + index);
    cache.set(index, array);
    return array;
  }

  function parseGlb(buffer) {
    var data = new DataView(buffer);
    if (data.byteLength < 20 || data.getUint32(0, true) !== 0x46546c67) {
      throw new Error("Not a glTF binary");
    }
    if (data.getUint32(4, true) !== 2) throw new Error("Only glTF 2 binaries are expected");
    var jsonLength = data.getUint32(12, true);
    var jsonType = data.getUint32(16, true);
    if (jsonType !== 0x4e4f534a) throw new Error("Missing glTF JSON chunk");
    var jsonStart = 20;
    var jsonText = new TextDecoder().decode(new Uint8Array(buffer, jsonStart, jsonLength));
    var json = JSON.parse(jsonText);
    if (json.extensionsRequired && json.extensionsRequired.length) {
      throw new Error("Required glTF extensions are not supported");
    }
    var binStart = jsonStart + jsonLength;
    if ((binStart % 4) !== 0) binStart += 4 - (binStart % 4);
    var binLength = data.getUint32(binStart, true);
    var binType = data.getUint32(binStart + 4, true);
    if (binType !== 0x004e4942) throw new Error("Missing glTF BIN chunk");
    return { json: json, bin: buffer.slice(binStart + 8, binStart + 8 + binLength) };
  }

  function buildMaterial(def) {
    var pbr = (def && def.pbrMetallicRoughness) || {};
    var color = pbr.baseColorFactor || [1, 1, 1, 1];
    var material = new THREE.MeshStandardMaterial({
      color: new THREE.Color().setRGB(color[0], color[1], color[2]),
      metalness: pbr.metallicFactor === undefined ? 0 : pbr.metallicFactor,
      roughness: pbr.roughnessFactor === undefined ? 1 : pbr.roughnessFactor,
      side: def && def.doubleSided ? THREE.DoubleSide : THREE.FrontSide
    });
    material.name = def && def.name ? def.name : "";
    if (color[3] < 1) {
      material.transparent = true;
      material.opacity = color[3];
    }
    return material;
  }

  function buildObject(json, bin) {
    if (json.images || json.textures || json.animations || json.skins) {
      throw new Error("Textures, animation, or skinning were not in the handoff files");
    }
    var cache = new Map();
    var materials = (json.materials || []).map(buildMaterial);
    var meshes = (json.meshes || []).map(function (def) {
      var group = new THREE.Group();
      def.primitives.forEach(function (prim) {
        if ((prim.mode === undefined ? 4 : prim.mode) !== 4) throw new Error("Only triangle meshes are expected");
        if (!prim.attributes || prim.attributes.POSITION === undefined || prim.indices === undefined) {
          throw new Error("A mesh is missing positions or indices");
        }
        var geometry = new THREE.BufferGeometry();
        var position = readAccessor(json, bin, prim.attributes.POSITION, cache);
        geometry.setAttribute("position", new THREE.BufferAttribute(position, 3));
        if (prim.attributes.NORMAL !== undefined) {
          geometry.setAttribute("normal", new THREE.BufferAttribute(readAccessor(json, bin, prim.attributes.NORMAL, cache), 3));
        } else {
          geometry.computeVertexNormals();
        }
        if (prim.attributes.TEXCOORD_0 !== undefined) {
          geometry.setAttribute("uv", new THREE.BufferAttribute(readAccessor(json, bin, prim.attributes.TEXCOORD_0, cache), 2));
        }
        geometry.setIndex(new THREE.BufferAttribute(readAccessor(json, bin, prim.indices, cache), 1));
        var material = materials[prim.material];
        if (!material) throw new Error("A mesh is missing its PBR material");
        group.add(new THREE.Mesh(geometry, material));
      });
      return group;
    });

    var object = new THREE.Group();
    object.name = "pasta-cooker";
    var sceneDef = json.scenes[json.scene || 0];
    var unmatched = [];
    var meshCount = 0;
    var vertexCount = 0;
    sceneDef.nodes.forEach(function (nodeIndex) {
      var node = json.nodes[nodeIndex];
      if (!node || node.mesh === undefined) throw new Error("A scene node has no mesh");
      if (node.children && node.children.length) throw new Error("Nested nodes are not in these files");
      if (node.matrix) throw new Error("Matrix transforms are not in these files");
      var group = meshes[node.mesh];
      group.name = node.name || "";
      if (node.translation) group.position.fromArray(node.translation);
      if (node.rotation) group.quaternion.fromArray(node.rotation);
      if (node.scale) group.scale.fromArray(node.scale);
      var partId = matchPart(group.name);
      if (!partId) unmatched.push(group.name || "(unnamed)");
      group.traverse(function (child) {
        if (!child.isMesh) return;
        child.name = group.name;
        child.userData.partId = partId;
        child.userData.baseMaterial = child.material;
        meshCount += 1;
        vertexCount += child.geometry.getAttribute("position").count;
      });
      object.add(group);
    });
    object.userData.meshCount = meshCount;
    object.userData.vertexCount = vertexCount;
    object.userData.unmatched = unmatched;
    return object;
  }

  function disposeRoot() {
    if (!root) return;
    root.traverse(function (child) {
      if (!child.isMesh) return;
      if (child.geometry) child.geometry.dispose();
      if (child.userData.baseMaterial) child.userData.baseMaterial.dispose();
      if (child.material && child.material !== child.userData.baseMaterial) child.material.dispose();
    });
    scene.remove(root);
    root = null;
  }

  function portraitFov() {
    var aspect = viewEl.clientWidth / Math.max(1, viewEl.clientHeight);
    return aspect < 0.85 ? 48 : 34;
  }

  function frameObject(object) {
    var box = new THREE.Box3().setFromObject(object);
    var size = box.getSize(new THREE.Vector3());
    var center = box.getCenter(new THREE.Vector3());
    var maxDim = Math.max(size.x, size.y, size.z, 0.2);
    camera.fov = portraitFov();
    camera.updateProjectionMatrix();
    var dist = (maxDim * 0.5) / Math.tan((camera.fov * Math.PI) / 360);
    dist *= viewEl.clientWidth < 760 ? 1.7 : 1.95;
    // glTF Y-up. Blender's front (-Y) is +Z here, and height is +Y.
    camera.position.set(center.x + dist * 0.78, center.y + dist * 0.62, center.z + dist * 1.12);
    camera.near = Math.max(dist / 200, 0.001);
    camera.far = dist * 20;
    camera.updateProjectionMatrix();
    camera.lookAt(center);
    controls.target.copy(center);
    controls.minDistance = dist * 0.28;
    controls.maxDistance = dist * 5;
    controls.update();
    frameHome = {
      position: camera.position.clone(),
      target: center.clone(),
      fov: camera.fov,
      near: camera.near,
      far: camera.far
    };
  }

  function restoreFrame() {
    if (!frameHome) return;
    camera.position.copy(frameHome.position);
    camera.fov = portraitFov();
    camera.near = frameHome.near;
    camera.far = frameHome.far;
    camera.updateProjectionMatrix();
    controls.target.copy(frameHome.target);
    controls.update();
  }

  function zoom(factor) {
    var offset = camera.position.clone().sub(controls.target);
    var next = offset.length() * factor;
    next = Math.min(controls.maxDistance, Math.max(controls.minDistance, next));
    offset.setLength(next);
    camera.position.copy(controls.target).add(offset);
    controls.update();
  }

  function objectsFor(part) {
    var found = [];
    if (!root) return found;
    root.traverse(function (child) {
      if (child.isMesh && child.userData.partId === part.id) found.push(child);
    });
    return found;
  }

  function anchorFor(part) {
    var preferred = [];
    var all = [];
    objectsFor(part).forEach(function (mesh) {
      all.push(mesh);
      if (part.prefer.indexOf(mesh.name) !== -1) preferred.push(mesh);
    });
    var use = preferred.length ? preferred : all;
    if (!use.length) return null;
    var box = new THREE.Box3();
    use.forEach(function (mesh) { box.expandByObject(mesh); });
    return box.getCenter(new THREE.Vector3());
  }

  function applyEmphasis() {
    if (!root) return;
    root.traverse(function (child) {
      if (!child.isMesh) return;
      var part = partById(child.userData.partId);
      var onPath = pathFilter === "all" || (part && part.path === pathFilter);
      var selected = part && part.id === selectedId;
      if (onPath && !selected) {
        if (child.material !== child.userData.baseMaterial) {
          child.material.dispose();
          child.material = child.userData.baseMaterial;
        }
        return;
      }
      var next = child.userData.baseMaterial.clone();
      if (!onPath) {
        next.transparent = true;
        next.opacity = 0.07;
        next.depthWrite = false;
      }
      if (selected) {
        next.emissive = new THREE.Color("#ed7946");
        next.emissiveIntensity = 0.28;
      }
      if (child.material !== child.userData.baseMaterial) child.material.dispose();
      child.material = next;
    });
  }

  function calloutFor(part) {
    return part.callout[current.id] || part.title;
  }

  function renderPartList() {
    var html = "";
    PARTS.forEach(function (part) {
      var count = objectsFor(part).length;
      var absent = count === 0;
      html += '<button type="button" class="part' + (absent ? " is-absent" : "") + '" data-part="' + part.id + '" aria-pressed="' + (selectedId === part.id ? "true" : "false") + '">' +
        '<span class="swatch" style="background:' + part.swatch + '"></span>' +
        '<span>' + calloutFor(part) + '</span>' +
        '<span class="sub">' + (absent ? "Not in this file" : count + " meshes in this file") + '</span>' +
        '</button>';
    });
    listEl.innerHTML = html;
    var selected = partById(selectedId);
    if (!selected) {
      aboutTitle.textContent = "Named parts";
      aboutEl.textContent = "Select a name or a label on the model. The list uses the Blender plate names. Mesh ribs are grouped, not listed one by one.";
      return;
    }
    aboutTitle.textContent = calloutFor(selected);
    aboutEl.textContent = objectsFor(selected).length
      ? selected.about
      : selected.about + " This piece is not in the current file. Switch Exterior, Cutaway, or Exploded.";
  }

  function ensureLabel(part) {
    if (labelButtons[part.id]) return labelButtons[part.id];
    var button = document.createElement("button");
    button.type = "button";
    button.dataset.part = part.id;
    button.addEventListener("click", function (event) {
      event.stopPropagation();
      selectPart(part.id);
    });
    nameLayer.appendChild(button);
    labelButtons[part.id] = button;
    return button;
  }

  function labelSet() {
    var ids = {};
    var source = pathFilter === "all" ? current.labels : PARTS.filter(function (part) { return part.path === pathFilter; }).map(function (part) { return part.id; });
    source.forEach(function (id) { ids[id] = true; });
    if (selectedId) ids[selectedId] = true;
    return ids;
  }

  function placeLabels() {
    var width = viewEl.clientWidth;
    var height = viewEl.clientHeight;
    var narrow = width < 760;
    var wanted = labelSet();
    var visible = [];
    leaders.innerHTML = "";
    PARTS.forEach(function (part) {
      var button = ensureLabel(part);
      var anchor = anchorFor(part);
      var show = !!anchor && !!wanted[part.id] && (pathFilter !== "all" || !narrow || part.id === selectedId || current.labels.indexOf(part.id) !== -1);
      if (narrow && pathFilter === "all" && part.id !== selectedId) show = false;
      if (narrow && pathFilter !== "all" && part.id !== selectedId && current.id === "exterior" && part.path !== pathFilter) show = false;
      button.hidden = !show;
      button.classList.toggle("on", part.id === selectedId);
      button.textContent = calloutFor(part);
      if (!show) return;
      var projected = anchor.clone().project(camera);
      visible.push({
        part: part,
        button: button,
        px: (projected.x * 0.5 + 0.5) * width,
        py: (-projected.y * 0.5 + 0.5) * height,
        behind: projected.z > 1
      });
    });
    visible = visible.filter(function (item) { return !item.behind; });
    if (narrow) {
      visible.forEach(function (item) {
        item.button.classList.add("float");
        item.button.style.left = Math.min(width - 16, Math.max(16, item.px)) + "px";
        item.button.style.top = Math.min(height - 28, Math.max(28, item.py)) + "px";
      });
      return;
    }
    visible.sort(function (a, b) { return a.py - b.py; });
    var left = [];
    var right = [];
    visible.forEach(function (item, index) {
      if (index % 2 === 0) left.push(item);
      else right.push(item);
    });
    placeColumn(left, "left", width, height);
    placeColumn(right, "right", width, height);
  }

  function placeColumn(items, side, width, height) {
    items.sort(function (a, b) { return a.py - b.py; });
    var labelWidth = 168;
    var top = 12;
    var bottom = height - 86;
    var span = Math.max(items.length, 1);
    items.forEach(function (item, index) {
      var y = items.length === 1 ? item.py : top + ((index + 0.5) * (bottom - top)) / span;
      var x = side === "left" ? 8 : width - labelWidth - 8;
      item.button.classList.remove("float");
      item.button.style.left = x + "px";
      item.button.style.top = y + "px";
      var x1 = side === "left" ? x + labelWidth : x;
      var y1 = y + 14;
      var line = document.createElementNS("http://www.w3.org/2000/svg", "line");
      line.setAttribute("x1", String(x1));
      line.setAttribute("y1", String(y1));
      line.setAttribute("x2", String(item.px));
      line.setAttribute("y2", String(item.py));
      line.setAttribute("stroke", item.part.id === selectedId ? "#ed7946" : "#36585e");
      line.setAttribute("stroke-width", "1.5");
      leaders.appendChild(line);
      var dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      dot.setAttribute("cx", String(item.px));
      dot.setAttribute("cy", String(item.py));
      dot.setAttribute("r", "3.5");
      dot.setAttribute("fill", "#ed7946");
      leaders.appendChild(dot);
    });
  }

  function selectPart(id) {
    selectedId = selectedId === id ? "" : id;
    applyEmphasis();
    renderPartList();
    document.documentElement.dataset.pastaPart = selectedId;
  }

  function bindList() {
    listEl.addEventListener("click", function (event) {
      var button = event.target.closest("[data-part]");
      if (!button) return;
      selectPart(button.dataset.part);
    });
  }

  function onPointer(event) {
    if (!root || event.target.closest("#name-layer button")) return;
    var rect = renderer.domElement.getBoundingClientRect();
    var pointer = new THREE.Vector2(
      ((event.clientX - rect.left) / rect.width) * 2 - 1,
      -((event.clientY - rect.top) / rect.height) * 2 + 1
    );
    var ray = new THREE.Raycaster();
    ray.setFromCamera(pointer, camera);
    var hits = ray.intersectObjects(root.children, true);
    if (!hits.length) return;
    var mesh = hits[0].object;
    if (mesh.userData.partId) selectPart(mesh.userData.partId);
  }

  function resize() {
    if (!renderer) return;
    var width = viewEl.clientWidth;
    var height = viewEl.clientHeight;
    if (!width || !height) return;
    camera.aspect = width / height;
    if (frameHome) {
      camera.fov = portraitFov();
    }
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
  }

  function animate() {
    requestAnimationFrame(animate);
    if (!renderer) return;
    controls.update();
    renderer.render(scene, camera);
    if (ready) placeLabels();
  }

  function markReady(object) {
    var unmatched = object.userData.unmatched;
    var meshOk = object.userData.meshCount === current.meshes;
    var vertOk = object.userData.vertexCount === current.vertices;
    document.documentElement.dataset.pastaView = current.id;
    document.documentElement.dataset.pastaFile = current.file;
    document.documentElement.dataset.pastaMeshes = String(object.userData.meshCount);
    document.documentElement.dataset.pastaVertices = String(object.userData.vertexCount);
    document.documentElement.dataset.pastaUnmatched = unmatched.join("|");
    if (!meshOk || !vertOk || unmatched.length) {
      fail("Expected " + current.file + " to have " + current.meshes + " meshes and " + current.vertices + " vertices. Loaded " + object.userData.meshCount + " meshes, " + object.userData.vertexCount + " vertices. Unmatched: " + (unmatched.join(", ") || "none") + ".");
      return;
    }
    ready = true;
    document.documentElement.dataset.pastaReady = "1";
    errorEl.textContent = "";
    statusEl.hidden = true;
    noteEl.textContent = current.note + " " + object.userData.meshCount + " meshes, " + object.userData.vertexCount + " vertices. Drag to orbit, scroll or pinch to zoom.";
  }

  function loadView(id) {
    var next = VIEWS[id];
    if (!next) return;
    current = next;
    ready = false;
    document.documentElement.dataset.pastaReady = "0";
    document.querySelectorAll("[data-view]").forEach(function (button) {
      button.setAttribute("aria-pressed", button.dataset.view === id ? "true" : "false");
    });
    setStatus("Loading " + next.file, "Blender 4.2.9 glTF. No substitute geometry.");
    var token = ++loadToken;
    fetch(ROOT + next.file)
      .then(function (response) {
        if (!response.ok) throw new Error(next.file + " returned " + response.status);
        return response.arrayBuffer();
      })
      .then(function (buffer) {
        if (token !== loadToken) return;
        var parsed = parseGlb(buffer);
        var object = buildObject(parsed.json, parsed.bin);
        disposeRoot();
        root = object;
        scene.add(root);
        frameObject(root);
        applyEmphasis();
        renderPartList();
        markReady(root);
      })
      .catch(function (error) {
        if (token !== loadToken) return;
        fail(error && error.message ? error.message : "Could not load the model");
      });
  }

  function setPath(path) {
    pathFilter = path;
    if (selectedId && path !== "all") {
      var selected = partById(selectedId);
      if (!selected || selected.path !== path) selectedId = "";
    }
    document.querySelectorAll("[data-path]").forEach(function (button) {
      button.setAttribute("aria-pressed", button.dataset.path === path ? "true" : "false");
    });
    document.documentElement.dataset.pastaPath = path;
    applyEmphasis();
    renderPartList();
  }

  function boot() {
    if (!window.THREE || !THREE.OrbitControls) {
      fail("Three.js did not load from /dollhouse/vendor/.");
      return;
    }
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(34, 1, 0.01, 50);
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, window.matchMedia("(pointer: coarse)").matches ? 1.75 : 2));
    renderer.outputEncoding = THREE.sRGBEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    renderer.setClearColor(0xd5d8dc, 1);
    viewEl.insertBefore(renderer.domElement, viewEl.firstChild);
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.screenSpacePanning = true;
    controls.touches = { ONE: THREE.TOUCH.ROTATE, TWO: THREE.TOUCH.DOLLY_PAN };
    controls.addEventListener("change", function () {
      document.documentElement.dataset.pastaDistance = camera.position.distanceTo(controls.target).toFixed(4);
    });
    scene.add(new THREE.HemisphereLight(0xfffaf3, 0x9eafb6, 0.72));
    scene.add(new THREE.AmbientLight(0xffffff, 0.28));
    var key = new THREE.DirectionalLight(0xffffff, 1.35);
    key.position.set(1.8, 3.4, 2.8);
    scene.add(key);
    var fill = new THREE.DirectionalLight(0xd5e7ff, 0.55);
    fill.position.set(-2.4, 1.6, 1.4);
    scene.add(fill);

    document.getElementById("btn-frame").addEventListener("click", restoreFrame);
    document.getElementById("btn-in").addEventListener("click", function () { zoom(0.82); });
    document.getElementById("btn-out").addEventListener("click", function () { zoom(1.22); });
    document.querySelectorAll("[data-view]").forEach(function (button) {
      button.addEventListener("click", function () { loadView(button.dataset.view); });
    });
    document.querySelectorAll("[data-path]").forEach(function (button) {
      button.addEventListener("click", function () { setPath(button.dataset.path); });
    });
    var pointerDown = null;
    renderer.domElement.addEventListener("pointerdown", function (event) {
      pointerDown = { x: event.clientX, y: event.clientY };
    });
    renderer.domElement.addEventListener("pointerup", function (event) {
      if (!pointerDown) return;
      var dx = event.clientX - pointerDown.x;
      var dy = event.clientY - pointerDown.y;
      pointerDown = null;
      if (dx * dx + dy * dy > 25) return;
      onPointer(event);
    });
    bindList();
    window.addEventListener("resize", resize);
    if (window.ResizeObserver) new ResizeObserver(resize).observe(viewEl);
    resize();
    animate();
    loadView("exterior");
  }

  document.querySelectorAll(".tabs button").forEach(function (button) {
    button.addEventListener("click", function () {
      document.querySelectorAll(".tabs button").forEach(function (other) {
        var on = other === button;
        other.setAttribute("aria-selected", on ? "true" : "false");
        other.tabIndex = on ? 0 : -1;
      });
      document.querySelectorAll(".panel").forEach(function (panel) {
        panel.hidden = panel.id !== button.getAttribute("aria-controls");
      });
    });
  });

  boot();
})();
