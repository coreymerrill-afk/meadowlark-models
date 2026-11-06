"""Geometry helpers on manifold3d."""
import numpy as np, math
import manifold3d as m3
M=m3.Manifold
def mesh_to_manifold(V,F):
    V=np.asarray(V,dtype=np.float32); F=np.asarray(F,dtype=np.uint32)
    man=M(m3.Mesh(vert_properties=V,tri_verts=F))
    if man.status()!=m3.Error.NoError: raise RuntimeError(str(man.status()))
    if man.volume()<0: man=M(m3.Mesh(vert_properties=V,tri_verts=F[:,::-1].copy()))
    return man
def sweep(samples):
    """samples: list of (origin xyz, tangent xy (horizontal unit), loop [(u,v),...]) — same N per loop,
    convex loops. u = left lateral, v = world up."""
    loops=[]
    for o,t,loop in samples:
        o=np.asarray(o,float); t=np.asarray(t,float); t=t/np.hypot(t[0],t[1])
        u=np.array([-t[1],t[0],0.0])
        pts=[o+u*a+np.array([0,0,b]) for a,b in loop]
        loops.append(pts)
    N=len(loops[0]); V=[p for L in loops for p in L]; F=[]
    K=len(loops)
    for k in range(K-1):
        for i in range(N):
            a=k*N+i; b=k*N+(i+1)%N; c=(k+1)*N+(i+1)%N; d=(k+1)*N+i
            F+=[[a,b,c],[a,c,d]]
    for i in range(1,N-1): F.append([0,i+1,i])
    base=(K-1)*N
    for i in range(1,N-1): F.append([base,base+i,base+i+1])
    man=mesh_to_manifold(V,F)
    return man
def cyl(r,h,x=0,y=0,z=0,seg=64):
    return M.cylinder(h,r,r,seg).translate([x,y,z])
def box(x0,x1,y0,y1,z0,z1):
    return M.cube([x1-x0,y1-y0,z1-z0]).translate([x0,y0,z0])
def poly_extrude(pts2d,h,z0=0):
    cs=m3.CrossSection([np.asarray(pts2d,float)],m3.FillRule.Positive)
    if cs.area()<0: cs=m3.CrossSection([np.asarray(pts2d[::-1],float)],m3.FillRule.Positive)
    return M.extrude(cs,h).translate([0,0,z0])
def circle_pts(r,n=64,cx=0,cy=0,a0=0,a1=360):
    return [(cx+r*math.cos(math.radians(a0+(a1-a0)*i/n)),cy+r*math.sin(math.radians(a0+(a1-a0)*i/n))) for i in range(n+ (0 if a1-a0>=360 else 1))]
def union(parts):
    parts=[p for p in parts if p is not None and not p.is_empty()]
    return M.batch_boolean(parts,m3.OpType.Add) if len(parts)>1 else parts[0]
def to_trimesh(man):
    import trimesh
    mm=man.to_mesh(); return trimesh.Trimesh(np.asarray(mm.vert_properties)[:,:3],np.asarray(mm.tri_verts),process=False)
def hexagon(af,n_rot=0.0):
    r=af/2/math.cos(math.pi/6)
    return [(r*math.cos(math.radians(30+60*i+n_rot)),r*math.sin(math.radians(30+60*i+n_rot))) for i in range(6)]
def rot_y_axis_to_z():
    # matrix mapping a part modelled with axis along z to axis along y (x stays)
    return np.array([[1,0,0,0],[0,0,-1,0],[0,1,0,0]],float)
