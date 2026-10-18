"""Verify B+ geometry, normals and surface masks survive studio preparation."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.root=a.root.resolve()
def signature():
    h=hashlib.sha256()
    for o in sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name):
        h.update(o.name.encode()+b'\0')
        for prop in ['m4a_role','m4a_render','m4a_variant']:
            h.update(json.dumps([prop,o.get(prop)],sort_keys=True).encode())
        for collection,prop,dtype,n in [(o.data.vertices,'co','<f4',3),(o.data.loops,'vertex_index','<i4',1),
                (o.data.polygons,'loop_total','<i4',1),(o.data.corner_normals,'vector','<f4',3)]:
            array=np.empty(len(collection)*n,dtype=dtype);collection.foreach_get(prop,array);h.update(array.tobytes())
        if o.get('m4a_role')=='body':
            for name in ['m4a_pectoral_mask','m4a_pectoral_L','m4a_pectoral_R']:
                attr=o.data.attributes[name];assert attr.domain=='POINT' and attr.data_type=='FLOAT'
                array=np.empty(len(attr.data),dtype='<f4');attr.data.foreach_get('value',array);h.update(array.tobytes())
    return h.hexdigest()
report={}
for v in ['../bplus-fitness/premium','power']:
    folder=a.root/v;c=json.loads((folder/'construction.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(folder/'model.blend'),use_scripts=False);before=signature()
    bpy.ops.wm.open_mainfile(filepath=str(folder/'scene-review.blend'),use_scripts=False);after=signature();assert before==after
    scene=bpy.context.scene;visible=[o for o in scene.objects if o.type=='MESH' and o.get('m4a_render')]
    assert len(visible)==c['counts']['objects']==3
    assert len([o for o in scene.objects if o.type=='LIGHT'])==4
    assert len([o for o in scene.objects if o.type=='CAMERA'])==1
    assert (scene.render.resolution_x,scene.render.resolution_y)==(720,1152)
    for o in visible:
        nodes=o.data.materials[0].node_tree.nodes
        assert nodes['M4A selection enabled'].outputs[0].default_value==0
        assert nodes['Principled BSDF'].inputs['Base Color'].is_linked
        assert any(n.type=='ATTRIBUTE' and n.attribute_name=='m4a_pectoral_mask' for n in nodes)
    report[v]={'source_review_geometry_normals_surface_masks_identical':True,'geometry_signature_sha256':before,
               'studio_lights':4,'camera_count':1,'neutral_material_restored':True,'visible_objects':len(visible)}
(a.root/'review-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('STUDIO_AUDIT',json.dumps(report),flush=True)

# Exact correspondence with the selected Premium: same topology and scalar masks.
def body_data(folder):
    bpy.ops.wm.open_mainfile(filepath=str(folder/'model.blend'),use_scripts=False)
    ob=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('m4a_role')=='body');m=ob.data
    xyz=np.empty(len(m.vertices)*3,dtype=np.float64);m.vertices.foreach_get('co',xyz);xyz=xyz.reshape(-1,3)
    normals=np.empty_like(xyz);m.vertices.foreach_get('normal',normals.ravel())
    h=hashlib.sha256()
    for collection,prop in [(m.loops,'vertex_index'),(m.polygons,'loop_total')]:
        array=np.empty(len(collection),dtype='<i4');collection.foreach_get(prop,array);h.update(array.tobytes())
    for name in ['m4a_pectoral_mask','m4a_pectoral_L','m4a_pectoral_R']:
        attr=m.attributes[name];array=np.empty(len(attr.data),dtype='<f4');attr.data.foreach_get('value',array);h.update(array.tobytes())
    return xyz,normals,h.hexdigest()
old,normals,topology=body_data(a.root/'../bplus-fitness/premium');new,_,other=body_data(a.root/'power')
assert topology==other and old.shape==new.shape
delta=new-old;x=np.abs(old[:,0]);y=old[:,1];z=old[:,2]
protected=(z<=.165)|(z>=1.548)|((x>=.430)&(z<=1.02))
assert np.max(np.abs(delta[protected]))==0
regions={
 'pectorals':(x>.025)&(x<.18)&(z>1.32)&(z<1.43)&(y<-.025),
 'deltoids':(x>.19)&(x<.30)&(z>1.38)&(z<1.48),
 'upper_arms':(x>.225)&(x<.35)&(z>1.18)&(z<1.33),
 'forearms':(x>.31)&(x<.405)&(z>1.02)&(z<1.12),
 'latissimus':(x>.055)&(x<.20)&(z>1.20)&(z<1.40)&(y>.07),
 'trapezius':(x<.17)&(z>1.40)&(z<1.51)&(y>.05),
 'abdomen_obliques':(x<.145)&(z>1.08)&(z<1.25)&(y<-.025),
 'quadriceps':(x>.06)&(x<.215)&(z>.59)&(z<.85)&(y<.02),
 'hamstrings':(x>.06)&(x<.215)&(z>.59)&(z<.85)&(y>.07),
 'calves':(x>.075)&(x<.22)&(z>.25)&(z<.43)}
metrics={}
for name,mask in regions.items():
    metrics[name]={'samples':int(mask.sum()),'mean_outward_offset_mm':float(np.mean(np.sum(delta[mask]*normals[mask],axis=1))*1000),
       'max_displacement_mm':float(np.linalg.norm(delta[mask],axis=1).max()*1000)}
comparison={'same_body_topology_and_three_surface_masks':True,'topology_masks_sha256':topology,
 'protected_head_hands_feet_vertices_unchanged':True,'protected_vertices':int(protected.sum()),
 'source_bounds':[old.min(0).tolist(),old.max(0).tolist()],'target_bounds':[new.min(0).tolist(),new.max(0).tolist()],
 'region_metrics':metrics,'method':'Corresponding original proxy vertices in fixed reference-coordinate windows; normal offsets are not circumference or muscle-volume measurements.'}
(a.root/'comparison-geometry.json').write_text(json.dumps(comparison,indent=2)+'\n')
print('PARENT_COMPARISON',json.dumps(comparison),flush=True)
