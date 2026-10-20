"""Export the exact source surface plus UVs and baked PBR selection textures.

Only vertices requiring different corner UVs are duplicated in the container.
The single primitive preserves original face order. No Blender exporter reorder.
"""
import argparse,copy,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import load_glb,sha,EXPECTED_SHA
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True);a=p.parse_args()
root=a.prepared.resolve();out=root/'texture-poc';raw,source,v,ix=load_glb(root/'source.glb');assert sha(raw)==EXPECTED_SHA
uv=np.frombuffer((out/'uv-loops.f32').read_bytes(),dtype='<f4').reshape(len(ix),3,2)
mask=np.array(Image.open(out/'textures/pectoralis-left-mask.png').convert('L'),dtype=float)/255
blue=np.array([.19,.28,.42]);orange=np.array([1,.085,.006]);linear=blue+(orange-blue)*mask[:,:,None]
srgb=np.where(linear<=.0031308,12.92*linear,1.055*np.power(linear,1/2.4)-.055)
Image.fromarray(np.rint(255*srgb).astype(np.uint8)).save(out/'textures/selected-basecolor-srgb.png')
orm=np.stack([.08+.04*mask,.37-.05*mask,.12-.04*mask],axis=2)
Image.fromarray(np.rint(255*orm).astype(np.uint8)).save(out/'textures/selected-coat-roughness-metallic-linear.png')
keys={};vertex_source=[];texcoords=[];indices=[]
for sid,t in zip(ix.ravel(),uv.reshape(-1,2)):
 key=(int(sid),*t.view('<u4').tolist())
 if key not in keys:
  keys[key]=len(vertex_source);vertex_source.append(int(sid));texcoords.append((float(t[0]),1-float(t[1])))
 indices.append(keys[key])
vertex_source=np.array(vertex_source,dtype='<u4');pos=v[vertex_source];indices=np.array(indices,dtype='<u4').reshape(-1,3);texcoords=np.array(texcoords,dtype='<f4')
face=np.cross(v[ix[:,1]].astype(float)-v[ix[:,0]],v[ix[:,2]].astype(float)-v[ix[:,0]]);normals=np.zeros(v.shape,float)
for i in range(3):np.add.at(normals,ix[:,i],face)
normals/=np.linalg.norm(normals,axis=1)[:,None];normals=normals[vertex_source].astype('<f4')
doc=copy.deepcopy(source);doc['asset']['copyright']='Model created with Meshy – CC BY 4.0 License'
blob=bytearray();doc['bufferViews']=[];doc['accessors']=[]
def view(data,target=None):
 while len(blob)%4:blob.append(0)
 row={'buffer':0,'byteOffset':len(blob),'byteLength':len(data)}
 if target:row['target']=target
 doc['bufferViews'].append(row);blob.extend(data);return len(doc['bufferViews'])-1
def accessor(array,kind,component,target):
 bv=view(array.tobytes(),target);row={'bufferView':bv,'componentType':component,'count':len(array),'type':kind}
 if kind=='VEC3' and len(doc['accessors'])==0:row.update(min=array.min(0).tolist(),max=array.max(0).tolist())
 doc['accessors'].append(row);return len(doc['accessors'])-1
position=accessor(pos,'VEC3',5126,34962);normal=accessor(normals,'VEC3',5126,34962);texcoord=accessor(texcoords,'VEC2',5126,34962);index=accessor(indices.ravel(),'SCALAR',5125,34963)
files=['selected-basecolor-srgb.png','selected-coat-roughness-metallic-linear.png','pectoralis-left-mask.png'];doc['images']=[]
for name in files:doc['images'].append({'bufferView':view((out/'textures'/name).read_bytes()),'mimeType':'image/png','name':name})
doc['samplers']=[{'magFilter':9729,'minFilter':9987,'wrapS':33071,'wrapT':33071}]
doc['textures']=[{'sampler':0,'source':i} for i in range(3)]
doc['extensionsUsed']=['KHR_materials_clearcoat']
doc['materials']=[{'name':'LEFT_PECTORAL_PAINTED_SELECTION_PBR_TEST','pbrMetallicRoughness':{'baseColorTexture':{'index':0},'metallicFactor':1,'roughnessFactor':1,'metallicRoughnessTexture':{'index':1}},
 'extensions':{'KHR_materials_clearcoat':{'clearcoatFactor':1,'clearcoatTexture':{'index':1},'clearcoatRoughnessFactor':.03}},
 'extras':{'logbook_selection_id':'pectoralis.left','logbook_mask_texture':2,'mask_threshold':.5,'mask_is_linear_data':True}}]
doc['meshes'][0]['primitives']=[{'attributes':{'POSITION':position,'NORMAL':normal,'TEXCOORD_0':texcoord},'indices':index,'material':0,'mode':4}]
doc['meshes'][0]['extras']={'logbook_source_sha256':EXPECTED_SHA,'logbook_source_triangle_order':'identity','logbook_vertex_to_source':'vertex-to-source.u32'}
doc['buffers']=[{'byteLength':len(blob)}];encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);blob+=b'\0'*((-len(blob))%4)
glb=struct.pack('<4sII',b'glTF',2,28+len(encoded)+len(blob))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(blob),0x004e4942)+blob
file=out/'export/meshy-painted-selection.glb';file.write_bytes(glb);mapfile=out/'export/vertex-to-source.u32';mapfile.write_bytes(vertex_source.tobytes())
assert np.array_equal(vertex_source[indices],ix) and pos.tobytes()==v[vertex_source].tobytes()
binding={'source_sha256':EXPECTED_SHA,'export_sha256':sha(glb),'file':file.name,'exporter_sha256':sha(Path(__file__).read_bytes()),'source_vertices':len(v),'export_vertices':len(pos),'uv_seam_duplicate_vertices':len(pos)-len(v),'triangles':len(ix),'primitive_count':1,
 'vertex_map_file':mapfile.name,'vertex_map_sha256':sha(vertex_source.tobytes()),'source_triangle_rule':'Single primitive 0: source_triangle = faceIndex. Actual serialized indices verified with vertex-to-source map. Not the old four-primitive GLB binding.',
 'uv_convention':'glTF UV = (Blender U, 1 - Blender V). PNG row zero is top. No further flip for GLTFLoader textures.',
 'selection_id':'pectoralis.left','mask_texture_index':2,'mask_filter':'linear with mipmaps, CLAMP_TO_EDGE','mask_color_space':'linear data, never sRGB',
 'material_textures':{name:sha((out/'textures'/name).read_bytes()) for name in files},'required_runtime_extension_for_coat':'KHR_materials_clearcoat (core PBR base color still works without coat)',
 'limitations':['Baked orange GLB is a static interchange test, not an interactive selection implementation.','Texture 2 is an unused-by-core mask referenced by extras; a future shader/CPU UV lookup must explicitly load it.','Local UV chart only; rest of body points at an unpainted texel. Not a full-body UV atlas.']}
(out/'export/export-binding.json').write_text(json.dumps(binding,ensure_ascii=False,indent=2)+'\n')
print('PAINTED_GLB_EXPORTED',json.dumps({'vertices':len(pos),'seam_duplicates':len(pos)-len(v),'triangles':len(ix),'bytes':len(glb)}))
