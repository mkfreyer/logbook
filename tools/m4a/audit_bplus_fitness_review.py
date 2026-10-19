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
for v in ['baseline','soft','premium']:
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
