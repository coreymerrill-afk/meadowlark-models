import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import assert from 'node:assert/strict';
import asm from './assembly.js';

const root = dirname(fileURLToPath(import.meta.url));
const repo = dirname(root);
const manifest = JSON.parse(readFileSync(join(root, 'manifest.json'), 'utf8'));

assert.equal(manifest.validation.cad_validated, true);
assert.equal(manifest.validation.printed, false);
assert.equal(manifest.validation.measured, false);
assert.equal(manifest.validation.physically_verified, false);
assert.deepEqual(manifest.validation.issues, []);
assert.equal(manifest.target_printer.nozzle_mm, 0.4);
assert.ok(manifest.assembled_size_mm.x < 220);
assert.ok(manifest.assembled_size_mm.y < 220);
assert.ok(manifest.assembled_size_mm.z < 220);
const ringed = manifest.parts.find((part) => part.id === 'planet_ringed');
assert.match(ringed.print_notes, /Supports are required/);
assert.match(ringed.print_notes, /no extrusions in the first layer/);
assert.match(manifest.slice.summary, /PrusaSlicer 2.7.4/);
assert.equal(manifest.slice.gcode_distributed, false);
assert.equal(manifest.slice.official_h3c_profile, false);
assert.ok(manifest.slice.supports_required.includes('planet_ringed'));
assert.equal(manifest.artifacts.scene_3mf_kind, 'colored-assembly-scene');
assert.equal(manifest.artifacts.stl_zip_kind, 'individual-part-stls');
assert.match(manifest.artifacts.scene_3mf_note, /not sliced as a plate/i);
assert.equal(asm.fileKind('bambu-sliced-3mf').includes('Bambu-sliced'), true);
assert.equal(asm.fileKind(manifest.artifacts.scene_3mf_kind).includes('not a plate'), true);

const claim = asm.claimSentence(manifest);
assert.match(claim, /CAD-validated, unprinted prototype/);
assert.match(claim, /Not measured/);
assert.match(claim, /not physically tested/i);

assert.equal(manifest.parts.length, 19);
const files = new Set(manifest.parts.map((part) => part.filename));
assert.equal(files.size, 19);
for (const part of manifest.parts) {
  const path = join(root, part.filename);
  assert.ok(existsSync(path), part.filename);
  const parsed = asm.parseStl(readFileSync(path));
  assert.ok(parsed.triangles > 0, part.id);
  let minZ = Infinity;
  for (let i = 2; i < parsed.positions.length; i += 3) minZ = Math.min(minZ, parsed.positions[i]);
  assert.ok(minZ >= -0.05, part.id + ' bed at ' + minZ);
}

for (const name of [
  manifest.artifacts.stl_zip,
  manifest.artifacts.scene_3mf,
  manifest.artifacts.generator,
  manifest.artifacts.coupon_stl,
  manifest.artifacts.preview
]) {
  assert.ok(existsSync(join(root, name)), name);
}

const home = readFileSync(join(repo, 'index.html'), 'utf8');
assert.match(home, /href="\/observatory\/"/);
assert.match(home, /unprinted/);

const page = readFileSync(join(root, 'index.html'), 'utf8');
assert.match(page, /assembly\.js/);
assert.match(page, /viewer\.js/);
assert.doesNotMatch(page, /physically tested and/);

const telescope = manifest.assembly_instances.find((item) => item.part_id === 'telescope_tube');
const pivot = manifest.pivots.find((item) => item.id === 'telescope_altitude');
const homePoint = asm.apply(asm.poseMatrix(telescope.transform, [], [0, 0, 0], 0), [0, 0, telescope.trunnion_z, 1]);
const dx = homePoint[0] - pivot.origin_mm[0];
const dy = homePoint[1] - pivot.origin_mm[1];
const dz = homePoint[2] - pivot.origin_mm[2];
assert.ok(Math.hypot(dx, dy, dz) < 1e-3, 'trunnion off hinge ' + [dx, dy, dz]);

const spun = asm.poseMatrix(telescope.transform, [{
  pivot: pivot.origin_mm,
  axis: pivot.axis,
  home: pivot.home_deg,
  angle: pivot.limits_deg[1],
  sign: pivot.delta_sign
}], telescope.explode_mm, 0);
const still = asm.apply(spun, [0, 0, telescope.trunnion_z, 1]);
assert.ok(Math.hypot(still[0] - pivot.origin_mm[0], still[1] - pivot.origin_mm[1], still[2] - pivot.origin_mm[2]) < 1e-3);

const lifted = asm.apply(asm.poseMatrix(telescope.transform, [], telescope.explode_mm, 1), [0, 0, 0, 1]);
const parked = asm.apply(telescope.transform, [0, 0, 0, 1]);
assert.ok(Math.abs((lifted[0] - parked[0]) - telescope.explode_mm[0]) < 1e-6);

console.log('observatory checks passed');
console.log(claim);
console.log('envelope', manifest.assembled_size_mm.x, manifest.assembled_size_mm.y, manifest.assembled_size_mm.z);
