/* Pose math for the observatory viewer.
   Manifest matrices are millimeters, CAD Z-up, row-major, and are applied as given.
   Motion is an extra rotation about the manifest pivot and axis. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.ObservatoryAssembly = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

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

  function quatToMat(x, y, z, w) {
    return [
      [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0],
      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0],
      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0],
      [0, 0, 0, 1]
    ];
  }

  function spinAbout(pivot, axis, deg) {
    var len = Math.hypot(axis[0], axis[1], axis[2]) || 1;
    var half = deg * Math.PI / 360;
    var s = Math.sin(half);
    var q = quatToMat(axis[0] / len * s, axis[1] / len * s, axis[2] / len * s, Math.cos(half));
    return mul(translate(pivot), mul(q, translate([-pivot[0], -pivot[1], -pivot[2]])));
  }

  function isVertical(axis) {
    return Math.abs(axis[2]) >= 0.9;
  }

  /* spins: {pivot, axis, home, angle, sign}. Non-vertical joints apply first. */
  function poseMatrix(rest, spins, explode, explodeT) {
    var ordered = spins.slice().sort(function (a, b) {
      return (isVertical(a.axis) ? 1 : 0) - (isVertical(b.axis) ? 1 : 0);
    });
    var m = rest;
    ordered.forEach(function (spin) {
      var delta = (spin.angle - spin.home) * spin.sign;
      m = mul(spinAbout(spin.pivot, spin.axis, delta), m);
    });
    if (explodeT) {
      m = mul(translate([
        explode[0] * explodeT,
        explode[1] * explodeT,
        explode[2] * explodeT
      ]), m);
    }
    return m;
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

  function claimSentence(manifest) {
    var flags = manifest.validation || {};
    if (flags.printed || flags.measured || flags.physically_verified) {
      throw new Error('manifest must stay unprinted and unmeasured');
    }
    if (flags.cad_validated) {
      return 'CAD-validated, unprinted prototype. Not measured and not physically tested. Sizes are the CAD model, not caliper readings.';
    }
    return 'Not CAD-validated, not printed, and not measured.';
  }

  function fileKind(kind) {
    switch (kind) {
      case 'individual-part-stls':
        return 'Individual STLs · one mesh per part, not a G-code file';
      case 'colored-assembly-scene':
        return 'Colored assembly scene · not a plate layout';
      case 'bambu-sliced-3mf':
        return 'Bambu-sliced 3MF · toolpaths from Bambu Studio';
      case 'coupon-stl':
        return 'First-print coupon · print this before the observatory';
      case 'source':
        return 'CAD source · not a print file';
      default:
        return assertNever(kind);
    }
  }

  return {
    mul: mul,
    apply: apply,
    poseMatrix: poseMatrix,
    parseStl: parseStl,
    claimSentence: claimSentence,
    fileKind: fileKind
  };
});
