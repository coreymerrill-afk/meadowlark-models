// v3 CAD gallery: loads real STLs (binary) into a small studio viewer.
(function(){
const P=[['weathervane_v3','Rooster weathervane','Ball-and-spire mast, N/E/S/W letters, Ø3.2 LED bore. 77 × 54 × 113'],
['porte_cochere_v3','Porte-cochère','Clustered columns, segmental arches, balustraded deck, lantern pockets. 236 × 128 × 146'],
['spiral_stair_v3','Spiral stair','Newel, 16 wedge treads, helical rail on balusters, one story tall. 80 × 80 × 152'],
['stained_bay_v3','Stained-glass bay','Canted bay, three rose-glass lights + transoms, dome cap, corbels. 132 × 52 × 127'],
['door_surround_v3','Ornate door surround','Fluted pilasters, sunburst fanlight, broken pediment + urn. 90 × 9 × 127'],
['garden_gate_v3','Garden gate','Scrolled iron double gate, stone piers, lantern caps with Ø3.2 bores. 166 × 30 × 153'],
['lamppost_cluster_v3','Lamppost cluster','Fluted post, three scrolled arms with globes + crown globe, LED bores. 69 × 77 × 228'],
['roof_cresting_v3','Roof cresting','Fleur-de-lis + spear iron ridge cresting, clips on the Ø6 ridge roll. 254 long'],
['mansard_panel_v3','Mansard panel','Fish-scale shingle slope panel, prints flat. Closes the v2 viewer-only gap. 254 × 96'],
['finial_spire_v3','Spire finial','Ball, collar, and lancet for turret caps and gables, LED tip bore. 79 tall'],
['stained_insert_rose_v3_lead','Stained insert: rose (lead)','Prints with *_glass in translucent PETG, H3C tool swap. See the 3MF plate.'],
['stained_insert_tulip_v3_lead','Stained insert: tulip (lead)','Arched 22 × 44 light, press-fit lip.'],
['stained_insert_sunburst_v3_lead','Stained insert: sunburst (lead)','Arched 22 × 44 light, press-fit lip.']];
const el=document.getElementById('gal'),grid=document.getElementById('galgrid'),info=document.getElementById('galinfo');if(!el||!window.THREE)return;
let R,S,C,O,mesh,inited=false,glassMesh;
function parse(buf){const dv=new DataView(buf),n=dv.getUint32(80,true),pos=new Float32Array(n*9),nor=new Float32Array(n*9);let o=84;
  for(let i=0;i<n;i++){const nx=dv.getFloat32(o,true),ny=dv.getFloat32(o+4,true),nz=dv.getFloat32(o+8,true);o+=12;for(let v=0;v<3;v++){pos[i*9+v*3]=dv.getFloat32(o,true);pos[i*9+v*3+1]=dv.getFloat32(o+4,true);pos[i*9+v*3+2]=dv.getFloat32(o+8,true);nor[i*9+v*3]=nx;nor[i*9+v*3+1]=ny;nor[i*9+v*3+2]=nz;o+=12;}o+=2;}
  const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(pos,3));g.setAttribute('normal',new THREE.BufferAttribute(nor,3));g.rotateX(-Math.PI/2);g.computeBoundingBox();return g;}
function init(){if(inited)return;inited=true;R=new THREE.WebGLRenderer({antialias:true});R.setPixelRatio(Math.min(devicePixelRatio,2));R.outputEncoding=THREE.sRGBEncoding;R.toneMapping=THREE.ACESFilmicToneMapping;el.appendChild(R.domElement);
  S=new THREE.Scene();C=new THREE.PerspectiveCamera(32,1,1,5000);O=new (THREE.OrbitControls||window.OrbitControls)(C,R.domElement);O.enableDamping=true;O.autoRotate=true;O.autoRotateSpeed=1.2;
  S.add(new THREE.HemisphereLight(0xfff1dc,0x30283a,.8));const k=new THREE.DirectionalLight(0xffe2b8,1.4);k.position.set(200,300,200);S.add(k);const r=new THREE.DirectionalLight(0x9fc0ff,.7);r.position.set(-300,120,-250);S.add(r);
  const fit=()=>{const w=el.clientWidth,h=el.clientHeight;if(!w)return;R.setSize(w,h,false);R.domElement.style.width='100%';R.domElement.style.height='100%';C.aspect=w/h;C.updateProjectionMatrix();};addEventListener('resize',fit);fit();
  (function L(){requestAnimationFrame(L);if(!el.offsetParent)return;O.update();R.render(S,C);})();}
const M=new THREE.MeshStandardMaterial({color:0xe8c468,metalness:.55,roughness:.38}),MG=new THREE.MeshStandardMaterial({color:0xa855f7,emissive:0x7c3aed,emissiveIntensity:.5,transparent:true,opacity:.85,roughness:.1});
async function load(i){init();const [id,name,desc]=P[i];[...grid.children].forEach((b,k)=>b.classList.toggle('on',k==i));info.innerHTML=`<b>${name}</b>: ${desc} · <a href="/dollhouse/stl/${id}.stl" download>Download STL</a>`+(id.includes('stained')?' · <a href="/dollhouse/stl/stained_inserts_plate_v3.3mf" download>3MF plate</a>':'');
  const g=parse(await (await fetch('/dollhouse/stl/'+id+'.stl')).arrayBuffer());if(mesh){S.remove(mesh);mesh.geometry.dispose();}if(glassMesh){S.remove(glassMesh);glassMesh=null;}
  const b=g.boundingBox,c=b.getCenter(new THREE.Vector3()),sz=b.getSize(new THREE.Vector3());g.translate(-c.x,-b.min.y,-c.z);mesh=new THREE.Mesh(g,M);S.add(mesh);
  if(id.endsWith('_lead')){const gg=parse(await (await fetch('/dollhouse/stl/'+id.replace('_lead','_glass')+'.stl')).arrayBuffer());gg.translate(-c.x,-b.min.y,-c.z);glassMesh=new THREE.Mesh(gg,MG);S.add(glassMesh);}
  const r=sz.length()/2;O.target.set(0,sz.y/2,0);C.position.set(r*1.6,sz.y/2+r*.9,r*1.9);}
P.forEach((p,i)=>{const b=document.createElement('button');b.textContent=p[1];b.onclick=()=>load(i);grid.appendChild(b);});
window.__gal=()=>{if(!inited)load(0);};
})();
(function(){const k=document.getElementById('kit');if(!k)return;const go=()=>{if(!k.hidden&&window.__gal)window.__gal();};new MutationObserver(go).observe(k,{attributes:true,attributeFilter:['hidden']});go();})();
