"""Extract immutable evaluated pass-three surfaces for local envelope reconstruction."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--work',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.work.mkdir(parents=True,exist_ok=True)
digest=hashlib.sha256(a.baseline.read_bytes()).hexdigest()
assert digest=='cfe710f5efd581922f46c0d25d4178cc81de74137fd2761716ad95516fdf13b8'
bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()),use_scripts=False);s=bpy.data.scenes['08_PASSE3_NEUTRE'];bpy.context.window.scene=s;s.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get();arrays={};rows=[]
for o in s.objects:
 if o.type!='MESH':continue
 m=bpy.data.meshes.new_from_object(o.evaluated_get(g),depsgraph=g);v=np.array([o.matrix_world@q.co for q in m.vertices]);f=np.array([q.vertices[:]for q in m.polygons]);key=o['asset_id'];arrays[key+'__v']=v;arrays[key+'__f']=f
 rows.append({'id':key,'source':o.get('source_piece_id'),'min':v.min(0).tolist(),'max':v.max(0).tolist(),'triangles':len(f)})
np.savez_compressed(a.work/'baseline.npz',**arrays)
(a.work/'parts.json').write_text(json.dumps({'baseline_sha256':digest,'parts':rows},indent=2)+'\n')
print('PASSE4_PREPARED',len(rows),flush=True)
