/* Pose math for the marble-factory viewer.
   assembly.json matrices are millimeters, CAD Z-up, row-major, applied as given.
   The crank spin is the kit's roty_xz: positive degrees move +X toward +Z
   about the axle (0, 1, 0) through the lift origin. That is the documented
   lift direction. It is not a ball simulation. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.MarbleAssembly = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  var AXLE_ORIGIN = [80, 0, 136];
  var AXLE_AXIS = [0, 1, 0];

  var SPIN_PARTS = {
    lift_wheel_half: true,
    lift_axle: true,
    lift_crank: true
  };

  var OPTIONAL = {
    track_switch_Y: true,
    track_merge_Y: true,
    track_spinner: true,
    switch_gate: true,
    spinner_rotor: true,
    spinner_post: true,
    spinner_retainer: true
  };

  function assertNever(value) {
    throw new Error('Unhandled case: ' + String(value));
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

  function apply(m, p) {
    var x = p[0], y = p[1], z = p[2], w = p.length > 3 ? p[3] : 1;
    return [
      m[0][0] * x + m[0][1] * y + m[0][2] * z + m[0][3] * w,
      m[1][0] * x + m[1][1] * y + m[1][2] * z + m[1][3] * w,
      m[2][0] * x + m[2][1] * y + m[2][2] * z + m[2][3] * w
    ];
  }

  function translate(v) {
    return [
      [1, 0, 0, v[0]],
      [0, 1, 0, v[1]],
      [0, 0, 1, v[2]],
      [0, 0, 0, 1]
    ];
  }

  /* Kit lift.roty_xz: CCW in the XZ plane, +X toward +Z. */
  function rotyXZ(deg) {
    var r = deg * Math.PI / 180;
    var c = Math.cos(r);
    var s = Math.sin(r);
    return [
      [c, 0, -s, 0],
      [0, 1, 0, 0],
      [s, 0, c, 0],
      [0, 0, 0, 1]
    ];
  }

  function spinAboutAxle(deg) {
    return mul(translate(AXLE_ORIGIN), mul(rotyXZ(deg), translate([-AXLE_ORIGIN[0], -AXLE_ORIGIN[1], -AXLE_ORIGIN[2]])));
  }

  function poseMatrix(rest, part, spinDeg, explode, explodeT) {
    var m = rest;
    if (SPIN_PARTS[part] && spinDeg) m = mul(spinAboutAxle(spinDeg), m);
    if (explodeT) {
      m = mul(translate([
        explode[0] * explodeT,
        explode[1] * explodeT,
        explode[2] * explodeT
      ]), m);
    }
    return m;
  }

  /* Viewer spread only. Not a CAD disassembly path and not a build step. */
  function explodeMm(part, index) {
    switch (part) {
      case 'base_tile':
        return [0, 0, -120];
      case 'lift_housing_back':
        return [0, -280, 40];
      case 'lift_housing_front':
        return [0, 320, 40];
      case 'lift_wheel_half':
        return [0, index === 0 ? 160 : -160, 120];
      case 'lift_axle':
        return [0, 460, 80];
      case 'lift_crank':
        return [0, 560, 40];
      case 'lift_clip':
        return [0, 660, 20];
      case 'lift_pawl':
        return [-200, -40, 80];
      case 'lift_inlet_chute':
        return [140, 80, 180];
      case 'ball_35':
        return [0, 0, 260];
      case 'track_straight_160':
      case 'track_straight_80':
      case 'track_corner_right':
        return [0, 0, 220];
      default:
        if (part.indexOf('stand_') === 0) return [0, 0, 90];
        return assertNever(part);
    }
  }

  function parseStl(buffer) {
    var bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
    if (bytes.length >= 84) {
      var view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
      var count = view.getUint32(80, true);
      if (count > 0 && 84 + count * 50 === bytes.length) {
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
    }
    throw new Error('Expected a binary STL');
  }

  function pieceCounts(parts) {
    var printed = 0;
    var optionalPieces = 0;
    var coupon = 0;
    parts.forEach(function (part) {
      printed += part.qty;
      if (OPTIONAL[part.name]) optionalPieces += part.qty;
      if (part.name === 'fit_coupon') coupon += part.qty;
    });
    return {
      unique: parts.length,
      printed: printed,
      optionalPieces: optionalPieces,
      coupon: coupon,
      defaultPieces: printed - optionalPieces - coupon
    };
  }

  function claimSentence() {
    return 'Unprinted prototype. Computational checks only — not a measured print, and not a certified toy. Print the fit coupon and the lift-only test before the full circuit. An adult should test it before a child plays with it.';
  }

  function fileKind(kind) {
    switch (kind) {
      case 'individual-stl':
        return 'One STL mesh · not a toolpath';
      case 'kit-zip':
        return 'Kit ZIP · meshes, scene, source, and notes · no G-code';
      case 'assembly-scene':
        return 'Colored assembly scene · not a plate and not sliced';
      case 'coupon':
        return 'Fit coupon · print this first';
      case 'source':
        return 'Python source · not a print file';
      case 'readme':
        return 'Kit notes';
      default:
        return assertNever(kind);
    }
  }

  function axisDistance(point) {
    var dx = point[0] - AXLE_ORIGIN[0];
    var dz = point[2] - AXLE_ORIGIN[2];
    return Math.hypot(dx, dz);
  }

  return {
    AXLE_ORIGIN: AXLE_ORIGIN,
    AXLE_AXIS: AXLE_AXIS,
    SPIN_PARTS: SPIN_PARTS,
    OPTIONAL: OPTIONAL,
    mul: mul,
    apply: apply,
    poseMatrix: poseMatrix,
    explodeMm: explodeMm,
    spinAboutAxle: spinAboutAxle,
    parseStl: parseStl,
    pieceCounts: pieceCounts,
    claimSentence: claimSentence,
    fileKind: fileKind,
    axisDistance: axisDistance
  };
});
