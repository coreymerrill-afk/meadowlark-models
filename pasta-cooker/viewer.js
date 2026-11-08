/* Pasta cooker viewer.
   Loads the Blender 4.2.9 glTF binaries in this folder. No stand-in geometry.
   V2 files are a glTF subset: triangles, tightly packed float attributes,
   uint16 indices, nested node translation/rotation, and PBR factors without textures.
   Anything outside that subset stops the load instead of drawing a guess. */
(function () {
  "use strict";

  var ROOT = "/pasta-cooker/";
  var VIEWS = {
    exterior: {
      id: "exterior",
      file: "pasta-cooker-v2-exterior.glb",
      meshes: 231,
      vertices: 141169,
      label: "Exterior",
      note: "pasta-cooker-v2-exterior.glb. Guards sit around the routes. Clean feed stays on the left and does not enter the waste tank.",
      labels: ["water", "meter", "heat", "gap", "salt", "circ", "valve", "downhill", "waste", "dry"]
    },
    cutaway: {
      id: "cutaway",
      file: "pasta-cooker-v2-cutaway.glb",
      meshes: 215,
      vertices: 132550,
      label: "Cutaway",
      note: "pasta-cooker-v2-cutaway.glb hides the front tank, chamber, and waste walls, the lid, and the dry exterior guards. The open floor low point, strainer, waterline, and waste coupling stay in the file.",
      labels: ["water", "meter", "heat", "gap", "salt", "circ", "valve", "downhill", "waste", "dry"]
    },
    exploded: {
      id: "exploded",
      file: "pasta-cooker-v2-exploded.glb",
      meshes: 217,
      vertices: 134123,
      label: "Exploded",
      note: "pasta-cooker-v2-exploded.glb raises the basket and carriage 190 mm and sets the lid aside. No plumbed module is moved, so the tank, heater, valve, and waste connections stay attached.",
      labels: ["basket", "lid", "water", "circ", "valve", "downhill", "waste", "dry"]
    }
  };

  var PARTS = [
    {
      id: "water",
      path: "water",
      swatch: "#3aa0c8",
      title: "Unsalted clean tank",
      callout: { exterior: "Unsalted clean tank", cutaway: "Unsalted clean tank", exploded: "Clean feed stays left" },
      prefer: ["Tank left wall", "Unsalted clean water visual"],
      about: "Hollow removable unsalted tank with a side bore. The clean route leaves that bore and never enters the waste solid. V1 ran 88.5 mm of clean-feed centerline through the waste tank; that intersection is gone in this file."
    },
    {
      id: "meter",
      path: "water",
      swatch: "#3aa0c8",
      title: "Isolation / meter / pump",
      callout: { exterior: "Isolation / meter / pump", cutaway: "Isolation / meter / pump", exploded: "Isolation / meter / pump" },
      prefer: ["Metering feed pump", "Flowmeter", "Isolation check cartridge"],
      about: "Named ports: tank outlet, isolation/check cartridge, metering pump, and flowmeter. The mechanisms inside those bodies are not simulated. Feed joins the first heater inlet, not a midpoint along the channel."
    },
    {
      id: "heat",
      path: "heat",
      swatch: "#e25a32",
      title: "Heated channel",
      callout: { exterior: "Heated channel", cutaway: "Heated channel", exploded: "Heated channel" },
      prefer: ["H01 heater.in -> heater.out", "Heater dry back enclosure"],
      about: "Isolated heater channel with a ceramic separator and a dry back enclosure. The inlet collar is the declared heater.in port. This is not a pressure cooker, and no flow rate or heat-up time is validated."
    },
    {
      id: "gap",
      path: "heat",
      swatch: "#e25a32",
      title: "Air gap / max water",
      callout: { exterior: "AIR GAP / max water", cutaway: "AIR GAP / max water", exploded: "AIR GAP / max water" },
      prefer: ["Air gap water drop 450", "MAX WATER 420mm", "PORT fill.nozzle"],
      about: "The hot nozzle ends at z480 mm. The geometric maximum waterline is z420 mm, a 60 mm gap. The dotted beads are free-falling water, not a pipe across the gap. The waterline is not a portion recipe or a thermal budget."
    },
    {
      id: "mantle",
      path: "heat",
      swatch: "#e25a32",
      title: "Vessel mantle heater",
      callout: { exterior: "Vessel mantle heater", cutaway: "Vessel mantle heater", exploded: "Vessel mantle heater" },
      prefer: ["Optional direct vessel mantle heater"],
      about: "Optional direct vessel heat, kept as a second input beside the channel. Two heaters still have to share one household supply. Neither arrangement has a validated cook time."
    },
    {
      id: "salt",
      path: "salt",
      swatch: "#d9d0b4",
      title: "Salt gravity chute",
      callout: { exterior: "Salt gravity chute", cutaway: "Salt gravity chute", exploded: "Salt gravity chute" },
      prefer: ["S01 salt.out -> salt.nozzle", "Salt open funnel"],
      about: "Dry salt cartridge and metering gate. The chute falls from z540 mm to the chamber annulus at z480 mm. It does not climb. Bridging, moisture sealing, and a real auger are not in the model. Clean water upstream stays unsalted."
    },
    {
      id: "circ",
      path: "circ",
      swatch: "#1faf78",
      title: "Screened recirculation",
      callout: { exterior: "Screened recirculation", cutaway: "Screened recirculation", exploded: "Recirculation stays attached" },
      prefer: ["C00 strainer.chamber -> strainer.out", "Strainer service union"],
      about: "A separate chamber loop: bar-screen cartridge inside the vessel, bored wall port, service union, pump placeholder, return port, and a tee into the same chamber. Only that tee is a branch. Screening, starch, and seals are unvalidated. In the exploded file this loop stays connected."
    },
    {
      id: "valve",
      path: "drain",
      swatch: "#b58362",
      title: "Low point + NC valve",
      callout: { exterior: "LOW POINT + NC valve", cutaway: "LOW POINT + NC valve", exploded: "Valve accessible" },
      prefer: ["Normally closed drain valve body", "Sloped floor with open low point"],
      about: "The sloped floor ends in an open 24 mm low point at z235 mm. The pipe meets the normally closed valve vertically at z215 mm and leaves at z185 mm. The default gate is closed. That is a geometric state, not a finished drain control."
    },
    {
      id: "downhill",
      path: "drain",
      swatch: "#b58362",
      title: "Downhill drain",
      callout: { exterior: "DOWNHILL drain", cutaway: "DOWNHILL drain", exploded: "Drain stays attached" },
      prefer: ["D02 drain.out -> waste.coupling"],
      about: "After the valve the centerline does not rise. V1 climbed 65 mm with no drain pump. This route stays level or downhill to the receiving coupling at z135 mm. Exploded view does not pull this pipe off its ports."
    },
    {
      id: "waste",
      path: "drain",
      swatch: "#b58362",
      title: "Waste inlet / headspace",
      callout: { exterior: "Waste inlet / headspace", cutaway: "Waste inlet / headspace", exploded: "Waste stays BELOW floor" },
      prefer: ["Removable drain dry break coupling", "Waste maximum fill level"],
      about: "A stub continues to z120 mm inside the waste headspace. The geometric max fill is z95 mm. The reservoir sits below the floor, with its own vent, inlet coupling, and drip tray. Max fill is a line in the model, not a sensor."
    },
    {
      id: "steam",
      path: "steam",
      swatch: "#d7e4ea",
      title: "Steam standpipe",
      callout: { exterior: "Steam standpipe", cutaway: "Steam standpipe", exploded: "Steam standpipe" },
      prefer: ["ST00 steam.pickup -> steam.in", "Steam standpipe rim bracket"],
      about: "Rim-supported headspace standpipe. It is not attached to the removable lid. Steam leaves toward the rear-left, away from the rear-right dry bay. That separation is not a condensation or ingress test."
    },
    {
      id: "dry",
      path: "dry",
      swatch: "#8d98a0",
      title: "Dry bay",
      callout: { exterior: "Dry bay / steam apart", cutaway: "Dry bay / steam apart", exploded: "Dry bay is separate" },
      prefer: ["Dry electronics compartment", "Wet dry barrier"],
      about: "Rear-right dry compartment and a wet/dry barrier. Packaging intent only. It does not prove grounding, leak sensing, or electrical compliance."
    },
    {
      id: "basket",
      path: "cook",
      swatch: "#c5ced1",
      title: "Pasta basket",
      callout: { exterior: "Pasta basket", cutaway: "Pasta basket", exploded: "Basket clears rim 15mm" },
      prefer: ["Basket rim 440", "Basket bridge"],
      about: "Basket bottom sits at z280 mm and, in the exploded file, rises to z470 mm. The vessel rim is z455 mm, so the raised bottom clears it by 15 mm. Mesh spacing is not a manufacturable screen. Nozzle and steam collars stay outside the radial lift sweep. The smallest nominal collar clearance is 5.247 mm, with no tolerance allowance."
    },
    {
      id: "lift",
      path: "cook",
      swatch: "#8d98a0",
      title: "Lift carriage",
      callout: { exterior: "Lift carriage", cutaway: "Lift carriage", exploded: "Lift carriage" },
      prefer: ["Lift load cell carriage", "Lift drive mast"],
      about: "Mast, rails, and a load-cell carriage. The exploded file moves this carriage with the basket. No actuator sizing, interlock, or motion limit is engineered."
    },
    {
      id: "vessel",
      path: "cook",
      swatch: "#9aa7ad",
      title: "Cooking vessel",
      callout: { exterior: "Cooking vessel", cutaway: "Cooking vessel", exploded: "Cooking vessel" },
      prefer: ["Chamber rolled rim", "Vessel rear half"],
      about: "Chamber and rolled rim. The cutaway removes the front shell so the sloped floor opening can be seen. Chassis envelope is about 660 by 480 mm, with the lift mast near 715 mm. Indicative layout, not a compact appliance package."
    },
    {
      id: "lid",
      path: "steam",
      swatch: "#f4f1ea",
      title: "Removable lid",
      callout: { exterior: "Removable lid", cutaway: "Removable lid", exploded: "Lid removed / service" },
      prefer: ["Removable chamber lid", "Cool touch lid handle"],
      about: "The lid has separate apertures around the fixed fill nozzle, salt nozzle, and standpipe. The steam pickup is not part of the lid. Cutaway omits the lid. Exploded sets it aside without moving the pipes."
    },
    {
      id: "case",
      path: "case",
      swatch: "#e7e4dc",
      title: "Guards and chassis",
      callout: { exterior: "Guards and chassis", cutaway: "Guards and chassis", exploded: "Guards and chassis" },
      prefer: ["Chassis drip containment base", "Control console"],
      about: "Drip base, cradle, feet, and outer guards. Paths are left readable instead of buried in a solid box. Not a tested enclosure."
    }
  ];

  function starts(name, prefix) {
    return name.indexOf(prefix) === 0;
  }

  var RULES = [
    ["valve", function (n) { return n === "NC" || starts(n, "NC ") || starts(n, "Normally closed") || starts(n, "Valve actuator") || starts(n, "PORT drain") || starts(n, "PORT chamber.low") || starts(n, "D01"); }],
    ["downhill", function (n) { return starts(n, "D02"); }],
    ["waste", function (n) { return starts(n, "D03") || starts(n, "V0") || starts(n, "PORT waste") || starts(n, "PORT vent") || starts(n, "Waste ") || starts(n, "Removable drain") || n === "DRAIN" || n === "WASTE"; }],
    ["meter", function (n) { return starts(n, "Flowmeter") || starts(n, "Isolation ") || starts(n, "Metering feed") || starts(n, "PORT isolation") || starts(n, "PORT feed") || starts(n, "PORT meter") || starts(n, "F02") || starts(n, "F03") || starts(n, "F04"); }],
    ["water", function (n) { return starts(n, "F0") || starts(n, "PORT tank") || starts(n, "Tank ") || starts(n, "Unsalted") || n === "CLEAN / UNSALTED" || starts(n, "Left tank"); }],
    ["mantle", function (n) { return starts(n, "Optional direct"); }],
    ["gap", function (n) { return starts(n, "Air gap") || starts(n, "PORT fill") || n === "FILL" || starts(n, "MAX WATER") || starts(n, "H02"); }],
    ["heat", function (n) { return starts(n, "H0") || starts(n, "PORT heater") || starts(n, "Heater "); }],
    ["salt", function (n) { return starts(n, "S0") || starts(n, "PORT salt") || starts(n, "Salt ") || n === "SALT"; }],
    ["circ", function (n) { return starts(n, "C0") || starts(n, "PORT circulation") || starts(n, "PORT return") || starts(n, "PORT strainer") || starts(n, "Strainer ") || starts(n, "Intake ") || starts(n, "Removable strainer") || starts(n, "Service union") || starts(n, "Circulation ") || starts(n, "Heat compatible") || n === "RECIRC"; }],
    ["steam", function (n) { return starts(n, "ST") || starts(n, "PORT steam") || starts(n, "Steam "); }],
    ["basket", function (n) { return starts(n, "Basket ") || starts(n, "Lift fork"); }],
    ["lift", function (n) { return starts(n, "Lift ") || starts(n, "Mast lower"); }],
    ["lid", function (n) { return starts(n, "Cool touch") || starts(n, "Removable chamber lid"); }],
    ["dry", function (n) { return n === "DRY BAY" || starts(n, "Dry ") || starts(n, "Wet dry"); }],
    ["vessel", function (n) { return starts(n, "Chamber ") || starts(n, "Sloped ") || starts(n, "Vessel "); }],
    ["case", function (n) { return starts(n, "Anti slip") || starts(n, "Chassis") || starts(n, "Cradle") || starts(n, "Front guard") || starts(n, "Rear outer") || starts(n, "Right outer") || starts(n, "Control console") || starts(n, "Portion dial") || n === "PASTA / 02" || n === "SHAPE + MASS" || starts(n, "Shape display"); }]
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
    function addNode(nodeIndex, parent) {
      var node = json.nodes[nodeIndex];
      if (!node) throw new Error("Missing node " + nodeIndex);
      if (node.matrix) throw new Error("Matrix transforms are not in these files");
      var group = new THREE.Group();
      group.name = node.name || "";
      if (node.translation) group.position.fromArray(node.translation);
      if (node.rotation) group.quaternion.fromArray(node.rotation);
      if (node.scale) group.scale.fromArray(node.scale);
      if (node.mesh !== undefined) {
        var partId = matchPart(group.name);
        if (!partId) unmatched.push(group.name || "(unnamed)");
        meshes[node.mesh].traverse(function (child) {
          if (!child.isMesh) return;
          child.name = group.name;
          child.userData.partId = partId;
          child.userData.baseMaterial = child.material;
          meshCount += 1;
          vertexCount += child.geometry.getAttribute("position").count;
        });
        group.add(meshes[node.mesh]);
      }
      (node.children || []).forEach(function (childIndex) {
        addNode(childIndex, group);
      });
      parent.add(group);
    }
    sceneDef.nodes.forEach(function (nodeIndex) {
      addNode(nodeIndex, object);
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
