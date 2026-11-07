"""Queen Anne upgrade, millimetres. Import build(snapshot), then Assembly.world().

Adapted for this repo. The helper's lift-off rear roof panel is not built:
the roof stays one fixed solid. Turret belt plates are molded bands with
raised rosettes, not a board of through-holes. Finial and console tips are
blunt. Cutters stay out of the print bill.
"""
from pathlib import Path
from dataclasses import dataclass, field
import math
import json
import numpy as np
import trimesh as tm
import manifold3d as md
from shapely.affinity import translate
from shapely.geometry import Polygon, Point, LineString, box as rect
from shapely.ops import unary_union

CREAM='#efe1bf'; SAGE='#75917e'; SLATE='#354552'

def U(ms):
    ms=[m for m in ms if m is not None]
    return tm.boolean.union(ms,engine='manifold') if len(ms)>1 else ms[0].copy()
def D(m,cs):
    return tm.boolean.difference([m,*cs],engine='manifold') if cs else m.copy()
def B(x0,y0,z0,x1,y1,z1):
    m=tm.creation.box([x1-x0,y1-y0,z1-z0]);m.apply_translation([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2]);return m
def E(p,z=0,d=2):
    p=p.buffer(0)
    if p.geom_type=='MultiPolygon':return U([E(q,z,d) for q in p.geoms])
    contours=[np.array(p.exterior.coords)[:-1]]+[np.array(r.coords)[:-1] for r in p.interiors]
    cs=md.CrossSection(contours,md.FillRule.EvenOdd)
    raw=md.Manifold.extrude(cs,d).to_mesh()
    m=tm.Trimesh(np.asarray(raw.vert_properties)[:,:3],np.asarray(raw.tri_verts),process=True)
    m.apply_translation([0,0,z]);return m

def stroke(pts,w=1.4):return LineString(pts).buffer(w/2,resolution=8,join_style=1)
def arc(cx,cy,rx,ry,a=0,b=math.pi,n=60):
    return [(cx+rx*math.cos(t),cy+ry*math.sin(t)) for t in np.linspace(a,b,n)]
def arch(w,h,r):
    return Polygon([(-w/2,0),(w/2,0),(w/2,h-r),*arc(0,h-r,w/2,r),(-w/2,0)])
def shift(p,x,y):
    return translate(p,xoff=x,yoff=y)
def plane(origin=(0,0,0),x=(1,0,0),y=(0,0,1),normal=(0,-1,0)):
    m=np.eye(4);m[:3,:3]=np.array([x,y,normal]).T;m[:3,3]=origin;return m

def key_shapes(points,clear=0):
    # Different widths and clipped corners prevent reversed seating.
    out=[]
    for i,(x,y) in enumerate(points):
        w=3.6 if i==0 else 5.2
        p=Polygon([(x-w/2,y-1.6),(x+w/2-.9,y-1.6),(x+w/2,y-.7),(x+w/2,y+1.6),(x-w/2,y+1.6)])
        out.append(p.buffer(clear,join_style=2))
    return out

@dataclass
class Part:
    name:str; mesh:tm.Trimesh; transform:np.ndarray; role:str='decor'; host:str=''; note:str=''; color:str=CREAM
    def world(self):
        m=self.mesh.copy();m.apply_transform(self.transform);return m
@dataclass
class Assembly:
    parts:list=field(default_factory=list)
    replacements:dict=field(default_factory=dict)
    cuts:dict=field(default_factory=dict)
    source:dict=field(default_factory=dict)
    def add(self,name,mesh,T,**kw):
        p=Part(name,mesh,T,**kw);self.parts.append(p);return p
    def keyed(self,name,mesh,T,points,host,note=''):
        tabs=[E(p,-2,2.25) for p in key_shapes(points)]
        p=self.add(name,U([mesh,*tabs]),T,host=host,note=note)
        for i,q in enumerate(key_shapes(points,.20)):
            c=self.add(name+f'_socket_{i+1}',E(q,-2.25,2.5),T,role='cutter',host=host,note='0.20 mm lateral and 0.25 mm depth allowance')
            self.cuts.setdefault(host,[]).append(c.world())
        return p
    def world(self):return {p.name:p.world() for p in self.parts if p.role!='cutter'}
    def apply(self,hosts):
        """hosts: instance-id -> WORLD mesh. Returns copies with replacements/cuts."""
        result={k:v.copy() for k,v in hosts.items()}
        result.update({k:v.copy() for k,v in self.replacements.items()})
        for k,cs in self.cuts.items():
            if k in result:result[k]=D(result[k],cs)
        # Quantize as STL does before removing zero-volume coplanar sheets.
        # A 2.864 mm³ old spindle stump is also freed by the porch crop; discard it.
        for k in ('rear','porch-front'):
            if k in result:
                q=tm.Trimesh(vertices=np.asarray(result[k].vertices,dtype=np.float32),faces=result[k].faces,process=True)
                bodies=[p for p in q.split(only_watertight=False) if abs(p.volume)>1e-6]
                if k=='porch-front':bodies=[max(bodies,key=lambda p:p.volume)]
                result[k]=tm.util.concatenate(bodies)
        for k in ('cap-back-l','cap-back-r'):result.pop(k,None)
        return result
    def export(self,out):
        out=Path(out);(out/'models').mkdir(parents=True,exist_ok=True)
        records=[];rows=[]
        for p in self.parts:
            # Lay the largest planar mounting face on the bed; tabs point up.
            R=tm.transformations.rotation_matrix(math.pi,[1,0,0])
            flat=p.mesh.copy();flat.apply_transform(R)
            lo=flat.bounds[0].copy();flat.apply_translation(-lo)
            tolocal=np.linalg.inv(R)@tm.transformations.translation_matrix(lo)
            T=p.transform@tolocal
            path=out/'models'/(p.name+'.stl');flat.export(path)
            reload=tm.load_mesh(path,process=True)
            bodies=len(reload.split(only_watertight=False))
            rows.append(f'| {p.name} | {reload.is_watertight} | {reload.is_winding_consistent} | {bodies} | {reload.volume:.3f} |')
            records.append(dict(name=p.name,role=p.role,host=p.host,note=p.note,print_to_world=T.tolist(),print_extents_mm=flat.extents.tolist(),color=p.color))
        for name,m in self.replacements.items():
            # Replacements provided in world and separately in flat print pose.
            W=m.copy();axis=int(np.argmin(W.extents));R=np.eye(4)
            if axis==1:R=tm.transformations.rotation_matrix(math.pi/2,[1,0,0])
            elif axis==0:R=tm.transformations.rotation_matrix(math.pi/2,[0,1,0])
            W.apply_transform(R);lo=W.bounds[0].copy();W.apply_translation(-lo)
            name='host_'+name.replace('-','_');path=out/'models'/(name+'.stl');W.export(path)
            reload=tm.load_mesh(path,process=True)
            rows.append(f'| {name} | {reload.is_watertight} | {reload.is_winding_consistent} | {len(reload.split(only_watertight=False))} | {reload.volume:.3f} |')
            records.append(dict(name=name,role='replacement_host',print_to_world=(np.linalg.inv(R)@tm.transformations.translation_matrix(lo)).tolist(),print_extents_mm=W.extents.tolist()))
        (out/'placements.json').write_text(json.dumps(dict(source=self.source,parts=records),indent=2))
        (out/'topology.md').write_text('# Reloaded STL topology\n\nVolumes in mm³. Every row reloads the exported STL with vertex merging; bodies count includes all components. Cutters are separate tools, never print quantities.\n\n| Part | Watertight | Winding consistent | Bodies | Volume mm³ |\n|---|---|---|---:|---:|\n'+'\n'.join(rows)+'\n')
        return records

def read_hosts(snapshot):
    root=Path(snapshot);m=json.loads((root/'manifest.json').read_text());hosts={};colors={}
    for i in m['instances']:
        if i['role']=='coupon':continue
        p=tm.load_mesh(root/'stl'/(i['part']+'.stl'));p.apply_transform(i['transform'])
        hosts[i['id']]=p;colors[i['id']]=i['color']
    return hosts,colors,m

def build(snapshot):
    """Read actual v640 geometry; return upgrades + keyed cutters + host replacements.
    Call apply(world_hosts) before combining decorative world meshes.
    """
    hosts,colors,manifest=read_hosts(snapshot)
    src=Path(snapshot)/'cad'/'build_queen_anne_v5.py'
    if not src.exists():
        src=Path(snapshot)/'source'/'build_queen_anne_v5.py'
    text=src.read_text()
    required=['gx0, gx1 = 292.0, 468.0','TX, TY, TR = 156.0, 126.0, 58.0','front_posts = [(250, 36), (330, 32), (410, 32), (488, 36)]']
    for s in required:
        if s not in text:raise ValueError('Unsupported source geometry: '+s)
    a=Assembly(source=dict(snapshot=str(snapshot),gable_triangle=[[296,74,216],[464,74,216],[380,74,376]],turret_radius=58,porch_posts=[[250,36],[330,32],[410,32],[488,36]],original_gable_bounds=hosts['gable'].bounds.tolist()))
    T=plane((380,74,216))
    verges=[]
    tri=Polygon([(-84,0),(84,0),(0,160)])
    win=shift(arch(46,71,20),0,23)
    host=E(tri.difference(win),-5.2,5.2);host.apply_transform(T)
    a.replacements['gable']=host
    # Two flowing openwork verges: continuous scalloped lower edge and interlaced S-scrolls.
    for side in [-1,1]:
        start=np.array([side*81,4.]);end=np.array([side*2,155.]);d=end-start;L=np.linalg.norm(d);v=d/L
        n=np.array([-v[1],v[0]])*side
        # n points inward on both rakes.
        def pt(s,t):return tuple(start+v*s+n*t)
        pieces=[stroke([pt(0,1),pt(L,1)],2.4),stroke([pt(0,10),pt(L-4,10)],1.6)]
        for c in np.arange(8,L-8,18):
            path=[]
            for t in np.linspace(0,2*math.pi,65):path.append(pt(c+7.4*math.cos(t),7+5.0*math.sin(t)))
            pieces.append(stroke(path,1.4))
            spts=[pt(c-8+16*t,7+3.8*math.sin(2*math.pi*t)) for t in np.linspace(0,1,55)]
            pieces.append(stroke(spts,1.3))
        p=unary_union(pieces).buffer(0)
        # Keeps delicate work within the gable silhouette, no isolated fragments.
        p=p.intersection(tri.buffer(1.4)).intersection(rect(-100,4.1,100,180))
        casing_keepout=shift(arch(60,82,25),0,19).union(stroke(arc(0,70,31,31),3.2)).buffer(.25)
        p=p.difference(casing_keepout).difference(rect(-3.5,128,3.5,180))
        for q in key_shapes([(-12,110),(0,130)],.3):p=p.difference(q)
        if p.geom_type=='MultiPolygon':p=max(p.geoms,key=lambda q:q.area)
        points=[pt(22,1),pt(L-30,1)]
        verges.append(p)
        base=E(p,0,2.2)
        outer=E(stroke([pt(0,1),pt(L,1)],1.2).intersection(p),2.1,1.0)
        a.keyed('gable_verge_'+('left' if side<0 else 'right'),U([base,outer]),T,points,'gable','1.3 mm scroll webs, flowing enclosed curved voids')
    # Large arched sash casing: outer moulding, recessed inner bead, projecting hood.
    outer=shift(arch(60,82,25),0,19)
    ring=outer.difference(win)
    inner=win.buffer(1.6).difference(win)
    hood=stroke(arc(0,70,31,31),3.2)
    casing=U([E(ring,0,2.5),E(inner,2.4,1.6),E(hood,2.3,3.2),E(rect(-33,18,33,22),0,5.2)])
    casing=D(casing,[E(q,-2.25,3) for q in key_shapes([(-22.5,30),(22.5,35)],.2)])
    a.keyed('gable_arched_casing',casing,T,[(-27,43),(27,52)],'gable','Opening 46 x 71 mm; casing 60 x 82 mm; elliptical arched head')
    # Separate connected sash. 1.6 mm mullions linked to perimeter.
    sash=win.buffer(.0).difference(win.buffer(-1.6))
    sash=sash.union(rect(-.9,23,.9,93).intersection(win)).union(rect(-23,57,23,58.8).intersection(win))
    a.keyed('gable_sash',E(sash,-1,1.5),T,[(-22.5,30),(22.5,35)],'gable','Tabs land in opening jamb; perimeter bead remains 1.6 mm')
    # Apex fan and kingpost; fan rim ties every ray to the kingpost.
    fan=stroke(arc(0,109,20,18),1.6).union(rect(-20,107.8,20,110))
    for t in np.linspace(.12,math.pi-.12,9):fan=fan.union(stroke([(0,109),(20*math.cos(t),109+18*math.sin(t))],1.3))
    king=Polygon([(-1.6,108),(1.6,108),(1.6,154),(3.0,158),(1.7,162),(-1.7,162),(-3.0,158),(-1.6,154)]).union(Point(0,163.2).buffer(1.8,16))
    fanmesh=U([E(fan.union(king),4,2.8),*[E(q,0,4.25) for q in key_shapes([(-12,110),(0,130)])]])
    a.keyed('gable_fan_kingpost',fanmesh,T,[(-12,110),(0,130)],'gable','Nine fan rays. Apex ends in a 3.6 mm ball, not a needle.')
    # Deep stepped cornice with curved brackets tied to continuous rails.
    corn=[E(rect(-85,-3,85,2),0,3),E(rect(-87,-1,87,2),2.8,3),E(rect(-89,1,89,3.8),5.6,2)]
    for x in np.arange(-72,73,18):
        q=Polygon([(x-2.8,1),(x+2.8,1),(x+2.2,-8),(x+1.5,-9.4),(x-0.3,-9.4),(x-1.6,-8),(x-2.8,-5)]).buffer(.45)
        corn.append(E(q,.3,4.5))
    a.keyed('gable_cornice',U(corn),T,[(-65,0),(57,0)],'gable','7.6 mm projection, nine consoles, stepped rail')
    # Porch spans use actual slanted post center lines, beam sockets at z=96..103.
    posts=[(250,36),(330,32),(410,32),(488,36)]
    for j,(p,q) in enumerate(zip(posts[:-1],posts[1:])):
        d=np.subtract(q,p);L=np.linalg.norm(d);x=np.array([d[0]/L,d[1]/L,0]);normal=np.cross(x,[0,0,1])
        L=float(q[0]-p[0]);x=np.array([1.,0,0]);normal=np.array([0.,-1,0])
        origin=np.array([p[0],17.8,0])
        P=plane(origin,x,(0,0,1),normal)
        left,right=7,L-7
        poly=rect(left,94,right,97).union(rect(left,78,right,80))
        for s in np.arange(left+3,right-1,5.5):
            # Turned spindle silhouette: neck, bead, belly, bead.
            prof=[(s-.65,79),(s-.65,83),(s-1.15,84),(s-.75,86),(s-1.3,88),(s-.75,90),(s-.65,95),(s+.65,95),(s+.75,90),(s+1.3,88),(s+.75,86),(s+1.15,84),(s+.65,83),(s+.65,79)]
            poly=poly.union(Polygon(prof))
        # Curved, pierced corner brackets, connected to lower and upper rails.
        for c,sign in [(left,1),(right,-1)]:
            shape=Polygon([(c,65),(c,97),(c+sign*19,97),(c+sign*18,93),(c+sign*12,90),(c+sign*7,82),(c+sign*4,72)])
            hole=Point(c+sign*5.7,87).buffer(2.8,resolution=20)
            poly=poly.union(shape.difference(hole))
        a.keyed(f'porch_frieze_{j+1}',E(poly,0,2.4),P,[(15,97),(L-19,98)],'porch-front','Actual center spacing %.3f mm; spindle neck 1.3 mm'%L)
    # Improved 25 mm rail insert, linked turned balusters. Replaces original baluster row only.
    for j,(p,q) in enumerate(zip(posts[:-1],posts[1:])):
        d=np.subtract(q,p);L=np.linalg.norm(d);x=np.array([d[0]/L,d[1]/L,0]);n=np.cross(x,[0,0,1]);P=plane((p[0],p[1],0),x,(0,0,1),n)
        poly=rect(7,22,L-7,24.4).union(rect(7,46,L-7,48.4))
        for s in np.arange(11,L-8,7):
            prof=[(s-1,23),(s-1,27),(s-1.6,28),(s-1.1,31),(s-2,34),(s-1.8,36),(s-.9,39),(s-.9,44),(s-1.5,45),(s-1.5,47),(s+1.5,47),(s+1.5,45),(s+.9,44),(s+.9,39),(s+1.8,36),(s+2,34),(s+1.1,31),(s+1.6,28),(s+1,27),(s+1,23)]
            poly=poly.union(Polygon(prof))
        a.keyed(f'porch_balustrade_{j+1}',E(poly,0,3.2),P,[(10,21.5),(L-12,21.5)],'porch-front','2 mm minimum baluster neck; flat profiled turned silhouette')
        # Body relief removes the old straight rail where the new angled rail seats.
        relief=E(poly.buffer(.1),-.1,3.4)
        a.add(f'porch_balustrade_relief_{j+1}',relief,P,role='cutter',host='porch-front')
        a.cuts.setdefault('porch-front',[]).append(a.parts[-1].world())
        # Remove old rail infill in each open bay, preserving posts and steps.
        cut=B(7,-10,24,L-7,10,47) # local x,y,z where y depth
        # convert construction xyz with z vertical to world basis
        C=np.eye(4);C[:3,0]=x;C[:3,1]=n;C[:3,2]=[0,0,1];C[:3,3]=[p[0],p[1],0]
        cut.apply_transform(C);a.cuts.setdefault('porch-front',[]).append(cut)
        a.add(f'porch_infill_removal_{j+1}',cut,np.eye(4),role='cutter',host='porch-front')
    # Turret belt: seven faceted plates avoid the house intersection at east facet.
    apo=58*math.cos(math.pi/8);fw=2*58*math.sin(math.pi/8)
    for ang in [45,90,135,180,225,270,315]:
        r=math.radians(ang);n=np.array([math.cos(r),math.sin(r),0]);x=np.array([-math.sin(r),math.cos(r),0])
        # local normal must outward with correct handedness: x cross up = outward.
        P=plane(np.array([156,126,201])+n*(apo+1.5),x,(0,0,1),n)
        outline=rect(-fw/2,-2,fw/2,6)
        band=U([E(outline,0,2.2),E(rect(-fw/2,-2,fw/2,-.5),1.8,1.2),E(rect(-fw/2,4.5,fw/2,6),1.8,1.2)])
        for s in np.arange(-16,17,8):
            band=U([band,E(Point(s,2).buffer(2.15,12),2.05,1.15)])
        a.keyed(f'turret_belt_{ang}',band,P,[(-13,0),(12,4)],'turret','Molded band and raised rosettes. No through-holes. East facet omitted.')
    # Layered rings fit all four existing street windows at upper two levels.
    for lev,wz,hostid in [('middle',132,'turret'),('loft',230,'turret-loft')]:
        for ang in [180,225,270,315]:
            r=math.radians(ang);n=np.array([math.cos(r),math.sin(r),0]);x=np.array([-math.sin(r),math.cos(r),0])
            P=plane(np.array([156,126,wz])+n*(apo+.05),x,(0,0,1),n)
            oldtrim=B(-18,-5,.0,18,55,7)
            a.add(f'turret_trim_removal_{lev}_{ang}',oldtrim,P,role='cutter',host=hostid)
            a.cuts.setdefault(hostid,[]).append(a.parts[-1].world())
            opening=rect(-10,0,10,42);outside=rect(-15,-4,15,46)
            ring=outside.difference(opening)
            crown=stroke(arc(0,44,15,7),2).union(rect(-16,43,16,45))
            m=U([E(ring,0,2),E(opening.buffer(1.2).difference(opening),1.8,1.4),E(crown,0,3.5)])
            a.keyed(f'turret_window_{lev}_{ang}',m,P,[(-12.5,8),(12.5,31)],hostid,'Existing 20 x 42 mm opening retained; layered rectangular ring with curved hood')
    # Replace the short ridge sticks with an open spindle-and-scroll crest.
    remove=B(235,190,354.5,290,204,376)
    a.add('crest_old_sticks_removal',remove,np.eye(4),role='cutter',host='roof-front')
    a.cuts.setdefault('roof-front',[]).append(remove)
    CP=plane((0,189.8,0))
    crest=rect(236,352.5,289,355.5).union(rect(236,370,289,372))
    for x in np.arange(239,288,7):
        crest=crest.union(stroke([(x,354),(x,359),(x-1.1,362),(x,365),(x,371)],1.4))
    for x in [237,288]:
        crest=crest.union(stroke([(x,353),(x,376)],2)).union(Point(x,376).buffer(1.8,16))
    a.keyed('roof_ridge_crest',E(crest,0,2.4),CP,[(243,354),(281,354)],'roof-front','53 mm continuous open spindle crest; two terminal balls')
    # The fixed rear roof is not replaced and no lift-off panel is built.
    # Positive cap capture: two rear strips with headed studs, lowered 3 mm into blind keyholes.
    # No new magnet, no change to ONE full magnetic back. Lower z lock position aligns mouths.
    for side,cx in [('left',228),('right',495)]:
        P=plane((cx,301.25,0),x=(1,0,0),y=(0,0,1),normal=(0,-1,0))
        # Strip lies behind back; heads project toward host (negative local depth).
        zs=[44,68,90,142,166,188]
        strip=E(rect(-3.5,39,3.5,194),-1.6,1.6)
        # Mouth plugs, kept clear of disc seat (rear skin at 295.45..).
        # Bosses omitted: the strip can slide without dragging a plug across a magnet mouth.
        # Stud capture away from magnets, at x offset +5.0, with integral lateral bridges.
        for j,z in enumerate([54,177]):
            bridge=E(rect(0,z-2.6,7,z+2.6),-1.6,1.6)
            stem=E(rect(4,z-1,6,z+1),-.2,3.2)
            head=E(rect(3.2,z-2.1,6.8,z+2.1),2.75,1.25)
            strip=U([strip,bridge,stem,head])
            # Entry at z+3, down-slide 3 mm. Cavity behind host surface, narrow mouth retains head.
            cavity=U([E(rect(3,z-2.3,7,z+5.3),2.55,1.7),E(rect(3,z+.7,7,z+5.3),-2,6.5),E(rect(3.8,z-1.2,6.2,z+3.2),-.5,3.2)])
            
            if side=='right':cavity.apply_transform(np.diag([-1,1,1,1]))
            a.add(f'cap_{side}_keyhole_{j+1}',cavity,P,role='cutter',host='rear',note='3 mm down-slide; 0.20 mm sides, 0.25 mm head-depth allowance; 1.35 mm host retaining lip')
            a.cuts.setdefault('rear',[]).append(a.parts[-1].world())
        if side=='right':strip.apply_transform(np.diag([-1,1,1,1]))
        a.add('cap_capture_'+side,strip,P,role='retention',host='rear',note='Enter at z+3, push toward back then slide down 3 mm; mushroom studs captive below 1.35 mm lip')
    return a

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--snapshot',default='v640/qa640-review');p.add_argument('--out',default='out4');args=p.parse_args()
    a=build(args.snapshot);a.export(args.out)
    print('Exported',len(a.parts),'parts/tools and',len(a.replacements),'replacement hosts',flush=True)
