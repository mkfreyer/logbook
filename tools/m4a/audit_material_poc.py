"""Prove zero geometry/original-UV changes and audit the four material maps."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.root.resolve();repo=Path(__file__).resolve().parents[2]
def signature(all_fields=False):
 h=hashlib.sha256();counts=[]
 for o in sorted((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:o.name):
  h.update(o.name.encode());m=o.data;m.calc_loop_triangles();counts.append(len(m.loop_triangles))
  for collection,prop,dtype,n in [(m.vertices,'co','<f4',3),(m.loops,'vertex_index','<i4',1),(m.polygons,'loop_total','<i4',1),(m.corner_normals,'vector','<f4',3)]:
   arr=np.empty(len(collection)*n,dtype=dtype);collection.foreach_get(prop,arr);h.update(arr.tobytes())
  for uv in m.uv_layers:
   if all_fields or uv.name=='UVMap':
    h.update(uv.name.encode());arr=np.empty(len(uv.data)*2,dtype='<f4');uv.data.foreach_get('uv',arr);h.update(arr.tobytes())
  if all_fields:
   for attr in sorted((v for v in m.attributes if v.name.startswith('m4a_')),key=lambda v:v.name):
    h.update((attr.name+attr.domain+attr.data_type).encode());arr=np.empty(len(attr.data),dtype='<f4' if attr.data_type=='FLOAT' else '<i4');attr.data.foreach_get('value',arr);h.update(arr.tobytes())
 return h.hexdigest(),counts
source=repo/'docs/m4a/bplus-power/power/model.blend';bpy.ops.wm.open_mainfile(filepath=str(source),use_scripts=False);before,counts=signature()
bpy.ops.wm.open_mainfile(filepath=str(root/'experiment/model.blend'),use_scripts=False);prepared,other=signature();assert prepared==before and other==counts and sum(counts)==112176
full,_=signature(True);body=bpy.data.objects['BPF.body'];assert [v.name for v in body.data.uv_layers]==['UVMap','M4A_visual_pectoral','M4A_visual_deltoid']
m=body.data.materials[0];nodes=m.node_tree.nodes;maps=[n for n in nodes if n.type=='TEX_IMAGE'];assert len(maps)==4
for n in maps:
 im=n.image;assert im.packed_file and im.colorspace_settings.name=='Non-Color' and tuple(im.size)==(1024,1024)
 path=root/'experiment/textures'/Path(im.filepath).name
 assert hashlib.sha256(bytes(im.packed_file.data)).hexdigest()==hashlib.sha256(path.read_bytes()).hexdigest()
assert len([n for n in nodes if n.type=='NORMAL_MAP'])==2
assert {int(n.inputs[1].default_value) for n in nodes if n.type=='MATH' and n.operation=='COMPARE'}=={1,2,3,4}
mask_counts={}
for name in ['m4a_mat_pec_L','m4a_mat_pec_R','m4a_mat_delt_L','m4a_mat_delt_R']:
 values=np.array([v.value for v in body.data.attributes[name].data]);assert np.isfinite(values).all() and values.min()>=0 and values.max()<=1 and np.any(values>.5);mask_counts[name]=int((values>.5).sum())
bpy.ops.wm.open_mainfile(filepath=str(root/'renders/scene-review.blend'),use_scripts=False);assert signature(True)[0]==full
assert bpy.data.objects['BPF.body'].data.materials[0].node_tree.nodes['M4A selected region'].outputs[0].default_value==0
report={'verdict':'approche insuffisante','source_prepared_geometry_normals_original_UV_identical':True,'geometry_signature_sha256':before,
 'source_review_all_geometry_UV_masks_identical':True,'visible_triangles':112176,'added_triangles':0,'objects':3,'original_UV_preserved':True,'added_UV_sets':2,
 'packed_noncolor_maps_verified':4,'normal_maps':2,'surface_maps':2,'regional_masks':mask_counts,'selection_ids':[1,2,3,4],
 'no_source_mesh_self_intersections_changed':True,'source_geometry_audit':'../bplus-power/power/geometry-check.json',
 'mobile_runtime_measured':False,'application_integration':False,'commercial_cost_eur':0}
(root/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('MATERIAL_AUDIT',json.dumps(report),flush=True)
