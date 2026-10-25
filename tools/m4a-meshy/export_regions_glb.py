"""Pack four material primitives without changing a vertex or a source triangle.

Triangle order changes explicitly; a checked primitive-local -> original-triangle
map is emitted. The supplied source GLB is never overwritten.
"""
import argparse,copy,json,struct
from pathlib import Path
import numpy as np
from mesh_io import EXPECTED_SHA,load_glb,sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--regions',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
raw,original,v,ix=load_glb(a.source);meta=json.loads(a.regions.read_text());assert sha(raw)==meta['source_sha256']==EXPECTED_SHA
labels=np.frombuffer((a.regions.parent/meta['labels']['file']).read_bytes(),dtype=np.uint8)
assert len(labels)==len(ix) and sha(labels.tobytes())==meta['labels']['sha256'] and set(labels)=={0,1,2,3}
ids={0:'unassigned',**{r['value']:r['id'] for r in meta['regions']}}
parts=[np.flatnonzero(labels==value).astype('<u4') for value in range(4)]
permutation=np.concatenate(parts);assert np.array_equal(np.sort(permutation),np.arange(len(ix)))
position_bytes=v.astype('<f4').tobytes();render_indices=ix[permutation].astype('<u4')
# Presentation normals only: same 47,711 positions and no duplicate vertices.
face_normals=np.cross(v[ix[:,1]].astype(np.float64)-v[ix[:,0]],v[ix[:,2]].astype(np.float64)-v[ix[:,0]])
normals=np.zeros(v.shape,dtype=np.float64)
for corner in range(3):np.add.at(normals,ix[:,corner],face_normals)
length=np.linalg.norm(normals,axis=1);assert np.all(length>0)
normals=(normals/length[:,None]).astype('<f4');binary=position_bytes+render_indices.tobytes()+normals.tobytes()
doc=copy.deepcopy(original);doc['asset']['copyright']='Model created with Meshy – CC BY 4.0 License'
doc['buffers']=[{'byteLength':len(binary)}]
doc['bufferViews']=[{'buffer':0,'byteOffset':0,'byteLength':len(position_bytes),'target':34962},
 {'buffer':0,'byteOffset':len(position_bytes),'byteLength':render_indices.nbytes,'target':34963},
 {'buffer':0,'byteOffset':len(position_bytes)+render_indices.nbytes,'byteLength':normals.nbytes,'target':34962}]
position=copy.deepcopy(original['accessors'][0]);position['bufferView']=0;position.pop('byteOffset',None)
doc['accessors']=[position];doc['materials']=[];primitives=[];primitive_map=[];start=0
for value,source_ids in enumerate(parts):
 count=len(source_ids);doc['accessors'].append({'bufferView':1,'byteOffset':start*12,'componentType':5125,'count':count*3,'type':'SCALAR'})
 doc['materials'].append({'name':ids[value],'pbrMetallicRoughness':{'baseColorFactor':[.19,.28,.42,1],'metallicFactor':.12,'roughnessFactor':.37}})
 primitives.append({'attributes':{'POSITION':0},'indices':value+1,'material':value,'mode':4,
  'extras':{'logbook_region':ids[value],'logbook_value':value}})
 primitive_map.append({'primitive_index':value,'region_value':value,'region_id':ids[value],'map_triangle_offset':start,'triangle_count':count})
 start+=count
normal_accessor=len(doc['accessors']);doc['accessors'].append({'bufferView':2,'componentType':5126,'count':len(v),'type':'VEC3'})
for primitive in primitives:primitive['attributes']['NORMAL']=normal_accessor
doc['meshes'][0]['primitives']=primitives
doc['meshes'][0]['extras']={'logbook_source_sha256':EXPECTED_SHA,'logbook_triangle_map':'draw-triangle-to-source.u32'}
json_bytes=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();json_bytes+=b' '*((-len(json_bytes))%4)
binary+=b'\0'*((-len(binary))%4)
output=struct.pack('<4sII',b'glTF',2,12+8+len(json_bytes)+8+len(binary))+struct.pack('<II',len(json_bytes),0x4e4f534a)+json_bytes+struct.pack('<II',len(binary),0x004e4942)+binary
file=a.output/'meshy-zones.glb';assert file.resolve()!=a.source.resolve();file.write_bytes(output)
mapfile=a.output/'draw-triangle-to-source.u32';mapfile.write_bytes(permutation.tobytes())
# Read back the actual serialized buffers, including primitive-local offsets.
n=struct.unpack_from('<I',output,12)[0];loaded=json.loads(output[20:20+n]);blob=output[28+n:]
read_positions=np.frombuffer(blob,dtype='<f4',count=len(v)*3).reshape(-1,3);assert np.array_equal(read_positions,v)
for row in primitive_map:
 ac=loaded['accessors'][row['primitive_index']+1];offset=loaded['bufferViews'][1]['byteOffset']+ac['byteOffset']
 faces=np.frombuffer(blob,dtype='<u4',count=ac['count'],offset=offset).reshape(-1,3)
 start=row['map_triangle_offset'];source_ids=permutation[start:start+row['triangle_count']]
 assert np.array_equal(faces,ix[source_ids]) and np.all(labels[source_ids]==row['region_value'])
report={'source_sha256':EXPECTED_SHA,'export_file':file.name,'export_sha256':sha(file.read_bytes()),
 'map_file':mapfile.name,'map_dtype':'uint32 little-endian','map_sha256':sha(mapfile.read_bytes()),
 'rule':'sourceTriangle = map[primitive.map_triangle_offset + raycast.faceIndex]; region = sourceLabels[sourceTriangle].',
 'source_vertex_count':len(v),'source_triangle_count':len(ix),'shared_position_accessors':1,
 'smooth_normals_added_without_vertex_duplication':True,'position_bytes_equal_source':True,'all_source_triangles_exactly_once':True,'vertex_indices_inside_each_triangle_preserved':True,
 'triangle_order_changed':True,'primitive_count':4,'primitives':primitive_map,'readback_checked':True,
 'original_AI_generator_preserved':loaded['asset']['generator']==original['asset']['generator'],
 'limitations':['No Draco, meshopt or quantization. Any optimizer requires new bindings and a new readback verification.',
 'This is a data export demonstration, not an app integration or iPhone performance result.']}
(a.output/'export-binding.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
