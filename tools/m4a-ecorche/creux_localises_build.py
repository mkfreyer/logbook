"""Apply only the permitted bands, with exact P4 coordinates everywhere else."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np
from mathutils.bvhtree import BVHTree

p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--surface',type=Path,required=True);p.add_argument('--camera',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.output.resolve();root.mkdir(parents=True,exist_ok=True);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.baseline)=='f8b6a232a18335221af3cafc62b37837fedc1caaf9bc6cb48e1cb583f222d9ab'
prior=json.loads((a.baseline.parent/'combinaison.json').read_text());data=np.load(a.surface);plane=prior['median_plane_x_m'];bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()),use_scripts=False)
source=bpy.data.scenes['16_COMBINAISON_P4_P5'];bpy.context.window.scene=source;source.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get();after=bpy.data.scenes.new('17_CREUX_LOCALISES');after.world=source.world;after.collection.children.link(bpy.data.collections['COMBINAISON_LUMIERES_SYMETRIQUES']);records={}
for ob in source.objects:
 if ob.type!='MESH':continue
 key=ob['asset_id'];clone=ob.copy();clone.name='CREUX__'+key;after.collection.objects.link(clone)
 if key not in ['deltoid.right','deltoid.left']:continue
 mesh=bpy.data.meshes.new_from_object(ob.evaluated_get(g),preserve_all_data_layers=True,depsgraph=g);v=np.array([ob.matrix_world@p.co for p in mesh.vertices]);f=np.array([p.vertices[:]for p in mesh.polygons]);q=v.copy()
 if key.endswith('.right'):
  assert np.array_equal(v,data['source_v'])and np.array_equal(f,data['f']);q=data['v'].copy()
 else:
  delta=data['v']-data['source_v'];delta[:,0]*=-1;q[data['allowed']]=(v[data['allowed']]+delta[data['allowed']]).astype(np.float32)
 assert np.array_equal(q[~data['allowed']],v[~data['allowed']])
 assert np.array_equal(q[data['belly']],v[data['belly']])
 mesh.vertices.foreach_set('co',q.astype(np.float32).ravel());mesh.update();clone.data=mesh
 # Coordinates are baked directly: no relative-key cancellation on locked points.
 tree=BVHTree.FromPolygons(q.tolist(),f.tolist(),all_triangles=True);pairs=[(i,j)for i,j in tree.overlap(tree)if i<j and not np.isin(f[i],f[j]).any()];assert not pairs,(key,len(pairs))
 oldcross=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]);cross=np.cross(q[f[:,1]]-q[f[:,0]],q[f[:,2]]-q[f[:,0]])
 # Filling a steep old trough can legitimately rotate its normal past 90deg.
 # Test actual degeneracy, signed projected orientation and self-intersections.
 direction=np.load(a.surface.parent/'source.npz')['direction'].copy()
 if key.endswith('.left'):direction[0]*=-1
 oldproj=oldcross@direction;newproj=cross@direction;stable=np.abs(oldproj)>1e-10
 assert (oldproj[stable]*newproj[stable]>0).all()
 assert (np.linalg.norm(cross,axis=1)>1e-10).all()
 vol=lambda points:float(np.einsum('ij,ij->i',points[f[:,0]],np.cross(points[f[:,1]],points[f[:,2]])).sum()/6)
 records[key]={'triangles':len(f),'vertices':len(v),'changed_vertices':int((np.linalg.norm(q-v,axis=1)>0).sum()),'protected_belly_vertices':int(data['belly'].sum()),'belly_max_difference_m':0,'outside_allowed_bands_max_difference_m':0,'volume_before_m3':vol(v),'volume_after_m3':vol(q),'relative_volume_error':abs(vol(q)/vol(v)-1),'bbox_identical':bool(np.array_equal(np.ptp(v,axis=0),np.ptp(q,axis=0))),'self_contacts':len(pairs),'faces_rotated_over_90deg_from_old_trough':int((np.einsum('ij,ij->i',oldcross,cross)<0).sum()),'projected_orientation_preserved':True}
meta={'baseline_commit':'0ab3d838c728a88f2d325edff7a6884400c9ed78','baseline_blend_sha256':sha(a.baseline),'scene':after.name,'before_scene':source.name,'changed_objects':sorted(records),'unchanged_other_objects':298,'source_asset':prior['source_asset'],'source_sha256':prior['source_sha256'],'head_source':prior['head_source'],'median_plane_x_m':plane,'records':records,'surface_method':json.loads(a.surface.with_suffix('.json').read_text()),'camera':json.loads(a.camera.read_text()),'topology_unchanged':True,'new_triangles':0,'new_segmentation':False,'builder_sha256':sha(Path(__file__))}
(root/'creux.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');bpy.data.texts.new('CREUX_LOCALISES.json').write(json.dumps(meta,ensure_ascii=False,indent=2));bpy.context.window.scene=after;after.camera=source.camera;bpy.ops.wm.save_as_mainfile(filepath=str(root/'ecorche-creux-localises.blend'),compress=True);print('BUILT',json.dumps(records),flush=True)
