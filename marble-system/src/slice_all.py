"""Slice v2 interface STLs with official PrusaSlicer 2.7.4 (generic 0.4/0.20 PLA)."""
import os, re, subprocess, json
from pathlib import Path

ROOT = Path('/workspace/marble-system-v2')
STL = ROOT / 'stl'
OUT = ROOT / 'slice'
GCODE = OUT / 'gcode'
LOGS = OUT / 'logs'
SET = Path('/workspace/observatory-slice-validation/settings')
RUNNER = Path('/workspace/tools/prusaslicer/run-prusa-slicer')
for d in (GCODE, LOGS):
    d.mkdir(parents=True, exist_ok=True)

BRIM = {'post_short', 'post_medium', 'post_tall', 'ball_cap', 'lock_clip_short',
        'lock_clip_medium', 'lock_clip_tall', 'tile_latch', 'low_mount',
        'switch_gate', 'fit_coupon'}
SUPPORTS = {'track_HX360', 'track_DROP40', 'track_SPLIT_Y', 'track_MERGE_Y',
            'track_SWITCH', 'track_FUNNEL', 'ADAPT_IN', 'ADAPT_OUT'}

def settings_for(name):
    if name in SUPPORTS or name.startswith('low_mount'):
        return SET / 'generic_0.4_pla_0.20_supports.ini'
    if name in BRIM:
        return SET / 'generic_0.4_pla_0.20_brim.ini'
    return SET / 'generic_0.4_pla_0.20.ini'

def parse_gcode(path):
    text = path.read_text(errors='replace')
    filament = None
    m = re.search(r';\s*filament used \[mm\]\s*=\s*([0-9.]+)', text)
    if m:
        filament = float(m[1])
    e_moves = len(re.findall(r'^G1 .*E[-0-9.]', text, re.M))
    zs = [float(z) for z in re.findall(r'^G1 .*Z([0-9.]+)', text, re.M)]
    zrange = (min(zs), max(zs)) if zs else (None, None)
    first_layer_empty = 'no extrusions in the first layer' in text.lower()
    return dict(filament_mm=filament, extrusion_moves=e_moves, z_range=zrange,
                bytes=path.stat().st_size, first_layer_empty=first_layer_empty)

def run_one(stl: Path):
    name = stl.stem
    ini = settings_for(name)
    gcode = GCODE / f'{name}.gcode'
    log = LOGS / f'{name}.log'
    cmd = [str(RUNNER), '--load', str(ini), '--export-gcode', '--output', str(gcode), str(stl)]
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log.write_text(p.stdout)
    ok = p.returncode == 0 and gcode.exists() and gcode.stat().st_size > 100
    info = dict(part=name, settings=ini.name, exit=p.returncode, ok=ok)
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
        warn.append('very few extrusion moves'); info['ok'] = False
    if g['first_layer_empty']:
        warn.append('empty first layer in gcode'); info['ok'] = False
    info['warn'] = warn
    return info

def main():
    rows = []
    for stl in sorted(STL.glob('*.stl')):
        print('slice', stl.name, flush=True)
        rows.append(run_one(stl))
    (OUT / 'slice_report.json').write_text(json.dumps(rows, indent=2))
    lines = ['# v2 full-48 slice report', '',
             'Official PrusaSlicer 2.7.4, generic 0.4 mm / 0.20 mm PLA. **Not** an official H3C profile. Re-slice in Bambu Studio before printing.',
             '',
             f'- Unique STLs: {len(rows)}',
             f'- PASS: {sum(1 for r in rows if r.get("ok"))}/{len(rows)}',
             '',
             '| Part | Settings | Filament mm | Moves | Verdict | Warnings |',
             '|------|----------|-------------|------:|---------|----------|']
    for r in rows:
        lines.append(f"| `{r['part']}` | `{r.get('settings','')}` | {r.get('filament_mm')} | {r.get('extrusion_moves')} | {'PASS' if r.get('ok') else 'FAIL'} | {', '.join(r.get('warn') or []) or '—'} |")
    (OUT / 'SLICE_REPORT.md').write_text('\n'.join(lines))
    print('DONE', len(rows), 'fails', sum(1 for r in rows if not r.get('ok')))

if __name__ == '__main__':
    main()
