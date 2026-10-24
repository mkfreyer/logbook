"""Check actual source, Blender, face masks, exported GLB and raycast bindings."""
import argparse,json,math,struct,sys
from collections import Counter
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import EXPECTED_SHA,components,load_glb,neighbors,patch_topology,sha
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.prepared.resolve()
raw,original,v,ix=load_glb(root/'source.glb');assert sha(raw)==EXPECTED_SHA
assert len(v)==47711 and len(ix)==95426 and not original.get('materials') and not original.get('textures') and not original.get('images')
meta=json.loads((root/'regions/regions.json').read_text());labels=np.frombuffer((root/'regions/triangle-regions.u8').read_bytes(),dtype=np.uint8)
assert sha(labels.tobytes())==meta['labels']['sha256'] and len(labels)==len(ix)
assert sha(v.tobytes())==meta['binding']['position_buffer_sha256'] and sha(ix.tobytes())==meta['binding']['index_buffer_sha256']
adj=neighbors(ix);patches=[]
for row in meta['regions']:
 mask=labels==row['value'];stats=patch_topology(mask,ix,adj)
 for key,value in stats.items():assert row[key]==value
 faces=ix[mask];edges=np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[2,0]]]),axis=1)
 edges,count=np.unique(edges,axis=0,return_counts=True);boundary=edges[count==1]
 degree=Counter(boundary.ravel().tolist());assert all(n==2 for n in degree.values())
 bmap={i:[] for i in degree}
 for i,j in boundary:bmap[int(i)].append(int(j));bmap[int(j)].append(int(i))
 todo=set(bmap);loops=0
 while todo:
  stack=[todo.pop()];loops+=1
  while stack:
   for n in bmap[stack.pop()]:
    if n in todo:todo.remove(n);stack.append(n)
 assert stats['single_disk'] and loops==1
 patches.append({'id':row['id'],**stats,'boundary_loops':loops,'boundary_vertices_degree_two':True})
assert set(labels)=={0,1,2,3}
render=json.loads((root/'renders/render-metadata.json').read_text());blend=root/'renders/meshy-masques.blend'
assert sha(blend.read_bytes())==render['blend_sha256']
assert sha((root/'regions/regions.json').read_bytes())==render['regions_sha256']
assert sha(Path(__file__).with_name('blender_demo.py').read_bytes())==render['renderer_sha256']
for frame in render['frames']:assert sha((root/'renders'/frame['file']).read_bytes())==frame['sha256']
bpy.ops.wm.open_mainfile(filepath=str(blend),use_scripts=False)
assert bpy.context.scene.name=='00_NEUTRE'
post=render['license_and_guide_postprocess'];assert sha(Path(__file__).with_name('finish_demo.py').read_bytes())==post['script_sha256']
for name in post['embedded_texts']:assert bpy.data.texts[name].as_string()==(root/name).read_text()
meshes={o.data for o in bpy.data.objects if o.type=='MESH'};assert len(meshes)==1
mesh=meshes.pop();positions=np.array([x.co[:] for x in mesh.vertices],dtype='<f4');faces=np.array([f.vertices[:] for f in mesh.polygons],dtype='<u4')
assert np.array_equal(positions,v) and np.array_equal(faces,ix)
assert np.array_equal(np.array([d.value for d in mesh.attributes['source_triangle_index'].data]),np.arange(len(ix)))
assert np.array_equal(np.array([d.value for d in mesh.attributes['muscle_zone'].data]),labels)
assert np.array_equal(np.array([f.material_index for f in mesh.polygons]),labels)
assert all(not o.modifiers for o in bpy.data.objects if o.type=='MESH') and not mesh.shape_keys
selection=[]
for value,name in enumerate(['00_NEUTRE','01_PECTORAL_GAUCHE','02_PECTORAL_DROIT','03_DELTOIDE_GAUCHE']):
 ob=next(o for o in bpy.data.scenes[name].objects if o.type=='MESH');assert ob.data==mesh
 assert max(abs(ob.matrix_basis[i][j]-Matrix.Rotation(math.pi/2,4,'X')[i][j]) for i in range(4) for j in range(4))<1e-6
 for index,slot in enumerate(ob.material_slots):
  assert slot.link=='OBJECT';expected=(1,.18,.025,1) if index==value and value else (.19,.28,.42,1)
  assert np.allclose(slot.material.diffuse_color,expected,atol=1e-6)
 selection.append({'scene':name,'orange_value':value,'orange_faces':int((labels==value).sum()) if value else 0,'other_regions_blue':True})
binding=json.loads((root/'export/export-binding.json').read_text());export=(root/'export'/binding['export_file']).read_bytes()
assert sha(export)==binding['export_sha256'];n=struct.unpack_from('<I',export,12)[0];d=json.loads(export[20:20+n]);binary=export[28+n:]
assert len(d['meshes'])==1 and len(d['meshes'][0]['primitives'])==4
assert {p['attributes']['POSITION'] for p in d['meshes'][0]['primitives']}=={0}
assert d['asset']['generator']==original['asset']['generator']
def accessor(index,dtype,width):
 ac=d['accessors'][index];view=d['bufferViews'][ac['bufferView']];offset=view.get('byteOffset',0)+ac.get('byteOffset',0)
 return np.frombuffer(binary,dtype=dtype,count=ac['count']*width,offset=offset).reshape(-1,width)
permutation=np.frombuffer((root/'export'/binding['map_file']).read_bytes(),dtype='<u4')
assert sha(permutation.tobytes())==binding['map_sha256'] and np.array_equal(np.sort(permutation),np.arange(len(ix)))
primitive_trees=[]
for row,primitive in zip(binding['primitives'],d['meshes'][0]['primitives']):
 pos=accessor(primitive['attributes']['POSITION'],'<f4',3);tri=accessor(primitive['indices'],'<u4',1).reshape(-1,3)
 norm=accessor(primitive['attributes']['NORMAL'],'<f4',3);assert np.isfinite(norm).all() and np.allclose(np.linalg.norm(norm,axis=1),1,atol=1e-6)
 assert np.array_equal(pos,v)
 start=row['map_triangle_offset'];ids=permutation[start:start+row['triangle_count']]
 assert np.array_equal(tri,ix[ids]) and np.all(labels[ids]==row['region_value'])
 primitive_trees.append(BVHTree.FromPolygons(pos.tolist(),tri.tolist(),all_triangles=True))
source_tree=BVHTree.FromPolygons(v.tolist(),ix.tolist(),all_triangles=True)
rays=[]
for expected,origin in [(1,(.09,.52,1)),(2,(-.09,.52,1)),(3,(.22,.56,1)),(0,(0,.10,1))]:
 hit=source_tree.ray_cast(origin,(0,0,-1));assert hit[2] is not None and labels[hit[2]]==expected
 hits=[]
 for p,tree in enumerate(primitive_trees):
  h=tree.ray_cast(origin,(0,0,-1))
  if h[2] is not None:hits.append((h[3],p,h[2]))
 distance,p,face=min(hits);source_id=int(permutation[binding['primitives'][p]['map_triangle_offset']+face])
 assert source_id==hit[2] and labels[source_id]==expected
 rays.append({'origin_source_coordinates':origin,'direction':[0,0,-1],'export_primitive':p,'local_face_index':face,'source_triangle':source_id,'region_value':expected,'same_hit_on_original_and_export':True})
report={'source_sha256':EXPECTED_SHA,'vertices':len(v),'triangles':len(ix),'source_components':len(components(np.ones(len(ix),dtype=bool),adj)),
 'source_file_intact':True,'blender_positions_bit_equal_source':True,'blender_triangle_indices_bit_equal_source':True,
 'new_anatomical_geometry':0,'source_coordinate_conversion':'Object rotation +90 X only; local vertex buffers untouched.',
 'regions':patches,'blender_selection_checks':selection,'export_primitives':4,'export_positions_bit_equal_source':True,
 'export_all_original_triangles_once':True,'export_triangle_reorder_has_explicit_bijection':True,'raycast_binding_tests':rays,
 'render_hashes_verified':True,'rendered_frames':len(render['frames']),
 'anatomical_contours_validated':False,'visual_verdict':'Partial POC: functional surface selection; deltoid lower/posterior boundary requires manual correction before full visual approval.',
 'limitations':['BVH raycasts test offline triangle/primitive identity, not a touch engine, Three.js runtime or iPhone.',
 'Topologically continuous masks do not prove anatomical borders; the deltoid remains provisional.',
 'No deformation, new muscle, remesh, full-body segmentation, rig, application integration or SQLite access.']}
(root/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('MESHY_CHECK',json.dumps({'vertices':len(v),'triangles':len(ix),'regions':patches,'raycasts':len(rays),'geometry_intact':True,'anatomical_contours_validated':False}),flush=True)
