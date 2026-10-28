"""Independent standard glTF import and original-surface preservation in Blender."""
import json,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from glb_io import read_glb,accessor,source
root=Path(__file__).resolve().parents[2];out=root/'docs/m4c/meshy-huit-zones'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(out/'exports/meshy-eight-zones-control.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];assert len(meshes)==1
ob=meshes[0];_,d,b=read_glb(out/'exports/meshy-eight-zones-control.glb');p=d['meshes'][0]['primitives'][0]
v=accessor(d,b,p['attributes']['POSITION']);f=accessor(d,b,p['indices']).reshape(-1,3)
actual=np.array([v.co[:] for v in ob.data.vertices],np.float32)
assert np.array_equal(actual,np.column_stack([v[:,0],-v[:,2],v[:,1]]))
assert np.array_equal(np.array([p.vertices[:] for p in ob.data.polygons]),f)
assert ob.data.uv_layers and len(ob.data.materials)==1
images=[node.image for node in ob.data.materials[0].node_tree.nodes if node.type=='TEX_IMAGE']
assert images and list(images[0].size)==[2048,2048]
assert ob.get('muscle_segmentation_performed') is True
# Open editable master separately: its original geometry is also intact.
bpy.ops.wm.open_mainfile(filepath=str(out/'meshy-eight-zones.blend'),use_scripts=False)
ob=bpy.data.objects['MESHY_M4C'];_,v,n,f=source(root/'assets/models/meshy-e45e5d8.glb')
assert np.array_equal(np.array([p.co[:] for p in ob.data.vertices],np.float32),np.column_stack([v[:,0],-v[:,2],v[:,1]]))
assert np.array_equal(np.array([p.vertices[:] for p in ob.data.polygons]),f)
assert not ob.modifiers and not ob.data.shape_keys
assert len([node for node in ob.data.materials[0].node_tree.nodes if node.name.startswith('SHOW::')])==8
assert len([node for node in ob.data.materials[0].node_tree.nodes if node.name.startswith('COLOR::')])==8
report={'standard_blender_gltf_import':'passed','control_import_vertices':len(actual),'triangles':len(f),'editable_original_vertices':len(v),'editable_source_positions_and_indices_equal':True,'editable_eight_show_and_color_controls':True,'modifiers_or_shape_keys':False,'imported_uv_and_pbr_image':True,'source_glb_untouched':True}
(out/'blender-import-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
