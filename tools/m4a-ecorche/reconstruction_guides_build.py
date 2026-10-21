"""Build an isolated Blender comparison from unchanged P4 + validated guides."""
import argparse,hashlib,json,sys
from pathlib import Path
import bpy,numpy as np

p=argparse.ArgumentParser();p.add_argument('--baseline',type=Path,required=True);p.add_argument('--asset',type=Path,required=True)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.asset.resolve();s=np.load(root/'surface.npz')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(a.baseline)=='f8b6a232a18335221af3cafc62b37837fedc1caaf9bc6cb48e1cb583f222d9ab'
bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()),use_scripts=False)
source=bpy.data.scenes['16_COMBINAISON_P4_P5'];bpy.context.window.scene=source
for scene in list(bpy.data.scenes):
    if scene!=source:bpy.data.scenes.remove(scene)
bpy.data.orphans_purge(do_recursive=True)
source.view_layers[0].update();graph=bpy.context.evaluated_depsgraph_get()
after=bpy.data.scenes.new('19_RECONSTRUCTION_GUIDES');after.world=source.world
after.collection.children.link(bpy.data.collections['COMBINAISON_LUMIERES_SYMETRIQUES'])
plane=.002114987923242599
f=s['f'];parent=s['parent_face'];ref=s['reference_v'];changed=np.linalg.norm(s['v']-ref,axis=1)>1e-9
retained=s['retained_original_ids'] if 'retained_original_ids' in s else np.arange(len(s['original_v']))
if 'corner_bary' in s:
    bary=s['corner_bary'];corner_parent=s['corner_parent']
else:
    tri=s['original_v'][s['original_f'][parent]];query=ref[f]
    U,V=tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]
    UU,VV,UV=(U*U).sum(1),(V*V).sum(1),(U*V).sum(1)
    Q=query-tri[:,None,0];QU=(Q*U[:,None,:]).sum(2);QV=(Q*V[:,None,:]).sum(2);den=UU*VV-UV*UV
    b=(QU*VV[:,None]-QV*UV[:,None])/den[:,None];c=(QV*UU[:,None]-QU*UV[:,None])/den[:,None]
    bary=np.stack([1-b-c,b,c],axis=2);corner_parent=np.repeat(parent[:,None],3,axis=1)
# Keep originals exactly; interpolate new vertices on their original triangles.
vertex_parent=np.zeros(len(ref),int);vertex_bary=np.zeros((len(ref),3))
for k in range(3):vertex_parent[f[:,k]]=corner_parent[:,k];vertex_bary[f[:,k]]=bary[:,k]
records={}
for ob in source.objects:
    if ob.type!='MESH':continue
    key=ob['asset_id'];clone=ob.copy();clone.name='RECONSTRUIT__'+key;after.collection.objects.link(clone)
    if key not in ['deltoid.right','deltoid.left']:continue
    assert np.array_equal(np.array(ob.matrix_world),np.eye(4)) and not ob.modifiers
    ev=ob.evaluated_get(graph);old=ev.to_mesh()
    old_v=np.array([p.co[:]for p in old.vertices]);old_f=np.array([p.vertices[:]for p in old.polygons])
    assert np.array_equal(np.sort(old_f,axis=1),np.sort(s['original_f'],axis=1))
    flip=np.array([0,2,1]) if key.endswith('.left') else np.array([0,1,2])
    ff=f[:,flip]
    cp=corner_parent[:,flip]
    permutation=(s['original_f'][cp][...,:,None]==old_f[cp][...,None,:]).argmax(axis=2)
    corner_bary=np.take_along_axis(bary[:,flip,:],permutation,axis=2)
    if key.endswith('.right'):
        assert np.array_equal(old_v,s['original_v']);reference=ref.copy();q=s['v'].copy()
    else:
        reference=np.einsum('ij,ijk->ik',vertex_bary,old_v[s['original_f'][vertex_parent]])
        reference[:len(retained)]=old_v[retained]
        delta=s['v']-ref;delta[:,0]*=-1
        q=reference.copy();q[changed]=(reference[changed]+delta[changed]).astype(np.float32)
    belly_ids=np.flatnonzero(s['original_belly']);belly_indices=np.searchsorted(retained,belly_ids)
    assert np.array_equal(q[belly_indices],old_v[belly_ids])
    mesh=bpy.data.meshes.new('SURFACE_RECONSTRUITE_'+key)
    mesh.from_pydata(q.tolist(),[],ff.tolist());mesh.update()
    for slot in old.materials:mesh.materials.append(slot)
    mesh.polygons.foreach_set('use_smooth',np.ones(len(f),bool))
    mesh.polygons.foreach_set('material_index',np.array([old.polygons[i].material_index for i in parent],int))
    for layer in old.uv_layers:
        old_uv=np.array([x.uv[:]for x in layer.data]).reshape(-1,3,2)
        new_uv=np.einsum('fkj,fkjd->fkd',corner_bary,old_uv[cp]).reshape(-1,2)
        mesh.uv_layers.new(name=layer.name).data.foreach_set('uv',new_uv.ravel())
    # Preserve P4 shading on the locked/outside surface; actual changed geometry
    # supplies the smooth normals inside the reconstruction and its transition.
    old_norm=np.array([p.vector[:]for p in old.corner_normals]).reshape(-1,3,3)
    original_norm=np.einsum('fkj,fkjd->fkd',corner_bary,old_norm[cp])
    normal=np.array([p.vector[:]for p in mesh.corner_normals]).reshape(-1,3,3)
    blend=s['work'][ff][:,:,None]
    normal=original_norm*(1-blend)+normal*blend
    normal/=np.maximum(np.linalg.norm(normal,axis=2)[:,:,None],1e-12)
    mesh.normals_split_custom_set(normal.reshape(-1,3).tolist())
    clone.data=mesh
    # Transfer pre-existing deform groups; do not create selection segmentation.
    if len(ob.vertex_groups):
        weights=np.zeros((len(old_v),len(ob.vertex_groups)))
        for vertex in old.vertices:
            for g in vertex.groups:weights[vertex.index,g.group]=g.weight
        interp=np.einsum('ij,ijk->ik',vertex_bary,weights[s['original_f'][vertex_parent]])
        interp[:len(retained)]=weights[retained]
        for gi,group in enumerate(clone.vertex_groups):
            for vi in np.flatnonzero(interp[:,gi]>1e-7):group.add([int(vi)],float(interp[vi,gi]),'REPLACE')
    q=np.array([p.co[:]for p in mesh.vertices]);reference=reference.astype(np.float32).astype(float)
    volume=lambda v:float(np.einsum('ij,ij->i',v[ff[:,0]],np.cross(v[ff[:,1]],v[ff[:,2]])).sum()/6)
    np.savez_compressed(root/('serialized-'+key+'.npz'),v=q,reference_v=reference,f=ff)
    records[key]={'vertices':len(mesh.vertices),'triangles':len(mesh.polygons),
                  'original_belly_vertices_unchanged':int(s['original_belly'].sum()),
                  'max_belly_displacement_m':0.,'volume_after_m3':volume(q)}
    ev.to_mesh_clear()
after.camera=source.camera;bpy.context.window.scene=after
meta={'scene':after.name,'before_scene':source.name,'baseline_blend_sha256':sha(a.baseline),
      'validation_status':'INSUFFISANT_NON_VALIDE','known_self_intersections_per_deltoid':7,
      'reference_commit':'0ab3d838c728a88f2d325edff7a6884400c9ed78',
      'guides_commit':'0fc6f0b3a0ffacc2283d26a06afa852ef3be35ad',
      'master':'reconstruction-guides.blend','records':records,'unchanged_objects':298,
      'surface_method':json.loads((root/'surface.json').read_text()),
      'source_attribution':'Ecorche - Anatomy study, Beatriz Gomez Santamaria, CC BY 4.0; P5 head: Blender Studio / Dan Ulrich, CC0. Derived local deltoid reconstruction; rest unchanged.'}
(root/'reconstruction.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
bpy.data.texts.new('RECONSTRUCTION_GUIDES.json').write(json.dumps(meta,ensure_ascii=False,indent=2))
bpy.data.texts.new('NON_VALIDE_LIRE_AVANT_UTILISATION').write(
    'ESSAI INSUFFISANT NON VALIDE. 7 intersections par deltoide et marques aux raccords.\n'
    'Ne pas integrer. Conserver 0ab3d83 comme reference et 0fc6f0b comme guides.\n'
    'Le bombee central et les 298 autres objets sont preserves, mais la correction des creux est insuffisante.\n')
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']),compress=True)
print('BUILT',json.dumps(records),flush=True)
