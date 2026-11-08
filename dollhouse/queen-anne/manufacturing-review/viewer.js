/* All visible house meshes come from the same solid parts exported in the print kit. */
(async function(){
 const host=document.getElementById('view'),status=document.getElementById('status');
 try{
  const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(Math.min(devicePixelRatio,1.6));renderer.setClearColor(0xe5e7e3);renderer.outputEncoding=THREE.sRGBEncoding;host.appendChild(renderer.domElement);
  const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(38,1,1,5000);camera.up.set(0,0,1);
  const controls=new THREE.OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.target.set(290,140,280);
  scene.add(new THREE.HemisphereLight(0xffffff,0x737165,.65));for(const [p,e] of [[[0,-600,900],.75],[[700,600,700],.4]]){const l=new THREE.DirectionalLight(0xffffff,e);l.position.set(...p);scene.add(l);}
  const meshes=[],refs=[];let mode='outside';
  function resize(){renderer.setSize(host.clientWidth,host.clientHeight);camera.aspect=host.clientWidth/host.clientHeight;camera.updateProjectionMatrix();}new ResizeObserver(resize).observe(host);resize();
  function pose(rear=false){camera.position.set(rear?1050:1050,rear?1300:-1050,800);controls.target.set(290,140,280);controls.update();}pose();
  (function tick(){requestAnimationFrame(tick);controls.update();renderer.render(scene,camera);})();
  status.textContent='Loading the clean house parts…';
  const [data,manifest]=await Promise.all([fetch('/dollhouse/queen-anne/manufacturing-review/scene.json').then(r=>{if(!r.ok)throw Error('Model file unavailable');return r.json();}),fetch('/dollhouse/queen-anne/manufacturing-review/manifest.json').then(r=>r.json())]);
  const selector=document.getElementById('part');
  for(let i=0;i<data.length;i++){
   const d=data[i],g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(d.positions,3));g.computeVertexNormals();
   const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({color:new THREE.Color(...d.color),roughness:.73,side:THREE.DoubleSide}));m.userData=d;scene.add(m);meshes.push(m);
   const op=document.createElement('option');op.value=d.id;op.textContent=d.id;selector.appendChild(op);
   if(i%12===0){status.textContent=`Loading parts ${i+1} / ${data.length}`;await new Promise(r=>setTimeout(r,0));}
  }
  // Caster placeholders are purchased hardware references, excluded from printable files.
  for(const x of [0,580])for(const y of [-25,325]){const m=new THREE.Mesh(new THREE.CylinderGeometry(12,12,8,20),new THREE.MeshStandardMaterial({color:0x555955}));m.position.set(x,y,0);scene.add(m);refs.push(m);}
  function update(){
   const f=document.getElementById('floor').value,extension=Number(document.getElementById('drawers').value),selected=selector.value;
   for(const m of meshes){const d=m.userData;let visible=true;
    if(mode==='inside'&&d.kind==='rear')visible=false;
    if(f!=='all'&&d.floor!==Number(f))visible=false;
    m.visible=visible;m.position.y=d.kind.startsWith('drawer-')?extension:0;
    m.material.emissive.setHex(selected===d.id?0x374e28:0);m.material.opacity=selected&&selected!==d.id?.27:1;m.material.transparent=!!selected&&selected!==d.id;
   }
   refs.forEach(r=>r.visible=f==='all');document.getElementById('travel').textContent=extension+' mm';
   const a=document.getElementById('part-download');a.hidden=!selected;if(selected){a.href='/dollhouse/queen-anne/manufacturing-review/parts/'+encodeURIComponent(selected.split('__')[0])+'.3mf';a.download=selected.split('__')[0]+'.3mf';}
  }
  document.getElementById('outside').onclick=()=>{mode='outside';document.getElementById('floor').value='all';selector.value='';pose();update();};
  document.getElementById('inside').onclick=()=>{mode='inside';document.getElementById('floor').value='all';selector.value='';pose(true);update();};
  document.getElementById('trimdetail').onclick=()=>{mode='outside';document.getElementById('floor').value='all';selector.value='';camera.position.set(970,430,530);controls.target.set(580,180,404);controls.update();update();};
  document.getElementById('roofjoin').onclick=()=>{mode='inside';document.getElementById('floor').value='all';selector.value='';camera.position.set(850,650,710);controls.target.set(500,310,510);controls.update();update();};
  document.getElementById('jointclose').onclick=()=>{mode='inside';document.getElementById('floor').value='all';selector.value='';camera.position.set(685,423,500);controls.target.set(578,327,445);controls.update();update();};
  document.getElementById('interior').onclick=()=>{mode='inside';document.getElementById('floor').value='all';selector.value='';camera.position.set(180,640,390);controls.target.set(560,265,285);controls.update();update();};
  document.getElementById('left').onclick=()=>{mode='outside';document.getElementById('floor').value='all';selector.value='';camera.position.set(-1000,-500,680);controls.target.set(210,140,300);controls.update();update();};
  document.getElementById('roofview').onclick=()=>{mode='outside';document.getElementById('floor').value='all';selector.value='';camera.position.set(900,-750,1100);controls.target.set(290,100,480);controls.update();update();};
  document.getElementById('top').onclick=()=>{camera.position.set(290,140,1400);controls.target.set(290,140,260);controls.update();};
  document.getElementById('floor').onchange=()=>{mode='inside';selector.value='';update();};document.getElementById('drawers').oninput=update;selector.onchange=update;
  document.getElementById('count').textContent=manifest.parts.length+' candidate sections · no furniture · millimetres · '+manifest.version;
  status.textContent='Ready — drag to orbit, scroll to zoom, right-drag to pan.';window.houseReview={loaded:true,parts:data.length,version:manifest.version,furniture:manifest.furniture_count};update();
 }catch(e){status.textContent='Could not load the model: '+e.message;console.error(e);}
})();
