import { readFileSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../..', import.meta.url));
const here = fileURLToPath(new URL('.', import.meta.url));

function read(path) {
  return readFileSync(path, 'utf8');
}

const manifest = JSON.parse(read(here + 'manifest.json'));
const validation = JSON.parse(read(here + 'reports/validation.json'));
const home = read(root + 'index.html');
const kit = read(root + 'dollhouse/index.html');
const grand = read(root + 'dollhouse/grand.js');
const stls = new Set(readdirSync(here + 'stl').filter((name) => name.endsWith('.stl')));

const errors = [];
function assert(cond, message) {
  if (!cond) errors.push(message);
}

assert(validation.ok === true, 'validation.ok');
assert(manifest.validation.printed === false, 'printed flag');
assert(manifest.validation.measured === false, 'measured flag');
assert(manifest.validation.forces_tested === false, 'forces flag');
assert(manifest.validation.h3c_sliced === false, 'slice flag');
assert(manifest.validation.cad_validated === true, 'cad flag');
assert(manifest.legacy_interface.snap_compatible === false, 'snap claim');
assert(manifest.legacy_interface.bay_width_over_measured_tile === 2, 'tile multiple');
assert(manifest.legacy_interface.depth_matches_two_tiles === false, 'depth claim');
assert(manifest.instances.length === validation.instance_count, 'instance count');
assert(manifest.parts.length === stls.size, 'part count matches stl directory');

manifest.instances.forEach((instance) => {
  const part = manifest.parts.find((item) => item.id === instance.part);
  assert(part, 'missing part ' + instance.part);
  if (!part) return;
  assert(stls.has(part.file.replace('stl/', '')), 'missing file ' + part.file);
  assert(instance.transform.length === 4, 'transform rows ' + instance.id);
  assert(instance.transform[3][0] === 0 && instance.transform[3][3] === 1, 'transform row ' + instance.id);
});
manifest.parts.forEach((part) => {
  assert(stls.has(part.file.replace('stl/', '')), 'part file missing ' + part.file);
});
stls.forEach((name) => {
  assert(manifest.parts.some((part) => part.file === 'stl/' + name), 'unlisted stl ' + name);
});
assert(manifest.bom.find((row) => row.part === 'qa_coupon_socket_v1').qty === 1, 'coupon qty');

assert(home.includes('href="/dollhouse/queen-anne/"'), 'home link');
assert(home.includes('href="/dollhouse/"'), 'home still links the play kit');
assert(home.includes('href="/marble-factory/"'), 'home marble factory');
assert(home.includes('href="/marble-system/"'), 'home marble system');
assert(home.includes('href="/observatory/"'), 'home observatory');
assert(kit.includes('href="/dollhouse/queen-anne/"'), 'kit page link');
['Bramble Cottage', 'Larkspur', 'Pennywhistle', 'Cloisterwick', 'Cogsworth', 'Electrified'].forEach((name) => {
  assert(grand.includes(name), 'missing manor ' + name);
});
assert(!grand.includes('queen-anne'), 'queen anne must stay out of the six-manor viewer');

const page = read(here + 'index.html');
assert(page.includes('data-mode="closed"'), 'closed control');
assert(page.includes('data-mode="open"'), 'open control');
assert(page.includes('data-mode="remove-panels"'), 'panel control');
assert(page.includes('data-mode="roof"'), 'roof control');
assert(page.includes('data-mode="explode"'), 'explode control');
assert(page.includes('/dollhouse/queen-anne/viewer.js'), 'viewer script');

if (errors.length) {
  console.error(errors.join('\n'));
  process.exit(1);
}
console.log(JSON.stringify({
  ok: true,
  parts: manifest.parts.length,
  instances: manifest.instances.length,
  triangles: validation.triangles,
  assembly: validation.assembly_mm
}));
