"""Overview + assembly-step illustrations (matplotlib, no browser)."""
import math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch, Rectangle, Wedge, Polygon, Arc
import assembly as A
import lift as L
import tracks as T

OUT = Path('/workspace/marble-factory/renders')
OUT.mkdir(exist_ok=True)


def _xy():
    A.build_catalogue()
    return A.XY, A.ZV


def overview():
    XY, ZV = _xy()
    fig, ax = plt.subplots(figsize=(12.5, 8.2), dpi=140)
    # tiles
    for x0 in (-360, -120, 120):
        for y0 in (-40, 200):
            ax.add_patch(Rectangle((x0, y0), 240, 240, fill=True, facecolor='#eef2f5',
                                   edgecolor='#b2bec3', lw=0.8, zorder=0))
    # lift footprint
    ax.add_patch(Circle((80, 0), 122, fill=True, facecolor='#dfe6e9', edgecolor='#576574', lw=1.4, zorder=1, alpha=0.9))
    ax.add_patch(Circle((80, 0), 70, fill=False, edgecolor='#EE5253', lw=1.6, zorder=2))
    # paddles hint
    for k in range(6):
        a = math.radians(30 + 60 * k)
        ax.plot([80 + 70 * math.cos(a), 80 + 105 * math.cos(a)],
                [0 + 70 * math.sin(a) * 0, 0], color='#EE5253', lw=0)  # placeholder
    # better: paddles in XZ projected? This is top view — wheel is in XZ, axis along Y.
    # Show housing rectangle and crank on +y
    ax.add_patch(Rectangle((80 - 108, -26), 108 + 122, 52, fill=False, edgecolor='#576574', lw=1.2, ls='--'))
    ax.plot([80, 80], [29.5, 78], color='#FECA57', lw=6, solid_capstyle='round', zorder=4)
    ax.add_patch(Circle((80, 78), 11, facecolor='#FECA57', edgecolor='#f39c12', zorder=5))
    ax.text(80, 95, 'CRANK', ha='center', va='bottom', fontsize=8, color='#d35400', fontweight='bold')

    colors = {'S160': '#2E86DE', 'S80': '#54A0FF', 'CR': '#10AC84', 'CL': '#01a3a4', 'IN': '#5f27cd'}
    pts, segs = A.default_ball_path()
    for seg in segs:
        col = colors.get(seg['mod'], '#576574')
        xy = [(p[0], p[1]) for p in seg['pts']]
        ax.plot([p[0] for p in xy], [p[1] for p in xy], color=col, lw=7,
                solid_capstyle='round', alpha=0.9, zorder=3)
        mid = xy[len(xy)//2]
        ax.text(mid[0], mid[1], seg['mod'], fontsize=7, color='white', ha='center', va='center',
                fontweight='bold', zorder=8,
                bbox=dict(boxstyle='round,pad=0.15', facecolor=col, edgecolor='none', alpha=0.9))
    for j, (x, y) in XY.items():
        ax.add_patch(Circle((x, y), 9, facecolor='white', edgecolor='#2d3436', lw=0.9, zorder=6))
        ax.text(x, y + 16, f'{j}\n{ZV[j]:.0f}z', ha='center', va='bottom', fontsize=6.5, color='#2d3436', zorder=7)

    ax.annotate('LIFT', xy=(80, 0), xytext=(200, -70),
                fontsize=11, fontweight='bold', color='#576574',
                arrowprops=dict(arrowstyle='->', color='#576574'))
    ax.annotate('continuous downhill return', xy=(-80, 320), xytext=(-80, 430),
                fontsize=9, color='#10AC84', ha='center',
                arrowprops=dict(arrowstyle='->', color='#10AC84'))
    ax.set_aspect('equal')
    ax.set_xlim(-400, 420)
    ax.set_ylim(-130, 470)
    ax.set_title('Hand-Cranked Marble Factory — default playable loop (top view, mm)', fontsize=14, pad=10)
    ax.set_xlabel('X (mm)')
    ax.set_ylabel('Y (mm)')
    ax.text(-390, -120,
            'Unprinted prototype · not a certified toy · 35 mm balls · downhill only after the lift',
            fontsize=8, color='#636e72')
    fig.tight_layout()
    fig.savefig(OUT / '01_overview.png')
    plt.close(fig)


def _panel(ax, title, body, n):
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.add_patch(FancyBboxPatch((0.2, 0.2), 9.6, 9.6, boxstyle='round,pad=0.15,rounding_size=0.3',
                                facecolor='#f8f9fa', edgecolor='#dfe6e9', lw=1.2))
    ax.add_patch(Circle((1.2, 8.7), 0.45, facecolor='#2E86DE', edgecolor='none'))
    ax.text(1.2, 8.7, str(n), ha='center', va='center', color='white', fontsize=11, fontweight='bold')
    ax.text(1.85, 8.7, title, ha='left', va='center', fontsize=11, fontweight='bold', color='#2d3436')
    ax.text(0.6, 7.9, body, ha='left', va='top', fontsize=8.3, color='#2d3436', wrap=True,
            linespacing=1.35)


def assembly_steps():
    fig, axes = plt.subplots(2, 3, figsize=(13.2, 8.4), dpi=140)
    copy = [
        (1, 'Base lattice',
         'Dovetail the six 240 mm tiles\ninto a 3×2 grid (720×480 mm).\nNine sockets on each tile take\nthe stands.'),
        (2, 'Stands + tracks',
         'Drop each named stand into its\nsocket (height is in the filename).\nSnap track modules on top — two\nhalf-disc pegs share one socket.'),
        (3, 'Corners & return',
         'Snap the three right-hand corners\nand the short 80 mm straight so\nthe route turns smoothly — no\nsharp 90° joints. The last long\nstraight aims at the inlet.'),
        (4, 'Lift housing',
         'Seat the back housing (teardrop\npegs) at (0,0) and (160,0).\nSlide the pawl onto its pin.\nPark both wheel halves in the\npocket, hexes aligned.'),
        (5, 'Axle, crank, clip',
         'Fit the front plate on the pins.\nInsert the axle from the BACK,\ntip-first toward the child.\nPress on the crank and snap the\nU-clip into the groove.'),
        (6, 'Inlet & play',
         'Snap the inlet chute onto J11\n(it is the tunnel into the lift).\nLoad up to six 35 mm balls.\nTurn the crank CCW from the\nfront. Print the coupon and\nlift-only test first.'),
    ]
    # simple glyphs
    for ax, (n, title, body) in zip(axes.ravel(), copy):
        _panel(ax, title, body, n)
        # tiny glyph per step
        if n == 1:
            for i in range(3):
                for j in range(2):
                    ax.add_patch(Rectangle((2.2 + i * 1.8, 2.2 + j * 1.8), 1.6, 1.6,
                                           facecolor='#C8D6E5', edgecolor='#8395A7'))
        elif n == 2:
            ax.plot([2.0, 8.0], [3.5, 3.5], color='#2E86DE', lw=8, solid_capstyle='round')
            ax.add_patch(Circle((2.0, 3.5), 0.25, facecolor='#2d3436'))
            ax.add_patch(Circle((8.0, 3.5), 0.25, facecolor='#2d3436'))
            ax.add_patch(Rectangle((4.7, 1.6), 0.6, 1.6, facecolor='#8395A7'))
        elif n == 3:
            ax.add_patch(Rectangle((2.4, 2.8), 3.2, 2.2, facecolor='#F368E0', alpha=0.5))
            ax.add_patch(Rectangle((3.2, 4.4), 1.6, 0.35, facecolor='#FECA57'))
            ax.add_patch(Circle((7.0, 3.6), 0.9, fill=False, edgecolor='#FF6B6B', lw=2))
        elif n == 4:
            ax.add_patch(Circle((5.0, 3.6), 2.0, fill=False, edgecolor='#576574', lw=2))
            for k in range(6):
                a = math.radians(60 * k)
                ax.plot([5 + 0.9 * math.cos(a), 5 + 1.8 * math.cos(a)],
                        [3.6 + 0.9 * math.sin(a), 3.6 + 1.8 * math.sin(a)], color='#EE5253', lw=3)
        elif n == 5:
            ax.add_patch(Rectangle((3.2, 2.4), 0.5, 3.4, facecolor='#F5F6FA', edgecolor='#636e72'))
            ax.plot([3.45, 7.2], [5.2, 5.2], color='#FECA57', lw=5)
            ax.add_patch(Circle((7.2, 5.2), 0.45, facecolor='#FECA57'))
        else:
            ax.add_patch(Circle((3.3, 3.5), 0.55, facecolor='#FF4757'))
            ax.add_patch(Circle((4.6, 3.2), 0.55, facecolor='#2E86DE'))
            ax.add_patch(Circle((5.9, 3.6), 0.55, facecolor='#10AC84'))
            ax.annotate('', xy=(8.2, 4.6), xytext=(7.0, 2.6),
                        arrowprops=dict(arrowstyle='->', color='#FECA57', lw=2))
    fig.suptitle('Assembly — tool-free, no glue or screws', fontsize=15, fontweight='bold')
    fig.tight_layout()
    fig.savefig(OUT / '02_assembly_steps.png')
    plt.close(fig)


def lift_diagram():
    fig, ax = plt.subplots(figsize=(11, 7.2), dpi=140)
    # XZ view of lift
    hub = plt.Circle((0, 0), 70, fill=True, facecolor='#fab1a0', edgecolor='#EE5253', lw=1.5)
    ax.add_patch(hub)
    ax.add_patch(Wedge((0, 0), 108, -120, 98, width=5, facecolor='#636e72', edgecolor='#2d3436'))
    for k in range(6):
        a = math.radians(15 + 60 * k)
        ax.plot([70 * math.cos(a), 105 * math.cos(a)],
                [70 * math.sin(a), 105 * math.sin(a)], color='#c0392b', lw=6, solid_capstyle='round')
    # chute
    import lift as Lf
    xs = np.linspace(float(Lf.P_tan()[0]), Lf.CHUTE_END_X, 40)
    zs = [Lf.chute_center_z(x) for x in xs]
    ax.plot(xs, zs, color='#2E86DE', lw=3, label='chute (ball centre)')
    # sample lift path
    import json
    log = json.loads(Path('/workspace/marble-factory/reports/lift2d_log.json').read_text())['log']
    ax.plot([s['x'] for s in log if s['x'] > -180], [s['z'] for s in log if s['x'] > -180],
            color='#0984e3', lw=1.4, ls='--', label='simulated ball centre')
    ax.add_patch(Circle((0, -90.5), 17.5, facecolor='#FF4757', edgecolor='#c0392b', alpha=0.85))
    ax.text(0, -90.5, 'pickup', ha='center', va='center', fontsize=7, color='white')
    ax.set_aspect('equal')
    ax.set_xlim(-200, 140)
    ax.set_ylim(-150, 140)
    ax.set_xlabel('X (mm)  —  front is +Y, out of the page')
    ax.set_ylabel('Z (mm)')
    ax.set_title('Paddle-wheel lift (section through the wheel plane)')
    ax.legend(loc='upper right', fontsize=8)
    ax.axhline(-136, color='#b2bec3', lw=1)
    ax.text(-190, -132, 'tile top', fontsize=8, color='#636e72')
    fig.tight_layout()
    fig.savefig(OUT / '03_lift_mechanism.png')
    plt.close(fig)


if __name__ == '__main__':
    overview()
    assembly_steps()
    lift_diagram()
    print('wrote', list(OUT.glob('*.png')))
