from pathlib import Path
import json,math,zipfile
import numpy as np
import trimesh as tm
import manifold3d as md
ROOT=Path(__file__).parent
OUT=ROOT/'print-candidate'
(OUT/'parts').mkdir(parents=True,exist_ok=True)
def box(x,y,z,sx,sy,sz):return md.Manifold.cube((sx,sy,sz),True).translate((x,y,z))
def cyl(x,y,z,r,h,axis='z'):
 a=md.Manifold.cylinder(h,r,r,24,True)
 if axis=='x':a=a.rotate((0,90,0))
 if axis=='y':a=a.rotate((90,0,0))
 return a.translate((x,y,z))
def union(xs):return md.Manifold.batch_boolean(xs,md.OpType.Add)
def meshof(m):
 q=m.to_mesh();return tm.Trimesh(np.asarray(q.vert_properties)[:,:3],np.asarray(q.tri_verts),process=False)
whole={};banks={}
for path in (ROOT/'assembly-cache').glob('*.npz'):
 name,f=path.stem.rsplit('_',1);d=np.load(path);m=md.Manifold(md.Mesh(np.array(d['vertices'],dtype=np.float32),np.array(d['faces'],dtype=np.uint32)))
 if name.startswith('paint-'):banks.setdefault(name[6:],{})[int(f)]=m
 else:whole[(name,int(f))]=m
# Treat fixed architecture as one design before cutting mutually exclusive assembly modules.
roof_mask=union([m for (k,f),m in whole.items() if k=='roof'])
oriel_roof=whole[('roof',1)].minkowski_sum(box(0,0,0,.12,.12,.12))
oriel_body=box(599,255,264,30,88,122)
fixed=union([m for (k,f),m in whole.items() if k in ('body','roof')])
for key in list(whole):
 if key[0] in ('body','roof'):del whole[key]
# Preserve the entire porch/gable as one architectural subassembly; never cut pendant
# ornaments at the storey plane. The broad rear/side butt faces are adhesive joints.
porch_region=box(413,-39,161.99,386,102,156.02)
whole[('porch',0)]=fixed^porch_region
fixed=fixed-box(413,-39,161.99,386.6,102.6,156.62)
# Ground-floor deck now rests above base; upper joints are explicit horizontal planes.
for f,(lo,hi) in enumerate([(83.98,203.85),(204.15,323.85),(324.15,443.85),(444.15,620)]):
 whole[('body',f)]=fixed ^ box(290,130,(lo+hi)/2,1400,1400,hi-lo)
# Lower the base-deck top to leave a 0.28mm adhesive line under ground floor.
whole[('cabinet',-1)]=whole[('cabinet',-1)] ^ box(290,130,-458.15,1400,1400,1083.7)
# Drawer backs had penetrated the cabinet front wall: move each drawer rearwards 2mm.
for k in ('drawer-left','drawer-right'):whole[(k,-1)]=whole[(k,-1)].translate((0,2,0))
# Continuous open-ended slide grooves: old grooves stopped short and jammed at travel.
for k,edges in [('drawer-left',(-21,283)),('drawer-right',(297,601))]:
 for edge in edges:
  x=edge+(1 if edge==edges[0] else -1)
  whole[(k,-1)]=whole[(k,-1)]-box(x,145,34,2.8,380,4)
# Clear rear faces through the cabinet opening with 0.3mm nominal side clearance.
for x in (131,451):whole[('cabinet',-1)]=whole[('cabinet',-1)]-box(x,450,48,307,257,52)
# Removable rear panels sit BEHIND the wall ends, not inside floors and corner boards.
for f in range(4):whole[('rear',f)]=whole[('rear',f)].translate((0,3.42,0))
# Vertical alignment dowels at bearing wall corners. Full pins are separate fit-test parts.
for f,z in enumerate((84,204,324,444)):
 for x in (2,578):
  for y in (50,300):
   hole=cyl(x,y,z,1.7,12.8)
   whole[('body',f)]=whole[('body',f)]-hole
   below=('cabinet',-1) if f==0 else ('body',f-1)
   whole[below]=whole[below]-hole
# Explicit dowel joints for broad base-deck seams and porch attachment.
for x in (190,410):
 for y in (100,260):whole[('cabinet',-1)]=whole[('cabinet',-1)]-cyl(x,y,80.35,1.7,12.8,'x')
for x in (100,350,500):whole[('cabinet',-1)]=whole[('cabinet',-1)]-cyl(x,150,80.35,1.7,12.8,'y')
for x in (260,350,500):
 for key in [('porch',0),('body',0)]:whole[key]=whole[key]-cyl(x,12.15,87,1.7,12.8,'y')
 for key in [('porch',0),('body',1)]:whole[key]=whole[key]-cyl(x,4,240.15,1.7,12.8)
# Each wide rear panel is assembled on a flat surface with dowels before mounting.
for f,z in enumerate((90,210,330,450)):
 for x in (190,410):
  for h in (20,90):whole[('rear',f)]=whole[('rear',f)]-cyl(x,333.42,z+h,1.7,12.8,'x')
# Rear panel screw clearance and matching fixed-wall pilots, lower three storeys.
# Use M2 screws only after fit coupon; not a strength certification.
for f,z in enumerate((90,210,330)):
 for x in (2,578):
  for h in (12,102):
   whole[('rear',f)]=whole[('rear',f)]-cyl(x,333.5,z+h,1.2,10,'y')
   whole[('body',f)]=whole[('body',f)]-cyl(x,324,z+h,.85,12,'y')
# Loft rear closes against the existing 6mm side walls; same reversible screw scheme.
for x in (47,533):
 for z in (462,546):
  whole[('rear',3)]=whole[('rear',3)]-cyl(x,333.5,z,1.2,10,'y')
  whole[('body',3)]=whole[('body',3)]-cyl(x,324,z,.85,12,'y')
roof_mask=roof_mask.minkowski_sum(box(0,0,0,.12,.12,.12))
# Unified colour masks preserve the Victorian finish across new physical seams.
paint_roof={}
paint_trim={f:union(list(banks.get('trim',{}).values())+list(banks.get('rooftrim',{}).values())) for f in range(4)}
paint_wood={f:union(list(banks.get('wood',{}).values())) for f in range(4)}
paint_accent={f:union(list(banks.get('accent',{}).values())) for f in range(4)}
# Separate the cabinet roof/deck from the open frame for accessible printing and assembly.
base=whole[('cabinet',-1)]
for x in (-26,290,606):
 for y in (50,280):base=base-cyl(x,y,77,1.7,11.8)
whole[('cabinet-top',-1)]=base^box(290,130,538.575,1400,1400,922.85)
whole[('cabinet',-1)]=base^box(290,130,-461.575,1400,1400,1076.85)
# Check saved design solids before export. Clearance audit samples drawer travel separately.
collisions=[]
keys=[k for k in whole if k[1]>=-1 and not k[0].startswith('lamp')]
for i,a in enumerate(keys):
 for b in keys[i+1:]:
  v=(whole[a]^whole[b]).volume()
  if v>.1:collisions.append({'a':str(a),'b':str(b),'volume_mm3':round(v,3)})
clearance=[]
for kind in ('drawer-left','drawer-right'):
 sweep=whole[(kind,-1)].minkowski_sum(box(0,85,0,.6,170.6,.6))
 v=(sweep^(whole[('cabinet',-1)]+whole[('cabinet-top',-1)])).volume()
 clearance.append({'drawer':kind,'continuous_travel_mm':170,'extra_clearance_mm':.3,'collision_mm3':round(v,6)})
travel=[]
for kind in ('drawer-left','drawer-right'):
 for distance in range(0,171,5):
  v=(whole[(kind,-1)].translate((0,distance,0))^(whole[('cabinet',-1)]+whole[('cabinet-top',-1)])).volume()
  if v>.1:travel.append({'drawer':kind,'travel_mm':distance,'collision_mm3':round(v,3)})
(OUT/'assembly-audit.json').write_text(json.dumps({'major_assembly_collisions':collisions,'drawer_sample_collisions':travel,'drawer_sampling_mm':5,'continuous_drawer_clearance':clearance,'limitations':['Rear screw retention and dowel joint strength require physical fit coupons','Physical fit and slicer verification outstanding']},indent=2))
(OUT/'fixed-components.json').write_text(json.dumps([{'volume':c.volume(),'bounds':meshof(c).bounds.tolist()} for c in fixed.decompose()],indent=2))
print('AUDIT',len(collisions),'static collisions',len(travel),'drawer collisions',flush=True)
for c in collisions+travel:print(c,flush=True)
(OUT/'ASSEMBLY.txt').write_text('DEVELOPMENT CANDIDATE - DO NOT PRINT. Assembly audit and attachment review ongoing. Preserve all originals. New fixed architectural union is partitioned at storey bearing planes; roof detailing retained. Loft rear attachment, joint strength and slicer review unresolved.')
parts=[];display=[];tiny=[];repairs=[]
palette={'teal':('#397C7C',[.041,.201,.201]),'ivory':('#F2E2C5',[.888,.761,.558]),'rose':('#B86C83',[.479,.150,.227]),'slate':('#65778E',[.130,.184,.270]),'walnut':('#9B785D',[.328,.188,.109]),'copper':('#B77F58',[.474,.212,.098])}
colors={'body':[.44,.59,.51],'roof':[.20,.27,.30],'cabinet':[.57,.38,.20],'rear':[.44,.59,.51],'drawer-left':[.54,.67,.58],'drawer-right':[.54,.67,.58],'service-cover':[.25,.3,.29]}
for (kind,f),m in whole.items():
 # Module cuts stay well inside the nominal 330 x 320 bed. Small parts remain whole.
 if f==-2 or kind=='service-cover':cells=[(-1000,1000,-1000,1000)]
 else:cells=[(a,b,c,d) for a,b in zip((-35,190,410),(190,410,620)) for c,d in ((-95,150),(150,352))]
 for ix,(a,b,c,d) in enumerate(cells):
  # 0.30 mm glue-line allowance between neighbouring large modules.
  aa=a+(.15 if a in (190,410) else 0);bb=b-(.15 if b in (190,410) else 0)
  cc=c+(.15 if c==150 else 0);dd=d-(.15 if d==150 else 0)
  cut=m ^ box((aa+bb)/2,(cc+dd)/2,300,bb-aa,dd-cc,2000)
  if cut.is_empty():continue
  for j,piece in enumerate(cut.decompose()):
   if piece.volume()<.02:continue
   piece=piece.simplify(.01)
   t=meshof(piece);bounds=t.bounds.copy();ext=t.extents
   ident=f'{kind}-F{f+1}-M{ix+1}-{j+1}'
   if piece.volume()<3:tiny.append(ident)
   # Lay the shortest dimension vertically; print orientation is an initial suggestion.
   axis=int(np.argmin(ext));rot=np.eye(4)
   if axis==0:rot=tm.transformations.rotation_matrix(math.pi/2,[0,1,0])
   if axis==1:rot=tm.transformations.rotation_matrix(math.pi/2,[1,0,0])
   t.apply_transform(rot);shift=t.bounds[0].copy();t.apply_translation(-shift)
   assert t.is_watertight and t.is_volume,(ident,t.is_watertight,t.volume,len(t.faces),ext.tolist())
   assert max(t.extents[:2])<310 and t.extents[2]<315,(ident,t.extents)
   # Closed colour volumes share one placement transform; no overlapping colour shells.
   material='slate' if kind=='roof' else ('walnut' if kind in ('cabinet','cabinet-top') else ('rose' if kind.startswith('drawer') else ('teal' if kind in ('body','porch','rear') else 'ivory')))
   chunks=[];remaining=piece
   masks=[]
   if kind=='roof':masks=[(paint_roof.get(f),'ivory')]
   if kind in ('body','porch'):masks= [(paint_accent.get(f),'rose'),(paint_trim.get(f),'ivory'),(paint_wood.get(f),'walnut'),(oriel_roof,'copper'),(oriel_body,'rose'),(roof_mask,'slate')]
   if masks:
    for mask,name in masks:
     if mask is None:continue
     c=remaining^mask
     if not c.is_empty() and c.volume()>.01:chunks.append((c,name));remaining=remaining-mask
   if not remaining.is_empty():chunks.append((remaining,material))
   import xml.etree.ElementTree as ET
   file=OUT/'parts'/f'{ident}.3mf';ns='http://schemas.microsoft.com/3dmanufacturing/core/2015/02'
   model=ET.Element('model',{'unit':'millimeter','xmlns':ns});res=ET.SubElement(model,'resources');bas=ET.SubElement(res,'basematerials',{'id':'1'})
   for name,(hexcol,col) in palette.items():ET.SubElement(bas,'base',{'name':name,'displaycolor':hexcol+'FF'})
   component_ids=[];volume_sum=0;material_names=[]
   for idx,(solid,name) in enumerate(chunks,2):
    cm=meshof(solid);assert cm.is_watertight and cm.is_volume,(ident,name)
    volume_sum+=cm.volume;cm.apply_transform(rot);cm.apply_translation(-shift)
    component_ids.append(idx);material_names.append(name);obj=ET.SubElement(res,'object',{'id':str(idx),'type':'model','name':ident+'-'+name,'pid':'1','pindex':str(list(palette).index(name))});mesh=ET.SubElement(obj,'mesh');vs=ET.SubElement(mesh,'vertices');fs=ET.SubElement(mesh,'triangles')
    for v in cm.vertices:ET.SubElement(vs,'vertex',dict(zip(('x','y','z'),(format(float(c),'.17g') for c in v))))
    for face in cm.faces:ET.SubElement(fs,'triangle',dict(zip(('v1','v2','v3'),map(str,face))))
    assembled=cm.copy();assembled.apply_translation(shift);assembled.apply_transform(np.linalg.inv(rot));q=assembled.triangles.reshape((-1,3))
    if f!=-2:display.append({'id':ident+'__'+name,'print_id':ident,'kind':kind,'floor':f,'color':palette[name][1],'positions':np.round(q,4).reshape(-1).tolist()})
   assert abs(volume_sum-piece.volume())<max(.05,piece.volume()*1e-4),(ident,'colour partition volume',volume_sum,piece.volume())
   assembly_id=100;assembly=ET.SubElement(res,'object',{'id':str(assembly_id),'type':'model','name':ident});components=ET.SubElement(assembly,'components')
   for idx in component_ids:ET.SubElement(components,'component',{'objectid':str(idx)})
   build=ET.SubElement(model,'build');ET.SubElement(build,'item',{'objectid':str(assembly_id)})
   with zipfile.ZipFile(file,'w',zipfile.ZIP_DEFLATED) as package:
    package.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
    package.writestr('_rels/.rels','<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    package.writestr('3D/3dmodel.model',ET.tostring(model,encoding='utf-8',xml_declaration=True))
   with zipfile.ZipFile(file) as package:doc=ET.fromstring(package.read('3D/3dmodel.model'))
   for mesh in doc.findall('.//{'+ns+'}mesh'):
    vv=[[float(v.attrib[k]) for k in ('x','y','z')] for v in mesh.findall('.//{'+ns+'}vertex')];ff=[[int(v.attrib[k]) for k in ('v1','v2','v3')] for v in mesh.findall('.//{'+ns+'}triangle')]
    verified=tm.Trimesh(vv,ff,process=False);assert verified.is_watertight and verified.is_volume,ident
   assert t.extents[0]+16<=330 and t.extents[1]+16<=320 and t.extents[2]<=325,(ident,'H3C brim fit')
   parts.append({'id':ident,'file':'parts/'+ident+'.3mf','kind':kind,'floor':f,'bounds_mm':bounds.tolist(),'assembly_from_print':(np.linalg.inv(rot)@tm.transformations.translation_matrix(shift)).tolist(),'print_size_mm':t.extents.round(3).tolist(),'volume_mm3':round(piece.volume(),3),'watertight':True,'materials':material_names,'color_partition_volume_delta_mm3':round(float(volume_sum-piece.volume()),6),'H3C_8mm_brim_fit':True})
   print('Part',ident,len(t.faces),flush=True)
manifest={'version':'2026-11-08-manufacturing-candidate','status':'NOT FOR PRINTING - assembly candidate under review','furniture_count':0,'base_mm':[640,440],'parts':parts,'tiny_detail_parts':tiny,'stl_cleanup':repairs,'constraints':['All 3MF meshes reloaded watertight and within 310mm XY /315mm Z.','Suggested orientations are not slicer-tested; supports and thin ornament require review.','Alignment pins and adhesive joints are not load-tested.','Drawer guides nominal0.4mm running clearance; M3x10 removable stop screws and4mm-long heat inserts require fit coupon.','Lighting is a5V low-voltage provision, no mains; select/test components before wiring.']}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));(OUT/'scene.json').write_text(json.dumps(display,separators=(',',':')))
with zipfile.ZipFile(OUT/'clean-print-kit.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in parts:z.write(OUT/p['file'],p['file'])
 z.write(OUT/'manifest.json','manifest.json')
 z.write(OUT/'ASSEMBLY.txt','ASSEMBLY.txt')
print('DONE',len(parts),'parts',len(tiny),'tiny details; scene MB',(OUT/'scene.json').stat().st_size/1e6,flush=True)


