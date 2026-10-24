"""Verify the targeted correction against the actual original/edited/exported buffers."""
import argparse,json,math,struct,sys
from collections import Counter
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
from mesh_io import load_glb,sha,EXPECTED_SHA,neighbors,patch_topology
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepared',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.prepared.resolve();new=root/'correction'
raw,original,v,ix=load_glb(root/'source.glb');assert sha(raw)==EXPECTED_SHA
old=np.frombuffer((root/'regions/triangle-regions.u8').read_bytes(),dtype=np.uint8)
labels=np.frombuffer((new/'regions/triangle-regions.u8').read_bytes(),dtype=np.uint8)
meta=json.loads((new/'regions/regions.json').read_text());edit=json.loads((new/'face-edits.json').read_text())
assert len(labels)==len(ix)==95426 and len(v)==47711
assert sha(old.tobytes())==edit['baseline_labels_sha256']
assert sha(labels.tobytes())==edit['corrected_labels_sha256']==meta['labels']['sha256']
expected=old.copy();seen=set()
for r in edit['edits']:
 i=r['source_triangle'];assert i not in seen and int(expected[i])==r['from'];seen.add(i)
 assert r['from'] in [1,2,3] and r['to']==0;expected[i]=r['to']
assert np.array_equal(labels,expected) and set(np.flatnonzero(labels!=old))==seen
review=json.loads((new/'manual-review.json').read_text())
for area in review['areas']:
 ids=np.array(area['source_triangles'],dtype=int)
 assert len(ids)==len(set(ids)) and np.all((ids>=0)&(ids<len(ix)))
 assert np.all(labels[ids]==area['region'])
assert [(r['value'],r['id']) for r in meta['regions']]==[(1,'pectoralis.left'),(2,'pectoralis.right'),(3,'deltoid.left')]
adj=neighbors(ix);patches=[]
for row in meta['regions']:
 f=ix[labels==row['value']];stats=patch_topology(labels==row['value'],ix,adj);assert stats['single_disk']
 for key,value in stats.items():assert row[key]==value
 edges=np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1)
 edges,n=np.unique(edges,axis=0,return_counts=True);boundary=edges[n==1]
 assert set(Counter(boundary.ravel()).values())=={2}
 links={int(i):[] for i in np.unique(boundary)}
 for i,j in boundary:links[int(i)].append(int(j));links[int(j)].append(int(i))
 todo=set(links);loops=0
 while todo:
  stack=[todo.pop()];loops+=1
  while stack:
   for n in links[stack.pop()]:
    if n in todo:todo.remove(n);stack.append(n)
 assert loops==1;patches.append({'id':row['id'],**stats,'boundary_loops':loops,'boundary_vertex_degree':2})
def scene_signature():
 scene=bpy.data.scenes['00_NEUTRE'];ob=next(o for o in scene.objects if o.type=='MESH')
 blue=[]
 for s in ob.material_slots:
  n=s.material.node_tree.nodes['Principled BSDF']
  blue.append({k:list(n.inputs[k].default_value) if k=='Base Color' else n.inputs[k].default_value for k in ['Base Color','Metallic','Roughness','Coat Weight']})
 lights={o.name:{'matrix':[list(r) for r in o.matrix_world],'energy':o.data.energy,'size':o.data.size,'color':list(o.data.color)} for o in scene.objects if o.type=='LIGHT'}
 world=scene.world.node_tree.nodes['Background'];return {'blue':blue,'lights':lights,'world_color':list(world.inputs['Color'].default_value),'world_strength':world.inputs['Strength'].default_value,'view_transform':scene.view_settings.view_transform}
signatures=[]
for file,wanted in [(root/'renders/meshy-masques.blend',old),(new/'renders/meshy-masques.blend',labels)]:
 bpy.ops.wm.open_mainfile(filepath=str(file),use_scripts=False)
 meshes={o.data for o in bpy.data.objects if o.type=='MESH'};assert len(meshes)==1;mesh=meshes.pop()
 assert np.array([p.co[:] for p in mesh.vertices],dtype='<f4').tobytes()==v.tobytes()
 assert np.array([p.vertices[:] for p in mesh.polygons],dtype='<u4').tobytes()==ix.tobytes()
 assert np.array_equal(np.array([p.material_index for p in mesh.polygons],dtype='u1'),wanted)
 assert np.array_equal(np.array([d.value for d in mesh.attributes['source_triangle_index'].data]),np.arange(len(ix)))
 assert np.array_equal(np.array([d.value for d in mesh.attributes['muscle_zone'].data]),wanted)
 assert not mesh.shape_keys and all(not o.modifiers for o in bpy.data.objects if o.type=='MESH')
 for o in [o for o in bpy.data.objects if o.type=='MESH']:
  assert np.allclose(o.location,(0,0,0)) and np.allclose(o.scale,(1,1,1)) and np.allclose(o.rotation_euler,(math.pi/2,0,0))
 signatures.append(scene_signature())
assert signatures[0]==signatures[1]
selection=[]
for value,name in enumerate(['00_NEUTRE','01_PECTORAL_GAUCHE','02_PECTORAL_DROIT','03_DELTOIDE_GAUCHE']):
 ob=next(o for o in bpy.data.scenes[name].objects if o.type=='MESH')
 for i,s in enumerate(ob.material_slots):
  assert s.link=='OBJECT';wanted=(1,.085,.006,1) if value and i==value else (.19,.28,.42,1)
  assert np.allclose(s.material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value,wanted)
  assert s.material.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value==0
 selection.append({'id':value,'other_regions_blue':True,'no_emission':True})
assert json.loads(bpy.data.texts['CORRECTION_FACES.json'].as_string())==edit
assert json.loads(bpy.data.texts['REGIONS.json'].as_string())==meta
assert bpy.data.texts['CORRECTION_GUIDE.md'].as_string()==(new/'README.md').read_text()
assert bpy.data.texts['MANUAL_REVIEW.json'].as_string()==(new/'manual-review.json').read_text()
for name in ['LICENCE_ET_PROVENANCE.md','RAYCAST_ET_EXPORT.md']:assert bpy.data.texts[name].as_string()==(root/name).read_text()
binding=json.loads((new/'export/export-binding.json').read_text());export=(new/'export'/binding['export_file']).read_bytes()
assert sha(export)==binding['export_sha256'];length=struct.unpack_from('<I',export,12)[0];doc=json.loads(export[20:20+length]);binary=export[28+length:]
assert doc['asset']['generator']==original['asset']['generator'] and 'Meshy' in doc['asset']['copyright']
def accessor(i,dtype,width):
 ac=doc['accessors'][i];view=doc['bufferViews'][ac['bufferView']]
 return np.frombuffer(binary,dtype=dtype,count=ac['count']*width,offset=view.get('byteOffset',0)+ac.get('byteOffset',0)).reshape(-1,width)
mapping=np.frombuffer((new/'export'/binding['map_file']).read_bytes(),dtype='<u4')
assert sha(mapping.tobytes())==binding['map_sha256'] and np.array_equal(np.sort(mapping),np.arange(len(ix)))
primitives=doc['meshes'][0]['primitives'];assert len(primitives)==4 and {p['attributes']['POSITION'] for p in primitives}=={0}
trees=[]
for row,primitive in zip(binding['primitives'],primitives):
 pos=accessor(primitive['attributes']['POSITION'],'<f4',3);tri=accessor(primitive['indices'],'<u4',1).reshape(-1,3)
 assert pos.tobytes()==v.tobytes()
 start=row['map_triangle_offset'];ids=mapping[start:start+row['triangle_count']]
 assert np.array_equal(tri,ix[ids]) and np.all(labels[ids]==row['region_value'])
 norm=accessor(primitive['attributes']['NORMAL'],'<f4',3);assert np.isfinite(norm).all() and np.allclose(np.linalg.norm(norm,axis=1),1,atol=1e-6)
 trees.append(BVHTree.FromPolygons(v.tolist(),tri.tolist(),all_triangles=True))
source_tree=BVHTree.FromPolygons(v.tolist(),ix.tolist(),all_triangles=True);rays=[]
def test_ray(origin,direction,expected_region,expected_face=None):
 h=source_tree.ray_cast(origin,direction);assert h[2] is not None and int(labels[h[2]])==expected_region
 if expected_face is not None:assert h[2]==expected_face
 hits=[]
 for p,tree in enumerate(trees):
  hit=tree.ray_cast(origin,direction)
  if hit[2] is not None:hits.append((hit[3],p,hit[2]))
 distance,p,face=min(hits);mapped=int(mapping[binding['primitives'][p]['map_triangle_offset']+face]);assert mapped==h[2]
 rays.append({'origin':list(origin),'direction':list(direction),'source_triangle':mapped,'export_primitive':p,'local_face':face,'region':expected_region})
for value,origin in [(1,(.09,.52,1)),(2,(-.09,.52,1)),(3,(.22,.56,1)),(0,(0,.10,1))]:test_ray(origin,(0,0,-1),value)
for value in [1,2,3]:
 row=next(r for r in edit['edits'] if r['from']==value);i=row['source_triangle'];pts=v[ix[i]].astype(float)
 center=pts.mean(0);normal=np.cross(pts[1]-pts[0],pts[2]-pts[0]);normal/=np.linalg.norm(normal)
 test_ray(center+normal*.00002,-normal,0,i)
frames=[]
for version in ['before','after']:
 render=json.loads((new/'renders'/f'{version}-metadata.json').read_text())
 assert len(render['frames'])==(3 if version=='before' else 10)
 assert sha(Path(__file__).with_name('render_correction.py').read_bytes())==render['renderer_sha256']
 blend=root/'renders/meshy-masques.blend' if version=='before' else new/'renders/meshy-masques.blend'
 if version=='after':
  post=render['postprocess'];assert post['render_input_blend_sha256']==render['input_blend_sha256']
  assert sha(blend.read_bytes())==post['final_blend_sha256']
  assert sha(Path(__file__).with_name('finish_correction.py').read_bytes())==post['script_sha256']
 else:assert sha(blend.read_bytes())==render['input_blend_sha256']
 for frame in render['frames']:
  png=(new/'renders'/frame['file']).read_bytes();assert sha(png)==frame['sha256']
  assert list(struct.unpack_from('>II',png,16))==frame['size'];frames.append(frame['file'])
comparisons=json.loads((new/'renders/comparisons-metadata.json').read_text())
assert sha(Path(__file__).with_name('compare_correction.py').read_bytes())==comparisons['script_sha256']
for row in comparisons['comparisons']:
 png=(new/'renders'/row['file']).read_bytes();assert sha(png)==row['sha256']
 assert list(struct.unpack_from('>II',png,16))==row['size']
 for item in row['inputs']:assert sha((root/item['file']).read_bytes())==item['sha256']
report={'source_sha256':sha(raw),'vertices':len(v),'triangles':len(ix),'source_file_intact':True,'both_blender_meshes_bit_equal_source':True,
 'positions_added_removed_or_moved':0,'triangles_added_removed':0,'stable_region_ids':True,'face_edits':len(seen),'untargeted_face_labels_unchanged':True,
 'regions':patches,'neutral_blue_material_lights_world_unchanged':True,'selection_checks':selection,'export_positions_bit_equal_source':True,
 'all_original_triangles_exported_once':True,'regenerated_mapping_bijective_and_verified':True,'raycast_checks':rays,'render_hashes_verified':True,'frames':frames,
 'visual_verdict':'PARTIEL','anatomical_contours_validated':False,'mobile_device_performance_validated':False,
 'limitations':['Local boundary-tip cleanup is not an anatomical contour validation.','Residual triangle steps and uncertain clavicular/axillary/posterior boundaries require human face review.','390 px contact sheets are image-size checks, not an iPhone or touch-engine benchmark.']}
(new/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print('CORRECTION_VERIFIED',json.dumps({'vertices':len(v),'triangles':len(ix),'face_edits':len(seen),'raycasts':len(rays),'frames':len(frames),'verdict':'PARTIEL'}),flush=True)
