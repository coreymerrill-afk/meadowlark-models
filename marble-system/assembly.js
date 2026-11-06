/* Pose math for the marble-system viewer.
   Track STLs are the generator's Rx(180) print orientation.
   Support clips and caps use the inverse of their print rotations.
   Crank spin is the v1 lift direction about the layout axle. */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.MarbleSystem = api;
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

  function trans(x, y, z) {
    return [[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]];
  }

  function rotyXZ(deg) {
    var r = deg * Math.PI / 180;
    var c = Math.cos(r);
    var s = Math.sin(r);
    return [[c, 0, -s, 0], [0, 1, 0, 0], [s, 0, c, 0], [0, 0, 0, 1]];
  }

  function spinAbout(origin, deg) {
    return mul(trans(origin[0], origin[1], origin[2]), mul(rotyXZ(deg), trans(-origin[0], -origin[1], -origin[2])));
  }

  function explodeFor(role) {
    switch (role) {
      case 'base': return [0, 0, -100];
      case 'track': return [0, 0, 200];
      case 'support': return [0, 0, 140];
      case 'low': return [0, 0, 70];
      case 'plate': return [0, 80, 30];
      case 'lift': return [0, 220, 40];
      default: return assertNever(role);
    }
  }

  function poseMatrix(rest, spin, axle, crankDeg, heightDelta, explode, explodeT) {
    var m = rest;
    if (heightDelta) m = mul(trans(0, 0, heightDelta), m);
    if (spin && crankDeg) m = mul(spinAbout(axle, crankDeg), m);
    if (explodeT) {
      m = mul(trans(explode[0] * explodeT, explode[1] * explodeT, explode[2] * explodeT), m);
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

  function claimSentence() {
    return 'Unprinted v2 prototype. Layouts A and B are computational examples, not a measured print and not a certified toy. Print the fit coupon and one short support before the rest of the kit. Creep, fatigue, rolling, and helix sag are untested.';
  }

  function fileKind(kind) {
    switch (kind) {
      case 'individual-stl':
        return 'One STL mesh · not a toolpath';
      case 'kit-zip':
        return 'Kit ZIP · meshes, notes, and source · no G-code';
      case 'assembly-scene':
        return 'Layout A colored scene · not a plate and not sliced';
      case 'coupon':
        return 'Interface coupon · print this first';
      case 'source':
        return 'Python source · not a print file';
      case 'readme':
        return 'Kit notes';
      default:
        return assertNever(kind);
    }
  }

  return {
    mul: mul,
    apply: apply,
    spinAbout: spinAbout,
    explodeFor: explodeFor,
    poseMatrix: poseMatrix,
    parseStl: parseStl,
    claimSentence: claimSentence,
    fileKind: fileKind
  };
});
