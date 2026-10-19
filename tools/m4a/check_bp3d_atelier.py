"""Verify the BP3D atelier's immutable sources, editable copies and whole-muscle selection.

These are structural checks of an unsculpted preparation, never visual approval.
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--prepared',type=Path,required=True)
p.add_argument('--diagnostic-dir',type=Path)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.prepared.resolve()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def xyz(mesh):return np.array([v.co[:] for v in mesh.vertices],dtype=np.float32)
def parse(raw):
    v=[];f=[]
    for line in raw.decode('utf-8-sig').splitlines():
        b=line.split()
        if b and b[0]=='v':v.append(tuple(float(x) for x in b[1:4]))
        elif b and b[0]=='f':f.append(tuple(int(x.split('/')[0])-1 for x in b[1:]))
    return v,f
meta=json.loads((root/'identites.json').read_text());prep=json.loads((root/'preparation.json').read_text())
assert sha(Path(__file__).with_name('prepare_bp3d_atelier.py'))==prep['generator_sha256']
assert sha(root/'sources-originales.zip')==prep['source_bundle_sha256']
with zipfile.ZipFile(root/'sources-originales.zip') as z:
    assert z.testzip() is None and json.loads(z.read('manifest.json'))==meta
    blobs={r['element_id']:z.read(r['obj_filename']) for r in meta['objects']}
for r in meta['objects']:assert hashlib.sha256(blobs[r['element_id']]).hexdigest()==r['obj_sha256']
bpy.ops.wm.open_mainfile(filepath=str(root/'atelier-pectoraux-deltoide.blend'),use_scripts=False)
assert bpy.context.scene.name=='00_ATELIER'
assert set(s.name for s in bpy.data.scenes)=={'00_ATELIER','01_SOURCES','02_DEMO_PEC_G','03_DEMO_PEC_D','04_DEMO_DELTOIDE_G'}
assert all(not (d.animation_data and d.animation_data.drivers) for d in list(bpy.data.objects)+list(bpy.data.materials)+list(bpy.data.shape_keys))
assert not bpy.data.libraries and not bpy.data.curves
assert all(i.type in {'RENDER_RESULT','COMPOSITING'} and not i.filepath for i in bpy.data.images)
assert all(not ob.modifiers for ob in bpy.data.objects if ob.type=='MESH')
for name in ['LIRE_AVANT_SCULPTURE.md','IDENTITES.json','ATTRIBUTION.md']:assert name in bpy.data.texts
assert bpy.data.texts['LIRE_AVANT_SCULPTURE.md'].as_string()==(root/'GUIDE_SCULPTURE.md').read_text()
source=bpy.data.scenes['01_SOURCES'];work=bpy.data.scenes['00_ATELIER']
normalization=Matrix.Scale(meta['transform']['uniform_scale'],4) @ Matrix.Translation(-Vector(meta['transform']['center']))
rows=[];expected_groups=meta['muscle_ids'];trees={}
for r in meta['objects']:
    element=r['element_id'];positions,faces=parse(blobs[element]);raw=bpy.data.objects['RAW__'+element]
    assert np.array_equal(xyz(raw.data),np.array(positions,dtype=np.float32))
    assert [tuple(f.vertices) for f in raw.data.polygons]==faces
    assert raw.hide_select and raw.data.users>=1 and raw['fma']==r['concept_id']
    assert raw.parent is None
    assert max(abs(raw.matrix_basis[i][j]-normalization[i][j]) for i in range(4) for j in range(4))<1e-7
    if r['role']!='muscle':continue
    assert raw.name in source.objects and raw.name not in work.objects
    edit=bpy.data.objects['EDIT__'+element];assert edit.name in work.objects and edit.data!=raw.data
    assert edit['muscle_id']==raw['muscle_id']==r['muscle_id'] and edit['fma']==r['concept_id']
    assert edit.matrix_world==Matrix.Identity(4)
    unique={};coords=[];remap=[]
    for v in positions:
        if v not in unique:unique[v]=len(coords);coords.append(tuple(normalization @ Vector(v)))
        remap.append(unique[v])
    expected_faces=[tuple(remap[i] for i in f) for f in faces]
    assert np.array_equal(xyz(edit.data),np.array(coords,dtype=np.float32))
    assert [tuple(f.vertices) for f in edit.data.polygons]==expected_faces
    assert [k.name for k in edit.data.shape_keys.key_blocks]==['Basis','VOLUME_MANUEL','RACCORDS_MANUELS']
    for k in edit.data.shape_keys.key_blocks:
        assert np.array_equal(np.array([v.co[:] for v in k.data],dtype=np.float32),xyz(edit.data))
        if k.name!='Basis':assert k.value==0
    edit.data.calc_loop_triangles();ix=np.array([t.vertices[:] for t in edit.data.loop_triangles]);pos=xyz(edit.data)
    area=np.linalg.norm(np.cross(pos[ix[:,1]]-pos[ix[:,0]],pos[ix[:,2]]-pos[ix[:,0]]),axis=1)
    bm=bmesh.new();bm.from_mesh(edit.data);todo=set(bm.verts);parts=[]
    while todo:
        stack=[todo.pop()];count=0
        while stack:
            v=stack.pop();count+=1
            for edge in v.link_edges:
                other=edge.other_vert(v)
                if other in todo:todo.remove(other);stack.append(other)
        parts.append(count)
    diag=[g.index for g in edit.vertex_groups if g.name.startswith('DIAG_ILOT_')]
    assert len(diag)==len(parts) and all(sum(g.group in diag for g in v.groups)==1 for v in edit.data.vertices)
    row={'element_id':element,'muscle_id':r['muscle_id'],'fma':r['concept_id'],
        'source_vertices':len(positions),'editable_vertices':len(pos),'triangles':len(ix),
        'source_OBJ_and_raw_mesh_preserved':True,'work_positions_equal_normalized_source':True,
        'components':len(parts),'component_vertices':sorted(parts,reverse=True),
        'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),
        'degenerate_triangles':int((area<=1e-12).sum()),'signed_volume_scene_units_cubed':bm.calc_volume(signed=True),
        'bounds_min':pos.min(0).tolist(),'bounds_max':pos.max(0).tolist(),'centroid':pos.mean(0).tolist()}
    bm.free();assert np.isfinite(pos).all()
    if r['muscle_id'].endswith('left'):assert row['centroid'][0]>0
    else:assert row['centroid'][0]<0
    trees[element]=BVHTree.FromPolygons(pos.tolist(),ix.tolist(),all_triangles=True)
    rows.append(row)
assert len(rows)==9
selection=[]
for scene_name,g in zip(['02_DEMO_PEC_G','03_DEMO_PEC_D','04_DEMO_DELTOIDE_G'],expected_groups):
    scene=bpy.data.scenes[scene_name];objects=[o for o in scene.objects if o.type=='MESH'];assert len(objects)==9
    orange=[]
    for ob in objects:
        origin=bpy.data.objects['EDIT__'+ob['source_element_id']];assert ob.data==origin.data
        is_orange=ob['muscle_id']==g;mat=ob.material_slots[0].material
        assert ob.material_slots[0].link=='OBJECT'
        assert mat.name==('ORANGE__MUSCLE_ENTIER' if is_orange else 'BLEU_ARGENTE__SATINE')
        assert len(ob.data.materials)==1 and all(f.material_index==0 for f in ob.data.polygons)
        if is_orange:orange.append(ob['source_element_id'])
    assert len(orange)==3
    selection.append({'scene':scene_name,'muscle_id':g,'whole_portions_orange':orange,'other_portions_blue':6,'projected_face_mask':False})
# Broad-phase contact candidates only: source overlaps are not silently repaired.
contacts=[]
for i,left in enumerate(rows):
    for right in rows[i+1:]:
        candidates=len(trees[left['element_id']].overlap(trees[right['element_id']]))
        if candidates:contacts.append({'a':left['element_id'],'b':right['element_id'],'BVH_candidates':candidates})
report={'file_sha256':sha(root/'atelier-pectoraux-deltoide.blend'),'bundle_sha256':sha(root/'sources-originales.zip'),
    'scope':'Editing preparation only, not a visually approved prototype','source_originals_preserved':15,
    'work_meshes':rows,'total_work_triangles':sum(r['triangles'] for r in rows),'selection_demonstrations':selection,
    'contact_candidates_between_source_portions':contacts,'contact_interpretation':'BVH candidates are not a narrow-phase anatomical collision verdict. Contacts may be intentional overlaps; inspect manually.',
    'raw_source_topology_untouched':True,'each_work_object_exact_weld_only':True,'work_and_source_datablocks_independent':True,
    'demos_share_editable_geometry':True,'all_empty_shape_keys_equal_basis':True,'automatic_sculpt_variants':0,
    'modifiers_or_voxel_union':0,'startup_scripts_or_drivers':0,'sculpture_performed':False,'visual_validation':False,
    'attachment_and_fiber_direction_validation':'Not established by identity tables. Manual review required.',
    'limitations':['Only nine muscle portions and six bone references; no complete torso/body or target athletic reconstruction.',
    'Signed volumes are scene-unit diagnostics, not physical measurements or training volume.',
    'Source pose and all component intersections are preserved, not medically or artistically corrected.',
    'No touch engine, production segmentation, rig, glTF export or iPhone performance validation.']}
(root/'controle-scene.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if a.diagnostic_dir:
    a.diagnostic_dir.mkdir(parents=True,exist_ok=True)
    for name,scene_name,camera in [('source-face','01_SOURCES','CAM_FACE'),('atelier-trois-quarts','00_ATELIER','CAM_TROIS_QUARTS'),('selection-technique','02_DEMO_PEC_G','CAM_TROIS_QUARTS')]:
        scene=bpy.data.scenes[scene_name];scene.camera=bpy.data.objects[camera]
        scene.cycles.samples=16;scene.render.resolution_percentage=60
        scene.render.filepath=str(a.diagnostic_dir/(name+'.png'))
        bpy.ops.render.render(write_still=True,scene=scene.name)
    # Private diagnostics do not overwrite or save the supplied .blend.
assert sha(root/'atelier-pectoraux-deltoide.blend')==report['file_sha256']
print('ATELIER_CHECK',json.dumps({'work_triangles':report['total_work_triangles'],'source_objects':15,'whole_muscle_selection_cases':3,'visual_validation':False}),flush=True)
