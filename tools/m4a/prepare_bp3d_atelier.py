"""Prepare a non-destructive BP3D editing atelier, not an automatic sculpture.

Blender 4.3.2. The original OBJ bytes remain available in a small standalone
bundle. No global union, primitive muscle replacement, warp or artist claim.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import sys
import zipfile
from pathlib import Path

import bpy
from mathutils import Matrix, Vector, kdtree

PINS = '40665852c49f218326590e204db91064a1ecfc3c6f8cbd7bbbcaac62c7cd409e'
GROUPS = ['pectoralis-major-left', 'pectoralis-major-right', 'deltoid-left']
BONES = ['FMA7486', 'FMA7487', 'FMA13322', 'FMA13323', 'FMA13396', 'FMA23131']
REPO = Path(__file__).resolve().parents[2]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--source-dir', type=Path)
p.add_argument('--bundle', type=Path)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--guide', type=Path, default=REPO/'docs/m4a/bp3d-atelier-local/GUIDE_SCULPTURE.md')
p.add_argument('--attribution', type=Path, default=REPO/'docs/m4a/bp3d-atelier-local/ATTRIBUTION.md')
a = p.parse_args(sys.argv[sys.argv.index('--')+1:])
assert bool(a.source_dir) != bool(a.bundle), 'Choose original source directory OR delivered bundle'
a.output.mkdir(parents=True, exist_ok=True)
def sha(raw): return hashlib.sha256(raw).hexdigest()
def dump(value): return json.dumps(value, ensure_ascii=False, indent=2)+'\n'

if a.source_dir:
    provenance = json.loads((REPO/'docs/m4a/bodyparts3d/provenance.json').read_text())
    pins = {r['file']:r['sha256'] for r in provenance['files']}
    for file in ['isa_BP3D_4.0_obj_99.zip', 'isa_parts_list_e.txt', 'isa_element_parts.txt']:
        assert sha((a.source_dir/file).read_bytes()) == pins[file]
    selection = json.loads((REPO/'docs/m4a/bodyparts3d/selection-candidate.json').read_text())
    muscle_groups = [next(g for g in selection['selection_candidates'] if g['id']==key) for key in GROUPS]
    records = []
    for g in muscle_groups:
        for c in g['components']:
            for element in c['elements']:
                records.append({'role':'muscle', 'muscle_id':g['id'], 'side':g['side'],
                    'concept_id':c['concept_id'], 'representation_id':c['representation_id'],
                    'name_en':c['name_en'], 'parts_list_line':c['parts_list_line'], **element})
    parts = {}
    for n, row in enumerate(csv.DictReader(io.StringIO((a.source_dir/'isa_parts_list_e.txt').read_text()), delimiter='\t'), 2):
        parts[row['concept id']] = {**row, 'line':n}
    for n, row in enumerate(csv.DictReader(io.StringIO((a.source_dir/'isa_element_parts.txt').read_text()), delimiter='\t'), 2):
        fma = row['concept id']
        if fma in BONES:
            r = parts[fma]
            records.append({'role':'bone_reference', 'concept_id':fma,
                'representation_id':r['representation id'], 'name_en':r['en'],
                'element_id':row['element file id'], 'obj_filename':row['element file id']+'.obj',
                'parts_list_line':r['line'], 'element_parts_line':n})
    assert len(records)==15
    with zipfile.ZipFile(a.source_dir/'isa_BP3D_4.0_obj_99.zip') as z:
        names = {Path(n).stem:n for n in z.namelist() if n.endswith('.obj')}
        blobs = {r['element_id']:z.read(names[r['element_id']]) for r in records}
    for r in records:
        raw = blobs[r['element_id']]; r.update(obj_sha256=sha(raw), obj_bytes=len(raw))
    manifest = {'official_archive_sha256':PINS, 'muscle_ids':GROUPS,
        'transform':json.loads((REPO/'docs/m4a/ecorche/bodyparts3d/inventory.json').read_text())['transform'],
        'axes':{'+X':'anatomical left', '-Y':'anterior', '+Z':'superior'},
        'pose':'Unchanged BP3D source pose. No athletic volume or attachment correction performed.',
        'table_sha256':{k:pins[k] for k in ['isa_parts_list_e.txt','isa_element_parts.txt']}, 'objects':records}
    bundle = a.output/'sources-originales.zip'
    with zipfile.ZipFile(bundle, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        content = {'manifest.json':dump(manifest).encode(), 'ATTRIBUTION.md':a.attribution.read_bytes()}
        content.update({r['obj_filename']:blobs[r['element_id']] for r in records})
        for name, raw in content.items():
            info = zipfile.ZipInfo(name, (2026,10,19,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info, raw)
else:
    bundle = a.bundle
    with zipfile.ZipFile(bundle) as z:
        manifest = json.loads(z.read('manifest.json')); records = manifest['objects']
        assert manifest['official_archive_sha256']==PINS and manifest['muscle_ids']==GROUPS
        blobs = {r['element_id']:z.read(r['obj_filename']) for r in records}
    for r in records: assert sha(blobs[r['element_id']])==r['obj_sha256']
(a.output/'identites.json').write_text(dump(manifest))

for ob in list(bpy.data.objects): bpy.data.objects.remove(ob, do_unlink=True)
for attr in ['meshes','materials','cameras','lights']:
    blocks=getattr(bpy.data,attr)
    for block in list(blocks):
        if block.users==0:blocks.remove(block)
work = bpy.context.scene; work.name='00_ATELIER'
for c in list(work.collection.children): work.collection.children.unlink(c)
source = bpy.data.scenes.new('01_SOURCES')
def collection(name, parent):
    c=bpy.data.collections.new(name); parent.children.link(c); return c
raw_col=collection('ORIGINAUX_VERROUILLES', source.collection)
bone_col=collection('REPERES_OSSEUX', work.collection); source.collection.children.link(bone_col)
bone_col.hide_render=True
work_col=collection('TRAVAIL', work.collection)
markers_col=collection('RACCORDS_A_REPRENDRE', work.collection)
rig=collection('CAMERAS_ET_LUMIERES', work.collection); source.collection.children.link(rig)
sub={g:collection('MUSCLE__'+g, work_col) for g in GROUPS}

def material(name, color):
    m=bpy.data.materials.new(name); m.use_nodes=True; m.diffuse_color=(*color,1)
    n=m.node_tree.nodes.get('Principled BSDF'); n.inputs['Base Color'].default_value=(*color,1)
    n.inputs['Roughness'].default_value=.37; n.inputs['Metallic'].default_value=.12
    n.inputs['Coat Weight'].default_value=.08; return m
blue=material('BLEU_ARGENTE__SATINE', (.19,.28,.42))
orange=material('ORANGE__MUSCLE_ENTIER', (1,.18,.025))
bone_mat=material('OS__REFERENCE_SEULEMENT', (.22,.25,.30))
center=Vector(manifest['transform']['center']); scale=manifest['transform']['uniform_scale']
normalization=Matrix.Scale(scale,4) @ Matrix.Translation(-center)
xyz_by_id={}; working=[]; original=[]; scene_records=[]
def parse(raw):
    vertices=[]; faces=[]
    for line in raw.decode('utf-8-sig').splitlines():
        b=line.split()
        if b and b[0]=='v': vertices.append(tuple(float(x) for x in b[1:4]))
        elif b and b[0]=='f': faces.append(tuple(int(x.split('/')[0])-1 for x in b[1:]))
    return vertices,faces

def mesh_object(name, coords, faces, col, mat):
    mesh=bpy.data.meshes.new(name); mesh.from_pydata(coords, [], faces); mesh.update()
    mesh.materials.append(mat)
    for f in mesh.polygons: f.use_smooth=True
    ob=bpy.data.objects.new(name,mesh); col.objects.link(ob); return ob

for r in records:
    element=r['element_id']; xyz,faces=parse(blobs[element]); normalized=[normalization @ Vector(v) for v in xyz]
    xyz_by_id[element]=normalized
    ob=mesh_object('RAW__'+element,xyz,faces,raw_col if r['role']=='muscle' else bone_col, blue if r['role']=='muscle' else bone_mat)
    ob.matrix_world=normalization; ob.hide_select=True; ob['source_element_id']=element
    ob['fma']=r['concept_id']; ob['source_name']=r['name_en']; ob['source_obj_sha256']=r['obj_sha256']
    if r['role']!='muscle':
        ob.display_type='WIRE'; ob.show_in_front=True; continue
    ob['muscle_id']=r['muscle_id']; original.append(ob)
    # Exact-position weld is within one source OBJ only. No warp or surface union.
    unique={}; coords=[]; remap=[]
    for v in xyz:
        if v not in unique: unique[v]=len(coords); coords.append(tuple(normalization @ Vector(v)))
        remap.append(unique[v])
    indices=[tuple(remap[i] for i in f) for f in faces]
    edit=mesh_object('EDIT__'+element,coords,indices,sub[r['muscle_id']],blue)
    for key in ['source_element_id','fma','source_name','source_obj_sha256','muscle_id']: edit[key]=ob[key]
    edit['sculpture_status']='Not sculpted; source geometry, exact-position weld and normalization only'
    vg=edit.vertex_groups.new(name='source_'+element); vg.add(list(range(len(coords))),1,'REPLACE')
    # Label connected islands for manual inspection; do not remove or reshape them.
    neighbors=[set() for _ in coords]
    for face in indices:
        for u,v in zip(face,face[1:]+face[:1]):neighbors[u].add(v);neighbors[v].add(u)
    todo=set(range(len(coords)));components=[]
    while todo:
        stack=[min(todo)];todo.remove(stack[0]);part=[]
        while stack:
            v=stack.pop();part.append(v)
            for n in sorted(neighbors[v]):
                if n in todo:todo.remove(n);stack.append(n)
        components.append(part)
    for i,part in enumerate(sorted(components,key=lambda c:(-len(c),min(c))),1):
        group=edit.vertex_groups.new(name=f'DIAG_ILOT_{i:02d}_V{len(part)}');group.add(part,1,'REPLACE')
    edit['source_connected_islands']=len(components)
    for name in ['Basis','VOLUME_MANUEL','RACCORDS_MANUELS']: edit.shape_key_add(name=name)
    edit.active_shape_key_index=1
    edit.data.calc_loop_triangles(); working.append(edit)
    scene_records.append({'element_id':element,'muscle_id':r['muscle_id'],'source_vertices':len(xyz),
        'editable_vertices':len(coords),'triangles':len(edit.data.loop_triangles),'position_changes':'none; normalization only'})

# Marker locations are geometric navigation aids, not validated anatomical attachments.
def avg(points): return sum(points,Vector())/len(points)
def near_pair(a,b):
    tree=kdtree.KDTree(len(b))
    for i,v in enumerate(b): tree.insert(v,i)
    tree.balance(); pairs=[(v,*tree.find(v)) for v in a]
    u,v,i,d=min(pairs,key=lambda q:q[-1]); return (u+v)/2
left_pec=[v for f in ['FJ1446M','FJ1447M','FJ1464M'] for v in xyz_by_id[f]]
left_del=[v for f in ['FJ1467M','FJ1468M','FJ1513M'] for v in xyz_by_id[f]]
marker_rows=[
 ('R01_STERNUM',avg(xyz_by_id['FJ3178']),'Sternal origin edges: inspect medially; centroid of body of sternum only.'),
 ('R02_CLAVICULE_G',avg(xyz_by_id['FJ3237']),'Inspect clavicular origin; bone centroid only.'),
 ('R03_DELTO_PECTORAL_G',near_pair(left_pec,left_del),'Nearest surface pair, not a validated sulcus or insertion.'),
 ('R04_HUMERUS_G',near_pair(left_pec,xyz_by_id['FJ3262']),'Nearest pec/humerus surfaces; insertion needs manual verification.'),
 ('R05_AXILLAIRE_G',avg(sorted(xyz_by_id['FJ1446M'],key=lambda v:v.x)[-80:]),'Lateral sample of abdominal pec portion; inspect anterior axillary fold.'),
 ('R06_DELTOIDE_ACROMIAL',avg(xyz_by_id['FJ1467M']),'Centroid of acromial portion, not a point on the acromion.')]
for name,location,note in marker_rows:
    ob=bpy.data.objects.new(name,None); markers_col.objects.link(ob); ob.location=location
    ob.empty_display_type='PLAIN_AXES'; ob.empty_display_size=.018; ob.show_in_front=True
    ob['manual_review']=note; ob['anatomical_attachment_validated']=False
(a.output/'raccords-a-reprendre.json').write_text(dump([{'name':n,'location':list(v),'scope':t} for n,v,t in marker_rows]))

def aim(ob, target): ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size,col in [('KEY',(-2,-2.5,3),230,3,(.81,.88,1)),('FILL',(2.6,-1.7,1.6),110,2.5,(.56,.69,1)),('RIM',(1.6,2.3,2.8),310,2,(.58,.72,1))]:
    data=bpy.data.lights.new(name,'AREA'); data.energy=power; data.shape='DISK'; data.size=size; data.color=col
    ob=bpy.data.objects.new(name,data); rig.objects.link(ob); ob.location=loc; aim(ob,(0,0,1.4))
cameras={}
for name,yaw,ortho,target in [('CAM_FACE',0,.70,(0,-.04,1.40)),('CAM_TROIS_QUARTS',-35,.70,(0,-.04,1.40)),('CAM_DETAIL',-25,.43,(.095,-.04,1.41))]:
    data=bpy.data.cameras.new(name); data.type='ORTHO'; data.ortho_scale=ortho
    ob=bpy.data.objects.new(name,data); rig.objects.link(ob); theta=math.radians(yaw)
    ob.location=(3*math.sin(theta),-3*math.cos(theta),1.41); aim(ob,target); cameras[name]=ob

# Object material overrides: whole anatomical pieces, no nearest-face masks or drivers.
demos=[]
for index,g in enumerate(GROUPS,2):
    scene=bpy.data.scenes.new(['02_DEMO_PEC_G','03_DEMO_PEC_D','04_DEMO_DELTOIDE_G'][index-2])
    scene.collection.children.link(rig); col=collection('DEMONSTRATION__'+g,scene.collection)
    scene['selected_muscle_id']=g; scene['presentation']='Technical selection demonstration, not a sculpted result'
    for ob in working:
        duplicate=ob.copy(); duplicate.data=ob.data; col.objects.link(duplicate)
        duplicate.name=scene.name+'__'+ob['source_element_id']; duplicate.hide_select=True
        slot=duplicate.material_slots[0]; slot.link='OBJECT'; slot.material=orange if ob['muscle_id']==g else blue
    demos.append(scene)
world=bpy.data.worlds.new('BLEU_NUIT'); world.use_nodes=True
world.node_tree.nodes['Background'].inputs['Color'].default_value=(.009,.019,.036,1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6
for scene in [work,source]+demos:
    scene.world=world; scene.camera=cameras['CAM_FACE']; scene.render.engine='CYCLES'
    scene.cycles.device='CPU'; scene.cycles.samples=64; scene.cycles.seed=0; scene.cycles.use_denoising=False
    scene.render.resolution_x=720; scene.render.resolution_y=800; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'; scene.view_settings.view_transform='AgX'
    scene['artistic_sculpture_performed']=False; scene['visual_approval']=False
    scene['scope']='Only two pectorals and left deltoid; no skin, body reconstruction, rig or app'
for name,text in [('LIRE_AVANT_SCULPTURE.md',a.guide.read_text()),('IDENTITES.json',dump(manifest)),('ATTRIBUTION.md',a.attribution.read_text())]:
    bpy.data.texts.new(name).write(text)
bpy.context.window.scene=work
bpy.ops.object.select_all(action='DESELECT'); working[0].select_set(True); work.view_layers[0].objects.active=working[0]
for workspace in bpy.data.workspaces:
    for screen in [workspace.screens[0]] if workspace.screens else []:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active; space.shading.type='SOLID'; space.shading.color_type='MATERIAL'
                space.overlay.show_floor=False; space.region_3d.view_location=(0,-.04,1.40)
                space.region_3d.view_rotation=cameras['CAM_FACE'].rotation_euler.to_quaternion()
                space.region_3d.view_distance=1; space.region_3d.view_perspective='ORTHO'
summary={'generator_sha256':sha(Path(__file__).read_bytes()),'source_bundle_sha256':sha(bundle.read_bytes()),
    'muscle_objects':9,'logical_muscles':GROUPS,'bone_reference_objects':6,'copies':scene_records,
    'sculpture_performed':False,'automatic_sculpt_variants':0,'source_geometry_unmodified':True,
    'work_geometry_changes':'Per-OBJ exact-position weld, normalized coordinates, smooth display only; no artistic deformation.',
    'selection':'Whole object material override on all three portions of one muscle. No face masks or startup scripts.',
    'reference_pose':'Unchanged source pose; target athletic volumes/attachments not manually corrected.',
    'license_for_adapted_scene':'CC-BY-SA-4.0'}
(a.output/'preparation.json').write_text(dump(summary))
bpy.ops.wm.save_as_mainfile(filepath=str((a.output/'atelier-pectoraux-deltoide.blend').resolve()),compress=True)
print('ATELIER_READY',dump(summary),flush=True)
