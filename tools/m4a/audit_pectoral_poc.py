"""Audit the bounded experiment without equating geometric checks with visual success."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.root.resolve();repo=Path(__file__).resolve().parents[2]
def coordinates(o):
    q=np.empty(len(o.data.vertices)*3,dtype=np.float64);o.data.vertices.foreach_get('co',q);return q.reshape(-1,3)
def signature():
    h=hashlib.sha256()
    for o in sorted((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:o.name):
        h.update(o.name.encode())
        for collection,prop,dtype,n in [(o.data.vertices,'co','<f4',3),(o.data.loops,'vertex_index','<i4',1),(o.data.polygons,'loop_total','<i4',1),(o.data.corner_normals,'vector','<f4',3)]:
            arr=np.empty(len(collection)*n,dtype=dtype);collection.foreach_get(prop,arr);h.update(arr.tobytes())
        for attr in sorted((v for v in o.data.attributes if v.name.startswith('m4a_')),key=lambda v:v.name):
            h.update((attr.name+attr.domain+attr.data_type).encode());arr=np.empty(len(attr.data),dtype='<f4' if attr.data_type=='FLOAT' else '<i4');attr.data.foreach_get('value',arr);h.update(arr.tobytes())
    return h.hexdigest()
parent=repo/'docs/m4a/bplus-power/power/model.blend'
bpy.ops.wm.open_mainfile(filepath=str(parent),use_scripts=False)
old=coordinates(bpy.data.objects['BPF.body']);eyes={o.name:coordinates(o) for o in bpy.context.scene.objects if o.type=='MESH' and o.get('m4a_role')=='eye'}
bpy.ops.wm.open_mainfile(filepath=str(root/'experiment/model.blend'),use_scripts=False)
body=bpy.data.objects['BPF.body'];new=coordinates(body)
x=np.abs(old[:,0]);y=old[:,1];z=old[:,2]
allowed=((x<.244)&(y<.020)&(z>1.282)&(z<1.482))|((old[:,0]<-.166)&(old[:,0]>-.321)&(np.abs(y-.025)<.124)&(z>1.294)&(z<1.512))
assert np.array_equal(old[~allowed],new[:len(old)][~allowed])
for name,xyz in eyes.items():assert np.array_equal(xyz,coordinates(bpy.data.objects[name]))
ids=np.array([v.value for v in body.data.attributes['m4a_poc_region_id'].data]);zone_counts={name:int((ids==i).sum()) for i,name in [(1,'pectoralis.left'),(2,'pectoralis.right'),(3,'deltoid.right')]}
assert all(v>0 for v in zone_counts.values()) and set(np.unique(ids))=={0,1,2,3}
height=np.array([v.value for v in body.data.attributes['m4a_poc_fibre_height'].data]);before=signature()
bpy.ops.wm.open_mainfile(filepath=str(root/'after/scene-review.blend'),use_scripts=False);assert signature()==before
nodes=bpy.data.objects['BPF.body'].data.materials[0].node_tree.nodes
for zone in zone_counts:assert nodes['Select '+zone].outputs[0].default_value==0
# Verify every selector is separately controllable, with the other two off.
for zone in zone_counts:
    nodes['Select '+zone].outputs[0].default_value=1
    assert sum(nodes['Select '+z].outputs[0].default_value for z in zone_counts)==1
    nodes['Select '+zone].outputs[0].default_value=0
geometry=json.loads((root/'experiment/geometry-check.json').read_text());assert geometry['all_objects_closed_single_component_genus_zero']
report={'verdict':'méthode insuffisante','original_vertices_outside_scope_unchanged':int((~allowed).sum()),'outside_scope_max_coordinate_error_m':0,
 'two_eyes_unchanged':True,'source_review_geometry_normals_surface_attributes_identical':True,'geometry_signature_sha256':before,
 'independent_selectors_verified':list(zone_counts),'face_region_ids':{'0':'unassigned','1':'pectoralis.left','2':'pectoralis.right','3':'deltoid.right'},
 'zone_triangles':zone_counts,'maximum_scalar_fibre_height_m':float(height.max()),
 'selection_semantics':'Three independent point-mask shader controls; disjoint provisional integer face IDs for the same regions. Borders are approximate, not final anatomical segmentation.',
 'geometry_checks_are_not_visual_success':True,'application_integration':False}
(root/'audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('POC_AUDIT',json.dumps(report),flush=True)
