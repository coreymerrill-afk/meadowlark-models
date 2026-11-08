from pathlib import Path
exec(compile((Path(__file__).parent/'build_print_candidate.py').read_text().split('parts=[];display=[]')[0],'candidate-foundation','exec'))
sequence=[]
# A finite-width envelope tests the entire straight insertion path, not snapshots.
def check(label,m,stationary,delta):
 length=np.linalg.norm(delta);axis=np.argmax(np.abs(delta));size=[.002,.002,.002];size[axis]=length+.002
 swept=m.minkowski_sum(box(*(np.array(delta)/2),*size));v=(swept^stationary).volume();sequence.append({'operation':label,'path_mm':list(delta),'interference_mm3':round(v,6)})
base=whole[('cabinet',-1)]+whole[('cabinet-top',-1)]
check('Lower separate cabinet deck onto frame',whole[('cabinet-top',-1)],whole[('cabinet',-1)],[0,0,100])
check('Lower ground floor onto base',whole[('body',0)],base,[0,0,300])
check('Fit complete porch from front before upper floor',whole[('porch',0)],base+whole[('body',0)],[0,-200,0])
stationary=base+whole[('body',0)]+whole[('porch',0)]
for f in (1,2,3):
 check(f'Lower storey {f+1}',whole[('body',f)],stationary,[0,0,300]);stationary=stationary+whole[('body',f)]
for f in range(4):check(f'Rear panel {f+1} straight removal',whole[('rear',f)],stationary,[0,100,0])
(OUT/'assembly-sequence-audit.json').write_text(json.dumps(sequence,indent=2));print(json.dumps(sequence,indent=2))
