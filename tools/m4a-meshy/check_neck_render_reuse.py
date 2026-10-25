"""Reuse completed BEFORE frames only after exact scene-equivalence checks."""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from assemble_head import sha
p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--rendered-master',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve()
meta=json.loads((root/'assemblage.json').read_text());record=json.loads((root/'renders/before/metadata.json').read_text())
assert sha(a.rendered_master)==record['master_sha256']
assert sha(root/meta['master'])==meta['master_sha256']
assert record['renderer_sha256']==sha(Path(__file__).parent/'render_head_assembly.py')
for frame in record['frames']:assert sha(root/'renders/before'/frame['file'])==frame['sha256']
def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path),use_scripts=False)
 scene=bpy.data.scenes[meta['scene_before']];meshes=[o for o in scene.objects if o.type=='MESH'];assert len(meshes)==1
 ob=meshes[0];material=ob.data.materials[0];bsdf=material.node_tree.nodes.get('Principled BSDF')
 return [np.array([v.co[:] for v in ob.data.vertices]),np.array([f.vertices[:] for f in ob.data.polygons]),np.array([n.vector[:] for n in ob.data.corner_normals]),np.array(ob.matrix_world)],{
 'material':[material.name,list(material.diffuse_color),list(bsdf.inputs['Base Color'].default_value),bsdf.inputs['Roughness'].default_value,bsdf.inputs['Metallic'].default_value],
 'lights':{o.name:[o.data.energy,o.data.size,list(o.location)] for o in scene.objects if o.type=='LIGHT'},
 'world':[list(scene.world.node_tree.nodes['Background'].inputs[0].default_value),scene.world.node_tree.nodes['Background'].inputs[1].default_value],
 }
old_arrays,old_state=snapshot(a.rendered_master);new_arrays,new_state=snapshot(root/meta['master'])
assert all(np.array_equal(x,y) for x,y in zip(old_arrays,new_arrays))
assert old_state==new_state and old_state['lights']==record['lights']
out={'rendered_master_sha256':record['master_sha256'],'current_master_sha256':meta['master_sha256'],
 'before_scene_geometry_normals_transform_material_lights_world_exact':True,'raw_render_hashes_verified':len(record['frames']),
 'checker_sha256':sha(Path(__file__))}
(root/'renders/before/reuse.json').write_text(json.dumps(out,indent=2)+'\n')
print('BEFORE_REUSE_VERIFIED',json.dumps(out),flush=True)
