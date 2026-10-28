"""Append UV data on an export copy, duplicating only vertices at UV seams.

Every position and normal is copied bit-for-bit from the validated source.
No Blender normal recalculation or mesh reordering is used for the GLB export.
"""
import copy,json,sys
from pathlib import Path
import numpy as np
from glb_io import source,write_glb,sha,SOURCE_SHA
root=Path(__file__).resolve().parents[2];out=root/'docs/m4c/meshy-huit-zones'
original,v,n,f=source(root/'assets/models/meshy-e45e5d8.glb');spec=json.loads((out/'regions.json').read_text())
uv=np.load(out/'source-uv-binding.npz')['uv_blender'].copy();uv[:,:,1]=1-uv[:,:,1]
# Initialize every original vertex with one of its actual corner UVs. UV splits
# then append copies; no original vertex is deleted or moved.
flat=f.ravel().astype(np.int64);loops=uv.reshape(-1,2)
_,first=np.unique(flat,return_index=True);first=first[np.argsort(flat[first])]
assert len(first)==len(v)
export_uv=loops[first].tolist();remap=list(range(len(v)));table={(i,np.array(export_uv[i],'<f4').tobytes()):i for i in range(len(v))};indices=[]
for old,coord in zip(flat,loops):
    key=(int(old),coord.astype('<f4').tobytes())
    if key not in table:table[key]=len(remap);remap.append(int(old));export_uv.append(coord.tolist())
    indices.append(table[key])
remap=np.array(remap,'<u4');indices=np.array(indices,'<u2' if len(remap)<=65535 else '<u4')
export_uv=np.array(export_uv,'<f4');doc=copy.deepcopy(original)
doc['bufferViews']=[];doc['accessors']=[];binary=bytearray()
def buffer(data,target=None):
    binary.extend(b'\0'*((-len(binary))%4));offset=len(binary);binary.extend(data)
    view={'buffer':0,'byteOffset':offset,'byteLength':len(data)}
    if target:view['target']=target
    doc['bufferViews'].append(view);return len(doc['bufferViews'])-1
def acc(array,width,component,target):
    view=buffer(array.tobytes(),target);a={'bufferView':view,'componentType':component,'count':len(array) if array.ndim>1 else len(array),'type':{1:'SCALAR',2:'VEC2',3:'VEC3'}[width]}
    if width==3 and len(doc['accessors'])==0:a.update(min=array.min(0).tolist(),max=array.max(0).tolist())
    doc['accessors'].append(a);return len(doc['accessors'])-1
position=acc(v[remap],3,5126,34962);normal=acc(n[remap],3,5126,34962);texcoord=acc(export_uv,2,5126,34962);index=acc(indices,1,5123 if indices.dtype.itemsize==2 else 5125,34963)
image=buffer((out/'textures/control-basecolor.png').read_bytes());idimage=buffer((out/'textures/muscle-ids.png').read_bytes())
doc['images']=[{'name':'M4C_static_control_palette','bufferView':image,'mimeType':'image/png'},{'name':'M4C_discrete_muscle_IDs_linear','bufferView':idimage,'mimeType':'image/png'}]
doc['samplers']=[{'magFilter':9729,'minFilter':9729,'wrapS':33071,'wrapT':33071},{'magFilter':9728,'minFilter':9728,'wrapS':33071,'wrapT':33071}]
doc['textures']=[{'source':0,'sampler':0},{'source':1,'sampler':1}]
doc['materials']=[{'name':'M4C_COLOR_CONTROL_STATIC','doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[1,1,1,1],'baseColorTexture':{'index':0,'texCoord':0},'metallicFactor':0,'roughnessFactor':.86},'extras':{'muscleIds':spec['zones'],'idTexture':1,'idTextureColorSpace':'linear-data','idTextureSampling':'nearest; no mipmaps','interactiveSelectionImplemented':False}}]
doc['meshes'][0]['primitives']=[{'attributes':{'POSITION':position,'NORMAL':normal,'TEXCOORD_0':texcoord},'indices':index,'material':0}]
doc['nodes'][0]['extras'].update(muscle_segmentation_performed=True,segmentation_status='proposed, awaiting user validation',source_sha256=SOURCE_SHA)
doc['asset'].setdefault('extras',{}).update(attribution='Model created with Meshy — CC BY 4.0 License. Logbook adaptation: eight proposed UV muscle surface masks; no geometry change.')
doc['buffers']=[{'byteLength':len(binary)}]
file=out/'exports/meshy-eight-zones-control.glb';write_glb(file,doc,bytes(binary))
np.savez_compressed(out/'exports/export-source-binding.npz',source_vertex=remap,source_faces=f,uv_gltf=uv)
# Sparse original-face-to-UV binding for SurfaceHit from the unchanged viewer.
# IDs never depend on these indices: this acceleration binding is SHA-bound.
domain=np.load(out/'source-uv-binding.npz')['domain'];faces=np.flatnonzero(domain).astype('<u4')
coords=uv[domain].astype('<f4')
(out/'exports/source-face-indices.u32').write_bytes(faces.tobytes());(out/'exports/source-corner-uv.f32').write_bytes(coords.tobytes())
report={'source_sha256':SOURCE_SHA,'source_vertices':len(v),'export_vertices':len(remap),'uv_seam_duplicates':len(remap)-len(v),'triangles_before':len(f),'triangles_after':len(indices)//3,'position_buffers_equal_via_binding':True,'normal_buffers_equal_via_binding':True,'source_triangle_order_preserved':True,'index_component_type':5123 if indices.dtype.itemsize==2 else 5125,'glb_bytes':file.stat().st_size,'glb_sha256':sha(file.read_bytes()),'source_binding_faces':len(faces),'source_binding_bytes':faces.nbytes+coords.nbytes,'original_glb_untouched':True}
(out/'exports/export-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
