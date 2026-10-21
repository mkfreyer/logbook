"""Step 1 only: project the user's red/blue paths onto unchanged 0ab3d83.

No mesh, shape-key, UV, weight, modifier or muscle material is edited.
The additional CURVE objects are removable visual guides, not muscle geometry.
Run in Blender 4.3.2. The input camera is the documented manual crop calibration.
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.bvhtree import BVHTree

p = argparse.ArgumentParser()
p.add_argument('--baseline', type=Path, required=True)
p.add_argument('--camera', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--render', action='store_true')
p.add_argument('--reuse-unchanged-controls', action='store_true')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
root = a.output.resolve()
root.mkdir(parents=True, exist_ok=True)
out = root / 'renders'
out.mkdir(exist_ok=True)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
cached_controls = {}
if a.reuse_unchanged_controls:
    previous = json.loads((out/'metadata.json').read_text())
    cached_controls = {f['file']:f for f in previous['frames']
                       if f['file'] in ['reference-sans-guides.png','reference-anciens-rouges.png']}
assert sha(a.baseline) == 'f8b6a232a18335221af3cafc62b37837fedc1caaf9bc6cb48e1cb583f222d9ab'
c = json.loads(a.camera.read_text())
plane = 0.002114987923242599
radius, lift = 0.00022, 0.0004

# Manually transcribed open polylines in the supplied 320 x 384 image.
# Green outlines are intentionally unused: they are region indications only.
old1 = [[92,130],[80,153],[69,180],[60,208],[54,230],
        [53,258],[53,286],[55,292],[57,300],[65,319],[78,335],[94,350]]
blue1 = [[55,292],[57,312],[57,333],[60,353],[64,370],[70,378]]
old2 = [[230,82],[233,100],[234,128],[231,160],[225,192],
        [217,223],[207,254],[194,286],[179,315],[161,344]]
blue2 = [[229,72],[230,90],[219,123],[213,151],[207,185],
         [200,217],[187,251],[174,280],[164,315],[149,352],[132,379]]
anchors = {'ancien_1':old1, 'ancien_2':old2,
           'nouveau_1_partie_conservee':old1[:8],
           'nouveau_1_terminaison':blue1, 'nouveau_2':blue2}


def sample_path(points, step=.4):
    """Dense cubic Hermite sampling, no curvature snapping or trajectory fitting."""
    points = np.asarray(points, float)
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    t = np.r_[0, np.cumsum(lengths)]
    tangent = np.empty_like(points)
    tangent[0] = (points[1]-points[0])/lengths[0]
    tangent[-1] = (points[-1]-points[-2])/lengths[-1]
    for i in range(1,len(points)-1):
        tangent[i] = (points[i+1]-points[i-1])/(t[i+1]-t[i-1])
    result = []
    for i,length in enumerate(lengths):
        u = np.arange(max(2,math.ceil(length/step))) / max(2,math.ceil(length/step))
        q = ((2*u**3-3*u**2+1)[:,None]*points[i]
             +(u**3-2*u**2+u)[:,None]*length*tangent[i]
             +(-2*u**3+3*u**2)[:,None]*points[i+1]
             +(u**3-u**2)[:,None]*length*tangent[i+1])
        result.extend(q.tolist())
    return np.array(result+[points[-1].tolist()])


bpy.ops.wm.open_mainfile(filepath=str(a.baseline.resolve()), use_scripts=False)
scene = bpy.data.scenes['16_COMBINAISON_P4_P5']
bpy.context.window.scene = scene
# This standalone review file retains the approved scene only. All historical
# versions remain in their original files and git history, which are untouched.
for other in list(bpy.data.scenes):
    if other != scene:
        bpy.data.scenes.remove(other)
bpy.data.orphans_purge(do_recursive=True)
scene.name = '18_GUIDES_SANS_SCULPTURE'
scene.view_layers[0].update()
graph = bpy.context.evaluated_depsgraph_get()
trees, arrays = {}, {}
for side in ['right','left']:
    ob = scene.objects['P4P5__deltoid.'+side]
    ev = ob.evaluated_get(graph)
    mesh = ev.to_mesh()
    v = np.array([ob.matrix_world @ p.co for p in mesh.vertices])
    f = np.array([p.vertices[:] for p in mesh.polygons], np.int32)
    arrays[side] = (v,f)
    trees[side] = BVHTree.FromPolygons(v.tolist(),f.tolist(),all_triangles=True)
    ev.to_mesh_clear()

target = np.array(c['target_m'])
theta = math.radians(c['yaw_degrees'])
right = np.array([math.cos(theta),math.sin(theta),0.])
direction = np.array([math.sin(theta),-math.cos(theta),0.])
camdata = bpy.data.cameras.new('GUIDES_REFERENCE_DROITE')
camdata.type = 'ORTHO'
camdata.ortho_scale = c['ortho_scale']
cam = bpy.data.objects.new(camdata.name,camdata)
scene.collection.objects.link(cam)
cam.location = c['location_m']
cam.rotation_euler = (Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
scene.camera = cam
scene.render.resolution_x,scene.render.resolution_y = 320,384
scene.render.resolution_percentage = 100
scene.render.pixel_aspect_x,scene.render.pixel_aspect_y = c['pixel_aspect_x'],1
scene.view_layers[0].update()


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    emission = mat.node_tree.nodes.new('ShaderNodeEmission')
    emission.inputs['Color'].default_value = (*color,1)
    emission.inputs['Strength'].default_value = 1
    output = mat.node_tree.nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(emission.outputs[0],output.inputs['Surface'])
    return mat


mats = {'old':material('GUIDE_ROUGE_ANCIEN',(.8,.008,.012)),
        'new':material('GUIDE_BLEU_DEMANDE',(.006,.055,1)),
        'outside':material('GUIDE_ORANGE_HORS_DELTOIDE',(1,.38,.005))}
collections = {}
for side in ['right','left']:
    coll = bpy.data.collections.new('GUIDES_RETRAIT_FACILE_'+side.upper())
    scene.collection.children.link(coll)
    collections[side] = coll
guide_objects = []


def curve(name, points, normals, side, role, part):
    # The stored projection is exactly on the original triangles. A display-only
    # normal lift avoids z fighting; this is recorded separately, never baked.
    pos = np.asarray(points)+lift*np.asarray(normals)
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.bevel_depth = radius
    data.bevel_resolution = 2
    spline = data.splines.new('POLY')
    spline.points.add(len(pos)-1)
    spline.points.foreach_set('co',np.c_[pos,np.ones(len(pos))].ravel())
    data.materials.append(mats[role])
    ob = bpy.data.objects.new(name, data)
    collections[side].objects.link(ob)
    ob['guide_only'] = True
    ob['side'] = side
    ob['role'] = role
    ob['part'] = part
    ob.visible_shadow = False
    ob.hide_viewport = True
    guide_objects.append(ob)
    return ob


records = {}
max_projection_error = max_surface_error = max_left_snap = 0.
for name,path in anchors.items():
    points = sample_path(path)
    rows = []
    for uv in points:
        origin = target+right*(uv[0]-160)/c['pixels_per_meter_x']
        origin += [0,0,(192-uv[1])/c['pixels_per_meter_y']]
        origin += 4*direction
        hit = scene.ray_cast(graph, Vector(origin), Vector(-direction), distance=8)
        assert hit[0], (name,uv.tolist())
        visible_loc,visible_normal,obj = hit[1],hit[2],hit[4]
        sid = obj.get('asset_id')
        assert sid == 'deltoid.right' or name.startswith('nouveau_'), (name,sid,uv)
        loc,normal = visible_loc,visible_normal
        if sid != 'deltoid.right':
            actual = trees['right'].ray_cast(Vector(origin),Vector(-direction),8)
            assert actual[0] is not None, ('requested ray misses deltoid',name,uv)
            loc,normal = actual[:2]
        q = world_to_camera_view(scene,cam,loc)
        reproj = np.array([q.x*320,(1-q.y)*384])
        error = float(np.linalg.norm(reproj-uv))
        max_projection_error = max(max_projection_error,error)
        nearest = trees['right'].find_nearest(loc)
        max_surface_error = max(max_surface_error,float(nearest[3]))
        rows.append({'reference_px':uv.tolist(),'surface_m':list(loc),
                     'normal':list(normal),'object':'deltoid.right',
                     'first_visible_object':sid,
                     'first_visible_surface_m':list(visible_loc),
                     'first_visible_normal':list(visible_normal),
                     'occlusion_depth_m':float((Vector(loc)-visible_loc).length),
                     'deltoid_visible':sid == 'deltoid.right',
                     'reprojection_error_px':error})
    records[name] = {'anchors_px':path,'points':rows}
    role = 'old' if name.startswith('ancien') else 'new'
    # The true full guide follows the DELTOID, including its occluded portion.
    positions = np.array([r['surface_m'] for r in rows])
    normals = np.array([r['normal'] for r in rows])
    for side in ['right','left']:
        pos,ns = positions.copy(),normals.copy()
        if side == 'left':
            pos[:,0] = 2*plane-pos[:,0]
            ns[:,0] *= -1
            for i in range(len(pos)):
                nearest = trees['left'].find_nearest(Vector(pos[i]))
                max_left_snap = max(max_left_snap,float(nearest[3]))
                pos[i],ns[i] = nearest[:2]
        curve(name+'_'+side,pos,ns,side,role,name)
    # Separate amber proxies merely show where the requested image trajectory
    # is occluded by another object. They are NOT deltoid guides or sculpt paths.
    start = 0
    for end in range(1,len(rows)+1):
        if end < len(rows) and rows[end]['first_visible_object'] == rows[start]['first_visible_object']:
            continue
        group = rows[start:end]
        start = end
        on_deltoid = group[0]['deltoid_visible']
        if len(group)<2 or on_deltoid:
            continue
        positions = np.array([r['first_visible_surface_m'] for r in group])
        normals = np.array([r['first_visible_normal'] for r in group])
        label = name+'_REPERE_OCCLUSION'
        ranges = [
            (i,min(i+6,len(group))) for i in range(0,len(group),11)
            if min(i+6,len(group))-i>1]
        for begin,stop in ranges:
            for side in ['right','left']:
                pos,ns = positions[begin:stop].copy(),normals[begin:stop].copy()
                if side == 'left':
                    pos[:,0] = 2*plane-pos[:,0]
                    ns[:,0] *= -1
                curve(label+'_'+side+f'_{begin}',pos,ns,side,'outside',name)

# Audit only; no subdivision, remeshing, smoothing or displacement takes place.
v,f = arrays['right']
edges = np.unique(np.sort(np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]),axis=1),axis=0)
lengths = np.linalg.norm(v[edges[:,1]]-v[edges[:,0]],axis=1)
allpts = np.array([r['surface_m'] for rows in records.values() for r in rows['points']])
distance = np.full(len(v),np.inf)
for chunk in np.array_split(allpts,24):
    distance = np.minimum(distance,np.linalg.norm(v[:,None,:]-chunk[None,:,:],axis=2).min(axis=1))
# 12 mm is a measurement region, NOT a fixed future sculpting permission/mask.
near = distance < .012
local_edges = near[edges].all(axis=1)
local_faces = near[f].all(axis=1)
tri = v[f]
side_lengths = np.stack([np.linalg.norm(tri[:,1]-tri[:,0],axis=1),
                         np.linalg.norm(tri[:,2]-tri[:,1],axis=1),
                         np.linalg.norm(tri[:,0]-tri[:,2],axis=1)],axis=1)
area2 = np.linalg.norm(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]),axis=1)
aspect = side_lengths.max(axis=1)**2/area2
percentiles = lambda x:{str(p):float(np.percentile(x,p)) for p in [0,10,50,90,95,100]}
mesh_audit = {'vertices_per_deltoid':len(v),'triangles_per_deltoid':len(f),
              'edge_length_mm':percentiles(lengths*1000),
              'measurement_radius_mm':12,'local_vertices':int(near.sum()),
              'local_edges':int(local_edges.sum()),'local_triangles':int(local_faces.sum()),
              'local_edge_length_mm':percentiles(lengths[local_edges]*1000),
              'local_triangle_aspect_longest_edge_over_altitude':percentiles(aspect[local_faces]),
              'local_triangles_aspect_above_5':int((aspect[local_faces]>5).sum()),
              'alterations_performed':False}
new2 = records['nouveau_2']['points']
last = [r for r in new2 if r['deltoid_visible']][-1]
firstoutside = [r for r in new2 if not r['deltoid_visible']][0]
meta = {'baseline_commit':'0ab3d838c728a88f2d325edff7a6884400c9ed78',
        'baseline_blend_sha256':sha(a.baseline),'source_scene':'16_COMBINAISON_P4_P5',
        'scene':scene.name,'master':'guides-deltoides-p4.blend','camera':c,
        'median_plane_x_m':plane,'display_normal_lift_m':lift,'display_radius_m':radius,
        'paths':records,'surface_reprojection_error_max_px':max_projection_error,
        'right_surface_distance_max_m':max_surface_error,
        'mirrored_left_surface_snap_max_m':max_left_snap,
        'new2_last_visible_deltoid':last,'new2_first_occluded_point':firstoutside,
        'occluded_deltoid_samples':{name:[r for r in rec['points'] if not r['deltoid_visible']]
                                   for name,rec in records.items()},
        'mesh_audit':mesh_audit,'sculpture_performed':False,
        'registration':'Same -55 degree original orientation; manual crop/aspect calibration from two visible landmarks, not automatic pixel registration. Paths are manual transcriptions awaiting user validation.',
        'rights':'Body: Beatriz Gomez Santamaria, CC BY 4.0. P5 head: Human Base Meshes v1.4.1, Blender Studio / Dan Ulrich, CC0. Only separate curve guides added.'}
(root/'guides.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
(root/'maillage-audit.json').write_text(json.dumps(mesh_audit,indent=2)+'\n')
bpy.data.texts.new('GUIDES_LIRE_AVANT_TOUTE_SCULPTURE').write(
    'ETAPE 1 UNIQUEMENT. Aucun maillage modifie. Validation des courbes requise.\n'
    'Rouge: ancien trace. Bleu: trajet demande sur deltoide. Orange pointille: reperes des portions masquees par le bras.\n'
    'Deux collections GUIDES_RETRAIT_FACILE_* peuvent etre masquees ou supprimees.\n')
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 48
scene.cycles.seed = 0
scene.cycles.use_denoising = False
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
scene.world = bpy.data.worlds['PASSE3_FOND_NEUTRE']


def set_guides(mode, side='right'):
    for ob in guide_objects:
        hide = ob['side'] != side or mode == 'none'
        if mode == 'old':
            hide |= ob['role'] != 'old'
        if mode == 'new':
            hide |= ob['role'] == 'old'
        if mode == 'both':
            # Common upper segment remains red in the combined view. Avoid
            # coincident blue/red tubes. It is blue in the new-only view.
            hide |= ob['part'] == 'nouveau_1_partie_conservee'
        ob.hide_render = hide
        ob.hide_viewport = hide


set_guides('both')
scene.camera = cam
scene.render.resolution_x,scene.render.resolution_y = 960,1152
scene.render.pixel_aspect_x = c['pixel_aspect_x']
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']),compress=True)
print('GUIDES_SAVED',json.dumps({k:meta[k] for k in [
    'surface_reprojection_error_max_px','right_surface_distance_max_m',
    'mirrored_left_surface_snap_max_m','sculpture_performed']}),flush=True)

if a.render:
    frames = []
    views = [(label,cam,(960,1152),c['pixel_aspect_x'],mode,'right')
             for label,mode in [('reference-sans-guides','none'),
                               ('reference-anciens-rouges','old'),
                               ('reference-nouveaux-bleus','new'),
                               ('reference-superposition','both')]]
    views += [('profil-guides',scene.objects['P4P5_epaule-profil'],(960,864),1,'both','right'),
              ('face-guides',scene.objects['P4P5_epaules-face'],(1200,640),1,'both','both')]
    # An exactly mirrored reference camera checks the opposite shoulder.
    leftcam = cam.copy()
    leftcam.data = cam.data.copy()
    leftcam.name = 'GUIDES_REFERENCE_GAUCHE'
    scene.collection.objects.link(leftcam)
    loc,aim = np.array(c['location_m']),target.copy()
    loc[0],aim[0] = 2*plane-loc[0],2*plane-aim[0]
    leftcam.location = loc
    leftcam.rotation_euler = (Vector(aim)-leftcam.location).to_track_quat('-Z','Y').to_euler()
    views.append(('reference-epaule-gauche',leftcam,(960,1152),c['pixel_aspect_x'],'both','left'))
    for label,camera,resolution,aspect,mode,side in views:
        set_guides(mode,side)
        if side == 'both':
            for ob in guide_objects:
                ob.hide_render = ob.hide_viewport = ob['part'] == 'nouveau_1_partie_conservee'
        if label in ['profil-guides','face-guides']:
            for ob in guide_objects:
                if ob['role']=='outside':
                    ob.hide_render = ob.hide_viewport = True
        scene.camera = camera
        scene.render.resolution_x,scene.render.resolution_y = resolution
        scene.render.pixel_aspect_x = aspect
        scene.render.filepath = str(out/(label+'.png'))
        cache = cached_controls.get(label+'.png')
        if cache:
            scene.view_layers[0].update()
            assert cache['camera_matrix']==[list(r) for r in camera.matrix_world]
            assert sha(out/(label+'.png'))==cache['sha256']
        else:
            bpy.ops.render.render(write_still=True,scene=scene.name)
        frames.append({'file':label+'.png','sha256':sha(out/(label+'.png')),
                       'camera_matrix':[list(r) for r in camera.matrix_world],
                       'ortho_scale':camera.data.ortho_scale,'resolution':resolution,
                       'pixel_aspect_x':aspect,'mode':mode})
        (out/'metadata.json').write_text(json.dumps({'samples':48,'neutral_matte_unchanged':True,
            'original_five_lights_unchanged':True,'frames':frames},indent=2)+'\n')
    set_guides('both')
    scene.camera = cam
    scene.render.resolution_x,scene.render.resolution_y = 960,1152
    scene.render.pixel_aspect_x = c['pixel_aspect_x']
    bpy.ops.wm.save_as_mainfile(filepath=str(root/meta['master']),compress=True)
    print('RENDERED',len(frames),flush=True)
