from pathlib import Path
exec(compile((Path(__file__).parent/'build_print_candidate.py').read_text().split('parts=[];display=[]')[0],'candidate-foundation','exec'))
T=OUT/'test-pieces';T.mkdir(exist_ok=True)
items=[]
def save(name,m,rotation=(0,0,0)):
 m=m.rotate(rotation);t=meshof(m);t.apply_translation(-t.bounds[0]);assert t.is_watertight and t.volume>0,name
 t.export(T/(name+'.stl'));items.append({'file':name+'.stl','size_mm':t.extents.round(3).tolist(),'volume_mm3':round(t.volume,3)})
floor=whole[('body',0)]
save('01-floor-joint-left',floor^box(183.925,100,87,11.85,18,6.04))
save('02-floor-joint-right',floor^box(196.075,100,87,11.85,18,6.04))
save('03-alignment-pin-3mm',cyl(0,0,5.6,1.5,11.2))
save('04-actual-drawer-guide',whole[('cabinet',-1)]^box(-23,100,34,10,40,12),(0,0,0))
save('05-actual-drawer-runner',whole[('drawer-left',-1)]^box(-19,100,34,6,30,12),(0,0,0))
save('06-rear-panel-screw-hole',whole[('rear',0)]^box(7,333.42,102,14,8,18),(90,0,0))
save('07-frame-screw-pilot',whole[('body',0)]^box(2,323,102,13,14,18),(0,0,0))
save('08-window-ornament-detail',whole[('body',2)]^box(582,255,428,16,72,16),(0,0,0))
save('09-roof-slate-detail',whole[('body',3)]^box(562,150,490,26,38,54),(0,-math.degrees(math.atan2(114,45)),0))
save('10-cabinet-deck-bearing',whole[('cabinet',-1)]^box(-26,50,73.425,12,18,6.85))
save('11-cabinet-deck-socket',whole[('cabinet-top',-1)]^box(-26,50,80.425,16,18,6.55))
(T/'manifest.json').write_text(json.dumps(items,indent=2))
print('TEST PIECES',json.dumps(items),flush=True)
