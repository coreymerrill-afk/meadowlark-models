"""Track modules, stands, base tiles, switch vane, spinner rotor/posts. Local module frame:
start joint at origin heading +x, V-vertex z=0 at start. Rims horizontal at z=+34 (print face)."""
import numpy as np, math
from geom import *
RB=17.5; VH=RB*math.sqrt(2)          # ball-centre height above V vertex (24.75)
BOT=6.0; W2=38.0; VT=30.0; VTN=20.0; RIM=34.0
PEG_R=9.7; PEG_D=10.0; SOCK_R=10.2; SOCK_D=11.0; CAP_CLR_R=16.5
DROP=20.0
def straight(L,drop,x0=0,y0=0,z0=0,n=2):
    return [((x0+L*i/(n-1),y0,z0-drop*i/(n-1)),(1,0)) for i in range(n)]
def arc(R,turn,drop,ang=90.0,n=49):
    s=1 if turn=='L' else -1; cx,cy=0.0,s*R; out=[]
    for i in range(n):
        a=math.radians(ang*i/(n-1))
        x=R*math.sin(a); y=s*R*(1-math.cos(a)); t=(math.cos(a),s*math.sin(a))
        out.append(((x,y,-drop*i/(n-1)),t))
    return out
def scurve(L,D,drop,z0=0,n=65,reverse=False):
    out=[]
    for i in range(n):
        x=L*i/(n-1); f=0.5*(1-math.cos(math.pi*x/L)); df=0.5*math.pi/L*math.sin(math.pi*x/L)
        y=D*(1-f) if reverse else D*f; dy=-D*df if reverse else D*df
        out.append(((x,y,z0-drop*i/(n-1)),(1,dy)))
    return out
def path_len(path):
    P=np.array([p for p,_ in path]); return float(np.sum(np.linalg.norm(np.diff(P,axis=0),axis=1)))
def extend(path,e=1.0):
    (p0,t0),(p1,t1)=path[0],path[1]; (q0,s0),(q1,s1)=path[-2],path[-1]
    def ext(a,b,t,e):
        a=np.array(a);b=np.array(b); d=b-a; d=d/np.hypot(d[0],d[1]); return tuple(b+d*e)
    first=(ext(p1,p0,t0,e),t0); last=(ext(q0,q1,s1,e),s1)
    return [first]+path+[last]
def pocket_cutters(path,keep=24.0,skip=None):
    """Hollow the underside: two triangular pockets per side parallel to the V (4 mm shell)."""
    P=np.array([p for p,_ in path]); s=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(P,axis=0),axis=1))])
    Ltot=s[-1]; out=[]
    def ok(si): return keep<=si<=Ltot-keep and not (skip and skip[0]<=si<=skip[1])
    segs=[];cur=[]
    for i,si in enumerate(s):
        if ok(si): cur.append(i)
        elif cur: segs.append(cur);cur=[]
    if cur: segs.append(cur)
    for seg in segs:
        if len(seg)<2:continue
        sub=[path[i] for i in seg]
        for sg in (1,-1):
            loop=[(sg*1.5,-7.0),(sg*32,-7.0),(sg*32,32-5.66-1.5)] if sg>0 else [(-32,-7.0),(-1.5,-7.0),(-32,32-5.66-1.5)]
            if sg>0: loop=[(1.5,-7.0),(32,-7.0),(32,24.84)]
            else: loop=[(-32,-7.0),(-1.5,-7.0),(-32,24.84)]
            out.append(sweep([(p,t,loop) for p,t in sub]))
    return out
def channel_solids(path,z_top,vt=VT,w2=W2,body=True):
    bod=None
    if body:
        bod=sweep([(p,t,[(-w2,-BOT),(w2,-BOT),(w2,z_top-p[2]),(-w2,z_top-p[2])]) for p,t in path])
    cut=sweep([(p,t,[(0,0),(vt,vt),(vt,z_top-p[2]+6),(-vt,z_top-p[2]+6),(-vt,vt)]) for p,t in extend(path,1.0)])
    return bod,cut
def joint_features(man,joints):
    """joints: list of (x,y,zv,outward_heading_angle_deg). Clears stand cap and adds half-disc peg."""
    for (x,y,zv,ang) in joints:
        cap=zv-BOT
        man=man-cyl(CAP_CLR_R,40,x,y,cap-40)
    pegs=[]
    for (x,y,zv,ang) in joints:
        cap=zv-BOT
        half=box(-30,-0.15,-30,30,cap-PEG_D,cap+1.0).rotate([0,0,ang]).translate([x,y,0])
        pegs.append(cyl(PEG_R,PEG_D+1.0,x,y,cap-PEG_D)^half)
    return union([man]+pegs)
def hollow(man,inset_bodies,cutters,joints,keep_r=22.0,shell=4.5,extra_keep=None):
    """Open-bottom underside pockets keeping >=shell mm under every floor/wall (print-upside-down friendly)."""
    tall=[c for c in cutters]
    sh=[]
    for c in tall:
        sh.append(c.translate([0,0,-shell*1.4143]))
        for dx,dy in ((shell,0),(-shell,0),(0,shell),(0,-shell)):
            sh.append(c.translate([dx,dy,-shell]))
    pocket=union(inset_bodies)-union(sh+tall)
    pocket=pocket^box(-1e4,1e4,-1e4,1e4,-1e3,RIM-10)
    keep=[cyl(keep_r,400,x,y,-300) for (x,y,zv,a) in joints]+(extra_keep or [])
    pocket=pocket-union(keep)
    return man-pocket
def inset_body(path,w=W2-6.0):
    return sweep([(p,t,[(-w,-300),(w,-300),(w,RIM-10-p[2]),(-w,RIM-10-p[2])]) for p,t in path])
def module(channels,joints,z_top=RIM,vt=VT,extra_add=None,extra_cut=None,pockets=False,pocket_skip=None,hollow_it=True,keep=None):
    bods=[];cuts=[]
    for ch in channels:
        b,c=channel_solids(ch,z_top,vt); bods.append(b); cuts.append(c)
        if pockets: cuts+=pocket_cutters(ch,skip=pocket_skip)
    man=union(bods+(extra_add or []))
    man=man-union(cuts)
    if extra_cut: man=man-union(extra_cut)
    if hollow_it:
        tallc=[channel_solids(ch,RIM+150,vt,body=False)[1] for ch in channels]
        man=hollow(man,[inset_body(ch) for ch in channels],tallc,joints,extra_keep=keep)
    return joint_features(man,joints)
# ---------------- module catalogue (local frames) -----------------
def mod_straight(L=160.0,drop=DROP):
    p=straight(L,drop,n=17); return module([p],[(0,0,0,180),(L,0,-drop,0)]),p
def mod_corner(turn,drop=DROP,R=80.0):
    p=arc(R,turn,drop); s=1 if turn=='L' else -1
    return module([p],[(0,0,0,180),(R,s*R,-drop,s*90)]),p
SW_L=240.0; SW_D=80.0; SW_DROP=40.0; ZONE0=15.0; ZONE1=135.0; B_LAT=40.0
SW_DA=12.0; SW_DB_OUT=SW_DROP+12.0     # A output -12 ; B output -52 (rel. input vertex)
def sw_zvA(x): return -SW_DA*x/SW_L
def sw_B_path(n=40):
    """B vertex path: straight at y=40 inside the drop zone, then S-curve to (240,80)."""
    out=[]
    zB1=sw_zvA(ZONE1)-SW_DROP
    for i in range(9):
        x=ZONE0+(ZONE1-ZONE0)*i/8; out.append(((x,B_LAT,sw_zvA(x)-SW_DROP),(1,0)))
    L2=SW_L-ZONE1
    for i in range(1,n+1):
        t=i/n; x=ZONE1+L2*t; f=0.5*(1-math.cos(math.pi*t)); df=0.5*math.pi/L2*math.sin(math.pi*t)
        y=B_LAT+(SW_D-B_LAT)*f; z=zB1+(-SW_DB_OUT-zB1)*t
        out.append(((x,y,z),(1,(SW_D-B_LAT)*df)))
    return out
def mod_switch():
    """Drop switch: A rides a 45deg shelf; with the bridge-gate removed the ball rolls off the
    shelf and drops 40 mm into channel B. Shelf plane = A's right V face extended (v=-u)."""
    A=straight(SW_L,SW_DA,n=49); B=sw_B_path()
    zt=RIM
    bodA=sweep([(p,t,[(-W2,-BOT),(W2,-BOT),(W2,zt-p[2]),(-W2,zt-p[2])]) for p,t in A])
    # B body (outer), bottom 6 below B vertex
    bodB=sweep([(p,t,[(-W2,-BOT),(W2,-BOT),(W2,zt-p[2]),(-W2,zt-p[2])]) for p,t in B])
    # zone filler under the shelf between A and B
    zone=sweep([((x,0,sw_zvA(x)),(1,0),[(-W2,-SW_DROP-BOT),(B_LAT+W2,-SW_DROP-BOT),(B_LAT+W2,zt-sw_zvA(x)),(-W2,zt-sw_zvA(x))]) for x in (ZONE0-8,ZONE1+8)])
    body=union([bodA,bodB,zone])
    cuts=[]; cuts_tall=[]
    # A normal V upstream of zone
    cuts.append(sweep([((x,0,sw_zvA(x)),(1,0),[(0,0),(VT,VT),(VT,zt-sw_zvA(x)+6),(-VT,zt-sw_zvA(x)+6),(-VT,VT)]) for x in (-1.0,ZONE0)]))
    # zone: shelf plane from A right-face top down to B vertex, B left face, B left wall
    cuts.append(sweep([((x,0,sw_zvA(x)),(1,0),[(-VT,VT),(B_LAT,-SW_DROP),(B_LAT+VT,-SW_DROP+VT),(B_LAT+VT,zt-sw_zvA(x)+6),(-VT,zt-sw_zvA(x)+6)]) for x in (ZONE0,ZONE1)]))
    # A after zone: right face + vertical guide face at u=17.5 (fixed wall)
    cuts.append(sweep([((x,0,sw_zvA(x)),(1,0),[(-VT,VT),(17.5,-17.5),(17.5,zt-sw_zvA(x)+6),(-VT,zt-sw_zvA(x)+6)]) for x in (ZONE1,SW_L+1)]))
    # B after zone: V with right face truncated by the fixed wall (u_B=-18.5)
    Bp=[q for q in B if q[0][0]>=ZONE1-1e-6]
    cuts.append(sweep([(p,t,[(0,0),(VT,VT),(VT,zt-p[2]+6),(-18.5,zt-p[2]+6),(-18.5,18.5)]) for p,t in extend(Bp,1.0)]))
    def tallify(c): return c
    # tall versions for hollowing (extend tops to +150)
    zt2=RIM+150
    cuts_tall.append(sweep([((x,0,sw_zvA(x)),(1,0),[(0,0),(VT,VT),(VT,zt2),(-VT,zt2),(-VT,VT)]) for x in (-1.0,ZONE0)]))
    cuts_tall.append(sweep([((x,0,sw_zvA(x)),(1,0),[(-VT,VT),(B_LAT,-SW_DROP),(B_LAT+VT,-SW_DROP+VT),(B_LAT+VT,zt2),(-VT,zt2)]) for x in (ZONE0,ZONE1)]))
    cuts_tall.append(sweep([((x,0,sw_zvA(x)),(1,0),[(-VT,VT),(17.5,-17.5),(17.5,zt2),(-VT,zt2)]) for x in (ZONE1,SW_L+1)]))
    cuts_tall.append(sweep([(p,t,[(0,0),(VT,VT),(VT,zt2),(-18.5,zt2),(-18.5,18.5)]) for p,t in extend(Bp,1.0)]))
    man=body-union(cuts)
    tall=[c.translate([0,0,0]) for c in cuts]
    big=[sweep([(p,t,[(0,0),(VT,VT),(VT,300),(-VT,300),(-VT,VT)]) for p,t in extend(A,1.0)])] if False else []
    insets=[inset_body(A),inset_body(Bp),sweep([((x,0,sw_zvA(x)),(1,0),[(-W2+6,-300),(B_LAT+W2-6,-300),(B_LAT+W2-6,RIM-10-sw_zvA(x)),(-W2+6,RIM-10-sw_zvA(x))]) for x in (ZONE0-8,ZONE1+8)])]
    keepg=[cyl(10,400,x,y,-300) for x in (ZONE0+8,ZONE1-8) for y in (-34.0,B_LAT+34.0)]
    man=hollow(man,insets,[c.translate([0,0,0]) for c in cuts_tall],[(0,0,0,0),(SW_L,0,0,0),(SW_L,SW_D,0,0)],extra_keep=keepg)
    # gate locating holes in rim (right rim and B left rim)
    holes=[cyl(4.3,8,x,y,zt-7) for x in (ZONE0+8,ZONE1-8) for y in (-34.0,B_LAT+34.0)]
    man=man-union(holes)
    man=joint_features(man,[(0,0,0,180),(SW_L,0,-SW_DA,0),(SW_L,SW_D,-SW_DB_OUT,0)])
    return man,(A,B)
MG_L=160.0; MG_DA=SW_DB_OUT-SW_DA+12.0; MG_DB=12.0
def mod_merge():
    """Inputs: A at (0,0) zv 0, B at (0,80) zv -(SW_DB_OUT-SW_DA). Output (160,0) zv -MG_DA."""
    zB0=-(SW_DB_OUT-SW_DA)
    a=straight(MG_L,MG_DA,n=33)
    b=scurve(MG_L,SW_D,MG_DB,z0=zB0,reverse=True)
    man=module([a,b],[(0,0,0,180),(0,SW_D,zB0,180),(MG_L,0,-MG_DA,0)])
    return man,(a,b)
def gate_bridge():
    """Removable bridge-gate in switch-local frame: plate above the ball, legs into rim holes,
    blade hanging to the shelf with its guide face at u=+17.5."""
    zt=RIM; x0,x1=ZONE0,ZONE1
    plate=box(x0,x1,-38,B_LAT+38,zt+11,zt+15)
    legs=[cyl(6,11.01,x,y,zt) for x in (x0+8,x1-8) for y in (-34.0,B_LAT+34.0)]
    pegs=[cyl(3.9,6.5,x,y,zt-6.5) for x in (x0+8,x1-8) for y in (-34.0,B_LAT+34.0)]
    # blade: face at y=17.5, thickness 4; bottom follows shelf plane (v=-u) with 1 mm clearance
    blade=sweep([((x,0,sw_zvA(x)),(1,0),[(17.5,-17.5+1.0),(21.5,-21.5+1.0),(21.5,zt-sw_zvA(x)+11.5),(17.5,zt-sw_zvA(x)+11.5)]) for x in (x0+0.3,x1-0.3)])
    grip=box((x0+x1)/2-30,(x0+x1)/2+30,B_LAT+38,B_LAT+52,zt+11,zt+15)
    return union([plate,blade,grip]+legs+pegs)
SP_POST_U=29.0; SP_SOCK=10.0; SP_SOCK_D=15.0
SP_H=36.0; SP_RH=10.0; SP_RP=30.0; SP_T=6.0; SP_N=4; SP_HUB_L=47.0
def mod_spinner(drop=DROP,L=160.0):
    p=straight(L,drop,n=33)
    socks=[box(L/2-SP_SOCK/2,L/2+SP_SOCK/2,s*SP_POST_U-SP_SOCK/2,s*SP_POST_U+SP_SOCK/2,RIM-SP_SOCK_D,RIM+1) for s in (1,-1)]
    return module([p],[(0,0,0,180),(L,0,-drop,0)],vt=VTN,extra_cut=socks,keep=[box(L/2-14,L/2+14,-60,60,-300,400)]),p
def spinner_axis_local(L=160.0,drop=DROP):
    zv=-drop*0.5; return np.array([L/2,0.0,zv+VH+SP_H])
def spinner_rotor():
    """Rotor + integral stubs. Built with axis along +Z, then mapped to +Y.
    Four paddles live in planes containing the axis (they sweep the XZ plane when the axis is +Y)."""
    half=SP_HUB_L/2
    stub_l=8.0
    hub=cyl(SP_RH,SP_HUB_L,0,0,-half)
    stubs=cyl(4.0,SP_HUB_L+2*stub_l,0,0,-(half+stub_l))
    # paddle in XY (radial along +X), thickness along Y, length along Z (=axis)
    # chamfer the last (SP_RP-12) mm of radius so the tips are narrower than the hub
    tip=half-(SP_RP-12.0)
    pads=[]
    blade=box(SP_RH-1.0, SP_RP, -SP_T/2, SP_T/2, -tip, tip)
    for k in range(SP_N):
        pads.append(blade.rotate([0,0,360.0/SP_N*k]))
    rot=union([hub,stubs]+pads)
    # (x,y,z) -> (x,z,-y)  so +Z axis becomes +Y
    rot=rot.transform(np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0]],float))
    return rot
def spinner_post(L=160.0,drop=DROP,side=+1):
    """Post with open-top U-slot that the rotor stub drops into. side=+1 is +u (left)."""
    ax=spinner_axis_local(L,drop)
    x0=L/2; u0=side*SP_POST_U
    ui,uo=(u0-5,u0+5) if side>0 else (u0-5,u0+5)
    body=box(x0-7,x0+7,ui,uo,RIM-SP_SOCK_D+0.5,ax[2]+14)
    # U-slot: 8.8 mm wide, open at the top, semicircle seat at axis
    slot=box(x0-4.4,x0+4.4,ui-1,uo+1,ax[2],ax[2]+20)
    seat=cyl(4.4,abs(uo-ui)+2,0,0,0).transform(np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0]],float)).translate([ax[0],min(ui,uo)-1,ax[2]])
    # retainer sockets on top of each post ear
    holes=cyl(3.2,8,x0-0,u0,ax[2]+14-7.5)
    return body-slot-seat-holes
def spinner_retainer(L=160.0,drop=DROP):
    """Two caps that close the U-slots, joined by a high arch that clears the r=30 paddle disc."""
    ax=spinner_axis_local(L,drop)
    x0=L/2
    # caps sit on each post top (outside the paddle width |y|<=23.5)
    caps=[box(x0-8,x0+8,s*SP_POST_U-6,s*SP_POST_U+6,ax[2]+14,ax[2]+20) for s in (1,-1)]
    pegs=[cyl(2.9,8.0,x0,s*SP_POST_U,ax[2]+14-8.0) for s in (1,-1)]
    teeth=[box(x0-4.1,x0+4.1,s*SP_POST_U-4.6,s*SP_POST_U+4.6,ax[2]+4.6,ax[2]+14.1) for s in (1,-1)]
    # high arch above the paddle tip (Rp=30) so spinning blades pass underneath
    arch=box(x0-6,x0+6,-SP_POST_U-6,SP_POST_U+6,ax[2]+SP_RP+4,ax[2]+SP_RP+10)
    legs=[box(x0-6,x0+6,s*SP_POST_U-5,s*SP_POST_U+5,ax[2]+20,ax[2]+SP_RP+4.1) for s in (1,-1)]
    return union(caps+pegs+teeth+[arch]+legs)
# ---------------- vane ----------------
VANE_L=84.0; VANE_DIP_R=36.0
def switch_vane(angle_deg,zbottom_abs):
    """Vane in module-local frame, blade pointing at angle_deg (0=+x) from pivot."""
    px,py=switch_pivot()
    hub=cyl(10,8,0,0,RIM+0.3); pin=cyl(4.0,13.3,0,0,RIM-13.0)
    hi=box(0,VANE_DIP_R+1,-2.5,2.5,RIM+0.6,RIM+8.3)
    lo=box(VANE_DIP_R,VANE_L,-2.5,2.5,zbottom_abs,RIM+8.3)
    tip=cyl(2.5,RIM+8.3-zbottom_abs,VANE_L,0,zbottom_abs)
    handle=box(-34,0,-3.5,3.5,RIM+0.3,RIM+8.3)
    knob=cyl(6,8,-34,0,RIM+0.3)
    v=union([hub,pin,hi,lo,tip,handle,knob])  # unused if drop-gate is used
    return v.rotate([0,0,angle_deg]).translate([px,py,0])
# ---------------- stands & tiles --------------
TILE=240.0; TILE_H=12.0; TILE_SOCK_R=10.2; TILE_SOCK_D=10.0
def stand(cap_top):
    """Stand with cap top at height cap_top above tile top (z=0)."""
    peg=cyl(9.7,TILE_SOCK_D-0.5,0,0,-(TILE_SOCK_D-0.5))
    flange=union([cyl(20,3,0,0,0),M.cylinder(5,20,15,64).translate([0,0,3])])
    col=cyl(15,cap_top-3,0,0,1)
    capb=cyl(18,6,0,0,cap_top-6)
    s=union([peg,flange,col,capb])
    s=s-cyl(SOCK_R,SOCK_D+0.01,0,0,cap_top-SOCK_D)
    return s
def dovetail(w0,w1,d):
    return [(0,-w0/2),(d,-w1/2),(d,w1/2),(0,w0/2)]
def base_tile():
    t=TILE; h=TILE_H; ribs=[]
    ribs.append(box(0,t,0,6,-h,0)); ribs.append(box(0,t,t-6,t,-h,0))
    ribs.append(box(0,6,0,t,-h,0)); ribs.append(box(t-6,t,0,t,-h,0))
    for c in (40,120,200):
        ribs.append(box(0,t,c-3,c+3,-h,0)); ribs.append(box(c-3,c+3,0,t,-h,0))
    boss=[cyl(17,h,x,y,-h) for x in (40,120,200) for y in (40,120,200)]
    tile=union(ribs+boss)
    # dovetail tabs on +x and +y edges, notches on -x and -y
    tabs=[];notch=[]
    for c in (80,160):
        tabs.append(poly_extrude([(t+a,c+b) for a,b in dovetail(14,20,10)],h,-h))
        tabs.append(poly_extrude([(c-b,t+a) for a,b in dovetail(14,20,10)],h,-h))
        notch.append(poly_extrude([(a-0.01,c+b*(1+0.04)) for a,b in [(0,-7.3),(10.3,-10.3),(10.3,10.3),(0,7.3)]],h+2,-h-1))
        notch.append(poly_extrude([(c-b*(1+0.04),a-0.01) for a,b in [(0,-7.3),(10.3,-10.3),(10.3,10.3),(0,7.3)]],h+2,-h-1))
    tile=union([tile]+tabs)
    # fill under notches so notch walls exist: add solid strip along -x/-y edge where notches are
    strips=[box(0,14,c-16,c+16,-h,0) for c in (80,160)]+[box(c-16,c+16,0,14,-h,0) for c in (80,160)]
    tile=union([tile]+strips)-union(notch)
    socks=[cyl(TILE_SOCK_R,TILE_SOCK_D+0.01,x,y,-TILE_SOCK_D) for x in (40,120,200) for y in (40,120,200)]
    return tile-union(socks)

def mod_inlet(L,drop,nose=15.0):
    p=straight(L,drop,n=5)
    pw=[q for q in p if q[0][0]<=L-nose+1e-6]+[((L-nose,0,-drop*(L-nose)/L),(1,0))]
    pn=[((L-nose,0,-drop*(L-nose)/L),(1,0)),((L,0,-drop),(1,0))]
    b1=sweep([(q,tt,[(-W2,-BOT),(W2,-BOT),(W2,RIM-q[2]),(-W2,RIM-q[2])]) for q,tt in pw[:-1]+[pw[-1]]])
    b2=sweep([(q,tt,[(-24,-BOT),(24,-BOT),(24,RIM-q[2]),(-24,RIM-q[2])]) for q,tt in pn])
    cut=sweep([(q,tt,[(0,0),(21,21),(21,RIM-q[2]+6),(-21,RIM-q[2]+6),(-21,21)]) for q,tt in extend(p,1.0)])
    man=union([b1,b2])-cut
    return joint_features(man,[(0,0,0,180)]),p
