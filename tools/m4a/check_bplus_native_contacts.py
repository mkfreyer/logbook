"""Inspect existing B+ head/foot crossings without relief or proxy decimation."""
import argparse,ast,hashlib,json
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(__import__('sys').argv[__import__('sys').argv.index('--')+1:])
repo=Path(__file__).resolve().parents[2];source=repo/'docs/m4a/alternatives/studio-realistic-plus/B-plus.blend'
bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False)
ob=max((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices))
graph=bpy.context.evaluated_depsgraph_get();mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(graph),depsgraph=graph);mesh.calc_loop_triangles()
ref=json.loads((repo/'docs/m4a/alternatives/studio-realistic-plus/render-metadata.json').read_text())['transform']
xyz=np.empty(len(mesh.vertices)*3,dtype=np.float64);mesh.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
m=np.array(ob.matrix_world);xyz=(xyz@m[:3,:3].T+m[:3,3]-np.array(ref['center']))*ref['uniform_scale']
ix=np.empty(len(mesh.loop_triangles)*3,dtype=np.int32);mesh.loop_triangles.foreach_get('vertices',ix);ix=ix.reshape(-1,3)
selected=np.any((xyz[ix][:,:,2]<.165)|(xyz[ix][:,:,2]>1.548),axis=1);ix=ix[selected]
code=(repo/'tools/m4a/check_bplus_fitness.py').read_text();node=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='crossings')
exec(compile(ast.Module(body=[node],type_ignores=[]),'<trusted-local-crossing-audit>','exec'))
result=crossings(xyz,ix)
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Original B+ evaluated Multires, head and feet only; no proxy decimation or relief',
        'tested_triangles':len(ix),'crossings':result}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(report,indent=2)+'\n')
print('NATIVE_CONTACTS',json.dumps({k:v for k,v in result.items() if k!='examples'}),flush=True)
