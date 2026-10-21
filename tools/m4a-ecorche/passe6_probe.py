"""Extract the two published shoulder states and immutable body for pass-six authoring."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True)
assert hashlib.sha256(a.baseline.read_bytes()).hexdigest()=='926cadf61c4608c096cbf84e0c50ff0785eb7c5568d613206dfe57d695e4a54d'
bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()),use_scripts=False);arrays={};samples=[]
for label,scene_name in [('p4','10_PASSE4_NEUTRE'),('p5','12_PASSE5_NEUTRE')]:
 s=bpy.data.scenes[scene_name];bpy.context.window.scene=s;s.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get()
 for o in s.objects:
  if o.type!='MESH'or(label=='p4'and o.get('asset_id')not in ['deltoid.right','deltoid.left']):continue
  ev=o.evaluated_get(g);m=ev.to_mesh();v=np.array([o.matrix_world@x.co for x in m.vertices]);f=np.array([q.vertices[:]for q in m.polygons],int);ev.to_mesh_clear();key=label+'__'+o['asset_id'];arrays[key+'__v']=v;arrays[key+'__f']=f
  if o['asset_id']!='deltoid.right':continue
  tree=BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True)
  for z in [1.35,1.39,1.43,1.47]:
   t=np.clip((z-1.286)/.217,0,1);axis=np.array([-.241+.057*t,.080-.010*t,z]);row=[]
   for deg in [-150,-120,-90,-60,-30,0,30,60,90,120,150]:
    theta=np.deg2rad(deg);d=np.array([-np.cos(theta),np.sin(theta),0]);hit=tree.ray_cast(Vector(axis+.3*d),Vector(-d),.3)
    row.append([deg,round(.3-hit[3],4)if hit[0]is not None else None])
   samples.append({'pass':label,'z':z,'radius_m':row})
np.savez_compressed(a.output/'shoulder-baselines.npz',**arrays);(a.output/'radial-samples.json').write_text(json.dumps(samples,indent=2)+'\n');print(json.dumps(samples),flush=True)
