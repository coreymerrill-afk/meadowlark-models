"""3D assembly previews and a technical support/height diagram. No browser."""
import math
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import matplotlib.patches as patches
import constants as C
import layouts as L
import assembly as A

OUT = Path('/workspace/marble-system-v2/renders')
OUT.mkdir(parents=True, exist_ok=True)


def _straight(origin, hdg, z0, L, drop, n=16):
    ca, sa = math.cos(math.radians(hdg)), math.sin(math.radians(hdg))
    pts = []
    for i in range(n):
        s = L * i / (n - 1)
        pts.append((origin[0] + ca * s, origin[1] + sa * s, z0 - drop * s / L))
    return pts


def _corner(origin, hdg, z0, drop, turn='R', n=24):
    s = -1 if turn == 'R' else 1
    pts = []
    for i in range(n):
        a = math.radians(90 * i / (n - 1))
        # local (R sin a, s R (1-cos a)) then rotate by hdg
        lx, ly = C.RC90 * math.sin(a), s * C.RC90 * (1 - math.cos(a))
        ca, sa = math.cos(math.radians(hdg)), math.sin(math.radians(hdg))
        x = origin[0] + ca * lx - sa * ly
        y = origin[1] + sa * lx + ca * ly
        pts.append((x, y, z0 - drop * i / (n - 1)))
    return pts


def _helix(origin, hdg, z0, drop=80.0, R=90.0, stub=40.0, turn='R', n=72):
    pts = []
    ca, sa = math.cos(math.radians(hdg)), math.sin(math.radians(hdg))
    for i in range(n):
        a = 2 * math.pi * i / (n - 1)
        lx, ly = R * math.sin(a), R * (1 - math.cos(a))
        if turn == 'R':
            ly = -ly
        x = origin[0] + ca * lx - sa * ly
        y = origin[1] + sa * lx + ca * ly
        pts.append((x, y, z0 - drop * i / (n - 1)))
    # exit stub along final heading (= start heading after 360)
    for k in range(1, 5):
        s = stub * k / 4
        pts.append((origin[0] + ca * s, origin[1] + sa * s, z0 - drop))
    return pts


def paths_for(lay):
    out = []
    for p in lay['pieces']:
        kind, o, h, z = p['kind'], p.get('origin'), p.get('hdg'), p.get('z0', 0)
        if kind == 'S160':
            out.append((kind, _straight(o, h, z, 160, p['drop'])))
        elif kind == 'S80':
            out.append((kind, _straight(o, h, z, 80, p['drop'])))
        elif kind == 'S40':
            out.append((kind, _straight(o, h, z, 40, p['drop'])))
        elif kind == 'CR90':
            out.append((kind, _corner(o, h, z, p['drop'], 'R')))
        elif kind == 'CL90':
            out.append((kind, _corner(o, h, z, p['drop'], 'L')))
        elif kind == 'HX360R':
            out.append((kind, _helix(o, h, z, p['drop'], turn='R')))
        elif kind == 'ADAPT_IN':
            out.append((kind, _straight(o, h, z, C.V1_INLET_L, p.get('drop', 15))))
        elif kind == 'ADAPT_OUT':
            out.append((kind, _straight(o, h, z, 26, 1.2)))
    return out


COL = {
    'S160': '#1e90ff', 'S80': '#4aa3ff', 'S40': '#7ec8ff',
    'CR90': '#10ac84', 'CL90': '#1dd1a1', 'HX360R': '#5f27cd',
    'ADAPT_IN': '#ff9ff3', 'ADAPT_OUT': '#f368e0',
}


def render_layout_3d(lay, path, title):
    fig = plt.figure(figsize=(11.2, 8.4), dpi=130)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_title(title, fontsize=11, pad=8)
    # tiles
    for ix in (0, 1):
        for iy in (0, 1):
            x0, y0 = ix * C.TILE_PX, iy * C.TILE_PY
            xs = [x0, x0 + C.TILE_PX, x0 + C.TILE_PX, x0]
            ys = [y0, y0, y0 + C.TILE_PY, y0 + C.TILE_PY]
            zs = [0, 0, 0, 0]
            verts = [list(zip(xs, ys, zs))]
            ax.add_collection3d(Poly3DCollection(verts, facecolor='#dfe6e9',
                                                 edgecolor='#636e72', alpha=0.35, linewidths=0.6))
    # wells
    wells = np.array(C.all_wells())
    ax.scatter(wells[:, 0], wells[:, 1], np.zeros(len(wells)),
               s=4, c='#fdcb6e', alpha=0.35, depthshade=False)
    # tracks
    for kind, pts in paths_for(lay):
        P = np.array(pts)
        ax.plot(P[:, 0], P[:, 1], P[:, 2] + C.VH, color=COL.get(kind, '#333'),
                lw=3.4, solid_capstyle='round', label=kind)
    # supports
    for s in lay['support_instances']:
        x, y = s['well']
        if s['kind'] == 'low_mount':
            ax.plot([x, x], [y, y], [0, 52], color='#a3cb38', lw=3)
            ax.scatter([x], [y], [52], c='#a3cb38', s=18, depthshade=False)
        else:
            ax.plot([x, x], [y, y], [0, s['H']], color='#2d3436', lw=3.5)
            ax.scatter([x], [y], [s['H']], c={'short': '#00b894', 'medium': '#0984e3',
                                              'tall': '#6c5ce7'}[s['kind']],
                       s=28, edgecolors='k', depthshade=False)
    # lift
    axl, ayl = lay['lift']['axle']
    th = np.linspace(0, 2 * math.pi, 60)
    ax.plot(axl + 105 * np.cos(th), ayl + 105 * np.sin(th), np.full_like(th, 136),
            color='#2d3436', lw=1.2, ls='--')
    ax.plot([axl], [ayl], [136], 'o', color='#2d3436', ms=5)
    ax.text(axl, ayl, 155, 'v1 lift axle', fontsize=7)
    for px, py in lay['lift']['pegs']:
        ax.scatter([px], [py], [8], c='#84817a', s=22, depthshade=False)
    # legend unique
    handles, labels = ax.get_legend_handles_labels()
    uniq = dict(zip(labels, handles))
    ax.legend(uniq.values(), uniq.keys(), loc='upper left', fontsize=7)
    ax.set_xlabel('X mm'); ax.set_ylabel('Y mm'); ax.set_zlabel('Z mm')
    ax.set_xlim(0, C.ASSEMBLED[0]); ax.set_ylim(0, C.ASSEMBLED[1]); ax.set_zlim(-5, 230)
    try:
        ax.set_box_aspect((C.ASSEMBLED[0], C.ASSEMBLED[1], 230))
    except Exception:
        pass
    ax.view_init(elev=28, azim=-62)
    fig.tight_layout()
    fig.savefig(path, facecolor='white')
    plt.close(fig)


def render_board_plan():
    fig, ax = plt.subplots(figsize=(10.6, 7.6), dpi=130)
    ax.set_aspect('equal')
    ax.set_title('18×24 in board — 117 wells on a global 40 mm lattice\n'
                 '(seam / edge / joiner wells omitted; four distinct tile patterns)', fontsize=10)
    colors = {(0, 0): '#dfe6e9', (1, 0): '#c8d6e5', (0, 1): '#b2bec3', (1, 1): '#dfe6e9'}
    for ix in (0, 1):
        for iy in (0, 1):
            x0, y0 = ix * C.TILE_PX, iy * C.TILE_PY
            ax.add_patch(patches.Rectangle((x0, y0), C.TILE_PX, C.TILE_PY,
                                           facecolor=colors[(ix, iy)], edgecolor='#2d3436', lw=1.4))
            n = len(C.wells_on_tile(ix, iy))
            ax.text(x0 + C.TILE_PX / 2, y0 + C.TILE_PY / 2, f'tile_{ix}{iy}\n{n} wells',
                    ha='center', va='center', fontsize=8, color='#636e72', alpha=0.8)
    ax.axvline(C.SEAM_X, color='#e17055', ls='--', lw=1, label='tile seam')
    ax.axhline(C.SEAM_Y, color='#e17055', ls='--', lw=1)
    for x, y in C.all_wells():
        ax.add_patch(patches.Rectangle((x - 9, y - 9), 18, 18, facecolor='#fdcb6e',
                                       edgecolor='#d35400', lw=0.25, alpha=0.7))
    ax.set_xlim(-15, C.ASSEMBLED[0] + 15)
    ax.set_ylim(-15, C.ASSEMBLED[1] + 15)
    ax.set_xlabel('X mm (24 in = 609.6)'); ax.set_ylabel('Y mm (18 in = 457.2)')
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / '01_board_wells.png', facecolor='white')
    plt.close(fig)


def render_height_windows():
    fig, ax = plt.subplots(figsize=(10.2, 5.6), dpi=130)
    ax.set_title('Support height classes (honest matched sleeve/post pairs)\n'
                 'No single post does 50–230 mm; nothing protrudes below the tile.', fontsize=10)
    colors = {'short': '#00b894', 'medium': '#0984e3', 'tall': '#6c5ce7'}
    y = 0
    for kind, spec in C.CLASSES.items():
        ax.add_patch(patches.Rectangle((spec['Hmin'], y + 0.15), spec['Hmax'] - spec['Hmin'], 0.7,
                                       facecolor=colors[kind], alpha=0.35, edgecolor=colors[kind], lw=2))
        ax.text((spec['Hmin'] + spec['Hmax']) / 2, y + 0.5,
                f"{kind}  H={spec['Hmin']:.0f}–{spec['Hmax']:.0f}   "
                f"Ls={spec['Ls']:.0f}  Lpost={spec['Lpost']:.0f}  "
                f"Omin={spec['Omin']:.0f}  qty={spec['qty']}",
                ha='center', va='center', fontsize=9)
        ax.plot([spec['Hmin'], spec['Hmin']], [y + 0.1, y + 0.9], color=colors[kind], lw=2)
        ax.plot([spec['Hmax'], spec['Hmax']], [y + 0.1, y + 0.9], color=colors[kind], lw=2)
        y += 1
    ax.axvline(70, color='#636e72', ls=':', label='Hmin 70 (rolling ≈ 106 with socket_to_rail)')
    ax.axvline(230, color='#636e72', ls=':')
    ax.set_xlim(50, 250); ax.set_ylim(-0.2, 3.2)
    ax.set_xlabel('support H = V-vertex − 11 mm  (= rail rolling height − 35.75 mm)')
    ax.set_yticks([])
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / '02_height_windows.png', facecolor='white')
    plt.close(fig)


def render_support_diagram():
    """Technical section through a medium support: tile, sleeve, post, clip, cap, track, ball."""
    fig, ax = plt.subplots(figsize=(9.2, 8.4), dpi=140)
    ax.set_title('Medium support at H = 130 mm (technical section)\n'
                 '5 mm rack, captive pawl above the tile, keyed ball, V-track', fontsize=10)
    # tile
    ax.add_patch(patches.Rectangle((-40, -12), 80, 12, facecolor='#b2bec3', edgecolor='k'))
    ax.add_patch(patches.Rectangle((-11.2, -10), 22.4, 10, facecolor='#dfe6e9', edgecolor='#636e72'))
    # sleeve
    ax.add_patch(patches.Rectangle((-11, -9), 22, 80 + 9, facecolor='#74b9ff', edgecolor='#0984e3', alpha=0.55))
    ax.add_patch(patches.Rectangle((-8.2, 0), 16.4, 80, facecolor='white', edgecolor='#0984e3', ls='--'))
    ax.add_patch(patches.Rectangle((-15, 0), 30, 3.5, facecolor='#74b9ff', edgecolor='#0984e3'))
    # post (z_bottom = 130-100 = 30)
    ax.add_patch(patches.Rectangle((-8, 30), 16, 90, facecolor='#a29bfe', edgecolor='#6c5ce7'))
    # cap + ball
    ball = plt.Circle((0, 30 + 90 + 10), 8, facecolor='#ffeaa7', edgecolor='#d35400')
    ax.add_patch(ball)
    # V track (rolling centre = H + SOCKET_TO_RAIL = 130+35.75 = 165.75)
    # V vertex = H + 11 = 141
    V = 141
    ax.plot([-32, 0, 32], [V + 18, V, V + 18], color='#0984e3', lw=2)
    ax.plot([-32, 32], [V + 18, V + 18], color='#0984e3', lw=2)
    marble = plt.Circle((0, V + C.VH), 17.5, facecolor='#fab1a0', edgecolor='#d63031', alpha=0.85)
    ax.add_patch(marble)
    ax.annotate('', xy=(22, 130), xytext=(22, 0),
                arrowprops=dict(arrowstyle='<->', color='#2d3436'))
    ax.text(28, 65, 'H = 130', fontsize=8)
    ax.annotate('', xy=(-28, V + C.VH), xytext=(-28, 130),
                arrowprops=dict(arrowstyle='<->', color='#d63031'))
    ax.text(-50, (130 + V + C.VH) / 2, 'socket_to_rail\n35.75 mm', fontsize=7, color='#d63031')
    ax.plot([-18, 18], [68, 68], color='#e17055', lw=4, solid_capstyle='butt')
    ax.text(24, 78, 'lock clip / pawl window\n(unload-to-release)', fontsize=7, va='bottom')
    ax.set_xlim(-70, 70); ax.set_ylim(-20, 200)
    ax.set_aspect('equal')
    ax.set_xlabel('mm'); ax.set_ylabel('Z mm above tile top')
    ax.grid(True, ls=':', alpha=0.35)
    fig.tight_layout()
    fig.savefig(OUT / '03_support_section.png', facecolor='white')
    plt.close(fig)


def render_sample_plan():
    fig, ax = plt.subplots(figsize=(8.4, 6.6), dpi=130)
    ax.set_aspect('equal')
    ax.set_title('Retained interface sample on tile_00 (same XY as CAD 0.2)', fontsize=10)
    ax.add_patch(patches.Rectangle((0, 0), C.TILE_PX, C.TILE_PY,
                                   facecolor='#dfe6e9', edgecolor='#2d3436', lw=1.2))
    for x, y in C.wells_on_tile(0, 0):
        ax.add_patch(patches.Rectangle((x - 9, y - 9), 18, 18, facecolor='#fdcb6e',
                                       edgecolor='#d35400', lw=0.3, alpha=0.55))
    ax.plot([A.J0[0], A.J1[0]], [A.J0[1], A.J1[1]], color='#0984e3', lw=6, solid_capstyle='round')
    tt = np.linspace(0, math.pi / 2, 40)
    ax.plot(A.J1[0] + 80 * np.sin(tt), A.J1[1] + 80 * (1 - np.cos(tt)),
            color='#00b894', lw=6, solid_capstyle='round')
    ax.plot([A.J2[0], A.J3[0]], [A.J2[1], A.J3[1]], color='#0984e3', lw=6, solid_capstyle='round')
    colors = {'medium': '#0984e3', 'short': '#00b894', 'tall': '#6c5ce7'}
    for x, y, kind, H in A.SUPPORTS:
        ax.plot(x, y, 'o', ms=14, color=colors[kind], markeredgecolor='k')
        ax.text(x, y - 14, f'{kind}\nH={H:.0f}', ha='center', va='top', fontsize=7)
    ax.set_xlim(-15, C.TILE_PX + 15); ax.set_ylim(-20, C.TILE_PY + 20)
    ax.set_xlabel('X mm'); ax.set_ylabel('Y mm')
    fig.tight_layout()
    fig.savefig(OUT / '04_sample_tile00.png', facecolor='white')
    plt.close(fig)


def main():
    print('render board / heights / section / sample', flush=True)
    render_board_plan()
    render_height_windows()
    render_support_diagram()
    render_sample_plan()
    print('layout A 3d', flush=True)
    A_lay = L.layout_A()
    render_layout_3d(A_lay, OUT / '05_layoutA_3d.png',
                     'Layout A — simple downhill loop on the 18×24 board  (lift at 460, 100)')
    print('layout B 3d', flush=True)
    B_lay = L.layout_B()
    render_layout_3d(B_lay, OUT / '06_layoutB_3d.png',
                     'Layout B — descending helix (244 mm / 80 mm drop) then return  (lift at 420, 100)')
    print('renders written')


if __name__ == '__main__':
    main()
