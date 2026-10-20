"""Export edited Blender face material IDs back onto the untouched source GLB order.

Run with Blender --background --disable-autoexec --python ... -- --blend ...
--source ... --metadata ... --output ... . No Blender exporter assumptions.
"""
import argparse,json,sys,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import EXPECTED_SHA,components,load_glb,neighbors,patch_topology,sha
p=argparse.ArgumentParser(description=__doc__)
for key in ['blend','source','metadata','output']:p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.output.mkdir(parents=True,exist_ok=True)
raw,doc,v,ix=load_glb(a.source);assert sha(raw)==EXPECTED_SHA
meta=json.loads(a.metadata.read_text());bpy.ops.wm.open_mainfile(filepath=str(a.blend.resolve()),use_scripts=False)
ob=next(o for o in bpy.data.scenes['00_NEUTRE'].objects if o.type=='MESH');mesh=ob.data
assert not ob.modifiers and not mesh.shape_keys
assert max(abs(ob.matrix_basis[i][j]-Matrix.Rotation(math.pi/2,4,'X')[i][j]) for i in range(4) for j in range(4))<1e-6
assert len(mesh.vertices)==len(v) and len(mesh.polygons)==len(ix)
assert np.array_equal(np.array([x.co[:] for x in mesh.vertices],dtype='<f4'),v),'Vertex edits are forbidden'
ids=np.array([d.value for d in mesh.attributes['source_triangle_index'].data]);assert np.array_equal(np.sort(ids),np.arange(len(ix)))
labels=np.zeros(len(ix),dtype=np.uint8)
for face in mesh.polygons:
 source_id=ids[face.index];assert tuple(face.vertices)==tuple(ix[source_id]),'Topology/corner order differs from source'
 assert face.material_index in range(4);labels[source_id]=face.material_index
adj=neighbors(ix);records=[]
for row in meta['regions']:
 stats=patch_topology(labels==row['value'],ix,adj);assert stats['single_disk'],(row['id'],stats)
 records.append({'id':row['id'],'value':row['value'],**stats})
file=a.output/'triangle-regions.u8';file.write_bytes(labels.tobytes());meta['labels'].update(file=file.name,sha256=sha(file.read_bytes()),byte_length=len(labels));meta['regions']=records
meta['method']='Editable Blender face material indices, explicitly mapped through source_triangle_index and checked against original vertex/triangle arrays.'
meta['blender_source_sha256']=sha(a.blend.read_bytes());meta['contours_sha256']=None
(a.output/'regions.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
print('REGIONS_SAVED',json.dumps(records),flush=True)
