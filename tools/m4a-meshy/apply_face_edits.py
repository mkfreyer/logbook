"""Apply an explicit local face-edit list to the existing editable Blender file.

No classifier, contour regeneration or geometry operation is performed here.
Every edit is checked against its prior material assignment and source face ID.
"""
import argparse,json,sys
from pathlib import Path
import bpy,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import load_glb,sha,EXPECTED_SHA
p=argparse.ArgumentParser(description=__doc__)
for key in ['blend','source','edits','output']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:])
raw,_,v,ix=load_glb(a.source);assert sha(raw)==EXPECTED_SHA
edit=json.loads(a.edits.read_text());assert edit['source_sha256']==EXPECTED_SHA
bpy.ops.wm.open_mainfile(filepath=str(a.blend.resolve()),use_scripts=False)
mesh=next(o.data for o in bpy.data.scenes['00_NEUTRE'].objects if o.type=='MESH')
assert np.array_equal(np.array([x.co[:] for x in mesh.vertices],dtype='<f4'),v)
assert np.array_equal(np.array([f.vertices[:] for f in mesh.polygons],dtype='<u4'),ix)
ids=np.array([d.value for d in mesh.attributes['source_triangle_index'].data]);assert np.array_equal(ids,np.arange(len(ix)))
labels=np.array([f.material_index for f in mesh.polygons],dtype=np.uint8)
assert sha(labels.tobytes())==edit['baseline_labels_sha256']
seen=set()
for row in edit['edits']:
 i=row['source_triangle'];assert i not in seen and 0<=i<len(ix);seen.add(i)
 assert int(labels[i])==row['from'] and row['to'] in range(4)
 mesh.polygons[i].material_index=row['to'];labels[i]=row['to']
mesh.attributes['muscle_zone'].data.foreach_set('value',labels.astype(np.int32))
assert sha(labels.tobytes())==edit['corrected_labels_sha256']
mat=bpy.data.materials['ORANGE_SELECTION'];orange=(1,.085,.006,1)
mat.diffuse_color=orange;n=mat.node_tree.nodes.get('Principled BSDF')
n.inputs['Base Color'].default_value=orange;n.inputs['Roughness'].default_value=.32
n.inputs['Metallic'].default_value=.08;n.inputs['Coat Weight'].default_value=.12
assert n.inputs['Emission Strength'].default_value==0
mesh.attributes.new('contour_review','INT','FACE')
review=np.zeros(len(ix),dtype=np.int32)
for row in edit['review_groups']:
 for i in row['source_triangles']:review[i]=row['value']
mesh.attributes['contour_review'].data.foreach_set('value',review)
text=bpy.data.texts.new('CORRECTION_FACES.json');text.write(json.dumps(edit,ensure_ascii=False,indent=2))
for name in ['LICENCE_ET_PROVENANCE.md','RAYCAST_ET_EXPORT.md']:
 assert bpy.data.texts.get(name),name
a.output.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(a.output.resolve()),compress=True)
print('EXPLICIT_FACE_EDITS_APPLIED',len(seen),flush=True)
