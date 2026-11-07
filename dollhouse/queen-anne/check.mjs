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
assert(manifest.version === '6.5.2', 'version');
assert(manifest.prior_version === 'archive/v4.0.0', 'v4 archive pointer');
assert(manifest.magnet.status === 'NOMINAL_NOT_FIT_APPROVED', 'magnet status');
assert(manifest.magnet.nominal_mm[0] === 5 && manifest.magnet.nominal_mm[1] === 2.8, 'magnet nominal');
assert(manifest.magnet.holding_force_calculated === false, 'no force from size');
assert(manifest.magnet.h3c_pause_profile === false, 'no pause profile');
assert(manifest.magnet.retention === 'nominal_M2_screw_and_captive_nut_not_safety_validated', 'captive nut retention');
assert(manifest.validation.h3c_pause_profile === false, 'validation pause flag');
assert(manifest.validation.electrically_tested === false, 'no electrical test');
assert(manifest.validation.protection_finalized === false, 'protection open');
assert(manifest.validation.led_fit_validated === false, 'led fit open');
assert(manifest.lighting.fixture_count === 10, 'fixture count from this house');
assert(manifest.lighting.fuse_nominated === false, 'no fuse nominated from the milliamp sum');
assert(manifest.lighting.research_scenario_leds === 24, 'research scenario kept distinct');
assert(manifest.lighting.fixture_count !== manifest.lighting.research_scenario_leds, 'do not use the 24-led scenario');
assert(manifest.lighting.cavity_status === 'PROVISIONAL_NOT_FIT_VALIDATED', 'cavity status');
assert(manifest.lighting.mains_inside === false, 'no mains');
assert(manifest.lighting.budget_is_measured === false, 'current not measured');
assert(validation.roofs.every((roof) => roof.bearing_probe_mm3 > 80), 'every roof bears');
assert(validation.roofs.every((roof) => roof.bodies === 1), 'one roof body');
assert(validation.stairs.every((stair) => stair.headroom_sample_mm >= 72), 'stair headroom');
assert(validation.stairs.every((stair) => stair.well_blocked_mm3 === 0), 'stair wells open');
assert(validation.worst_mm3 === 0, 'no rest collision');
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
assert(manifest.bom.find((row) => row.part === 'qa5_coupon_panel_v5').qty === 1, 'coupon panel');
assert(manifest.bom.find((row) => row.part === 'qa5_retainer_v5').print_qty > 4, 'retainer print count');
assert(read(here + 'archive/v1.0.0/README.md').includes('78 mm'), 'v1 defect note');
assert(read(here + 'archive/v3.0.0/README.md').includes('v3.0.0'), 'v3 archive note');
assert(read(here + 'archive/v4.0.0/README.md').includes('narrow stack'), 'v4 archive note');
assert(read(here + 'index.html').includes('approved-direction.jpg'), 'concept image on the page');
assert(!manifest.instances.some((instance) => instance.role === 'facade'), 'no room facades');
const rear = manifest.instances.find((instance) => instance.id === 'rear');
assert(rear && rear.motion && rear.motion.pull && rear.motion.pull[1] > 0 && !rear.motion.slide && !rear.motion.lift, 'rear pulls straight off');
assert(validation.rear_fit && validation.rear_fit.gap_y_mm === 0.45, 'rear seats at 0.45 mm');
assert(validation.rear_fit.intersection_mm3 === 0, 'rear does not occupy the jambs');
assert(validation.rear_fit.panel_bbox_mm[0] < 310 && validation.rear_fit.panel_bbox_mm[2] < 315, 'rear fits the bed');

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
assert(page.includes('data-mode="rear"'), 'rear control');
assert(page.includes('data-mode="front"'), 'front control');
assert(page.includes('data-mode="detail"'), 'detail control');
assert(page.includes('data-mode="closed"'), 'closed control');
assert(page.includes('data-mode="open"'), 'open control');
assert(page.includes('data-mode="plan"'), 'plan control');
assert(page.includes('data-mode="lighting"'), 'lighting control');
assert(page.includes('data-mode="stairs"'), 'stairs control');
assert(page.includes('data-mode="attic"'), 'attic control');
assert(page.includes('approved-direction.jpg'), 'concept image');
assert(page.includes('data-mode="explode"'), 'explode control');
assert(page.includes('data-mode="attachment"'), 'attachment control');
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
