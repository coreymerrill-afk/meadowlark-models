"""Build scenes.json: print-STL to board transforms for layouts A and B, plus the v1 lift."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
MAN = json.loads((ROOT / 'kit/manifest.json').read_text())
ASM = json.loads((ROOT / 'kit/assembly.json').read_text())
V1 = json.loads((REPO / 'marble-factory/assembly.json').read_text())

CLASSES = MAN['height_classes']
LPOST = {k: v['Lpost'] for k, v in CLASSES.items()}
HMIN = {k: v['Hmin'] for k, v in CLASSES.items()}
COLOR = {p['name']: p['color'] for p in MAN['parts']}
COLOR.update({
    'lift_housing_back': '#576574',
    'lift_housing_front': '#48DBFB',
    'lift_wheel_half': '#EE5253',
    'lift_axle': '#F5F6FA',
    'lift_crank': '#FECA57',
    'lift_clip': '#FF9F43',
    'lift_pawl': '#222F3E',
})
ZV0 = 180.96
WF = 0.5
V1_INLET_END = 22.75

LIFT_PARTS = {
    'lift_housing_back', 'lift_housing_front', 'lift_wheel_half',
    'lift_axle', 'lift_crank', 'lift_clip', 'lift_pawl',
}
SPIN = {'lift_wheel_half', 'lift_axle', 'lift_crank'}


def mul(a, b):
    o = [[0, 0, 0, 0] for _ in range(4)]
    for i in range(4):
        for j in range(4):
            o[i][j] = sum(a[i][k] * b[k][j] for k in range(4))
    return o


def eye():
    return [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def trans(x, y, z):
    m = eye()
    m[0][3], m[1][3], m[2][3] = x, y, z
    return m


def rx180():
    return [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]


def rz(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def rx_neg90():
    # Inverse of manifold rotate([90,0,0]): (x,y,z) -> (x, z, -y)
    return [[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]


def ry_neg90():
    # Inverse of manifold rotate([0,90,0]): (x,y,z) -> (-z, y, x)
    return [[0, 0, -1, 0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]


def track_matrix(origin, heading, z0):
    return mul(trans(origin[0], origin[1], z0), mul(rz(heading), rx180()))


def rnd(m):
    return [[round(v, 6) for v in row] for row in m]


def inst(iid, part, matrix, role, **extra):
    row = {
        'id': iid,
        'part': part,
        'color': COLOR.get(part, '#d0d0d0'),
        'role': role,
        'transform': rnd(matrix),
    }
    row.update(extra)
    return row


def chain(seq):
    prev = ZV0
    out = []
    for i, piece in enumerate(seq):
        z0 = ZV0 if i == 0 else prev - WF
        end = z0 - piece['drop']
        piece = dict(piece)
        piece['z0'] = z0
        piece['endV'] = end
        out.append(piece)
        prev = end
    adapt_z = prev - WF
    adapt_drop = adapt_z - V1_INLET_END
    return out, adapt_z, adapt_drop


def layout_pieces(name):
    if name == 'A_simple_loop':
        j0, j11 = (300.0, 100.0), (460.0, 180.0)
        seq = [
            dict(id='S160_1', part='track_S160', origin=(300, 100), hdg=180, drop=20),
            dict(id='CR1', part='track_CR90', origin=(140, 100), hdg=180, drop=15),
            dict(id='S160_2', part='track_S160', origin=(60, 180), hdg=90, drop=20),
            dict(id='CR2', part='track_CR90', origin=(60, 340), hdg=90, drop=15),
            dict(id='S160_3', part='track_S160', origin=(140, 420), hdg=0, drop=20),
            dict(id='S80_1', part='track_S80', origin=(300, 420), hdg=0, drop=10),
            dict(id='CR3', part='track_CR90', origin=(380, 420), hdg=0, drop=15),
            dict(id='S160_4', part='track_S160', origin=(460, 340), hdg=270, drop=20),
        ]
    else:
        j0, j11 = (260.0, 100.0), (420.0, 180.0)
        seq = [
            dict(id='HX1', part='track_HX360', origin=(260, 100), hdg=180, drop=80),
            dict(id='CR1', part='track_CR90', origin=(220, 100), hdg=180, drop=15),
            dict(id='CR2', part='track_CR90', origin=(140, 180), hdg=90, drop=15),
            dict(id='S80_1', part='track_S80', origin=(220, 260), hdg=0, drop=10),
            dict(id='S40_1', part='track_S40', origin=(300, 260), hdg=0, drop=5),
            dict(id='CR3', part='track_CR90', origin=(340, 260), hdg=0, drop=15),
        ]
    seq, adapt_z, adapt_drop = chain(seq)
    pieces = [dict(id='ADAPT_OUT', part='ADAPT_OUT', origin=j0, hdg=180, z0=ZV0)]
    pieces.extend(seq)
    pieces.append(dict(id='ADAPT_IN', part='ADAPT_IN', origin=j11, hdg=270, z0=adapt_z))
    return pieces, adapt_drop


def build(record):
    pieces, adapt_drop = layout_pieces(record['name'])
    axle = record['lift']['axle']
    rows = []
    tiles = [('tile_00', 0, 0), ('tile_10', 1, 0), ('tile_01', 0, 1), ('tile_11', 1, 1)]
    for name, ix, iy in tiles:
        rows.append(inst(name, name, trans(ix * 304.8, iy * 228.6, 0), 'base'))
    for piece in pieces:
        rows.append(inst(
            piece['id'], piece['part'],
            track_matrix(piece['origin'], piece['hdg'], piece['z0']),
            'track',
            adapter=piece['part'].startswith('ADAPT'),
        ))
    for i, post in enumerate(record['posts']):
        kind = post['kind']
        x, y = post['well']
        zb = post['H'] - HMIN[kind]
        hid = 'h' + str(i)
        meta = {'heightId': hid, 'H': post['H'], 'Hmin': HMIN[kind], 'Hmax': CLASSES[kind]['Hmax'], 'kind': kind}
        rows.append(inst(hid + '-sleeve', 'sleeve_' + kind, trans(x, y, 0), 'support', **meta, moves=False))
        rows.append(inst(hid + '-post', 'post_' + kind, trans(x, y, zb), 'support', **meta, moves=True))
        rows.append(inst(hid + '-clip', 'lock_clip_' + kind, mul(trans(x, y, 0), ry_neg90()), 'support', **meta, moves=False))
        rows.append(inst(
            hid + '-cap', 'ball_cap',
            mul(trans(x, y, zb + LPOST[kind]), rx_neg90()),
            'support', **meta, moves=True,
        ))
    for i, low in enumerate(record['low_mounts']):
        x, y = low['well']
        hname = 'low_mount_h' + str(int(round(float(low['Hraw']))))
        rows.append(inst('low-' + str(i), hname, trans(x, y, 0), 'low', Hraw=low['Hraw']))
    rows.append(inst('lift-plate', 'lift_mount_plate', trans(axle[0], axle[1], 0), 'plate'))
    shift = trans(axle[0] - 80.0, axle[1] - 0.0, 0.0)
    for src in V1['instances']:
        if src['part'] not in LIFT_PARTS:
            continue
        rows.append(inst(
            'v1-' + src['part'] + '-' + str(src['index']),
            src['part'],
            mul(shift, src['transform']),
            'lift',
            spin=src['part'] in SPIN,
            v1=True,
        ))
    return {
        'name': record['name'],
        'axle': [axle[0], axle[1], 136.0],
        'installedTracks': record['n_track_pieces'],
        'installedPosts': record['n_posts'],
        'lowMounts': record['n_low_mounts'],
        'adaptInDrop': record['adapt_in_drop'],
        'adaptInSlope': record['adapt_in_slope_deg'],
        'status': record.get('status', 'default'),
        'note': (
            'Layout A is the default route. A 35 mm ball along it stays under 5 mm³ '
            'against the track solids and the v1 housings. Layout B is a design study: '
            'the 80 mm helix meets the lift. Not every catalog piece is installed. '
            'Do not print the full kit.'
            if record.get('status') != 'design_study'
            else 'Design study. The 80 mm helix meets the lift housing. Not a working route.'
        ),
        'instances': rows,
        'computedAdaptDrop': round(adapt_drop, 2),
    }


def main():
    scenes = {rec['name'][0]: build(rec) for rec in ASM}
    (ROOT / 'scenes.json').write_text(json.dumps(scenes, indent=2))
    for key, scene in scenes.items():
        print(key, scene['name'], 'instances', len(scene['instances']), 'adapt', scene['computedAdaptDrop'])


if __name__ == '__main__':
    main()
