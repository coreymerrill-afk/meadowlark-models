"""Slice every unique STL with official PrusaSlicer 2.7.4 (generic 0.4/0.20 PLA)."""
import os, re, subprocess, csv, json
from pathlib import Path

ROOT = Path('/workspace/marble-factory')
STL = ROOT / 'stl'
OUT = ROOT / 'slice'
GCODE = OUT / 'gcode'
LOGS = OUT / 'logs'
SET = Path('/workspace/observatory-slice-validation/settings')
RUNNER = Path('/workspace/tools/prusaslicer/run-prusa-slicer')
for d in (GCODE, LOGS):
    d.mkdir(parents=True, exist_ok=True)

SUPPORTS = {'ball_35'}
# brim: tall stands, small footprints, axle, clip, rotor
BRIM_PREFIX = ('stand_',)
BRIM = {'spinner_rotor', 'lift_axle', 'lift_clip', 'ball_35'}


def settings_for(name):
    if name in SUPPORTS:
        return SET / 'generic_0.4_pla_0.20_supports.ini'
    if name in BRIM or name.startswith(BRIM_PREFIX):
        return SET / 'generic_0.4_pla_0.20_brim.ini'
    return SET / 'generic_0.4_pla_0.20.ini'


def parse_gcode(path):
    text = path.read_text(errors='replace')
    filament = None
    m = re.search(r';\s*filament used \[mm\]\s*=\s*([0-9.]+)', text)
    if m:
        filament = float(m.group(1))
    support = bool(re.search(r';\s*support_material\s*=\s*1', text, re.I) or
                   'Support material: yes' in text or
                   re.search(r';TYPE:Support', text))
    if 'SUPPORT' in text.upper() and re.search(r';TYPE:Support', text):
        support = True
    # extrusion moves: G1 with E increase
    e_moves = len(re.findall(r'^G1 .*E[-0-9.]', text, re.M))
    zs = [float(z) for z in re.findall(r'^G1 .*Z([0-9.]+)', text, re.M)]
    zrange = (min(zs), max(zs)) if zs else (None, None)
    first_layer_empty = 'no extrusions in the first layer' in text.lower()
    # also inspect layer 0 for extrusion
    return dict(filament_mm=filament, extrusion_moves=e_moves, z_range=zrange,
                support_paths=support, bytes=path.stat().st_size,
                first_layer_empty=first_layer_empty)


def run_one(stl: Path):
    name = stl.stem
    ini = settings_for(name)
    gcode = GCODE / f'{name}.gcode'
    log = LOGS / f'{name}.log'
    cmd = [str(RUNNER), '--load', str(ini), '--export-gcode', '--output', str(gcode), str(stl)]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log.write_text(p.stdout)
    ok = p.returncode == 0 and gcode.exists() and gcode.stat().st_size > 100
    info = dict(part=name, settings=ini.name, exit=p.returncode, ok=ok,
                log=str(log), gcode=str(gcode) if gcode.exists() else None)
    warn = []
    if 'no extrusions in the first layer' in p.stdout.lower():
        warn.append('empty first layer')
    if 'floating' in p.stdout.lower():
        warn.append('floating islands/bridges mentioned')
    if not ok:
        warn.append('slice failed or empty gcode')
        info['warn'] = warn
        return info
    g = parse_gcode(gcode)
    info.update(g)
    if g['extrusion_moves'] < 10:
        warn.append('very few extrusion moves')
        info['ok'] = False
    if g['first_layer_empty']:
        warn.append('empty first layer in gcode')
        info['ok'] = False
    info['warn'] = warn
    return info


if __name__ == '__main__':
    from concurrent.futures import ProcessPoolExecutor, as_completed
    stls = sorted(STL.glob('*.stl'))
    print(f'slicing {len(stls)} parts (4-way)', flush=True)
    rows = []
    with ProcessPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(run_one, stl): stl for stl in stls}
        for fut in as_completed(futs):
            info = fut.result()
            rows.append(info)
            print(' ', info['part'], 'OK' if info['ok'] else 'FAIL', info.get('warn'), flush=True)
    rows.sort(key=lambda r: r['part'])
    (OUT / 'slice_report.json').write_text(json.dumps(rows, indent=2))
    fails = [r for r in rows if not r['ok']]
    print('DONE', len(rows), 'fails', len(fails))
    for f in fails:
        print(' FAIL', f['part'], f.get('warn'), 'exit', f.get('exit'))
