"""Independent checks on the saved Blender master and actual serialized GLB.

Run inside Blender after render_asset.py and export_asset.py have finished.
These checks establish geometric consistency, not medical correctness.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
meta=json.loads((root/'construction.json').read_text());plane=meta['median_plane_x_m']
assert sha(root/'source.glb')==meta['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(root/'ecorche-athletique.blend'),use_scripts=False)
scene=bpy.data.scenes['02_ATHLETIQUE'];bpy.context.window.scene=scene;scene.view_layers[0].update()
graph=bpy.context.evaluated_depsgraph_get();master={};triangles=0;seam_error=0.;flips=0
for ob in scene.objects:
 if ob.type!='MESH':continue
 ev=ob.evaluated_get(graph);mesh=ev.to_mesh();v=np.array([ob.matrix_world@x.co for x in mesh.vertices]);f=np.array([q.vertices[:]for q in mesh.polygons],int)
 assert all(len(q.vertices)==3 for q in mesh.polygons)
 master[ob.name]=(v,f);triangles+=len(f);ev.to_mesh_clear()
 if ob.data.shape_keys:
  base=np.array([v.co[:]for v in ob.data.shape_keys.key_blocks[0].data]);target=np.array([v.co[:]for v in ob.data.shape_keys.key_blocks['ATHLETIQUE'].data])
  _,inverse=np.unique(base,axis=0,return_inverse=True);n=int(inverse.max())+1
  low=np.full((n,3),np.inf);high=np.full((n,3),-np.inf);delta=target-base
  np.minimum.at(low,inverse,delta);np.maximum.at(high,inverse,delta);seam_error=max(seam_error,float(np.max(high-low)))
  cross0=np.cross(base[f[:,1]]-base[f[:,0]],base[f[:,2]]-base[f[:,0]])
  cross1=np.cross(target[f[:,1]]-target[f[:,0]],target[f[:,2]]-target[f[:,0]])
  valid=np.linalg.norm(cross0,axis=1)>1e-10
  flips+=int(np.sum(valid&(np.einsum('ij,ij->i',cross0,cross1)<=0)))
assert seam_error<1e-7,('source seams diverged',seam_error)
assert flips==0,('new triangle orientation inversions',flips)
paired_error=0.;pairs=0;central_error=0.
for row in meta['records']:
 name=row['object'];v,f=master[name]
 if row['side']=='right':
  mate=master[name[:-5]+'left'][0];reflection=v.copy();reflection[:,0]=2*plane-reflection[:,0]
  assert mate.shape==v.shape;paired_error=max(paired_error,float(np.max(np.abs(mate-reflection))));pairs+=1
 if row['side']=='central':
  tree=KDTree(len(v))
  for i,x in enumerate(v):tree.insert(x,i)
  tree.balance()
  for x in v:
   q=Vector((2*plane-x[0],x[1],x[2]));central_error=max(central_error,float(tree.find(q)[2]))
assert paired_error<2e-7 and central_error<2e-6
assert len(master)==meta['final_objects'] and triangles==meta['final_triangles']
required=['pectoralis_major','deltoid','latissimus_dorsi','trapezius','rectus_abdominis']
assert all(name+'.'+side in master for name in required for side in ['left','right'])

# Actual glTF bytes, independently decoded, including accessor strides.
raw=(root/'ecorche-athletique.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0]
doc=json.loads(raw[20:20+n]);blob=raw[28+n:]
def accessor(index):
 ac=doc['accessors'][index];view=doc['bufferViews'][ac['bufferView']]
 width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[ac['type']]
 dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[ac['componentType']])
 return np.ndarray((ac['count'],width),dtype=dtype,buffer=blob,offset=view.get('byteOffset',0)+ac.get('byteOffset',0),strides=(view.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()
def signatures(v,f):
 q=np.rint(v[f]*1e6).astype('<i4');order=np.lexsort((q[:,:,2],q[:,:,1],q[:,:,0]),axis=1)
 q=np.ascontiguousarray(np.take_along_axis(q,order[:,:,None],axis=1).reshape(-1,9))
 return np.sort(q.view(np.dtype([(f'c{i}','<i4')for i in range(9)])).ravel())
export_triangles=0;export_vertices=0;omitted=[];position_error=0.
for node in doc['nodes']:
 if 'mesh'not in node:continue
 assert node['name']in master,node['name'];expected_v,expected_f=master[node['name']]
 assert not any(k in node for k in ['matrix','translation','rotation','scale']),node
 primitives=doc['meshes'][node['mesh']]['primitives'];assert len(primitives)==1
 primitive=primitives[0];v=accessor(primitive['attributes']['POSITION']).astype(float);v=v[:,[0,2,1]];v[:,1]*=-1
 assert not any(key.startswith('COLOR_')for key in primitive['attributes']),('unwanted source colors in blue export',node['name'])
 f=accessor(primitive['indices']).reshape(-1,3);export_triangles+=len(f);export_vertices+=len(v)
 expected=signatures(expected_v,expected_f);actual=signatures(v,f)
 assert not len(np.setdiff1d(actual,expected)),('unexpected exported faces',node['name'])
 if not np.array_equal(expected,actual):
  # Compare multiplicities too: an exporter can remove a duplicate face
  # without removing its visible surface.
  signatures0,counts0=np.unique(expected,return_counts=True)
  signatures1,counts1=np.unique(actual,return_counts=True)
  remaining=np.zeros(len(signatures0),int);remaining[np.searchsorted(signatures0,signatures1)]=counts1
  difference=counts0-remaining;assert (difference>=0).all()
  for index in np.flatnonzero(difference):
   sig=signatures0[index]
   coords=np.array(sig.tolist(),float).reshape(3,3)*1e-6
   area=float(np.linalg.norm(np.cross(coords[1]-coords[0],coords[2]-coords[0]))/2)
   assert remaining[index]>0 or area<1e-10,('visible surface omitted',node['name'],area)
   omitted.append({'object':node['name'],'quantized_area_m2':area,'removed_copies':int(difference[index]),'copies_still_exported':int(remaining[index]),'kind':'duplicate_surface'if remaining[index]>0 else 'near_zero_area'})
assert len([n for n in doc['nodes']if 'mesh'in n])==len(master)
assert doc['asset']['extras']['source_sha256']==meta['source_sha256']
assert 'CC BY 4.0'in doc['asset']['copyright']
factor=doc['materials'][0]['pbrMetallicRoughness']['baseColorFactor'];assert np.allclose(factor,[.19,.28,.42,1])

# Check median front/back ray coverage rather than inferring it from object count.
allv=[];allf=[];offset=0
for v,f in master.values():allv.extend(v.tolist());allf.extend((f+offset).tolist());offset+=len(v)
tree=BVHTree.FromPolygons(allv,allf,all_triangles=True);coverage=[]
for z in [.98,1.05,1.12,1.20,1.30,1.38,1.45]:
 row={'z_m':z}
 for side,y,dy in [('front',-1,1),('back',1,-1)]:
  hit=tree.ray_cast(Vector((plane,y,z)),Vector((0,dy,0)),2)
  row[side+'_hit_y_m']=float(hit[0].y)if hit[0]is not None else None
 coverage.append(row)

render=json.loads((root/'renders/metadata.json').read_text())
assert render['final_blend_sha256']==sha(root/'ecorche-athletique.blend')
assert all(sha(root/'renders'/f['file'])==f['sha256']for f in render['frames'])
assert len(render['frames'])==12
import_scene=bpy.data.scenes.new('VERIFY_IMPORT');bpy.context.window.scene=import_scene
bpy.ops.import_scene.gltf(filepath=str(root/'ecorche-athletique.glb'),merge_vertices=False)
imported=[o for o in import_scene.objects if o.type=='MESH'];imported_triangles=sum(sum(len(f.vertices)-2 for f in o.data.polygons)for o in imported)
assert len(imported)==len(master) and imported_triangles==export_triangles
report={'source_unchanged_sha256':sha(root/'source.glb'),'master_sha256':sha(root/'ecorche-athletique.blend'),'glb_sha256':sha(root/'ecorche-athletique.glb'),'master_objects':len(master),'master_triangles':triangles,'bilateral_pairs':pairs,'max_pair_reflection_error_m':paired_error,'max_central_reflection_distance_m':central_error,'max_duplicate_seam_delta_error_m':seam_error,'retouch_triangle_inversions':flips,'glb_triangles':export_triangles,'glb_vertices':export_vertices,'export_omissions_checked':omitted,'geometry_matches_serialized_export_at_micron_quantization':True,'glb_blender_reimport_objects':len(imported),'glb_blender_reimport_triangles':imported_triangles,'blue_material_without_source_vertex_color_multiplication':True,'median_ray_coverage':coverage,'renders_verified':len(render['frames']),'medical_anatomy_certified':False,'deltoid_three_heads_independently_segmented':False,'verifier_sha256':sha(Path(__file__))}
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('ANATOMY_VERIFIED',json.dumps(report),flush=True)
