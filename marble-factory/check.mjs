import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';
import asm from './assembly.js';

const root = dirname(fileURLToPath(import.meta.url));
const repo = dirname(root);
const manifest = JSON.parse(readFileSync(join(root, 'manifest.json'), 'utf8'));
const assembly = JSON.parse(readFileSync(join(root, 'assembly.json'), 'utf8'));
const readme = readFileSync(join(root, 'README.md'), 'utf8');
const page = readFileSync(join(root, 'index.html'), 'utf8');
const viewer = readFileSync(join(root, 'viewer.js'), 'utf8');
const source = readFileSync(join(root, 'src/export.py'), 'utf8');
const home = readFileSync(join(repo, 'index.html'), 'utf8');

const counts = asm.pieceCounts(manifest.parts);
assert.equal(counts.unique, 32);
assert.equal(counts.printed, 49);
assert.equal(counts.optionalPieces, 8);
assert.equal(counts.coupon, 1);
assert.equal(counts.defaultPieces, 40);
assert.equal(manifest.parts.length, 32);
assert.equal(assembly.instances.length, 38);
assert.equal(manifest.clearances_mm.track_slope_deg, 7.13);
assert.match(manifest.clearances_mm.track_slope_note, /20 mm drop per 160 mm/);
assert.match(source, /atan\(20 \/ 160\)/);
assert.doesNotMatch(source, /atan\(12 \/ 160\)/);
assert.match(readme, /7\.13°/);
assert.match(readme, /Unprinted prototype/);
assert.match(readme, /not a certified toy/i);
assert.match(manifest.ball_center_paths_note, /7\.13/);

const names = new Set(manifest.parts.map((part) => part.name));
assert.equal(names.size, 32);
for (const part of manifest.parts) {
  const path = join(root, 'stl', part.name + '.stl');
  assert.ok(existsSync(path), part.name);
  const parsed = asm.parseStl(readFileSync(path));
  assert.equal(parsed.triangles, part.faces, part.name);
  let minZ = Infinity;
  for (let i = 2; i < parsed.positions.length; i += 3) minZ = Math.min(minZ, parsed.positions[i]);
  assert.ok(minZ >= -0.05, part.name + ' bed at ' + minZ);
  const extent = Math.max(...part.extents_mm);
  assert.ok(extent <= 330, part.name + ' extent ' + extent);
}

const back = manifest.parts.find((part) => part.name === 'lift_housing_back');
assert.ok(Math.abs(back.extents_mm[0] - 294) < 0.05);
assert.ok(Math.abs(back.extents_mm[1] - 267.5) < 0.05);
assert.ok(Math.abs(back.extents_mm[2] - 52) < 0.05);
const ball = manifest.parts.find((part) => part.name === 'ball_35');
assert.equal(ball.supports, true);
assert.equal(ball.qty, 6);

const placed = {};
for (const instance of assembly.instances) {
  assert.ok(names.has(instance.part), instance.part);
  assert.equal(instance.transform.length, 4);
  assert.equal(instance.transform[3][3], 1);
  asm.explodeMm(instance.part, instance.index);
  placed[instance.part] = (placed[instance.part] || 0) + 1;
  if (asm.OPTIONAL[instance.part]) assert.fail(instance.part + ' is placed on the default loop');
}
assert.equal(placed.track_straight_160, 4);
assert.equal(placed.track_straight_80, 1);
assert.equal(placed.track_corner_right, 3);
assert.equal(placed.lift_inlet_chute, 1);
assert.equal(placed.ball_35, 6);
assert.equal(placed.base_tile, 6);
assert.equal(placed.lift_wheel_half, 2);
assert.equal(placed.lift_crank, 1);
assert.equal(placed.track_corner_left, undefined);
assert.deepEqual(
  assembly.instances.filter((item) => item.part === 'track_corner_right').map((item) => item.at),
  ['J1', 'J3', 'J6']
);
assert.deepEqual(
  assembly.instances.filter((item) => item.part === 'track_straight_160').map((item) => item.at),
  ['J0', 'J2', 'J4', 'J7']
);

function restPoint(part, index, local) {
  const instance = assembly.instances.find((item) => item.part === part && item.index === index);
  return asm.apply(instance.transform, local);
}

function spunPoint(part, index, local, deg) {
  const instance = assembly.instances.find((item) => item.part === part && item.index === index);
  return asm.apply(asm.poseMatrix(instance.transform, part, deg, [0, 0, 0], 0), local);
}

for (const part of ['lift_crank', 'lift_axle', 'lift_wheel_half', 'lift_clip', 'lift_pawl', 'lift_housing_front']) {
  const parsed = asm.parseStl(readFileSync(join(root, 'stl', part + '.stl')));
  let best = null;
  let bestRadius = -1;
  for (let i = 0; i < parsed.positions.length; i += 3) {
    const local = [parsed.positions[i], parsed.positions[i + 1], parsed.positions[i + 2], 1];
    const world = restPoint(part, 0, local);
    const radius = asm.axisDistance(world);
    if (radius > bestRadius) {
      bestRadius = radius;
      best = local;
    }
  }
  const before = restPoint(part, 0, best);
  const after = spunPoint(part, 0, best, 90);
  const home = spunPoint(part, 0, best, 0);
  assert.ok(Math.hypot(home[0] - before[0], home[1] - before[1], home[2] - before[2]) < 1e-6, part + ' home');
  if (asm.SPIN_PARTS[part]) {
    assert.ok(Math.hypot(after[0] - before[0], after[1] - before[1], after[2] - before[2]) > 1, part + ' did not spin');
    assert.ok(Math.abs(asm.axisDistance(after) - asm.axisDistance(before)) < 0.05, part + ' left the axle');
    assert.ok(Math.abs(after[1] - before[1]) < 0.05, part + ' shifted along the axle');
  } else {
    assert.ok(Math.hypot(after[0] - before[0], after[1] - before[1], after[2] - before[2]) < 1e-6, part + ' spun');
  }
}

const crank = asm.parseStl(readFileSync(join(root, 'stl/lift_crank.stl')));
let probe = null;
let probeR = -1;
for (let i = 0; i < crank.positions.length; i += 3) {
  const local = [crank.positions[i], crank.positions[i + 1], crank.positions[i + 2], 1];
  const world = restPoint('lift_crank', 0, local);
  const radius = asm.axisDistance(world);
  if (radius > probeR) {
    probeR = radius;
    probe = { local, world };
  }
}
const lifted = spunPoint('lift_crank', 0, probe.local, 90);
const dx = probe.world[0] - 80;
const dz = probe.world[2] - 136;
const expectX = 80 + dx * Math.cos(Math.PI / 2) - dz * Math.sin(Math.PI / 2);
const expectZ = 136 + dx * Math.sin(Math.PI / 2) + dz * Math.cos(Math.PI / 2);
assert.ok(Math.abs(lifted[0] - expectX) < 0.05, 'crank x ' + lifted[0] + ' vs ' + expectX);
assert.ok(Math.abs(lifted[2] - expectZ) < 0.05, 'crank z ' + lifted[2] + ' vs ' + expectZ);
assert.ok(lifted[2] > probe.world[2], 'lift direction should move the crank arm toward +Z');

const paths = JSON.parse(readFileSync(join(root, 'reports/ball_paths.json'), 'utf8'));
assert.equal(paths.default_loop.length, 247);
let maxStep = 0;
let uphill = 0;
for (let i = 1; i < paths.default_loop.length; i++) {
  const a = paths.default_loop[i - 1];
  const b = paths.default_loop[i];
  maxStep = Math.max(maxStep, Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]));
  if (b[2] > a[2] + 0.15) uphill += 1;
}
assert.equal(uphill, 0);
assert.ok(maxStep < 30, 'path step ' + maxStep);
assert.match(viewer, /default_loop/);
assert.doesNotMatch(viewer, /paths\.lift|lift_log/);

assert.match(asm.claimSentence(), /Unprinted prototype/);
assert.match(asm.claimSentence(), /not a certified toy/);
assert.match(asm.claimSentence(), /fit coupon/i);
assert.equal(asm.fileKind('assembly-scene').includes('not a plate'), true);
assert.equal(asm.fileKind('kit-zip').includes('no G-code'), true);
assert.throws(() => asm.fileKind('bambu-sliced-3mf'));

assert.match(home, /href="\/marble-factory\/"/);
assert.match(home, /href="\/observatory\/"/);
assert.match(home, /href="\/dollhouse\/"/);
assert.match(home, /href="\/workbench\/"/);
assert.match(home, /Not a certified toy/);
assert.match(page, /assembly\.js/);
assert.match(page, /viewer\.js/);
assert.match(page, /marble-factory-kit\.zip/);
assert.match(page, /fit_coupon\.stl/);
assert.match(page, /marble_factory_assembly\.3mf/);
assert.doesNotMatch(page + viewer, /\.gcode/);
assert.match(viewer, /17\.15 mm/);
assert.match(viewer, /not drop-in/i);

for (const name of [
  'marble_factory_assembly.3mf',
  'README.md',
  'SUPPORT_NOTES.md',
  'reports/VALIDATION.md',
  'slice/SLICE_REPORT.md',
  'renders/01_overview.png',
  'src/assembly.py',
  'src/lift.py',
  'src/tracks.py'
]) {
  assert.ok(existsSync(join(root, name)), name);
}

const slice = readFileSync(join(root, 'slice/SLICE_REPORT.md'), 'utf8');
assert.match(slice, /PrusaSlicer 2\.7\.4/);
assert.match(slice, /\*\*Not\*\* an official H3C profile/);
assert.match(slice, /32\/32/);
assert.match(slice, /ball_35/);

function walk(dir, found) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) walk(path, found);
    else if (/\.gcode$/i.test(entry.name)) found.push(path);
  }
}
const gcode = [];
walk(root, gcode);
assert.deepEqual(gcode, []);

const listing = execFileSync('unzip', ['-Z1', join(root, 'marble-factory-kit.zip')], { encoding: 'utf8' });
const zipNames = listing.trim().split('\n');
const zipStls = zipNames.filter((name) => name.startsWith('stl/') && name.endsWith('.stl'));
assert.equal(zipStls.length, 32);
assert.ok(zipNames.includes('manifest.json'));
assert.ok(zipNames.includes('assembly.json'));
assert.ok(zipNames.includes('README.md'));
assert.ok(zipNames.includes('marble_factory_assembly.3mf'));
assert.ok(zipNames.includes('src/export.py'));
assert.ok(zipNames.includes('slice/SLICE_REPORT.md'));
assert.equal(zipNames.some((name) => name.toLowerCase().endsWith('.gcode')), false);
assert.equal(zipNames.some((name) => name.endsWith('index.html')), false);

console.log('marble factory checks passed');
console.log(asm.claimSentence());
console.log('pieces', counts);
console.log('crank arm radius', probeR.toFixed(2), 'mm');
