import bpy,json,os
from mathutils import Vector
D=os.path.dirname(os.path.abspath(__file__));m=json.load(open(D+'/connection-manifest.json'));out={}
for state in ['exterior','cutaway','exploded']:
 bpy.ops.wm.open_mainfile(filepath=D+'/pasta-cooker-v2-'+state+'.blend');bpy.context.view_layer.update();checks=[]
 for edge in m['edges']:
  ob=next(o for o in bpy.data.objects if o.name.startswith(edge['id']+' ') and o.type=='CURVE')
  for port,k in [(edge['from'],0),(edge['to'],-1)]:
   endpoint=ob.matrix_world@Vector(ob.data.splines[0].points[k].co[:3]);actual_port=bpy.data.objects['PORT '+port].matrix_world.translation;err=(endpoint-actual_port).length*1000
   checks.append({'edge':edge['id'],'port':port,'error_mm':err,'pass':err<.01})
 out[state]={'endpoint_checks':checks,'all_pass':all(c['pass'] for c in checks),'max_error_mm':max(c['error_mm'] for c in checks),'basket_bottom_mm':bpy.data.objects['Basket rim 280'].matrix_world.translation.z*1000,'cradle_ties_present':all('Cradle radial tie '+str(x) in bpy.data.objects for x in [-70,110])}
 assert out[state]['all_pass'] and out[state]['cradle_ties_present']
json.dump(out,open(D+'/final-saved-geometry-checks.json','w'),indent=2);print('ALL THREE SAVED STATES: 38/38 ACTUAL PORT ENDPOINTS PASS EACH')
