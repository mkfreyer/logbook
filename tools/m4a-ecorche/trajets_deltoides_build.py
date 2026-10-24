"""Apply a symmetric local edit to the P4 deltoids; preserve all other P5 parts."""
import argparse, hashlib, json, sys
from pathlib import Path
import bpy, numpy as np
from mathutils.bvhtree import BVHTree

p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--surface',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.output.resolve();root.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.baseline)=='f8b6a232a18335221af3cafc62b37837fedc1caaf9bc6cb48e1cb583f222d9ab'
prior=json.loads((a.baseline.parent/'combinaison.json').read_text());plane=prior['median_plane_x_m'];data=np.load(a.surface)
bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()),use_scripts=False);source=bpy.data.scenes['16_COMBINAISON_P4_P5'];bpy.context.window.scene=source;source.view_layers[0].update();g=bpy.context.evaluated_depsgraph_get()
after=bpy.data.scenes.new('17_TRAJETS_DELTOIDES');after.world=source.world
# The SAME light and camera objects are linked into both scenes.
after.collection.children.link(bpy.data.collections['COMBINAISON_LUMIERES_SYMETRIQUES'])
right=data['v'];f=data['f'];delta=right-data['source_v'];records={}
for ob in source.objects:
    if ob.type!='MESH':continue
    key=ob['asset_id'];clone=ob.copy();clone.name='TRAJETS__'+key;after.collection.objects.link(clone)
    if key not in ['deltoid.right','deltoid.left']:continue
    clone.data=ob.data.copy();ev=ob.evaluated_get(g);mesh=ev.to_mesh();v=np.array([ob.matrix_world@p.co for p in mesh.vertices]);ff=np.array([p.vertices[:]for p in mesh.polygons]);ev.to_mesh_clear()
    if key=='deltoid.right':assert np.array_equal(v,data['source_v'])and np.array_equal(f,ff)
    change=delta.copy()
    if key.endswith('.left'):change[:,0]*=-1
    q=v+change
    assert np.max(np.abs(np.array(ob.matrix_world)-np.eye(4)))<1e-8
    # Relative to the current P4 key: P4 stays active and this adds only q-P4.
    previous=clone.data.shape_keys.key_blocks['FINITION_ANTERIEURE_PASSE4']
    new=clone.shape_key_add(name='TRAJETS_BLEUS_LOCAUX');new.relative_key=previous;new.data.foreach_set('co',q.astype(np.float32).ravel());new.value=1
    q=q.astype(np.float32).astype(float)
    tree=BVHTree.FromPolygons(q.tolist(),ff.tolist(),all_triangles=True)
    contacts=[(i,j)for i,j in tree.overlap(tree)if i<j and not np.isin(ff[i],ff[j]).any()]
    assert not contacts,('self contact',key,len(contacts))
    cross=np.cross(q[ff[:,1]]-q[ff[:,0]],q[ff[:,2]]-q[ff[:,0]]);oldcross=np.cross(v[ff[:,1]]-v[ff[:,0]],v[ff[:,2]]-v[ff[:,0]])
    areas=np.linalg.norm(cross,axis=1)/2;assert (areas>1e-10).all()
    assert (np.einsum('ij,ij->i',cross,oldcross)>0).all(),('flipped triangle',key)
    vol=lambda points:float(np.einsum('ij,ij->i',points[ff[:,0]],np.cross(points[ff[:,1]],points[ff[:,2]])).sum()/6)
    records[key]={'vertices':len(q),'triangles':len(ff),'changed_vertices':int((np.linalg.norm(q-v,axis=1)>1e-8).sum()),'max_displacement_m':float(np.linalg.norm(q-v,axis=1).max()),'volume_before_m3':vol(v),'volume_after_m3':vol(q),'volume_ratio':vol(q)/vol(v),'bbox_before_m':np.ptp(v,axis=0).tolist(),'bbox_after_m':np.ptp(q,axis=0).tolist(),'self_contacts':len(contacts),'min_triangle_area_m2':float(areas.min())}
meta={'baseline_commit':'0ab3d838c728a88f2d325edff7a6884400c9ed78','baseline_blend_sha256':sha(a.baseline),'scene':after.name,'before_scene':source.name,'changed_objects':sorted(records),'unchanged_other_objects':298,'source_asset':prior['source_asset'],'source_sha256':prior['source_sha256'],'head_source':prior['head_source'],'median_plane_x_m':plane,'records':records,'surface_method':json.loads(a.surface.with_suffix('.json').read_text()),'topology_unchanged':True,'new_triangles':0,'new_segmentation':False,'builder_sha256':sha(Path(__file__))}
(root/'trajets.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');bpy.data.texts.new('TRAJETS_DELTOIDES.json').write(json.dumps(meta,ensure_ascii=False,indent=2));bpy.context.window.scene=after;after.camera=source.camera;bpy.ops.wm.save_as_mainfile(filepath=str(root/'ecorche-trajets-deltoides.blend'),compress=True);print('TRAJETS_BUILT',json.dumps(records),flush=True)
