from pathlib import Path
import json,zipfile,xml.etree.ElementTree as E
import numpy as np,trimesh as tm,manifold3d as md
P=Path(__file__).parent/'print-candidate'
manifest=json.loads((P/'manifest.json').read_text()); ns={'m':'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
solids=[]
for part in manifest['parts']:
 if part['floor']==-2:continue
 with zipfile.ZipFile(P/part['file']) as z:r=E.fromstring(z.read('3D/3dmodel.model'))
 chunks=[]
 for mesh in r.findall('.//m:mesh',ns):
  vv=[[float(v.attrib[k]) for k in ('x','y','z')] for v in mesh.findall('m:vertices/m:vertex',ns)]
  ff=[[int(v.attrib[k]) for k in ('v1','v2','v3')] for v in mesh.findall('m:triangles/m:triangle',ns)]
  t=tm.Trimesh(vv,ff,process=False);t.apply_transform(part['assembly_from_print'])
  chunks.append(md.Manifold(md.Mesh(np.asarray(t.vertices,dtype=np.float32),np.asarray(t.faces,dtype=np.uint32))))
 solid=md.Manifold.batch_boolean(chunks,md.OpType.Add);solids.append((part,solid))
collisions=[]
for i,(a,am) in enumerate(solids):
 ab=np.array(a['bounds_mm'])
 for b,bm in solids[i+1:]:
  bb=np.array(b['bounds_mm'])
  if np.any(ab[1]<bb[0]-.01) or np.any(bb[1]<ab[0]-.01):continue
  v=(am^bm).volume()
  if v>.1:collisions.append({'a':a['id'],'b':b['id'],'volume_mm3':round(v,4)})
report={'source':'Reloaded actual exported 3MF material meshes, reconstructed using stored assembly transforms','parts_checked':len(solids),'collisions_over_0_1_mm3':collisions,'limitations':['No slicer or physical assembly validation','Surface finish and unsupported features still require visual inspection']}
(P/'exported-assembly-audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
