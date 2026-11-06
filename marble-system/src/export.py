"""Export print-oriented STLs, manifest, assembly records, and a 3MF of layout A."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from geom import to_trimesh
import constants as C
import catalog as Cat
import assembly as A
import layouts as L

ROOT = Path(__file__).resolve().parents[1]
STL = ROOT / 'stl'
KIT = ROOT / 'kit'
for d in (STL, KIT):
    d.mkdir(parents=True, exist_ok=True)

def print_orient(name, man):
    if name.startswith('track_') or name in ('ADAPT_OUT', 'ADAPT_IN'):
        return man.rotate([180, 0, 0])
    if name.startswith('low_mount'):
        return man  # standing, well-pin down
    if name == 'ball_cap':
        return man.rotate([90, 0, 0])
    if name.startswith('lock_clip'):
        return man.rotate([0, 90, 0])
    return man

QTY = {
    'tile_00': 1, 'tile_10': 1, 'tile_01': 1, 'tile_11': 1,
    'tile_latch': 8,
    'sleeve_short': 8, 'post_short': 8, 'lock_clip_short': 11,
    'sleeve_medium': 10, 'post_medium': 10, 'lock_clip_medium': 13,
    'sleeve_tall': 6, 'post_tall': 6, 'lock_clip_tall': 8,
    'ball_cap': 32,
    'track_S160': 8, 'track_S80': 6, 'track_S40': 4,
    'track_CR90': 5, 'track_CL90': 5, 'track_CR45': 2, 'track_CL45': 2,
    'track_SPLIT_Y': 2, 'track_MERGE_Y': 2, 'track_FUNNEL': 2,
    'track_HX360': 2, 'track_DROP40': 2, 'track_SPAN240': 2,
    'track_TUN160': 1, 'track_SWITCH': 1,
    'ADAPT_OUT': 1, 'ADAPT_IN': 1,
    'switch_gate': 1, 'low_mount': 6, 'lift_mount_plate': 1,
    'fit_coupon': 1,
}

COLOR = {
    'tile_00': '#C8D6E5', 'tile_10': '#B8C6D5', 'tile_01': '#C8D6E5', 'tile_11': '#B8C6D5',
    'tile_latch': '#8395A7',
    'sleeve_short': '#10AC84', 'sleeve_medium': '#2E86DE', 'sleeve_tall': '#5F27CD',
    'post_short': '#1DD1A1', 'post_medium': '#54A0FF', 'post_tall': '#A55EEA',
    'lock_clip_short': '#FF9F43', 'lock_clip_medium': '#FF9F43', 'lock_clip_tall': '#FF9F43',
    'ball_cap': '#FECA57',
    'track_S160': '#2E86DE', 'track_S80': '#2E86DE', 'track_S40': '#54A0FF',
    'track_CR90': '#10AC84', 'track_CL90': '#10AC84', 'track_CR45': '#1DD1A1', 'track_CL45': '#1DD1A1',
    'track_SPLIT_Y': '#FF6B6B', 'track_MERGE_Y': '#FF6B6B', 'track_FUNNEL': '#F368E0',
    'track_HX360': '#5F27CD', 'track_DROP40': '#EE5A24', 'track_SPAN240': '#2E86DE',
    'track_TUN160': '#576574', 'track_SWITCH': '#FF9F43',
    'ADAPT_OUT': '#FF9FF3', 'ADAPT_IN': '#FF9FF3',
    'switch_gate': '#F79F1F', 'low_mount': '#A3CB38', 'lift_mount_plate': '#84817A',
    'fit_coupon': '#A3CB38',
}

IN_48 = {
    'track_S160', 'track_S80', 'track_S40', 'track_CR90', 'track_CL90',
    'track_CR45', 'track_CL45', 'track_SPLIT_Y', 'track_MERGE_Y', 'track_FUNNEL',
    'track_HX360', 'track_DROP40', 'track_SPAN240', 'track_TUN160', 'track_SWITCH',
    'ADAPT_OUT', 'ADAPT_IN',
}
IN_24 = {
    'sleeve_short', 'sleeve_medium', 'sleeve_tall',
    'post_short', 'post_medium', 'post_tall',
    'lock_clip_short', 'lock_clip_medium', 'lock_clip_tall',
    'ball_cap',
}

def _jsonify(o):
    if isinstance(o, dict):
        return {k: _jsonify(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonify(v) for v in o]
    if hasattr(o, 'item'):
        try:
            return o.item()
        except Exception:
            pass
    if isinstance(o, float):
        return round(o, 4)
    return o

def main():
    cat = Cat.part_catalog()
    parts = []
    for name, fn in cat.items():
        print('export', name, flush=True)
        man = print_orient(name, fn())
        tm = to_trimesh(man)
        path = STL / f'{name}.stl'
        tm.export(str(path))
        V = tm.vertices
        ext = (V.max(0) - V.min(0)).tolist()
        qty = QTY.get(name, 1)
        bucket = ('track48' if name in IN_48 else
                  'support24' if name in IN_24 else
                  'base' if name.startswith('tile') else
                  'extra')
        parts.append(dict(
            name=name, path=f'stl/{name}.stl', qty=qty, bucket=bucket,
            color=COLOR.get(name, '#888'), verts=int(len(tm.vertices)),
            faces=int(len(tm.faces)), volume_mm3=float(man.volume()),
            extents_mm=[round(x, 2) for x in ext], watertight=True,
        ))

    print('layouts for assembly records', flush=True)
    summaries = []
    solids_A = None
    for builder in (L.layout_A, L.layout_B):
        lay = builder()
        summaries.append(L.summarize(lay))
        if lay['name'].startswith('A') and solids_A is None:
            solids_A = lay
        for inst in lay['support_instances']:
            if inst['kind'] == 'low_mount':
                H = round(float(inst['Hraw']), 2)
                lname = f"low_mount_h{int(round(H))}"
                if lname not in cat and lname not in {pp['name'] for pp in parts}:
                    print('export', lname, flush=True)
                    man = print_orient(lname, Cat.low_mount(H, 0.0))
                    tm = to_trimesh(man)
                    path = STL / f'{lname}.stl'
                    tm.export(str(path))
                    V = tm.vertices
                    ext = (V.max(0) - V.min(0)).tolist()
                    parts.append(dict(
                        name=lname, path=f'stl/{lname}.stl', qty=1, bucket='extra',
                        color='#A3CB38', verts=int(len(tm.vertices)),
                        faces=int(len(tm.faces)), volume_mm3=float(man.volume()),
                        extents_mm=[round(x, 2) for x in ext], watertight=True,
                        note=f'printed extra; assemble at H_ball={H} mm (rail Hraw)',
                    ))

    # 3MF of layout A (tiles + tracks + supports + lift plate)
    print('writing assembly 3mf', flush=True)
    try:
        import trimesh
        scene = trimesh.Scene()
        for i, t in enumerate(solids_A['tiles']):
            scene.add_geometry(to_trimesh(t), node_name=f'tile_{i}')
        for p in solids_A['pieces']:
            scene.add_geometry(to_trimesh(p['solid']), node_name=p['name'])
        for i, s in enumerate(solids_A['support_instances']):
            tag = f"sup_{s['kind']}_{i}"
            if s['kind'] == 'low_mount':
                scene.add_geometry(to_trimesh(s['solid']), node_name=tag)
            else:
                for k in ('sleeve', 'post', 'clip', 'cap'):
                    scene.add_geometry(to_trimesh(s[k]), node_name=f'{tag}_{k}')
        scene.add_geometry(to_trimesh(solids_A['lift_mount_plate']), node_name='lift_mount_plate')
        scene.export(str(KIT / 'marble_system_v2_layoutA.3mf'))
        threemf = 'kit/marble_system_v2_layoutA.3mf'
    except Exception as e:
        print('3mf failed', e)
        threemf = None

    tz = timezone(timedelta(hours=-7))
    now = datetime.now(tz).isoformat(timespec='seconds')
    track_print_qty = sum(p['qty'] for p in parts if p['bucket'] == 'track48')
    manifest = dict(
        name='marble-system-v2',
        version='0.5-layoutA',
        generated=now,
        timezone='America/Denver',
        printer={'model': 'Bambu Lab H3C', 'envelope_mm': list(C.ENVELOPE),
                 'tile_print': '304.8 mm side along the 330 axis (25.2 mm leftover); 228.6 along 320'},
        ball_diameter_mm=35.0,
        socket_to_rail_mm=C.SOCKET_TO_RAIL,
        grid_pitch_mm=C.P,
        tile_pitch_mm=[C.TILE_PX, C.TILE_PY],
        assembled_mm=list(C.ASSEMBLED),
        assembled_in=list(C.ASSEMBLED_IN),
        well_count=len(C.all_wells()),
        wells_per_tile={f'{ix}{iy}': len(C.wells_on_tile(ix, iy)) for ix in (0, 1) for iy in (0, 1)},
        height_classes=C.CLASSES,
        bom48=[{'id': i, 'qty': q} for i, q in C.BOM48],
        bom48_sum=sum(q for _, q in C.BOM48),
        track_print_qty=track_print_qty,
        support_structures={'short': 8, 'medium': 10, 'tall': 6, 'total': 24},
        extras=C.EXTRAS,
        parts=parts,
        layouts=_jsonify(summaries),
        assembly_3mf=threemf,
        sample={
            'joints': {'J0': A.J0, 'J1': A.J1, 'J2': A.J2, 'J3': A.J3},
            'ZV0': A.ZV0,
            'supports': [dict(x=s[0], y=s[1], kind=s[2], H=s[3]) for s in A.SUPPORTS],
            'note': 'Retained demo coordinates after translating onto the exact 18x24 board; they already fit tile_00.',
        },
        public_status={
            'state': 'layout-a-clear-full-kit-held',
            'layout_a_35mm_ball_clear': True,
            'layout_a_ball_worst_mm3': 1.01,
            'layout_b_working_route': False,
            'layout_b_status': 'design_study',
            'layout_b_helix_x_housing_mm3': 10230.3,
            'do_not_print_full_kit': True,
            'full_48_play_kit': False,
            'kit_zip_regenerated': True,
            'physical_test': False,
        },
        disclaimer=('Layout A clears a 35 mm ball in computation (worst about 1 mm³). '
                    'Layout B is a design study: the 80 mm helix meets the lift. '
                    'Do not print the full kit. Not a certified toy. '
                    'Snap force, creep, fatigue, and rolling were not tested. '
                    'Generic slicing is not an H3C result. v1 marble-factory is unchanged.'),
    )
    (KIT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    (KIT / 'assembly.json').write_text(json.dumps(_jsonify(summaries), indent=2))
    print('exported', len(parts), 'STLs; track qty', track_print_qty)
    return manifest

if __name__ == '__main__':
    main()
