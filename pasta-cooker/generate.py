import bpy, math, os, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
S=.001
M={}
def mat(n,c,metal=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.3;M[n]=m;return m
for a in [('ivory',(.78,.76,.67),0),('graphite',(.035,.055,.065),.4),('steel',(.48,.56,.59),.8),('water',(.035,.45,.65),.2),('hot',(.95,.23,.055),.6),('salt',(.91,.88,.73),0),('green',(.05,.63,.42),.3),('waste',(.43,.25,.11),.1),('screen',(.02,.13,.16),.2),('pasta',(.95,.63,.17),0)]:mat(*a)
parts={};groups={}
def reg(o,n,m,g):
 o.name=n;o.data.materials.append(M[m]);parts[n]=o;groups.setdefault(g,[]).append(o);o['concept']='Unbuilt; not engineering validation';return o
def cube(n,p,d,m,g='core',bev=3):
 bpy.ops.mesh.primitive_cube_add(size=1,location=Vector(p)*S);o=bpy.context.object;o.dimensions=Vector(d)*S;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bev:mod=o.modifiers.new('Soft serviceable corners','BEVEL');mod.width=bev*S;mod.segments=3;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return reg(o,n,m,g)
def cyl(n,p,r,h,m,g='core'):
 bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=r*S,depth=h*S,location=Vector(p)*S);o=bpy.context.object;reg(o,n,m,g)
 for f in o.data.polygons:f.use_smooth=True
 return o
def pipe(n,pts,r,m,g='paths'):
 c=bpy.data.curves.new(n,'CURVE');c.dimensions='3D';c.bevel_depth=r*S;c.bevel_resolution=3;c.resolution_u=12;s=c.splines.new('POLY');s.points.add(len(pts)-1)
 for v,p in zip(s.points,pts):v.co=(*[x*S for x in p],1)
 o=bpy.data.objects.new(n,c);bpy.context.collection.objects.link(o);return reg(o,n,m,g)
def ring(n,p,r,minor,m,g='core'):
 bpy.ops.mesh.primitive_torus_add(major_segments=64,minor_segments=10,location=Vector(p)*S,major_radius=r*S,minor_radius=minor*S);return reg(bpy.context.object,n,m,g)
def shell(n,cx,cy,z,r,h,m,g='core',arc=2*math.pi):
 # open top cylindrical wall, optionally sectioned for visibility
 vs=[];fs=[];N=64
 for i in range(N+1):
  a=i/N*arc
  for rr,zz in [(r,z),(r,z+h),(r-2,z+h),(r-2,z)]:vs.append(((cx+rr*math.cos(a))*S,(cy+rr*math.sin(a))*S,zz*S))
 for i in range(N):
  for j in range(4):fs.append((i*4+j,(i+1)*4+j,(i+1)*4+(j+1)%4,i*4+(j+1)%4))
 mesh=bpy.data.meshes.new(n);mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new(n,mesh);bpy.context.collection.objects.link(o);return reg(o,n,m,g)
# Port-first plumbing graph. Coordinates millimetres; saved before any geometry.
PORTS={
 'tank.out':[-180,-45,210], 'isolation.in':[-170,-45,210], 'isolation.out':[-150,-45,210],
 'feed.in':[-145,-130,220], 'feed.out':[-115,-130,220],
 'meter.in':[-115,-155,230], 'meter.out':[-115,-155,250],
 'heater.in':[-170,-155,270], 'heater.out':[-170,-155,410],
 'fill.nozzle':[-75,-25,480],
 'strainer.chamber':[103,0,300], 'strainer.out':[132,0,300],
 'circulation.in':[175,0,300], 'circulation.out':[195,0,325],
 'return.wall':[132,-10,400], 'return.tee':[110,-10,400],
 'return.a':[100,-40,400], 'return.b':[100,30,400],
 'chamber.low':[20,-65,235], 'drain.in':[20,-110,215], 'drain.out':[20,-110,185],
 'waste.coupling':[150,-140,135], 'waste.internal':[150,-140,120],
 'waste.vent':[245,-140,135], 'vent.out':[245,-90,175],
 'salt.out':[-80,60,540], 'salt.nozzle':[-70,45,480],
 'steam.pickup':[-45,75,440], 'steam.in':[-45,75,465], 'steam.out':[-100,150,525]
}
# Each edge has independent authored endpoints, later tested against actual curve data and port centers.
EDGES=[
 ('F01','tank.out','isolation.in',[[-180,-45,210],[-170,-45,210]],'water',6),
 ('F02','isolation.out','feed.in',[[-150,-45,210],[-140,-45,210],[-140,-100,215],[-155,-130,220],[-145,-130,220]],'water',6),
 ('F03','feed.out','meter.in',[[-115,-130,220],[-105,-130,220],[-105,-155,220],[-115,-155,220],[-115,-155,230]],'water',6),
 ('F04','meter.out','heater.in',[[-115,-155,250],[-115,-155,255],[-115,-185,255],[-190,-185,255],[-190,-155,255],[-190,-155,270],[-170,-155,270]],'water',6),
 ('H01','heater.in','heater.out',[[-170,-155,270],[-120,-155,270],[-120,-155,305],[-170,-155,305],[-170,-155,340],[-120,-155,340],[-120,-155,375],[-170,-155,375],[-170,-155,410]],'hot',6),
 ('H02','heater.out','fill.nozzle',[[-170,-155,410],[-170,-155,495],[-75,-155,495],[-75,-25,495],[-75,-25,480]],'hot',6),
 ('C00','strainer.chamber','strainer.out',[[103,0,300],[132,0,300]],'green',12),
 ('C01','strainer.out','circulation.in',[[132,0,300],[175,0,300]],'green',12),
 ('C02','circulation.out','return.wall',[[195,0,325],[195,0,350],[195,-10,375],[195,-10,400],[132,-10,400]],'green',12),
 ('C03','return.wall','return.tee',[[132,-10,400],[110,-10,400]],'green',12),
 ('C04','return.tee','return.a',[[110,-10,400],[110,-40,400],[100,-40,400]],'green',9),
 ('C05','return.tee','return.b',[[110,-10,400],[110,30,400],[100,30,400]],'green',9),
 ('D01','chamber.low','drain.in',[[20,-65,235],[20,-65,225],[20,-110,225],[20,-110,215]],'waste',10),
 ('D02','drain.out','waste.coupling',[[20,-110,185],[20,-110,175],[20,-140,170],[100,-140,160],[150,-140,150],[150,-140,135]],'waste',10),
 ('D03','waste.coupling','waste.internal',[[150,-140,135],[150,-140,120]],'waste',10),
 ('V01','waste.vent','vent.out',[[245,-140,135],[245,-140,175],[245,-90,175]],'waste',5),
 ('S01','salt.out','salt.nozzle',[[-80,60,540],[-80,60,515],[-70,45,490],[-70,45,480]],'salt',8),
 ('ST01','steam.in','steam.out',[[-45,75,465],[-45,75,505],[-100,150,525]],'steel',12),
 ('ST00','steam.pickup','steam.in',[[-45,75,440],[-45,75,465]],'steel',12)
]
INTERNALS=[{'component':'Isolation/check cartridge','from':'isolation.in','to':'isolation.out'}, {'component':'Metering feed pump','from':'feed.in','to':'feed.out'}, {'component':'Flowmeter','from':'meter.in','to':'meter.out'}, {'component':'Recirculation pump','from':'circulation.in','to':'circulation.out'}, {'component':'Normally closed drain valve','from':'drain.in','to':'drain.out'}]
manifest={'units':'mm','ports':PORTS,'edges':[{'id':n,'from':a,'to':b,'points':p,'material':m,'radius_mm':r} for n,a,b,p,m,r in EDGES], 'internal_component_connections':INTERNALS,'open_transfers':[{'from':'fill.nozzle','to':'chamber water surface','air_gap_mm':60},{'from':'salt.nozzle','to':'chamber','type':'gravity drop'}], 'water_max_z':420,'waste_max_z':95,'waste_roof_z':135,'concept_only':True}
json.dump(manifest,open(OUT+'/connection-manifest.json','w'),indent=2)
# Additional materials for clear visual hierarchy.
mat('white',(.95,.94,.87));mat('dry',(.18,.23,.35),.3);mat('ink',(.015,.025,.03));mat('warning',(.95,.64,.02))
# helpers: ports are real hollow collars, not spheres obscuring endpoints.
def collar(n,p,axis,r,m,g='ports'):
 o=ring(n,p,r+2,2,m,g);o.rotation_euler=Vector(axis).to_track_quat('Z','Y').to_euler();return o
def rod(n,a,b,r,m,g='hardware'):
 v=Vector(b)-Vector(a);o=cyl(n,(Vector(a)+Vector(b))/2,r,v.length,m,g);o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return o
def arrow(n,a,b,m,g='arrows'):
 a,b=Vector(a),Vector(b);v=b-a
 if v.length<18:return
 p=a+v*.63;bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=9*S,radius2=0,depth=20*S,location=p*S);o=bpy.context.object;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();reg(o,n,m,g)
def hole(obj,center,axis,r,length):
 cutter=rod('temporary bore',Vector(center)-Vector(axis)*length/2,Vector(center)+Vector(axis)*length/2,r,'steel','cutters');bpy.context.view_layer.objects.active=obj;mod=obj.modifiers.new('Physical port bore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);groups['cutters'].remove(cutter);parts.pop('temporary bore',None);bpy.data.objects.remove(cutter,do_unlink=True)
def text(n,p,size,m='white',g='tags'):
 c=bpy.data.curves.new(n,'FONT');c.body=n;c.size=size*S;c.extrude=.0001;o=bpy.data.objects.new(n,c);bpy.context.collection.objects.link(o);o.location=Vector(p)*S;o.rotation_euler=(math.pi/2,0,0);return reg(o,n,m,g)
# Chassis fits around defined plumbing, no full-width slab across plumbing.
cube('Chassis drip containment base',(0,-10,15),(660,480,20),'graphite','base',10)
for x in [-270,270]:
 for y in [-195,175]:cyl('Anti slip foot %s %s'%(x,y),(x,y,2),16,10,'graphite','base')
# Tank hollow walls with actual side outlet. Front wall removable in cutaway.
for n,p,d in [('Tank left wall',(-290,0,325),(4,170,270)),('Tank right wall',(-180,0,325),(4,170,270)),('Tank rear wall',(-235,85,325),(110,4,270)),('Tank floor',(-235,0,190),(110,170,4))]:
 o=cube(n,p,d,'water','tank',0)
 if n=='Tank right wall':hole(o,PORTS['tank.out'],(1,0,0),6,15)
cube('Tank front panel',(-235,-85,325),(110,4,270),'water','tank_front',0)
cube('Unsalted clean water visual',(-235,0,282),(101,158,176),'water','tank',2)
cube('Tank lid',(-235,0,462),(116,177,8),'ivory','tank')
pipe('Tank removable handle',[(-260,0,466),(-260,0,485),(-210,0,485),(-210,0,466)],4,'steel','tank')
text('CLEAN / UNSALTED',(-285,-89,410),9)
# Real open-bottom chamber floor: annulus loft to off-center low-point aperture.
verts=[];faces=[];N=80
for i in range(N):
 a=i*math.tau/N
 for x,y,z,r in [(20,0,255,110),(20,-65,235,12)]:verts.append(((x+r*math.cos(a))*S,(y+r*math.sin(a))*S,z*S))
for i in range(N):j=(i+1)%N;faces.append((2*i,2*j,2*j+1,2*i+1))
mesh=bpy.data.meshes.new('Sloped floor with open low point');mesh.from_pydata(verts,[],faces);o=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(o);reg(o,mesh.name,'steel','vessel');sol=o.modifiers.new('Floor wall thickness','SOLIDIFY');sol.thickness=2*S
# Rear half is never removed; front half is genuinely sectional.
shell('Vessel rear half',20,0,255,112,200,'steel','vessel',math.pi)
o=shell('Vessel front cutaway shell',20,0,255,112,200,'steel','vessel_front',math.pi);o.rotation_euler[2]=math.pi;o.location.x=40*S # rotation about world origin restores center20
# Bore the x-positive wall for suction and return (cuts half at y0 / y-10)
for g in ['vessel','vessel_front']:
 for o in list(groups[g]):
  if o.name.startswith('Vessel'):
   hole(o,(132,0,300),(1,0,0),14,18);hole(o,(132,-10,400),(1,0,0),14,20)
ring('Chamber rolled rim',(20,0,455),112,3,'steel','vessel')
# Water limit ring, not a solid water plug obscuring internals.
ring('MAX WATER 420mm',(20,0,420),107,1.3,'water','vessel')
# Heater mantle follows outside vessel lower wall, keeps lowpoint free.
pipe('Optional direct vessel mantle heater',[(20+116*math.cos(a),116*math.sin(a),265) for a in [i*math.tau/90 for i in range(91)]],4,'hot','vessel')
# Perforated basket with actual open ribs, bottom grid and smooth withdrawal envelope.
for z,r in [(280,78),(440,78)]:ring('Basket rim '+str(z),(20,0,z),r,2.5,'steel','basket')
for i in range(36):
 a=math.tau*i/36;pipe('Basket vertical mesh %02d'%i,[(20+78*math.cos(a),78*math.sin(a),280),(20+78*math.cos(a),78*math.sin(a),440)],.75,'steel','basket')
for z in range(300,440,20):ring('Basket hoop '+str(z),(20,0,z),78,.75,'steel','basket')
for q in range(-60,61,20):
 extent=math.sqrt(78**2-q**2);pipe('Basket base grid '+str(q),[(20+q,-extent,280),(20+q,extent,280)],1,'steel','basket');pipe('Basket cross grid '+str(q),[(20-extent,q,280),(20+extent,q,280)],1,'steel','basket')
pipe('Basket bridge',[(20-77,0,440),(20-77,0,454),(20+77,0,454),(20+77,0,440)],3,'steel','basket')
# Actuation rails above full clearing height. Carriage travels vertically without swinging basket outside chamber.
for x in [-5,45]:rod('Lift rail '+str(x),(x,150,260),(x,150,710),5,'steel','lift')
cube('Lift drive mast',(20,175,485),(90,28,460),'graphite','lift')
cube('Lift load cell carriage',(20,150,454),(68,35,24),'green','carriage')
pipe('Lift fork into basket bridge',[(20,150,454),(20,0,454)],4,'steel','carriage')
# Fill, salt and steam apertures through actual lid.
lid=cyl('Removable chamber lid',(20,0,465),116,8,'ivory','lid')
for p,r in [((-75,-25,465),11),((-70,45,465),12),((-45,75,465),14),((20,0,465),7)]:hole(lid,p,(0,0,1),r,20)
cube('Cool touch lid handle',(60,30,478),(55,18,14),'graphite','lid')
# Salt hopper has open funnel, no rising chute or pretend auger.
shell('Salt cartridge cylinder',-80,60,565,24,45,'salt','salt')
# cone-like ring surface with central aperture; same loft method reused via mesh
vs=[];fs=[]
for i in range(48):
 a=i*math.tau/48
 for r,z in [(24,565),(8,540)]:vs.append(((-80+r*math.cos(a))*S,(60+r*math.sin(a))*S,z*S))
for i in range(48):j=(i+1)%48;fs.append((i*2,j*2,j*2+1,i*2+1))
me=bpy.data.meshes.new('Salt open funnel');me.from_pydata(vs,[],fs);o=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(o);reg(o,me.name,'salt','salt')
cyl('Salt moisture cap',(-80,60,613),26,6,'graphite','salt')
cube('Salt metering gate housing',(-80,60,548),(30,25,12),'graphite','salt');hole(parts['Salt metering gate housing'],(-80,60,548),(0,0,1),8,20)
# Distinct inline component bodies, each with declared visible connector ports.
rod('Isolation check cartridge',PORTS['isolation.in'],PORTS['isolation.out'],11,'graphite','feed')
rod('Metering feed pump',PORTS['feed.in'],PORTS['feed.out'],18,'graphite','feed')
rod('Flowmeter',PORTS['meter.in'],PORTS['meter.out'],11,'white','feed')
cube('Heater electrical isolation ceramic plate',(-145,-132,340),(78,10,170),'white','heater')
cube('Heater dry back enclosure',(-145,-116,340),(85,18,175),'graphite','heater')
# Recirc motor is outside screened chamber. Serviceable cartridge on the side, away from food basket.
rod('Heat compatible circulation pump concept',(175,0,300),(215,0,300),22,'green','recirc')
rod('Circulation discharge port riser',(195,0,300),PORTS['circulation.out'],13,'green','recirc')
# Broad screened inlet at x103; flat perimeter and bars over open inlet chamber.
for z in [275,325]:pipe('Removable strainer frame '+str(z),[(103,-30,z),(103,30,z)],2,'steel','strainer')
for y in [-30,30]:pipe('Strainer frame edge '+str(y),[(103,y,275),(103,y,325)],2,'steel','strainer')
for y in range(-25,26,5):pipe('Strainer guard bar '+str(y),[(103,y,275),(103,y,325)],.9,'steel','strainer')
# Open hood edges taper to suction tube; bars represent conceptual screen, not validated mesh.
for y in [-30,30]:
 for z in [275,325]:pipe('Intake plenum edge %s %s'%(y,z),[(103,y,z),(132,0,300)],1.4,'green','strainer')
collar('Strainer service union',(149,0,300),(1,0,0),14,'steel','strainer')
pipe('Service union release lever',[(149,-18,300),(149,-42,300)],3,'warning','strainer')
# NC drain has explicit through bore, actuator is beside rather than over the fluid centerline.
rod('Normally closed drain valve body',PORTS['drain.in'],PORTS['drain.out'],18,'graphite','drain')
cube('NC drain actuator accessible',(52,-110,200),(30,35,28),'graphite','drain');rod('Valve actuator stem',(20,-110,200),(52,-110,200),4,'steel','drain')
text('NC',(-1,-132,198),10,'white','drain')
# Bores align actual connection faces; pump internals remain conceptual, not performance geometry.
for nam,a,b,r in [('Isolation check cartridge',PORTS['isolation.in'],PORTS['isolation.out'],6),('Metering feed pump',PORTS['feed.in'],PORTS['feed.out'],6),('Flowmeter',PORTS['meter.in'],PORTS['meter.out'],6),('Normally closed drain valve body',PORTS['drain.in'],PORTS['drain.out'],10)]:
 mid=(Vector(a)+Vector(b))/2;axis=(Vector(b)-Vector(a)).normalized();hole(parts[nam],mid,axis,r,(Vector(b)-Vector(a)).length+4)
cyl('NC gate default CLOSED',(20,-110,200),10,2,'warning','drain')
# Waste is below entire vessel floor. Open front section shows headspace and real receiving inlet.
for n,p,d in [('Waste left wall',(125,-140,81),(4,150,106)),('Waste right wall',(275,-140,81),(4,150,106)),('Waste rear wall',(200,-65,81),(150,4,106)),('Waste bottom',(200,-140,28),(150,150,4))]:cube(n,p,d,'waste','waste',0)
cube('Waste front drawer panel',(200,-215,81),(150,4,106),'waste','waste_front',0)
roof=cube('Waste lid',(200,-140,135),(154,154,4),'waste','waste',0)
for p,r in [(PORTS['waste.coupling'],12),(PORTS['waste.vent'],6)]:hole(roof,p,(0,0,1),r,12)
cube('Waste max fill water visual',(200,-140,62),(140,140,64),'waste','waste',0)
pipe('Waste maximum fill level',[(128,-214,95),(272,-214,95)],1.5,'warning','waste')
collar('Removable drain dry break coupling',PORTS['waste.coupling'],(0,0,1),13,'steel','waste')
cube('Waste drawer cool pull',(200,-226,80),(65,16,12),'steel','waste_front')
cube('Waste coupling drip tray',(150,-140,22),(60,70,5),'steel','waste')
# Vent outlet shield is hollow/open, clearly not a potable feed.
collar('Waste vent anti splash outlet',PORTS['vent.out'],(0,1,0),7,'waste','waste')
rod('Steam standpipe rim bracket',(-45,75,452),(-54,85,452),3,'steel','vessel')
# Dry bay stays above and rear/right of wet circuits, solid segregating barrier.
cube('Dry electronics compartment',(270,130,450),(90,100,140),'dry','dry')
cube('Wet dry barrier',(218,130,450),(6,120,160),'white','dry')
text('DRY BAY',(230,77,465),10,'white','dry')
# Actual graph curves and physical port collars. Arrow cones sit on straight actual segments.
for n,a,b,pts,m,r in EDGES:
 pipe(n+' '+a+' -> '+b,pts,r,m,'plumbing');parts[n]=parts.pop(n+' '+a+' -> '+b)
 for k,(p,q) in enumerate(zip(pts,pts[1:])):
  if (Vector(q)-Vector(p)).length>=42:arrow(n+' flow '+str(k),p,q,m)
for n,p in PORTS.items():
 linked=[e for e in EDGES if e[1]==n or e[2]==n];e=linked[0]
 axis=Vector(e[3][1])-Vector(e[3][0]) if e[1]==n else Vector(e[3][-1])-Vector(e[3][-2])
 collar('PORT '+n,p,axis,e[5],e[4])
# Above-water free-fall, explicitly discontinuous: beads are water not a pipe/junction.
for z in [471,450,430]:
 bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=2*S,location=(-75*S,-25*S,z*S));reg(bpy.context.object,'Air gap water drop '+str(z),'water','drops')
# Exterior panels occupy only known dry clearance zones. No full-width deck through plumbing.
cube('Right outer guard',(326,40,320),(8,400,560),'ivory','exterior',12)
cube('Rear outer guard',(40,220,320),(570,8,560),'ivory','exterior',12)
cube('Left tank lower skirt',(-240,-95,130),(125,12,100),'ivory','exterior',8)
cube('Control console',(268,-203,440),(100,35,130),'graphite','exterior',10)
cube('Shape display',(268,-222,460),(80,2,55),'screen','exterior',3)
text('PASTA / 02',(232,-225,470),9,'white','exterior');text('SHAPE + MASS',(232,-225,451),6,'white','exterior')
dial=cyl('Portion dial',(268,-225,409),17,8,'steel','exterior');dial.rotation_euler[0]=math.pi/2
# Removable front guard frames only perimeter, leaves all paths viewable.
for x in [-105,308]:cube('Front guard post '+str(x),(x,-235,280),(10,10,470),'ivory','exterior')
# Port labels on physical circuits (readable from front, not a substitute for connections)
for n,p in [('FILL',(-171,-166,444)),('RECIRC',(169,-32,362)),('DRAIN',(44,-151,173)),('WASTE',(161,-221,108)),('SALT',(-98,34,583))]:text(n,p,8,'ink','tags')
# Numerical tests: inspect real Blender curves in millimetres, not only JSON values.
checks=[]
for n,a,b,pts,m,r in EDGES:
 o=parts[n];actual=[o.matrix_world@Vector(v.co[:3]) for v in o.data.splines[0].points]
 for end,port,k in [('start',a,0),('end',b,-1)]:
  err=(actual[k]/S-Vector(PORTS[port])).length;checks.append({'edge':n,'endpoint':end,'port':port,'error_mm':round(err,7),'pass':err<.01})
# Sample centerlines plus tube radius against unrelated tank/electrical/waste bounding solids.
def inside_box(p,lo,hi,pad=0):return all(lo[i]-pad<=p[i]<=hi[i]+pad for i in range(3))
interferences=[]
boxes={'clean tank':([-292,-87,188],[-178,87,466]),'waste reservoir':([123,-217,26],[277,-63,137]),'dry bay':([225,80,380],[315,180,520])}
for n,a,b,pts,m,r in EDGES:
 for box,(lo,hi) in boxes.items():
  if box=='clean tank' and n=='F01':continue
  if box=='waste reservoir' and n in ['D02','D03','V01']:continue
  for p,q in zip(pts,pts[1:]):
   for i in range(31):
    v=Vector(p).lerp(Vector(q),i/30)
    if inside_box(v,lo,hi,r):interferences.append({'edge':n,'unrelated_box':box,'point_mm':list(v)});break
# Gravity drain including valve and receiving stub must never ascend.
drain_points=EDGES[12][3]+[PORTS['drain.out']]+EDGES[13][3]+EDGES[14][3]
gravity=all(q[2]<=p[2]+.001 for p,q in zip(drain_points,drain_points[1:]))
# Basket clear travel envelope excludes fixed intake/return, nozzle beyond basket sweep or above bridge.
report={'endpoint_checks':checks,'endpoint_passed':all(x['pass'] for x in checks),'interference_scope':'Tube radius padded sampled AABB against unrelated clean tank, waste and dry bay only; not full mesh/manufacturing validation','unrelated_box_interferences':interferences,'drain_nonincreasing_z':gravity,'air_gap_to_maxwater_mm':480-420,'basket_raised_bottom_mm':280+190,'vessel_rim_mm':455,'basket_clearance_above_rim_mm':15,'basket_radial_gap_to_strainer_mm':103-(20+78),'steam_out_to_dry_bay_nearest_mm':math.dist(PORTS['steam.out'],[225,145,520]),'all_pass':all(x['pass'] for x in checks) and not interferences and gravity}
sweep={}
for key,r in [('fill.nozzle',6),('salt.nozzle',8),('steam.in',12)]:
 p=PORTS[key];sweep[key]=round(math.hypot(p[0]-20,p[1])-(r+4)-78,3)
report['basket_sweep_nozzle_radial_clearance_mm']=sweep
report['lift_sweep_check_pass']=all(v>0 for v in sweep.values())
report['all_pass']=report['all_pass'] and report['lift_sweep_check_pass']
def point_segment(p,a,b):
 v=b-a;return (p-(a+v*max(0,min(1,(p-a).dot(v)/v.dot(v))))).length if v.length else (p-a).length
def segment_distance(p,q,r,t):
 p,q,r,t=map(Vector,(p,q,r,t));u=q-p;v=t-r;w=p-r
 aa=u.dot(u);bb=u.dot(v);cc=v.dot(v);dd=u.dot(w);ee=v.dot(w);den=aa*cc-bb*bb
 candidates=[point_segment(p,r,t),point_segment(q,r,t),point_segment(r,p,q),point_segment(t,p,q)]
 if den>1e-9:
  sc=(bb*ee-cc*dd)/den;tc=(aa*ee-bb*dd)/den
  if 0<=sc<=1 and 0<=tc<=1:candidates.append((p+sc*u-r-tc*v).length)
 return min(candidates)
def circuit(n):return 'potable' if n[0] in 'FH' else 'steam' if n.startswith('ST') else n[0]
pairs=[]
for i,e in enumerate(EDGES):
 for f in EDGES[i+1:]:
  if circuit(e[0])==circuit(f[0]):continue
  if e[0].startswith('V') and f[0].startswith('D') or f[0].startswith('V') and e[0].startswith('D'):continue
  dist=min(segment_distance(p,q,r,t) for p,q in zip(e[3],e[3][1:]) for r,t in zip(f[3],f[3][1:]))
  gap=dist-e[5]-f[5]
  pairs.append({'edges':[e[0],f[0]],'surface_gap_mm':round(gap,3),'pass':gap>0})
report['distinct_circuit_segment_clearances']=pairs
report['distinct_circuit_clearance_pass']=all(q['pass'] for q in pairs)
expected_axes={k:(1,0,0) for k in ['tank.out','isolation.in','isolation.out','feed.in','feed.out','heater.in','strainer.chamber','strainer.out','circulation.in','return.wall']}
expected_axes.update({k:(0,0,1) for k in ['meter.in','meter.out','heater.out','fill.nozzle','circulation.out','chamber.low','drain.in','drain.out','waste.coupling','waste.internal','waste.vent','salt.out','salt.nozzle','steam.in','steam.pickup']})
axis_checks=[]
for n,a,b,pts,m,r in EDGES:
 for port,v in [(a,Vector(pts[1])-Vector(pts[0])),(b,Vector(pts[-1])-Vector(pts[-2]))]:
  if port in expected_axes:
   alignment=abs(v.normalized().dot(Vector(expected_axes[port])));axis_checks.append({'edge':n,'port':port,'axis_alignment':round(alignment,6),'pass':alignment>.999})
report['port_tangent_checks']=axis_checks
report['port_tangent_pass']=all(c['pass'] for c in axis_checks)
report['all_pass']=report['all_pass'] and report['port_tangent_pass']
report['all_pass']=report['all_pass'] and report['distinct_circuit_clearance_pass']
json.dump(report,open(OUT+'/topology-checks.json','w'),indent=2)
assert report['all_pass'],report
# Real structural cradle/load path (conceptual sizing) keeps vessel and lift supported.
cube('Mast lower structural pedestal',(20,175,140),(90,40,240),'graphite','base')
ring('Vessel support cradle',(20,0,280),114,3,'steel','base')
for x in [-70,110]:
 rod('Cradle upright '+str(x),(x,115,25),(x,115,280),6,'steel','base')
 rod('Cradle rear tie '+str(x),(x,115,280),(20,175,280),5,'steel','base')
 rod('Cradle radial tie '+str(x),(x,115,280),(20+(x-20)*7/9,90,280),5,'steel','base')
# Named actual Blender assemblies; all hydraulics remain in their assemblies in every view.
for g,objs in list(groups.items()):
 collection=bpy.data.collections.new('ASSEMBLY '+g);scene_root=bpy.context.scene.collection;scene_root.children.link(collection)
 root=bpy.data.objects.new('ASSEMBLY '+g,None);collection.objects.link(root)
 for ob in list(objs):
  for col in list(ob.users_collection):col.objects.unlink(ob)
  collection.objects.link(ob);ob.parent=root
 groups[g].append(root)
# Camera/render setup
cube('Studio floor',(0,0,-14),(10000,10000,10),'ivory','stage')
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1800;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.world.color=(.25,.25,.25);scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.65
bpy.ops.object.camera_add(location=(1.05,-1.6,1.1));cam=bpy.context.object;scene.camera=cam;cam.name='PRIMARY inspectable plumbing camera';cam.data.type='ORTHO';cam.data.ortho_scale=1.03;cam.rotation_euler=(Vector((0,-.015,.34))-cam.location).to_track_quat('-Z','Y').to_euler()
for pos,power,size in [((-.5,-.8,1.3),95,.9),((.9,-.2,.9),65,.7),((0,.8,1.1),80,.7)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.size=size;o.rotation_euler=(Vector((0,0,.3))-o.location).to_track_quat('-Z','Y').to_euler()
def hide(gs,state):
 for g in gs:
  for o in groups.get(g,[]):o.hide_render=state;o.hide_set(state)
VIEWCHECKS={}
def output(name,labels):
 bpy.context.view_layer.update()
 errs=[]
 for n,a,b,pts,m,r in EDGES:
  ob=parts[n]
  for port,k in [(a,0),(b,-1)]:
   end=ob.matrix_world@Vector(ob.data.splines[0].points[k].co[:3]);center=parts['PORT '+port].matrix_world.translation
   errs.append((end-center).length/S)
 VIEWCHECKS[name]={'actual_port_endpoint_max_error_mm':max(errs),'endpoint_count':len(errs),'pass':max(errs)<.01,'basket_bottom_z_mm':parts['Basket rim 280'].matrix_world.translation.z/S}
 assert VIEWCHECKS[name]['pass']
 json.dump(VIEWCHECKS,open(OUT+'/view-topology-checks.json','w'),indent=2)
 scene.render.filepath=OUT+'/'+name+'-raw.png'
 bpy.ops.wm.save_as_mainfile(filepath=OUT+'/pasta-cooker-v2-'+name+'.blend')
 bpy.ops.object.select_all(action='DESELECT')
 for g,os_ in groups.items():
  if g in ['stage','cutters']:continue
  for o in os_:
   if not o.hide_render:o.hide_set(False);o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=OUT+'/pasta-cooker-v2-'+name+'.glb',export_format='GLB',use_selection=True,export_apply=True,export_extras=True)
 bpy.ops.render.render(write_still=True)
 anchors={}
 for t,p in labels.items():
  q=world_to_camera_view(scene,cam,Vector(p)*S);anchors[t]=[round(q.x*1800),round((1-q.y)*1500)]
 json.dump(anchors,open(OUT+'/'+name+'-anchors.json','w'),indent=2)
labels={'Unsalted clean tank':[-235,-85,350],'Isolation / meter / pump':[-135,-130,220],'Heated channel':[-145,-155,340],'AIR GAP / max water':[-75,-25,475],'Salt gravity chute':[-72,50,505],'Screened recirculation':[165,0,300],'LOW POINT + NC valve':[20,-110,200],'DOWNHILL drain':[95,-140,152],'Waste inlet / headspace':[150,-140,128],'Dry bay / steam apart':[270,80,480]}
output('exterior',labels)
hide(['exterior','tank_front','waste_front','vessel_front','lid'],True)
output('cutaway',labels)
# Service exploded view preserves ALL hydraulic connectivity. Only basket/carriage and dry covers move.
for g in ['basket','carriage']:
 groups[g][-1].location.z+=190*S
hide(['lid'],False)
groups['lid'][-1].location+=Vector((-80,60,300))*S
cam.data.ortho_scale=1.18;cam.rotation_euler=(Vector((0,0,.39))-cam.location).to_track_quat('-Z','Y').to_euler()
labels2={'Basket clears rim 15mm':[20,0,470],'Lid removed / service':[-60,60,765],'Clean feed stays left':[-145,-155,340],'Recirculation stays attached':[195,0,350],'Drain stays attached':[95,-140,152],'Waste stays BELOW floor':[200,-215,95],'Dry bay is separate':[270,80,480],'Valve accessible':[52,-110,200]}
output('exploded',labels2)
print('V2 COMPLETE',bpy.app.version_string,'ENDPOINTS',len(checks),'PASS',report['all_pass'])
