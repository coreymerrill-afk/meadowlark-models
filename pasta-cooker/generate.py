import bpy, math, os, json
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
OUT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
S=.1
M={}
def mat(n,c,metal=0):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.3;M[n]=m;return m
for a in [('ivory',(.78,.76,.67),0),('graphite',(.035,.055,.065),.4),('steel',(.48,.56,.59),.8),('water',(.035,.45,.65),.2),('hot',(.95,.23,.055),.6),('salt',(.91,.88,.73),0),('green',(.05,.63,.42),.3),('waste',(.43,.25,.11),.1),('screen',(.02,.13,.16),.2),('pasta',(.95,.63,.17),0)]:mat(*a)
parts={};groups={}
def reg(o,n,m,g):
 o.name=n;o.data.materials.append(M[m]);parts[n]=o;groups.setdefault(g,[]).append(o);o['concept']='Unbuilt; not engineering validation';return o
def cube(n,p,d,m,g='core',bev=.06):
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
  for rr,zz in [(r,z),(r,z+h),(r-.055,z+h),(r-.055,z)]:vs.append(((cx+rr*math.cos(a))*S,(cy+rr*math.sin(a))*S,zz*S))
 for i in range(N):
  for j in range(4):fs.append((i*4+j,(i+1)*4+j,(i+1)*4+(j+1)%4,i*4+(j+1)%4))
 mesh=bpy.data.meshes.new(n);mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new(n,mesh);bpy.context.collection.objects.link(o);return reg(o,n,m,g)
# envelope 48 x 36 x 40 cm
cube('Structural drip tray base',(0,0,.22),(4.8,3.6,.3),'graphite')
for x in [-1.95,1.95]:
 for y in [-1.3,1.3]:cyl('Isolated foot %s %s'%(x,y),(x,y,.06),.2,.12,'graphite')
cube('Exterior front fascia',(0,-1.72,2),(4.8,.15,3.4),'ivory','exterior',.12)
cube('Exterior right side',(2.3,0,2),(.17,3.4,3.4),'ivory','exterior')
cube('Exterior left side',(-2.3,0,2),(.17,3.4,3.4),'ivory','exterior')
cube('Exterior back panel',(0,1.7,2),(4.8,.13,3.4),'ivory','exterior')
cube('Top deck',(0,0,3.72),(4.8,3.6,.16),'graphite','exterior',.15)
cube('Shape and portion display',(.0,-1.815,2.7),(1.65,.025,.68),'screen','exterior')
cyl('Shape setting rotary dial',(1.3,-1.83,2.65),.23,.12,'steel','exterior').rotation_euler[0]=math.pi/2
# tanks separate left and right front
cube('01 Clean water removable tank',(-1.65,.12,2.13),(.93,2.35,2.8),'water','tank',.18)
cube('Clean tank fill cap',(-1.65,.12,3.59),(.65,.85,.12),'graphite','tank')
pipe('Clean tank carry handle',[(-1.94,.4,3.65),(-1.94,.4,3.9),(-1.34,.4,3.9),(-1.34,.4,3.65)],.055,'steel','tank')
for z in [1.3,1.7,2.1,2.5,2.9]:cube('Tank level mark '+str(z),(-1.65,-1.07,z),(.4,.015,.018),'salt','tank',0)
cube('08 Removable waste drawer',(1.64,-.5,.85),(.95,1.95,.9),'waste','waste',.12)
cube('Waste drawer pull',(1.64,-1.53,.85),(.6,.12,.16),'steel','waste')
# central cooking stack
cyl('Vessel bottom',(.05,.3,1.15),1.02,.12,'steel','vessel')
shell('05 Vessel section wall',.05,.3,1.2,1.02,2.0,'steel','vessel',math.pi*1.05)
ring('Vessel rolled rim',(.05,.3,3.2),1.02,.06,'steel','vessel')
cyl('06 Direct vessel heater plate',(.05,.3,1.02),.94,.12,'hot','vessel')
# basket wire grid visually perforated
ring('04 Basket top rim',(.05,.3,3.06),.82,.04,'steel','basket')
ring('Basket base rim',(.05,.3,1.46),.78,.04,'steel','basket')
for i in range(32):
 a=2*math.pi*i/32;pipe('Basket perforation rib %02d'%i,[(.05+.78*math.cos(a),.3+.78*math.sin(a),1.46),(.05+.82*math.cos(a),.3+.82*math.sin(a),3.06)],.012,'steel','basket')
for z in [1.7,1.95,2.2,2.45,2.7]:ring('Basket mesh hoop '+str(z),(.05,.3,z),.8,.012,'steel','basket')
for i in range(13):
 a=i*2.4;x=.05+.5*math.cos(a);y=.3+.5*math.sin(a);pipe('Dry pasta illustrative %02d'%i,[(x,y,1.5),(x+.1,y+.05,2.8)],.035,'pasta','basket')
pipe('Basket lift bridge',[(-.74,.3,3.1),(-.74,.3,3.4),(.85,.3,3.4),(.85,.3,3.1)],.05,'steel','basket')
cube('09 Lift rail tower',(.5,1.45,2.65),(.45,.25,2.2),'graphite','lift')
pipe('Lift carriage arm',[(.5,1.45,3.35),(.5,.3,3.35)],.07,'steel','lift')
cube('Portion load cell concept',(.5,1.37,1.5),(.5,.4,.18),'green','lift')
# lid
cyl('Steam guarded lid',(.05,.3,3.9),1.12,.14,'ivory','lid');cube('Cool touch lid grip',(.05,.3,4.08),(.8,.25,.22),'graphite','lid')
for i in range(5):cube('Rear steam vent '+str(i),(-.3+i*.15,.92,3.98),(.055,.24,.015),'graphite','lid',.01)
# salt hopper with cone
cyl('02 Separate salt hopper',(1.67,.85,3.3),.3,.65,'salt','salt')
bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=.085*S,radius2=.3*S,depth=.35*S,location=(1.67*S,.85*S,2.8*S));reg(bpy.context.object,'Salt dosing funnel','steel','salt')
pipe('Salt auger dosing chute',[(1.67,.85,2.65),(1.45,.85,2.65),(1.15,.7,3.3),(.8,.7,3.3)],.065,'salt','salt')
# heater and flow routing right side exposed front
cube('03 Flow through heater block',(1.65,-.45,2.35),(.85,.4,1.3),'graphite','heater')
pts=[(1.33,-.72,1.8),(1.96,-.72,1.8),(1.96,-.72,2.05),(1.33,-.72,2.05),(1.33,-.72,2.3),(1.96,-.72,2.3),(1.96,-.72,2.55),(1.33,-.72,2.55),(1.33,-.72,2.9)]
pipe('Heated channel serpentine',pts,.055,'hot','heater')
cyl('Metering pump',(-1,-.95,.75),.18,.32,'water','paths')
pipe('A Clean tank to metering pump',[(-1.65,-.5,.8),(-1.65,-.95,.65),(-1,-.95,.65)],.045,'water')
pipe('B Metered cold feed to channel',[(-1,-.95,.9),(-1,-1.25,.9),(2.05,-1.25,.9),(2.05,-.72,1.8),(1.96,-.72,1.8)],.045,'water')
pipe('C Heated outlet to rim air gap',[(1.33,-.72,2.9),(1.33,-.72,3.45),(.8,-.4,3.45),(.8,-.4,3.25)],.05,'hot')
# guarded recirculation loop
cyl('07 Recirculation pump',(1.4,1.0,1.55),.2,.35,'green','circulation')
pipe('Guarded suction behind basket',[(.95,.85,1.5),(1.4,1,1.5)],.07,'green','circulation')
pipe('Gentle broad return loop',[(1.4,1,1.7),(1.4,1.15,2.7),(.8,1.15,2.7),(.7,.95,2.7)],.07,'green','circulation')
for z in [1.42,1.5,1.58]:pipe('Suction guard slot '+str(z),[(.95,.65,z),(.95,1.0,z)],.025,'steel','circulation')
pipe('Broad tangential outlet',[(.7,.95,2.7),(.4,1.05,2.7),(.1,1.05,2.7)],.10,'green','circulation')
pipe('D Vessel drain to waste',[(.6,.3,1.12),(.6,-.65,.7),(1.64,-.65,.7),(1.64,-.65,1.35)],.075,'waste')
cube('Drain valve actuator',(.65,-.65,.7),(.3,.3,.3),'graphite')
cube('10 Sealed electrical concept bay',(0,1.45,.7),(1.65,.35,.55),'graphite','electrical')
cube('Wet dry isolation barrier',(0,1.19,.75),(1.9,.06,.8),'ivory','electrical')
# Exterior access and readable interface added after first visual inspection
cube('Clean tank viewing strip',(-1.65,-1.81,2.15),(.42,.035,1.9),'water','exterior',.05)
cube('Waste access drawer face',(1.5,-1.82,.85),(1.13,.05,.68),'graphite','exterior',.045)
cube('Waste access cool pull',(1.5,-1.91,.85),(.65,.11,.12),'steel','exterior')
for text,pos,size in [('PASTA / 01',(-.66,-1.84,2.77),.17),('SHAPE  /  PORTION',(-.66,-1.84,2.54),.09),('LIFT + DRAIN',(.96,-1.87,.98),.075)]:
 c=bpy.data.curves.new(text,'FONT');c.body=text;c.size=size*S;c.extrude=.00005;o=bpy.data.objects.new(text,c);bpy.context.collection.objects.link(o);o.location=Vector(pos)*S;o.rotation_euler=(math.pi/2,0,0);reg(o,text,'salt','exterior')
# stage and camera
cube('Studio floor',(0,0,-.12),(200,200,.1),'ivory','stage')
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.world.color=(.3,.3,.3)
bpy.ops.object.camera_add(location=(.78,-1.05,.77));cam=bpy.context.object;cam.name='Presentation camera';scene.camera=cam
cam.rotation_euler=(Vector((0,0,.22))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=.78
for pos,power,size in [((0,-.7,1.2),75,.8),((-.7,.2,.8),55,.7),((.5,.5,1),65,.6)]:
 bpy.ops.object.light_add(type='AREA',location=pos);o=bpy.context.object;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(-o.location+Vector((0,0,.2))).to_track_quat('-Z','Y').to_euler()
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.65
def visibility(gs,hidden):
 for g in gs:
  for o in groups[g]:o.hide_render=hidden;o.hide_set(hidden)
def export(name):
 bpy.ops.object.select_all(action='DESELECT')
 for g,objs in groups.items():
  if g=='stage':continue
  for o in objs:
   if not o.hide_render:o.hide_set(False);o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=OUT+'/'+name+'.glb',export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
def render(name,anchors):
 scene.render.filepath=OUT+'/'+name+'-raw.png';bpy.ops.render.render(write_still=True)
 pts={}
 for label,p in anchors.items():
  q=world_to_camera_view(scene,cam,Vector(p)*S);pts[label]=[round(q.x*1600),round((1-q.y)*1200)]
 json.dump(pts,open(OUT+'/'+name+'-anchors.json','w'))
# Save exterior, cutaway, exploded as fully editable separate states
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/pasta-cooker-assembled.blend');export('pasta-cooker-assembled')
render('exterior',{'Lift-off vented lid':(.1,.3,4.0),'Shape + portion control':(0,-1.8,2.7),'Clean water tank':(-1.65,-1,2),'Removable waste drawer':(1.64,-1.5,.85)})
visibility(['exterior','lid'],True)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/pasta-cooker-cutaway.blend');export('pasta-cooker-cutaway')
anchors={'01 Clean water':(-1.65,-1,2.5),'02 Salt dose':(1.67,.85,3.35),'03 Heated channel':(1.7,-.72,2.45),'04 Pasta basket':(.05,-.4,2.7),'05 Cooking vessel':(.05,.95,2),'06 Base heater':(.05,.3,1.02),'07 Guarded circulation':(1.4,1,2.0),'08 Drain / waste':(1.64,-.7,.85),'09 Lift + load cell':(.5,1.45,3.1),'10 Electrical isolation':(0,1.45,.7)}
render('cutaway',anchors)
# exploded offset functional groups; pipes remain reference route skeleton
for g,delta in {'tank':(-1.1,0,.3),'salt':(1,0,1.4),'basket':(0,0,2.6),'lid':(0,0,3.4),'heater':(1.5,-.4,.4),'waste':(1.4,-1.1,-.1),'electrical':(-1,-2.8,0)}.items():
 for o in groups[g]:o.location+=Vector(delta)*S
visibility(['lid'],False)
cam.data.ortho_scale=1.42;cam.location=(.98,-1.3,.94);cam.rotation_euler=(Vector((0,0,.36))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/pasta-cooker-exploded.blend');export('pasta-cooker-exploded')
render('exploded',{'Lift / drain basket':(.05,.3,5.5),'Removable lid':(.05,.3,7.3),'Water reservoir':(-2.75,.1,2.5),'Salt dosing module':(2.67,.85,4.7),'Channel heater module':(3.15,-.85,2.7),'Waste drawer':(3.04,-1.6,.75),'Wet / dry separation':(-1,-1.35,.7)})
print('ASSETS COMPLETE',bpy.app.version_string)
