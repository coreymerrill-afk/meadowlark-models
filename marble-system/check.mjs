import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { execFileSync } from 'node:child_process';
import assert from 'node:assert/strict';
import asm from './assembly.js';

const root = dirname(fileURLToPath(import.meta.url));
const repo = dirname(root);
const manifest = JSON.parse(readFileSync(join(root, 'kit/manifest.json'), 'utf8'));
const assembly = JSON.parse(readFileSync(join(root, 'kit/assembly.json'), 'utf8'));
const scenes = JSON.parse(readFileSync(join(root, 'scenes.json'), 'utf8'));
const readme = readFileSync(join(root, 'README.md'), 'utf8');
const page = readFileSync(join(root, 'index.html'), 'utf8');
const home = readFileSync(join(repo, 'index.html'), 'utf8');
const v1 = readFileSync(join(repo, 'marble-factory/index.html'), 'utf8');

assert.ok(manifest.parts.length >= 45, manifest.parts.length);
assert.equal(manifest.bom48_sum, 48);
assert.equal(manifest.well_count, 117);
assert.equal(manifest.support_structures.total, 24);
assert.deepEqual(manifest.assembled_mm, [609.6, 457.2]);
assert.equal(manifest.grid_pitch_mm, 40);
assert.equal(manifest.height_classes.short.Hmin, 70);
assert.equal(manifest.height_classes.tall.Hmax, 230);
assert.equal(manifest.wells_per_tile['00'] + manifest.wells_per_tile['01'] + manifest.wells_per_tile['10'] + manifest.wells_per_tile['11'], 117);

let trackQty = 0;
for (const row of manifest.bom48) trackQty += row.qty;
assert.equal(trackQty, 48);

for (const part of manifest.parts) {
  const path = join(root, 'stl', part.name + '.stl');
  assert.ok(existsSync(path), part.name);
  const parsed = asm.parseStl(readFileSync(path));
  assert.equal(parsed.triangles, part.faces, part.name);
  const ext = part.extents_mm;
  assert.ok(ext[0] <= 330 && ext[1] <= 320 && ext[2] <= 325, part.name);
}
const tile = manifest.parts.find((part) => part.name === 'tile_00');
assert.deepEqual(tile.extents_mm, [304.8, 228.6, 12]);
const helix = manifest.parts.find((part) => part.name === 'track_HX360');
assert.ok(Math.max(helix.extents_mm[0], helix.extents_mm[1]) <= 320);

assert.equal(scenes.A.installedTracks, 10);
assert.equal(scenes.A.installedPosts, 9);
assert.equal(scenes.A.lowMounts, 3);
assert.equal(scenes.B.installedTracks, 8);
assert.equal(scenes.B.installedPosts, 2);
assert.equal(scenes.B.lowMounts, 6);
assert.equal(scenes.A.computedAdaptDrop, 19.21);
assert.equal(scenes.B.computedAdaptDrop, 15.21);

const aTracks = scenes.A.instances.filter((item) => item.role === 'track');
assert.equal(aTracks.length, 10);
assert.ok(aTracks.some((item) => item.part === 'ADAPT_OUT'));
assert.ok(aTracks.some((item) => item.part === 'ADAPT_IN'));
assert.equal(aTracks.filter((item) => item.part === 'track_SPLIT_Y').length, 0);
assert.equal(scenes.B.instances.filter((item) => item.part === 'track_HX360').length, 1);
assert.equal(scenes.A.instances.filter((item) => item.role === 'lift').length, 8);
assert.equal(scenes.A.instances.filter((item) => item.part === 'lift_wheel_half' && item.spin).length, 2);

const straight = scenes.A.instances.find((item) => item.id === 'S160_1');
assert.equal(straight.transform[0][3], 300);
assert.equal(straight.transform[1][3], 100);
assert.equal(straight.transform[2][3], 180.96);
const post = scenes.A.instances.find((item) => item.id === 'h0-post');
assert.equal(post.kind, 'tall');
assert.equal(post.H, 165);
assert.equal(post.transform[2][3], 20);

for (const lay of assembly) {
  assert.equal(lay.within_24, true);
  assert.ok(lay.adapt_in_drop > 0);
  for (const item of lay.posts) {
    const spec = manifest.height_classes[item.kind];
    assert.ok(item.H >= spec.Hmin && item.H <= spec.Hmax, item.H + ' ' + item.kind);
  }
}

const axle = scenes.A.axle;
const spun = asm.apply(asm.poseMatrix(straight.transform, true, axle, 90, 0, [0, 0, 0], 0), [0, 0, 0, 1]);
const parked = asm.apply(straight.transform, [0, 0, 0, 1]);
assert.ok(Math.hypot(spun[0] - parked[0], spun[1] - parked[1], spun[2] - parked[2]) > 1);

assert.match(readme, /Do not print the full kit/);
assert.match(readme, /design study/i);
assert.match(readme, /1\.01 mm³/);
assert.equal(manifest.public_status.layout_a_35mm_ball_clear, true);
assert.equal(manifest.public_status.layout_b_working_route, false);
assert.equal(manifest.public_status.do_not_print_full_kit, true);
assert.equal(manifest.public_status.full_48_play_kit, false);
assert.equal(manifest.public_status.kit_zip_regenerated, true);
assert.match(readme, /no G-code|G-code is not included/i);
assert.doesNotMatch(readme, /gcode \+ SLICE/);
assert.match(page, /marble-factory/);
assert.match(page, /fit_coupon/);
assert.match(page, /Do not print the full kit/);
assert.match(page, /design study/);
assert.doesNotMatch(page, /marble-system-v2-kit\.zip/);
assert.doesNotMatch(page, /layoutA\.3mf/);
assert.match(asm.claimSentence(), /Do not print the full kit/);
assert.match(asm.claimSentence(), /design study/);
assert.match(v1, /marble-system/);
assert.match(home, /href="\/marble-factory\/"/);
assert.match(home, /href="\/marble-system\/"/);
assert.match(home, /href="\/observatory\/"/);
assert.match(home, /href="\/dollhouse\/"/);
assert.match(home, /href="\/workbench\/"/);
assert.equal(asm.fileKind('assembly-scene').includes('not a plate'), true);
assert.throws(() => asm.fileKind('gcode'));

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

const listing = execFileSync('unzip', ['-Z1', join(root, 'marble-system-v2-kit.zip')], { encoding: 'utf8' });
const names = listing.trim().split('\n');
const stls = names.filter((name) => name.startsWith('stl/') && name.endsWith('.stl'));
assert.equal(stls.length, manifest.parts.length);
assert.ok(names.includes('README.md'));
assert.ok(names.includes('kit/manifest.json'));
assert.ok(names.includes('kit/assembly.json'));
assert.ok(names.includes('RESEARCH_BRIEF.md'));
assert.equal(names.some((name) => name.toLowerCase().endsWith('.gcode')), false);
assert.equal(names.some((name) => name.endsWith('index.html')), false);

console.log('marble system checks passed');
console.log(asm.claimSentence());
console.log('A instances', scenes.A.instances.length, 'B', scenes.B.instances.length);
