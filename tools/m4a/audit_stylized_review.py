"""Verify identical mesh geometry/normals/zone semantics in source and studio scenes."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.root=a.root.resolve()

def signature():
    h=hashlib.sha256()
    for o in sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o.name):
        h.update(o.name.encode()+b'\0')
        for prop in ['zone','role','selectable','render']:
            h.update(json.dumps([prop,o.get(prop)],sort_keys=True).encode())
        for collection,prop,dtype,n in [(o.data.vertices,'co','<f4',3),(o.data.loops,'vertex_index','<i4',1),
                                       (o.data.polygons,'loop_total','<i4',1),(o.data.corner_normals,'vector','<f4',3)]:
            array=np.empty(len(collection)*n,dtype=dtype);collection.foreach_get(prop,array);h.update(array.tobytes())
    return h.hexdigest()
report={}
for v in ['s1','s2','s3']:
    folder=a.root/v;c=json.loads((folder/'construction.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(folder/'model.blend'),use_scripts=False);before=signature()
    bpy.ops.wm.open_mainfile(filepath=str(folder/'scene-review.blend'),use_scripts=False);after=signature();assert before==after
    scene=bpy.context.scene;visible=[o for o in scene.objects if o.type=='MESH' and o.get('render')]
    assert len(visible)==c['counts']['visible_objects']
    assert len([o for o in scene.objects if o.type=='LIGHT'])==4
    assert len([o for o in scene.objects if o.type=='CAMERA'])==1
    assert (scene.render.resolution_x,scene.render.resolution_y)==(720,1152)
    for o in visible:
        color=o.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
        assert max(abs(float(x)-y) for x,y in zip(color,[.17,.245,.38,1]))<1e-6
    if v=='s1':assert bpy.data.objects['S1.hidden-continuous-source'].hide_render
    report[v]={'source_review_geometry_normals_semantics_identical':True,'geometry_signature_sha256':before,
               'studio_lights':4,'camera_count':1,'neutral_material_restored':True,'visible_objects':len(visible)}
(a.root/'review-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('STUDIO_AUDIT',json.dumps(report),flush=True)
